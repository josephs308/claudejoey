---
name: website-seo-aeo
description: Build, audit and launch websites that are technically excellent for Google SEO, AI answer engines (AEO/GEO — ChatGPT, Perplexity, Google AI Overviews, Copilot) and PageSpeed / Core Web Vitals. Use this whenever the user is building or editing a website or landing page of any kind (law firm, agency, local business, ecommerce store, SaaS, blog), asks about titles, meta descriptions, canonicals, sitemaps, robots.txt, llms.txt, schema / JSON-LD / structured data, FAQ or breadcrumb markup, rich results, Search Console, Bing Webmaster Tools, indexing, redirects, PageSpeed scores, LCP / CLS / INP, image optimization, contrast or accessibility warnings, or deploying a static site to Netlify / Vercel / Cloudflare Pages — even if they only say "make me a site", "why isn't my page showing on Google", "PageSpeed says X" or "push it live".
---

# Website SEO, AEO and speed

A playbook for shipping websites that rank in Google, get quoted by AI assistants and score green in PageSpeed. It was distilled from building a 36-page static marketing site end to end (pages, schema, blog, sitemap, audits, Netlify deploys, Search Console), but nothing here is tied to one brand or industry.

The core idea: **technical quality is a checklist you can verify with scripts, not a vibe.** Most SEO/AEO/speed problems are mechanical (a missing canonical, a duplicate title, an FAQ in the schema that isn't on the page, a hero image lazy-loaded, a font that blocks render). Build the site so those things are generated correctly by construction, then run the bundled audits before every publish so regressions get caught before a user or Google sees them.

## How to use this skill

1. **Figure out the site type and page types** — read `references/site-types.md` for the matching recipe (local/professional service, agency, ecommerce, SaaS, content/blog). This decides URL structure, which schema types go on which pages, and which pages need to exist.
2. **Build every page from one shared head/shell** so meta, canonical, OG tags, schema and asset links can't drift between pages. A small generator script (Python/Node) that writes static HTML from content files is ideal; a framework (Astro, Next, Eleventy) is fine too. See "Page shell" below.
3. **Apply the technical references while building**, not after:
   - `references/seo.md` — titles, descriptions, canonicals, headings, URLs, internal links, sitemap, robots, redirects, noindex pages.
   - `references/schema.md` — JSON-LD `@graph` pattern and which types to use per page; rules that keep structured data valid.
   - `references/aeo.md` — making pages quotable by AI assistants: quick-answer blocks, question headings, FAQs, llms.txt, AI crawler access, entity consistency.
   - `references/performance.md` — LCP, CLS, INP, images, fonts, CSS/JS delivery, caching, and the PageSpeed warnings that come up most.
   - `references/accessibility.md` — contrast, alt text, landmarks, keyboard, and the checks PageSpeed's Accessibility score is built from.
4. **Audit before every publish** with the bundled scripts (below). Fix everything they flag, or explain why a flag is intentional.
5. **Deploy and get indexed** — `references/launch.md` covers Netlify/Vercel/Cloudflare deploys, `_headers`/`_redirects`, preview-before-merge, Search Console, Bing, Google Business Profile, and rich-result testing.

Read only the references you need for the task at hand. A PageSpeed question needs `performance.md` (and maybe `accessibility.md`); a "why isn't Google indexing me" question needs `launch.md` and `seo.md`.

## Bundled scripts

All scripts take the built site folder as input and need no project-specific config. Run them from anywhere.

| Script | What it checks | Run |
|---|---|---|
| `scripts/audit_site.py` | Static SEO/AEO audit of every `.html` file: title/description presence + length, duplicates across pages, canonical matches URL, in sitemap (or noindex), exactly one H1, heading level skips, JSON-LD parses, `@id` references resolve, FAQ schema questions visible on page, breadcrumb targets exist, broken internal links and `#anchors`, duplicate ids, unclosed tags, missing `alt`/`lang`/`viewport`, missing OG/Twitter tags. | `python3 scripts/audit_site.py SITE_DIR --domain https://example.com` |
| `scripts/browser_check.js` | Loads every page in headless Chromium at phone (390px) and desktop (1440px) widths: JS errors, console errors, failed requests / 4xx-5xx, horizontal overflow on phones, font load failures. Optional `--contrast` flags text below WCAG AA contrast; `--block REGEX` skips flaky external requests (e.g. an image CDN); `--widths 390,768,1440` changes the viewports. | `NODE_PATH=$(npm root -g) node scripts/browser_check.js SITE_DIR [--contrast]` |
| `scripts/gen_sitemap.py` | Writes `sitemap.xml` from the HTML files, skipping pages with `noindex`, using git commit dates (or file mtime) for `<lastmod>`. Also writes `robots.txt` if missing. | `python3 scripts/gen_sitemap.py SITE_DIR --domain https://example.com` |
| `scripts/make_preview.sh` | Makes a single-file HTML preview of a page that loads its CSS/images from the live (or a preview) domain via `<base href>`, so the user can open it on their phone or in the chat without a server. | `scripts/make_preview.sh SITE_DIR/index.html https://example.com OUT.html` |

`browser_check.js` needs Playwright + Chromium. If Playwright isn't installed, `npm i -g playwright` (don't download browsers if a system Chromium is already configured). It serves the folder itself on a free local port.

A clean run of `audit_site.py` ends with `ISSUES 0`. Treat any non-zero count as a blocker unless it's a deliberate choice you've told the user about (e.g. a 62-char title that reads better than the 58-char version).

## Page shell

Every indexable page needs the same head. Generate it from one function so it's impossible to forget a tag:

```html
<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{Primary keyword phrase — distinct benefit | Brand}</title>          <!-- ≤ 60 chars -->
<meta name="description" content="{120–160 chars, answers the query, has a reason to click}">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="https://example.com/exact/path/">              <!-- absolute, trailing-slash style matches the real URL -->
<meta property="og:type" content="website">
<meta property="og:site_name" content="{Brand}">
<meta property="og:url" content="https://example.com/exact/path/">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:image" content="https://example.com/assets/og-image.png"> <!-- 1200×630 -->
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css?v={build-hash}">
<script type="application/ld+json">{"@context":"https://schema.org","@graph":[ ... ]}</script>
</head>
```

Non-indexable pages (thank-you, 404, client portal, internal search, cart/checkout, staging) get `<meta name="robots" content="noindex">` (or an `X-Robots-Tag: noindex` header), stay out of the sitemap, and are still allowed in robots.txt — blocking them in robots.txt stops Google from ever seeing the noindex.

## Working with the user

People asking for websites are often not developers, and they iterate visually in small steps ("a tiny bit lower", "less dark", "no fade at all"). A few habits make that go well:

- **Show a real preview after each change**, not a description of it. `make_preview.sh` produces an HTML file the user can open on any device. Screenshots are a fallback, not the default — users notice layout at real widths that a screenshot hides.
- **Keep changes minimal and exactly what was asked.** If they say "move it down 4px", change one number. If they reject a change, revert to precisely what they liked before rather than trying a third idea.
- **Check the actual rendered result before reporting done** — measure with a headless browser (element positions, computed styles) when the request is about position/size/color. CSS can be overridden by a later rule or a vendor-prefixed duplicate (e.g. `-webkit-mask-image` vs `mask-image`), so "I changed the rule" ≠ "the page changed".
- **When a global find/replace touches CSS, re-read the diff.** Replacing `118px` with `78px` on a line that also contains `981px` silently changes a breakpoint.
- **Publishing is a separate, explicit step.** Commit and push work freely to a branch; only merge to the production branch when the user says to publish. Confirm the host's deploy preview built successfully first (see `launch.md`).
- **Explain SEO in plain words.** "Google shows about 60 characters of a title" beats "SERP truncation at ~600px".

## Content rules that matter technically

These are writing choices, but they directly affect ranking and AI citation, so enforce them in the generator or audit:

- One H1 per page that states what the page is about; H2s that read like the questions people search. Don't skip levels (H2 → H4).
- Each service/product/location page opens with a **40–60 word direct answer** to its main question (see `aeo.md`). It's the passage AI assistants and featured snippets lift.
- FAQs: 5–8 real questions per key page, rendered visibly on the page **and** mirrored in FAQPage JSON-LD with identical wording.
- No placeholder text, lorem ipsum, fake reviews, fake addresses, or invented statistics — they're both a trust and a policy problem (Google's structured data policies prohibit markup for content users can't see or that is misleading).
- Keep claims about unreleased products/features clearly labeled ("Coming soon") and don't give them Product/Offer markup with prices that don't exist.
- Name, phone, email and address (if any) identical everywhere: footer, contact page, schema, Google Business Profile, directories.

## Before every publish — checklist

1. Rebuild the site from source.
2. `audit_site.py` → `ISSUES 0`.
3. `browser_check.js` → `problems 0` (run `--contrast` after color changes).
4. `gen_sitemap.py` if pages were added/removed (or confirm the generator did it).
5. Preview file sent to the user; user approved.
6. Push branch → deploy preview green → merge only on the user's go-ahead.
7. After a structural change (new pages, URL changes, schema changes): resubmit the sitemap / request indexing for key URLs in Search Console, and spot-check one page in the Rich Results Test.
