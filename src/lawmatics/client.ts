import type { Config } from '../config.js';
import { log, errField } from '../logger.js';
import { prospectSchema, type LawmaticsProspect } from './types.js';

/** Raised for responses that will never succeed on retry (4xx other than 429). */
export class LawmaticsPermanentError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'LawmaticsPermanentError';
  }
}

/** Raised for transient failures (5xx, 429, network) that are worth retrying. */
export class LawmaticsTransientError extends Error {
  constructor(message: string, readonly status?: number, readonly retryAfterMs?: number) {
    super(message);
    this.name = 'LawmaticsTransientError';
  }
}

interface TokenState {
  accessToken: string;
  /** Epoch ms; 0 means "never expires as far as we know" (static token). */
  expiresAt: number;
}

/**
 * Lawmatics REST client.
 *
 * Handles the OAuth2 refresh-token dance and the documented 150 req/min per-firm
 * rate limit. A single in-flight refresh is shared between concurrent callers so
 * a burst of webhooks cannot stampede the token endpoint.
 */
export class LawmaticsClient {
  private token: TokenState | null = null;
  private refreshInFlight: Promise<TokenState> | null = null;

  constructor(
    private readonly cfg: Config,
    private readonly fetchImpl: typeof fetch = fetch,
  ) {
    if (cfg.LAWMATICS_ACCESS_TOKEN) {
      this.token = { accessToken: cfg.LAWMATICS_ACCESS_TOKEN, expiresAt: 0 };
    }
  }

  /** Fetches a matter (prospect) with its contact and custom fields expanded. */
  async getProspect(id: string | number): Promise<LawmaticsProspect> {
    const body = await this.request<unknown>(`/v1/prospects/${encodeURIComponent(String(id))}?fields=all`);
    const payload = unwrapData(body);
    const parsed = prospectSchema.safeParse(payload);
    if (!parsed.success) {
      throw new LawmaticsPermanentError(
        `Prospect ${id} did not match the expected shape: ${parsed.error.issues.map((i) => i.path.join('.')).join(', ')}`,
        200,
      );
    }
    return parsed.data;
  }

  private async accessToken(): Promise<string> {
    const current = this.token;
    // Refresh 60s early so a token cannot expire mid-flight.
    if (current && (current.expiresAt === 0 || current.expiresAt - 60_000 > Date.now())) {
      return current.accessToken;
    }
    if (!this.refreshInFlight) {
      this.refreshInFlight = this.refreshToken().finally(() => {
        this.refreshInFlight = null;
      });
    }
    const refreshed = await this.refreshInFlight;
    return refreshed.accessToken;
  }

  private async refreshToken(): Promise<TokenState> {
    const { LAWMATICS_CLIENT_ID, LAWMATICS_CLIENT_SECRET, LAWMATICS_REFRESH_TOKEN } = this.cfg;
    if (!LAWMATICS_CLIENT_ID || !LAWMATICS_CLIENT_SECRET || !LAWMATICS_REFRESH_TOKEN) {
      throw new LawmaticsPermanentError('Access token expired and no refresh credentials are configured', 401);
    }

    const res = await this.fetchImpl(new URL('/oauth/token', this.cfg.LAWMATICS_API_BASE_URL).toString(), {
      method: 'POST',
      headers: { 'content-type': 'application/json', accept: 'application/json' },
      body: JSON.stringify({
        grant_type: 'refresh_token',
        refresh_token: LAWMATICS_REFRESH_TOKEN,
        client_id: LAWMATICS_CLIENT_ID,
        client_secret: LAWMATICS_CLIENT_SECRET,
      }),
    });

    if (!res.ok) {
      const detail = await safeText(res);
      // A rejected refresh token needs an operator to re-authorise; never retry it.
      if (res.status >= 400 && res.status < 500) {
        throw new LawmaticsPermanentError(`Token refresh rejected (${res.status}): ${detail}`, res.status);
      }
      throw new LawmaticsTransientError(`Token refresh failed (${res.status}): ${detail}`, res.status);
    }

    const json = (await res.json()) as { access_token?: string; expires_in?: number };
    if (!json.access_token) throw new LawmaticsPermanentError('Token refresh returned no access_token', 502);

    const expiresIn = typeof json.expires_in === 'number' ? json.expires_in : 3600;
    this.token = { accessToken: json.access_token, expiresAt: Date.now() + expiresIn * 1000 };
    log.info('lawmatics token refreshed', { expiresInSeconds: expiresIn });
    return this.token;
  }

  private async request<T>(path: string, init: RequestInit = {}, attempt = 0): Promise<T> {
    const token = await this.accessToken();
    const url = new URL(path, this.cfg.LAWMATICS_API_BASE_URL).toString();

    let res: Response;
    try {
      res = await this.fetchImpl(url, {
        ...init,
        headers: {
          ...(init.headers as Record<string, string> | undefined),
          authorization: `Bearer ${token}`,
          accept: 'application/json',
        },
        signal: AbortSignal.timeout(this.cfg.EVE_TIMEOUT_MS),
      });
    } catch (err) {
      throw new LawmaticsTransientError(`Network failure calling ${path}: ${errField(err).error}`);
    }

    // A 401 on a token we believed valid means it was revoked or expired early.
    // Drop it and retry once; a second 401 is a real credential problem.
    if (res.status === 401 && attempt === 0) {
      log.warn('lawmatics returned 401, forcing token refresh', { path });
      this.token = null;
      return this.request<T>(path, init, attempt + 1);
    }

    if (res.status === 429) {
      const retryAfter = Number(res.headers.get('retry-after'));
      throw new LawmaticsTransientError(
        'Lawmatics rate limit hit (150 req/min per firm)',
        429,
        Number.isFinite(retryAfter) && retryAfter > 0 ? retryAfter * 1000 : undefined,
      );
    }

    if (res.status >= 500) {
      throw new LawmaticsTransientError(`Lawmatics ${res.status} on ${path}: ${await safeText(res)}`, res.status);
    }

    if (!res.ok) {
      throw new LawmaticsPermanentError(`Lawmatics ${res.status} on ${path}: ${await safeText(res)}`, res.status);
    }

    return (await res.json()) as T;
  }
}

/** Lawmatics wraps single resources in `{ data: {...} }` on most endpoints. */
export function unwrapData(body: unknown): unknown {
  if (body && typeof body === 'object' && 'data' in body) {
    const data = (body as { data: unknown }).data;
    if (data && typeof data === 'object') {
      // JSON:API style: { data: { id, attributes: {...} } }
      if ('attributes' in data && (data as { attributes: unknown }).attributes) {
        const { attributes, ...rest } = data as Record<string, unknown>;
        return { ...rest, ...(attributes as Record<string, unknown>) };
      }
      return data;
    }
  }
  return body;
}

async function safeText(res: Response): Promise<string> {
  try {
    return (await res.text()).slice(0, 500);
  } catch {
    return '<unreadable body>';
  }
}
