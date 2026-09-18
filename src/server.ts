import express, { type Express, type Request, type Response } from 'express';
import type { Config } from './config.js';
import { log } from './logger.js';
import { verifyWebhook, SIGNATURE_HEADER, TIMESTAMP_HEADER } from './lawmatics/signature.js';
import { webhookEnvelopeSchema } from './lawmatics/types.js';
import { RetryQueue } from './queue/queue.js';
import type { SyncJob } from './pipeline/handler.js';
import type { Store } from './store/store.js';

export interface ServerDeps {
  cfg: Config;
  queue: RetryQueue<SyncJob>;
  store: Store;
}

const metrics = {
  received: 0,
  rejected: 0,
  duplicate: 0,
  enqueued: 0,
};

export function getMetrics() {
  return { ...metrics };
}

export function resetMetrics(): void {
  metrics.received = 0;
  metrics.rejected = 0;
  metrics.duplicate = 0;
  metrics.enqueued = 0;
}

export function createServer({ cfg, queue, store }: ServerDeps): Express {
  const app = express();
  app.disable('x-powered-by');

  // The raw body is required for signature verification -- Express must not
  // parse and re-serialise it, or the HMAC will never match.
  app.use('/webhooks/lawmatics', express.raw({ type: '*/*', limit: '2mb' }));

  app.get('/healthz', (_req: Request, res: Response) => {
    res.json({ status: 'ok', eveMode: cfg.EVE_MODE, queueDepth: queue.depth, ...store.stats() });
  });

  app.get('/metrics', (_req: Request, res: Response) => {
    res.json({ ...getMetrics(), queueDepth: queue.depth, ...store.stats() });
  });

  app.post('/webhooks/lawmatics', (req: Request, res: Response) => {
    metrics.received += 1;

    const rawBody: Buffer = Buffer.isBuffer(req.body) ? req.body : Buffer.from('');

    const verification = verifyWebhook({
      rawBody,
      signatureHeader: header(req, SIGNATURE_HEADER),
      timestampHeader: header(req, TIMESTAMP_HEADER),
      secret: cfg.LAWMATICS_WEBHOOK_SECRET,
      toleranceSeconds: cfg.LAWMATICS_WEBHOOK_TOLERANCE_SECONDS,
    });

    if (!verification.ok) {
      metrics.rejected += 1;
      log.warn('rejected webhook', { reason: verification.reason, ip: req.ip });
      res.status(401).json({ error: 'invalid_signature', reason: verification.reason });
      return;
    }

    let parsedBody: unknown;
    try {
      parsedBody = JSON.parse(rawBody.toString('utf8'));
    } catch {
      metrics.rejected += 1;
      res.status(400).json({ error: 'invalid_json' });
      return;
    }

    const envelope = webhookEnvelopeSchema.safeParse(parsedBody);
    if (!envelope.success) {
      metrics.rejected += 1;
      log.warn('malformed webhook envelope', {
        issues: envelope.error.issues.map((i) => i.path.join('.')),
      });
      // 400, not 500: Lawmatics retrying will not make the body valid.
      res.status(400).json({ error: 'invalid_envelope' });
      return;
    }

    // Dedupe before enqueueing so a Lawmatics retry of an event we already
    // accepted does not queue a second sync.
    if (!store.markEventSeen(envelope.data.event_id)) {
      metrics.duplicate += 1;
      log.info('duplicate delivery ignored', { eventId: envelope.data.event_id });
      res.status(200).json({ status: 'duplicate' });
      return;
    }

    queue.enqueue(envelope.data.event_id, { envelope: envelope.data, receivedAt: Date.now() });
    metrics.enqueued += 1;

    log.info('webhook accepted', {
      eventId: envelope.data.event_id,
      eventType: envelope.data.event_type,
      queueDepth: queue.depth,
    });

    // Ack immediately; the sync happens on the queue. Anything slower risks
    // Lawmatics timing out and redelivering while we are still working.
    res.status(202).json({ status: 'accepted', eventId: envelope.data.event_id });
  });

  app.use((_req: Request, res: Response) => {
    res.status(404).json({ error: 'not_found' });
  });

  return app;
}

function header(req: Request, name: string): string | undefined {
  const value = req.headers[name];
  return Array.isArray(value) ? value[0] : value;
}
