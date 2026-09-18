import { loadConfig } from './config.js';
import { log, errField } from './logger.js';
import { LawmaticsClient } from './lawmatics/client.js';
import { createEveClient } from './eve/client.js';
import { Store } from './store/store.js';
import { RetryQueue } from './queue/queue.js';
import { makeJobHandler, type SyncJob } from './pipeline/handler.js';
import { createServer } from './server.js';

function main(): void {
  const cfg = loadConfig();
  const store = new Store(cfg.STATE_DIR);
  const lawmatics = new LawmaticsClient(cfg);
  const eve = createEveClient(cfg);

  const queue: RetryQueue<SyncJob> = new RetryQueue<SyncJob>(
    makeJobHandler({ cfg, lawmatics, eve, store }),
    {
      maxAttempts: cfg.QUEUE_MAX_ATTEMPTS,
      baseDelayMs: cfg.QUEUE_BASE_DELAY_MS,
      maxDelayMs: cfg.QUEUE_MAX_DELAY_MS,
    },
    (job, err) => {
      store.deadLetter({
        jobId: job.id,
        attempts: job.attempts,
        envelope: job.payload.envelope,
        ...errField(err),
      });
    },
  );

  const app = createServer({ cfg, queue, store });
  const server = app.listen(cfg.PORT, () => {
    log.info('connector listening', {
      port: cfg.PORT,
      eveMode: cfg.EVE_MODE,
      conversionStatuses: cfg.CONVERSION_STATUSES,
    });
    if (cfg.EVE_MODE === 'mock') {
      log.warn('EVE_MODE=mock -- clients are logged, not delivered to Eve');
    }
  });

  const shutdown = (signal: string) => {
    log.info('shutting down', { signal, queueDepth: queue.depth });
    server.close(() => {
      queue.stop();
      store.flush();
      process.exit(0);
    });
    // Do not hang forever on open keep-alive connections.
    setTimeout(() => process.exit(1), 10_000).unref();
  };

  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));
}

try {
  main();
} catch (err) {
  log.error('failed to start', errField(err));
  process.exit(1);
}
