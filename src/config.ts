import 'dotenv/config';

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required env var: ${name} (see .env.example)`);
  }
  return value;
}

export const config = {
  port: Number(process.env.PORT ?? 3000),
  dataDir: process.env.DATA_DIR ?? './data',

  anthropic: {
    apiKey: required('ANTHROPIC_API_KEY'),
    // Default to the most capable model. For high reply volume you can switch
    // to claude-sonnet-4-6 (cheaper/faster) via the CLAUDE_MODEL env var.
    model: process.env.CLAUDE_MODEL ?? 'claude-opus-4-8',
  },

  instantly: {
    apiKey: required('INSTANTLY_API_KEY'),
    baseUrl: process.env.INSTANTLY_BASE_URL ?? 'https://api.instantly.ai/api/v2',
    // Endpoint paths live here so they are trivial to correct if the Instantly
    // API shape ever drifts from what this was built against.
    replyPath: '/emails/reply',
  },

  // Optional shared secret to verify inbound webhooks. Set the same value in the
  // Instantly webhook config. Leave unset to skip verification (dev only).
  webhookSecret: process.env.INSTANTLY_WEBHOOK_SECRET || undefined,

  // Bearer token protecting the approval API. Leave unset to disable the guard
  // (dev only — never expose /drafts publicly without a token).
  approvalApiToken: process.env.APPROVAL_API_TOKEN || undefined,
};
