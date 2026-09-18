import type { Config } from '../config.js';
import { associationName, type LawmaticsProspect, type WebhookEnvelope } from '../lawmatics/types.js';

/**
 * Decides whether a webhook represents "this lead just became a client".
 *
 * Lawmatics has no dedicated "converted" event; conversion shows up as a matter
 * status change into one of the firm's client statuses. Which statuses count is
 * firm-specific, so it is configuration (CONVERSION_STATUSES), not a constant.
 */

/** Event types that can carry a conversion. Anything else is ignored outright. */
const CONVERTIBLE_EVENTS = new Set([
  'matter_status_changed',
  'matter_updated',
  'matter_created',
  'prospect_status_changed',
  'prospect_updated',
  'prospect_created',
]);

export type ConversionDecision =
  | { sync: true; status: string; prospectId: string }
  | { sync: false; reason: string };

export function isConvertibleEvent(eventType: string): boolean {
  return CONVERTIBLE_EVENTS.has(eventType.toLowerCase());
}

/** Pulls the matter/prospect id out of an event payload, tolerating shape drift. */
export function extractProspectId(envelope: WebhookEnvelope): string | null {
  const data = envelope.data as Record<string, unknown>;
  const candidates = [
    data.prospect_id,
    data.matter_id,
    data.id,
    (data.prospect as Record<string, unknown> | undefined)?.id,
    (data.matter as Record<string, unknown> | undefined)?.id,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim();
    if (typeof candidate === 'number' && Number.isFinite(candidate)) return String(candidate);
  }
  return null;
}

/**
 * Applies the conversion rule against the authoritative prospect record.
 *
 * We deliberately judge on the record fetched from the API rather than on the
 * webhook body: the webhook can be stale by the time we process it, and syncing
 * a client whose status has since moved back to "lost" is worse than missing one.
 */
export function decideConversion(prospect: LawmaticsProspect, cfg: Config): ConversionDecision {
  const status = associationName(prospect.status);
  if (!status) return { sync: false, reason: 'prospect_has_no_status' };

  const normalised = status.toLowerCase();
  if (!cfg.CONVERSION_STATUSES.includes(normalised)) {
    return { sync: false, reason: `status_not_a_conversion:${normalised}` };
  }

  const subStatus = associationName(prospect.sub_status);
  if (subStatus && cfg.CONVERSION_EXCLUDED_SUBSTATUSES.includes(subStatus.toLowerCase())) {
    return { sync: false, reason: `sub_status_excluded:${subStatus.toLowerCase()}` };
  }

  return { sync: true, status, prospectId: String(prospect.id) };
}
