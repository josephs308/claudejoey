# Recipes by site type

Pick the closest recipe, then adapt. Every recipe shares the fundamentals in `SKILL.md` (page shell, one H1, unique titles, sitemap, audits).

## Contents
1. Professional / local service business (law firm, dentist, contractor, clinic, accountant)
2. Marketing or creative agency
3. Ecommerce store
4. SaaS / software product
5. Content site / blog
6. Single landing page

---

## 1. Professional / local service business

**Pages**
- Home: who you help, where, the main outcome, primary CTA (call / book), proof (reviews, results, logos), services overview, FAQ.
- `/services/` hub + one page per service (`/services/{service}/`). If they serve distinct niches (practice areas, treatment types, property types), a second hub (`/practice-areas/`, `/industries/`) with one page each.
- Location pages only for places they genuinely serve with specific content (local stats, office info, local proof).
- About (real people, credentials, photos), Contact (NAP, map or service-area list, hours, form), Blog.
- Thank-you (noindex), 404 (noindex), privacy policy.

**Service page template** (what worked well):
1. H1 + one-line value proposition + CTA
2. Quick-answer block (40–60 words, "What is X?")
3. 3 sections of explanation (why it matters, how it works, what's different) — H2s phrased as questions where natural
4. What's included (6–8 bullets)
5. Who it's for
6. Process (4–5 numbered steps)
7. How results are measured (3–4 metrics)
8. CTA band
9. FAQ (5–8)
10. Related services (2–3 links)

**Schema**: Organization as the relevant LocalBusiness subtype (`LegalService`, `Dentist`, `MedicalClinic`, `HomeAndConstructionBusiness`, `AccountingService`, `ProfessionalService`), `Service` per service page, BreadcrumbList, FAQPage.

**Off-site**: Google Business Profile (service-area businesses can hide the address), Bing Places, the main directories for the industry, consistent NAP everywhere. Industries with advertising rules (legal, medical, financial) need copy that avoids guarantees and unverifiable superlatives — check the relevant bar/board rules.

## 2. Marketing or creative agency

Same skeleton as §1, plus:
- `/work/` or `/case-studies/` with one page per case study: client type, challenge, approach, measurable results (with permission), testimonial. These are the pages that get cited ("agency that grew X by Y").
- Industry/niche pages (`/industries/{niche}/`) if they specialize — niche pages outrank generic "digital marketing agency" pages.
- Pricing or "how we price" page — "how much does X cost" is one of the most asked questions to AI assistants.
- Schema: `ProfessionalService` or `Organization`, `Service` pages, case studies as `Article` (or `CreativeWork`), Person nodes for leadership.

## 3. Ecommerce store

**Architecture**
- Home → category (`/collections/{category}/`) → subcategory → product (`/products/{product}/`). Keep product URLs stable and independent of the category path so a product in two categories has one URL.
- Faceted navigation (color, size, price filters) creates near-infinite URL combinations. Only let a filtered URL be indexable if it matches real search demand ("women's black hiking boots") and has a unique title/description/intro; canonicalize or noindex the rest, and keep sort parameters out of the index.
- Pagination: each page self-canonical; link pages sequentially; make sure all products are reachable through crawlable links (not only infinite scroll).
- Out-of-stock: keep the page live (200) with availability updated if it's coming back; 301 to the closest replacement if it's gone for good; 404/410 if there's no replacement.
- Variants: one canonical product URL with variant selection, or separate URLs per variant with `ProductGroup`/`hasVariant` markup — pick one approach.

**Product page**
- Unique title (`{Product name} – {key attribute} | Brand`), original description (not the manufacturer's copy used by every other store), multiple images with alt text, price, availability, shipping and returns info visible, reviews on the page.
- Product schema with `offers` (price, currency, availability), `aggregateRating`/`review` only from reviews shown on the page, `shippingDetails` and `hasMerchantReturnPolicy` for merchant listing eligibility. Keep schema prices in sync with displayed prices (generate both from the same data).
- Google Merchant Center feed (free listings) — often more traffic than organic product pages.

**Performance**: product images are the LCP; use a proper image CDN or build-time resizing. Watch third-party apps (reviews, upsell, chat) — each adds JS.

**Other pages**: collection intro copy (100–200 words, above or below the grid), buying guides and comparisons (blog), size guide, shipping/returns/FAQ pages (Organization-level `MerchantReturnPolicy`), noindex for cart/checkout/account/search.

## 4. SaaS / software product

- Home, `/features/` (one page per major feature or use case), `/pricing/` (visible prices; they get cited), `/integrations/{tool}/`, `/compare/{competitor}/` and `/alternatives/{competitor}/` pages (high intent, frequently cited by AI assistants — be accurate and fair), docs/help center (often the biggest organic traffic source — make it crawlable, not behind login or JS-only), changelog, blog.
- Schema: `SoftwareApplication` (with `offers`, `applicationCategory`, `operatingSystem`), Organization, FAQPage on pricing, BreadcrumbList in docs.
- If the app is a JS single-page app, keep marketing pages and docs statically rendered or server-rendered.

## 5. Content site / blog

- Topic clusters: a pillar page per core topic linking to 5–15 supporting posts, each linking back.
- Post template: H1, byline with author page link, published + updated dates, quick answer / key takeaways at top, table of contents for long posts (H2 anchors), images with alt, FAQ where natural, related posts.
- Author pages with credentials (`Person` schema, `sameAs`).
- RSS feed, blog index with pagination or "load more" that still has crawlable links, category pages with intro text.
- Draft support in the generator (`draft: true` excluded from build, sitemap and feed).
- Each post: `BlogPosting` schema, BreadcrumbList, added to sitemap + RSS + llms.txt automatically.

## 6. Single landing page

- One H1, a single conversion goal, fast (target LCP < 1.5 s), CTA visible without scrolling on phones.
- If it's for paid ads only and duplicates site content, `noindex` it; if it's meant to rank, give it the full SEO treatment and link to it from the main site.
- Track conversions (form submit / click-to-call) with an event, and make the thank-you state measurable (separate noindexed thank-you URL is easiest).
