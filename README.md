# Cold Email Reply Agent

Detects intent in replies to your cold-email campaigns and **drafts a contextual
response for every reply** — different every time, grounded in what the prospect
actually wrote — then holds it for your approval before sending via
[Instantly](https://instantly.ai).

This solves the two hard parts of replying to cold-email replies:

1. **Detection** — each reply is classified (interested, objection, question,
   unsubscribe, out-of-office, referral, …) so the right ones get a response and
   the wrong ones (auto-replies, OOO, unsubscribes) are skipped.
2. **Correct responses** — instead of templates, Claude reads your business
   context + the prospect's reply and **writes the answer**. No two are the same.

## How it works

```
Instantly  ──reply_received webhook──▶  POST /webhooks/instantly
                                              │
                              analyze (one Claude call):
                              { intent, confidence, risk, draft }
                                              │
                                 save as a PENDING draft
                                              │
   you ──▶ GET /drafts ──▶ approve (+edit) ──▶ POST /api/v2/emails/reply
```

Replies are **drafted, not auto-sent**. You review/edit each one, then approve.
(Flipping to auto-send or hybrid-by-confidence is a small change — see below.)

## Setup

1. **Install**
   ```bash
   npm install
   cp .env.example .env          # fill in keys
   cp context/business.example.json context/business.json   # fill in your offer + voice
   ```

2. **Configure `.env`** — `ANTHROPIC_API_KEY`, `INSTANTLY_API_KEY`,
   `APPROVAL_API_TOKEN` (any random string), and optionally
   `INSTANTLY_WEBHOOK_SECRET`.

3. **Configure `context/business.json`** — this is what the agent uses to decide
   what to say: your company, what you sell, value props, tone, scheduling link,
   and any claims it must never make. Edit this any time; no code changes needed.

4. **Run**
   ```bash
   npm run dev      # watch mode
   # or
   npm run build && npm start
   ```

5. **Point Instantly at the webhook** — in Instantly, add a webhook for the
   `reply_received` event pointing to
   `https://YOUR_HOST/webhooks/instantly?secret=YOUR_WEBHOOK_SECRET`
   (expose your local server with a tunnel like ngrok while testing).

## Reviewing & sending drafts

The approval API is protected by `Authorization: Bearer $APPROVAL_API_TOKEN`.

```bash
# List drafts waiting for review
curl -H "Authorization: Bearer $TOKEN" localhost:3000/drafts?status=pending

# Inspect one (shows the prospect's reply, detected intent, and the draft)
curl -H "Authorization: Bearer $TOKEN" localhost:3000/drafts/<id>

# Approve as-is and send
curl -X POST -H "Authorization: Bearer $TOKEN" localhost:3000/drafts/<id>/approve

# Approve with edits
curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"subject":"Re: ...","body":"your edited reply"}' \
  localhost:3000/drafts/<id>/approve

# Reject (don't send)
curl -X POST -H "Authorization: Bearer $TOKEN" localhost:3000/drafts/<id>/reject
```

## Project layout

| File | Purpose |
|------|---------|
| `src/analyzer.ts` | The core: one Claude call that classifies **and** drafts the reply (structured output). |
| `src/webhook.ts` | Normalizes Instantly's `reply_received` payload (probes several field names). |
| `src/instantly.ts` | Sends the threaded reply via Instantly's v2 API. |
| `src/store.ts` | JSON-file draft queue (swap for SQLite/Postgres for multi-instance). |
| `src/server.ts` | Express: webhook intake + approval API. |
| `src/context.ts` | Loads `context/business.json`. |
| `context/business.json` | Your offer + voice + guardrails. |

## Notes & next steps

- **Model**: defaults to `claude-opus-4-8`. For high reply volume, set
  `CLAUDE_MODEL=claude-sonnet-4-6` for lower cost/latency.
- **Field mapping**: Instantly's webhook field names have varied across versions.
  If a reply logs `could not map payload`, check the logged raw body and adjust
  the candidate key lists in `src/webhook.ts`.
- **Auto-send / hybrid**: every reply already carries `analysis.risk` and
  `confidence`. To auto-send low-risk replies, in `src/server.ts`'s webhook
  handler call `sendReply()` directly when
  `analysis.risk === 'low' && analysis.confidence > 0.8`, and queue the rest.
- **Unsubscribes**: classified and `shouldRespond=false`, but you still need to
  actually remove/suppress the lead in Instantly — wire that into the webhook
  handler for the `unsubscribe` intent.
