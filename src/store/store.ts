import { mkdirSync, readFileSync, writeFileSync, renameSync, existsSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';
import { log, errField } from '../logger.js';

/**
 * Durable-enough state for a single-instance connector:
 *  - which webhook event_ids have been seen (delivery dedupe)
 *  - which Lawmatics prospects already exist in Eve (sync idempotency)
 *  - a dead-letter log of payloads that exhausted their retries
 *
 * Backed by a JSON snapshot written atomically via rename. If this connector is
 * ever run multi-instance, swap this class for Redis or Postgres -- the
 * interface is narrow on purpose.
 */

interface Snapshot {
  processedEvents: Record<string, number>;
  syncedProspects: Record<string, { eveClientId: string; syncedAt: number }>;
}

const EVENT_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export class Store {
  private snapshot: Snapshot = { processedEvents: {}, syncedProspects: {} };
  private readonly file: string;
  private readonly dlqFile: string;
  private writeScheduled = false;

  constructor(private readonly dir: string) {
    mkdirSync(dir, { recursive: true });
    this.file = join(dir, 'state.json');
    this.dlqFile = join(dir, 'dead-letter.jsonl');
    this.load();
  }

  private load(): void {
    if (!existsSync(this.file)) return;
    try {
      const parsed = JSON.parse(readFileSync(this.file, 'utf8')) as Partial<Snapshot>;
      this.snapshot = {
        processedEvents: parsed.processedEvents ?? {},
        syncedProspects: parsed.syncedProspects ?? {},
      };
      this.pruneEvents();
    } catch (err) {
      // A corrupt snapshot must not stop the service from booting: the worst
      // case is re-delivering events, which the Eve idempotency key absorbs.
      log.error('could not read state file, starting empty', { file: this.file, ...errField(err) });
    }
  }

  private pruneEvents(): void {
    const cutoff = Date.now() - EVENT_TTL_MS;
    for (const [id, seenAt] of Object.entries(this.snapshot.processedEvents)) {
      if (seenAt < cutoff) delete this.snapshot.processedEvents[id];
    }
  }

  /** Coalesces bursts of writes into one flush per tick. */
  private scheduleFlush(): void {
    if (this.writeScheduled) return;
    this.writeScheduled = true;
    setImmediate(() => {
      this.writeScheduled = false;
      this.flush();
    });
  }

  flush(): void {
    const tmp = `${this.file}.tmp`;
    try {
      writeFileSync(tmp, JSON.stringify(this.snapshot), 'utf8');
      renameSync(tmp, this.file);
    } catch (err) {
      log.error('failed to persist state', { file: this.file, ...errField(err) });
    }
  }

  /** Returns true the first time an event id is seen, false on replay. */
  markEventSeen(eventId: string): boolean {
    if (this.snapshot.processedEvents[eventId] !== undefined) return false;
    this.snapshot.processedEvents[eventId] = Date.now();
    this.scheduleFlush();
    return true;
  }

  getSyncedProspect(prospectId: string): { eveClientId: string; syncedAt: number } | null {
    return this.snapshot.syncedProspects[prospectId] ?? null;
  }

  /**
   * Persisted synchronously, not debounced: this record is the only thing
   * preventing a duplicate client in Eve, so it must survive a crash in the
   * window immediately after a successful push. It runs once per conversion,
   * so the blocking write is not a throughput concern.
   */
  recordSync(prospectId: string, eveClientId: string): void {
    this.snapshot.syncedProspects[prospectId] = { eveClientId, syncedAt: Date.now() };
    this.flush();
  }

  /** Appends a permanently-failed job for manual replay. */
  deadLetter(record: Record<string, unknown>): void {
    try {
      appendFileSync(this.dlqFile, JSON.stringify({ ...record, deadLetteredAt: new Date().toISOString() }) + '\n', 'utf8');
    } catch (err) {
      log.error('failed to write dead-letter record', { ...errField(err) });
    }
  }

  stats(): { processedEvents: number; syncedProspects: number } {
    return {
      processedEvents: Object.keys(this.snapshot.processedEvents).length,
      syncedProspects: Object.keys(this.snapshot.syncedProspects).length,
    };
  }
}
