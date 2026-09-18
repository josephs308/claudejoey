import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { handleSyncJob, type SyncDeps } from '../src/pipeline/handler.js';
import { webhookEnvelopeSchema } from '../src/lawmatics/types.js';
import { LawmaticsClient, LawmaticsPermanentError, LawmaticsTransientError } from '../src/lawmatics/client.js';
import { MockEveClient, EvePermanentError, EveTransientError, type EveClient } from '../src/eve/client.js';
import { PermanentJobError } from '../src/queue/queue.js';
import { Store } from '../src/store/store.js';
import { testConfig, makeProspect } from './helpers.js';

function envelope(overrides: Record<string, unknown> = {}) {
  return webhookEnvelopeSchema.parse({
    event_id: 'evt_conv_1',
    firm_id: 'firm_1',
    event_type: 'matter_status_changed',
    timestamp: 1_750_000_000,
    data: { prospect_id: 4242, new_status: 'Hired' },
    ...overrides,
  });
}

describe('handleSyncJob', () => {
  let dir: string;
  let store: Store;
  let eve: MockEveClient;
  let deps: SyncDeps;
  let getProspect: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    dir = mkdtempSync(join(tmpdir(), 'connector-test-'));
    const cfg = testConfig({ STATE_DIR: dir });
    store = new Store(dir);
    eve = new MockEveClient(cfg);
    getProspect = vi.fn().mockResolvedValue(makeProspect());
    const lawmatics = { getProspect } as unknown as LawmaticsClient;
    deps = { cfg, lawmatics, eve, store };
  });

  afterEach(() => rmSync(dir, { recursive: true, force: true }));

  const job = (e = envelope()) => ({ envelope: e, receivedAt: Date.now() });

  it('syncs a converted lead into Eve', async () => {
    const result = await handleSyncJob(job(), deps);

    expect(result).toEqual({ status: 'synced', prospectId: '4242', eveClientId: 'mock-lawmatics-prospect-4242' });
    expect(eve.sent).toHaveLength(1);
    expect(eve.sent[0]!.payload.external_id).toBe('lawmatics:4242');
    expect(eve.sent[0]!.idempotencyKey).toBe('lawmatics-prospect-4242');
  });

  it('records the link so a redelivery does not create a duplicate', async () => {
    await handleSyncJob(job(), deps);
    const second = await handleSyncJob(job(envelope({ event_id: 'evt_conv_2' })), deps);

    expect(second.status).toBe('already_synced');
    expect(eve.sent).toHaveLength(1); // Eve was called exactly once
  });

  it('remembers the link across a restart', async () => {
    await handleSyncJob(job(), deps);

    const revived = { ...deps, store: new Store(dir) }; // fresh process, same state dir
    const result = await handleSyncJob(job(envelope({ event_id: 'evt_conv_3' })), revived);

    expect(result.status).toBe('already_synced');
    expect(eve.sent).toHaveLength(1);
  });

  it('ignores an event type that cannot carry a conversion', async () => {
    const result = await handleSyncJob(job(envelope({ event_type: 'invoice_paid' })), deps);

    expect(result).toEqual({ status: 'skipped', reason: 'event_type_not_convertible:invoice_paid' });
    expect(getProspect).not.toHaveBeenCalled();
    expect(eve.sent).toHaveLength(0);
  });

  it('does not sync a lead that has not converted', async () => {
    getProspect.mockResolvedValue(makeProspect({ status: { name: 'New Lead' } }));
    const result = await handleSyncJob(job(), deps);

    expect(result).toEqual({ status: 'skipped', reason: 'status_not_a_conversion:new lead' });
    expect(eve.sent).toHaveLength(0);
  });

  it('judges conversion on the fetched record, not the webhook body', async () => {
    // Webhook claims "Hired", but the matter has since moved to "Lost".
    getProspect.mockResolvedValue(makeProspect({ status: { name: 'Lost' } }));
    const result = await handleSyncJob(job(envelope({ data: { prospect_id: 4242, new_status: 'Hired' } })), deps);

    expect(result.status).toBe('skipped');
    expect(eve.sent).toHaveLength(0);
  });

  it('does not record a sync for a skipped lead', async () => {
    getProspect.mockResolvedValue(makeProspect({ status: { name: 'New Lead' } }));
    await handleSyncJob(job(), deps);
    expect(store.getSyncedProspect('4242')).toBeNull();

    // A later genuine conversion must still go through.
    getProspect.mockResolvedValue(makeProspect());
    const result = await handleSyncJob(job(envelope({ event_id: 'evt_later' })), deps);
    expect(result.status).toBe('synced');
  });

  it('permanently fails an event with no prospect id', async () => {
    await expect(handleSyncJob(job(envelope({ data: { foo: 'bar' } })), deps)).rejects.toBeInstanceOf(
      PermanentJobError,
    );
  });

  it('permanently fails when Lawmatics rejects the lookup', async () => {
    getProspect.mockRejectedValue(new LawmaticsPermanentError('not found', 404));
    await expect(handleSyncJob(job(), deps)).rejects.toBeInstanceOf(PermanentJobError);
  });

  it('propagates a transient Lawmatics error so the queue retries', async () => {
    getProspect.mockRejectedValue(new LawmaticsTransientError('rate limited', 429));
    await expect(handleSyncJob(job(), deps)).rejects.toBeInstanceOf(LawmaticsTransientError);
  });

  it('propagates a transient Eve error so the queue retries', async () => {
    const failing: EveClient = { createClient: vi.fn().mockRejectedValue(new EveTransientError('eve 503', 503)) };
    await expect(handleSyncJob(job(), { ...deps, eve: failing })).rejects.toBeInstanceOf(EveTransientError);
    expect(store.getSyncedProspect('4242')).toBeNull(); // nothing recorded on failure
  });

  it('permanently fails when Eve rejects the payload', async () => {
    const failing: EveClient = { createClient: vi.fn().mockRejectedValue(new EvePermanentError('bad request', 400)) };
    await expect(handleSyncJob(job(), { ...deps, eve: failing })).rejects.toBeInstanceOf(PermanentJobError);
  });

  it('treats an Eve 409 as an existing client', async () => {
    const existing: EveClient = {
      createClient: vi.fn().mockResolvedValue({ eveClientId: 'eve_777', alreadyExisted: true }),
    };
    const result = await handleSyncJob(job(), { ...deps, eve: existing });

    expect(result).toEqual({ status: 'already_synced', prospectId: '4242', eveClientId: 'eve_777' });
    expect(store.getSyncedProspect('4242')?.eveClientId).toBe('eve_777');
  });
});
