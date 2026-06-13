import express, { type NextFunction, type Request, type Response } from 'express';
import { config } from './config.js';
import { loadBusinessContext } from './context.js';
import { analyzeReply } from './analyzer.js';
import { mapWebhookPayload } from './webhook.js';
import { sendReply } from './instantly.js';
import { createDraft, getDraft, listDrafts, updateDraft } from './store.js';
import type { DraftStatus } from './types.js';

export function createServer() {
  const app = express();
  app.use(express.json({ limit: '2mb' }));

  app.get('/health', (_req, res) => res.json({ ok: true }));

  // --- Inbound: Instantly reply_received webhook ---------------------------
  app.post('/webhooks/instantly', async (req, res) => {
    // Verify shared secret if configured (query param or header).
    if (config.webhookSecret) {
      const provided = req.query.secret ?? req.header('x-webhook-secret');
      if (provided !== config.webhookSecret) {
        return res.status(401).json({ error: 'invalid webhook secret' });
      }
    }

    // Acknowledge fast so Instantly doesn't retry; process out of band.
    res.status(202).json({ received: true });

    try {
      const reply = mapWebhookPayload(req.body);
      if (!reply) {
        console.warn('[webhook] could not map payload; raw:', JSON.stringify(req.body));
        return;
      }
      const ctx = await loadBusinessContext();
      const analysis = await analyzeReply(reply, ctx);
      const draft = await createDraft(reply, analysis);
      console.log(
        `[webhook] ${reply.leadEmail} -> intent=${analysis.intent} ` +
          `risk=${analysis.risk} status=${draft.status} id=${draft.id}`,
      );
    } catch (err) {
      console.error('[webhook] processing failed:', (err as Error).message);
    }
  });

  // --- Approval API (protect with a bearer token) --------------------------
  const guard = (req: Request, res: Response, next: NextFunction) => {
    if (!config.approvalApiToken) return next(); // dev: no token configured
    const auth = req.header('authorization') ?? '';
    if (auth === `Bearer ${config.approvalApiToken}`) return next();
    return res.status(401).json({ error: 'unauthorized' });
  };

  // List drafts, optionally ?status=pending
  app.get('/drafts', guard, async (req, res) => {
    const status = req.query.status as DraftStatus | undefined;
    res.json(await listDrafts(status));
  });

  app.get('/drafts/:id', guard, async (req, res) => {
    const draft = await getDraft(req.params.id);
    if (!draft) return res.status(404).json({ error: 'not found' });
    res.json(draft);
  });

  // Approve (optionally with an edited subject/body), then send via Instantly.
  app.post('/drafts/:id/approve', guard, async (req, res) => {
    const draft = await getDraft(req.params.id);
    if (!draft) return res.status(404).json({ error: 'not found' });
    if (draft.status === 'sent') {
      return res.status(409).json({ error: 'already sent' });
    }

    const subject = (req.body?.subject as string) ?? draft.analysis.draftSubject;
    const body = (req.body?.body as string) ?? draft.analysis.draftBody;
    if (!body?.trim()) {
      return res.status(400).json({ error: 'empty body — nothing to send' });
    }

    try {
      await sendReply(draft.reply, subject, body);
      const updated = await updateDraft(draft.id, { status: 'sent', sentBody: body });
      res.json(updated);
    } catch (err) {
      const message = (err as Error).message;
      await updateDraft(draft.id, { status: 'failed', error: message });
      res.status(502).json({ error: message });
    }
  });

  app.post('/drafts/:id/reject', guard, async (req, res) => {
    const updated = await updateDraft(req.params.id, { status: 'rejected' });
    if (!updated) return res.status(404).json({ error: 'not found' });
    res.json(updated);
  });

  return app;
}
