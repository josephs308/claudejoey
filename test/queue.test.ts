import { describe, it, expect, vi } from 'vitest';
import { RetryQueue, PermanentJobError, backoffDelay, type Job } from '../src/queue/queue.js';

const policy = { maxAttempts: 4, baseDelayMs: 5, maxDelayMs: 50 };

describe('backoffDelay', () => {
  it('grows exponentially', () => {
    const noJitter = () => 1; // full-jitter factor becomes 1.0
    expect(backoffDelay(1, { maxAttempts: 5, baseDelayMs: 100, maxDelayMs: 10_000 }, noJitter)).toBe(100);
    expect(backoffDelay(2, { maxAttempts: 5, baseDelayMs: 100, maxDelayMs: 10_000 }, noJitter)).toBe(200);
    expect(backoffDelay(3, { maxAttempts: 5, baseDelayMs: 100, maxDelayMs: 10_000 }, noJitter)).toBe(400);
  });

  it('never exceeds the ceiling', () => {
    const delay = backoffDelay(20, { maxAttempts: 30, baseDelayMs: 100, maxDelayMs: 5_000 }, () => 1);
    expect(delay).toBeLessThanOrEqual(5_000);
  });

  it('applies jitter below the exponential value', () => {
    const delay = backoffDelay(3, { maxAttempts: 5, baseDelayMs: 100, maxDelayMs: 10_000 }, () => 0);
    expect(delay).toBe(200); // 400 * 0.5
  });
});

describe('RetryQueue', () => {
  it('runs a job once on success', async () => {
    const handler = vi.fn().mockResolvedValue(undefined);
    const queue = new RetryQueue(handler, policy, () => {});
    queue.enqueue('job-1', { value: 1 });
    await queue.idle();
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it('retries a transient failure and then succeeds', async () => {
    const handler = vi
      .fn()
      .mockRejectedValueOnce(new Error('boom'))
      .mockRejectedValueOnce(new Error('boom'))
      .mockResolvedValue(undefined);
    const deadLetter = vi.fn();
    const queue = new RetryQueue(handler, policy, deadLetter);

    queue.enqueue('job-1', { value: 1 });
    await queue.idle();

    expect(handler).toHaveBeenCalledTimes(3);
    expect(deadLetter).not.toHaveBeenCalled();
  });

  it('dead-letters after exhausting max attempts', async () => {
    const handler = vi.fn().mockRejectedValue(new Error('always fails'));
    const deadLetter = vi.fn();
    const queue = new RetryQueue(handler, policy, deadLetter);

    queue.enqueue('job-1', { value: 1 });
    await queue.idle();

    expect(handler).toHaveBeenCalledTimes(policy.maxAttempts);
    expect(deadLetter).toHaveBeenCalledOnce();
    const [job] = deadLetter.mock.calls[0] as [Job<unknown>, unknown];
    expect(job.attempts).toBe(policy.maxAttempts);
  });

  it('dead-letters a permanent error immediately without retrying', async () => {
    const handler = vi.fn().mockRejectedValue(new PermanentJobError('unusable payload'));
    const deadLetter = vi.fn();
    const queue = new RetryQueue(handler, policy, deadLetter);

    queue.enqueue('job-1', { value: 1 });
    await queue.idle();

    expect(handler).toHaveBeenCalledTimes(1);
    expect(deadLetter).toHaveBeenCalledOnce();
  });

  it('processes independent jobs without one failure blocking another', async () => {
    const seen: string[] = [];
    const handler = vi.fn(async (payload: { id: string }) => {
      seen.push(payload.id);
      if (payload.id === 'bad') throw new PermanentJobError('nope');
    });
    const queue = new RetryQueue(handler, policy, () => {});

    queue.enqueue('a', { id: 'bad' });
    queue.enqueue('b', { id: 'good' });
    await queue.idle();

    expect(seen).toContain('good');
  });

  it('reports queue depth', async () => {
    const queue = new RetryQueue(async () => {}, policy, () => {});
    expect(queue.depth).toBe(0);
    queue.enqueue('job-1', {});
    await queue.idle();
    expect(queue.depth).toBe(0);
  });
});
