import { describe, it, expect } from 'vitest';
import { computeSignature, verifyWebhook } from '../src/lawmatics/signature.js';

const SECRET = 'whsec_test_abc123';
const NOW = 1_750_000_000;
const now = () => NOW;

function sign(body: string, ts = String(NOW)) {
  return { signatureHeader: computeSignature(SECRET, ts, body), timestampHeader: ts };
}

const base = { secret: SECRET, toleranceSeconds: 300, now };

describe('verifyWebhook', () => {
  const body = JSON.stringify({ event_id: 'evt_1', event_type: 'matter_status_changed' });

  it('accepts a correctly signed payload', () => {
    expect(verifyWebhook({ rawBody: body, ...sign(body), ...base })).toEqual({ ok: true });
  });

  it('accepts a Buffer body identically to a string body', () => {
    const signed = sign(body);
    expect(verifyWebhook({ rawBody: Buffer.from(body, 'utf8'), ...signed, ...base })).toEqual({ ok: true });
  });

  it('rejects a tampered body', () => {
    const signed = sign(body);
    const tampered = body.replace('evt_1', 'evt_2');
    expect(verifyWebhook({ rawBody: tampered, ...signed, ...base })).toEqual({
      ok: false,
      reason: 'signature_mismatch',
    });
  });

  it('rejects a body that was re-serialised after parsing', () => {
    // Round-tripping JSON changes whitespace/key order, which breaks the HMAC.
    const signed = sign(body);
    const reserialised = JSON.stringify(JSON.parse(body), null, 2);
    expect(verifyWebhook({ rawBody: reserialised, ...signed, ...base }).ok).toBe(false);
  });

  it('rejects a signature computed with the wrong secret', () => {
    const signed = { signatureHeader: computeSignature('whsec_wrong', String(NOW), body), timestampHeader: String(NOW) };
    expect(verifyWebhook({ rawBody: body, ...signed, ...base })).toEqual({
      ok: false,
      reason: 'signature_mismatch',
    });
  });

  it('rejects a replayed delivery outside the tolerance window', () => {
    const oldTs = String(NOW - 3600);
    expect(verifyWebhook({ rawBody: body, ...sign(body, oldTs), ...base })).toEqual({
      ok: false,
      reason: 'timestamp_too_old',
    });
  });

  it('rejects a future-dated timestamp', () => {
    const futureTs = String(NOW + 3600);
    expect(verifyWebhook({ rawBody: body, ...sign(body, futureTs), ...base })).toEqual({
      ok: false,
      reason: 'timestamp_in_future',
    });
  });

  it('accepts a timestamp inside the tolerance window', () => {
    const recentTs = String(NOW - 120);
    expect(verifyWebhook({ rawBody: body, ...sign(body, recentTs), ...base })).toEqual({ ok: true });
  });

  it.each([
    ['missing signature', { signatureHeader: undefined, timestampHeader: String(NOW) }, 'missing_signature_header'],
    ['missing timestamp', { signatureHeader: 'sha256=abc', timestampHeader: undefined }, 'missing_timestamp_header'],
    ['non-numeric timestamp', { signatureHeader: 'sha256=abc', timestampHeader: 'not-a-number' }, 'malformed_timestamp'],
  ])('rejects %s', (_label, headers, reason) => {
    expect(verifyWebhook({ rawBody: body, ...headers, ...base })).toEqual({ ok: false, reason });
  });

  it('does not throw when the signature length differs from the expected digest', () => {
    expect(() =>
      verifyWebhook({ rawBody: body, signatureHeader: 'sha256=short', timestampHeader: String(NOW), ...base }),
    ).not.toThrow();
  });

  it('produces the documented sha256= hex format', () => {
    expect(computeSignature(SECRET, String(NOW), body)).toMatch(/^sha256=[0-9a-f]{64}$/);
  });
});
