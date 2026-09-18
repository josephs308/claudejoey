import type { Config } from '../config.js';
import { log, errField } from '../logger.js';
import { LawmaticsClient, LawmaticsPermanentError } from '../lawmatics/client.js';
import type { WebhookEnvelope } from '../lawmatics/types.js';
import type { EveClient } from '../eve/client.js';
import { EvePermanentError } from '../eve/client.js';
import type { Store } from '../store/store.js';
import { PermanentJobError } from '../queue/queue.js';
import { decideConversion, extractProspectId, isConvertibleEvent } from './conversion.js';
import { toCanonicalClient } from './mapper.js';

export interface SyncJob {
  envelope: WebhookEnvelope;
  receivedAt: number;
}

export type SyncOutcome =
  | { status: 'synced'; prospectId: string; eveClientId: string }
  | { status: 'already_synced'; prospectId: string; eveClientId: string }
  | { status: 'skipped'; reason: string };

export interface SyncDeps {
  cfg: Config;
  lawmatics: LawmaticsClient;
  eve: EveClient;
  store: Store;
}

/**
 * The full lead-to-client flow for one webhook delivery:
 *
 *   1. ignore events that cannot carry a conversion
 *   2. re-fetch the matter from Lawmatics (the webhook body is thin and can be
 *      stale), which is also where custom fields come from
 *   3. apply the firm's conversion rule to the authoritative record
 *   4. map to the canonical shape, then to Eve's payload
 *   5. push to Eve under an idempotency key and record the link
 *
 * Throws PermanentJobError for anything a retry cannot fix; lets transient
 * errors bubble so the queue can back off and try again.
 */
export async function handleSyncJob(job: SyncJob, deps: SyncDeps): Promise<SyncOutcome> {
  const { cfg, lawmatics, eve, store } = deps;
  const { envelope } = job;

  if (!isConvertibleEvent(envelope.event_type)) {
    log.debug('ignoring event type', { eventId: envelope.event_id, eventType: envelope.event_type });
    return { status: 'skipped', reason: `event_type_not_convertible:${envelope.event_type}` };
  }

  const prospectId = extractProspectId(envelope);
  if (!prospectId) {
    // Nothing to fetch and nothing to retry -- the payload is unusable.
    throw new PermanentJobError(`Event ${envelope.event_id} carried no prospect/matter id`);
  }

  let prospect;
  try {
    prospect = await lawmatics.getProspect(prospectId);
  } catch (err) {
    if (err instanceof LawmaticsPermanentError) {
      throw new PermanentJobError(`Cannot load prospect ${prospectId}: ${err.message}`, err);
    }
    throw err; // transient -- let the queue retry
  }

  const decision = decideConversion(prospect, cfg);
  if (!decision.sync) {
    log.info('no sync needed', {
      eventId: envelope.event_id,
      prospectId,
      reason: decision.reason,
    });
    return { status: 'skipped', reason: decision.reason };
  }

  // Guard against duplicate pushes across restarts and redeliveries. Checked
  // after the conversion decision so a skip never writes a sync record.
  const existing = store.getSyncedProspect(prospectId);
  if (existing) {
    log.info('prospect already in eve, skipping', {
      prospectId,
      eveClientId: existing.eveClientId,
    });
    return { status: 'already_synced', prospectId, eveClientId: existing.eveClientId };
  }

  const client = toCanonicalClient(prospect);
  const idempotencyKey = `lawmatics-prospect-${prospectId}`;

  let result;
  try {
    result = await eve.createClient(client, idempotencyKey);
  } catch (err) {
    if (err instanceof EvePermanentError) {
      throw new PermanentJobError(`Eve rejected prospect ${prospectId}: ${err.message}`, err);
    }
    throw err; // transient -- let the queue retry
  }

  store.recordSync(prospectId, result.eveClientId);
  log.info('client synced to eve', {
    eventId: envelope.event_id,
    prospectId,
    eveClientId: result.eveClientId,
    status: decision.status,
    alreadyExisted: result.alreadyExisted,
    latencyMs: Date.now() - job.receivedAt,
  });

  return result.alreadyExisted
    ? { status: 'already_synced', prospectId, eveClientId: result.eveClientId }
    : { status: 'synced', prospectId, eveClientId: result.eveClientId };
}

/** Queue-facing wrapper: runs the flow and swallows the (already logged) result. */
export function makeJobHandler(deps: SyncDeps) {
  return async (payload: SyncJob): Promise<void> => {
    try {
      await handleSyncJob(payload, deps);
    } catch (err) {
      log.debug('sync job raised', { eventId: payload.envelope.event_id, ...errField(err) });
      throw err;
    }
  };
}
