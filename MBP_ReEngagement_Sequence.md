# MBP Re-Engagement Sequence — 211 Unsettled Leads

**Goal:** re-open every lead who isn't a signed client or a hard no, and let their
replies surface the real status (Yes / Maybe Later / No / Ghosted). Tag replies in
GHL as they come in — the campaign becomes your tracking system.

**Audience (from `MBP_ReEngagement_Audience.csv`):**
- `reengage-hot` (39) — had a meeting / booked, no decision yet. Closest to signing.
- `reengage-warm` (44) — asked for a meeting, never scheduled. Get them on the calendar.
- `reengage-dormant` (128) — went quiet after earlier interest. One clean re-open + breakup.

> Personalize `{{first_name}}` and `{{business_name}}` with GHL merge fields.
> Keep sends from your real inbox/domain, not a no-reply.

---

## SEGMENT 1 — HOT (had a meeting, no decision)
Direct, low-friction, assume the relationship.

**Email 1 — Day 1**
Subject: picking this back up, {{first_name}}?
> {{first_name}} — we spoke a while back about getting {{business_name}} more signed
> cases and the timing wasn't right to pull the trigger. Things have moved since then
> and I think it's a better fit now.
>
> Worth a quick 15 minutes to see if it makes sense? Here's my calendar: [LINK]

**Email 2 — Day 4**
Subject: the one number that matters
> Quick one — the firms we work with care about one thing: signed cases per dollar in.
> That's all we optimize for. If I could show you what that would look like for
> {{business_name}}, would that be worth 15 minutes? [LINK]

**Email 3 — Day 9 (breakup)**
Subject: should I close your file?
> {{first_name}}, haven't heard back so I'll assume the timing still isn't right —
> no problem at all. Want me to keep your file open and check back next quarter, or
> close it out for now? Just reply "open" or "close." 🙏

---

## SEGMENT 2 — WARM (interested, never booked)
Re-spark the original interest, make scheduling effortless.

**Email 1 — Day 1**
Subject: we never got you on the calendar, {{first_name}}
> {{first_name}} — you'd reached out about getting {{business_name}} more cases and we
> never managed to lock in a time. My fault for not chasing it down.
>
> Still want to take a look? Grab whatever slot works: [LINK]

**Email 2 — Day 5**
Subject: 60-second version
> If a full call is too much right now, here's the 60-second version: [1-line offer /
> short Loom link]. If it's interesting, the next step is a quick 15-min walkthrough: [LINK]

**Email 3 — Day 10 (breakup)**
Subject: bad timing?
> Sounds like the timing might be off, {{first_name}} — totally fine. Want me to circle
> back in 90 days, or are you set for now? Just hit reply with "later" or "set."

---

## SEGMENT 3 — DORMANT (went quiet)
Pattern-interrupt, no guilt, easy out. This is the big batch — keep it short.

**Email 1 — Day 1**
Subject: still worth a conversation, {{first_name}}?
> {{first_name}} — we connected a while back about more signed cases for
> {{business_name}} and then life happened on both ends. Reopening the door:
> still something you'd want to explore, or should I take you off my list?
> A one-word reply is plenty.

**Email 2 — Day 6**
Subject: quick proof, then I'll leave you alone
> Not here to nag — just one data point: [short result / case study, e.g. "added 18
> signed cases in 90 days for a firm your size"]. If that's worth 15 minutes: [LINK].
> If not, no hard feelings.

**Email 3 — Day 12 (breakup)**
Subject: closing your file, {{first_name}}
> Last one from me — I'll close your file so I'm not cluttering your inbox. If you ever
> want to revisit getting {{business_name}} more cases, just reply and I'll pick it right
> back up. Appreciate you either way. 🙏

---

## How to run it in GHL
1. Import `MBP_ReEngagement_Audience.csv` (maps Email + Tag).
2. Build 3 workflows, one per tag (`reengage-hot/warm/dormant`), with the emails above.
3. **Reply handling = your live tracker:** as replies land, tag the contact:
   `status-yes`, `status-maybe`, `status-no`. No reply after the breakup → `status-ghosted`.
4. Weekly, pull counts per status tag — that's the report your boss asked for,
   now built from real responses.
