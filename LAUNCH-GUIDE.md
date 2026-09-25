# Vincere Legal Marketing: site files and launch guide

`vincere-site.zip` holds the complete website. Unzip it, and everything in it is what gets uploaded. Nothing else is needed.

## What's in the site

```
vincere-site/
├── index.html                  Home page
├── about/index.html            /about/
├── services/index.html         /services/  (hub for all 9 services)
│   ├── law-firm-consulting/
│   ├── law-firm-branding/
│   ├── local-services-ads-for-lawyers/
│   ├── law-firm-seo/
│   ├── law-firm-aeo/
│   ├── law-firm-ppc/
│   ├── meta-ads-for-lawyers/
│   ├── law-firm-traditional-advertising/
│   └── law-firm-website-design/
├── practice-areas/index.html   /practice-areas/  (hub for all 15)
│   ├── personal-injury-lawyer-marketing/
│   ├── criminal-defense-lawyer-marketing/
│   ├── family-law-marketing/
│   ├── estate-planning-attorney-marketing/
│   ├── real-estate-attorney-marketing/
│   ├── business-lawyer-marketing/
│   ├── litigation-attorney-marketing/
│   ├── employment-lawyer-marketing/
│   ├── immigration-lawyer-marketing/
│   ├── bankruptcy-attorney-marketing/
│   ├── workers-compensation-lawyer-marketing/
│   ├── medical-malpractice-lawyer-marketing/
│   ├── dui-lawyer-marketing/
│   ├── intellectual-property-attorney-marketing/
│   └── tax-attorney-marketing/
├── portal/index.html           Client portal (hidden from Google)
├── thanks.html                 Form thank-you page (hidden from Google)
├── 404.html                    "Page not found" page (hidden from Google)
├── assets/                     Stylesheet, logo, social share image, iPhone icon
├── fonts/                      Unbounded, Schibsted Grotesk, Instrument Serif
├── favicon.svg                 The purple V browser-tab icon
├── sitemap.xml                 All 28 public pages, for Google and Bing
├── robots.txt                  Lets all crawlers in and points them to the sitemap
├── llms.txt                    Plain-English site summary for AI answer engines
├── _redirects                  Permanent redirects from the old page URLs (Netlify)
└── _headers                    Security, caching and no-index headers (Netlify)
```

There are 31 pages in total: 28 public pages and 3 hidden ones.

## SEO and AEO: what's already built in

Every public page has:
- **Its own title and meta description.** No two pages share one, and each is sized to show in full in Google results.
- **A canonical URL** on `https://vincerelegalmarketing.com`.
- **Social previews:** Open Graph and Twitter tags with the share image.
- **Exactly one H1** and headings in the correct order.
- **An FAQ section** with matching FAQPage structured data.
- **Structured data (JSON-LD):** Organization, WebSite, WebPage, BreadcrumbList, and Service or ItemList as fits the page.
- **A "quick answer" block** at the top of each service and practice-area page, written so AI answer engines can quote it directly.
- **Links:** the Services and Practice Areas menus, a full footer, and related-page links, so every page is reachable in one or two clicks.

**Checks run on every page (all passed):**
- No broken links or anchors.
- No missing alt text.
- No duplicate IDs.
- No unclosed tags.
- No JavaScript errors.
- No sideways scrolling on phones.
- All fonts load.

## Launch on Netlify

1. In Netlify, go to **Add new site → Deploy manually** and drag in the unzipped `vincere-site` folder.
2. Under **Domain management**, add `vincerelegalmarketing.com`, and set `www` to redirect to it. Netlify turns on HTTPS automatically.
3. Under **Forms**, the `vincere-booking` form appears after the first deploy. Add an email notification to `joe@vincerelegalmarketing.com` so every booking reaches you.

## Get indexed by Google (after the site is live)

1. **Google Search Console** (search.google.com/search-console): add the domain `vincerelegalmarketing.com` and verify it with the DNS record it gives you.
2. **Submit the sitemap:** in Sitemaps, submit `https://vincerelegalmarketing.com/sitemap.xml`.
3. **Request indexing** with URL Inspection: first the home page, then `/services/` and `/practice-areas/`. Google finds the rest through the sitemap and links.
4. **Bing Webmaster Tools** (bing.com/webmasters): choose "Import from Google Search Console." Bing also feeds ChatGPT search and Copilot.
5. **Google Business Profile:** create or claim it with the same name, phone and email as the site.
6. **Check the structured data:** run the home page and one service page through search.google.com/test/rich-results.

## Before launch: things only you can supply

- **Real phone number.** `(555) 010-0199` is a placeholder. It appears in the booking section, the footer, the thank-you page and the structured data. Send the real number and it gets updated everywhere with one change.
- **LinkedIn URL.** The structured data lists `linkedin.com/company/vincere-legal-marketing`. Confirm that page exists, or send the right link.
- **Booking confirmations.** After booking, the form says "We just sent a calendar invite." The form delivers the booking through Netlify, but it doesn't send an invite by itself. Connect Netlify Forms to Zapier and Google Calendar, or change that line.

## Editing the site later

The `build/` folder in the repository creates every page:
- Page wording lives in `build/content/*.json`.
- Styles live in `build/extra.css` and `build/booking.css`.

After an edit, run `python3 build/build.py`, then `python3 build/audit.py` to recheck SEO. Then re-upload `vincere-site`.
