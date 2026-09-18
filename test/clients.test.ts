import { describe, it, expect, vi } from 'vitest';
import { LawmaticsClient, LawmaticsPermanentError, LawmaticsTransientError, unwrapData } from '../src/lawmatics/client.js';
import { HttpEveClient, EvePermanentError, EveTransientError } from '../src/eve/client.js';
import { toCanonicalClient } from '../src/pipeline/mapper.js';
import { testConfig, makeProspect } from './helpers.js';

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { 'content-type': 'application/json' },
    ...init,
  });
}

describe('unwrapData', () => {
  it('unwraps { data: {...} }', () => {
    expect(unwrapData({ data: { id: 1 } })).toEqual({ id: 1 });
  });

  it('flattens JSON:API attributes onto the record', () => {
    expect(unwrapData({ data: { id: 1, attributes: { name: 'Rivera' } } })).toEqual({ id: 1, name: 'Rivera' });
  });

  it('passes through an unwrapped body', () => {
    expect(unwrapData({ id: 1 })).toEqual({ id: 1 });
  });
});

describe('LawmaticsClient', () => {
  const oauthCfg = testConfig({
    LAWMATICS_ACCESS_TOKEN: '',
    LAWMATICS_CLIENT_ID: 'cid',
    LAWMATICS_CLIENT_SECRET: 'csecret',
    LAWMATICS_REFRESH_TOKEN: 'rtoken',
  });

  it('sends the bearer token and returns the prospect', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ data: makeProspect() }));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);

    const prospect = await client.getProspect(4242);

    expect(String(prospect.id)).toBe('4242');
    const [url, init] = fetchImpl.mock.calls[0]!;
    expect(url).toContain('/v1/prospects/4242');
    expect((init.headers as Record<string, string>).authorization).toBe('Bearer test-token');
  });

  it('exchanges the refresh token before the first call', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh-token', expires_in: 3600 }))
      .mockResolvedValueOnce(jsonResponse({ data: makeProspect() }));
    const client = new LawmaticsClient(oauthCfg, fetchImpl as unknown as typeof fetch);

    await client.getProspect(4242);

    expect(fetchImpl.mock.calls[0]![0]).toContain('/oauth/token');
    expect((fetchImpl.mock.calls[1]![1].headers as Record<string, string>).authorization).toBe('Bearer fresh-token');
  });

  it('reuses a cached token across calls', async () => {
    // Each call must get a fresh Response: a body can only be read once.
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh-token', expires_in: 3600 }))
      .mockImplementation(async () => jsonResponse({ data: makeProspect() }));
    const client = new LawmaticsClient(oauthCfg, fetchImpl as unknown as typeof fetch);

    await client.getProspect(1);
    await client.getProspect(2);

    const tokenCalls = fetchImpl.mock.calls.filter((c) => String(c[0]).includes('/oauth/token'));
    expect(tokenCalls).toHaveLength(1);
  });

  it('refreshes once when concurrent calls both need a token', async () => {
    const fetchImpl = vi.fn(async (url: string) => {
      if (String(url).includes('/oauth/token')) {
        return jsonResponse({ access_token: 'fresh-token', expires_in: 3600 });
      }
      return jsonResponse({ data: makeProspect() });
    });
    const client = new LawmaticsClient(oauthCfg, fetchImpl as unknown as typeof fetch);

    await Promise.all([client.getProspect(1), client.getProspect(2), client.getProspect(3)]);

    const tokenCalls = fetchImpl.mock.calls.filter((c) => String(c[0]).includes('/oauth/token'));
    expect(tokenCalls).toHaveLength(1);
  });

  it('refreshes and retries once after an unexpected 401', async () => {
    // Starts with a token we believe is valid, so the 401 lands on the
    // prospect call and exercises the revoked-token recovery path.
    const revocableCfg = testConfig({
      LAWMATICS_ACCESS_TOKEN: 'stale-token',
      LAWMATICS_CLIENT_ID: 'cid',
      LAWMATICS_CLIENT_SECRET: 'csecret',
      LAWMATICS_REFRESH_TOKEN: 'rtoken',
    });
    const fetchImpl = vi
      .fn()
      .mockResolvedValueOnce(new Response('unauthorized', { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ access_token: 'fresh-token', expires_in: 3600 }))
      .mockResolvedValueOnce(jsonResponse({ data: makeProspect() }));
    const client = new LawmaticsClient(revocableCfg, fetchImpl as unknown as typeof fetch);

    const prospect = await client.getProspect(4242);

    expect(String(prospect.id)).toBe('4242');
    expect(fetchImpl.mock.calls[1]![0]).toContain('/oauth/token');
    expect((fetchImpl.mock.calls[2]![1].headers as Record<string, string>).authorization).toBe('Bearer fresh-token');
  });

  it('gives up after a second consecutive 401', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('unauthorized', { status: 401 }));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);

    // No refresh credentials configured, so the retry cannot get a new token.
    await expect(client.getProspect(1)).rejects.toBeInstanceOf(LawmaticsPermanentError);
  });

  it('treats 429 as transient and surfaces retry-after', async () => {
    const fetchImpl = vi
      .fn()
      .mockResolvedValue(new Response('rate limited', { status: 429, headers: { 'retry-after': '30' } }));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);

    await expect(client.getProspect(1)).rejects.toMatchObject({
      name: 'LawmaticsTransientError',
      status: 429,
      retryAfterMs: 30_000,
    });
  });

  it('treats 5xx as transient', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('boom', { status: 503 }));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);
    await expect(client.getProspect(1)).rejects.toBeInstanceOf(LawmaticsTransientError);
  });

  it('treats 404 as permanent', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('missing', { status: 404 }));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);
    await expect(client.getProspect(1)).rejects.toBeInstanceOf(LawmaticsPermanentError);
  });

  it('treats a rejected refresh token as permanent', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('invalid_grant', { status: 400 }));
    const client = new LawmaticsClient(oauthCfg, fetchImpl as unknown as typeof fetch);
    await expect(client.getProspect(1)).rejects.toBeInstanceOf(LawmaticsPermanentError);
  });

  it('treats a network failure as transient', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error('ECONNRESET'));
    const client = new LawmaticsClient(testConfig(), fetchImpl as unknown as typeof fetch);
    await expect(client.getProspect(1)).rejects.toBeInstanceOf(LawmaticsTransientError);
  });
});

describe('HttpEveClient', () => {
  const cfg = testConfig({
    EVE_MODE: 'http',
    EVE_API_BASE_URL: 'https://api.eve.example',
    EVE_API_KEY: 'eve-key',
  });
  const client = () => toCanonicalClient(makeProspect());

  it('posts the mapped payload with a bearer token and idempotency key', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ id: 'eve_123' }, { status: 201 }));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);

    const result = await eve.createClient(client(), 'lawmatics-prospect-4242');

    expect(result).toEqual({ eveClientId: 'eve_123', alreadyExisted: false });
    const [url, init] = fetchImpl.mock.calls[0]!;
    expect(url).toBe('https://api.eve.example/v1/clients');
    expect((init.headers as Record<string, string>).authorization).toBe('Bearer eve-key');
    expect((init.headers as Record<string, string>)['idempotency-key']).toBe('lawmatics-prospect-4242');
    expect(JSON.parse(init.body as string).external_id).toBe('lawmatics:4242');
  });

  it('supports an api-key header scheme', async () => {
    const headerCfg = testConfig({
      EVE_MODE: 'http',
      EVE_API_BASE_URL: 'https://api.eve.example',
      EVE_API_KEY: 'eve-key',
      EVE_AUTH_SCHEME: 'header',
      EVE_API_KEY_HEADER: 'X-Eve-Key',
    });
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ id: 'eve_123' }));
    await new HttpEveClient(headerCfg, fetchImpl as unknown as typeof fetch).createClient(client(), 'key');

    const headers = fetchImpl.mock.calls[0]![1].headers as Record<string, string>;
    expect(headers['x-eve-key']).toBe('eve-key');
    expect(headers.authorization).toBeUndefined();
  });

  it('treats 409 as an existing client rather than an error', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ id: 'eve_existing' }, { status: 409 }));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);

    await expect(eve.createClient(client(), 'key')).resolves.toEqual({
      eveClientId: 'eve_existing',
      alreadyExisted: true,
    });
  });

  it.each([
    ['data-wrapped id', { data: { id: 'eve_1' } }],
    ['client_id', { client_id: 'eve_1' }],
    ['uuid', { uuid: 'eve_1' }],
  ])('reads the returned id from %s', async (_label, body) => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse(body));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);
    expect((await eve.createClient(client(), 'key')).eveClientId).toBe('eve_1');
  });

  it('fails permanently when Eve returns no id', async () => {
    const fetchImpl = vi.fn().mockResolvedValue(jsonResponse({ ok: true }));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);
    await expect(eve.createClient(client(), 'key')).rejects.toBeInstanceOf(EvePermanentError);
  });

  it.each([
    [422, EvePermanentError],
    [400, EvePermanentError],
    [503, EveTransientError],
    [429, EveTransientError],
  ])('classifies a %i response correctly', async (status, expected) => {
    const fetchImpl = vi.fn().mockResolvedValue(new Response('err', { status }));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);
    await expect(eve.createClient(client(), 'key')).rejects.toBeInstanceOf(expected);
  });

  it('treats a network failure as transient', async () => {
    const fetchImpl = vi.fn().mockRejectedValue(new Error('ETIMEDOUT'));
    const eve = new HttpEveClient(cfg, fetchImpl as unknown as typeof fetch);
    await expect(eve.createClient(client(), 'key')).rejects.toBeInstanceOf(EveTransientError);
  });
});
