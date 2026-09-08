---
name: site-launch-seo
description: >
  Pre-launch and post-launch URL/indexation checks for static marketing sites
  (Netlify, Vercel, Cloudflare Pages, plain S3). Covers canonical URL form,
  301 rules for alternate forms, sitemap/robots hygiene, noindex on utility
  pages, and diagnosing Google Search Console indexation errors. Use this
  skill whenever a site is about to go live, has just gone live, or when
  someone mentions Search Console, "not indexed", "duplicate content",
  "Google chose different canonical", pages missing from search, sitemap
  problems, or a traffic drop after a launch or migration — even if they
  only describe the symptom and never say "SEO".
---

# Site launch: URL form and indexation

Most "my pages aren't indexed" problems on a static site are not content
problems. They are the same problem: **the same page is reachable at more
than one URL**, so Google has to guess which one is real, and it does not
have to agree with you.

`/about` and `/about.html` serving identical HTML is two URLs, not one.
Google crawls both, marks them duplicates, picks a winner, and the loser
gets dropped from the index — often the one you link to everywhere and put
on business cards.

The whole job is: pick one form, serve one form, point every signal at that
form, and make every other form redirect to it.

## Before launch

Run the checker against the deploy preview before DNS points anywhere:

```bash
python3 scripts/check_canonical.py https://<preview-url>
```

It reads the sitemap, then for every listed URL checks the status, the
canonical tag, `og:url`, `noindex`, internal `.html` references, and — the
part that matters most — whether the alternate URL form redirects or
quietly serves a duplicate. Exit 0 means clean.

It reports a canonical pointing at a different *host* as a note, not a
problem, because that is correct on a preview deploy: canonicals should
name the production domain even before the domain is live.

What it cannot see, check by hand:

- **Canonical form chosen and written down.** Extensionless (`/about`) is
  the usual pick. Either is fine; mixing is not.
- **Every internal link uses that form** — nav, footer, buttons, and
  *form `action` attributes*. Form actions are the easy miss: a POST to a
  301 gets converted to a GET by browsers, so a form pointed at the wrong
  URL form can silently break a submission, not just muddy a signal.
  Internal links are one of Google's strongest canonical signals; if your
  own nav disagrees with your canonical tag, the tag may lose.
- **Utility pages are `noindex` and absent from the sitemap** — thank-you,
  confirmation, client portal, 404. A sitemap should list only pages you
  want in the index, so submitted-count and indexable-count match exactly
  and any future drift is visible.
- **Redirect rules exist for every page.** On Netlify, `_redirects` in the
  publish directory, one line per page. The trailing `!` is required —
  without it the rule is skipped when the destination file also exists,
  which is exactly the case here:

  ```
  /about.html   /about   301!
  ```

  A `/*.html /:splat 301!` catch-all is widely suggested but Netlify only
  documents splat matching at the *end* of a path. Do not ship it untested;
  explicit per-page rules always work. Some hosts (Netlify's "Pretty URLs"
  among them) already strip `.html` by default, which makes explicit rules
  redundant but not useless — they survive someone toggling a setting.
- **Sitemap and robots.txt agree** with the chosen form and with each other.

## After launch

Submit the sitemap, then expect to wait. Indexation takes weeks, and being
indexed only makes a page *eligible* to rank. A new domain with no external
links will be indexed and still invisible — that is a link and content
problem, not a technical one, and no amount of canonical work fixes it.
Say so plainly rather than letting someone read indexation as traffic.

## Diagnosing "Duplicate, Google chose different canonical than user"

This means Google crawled the page, decided it duplicates another URL, and
overrode your canonical tag. The page is not indexed and not served.

**Trust URL Inspection, not the summary reports.** Search Console's panels
refresh on different schedules and will openly contradict each other — a
sitemap page card reading "Indexed 5 / Not indexed 0" directly above a
table reading "Discovered – currently not indexed: 5 pages". When they
disagree, the pessimistic one has been right. URL Inspection on a specific
URL is the authoritative check; the aggregates are not. Do not tell someone
their problem is fixed on the strength of a summary card.

Read these two lines in URL Inspection:

- **User-declared canonical** — what your page says
- **Google-selected canonical** — what Google picked instead

Then work the gap:

**1. If the declared canonical is wrong** (points at the homepage or
another page), that is the whole bug. Fix the tag, deploy, Validate Fix.

**2. If the tag is right, verify the redirect is actually live.** Not in
the repo — on the deployed site:

```bash
curl -I https://example.com/about.html      # expect 301 + location: /about
```

A repo containing correct `_redirects` proves nothing; the deploy may
predate the file, or the site may not be git-linked at all. Check the
host's deploy log for which commit shipped and how many redirect rules it
processed.

**3. If the redirect is live and Google still names the alternate form,
it is recrawl lag — and the fix is counterintuitive.** Google is comparing
your page against an *old indexed copy* of the alternate URL. It will not
learn about the redirect until it re-fetches the alternate URL, and it has
no particular reason to do that soon.

So request indexing on the URL that redirects, not only on the canonical
one. You are requesting a *recrawl*, and the recrawl is what carries the
news. Do both forms of every affected page, then Validate Fix. The daily
submission quota is around 10 URLs, so batch accordingly.

Then it is 1–4 weeks, and nothing shortens that. Say that clearly instead
of implying a faster result.

## Judgment

The technical fix here is genuinely small — usually minutes. The failure
mode is spending a day on it. Diagnose with URL Inspection, fix, submit,
close the tab. If it needs real content rewrites, that is a separate
project on a separate day, and it is worth saying so out loud rather than
sliding into it.

Be careful about declaring victory. The tempting moment is when a report
turns green; the honest moment is when a live check agrees with it.
