# On-page and technical SEO

## Contents
1. Titles and meta descriptions
2. Headings and page structure
3. URLs and site architecture
4. Canonicals and duplicates
5. Internal linking and breadcrumbs
6. Sitemap, robots.txt and noindex
7. Redirects and migrations
8. Images for search
9. Local SEO basics
10. International / multi-language

## 1. Titles and meta descriptions

- **Title: ≤ 60 characters** (Google truncates around 600px). Lead with the phrase people search, then a differentiator, then the brand: `Car Accident Lawyer in San Diego | Smith Law`, `Waterproof Hiking Boots for Women | Trailco`.
- **Description: 120–160 characters.** It doesn't directly affect ranking but drives click-through. Say what the page answers or offers and give a reason to click. Google rewrites descriptions it thinks don't match the query — a specific, accurate one gets kept more often.
- **Unique per page.** Duplicate titles/descriptions tell Google two pages are the same thing. The audit script flags these.
- Homepage title can lead with the brand; every other page leads with its topic.
- Don't stuff keywords or repeat the same word 3 times; write for the searcher.

## 2. Headings and page structure

- **Exactly one `<h1>`**, matching the page's main topic (can be longer/friendlier than the title).
- H2s for main sections, H3s under them. No jumps (H2 → H4). Headings are for structure, not styling — use CSS for big text that isn't a heading.
- Put the most important content (what this is, who it's for, the direct answer) in the first screen of text, in real HTML — not inside images, canvas, or content loaded only after a click.
- Use semantic landmarks: `<header>`, `<nav>`, `<main>`, `<footer>`, `<article>` for posts.

## 3. URLs and site architecture

- Lowercase, hyphen-separated, descriptive, stable: `/services/seo/`, `/practice-areas/personal-injury-lawyer-marketing/`, `/products/womens-trail-boot/`.
- Pick one style for trailing slashes and stick to it; canonicals, sitemap, internal links and redirects must all use the same form. Static hosts serving `folder/index.html` naturally produce trailing-slash URLs.
- Hub-and-spoke: a hub page (`/services/`) links to every spoke (`/services/seo/`), and every spoke links back to its hub and to 2–3 related spokes. Every indexable page should be ≤ 3 clicks from the homepage.
- Avoid orphan pages (no internal links in). The audit's sitemap check plus nav/footer links usually cover this.
- Don't create thin near-duplicate pages (the same text with a city name swapped). Location or variant pages each need genuinely specific content.

## 4. Canonicals and duplicates

- Every indexable page has a self-referencing absolute canonical: `https://example.com/path/`.
- The canonical must be the URL that actually returns 200 (not a redirect, not a noindex page).
- `http`/`https`, `www`/non-www and trailing-slash variants must 301 to the canonical form (the host usually handles www→apex and http→https once configured).
- Parameter URLs (`?utm_source=`, `?sort=`, `?color=`) canonicalize to the clean URL.
- Paginated series (`/blog/page/2/`): each page canonicalizes to itself, not to page 1.

## 5. Internal linking and breadcrumbs

- Use descriptive anchor text ("our PPC management service"), not "click here".
- Nav and footer give every key page sitewide links; in-content links pass the most context — link related services/products/posts from body copy.
- Visible breadcrumbs on every page below the homepage (`Home › Services › SEO`) plus matching BreadcrumbList JSON-LD (see `schema.md`). Every breadcrumb URL must be a real page — the audit checks this.

## 6. Sitemap, robots.txt and noindex

**sitemap.xml**
- Lists every indexable, canonical, 200-status URL. Nothing noindexed, redirected, or blocked.
- `<lastmod>` should reflect real content changes (git commit date works well); don't set every page to today's date on every build — Google learns to ignore it.
- Reference it from robots.txt and submit it in Search Console and Bing Webmaster Tools.
- Large sites: split into multiple sitemaps under a sitemap index (max 50,000 URLs / 50MB each).

**robots.txt**
```
User-agent: *
Allow: /

Sitemap: https://example.com/sitemap.xml
```
- robots.txt controls crawling, not indexing. To keep a page out of Google, use `noindex` and **let it be crawled**. Blocking a URL in robots.txt can leave it indexed with no snippet.
- Only disallow things that waste crawl budget (internal search results, infinite filter combinations, cart).
- AI crawler rules live here too — see `aeo.md`.

**noindex** pages: thank-you, 404, login/portal, cart/checkout/account, internal search, staging/preview deploys, tag archives with thin content. Use the meta tag or `X-Robots-Tag` header.

**404 page**: a real 404 status (static hosts serve `404.html` with the right status), helpful links back into the site, noindex.

## 7. Redirects and migrations

- Moving or renaming a URL → **301 redirect** from old to new, one hop (no chains). Keep redirects forever, or at least a year.
- When replacing an old site, crawl or export every old URL (old sitemap, Search Console "Pages" report, analytics landing pages) and map each one to its closest new page. Don't blanket-redirect everything to the homepage — Google treats that as a soft 404.
- Update internal links to point straight at the new URLs; don't rely on redirects internally.
- After launch, watch Search Console's Pages report for "Not found (404)" and add missed redirects.

Netlify/Cloudflare `_redirects` example:
```
/old-page.html   /new-page/   301
/old-page        /new-page/   301
```

## 8. Images for search

- Descriptive file names (`womens-trail-boot-black.webp`), meaningful `alt` text describing the image (empty `alt=""` for purely decorative images).
- Real `<img>` elements (not CSS backgrounds) for images that should appear in image search or be understood as content.
- `width`/`height` attributes on every image (prevents layout shift, see `performance.md`).
- A 1200×630 Open Graph image per site (or per page for key pages) for social/link previews.

## 9. Local SEO basics

For businesses serving a geographic area:
- A Google Business Profile with the exact same name, phone and website as the site. Service-area businesses (no storefront) can hide their address and list service areas instead — never invent an address.
- NAP (name, address, phone) consistent across site footer, contact page, schema, GBP and major directories.
- Location in titles/H1s only where the business genuinely serves that location.
- LocalBusiness (or a subtype like `LegalService`, `Dentist`, `Plumber`) schema with `areaServed` — see `schema.md`.
- Reviews: ask real customers to review on Google; don't mark up your own Google reviews on your site as review schema (self-serving reviews aren't eligible for review rich results on LocalBusiness/Organization).

## 10. International / multi-language

Only if the site has multiple languages/regions: each version gets its own URL (`/es/…`), `hreflang` tags linking all versions (including a self-reference and `x-default`), and `lang` on the `<html>` tag matching the page language. Don't auto-redirect by IP; let users switch.
