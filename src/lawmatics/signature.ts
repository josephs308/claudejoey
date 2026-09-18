import { createHmac, timingSafeEqual } from 'node:crypto';

/**
 * Lawmatics signs outbound webhooks as:
 *   signed_payload = "<X-Lawmatics-Timestamp>.<raw_request_body>"
 *   signature      = "sha256=" + hex(HMAC_SHA256(secret, signed_payload))
 *
 * The secret is the full `whsec_...` string. The body MUST be the raw bytes as
 * received -- parsing and re-serialising JSON changes key order and whitespace
 * and will produce a different digest.
 */

export const SIGNATURE_HEADER = 'x-lawmatics-signature';
export const TIMESTAMP_HEADER = 'x-lawmatics-timestamp';

export type VerifyResult = { ok: true } | { ok: false; reason: string };

export interface VerifyOptions {
  rawBody: Buffer | string;
  signatureHeader: string | undefined;
  timestampHeader: string | undefined;
  secret: string;
  toleranceSeconds: number;
  /** Injectable for tests; seconds since epoch. */
  now?: () => number;
}

export function computeSignature(secret: string, timestamp: string, rawBody: Buffer | string): string {
  const body = Buffer.isBuffer(rawBody) ? rawBody : Buffer.from(rawBody, 'utf8');
  const signedPayload = Buffer.concat([Buffer.from(`${timestamp}.`, 'utf8'), body]);
  return 'sha256=' + createHmac('sha256', secret).update(signedPayload).digest('hex');
}

/** Constant-time compare that tolerates unequal lengths without throwing. */
function safeEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a, 'utf8');
  const bufB = Buffer.from(b, 'utf8');
  if (bufA.length !== bufB.length) return false;
  return timingSafeEqual(bufA, bufB);
}

export function verifyWebhook(opts: VerifyOptions): VerifyResult {
  const { rawBody, signatureHeader, timestampHeader, secret, toleranceSeconds } = opts;
  const now = opts.now ?? (() => Math.floor(Date.now() / 1000));

  if (!signatureHeader) return { ok: false, reason: 'missing_signature_header' };
  if (!timestampHeader) return { ok: false, reason: 'missing_timestamp_header' };

  // Timestamp must be a plain Unix epoch integer.
  if (!/^\d+$/.test(timestampHeader.trim())) return { ok: false, reason: 'malformed_timestamp' };
  const ts = Number(timestampHeader.trim());
  if (!Number.isSafeInteger(ts)) return { ok: false, reason: 'malformed_timestamp' };

  // Replay guard. A future-dated timestamp beyond tolerance is equally suspect.
  const skew = now() - ts;
  if (skew > toleranceSeconds) return { ok: false, reason: 'timestamp_too_old' };
  if (skew < -toleranceSeconds) return { ok: false, reason: 'timestamp_in_future' };

  const expected = computeSignature(secret, timestampHeader.trim(), rawBody);

  // Some senders present a comma-separated list; accept a match on any element.
  const candidates = signatureHeader.split(',').map((s) => s.trim()).filter(Boolean);
  for (const candidate of candidates) {
    if (safeEqual(candidate, expected)) return { ok: true };
  }
  return { ok: false, reason: 'signature_mismatch' };
}
