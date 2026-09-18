/**
 * Replays dead-lettered webhook events through the sync pipeline.
 *
 *   npm run replay -- [--file data/dead-letter.jsonl] [--dry-run] [--event evt_x]
 *
 * Safe to re-run: the store's idempotency record stops an already-synced
 * prospect from being pushed to Eve a second time.
 */
import { readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { loadConfig } from '../src/config.js';
import { log, errField } from '../src/logger.js';
import { LawmaticsClient } from '../src/lawmatics/client.js';
import { createEveClient } from '../src/eve/client.js';
import { Store } from '../src/store/store.js';
import { handleSyncJob } from '../src/pipeline/handler.js';
import { webhookEnvelopeSchema } from '../src/lawmatics/types.js';

function arg(name: string): string | undefined {
  const index = process.argv.indexOf(`--${name}`);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

async function main(): Promise<void> {
  const cfg = loadConfig();
  const dryRun = process.argv.includes('--dry-run');
  const only = arg('event');
  const file = arg('file') ?? join(cfg.STATE_DIR, 'dead-letter.jsonl');

  if (!existsSync(file)) {
    console.error(`No dead-letter file at ${file}`);
    process.exit(1);
  }

  const store = new Store(cfg.STATE_DIR);
  const deps = { cfg, lawmatics: new LawmaticsClient(cfg), eve: createEveClient(cfg), store };

  const lines = readFileSync(file, 'utf8').split('\n').filter((l) => l.trim());
  let replayed = 0;
  let failed = 0;

  for (const line of lines) {
    let record: { jobId?: string; envelope?: unknown };
    try {
      record = JSON.parse(line);
    } catch {
      console.error('skipping unparseable dead-letter line');
      continue;
    }

    const parsed = webhookEnvelopeSchema.safeParse(record.envelope);
    if (!parsed.success) {
      console.error(`skipping ${record.jobId ?? 'unknown'}: envelope no longer valid`);
      continue;
    }
    if (only && parsed.data.event_id !== only) continue;

    if (dryRun) {
      console.log(`would replay ${parsed.data.event_id} (${parsed.data.event_type})`);
      replayed += 1;
      continue;
    }

    try {
      const outcome = await handleSyncJob({ envelope: parsed.data, receivedAt: Date.now() }, deps);
      console.log(`${parsed.data.event_id}: ${outcome.status}`);
      replayed += 1;
    } catch (err) {
      failed += 1;
      log.error('replay failed', { eventId: parsed.data.event_id, ...errField(err) });
    }
  }

  store.flush();
  console.log(`\nreplayed ${replayed}, failed ${failed}${dryRun ? ' (dry run)' : ''}`);
  if (failed > 0) process.exit(1);
}

main().catch((err) => {
  log.error('replay crashed', errField(err));
  process.exit(1);
});
