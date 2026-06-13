import { config } from './config.js';
import type { IncomingReply } from './types.js';

/** Minimal newline -> <br> conversion so the HTML body matches the text body. */
function toHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '<br>\n');
}

/**
 * Send a threaded reply via Instantly's v2 API.
 * POST /api/v2/emails/reply with { eaccount, reply_to_uuid, subject, body }.
 */
export async function sendReply(
  reply: IncomingReply,
  subject: string,
  body: string,
): Promise<void> {
  const url = config.instantly.baseUrl + config.instantly.replyPath;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${config.instantly.apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      eaccount: reply.eaccount,
      reply_to_uuid: reply.replyToUuid,
      subject,
      body: { html: toHtml(body), text: body },
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`Instantly reply failed (${res.status}): ${detail}`);
  }
}
