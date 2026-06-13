import type { IncomingReply } from './types.js';

/** Pick the first defined, non-empty value from a list of candidate keys. */
function pick(obj: Record<string, unknown>, keys: string[]): string | undefined {
  for (const key of keys) {
    const value = obj[key];
    if (typeof value === 'string' && value.trim()) return value;
  }
  return undefined;
}

/**
 * Normalize an Instantly `reply_received` webhook payload into IncomingReply.
 *
 * Instantly's payload field names have shifted across versions, so we probe a
 * few likely keys for each field. If your payload uses different names, log the
 * raw body (the server does this) and adjust the candidate lists below.
 *
 * Returns null if we can't extract the essentials (inbox, reply UUID, sender).
 */
export function mapWebhookPayload(raw: unknown): IncomingReply | null {
  if (!raw || typeof raw !== 'object') return null;
  const p = raw as Record<string, unknown>;

  // Some webhooks nest the meaningful fields under `data` or `payload`.
  const inner =
    (p.data as Record<string, unknown> | undefined) ??
    (p.payload as Record<string, unknown> | undefined) ??
    p;

  const eaccount = pick(inner, ['eaccount', 'email_account', 'inbox', 'from_email']);
  const replyToUuid = pick(inner, [
    'reply_to_uuid',
    'message_uuid',
    'email_uuid',
    'uuid',
    'message_id',
    'thread_id',
  ]);
  const leadEmail = pick(inner, ['lead_email', 'from', 'sender_email', 'email']);

  if (!eaccount || !replyToUuid || !leadEmail) return null;

  const body =
    pick(inner, ['reply_text', 'reply_text_snippet', 'text', 'body_text', 'message']) ?? '';

  return {
    eaccount,
    replyToUuid,
    leadEmail,
    leadName: pick(inner, ['lead_name', 'first_name', 'sender_name', 'name']),
    campaignId: pick(inner, ['campaign_id', 'campaign']),
    subject: pick(inner, ['subject', 'reply_subject', 'email_subject']) ?? '(no subject)',
    body,
    threadText: pick(inner, ['thread', 'thread_text', 'conversation']),
    raw,
  };
}
