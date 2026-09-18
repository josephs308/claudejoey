import type { Config } from '../config.js';
import { log } from '../logger.js';
import type { CanonicalClient } from '../pipeline/mapper.js';

/**
 * Eve destination adapter.
 *
 * Eve publishes no developer documentation, so the exact endpoint, auth scheme
 * and body shape are configuration rather than hard-coded constants. Everything
 * Eve-specific is confined to this file: when the firm receives Eve's API
 * packet, `buildEvePayload` and the env vars are the only things that change.
 */

export interface EveCreateResult {
  eveClientId: string;
  /** True when Eve reported the record already existed (idempotent replay). */
  alreadyExisted: boolean;
}

export interface EveClient {
  createClient(client: CanonicalClient, idempotencyKey: string): Promise<EveCreateResult>;
}

export class EvePermanentError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'EvePermanentError';
  }
}

export class EveTransientError extends Error {
  constructor(message: string, readonly status?: number, readonly retryAfterMs?: number) {
    super(message);
    this.name = 'EveTransientError';
  }
}

/**
 * Canonical -> Eve request body.
 *
 * ASSUMPTION (unverified against Eve): a flat client record with a nested
 * `matter` object and free-form `metadata`. Adjust to match Eve's real schema.
 */
export function buildEvePayload(client: CanonicalClient, cfg: Config): Record<string, unknown> {
  const primaryPhone = client.phones[0]?.number ?? null;
  return {
    ...(cfg.EVE_FIRM_ID ? { firm_id: cfg.EVE_FIRM_ID } : {}),
    external_id: `${client.sourceSystem}:${client.sourceProspectId}`,
    source: 'lawmatics',
    client: {
      first_name: client.firstName,
      middle_name: client.middleName,
      last_name: client.lastName,
      full_name: client.fullName,
      email: client.email,
      phone: primaryPhone,
      phones: client.phones,
      date_of_birth: client.dateOfBirth,
      address: client.address,
    },
    matter: {
      name: client.matter.name,
      case_number: client.matter.caseNumber,
      practice_area: client.matter.practiceArea,
      status: client.matter.status,
      source: client.matter.source,
      estimated_value: client.matter.estimatedValue,
      opened_at: client.matter.openedAt,
      converted_at: client.matter.convertedAt,
      assigned_to: client.matter.assignedTo,
    },
    metadata: {
      lawmatics_prospect_id: client.sourceProspectId,
      lawmatics_contact_id: client.sourceContactId,
      custom_fields: client.customFields,
    },
  };
}

export class HttpEveClient implements EveClient {
  constructor(
    private readonly cfg: Config,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {}

  private authHeaders(): Record<string, string> {
    const key = this.cfg.EVE_API_KEY ?? '';
    switch (this.cfg.EVE_AUTH_SCHEME) {
      case 'bearer':
        return { authorization: `Bearer ${key}` };
      case 'basic':
        return { authorization: `Basic ${Buffer.from(key).toString('base64')}` };
      case 'header':
        return { [this.cfg.EVE_API_KEY_HEADER.toLowerCase()]: key };
    }
  }

  async createClient(client: CanonicalClient, idempotencyKey: string): Promise<EveCreateResult> {
    const url = new URL(this.cfg.EVE_CREATE_CLIENT_PATH, this.cfg.EVE_API_BASE_URL).toString();
    const body = buildEvePayload(client, this.cfg);

    let res: Response;
    try {
      res = await this.fetchImpl(url, {
        method: 'POST',
        headers: {
          ...this.authHeaders(),
          'content-type': 'application/json',
          accept: 'application/json',
          // Harmless if Eve ignores it; prevents duplicates if it honours it.
          'idempotency-key': idempotencyKey,
        },
        body: JSON.stringify(body),
        signal: AbortSignal.timeout(this.cfg.EVE_TIMEOUT_MS),
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      throw new EveTransientError(`Network failure calling Eve: ${message}`);
    }

    // 409 means the client is already there -- a success for our purposes.
    if (res.status === 409) {
      const existing = await safeJson(res);
      return { eveClientId: extractId(existing) ?? `existing:${idempotencyKey}`, alreadyExisted: true };
    }

    if (res.status === 429) {
      const retryAfter = Number(res.headers.get('retry-after'));
      throw new EveTransientError(
        'Eve rate limit hit',
        429,
        Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter * 1000 : undefined,
      );
    }

    if (res.status >= 500) {
      throw new EveTransientError(`Eve ${res.status}: ${await safeText(res)}`, res.status);
    }

    if (!res.ok) {
      throw new EvePermanentError(`Eve ${res.status}: ${await safeText(res)}`, res.status);
    }

    const payload = await safeJson(res);
    const id = extractId(payload);
    if (!id) {
      // The write probably succeeded, but without an id we cannot record the
      // link. Treat as permanent so it lands in the DLQ for a human to inspect
      // rather than retrying and risking duplicates.
      throw new EvePermanentError('Eve accepted the request but returned no client id', res.status);
    }
    return { eveClientId: id, alreadyExisted: false };
  }
}

/** Dev/CI destination: records what would have been sent. */
export class MockEveClient implements EveClient {
  readonly sent: { payload: Record<string, unknown>; idempotencyKey: string }[] = [];

  constructor(private readonly cfg: Config) {}

  async createClient(client: CanonicalClient, idempotencyKey: string): Promise<EveCreateResult> {
    const payload = buildEvePayload(client, this.cfg);
    this.sent.push({ payload, idempotencyKey });
    log.info('eve mock received client', {
      idempotencyKey,
      externalId: payload.external_id,
      name: client.fullName,
    });
    return { eveClientId: `mock-${idempotencyKey}`, alreadyExisted: false };
  }
}

export function createEveClient(cfg: Config, fetchImpl: typeof fetch = fetch): EveClient {
  return cfg.EVE_MODE === 'http' ? new HttpEveClient(cfg, fetchImpl) : new MockEveClient(cfg);
}

/** Eve's id field name is unknown; probe the common spellings. */
function extractId(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null;
  const obj = payload as Record<string, unknown>;
  const nested = obj.data && typeof obj.data === 'object' ? (obj.data as Record<string, unknown>) : obj;
  for (const key of ['id', 'client_id', 'clientId', 'uuid', 'matter_id']) {
    const value = nested[key];
    if (typeof value === 'string' && value.trim()) return value.trim();
    if (typeof value === 'number' && Number.isFinite(value)) return String(value);
  }
  return null;
}

async function safeJson(res: Response): Promise<unknown> {
  try {
    return await res.json();
  } catch {
    return null;
  }
}

async function safeText(res: Response): Promise<string> {
  try {
    return (await res.text()).slice(0, 500);
  } catch {
    return '<unreadable body>';
  }
}
