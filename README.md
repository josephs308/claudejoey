# Lawmatics → Eve connector

Watches Lawmatics for leads that convert into clients, and pushes each converted
client into Eve — so the firm's intake team never re-keys a retained client by hand.

```
Lawmatics                    this connector                         Eve
─────────                    ──────────────                         ───
matter status
  → "Hired"   ──webhook──►  verify HMAC signature
                            dedupe by event_id
                            ack 202 immediately
                                   │
                                   ▼  (background queue)
                            re-fetch matter from Lawmatics API
                            apply the firm's conversion rule
                            map → canonical client
                            map → Eve payload      ──POST──►  client created
                            record the link (idempotency)
```

## Status: one side is verified, one is not

**Lawmatics side — built against their documented contract.** Signature scheme,
OAuth flow, `prospects` endpoints, custom-field value keys and the 150 req/min
rate limit all follow [Lawmatics' developer docs](https://help.lawmatics.com/en/articles/10699983-lawmatics-developer-tools-open-api-webhooks).

**Eve side — built against an assumed contract.** Eve publishes no developer
documentation, no OpenAPI spec and no public developer portal. Their advertised
CRM integrations (Clio Grow, Lead Docket, Smart Advocate) do not include
Lawmatics. So the Eve request shape in this repo is a **placeholder that has not
been verified against a real Eve API.**

Everything Eve-specific is confined to `src/eve/client.ts` plus a handful of env
vars. When the firm obtains Eve's API details, the change is:

1. set `EVE_API_BASE_URL`, `EVE_API_KEY`, `EVE_AUTH_SCHEME`, `EVE_CREATE_CLIENT_PATH`
2. adjust `buildEvePayload()` to match Eve's real field names
3. set `EVE_MODE=http`

Nothing else in the pipeline needs to change. Until then the connector runs with
`EVE_MODE=mock`, which does the full Lawmatics-side work and logs exactly what
*would* be sent — useful for validating the conversion rule against live data
before any client record is created in Eve.

**To unblock:** ask Eve support for API access, the create-client endpoint, its
auth scheme, and whether they support an `Idempotency-Key` header.

## Setup

```bash
npm install
cp .env.example .env    # then fill it in
npm test
npm run dev
```

### 1. Lawmatics OAuth credentials

Create an API application in Lawmatics, complete the OAuth2 authorization-code
flow once, and put the resulting client id, client secret and refresh token in
`.env`. The connector refreshes access tokens on its own from there, including
recovery when a token is revoked mid-flight.

### 2. Lawmatics webhook

In Lawmatics: **Settings → Integrations → Webhooks**. Webhooks are dashboard-only
and cannot be created through the API.

- URL: `https://your-host/webhooks/lawmatics`
- Events: matter status changed (plus matter created/updated if you want those covered)
- Copy the `whsec_…` signing secret into `LAWMATICS_WEBHOOK_SECRET`

### 3. The conversion rule

This is the setting that matters most, and it is firm-specific. Lawmatics has no
dedicated "converted" event — conversion shows up as a matter moving into one of
the firm's client statuses. Set `CONVERSION_STATUSES` to the firm's actual status
names:

```
CONVERSION_STATUSES=hired,signed,retained
```

Matching is case-insensitive. `CONVERSION_EXCLUDED_SUBSTATUSES` can hold back
matters that are technically hired but not ready to sync (e.g. a pending conflict
check).

Run with `EVE_MODE=mock` for a few days first and read the logs: every skip is
logged with its reason, so you can confirm the rule fires on exactly the matters
the firm considers converted.

## How it behaves

**Fast ack.** The webhook endpoint verifies, dedupes, enqueues and returns `202`.
All Lawmatics and Eve I/O happens on a background queue, so a slow API call never
makes Lawmatics time out and redeliver.

**Signature verification.** HMAC-SHA256 over `"<timestamp>.<raw body>"`, compared
in constant time, with a ±5 minute window to block replays. The raw body is used
throughout — the request is never parsed before verification.

**The fetched record wins.** The conversion decision is made against the matter
re-fetched from the Lawmatics API, not the webhook body. A webhook can be minutes
stale by the time it is processed, and syncing a client whose status has since
moved back to "lost" is worse than missing one.

**Duplicates are blocked three ways.** Webhook `event_id` dedupe, a persisted
Lawmatics-prospect → Eve-client link that survives restarts, and an
`Idempotency-Key` header on the Eve call. An Eve `409` is treated as success.

**Failures are classified.** 5xx, 429 and network errors retry with exponential
backoff plus jitter (honouring `Retry-After`). 4xx, unparseable payloads and
missing ids go straight to `data/dead-letter.jsonl` — retrying them would never
help. Replay them with `npm run replay` once the cause is fixed.

**Nothing sensitive is logged.** The logger redacts tokens, secrets and
authorization headers at every nesting level.

## Operations

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Liveness, queue depth, Eve mode |
| `GET /metrics` | Counters: received, rejected, duplicate, enqueued, synced |

```bash
npm run replay -- --dry-run          # show what would be replayed
npm run replay                       # replay all dead-lettered events
npm run replay -- --event evt_abc123 # replay one

# send a correctly signed test delivery at a running connector
npx tsx scripts/send-test-webhook.ts --prospect 4242
```

Replay is safe to re-run: the idempotency record stops an already-synced client
from reaching Eve twice.

## Layout

```
src/
  config.ts              env parsing; the process refuses to boot if misconfigured
  server.ts              HTTP layer: verify → dedupe → enqueue → ack
  lawmatics/
    signature.ts         HMAC verification
    types.ts             payload schemas, custom-field value reader
    client.ts            OAuth refresh, rate-limit and error classification
  pipeline/
    conversion.ts        "did this lead become a client?"
    mapper.ts            Lawmatics → canonical client
    handler.ts           orchestration
  eve/client.ts          ← the only Eve-specific file
  queue/queue.ts         retry with backoff + jitter, dead-lettering
  store/store.ts         dedupe, idempotency links, dead-letter log
```

The canonical client model in `pipeline/mapper.ts` sits between the two vendors,
so a change on either side touches one adapter rather than the whole pipeline.

## Scaling note

State lives in a JSON file (`STATE_DIR`), which assumes a **single instance**.
That is the right size for one firm's intake volume. Running multiple replicas
requires swapping `store/store.ts` for Redis or Postgres — the interface is
four methods, kept deliberately narrow for exactly that reason.
