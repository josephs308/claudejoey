import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { AddressInfo } from 'node:net';
import type { Server } from 'node:http';
import { createServer, resetMetrics, getMetrics } from '../src/server.js';
import { computeSignature } from '../src/lawmatics/signature.js';
import { RetryQueue } from '../src/queue/queue.js';
import { Store } from '../src/store/store.js';
import { MockEveClient } from '../src/eve/client.js';
import { makeJobHandler, type SyncJob } from '../src/pipeline/handler.js';
import type { LawmaticsClient } from '../src/lawmatics/client.js';
import { testConfig, makeProspect } from './helpers.js';

const SECRET = 'whsec_test_abc123';

describe('POST /webhooks/lawmatics', () => {
  let dir: string;
  let server: Server;
  let baseUrl: string;
  let queue: RetryQueue<SyncJob>;
  let eve: MockEveClient;
  let store: Store;
  let deadLettered: unknown[];
  // When set, the Lawmatics lookup blocks until this resolves, letting a test
  // hold a job mid-flight and observe what the HTTP layer did meanwhile.
  let gate: { promise: Promise<void>; release: () => void } | null;

  beforeEach(async () => {
    resetMetrics();
    dir = mkdtempSync(join(tmpdir(), 'connector-http-'));
    const cfg = testConfig({ STATE_DIR: dir });
    store = new Store(dir);
    eve = new MockEveClient(cfg);
    deadLettered = [];
    gate = null;
    const lawmatics = {
      getProspect: vi.fn(async () => {
        if (gate) await gate.promise;
        return makeProspect();
      }),
    } as unknown as LawmaticsClient;

    queue = new RetryQueue<SyncJob>(
      makeJobHandler({ cfg, lawmatics, eve, store }),
      { maxAttempts: 2, baseDelayMs: 1, maxDelayMs: 5 },
      (job, err) => deadLettered.push({ job, err }),
    );

    const app = createServer({ cfg, queue, store });
    await new Promise<void>((resolve) => {
      server = app.listen(0, resolve);
    });
    baseUrl = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
  });

  afterEach(async () => {
    queue.stop();
    await new Promise<void>((resolve) => server.close(() => resolve()));
    rmSync(dir, { recursive: true, force: true });
  });

  function post(body: string, opts: { signature?: string; timestamp?: string } = {}) {
    const timestamp = opts.timestamp ?? String(Math.floor(Date.now() / 1000));
    const signature = opts.signature ?? computeSignature(SECRET, timestamp, body);
    return fetch(`${baseUrl}/webhooks/lawmatics`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-lawmatics-signature': signature,
        'x-lawmatics-timestamp': timestamp,
      },
      body,
    });
  }

  const conversionBody = (eventId = 'evt_1') =>
    JSON.stringify({
      event_id: eventId,
      firm_id: 'firm_1',
      event_type: 'matter_status_changed',
      version: '1',
      timestamp: Math.floor(Date.now() / 1000),
      data: { prospect_id: 4242, new_status: 'Hired' },
    });

  it('accepts a signed conversion and syncs it to Eve', async () => {
    const res = await post(conversionBody());
    expect(res.status).toBe(202);
    await expect(res.json()).resolves.toMatchObject({ status: 'accepted', eventId: 'evt_1' });

    await queue.idle();
    expect(eve.sent).toHaveLength(1);
    expect(eve.sent[0]!.payload.external_id).toBe('lawmatics:4242');
  });

  it('acks before the sync completes', async () => {
    // Hold the job inside the Lawmatics lookup so the sync provably cannot have
    // finished when the HTTP response arrives.
    let release!: () => void;
    const promise = new Promise<void>((resolve) => {
      release = resolve;
    });
    gate = { promise, release };

    const res = await post(conversionBody());

    expect(res.status).toBe(202);
    expect(eve.sent).toHaveLength(0); // still blocked upstream of Eve

    release();
    await queue.idle();
    expect(eve.sent).toHaveLength(1);
  });

  it('rejects an unsigned request', async () => {
    const res = await fetch(`${baseUrl}/webhooks/lawmatics`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: conversionBody(),
    });
    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toMatchObject({ reason: 'missing_signature_header' });
    expect(getMetrics().rejected).toBe(1);
  });

  it('rejects a forged signature', async () => {
    const res = await post(conversionBody(), { signature: 'sha256=' + '0'.repeat(64) });
    expect(res.status).toBe(401);
    expect(eve.sent).toHaveLength(0);
  });

  it('rejects a body modified after signing', async () => {
    const body = conversionBody();
    const timestamp = String(Math.floor(Date.now() / 1000));
    const signature = computeSignature(SECRET, timestamp, body);
    const tampered = body.replace('4242', '9999');

    const res = await post(tampered, { signature, timestamp });
    expect(res.status).toBe(401);
    expect(eve.sent).toHaveLength(0);
  });

  it('rejects a replayed old delivery', async () => {
    const oldTimestamp = String(Math.floor(Date.now() / 1000) - 7200);
    const res = await post(conversionBody(), { timestamp: oldTimestamp });
    expect(res.status).toBe(401);
    await expect(res.json()).resolves.toMatchObject({ reason: 'timestamp_too_old' });
  });

  it('returns 400 for a signed but malformed body', async () => {
    const res = await post('{not json');
    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toMatchObject({ error: 'invalid_json' });
  });

  it('returns 400 for a payload missing envelope fields', async () => {
    const res = await post(JSON.stringify({ data: {} }));
    expect(res.status).toBe(400);
    await expect(res.json()).resolves.toMatchObject({ error: 'invalid_envelope' });
  });

  it('ignores a duplicate delivery of the same event id', async () => {
    await post(conversionBody('evt_dup'));
    await queue.idle();

    const second = await post(conversionBody('evt_dup'));
    expect(second.status).toBe(200);
    await expect(second.json()).resolves.toMatchObject({ status: 'duplicate' });

    await queue.idle();
    expect(eve.sent).toHaveLength(1);
    expect(getMetrics().duplicate).toBe(1);
  });

  it('dead-letters an event with no usable prospect id', async () => {
    const body = JSON.stringify({ event_id: 'evt_bad', event_type: 'matter_status_changed', data: {} });
    const res = await post(body);
    expect(res.status).toBe(202); // accepted, then fails on the queue

    await queue.idle();
    expect(deadLettered).toHaveLength(1);
    expect(eve.sent).toHaveLength(0);
  });

  it('exposes health and metrics', async () => {
    await post(conversionBody('evt_metrics'));
    await queue.idle();

    const health = await (await fetch(`${baseUrl}/healthz`)).json();
    expect(health).toMatchObject({ status: 'ok', eveMode: 'mock' });

    const metrics = await (await fetch(`${baseUrl}/metrics`)).json();
    expect(metrics).toMatchObject({ received: 1, enqueued: 1, rejected: 0, syncedProspects: 1 });
  });

  it('404s an unknown path', async () => {
    expect((await fetch(`${baseUrl}/nope`)).status).toBe(404);
  });
});
