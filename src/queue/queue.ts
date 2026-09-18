import { log, errField } from '../logger.js';

/**
 * In-process FIFO work queue with exponential backoff and jitter.
 *
 * Webhook handlers must ack fast -- Lawmatics will retry a slow endpoint and the
 * firm's leads would back up behind our own API calls. So the HTTP layer enqueues
 * and returns 200 immediately; all Lawmatics/Eve I/O happens here.
 */

export interface Job<T> {
  id: string;
  payload: T;
  attempts: number;
}

export interface RetryPolicy {
  maxAttempts: number;
  baseDelayMs: number;
  maxDelayMs: number;
}

/** Thrown by a handler to signal "do not retry, dead-letter this now". */
export class PermanentJobError extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
    this.name = 'PermanentJobError';
  }
}

/** Optional hint from a handler that a retry should wait a specific time. */
export interface RetryHint {
  retryAfterMs?: number;
}

export type JobHandler<T> = (payload: T, job: Job<T>) => Promise<void>;

export function backoffDelay(attempt: number, policy: RetryPolicy, random = Math.random): number {
  const exponential = Math.min(policy.baseDelayMs * 2 ** (attempt - 1), policy.maxDelayMs);
  // Full jitter: spreads a thundering herd of simultaneous retries.
  return Math.floor(exponential * (0.5 + random() * 0.5));
}

export class RetryQueue<T> {
  private readonly pending: Job<T>[] = [];
  private readonly timers = new Set<NodeJS.Timeout>();
  private running = false;
  private draining: Promise<void> | null = null;
  private inFlight = 0;

  constructor(
    private readonly handler: JobHandler<T>,
    private readonly policy: RetryPolicy,
    private readonly onDeadLetter: (job: Job<T>, err: unknown) => void,
  ) {}

  enqueue(id: string, payload: T): void {
    this.pending.push({ id, payload, attempts: 0 });
    this.kick();
  }

  get depth(): number {
    return this.pending.length + this.inFlight + this.timers.size;
  }

  private kick(): void {
    if (this.running) return;
    this.running = true;
    this.draining = this.drain().finally(() => {
      this.running = false;
    });
  }

  private async drain(): Promise<void> {
    while (this.pending.length > 0) {
      const job = this.pending.shift()!;
      job.attempts += 1;
      this.inFlight += 1;
      try {
        await this.handler(job.payload, job);
        log.debug('job completed', { jobId: job.id, attempts: job.attempts });
      } catch (err) {
        this.handleFailure(job, err);
      } finally {
        this.inFlight -= 1;
      }
    }
  }

  private handleFailure(job: Job<T>, err: unknown): void {
    if (err instanceof PermanentJobError) {
      log.error('job failed permanently', { jobId: job.id, attempts: job.attempts, ...errField(err) });
      this.onDeadLetter(job, err);
      return;
    }

    if (job.attempts >= this.policy.maxAttempts) {
      log.error('job exhausted retries', { jobId: job.id, attempts: job.attempts, ...errField(err) });
      this.onDeadLetter(job, err);
      return;
    }

    const hint = (err as RetryHint | undefined)?.retryAfterMs;
    const delay = hint && hint > 0 ? Math.min(hint, this.policy.maxDelayMs) : backoffDelay(job.attempts, this.policy);
    log.warn('job failed, scheduling retry', {
      jobId: job.id,
      attempts: job.attempts,
      retryInMs: delay,
      ...errField(err),
    });

    const timer = setTimeout(() => {
      this.timers.delete(timer);
      this.pending.push(job);
      this.kick();
    }, delay);
    // Do not hold the event loop open purely for a pending retry.
    timer.unref?.();
    this.timers.add(timer);
  }

  /** Waits for in-flight and queued work to settle. Used by tests and shutdown. */
  async idle(): Promise<void> {
    while (this.depth > 0) {
      if (this.draining) await this.draining;
      if (this.timers.size > 0 && this.pending.length === 0 && this.inFlight === 0) {
        await new Promise((resolve) => setTimeout(resolve, 10));
      }
    }
    if (this.draining) await this.draining;
  }

  /** Cancels scheduled retries so the process can exit promptly. */
  stop(): void {
    for (const timer of this.timers) clearTimeout(timer);
    this.timers.clear();
  }
}
