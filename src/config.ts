import { z } from 'zod';

/**
 * All runtime configuration, validated at boot so a misconfigured deploy fails
 * immediately instead of at the first webhook delivery.
 */

const csv = (fallback: string) =>
  z
    .string()
    .default(fallback)
    .transform((s) =>
      s
        .split(',')
        .map((v) => v.trim().toLowerCase())
        .filter(Boolean),
    );

const schema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.coerce.number().int().positive().default(3000),
  LOG_LEVEL: z.enum(['debug', 'info', 'warn', 'error']).default('info'),

  // --- Lawmatics: inbound webhooks -----------------------------------------
  // Signing secret from the Lawmatics dashboard webhook config (whsec_...).
  LAWMATICS_WEBHOOK_SECRET: z.string().min(1),
  // Reject deliveries whose signed timestamp is older than this (replay guard).
  LAWMATICS_WEBHOOK_TOLERANCE_SECONDS: z.coerce.number().int().positive().default(300),

  // --- Lawmatics: outbound REST API ----------------------------------------
  LAWMATICS_API_BASE_URL: z.string().url().default('https://api.lawmatics.com'),
  LAWMATICS_CLIENT_ID: z.string().optional(),
  LAWMATICS_CLIENT_SECRET: z.string().optional(),
  // Long-lived refresh token obtained once via the OAuth authorization-code flow.
  LAWMATICS_REFRESH_TOKEN: z.string().optional(),
  // Escape hatch: a pre-issued access token, for local testing.
  LAWMATICS_ACCESS_TOKEN: z.string().optional(),

  // --- Conversion detection -------------------------------------------------
  // Matter/prospect statuses that mean "this lead became a client".
  CONVERSION_STATUSES: csv('hired,signed,client,retained,converted'),
  // Sub-statuses that must never sync even if the status matches.
  CONVERSION_EXCLUDED_SUBSTATUSES: csv(''),

  // --- Eve: outbound --------------------------------------------------------
  // 'http' talks to a real Eve API; 'mock' logs the payload and returns a stub id.
  EVE_MODE: z.enum(['http', 'mock']).default('mock'),
  EVE_API_BASE_URL: z.string().url().optional(),
  EVE_CREATE_CLIENT_PATH: z.string().default('/v1/clients'),
  EVE_AUTH_SCHEME: z.enum(['bearer', 'header', 'basic']).default('bearer'),
  EVE_API_KEY: z.string().optional(),
  // Header name used when EVE_AUTH_SCHEME=header.
  EVE_API_KEY_HEADER: z.string().default('X-Api-Key'),
  EVE_FIRM_ID: z.string().optional(),
  EVE_TIMEOUT_MS: z.coerce.number().int().positive().default(15_000),

  // --- Delivery -------------------------------------------------------------
  QUEUE_MAX_ATTEMPTS: z.coerce.number().int().positive().default(6),
  QUEUE_BASE_DELAY_MS: z.coerce.number().int().positive().default(1_000),
  QUEUE_MAX_DELAY_MS: z.coerce.number().int().positive().default(60_000),
  // Where the dedupe/idempotency state and dead-letter records live.
  STATE_DIR: z.string().default('./data'),
});

export type Config = z.infer<typeof schema>;

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  const parsed = schema.safeParse(env);
  if (!parsed.success) {
    const detail = parsed.error.issues.map((i) => `  ${i.path.join('.')}: ${i.message}`).join('\n');
    throw new Error(`Invalid configuration:\n${detail}`);
  }
  const cfg = parsed.data;

  if (cfg.EVE_MODE === 'http') {
    if (!cfg.EVE_API_BASE_URL) throw new Error('EVE_API_BASE_URL is required when EVE_MODE=http');
    if (!cfg.EVE_API_KEY) throw new Error('EVE_API_KEY is required when EVE_MODE=http');
  }
  const hasOauth = cfg.LAWMATICS_CLIENT_ID && cfg.LAWMATICS_CLIENT_SECRET && cfg.LAWMATICS_REFRESH_TOKEN;
  if (!hasOauth && !cfg.LAWMATICS_ACCESS_TOKEN) {
    throw new Error(
      'Lawmatics credentials missing: set LAWMATICS_CLIENT_ID + LAWMATICS_CLIENT_SECRET + ' +
        'LAWMATICS_REFRESH_TOKEN, or LAWMATICS_ACCESS_TOKEN for local testing',
    );
  }
  return cfg;
}
