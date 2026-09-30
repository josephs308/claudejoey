# Deploy, publish and get indexed

## Contents
1. Hosting a static site
2. Headers and redirects files
3. Safe publish workflow (branch → preview → merge)
4. Domain and HTTPS
5. Forms
6. Google Search Console
7. Bing Webmaster Tools
8. Google Business Profile
9. After launch: what to watch

## 1. Hosting a static site

Netlify, Vercel, and Cloudflare Pages all serve static HTML from a global CDN with free HTTPS and deploy previews. Connect the Git repo, set the publish directory (e.g. `site/` or `dist/`), and set the build command if there is one. Every push to the production branch deploys; every pull request gets its own preview URL.

GitHub Pages works too but has no custom headers, no server-side redirects (only meta-refresh), and no deploy previews — prefer the others for SEO work.

## 2. Headers and redirects files

**Netlify / Cloudflare Pages `_headers`** (in the publish directory):
```
/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: SAMEORIGIN
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

/assets/*
  Cache-Control: public, max-age=0, must-revalidate

/thanks.html
  X-Robots-Tag: noindex

/llms.txt
  Content-Type: text/plain; charset=utf-8
```

**`_redirects`**:
```
/old-page.html   /new-page/   301
/old-page        /new-page/   301
```
Vercel uses `vercel.json` (`"redirects"`, `"headers"`) instead.

If the host shows a failed deploy, open the deploy log — the usual causes are a wrong publish directory, a build command that fails in CI (missing dependency, Python/Node version), a malformed `_redirects`/`_headers` line, or a file over the size limit.

## 3. Safe publish workflow

1. Work on a branch; commit each change with a clear message.
2. Before pushing: rebuild, `audit_site.py` (ISSUES 0), `browser_check.js` (problems 0).
3. Send the user a preview (`make_preview.sh`, or the host's deploy-preview URL once it exists).
4. Open a pull request → wait for the host's deploy-preview check to go green.
5. Merge only when the user explicitly says to publish. Squash-merge keeps production history readable.
6. After merge, start the next change from the updated production branch rather than stacking on the merged branch.
7. Spot-check the live URL (hard refresh — or add `?v=random` — to bypass the cache).

## 4. Domain and HTTPS

- Add the apex domain and `www`; pick one as primary and redirect the other (host setting). Canonicals, sitemap and schema must use the primary.
- Point DNS at the host (either switch nameservers to the host, or add the A/ALIAS/CNAME records it gives you). HTTPS certificates are issued automatically once DNS resolves.
- Force HTTPS (usually on by default).

## 5. Forms

- Netlify Forms: add `data-netlify="true"` and a `name` to the `<form>`, include a hidden `form-name` input if the form is rendered by JS, and set email notifications in the dashboard. Add a honeypot field against spam.
- Otherwise: Formspree, Basin, a serverless function, or the CRM's embed.
- Send users to a noindexed thank-you page (or show a state change) and fire a conversion event.
- Don't promise automated follow-ups ("we just sent a calendar invite") unless an automation actually sends them.

## 6. Google Search Console

1. search.google.com/search-console → **Add property** → **Domain** property (covers http/https/www/subdomains) → verify with the DNS TXT record at the domain registrar/DNS host. (URL-prefix property with an HTML file or meta tag is the fallback if DNS access isn't possible.)
2. **Sitemaps** → submit `https://example.com/sitemap.xml`. Status "Success" plus discovered-URL count ≈ number of pages.
3. **URL Inspection** → paste the homepage → **Request indexing**. Repeat for the main hub pages. Everything else is found via sitemap and links; there's a daily quota, so don't request every page.
4. Check **Pages** (indexing) after a few days. Common statuses:
   - *Discovered – currently not indexed* / *Crawled – currently not indexed*: normal for a new site; improve internal links and content uniqueness, and wait.
   - *Duplicate without user-selected canonical* / *Alternate page with proper canonical tag*: check canonicals and redirects.
   - *Excluded by 'noindex' tag*: intended for thank-you/404/portal; a bug anywhere else.
   - *Page with redirect*: fine for old URLs.
   - *Not found (404)*: add a 301 if the URL used to exist or is linked externally.
5. **Enhancements** (Breadcrumbs, Products, etc.) show structured data errors sitewide.
6. **Performance** shows queries, clicks, impressions, position — the main ongoing SEO report. New sites typically take weeks to months to gain impressions.

## 7. Bing Webmaster Tools

bing.com/webmasters → **Import from Google Search Console** (fastest: pulls the verified site and sitemap). Bing's index feeds Bing, DuckDuckGo, Yahoo, Microsoft Copilot and ChatGPT search, so it matters for AEO. Enable **IndexNow** (Netlify/Cloudflare have plugins or you can ping the API on deploy) for near-instant recrawls.

## 8. Google Business Profile

For businesses serving customers in an area:
- business.google.com → create/claim the profile with the exact business name (no keyword stuffing), primary category, phone, website URL (homepage or the relevant location page).
- **No storefront?** Choose "I deliver goods and services to my customers", hide the address, and list service areas (cities/regions, up to 20). Verification is usually by video or phone. Never use a virtual office or fake address — it gets suspended.
- Add services, hours, photos, and a description consistent with the site. Ask real customers for reviews and respond to them.
- Bing Places can import from GBP.

## 9. After launch: what to watch

- Week 1: sitemap processed, homepage indexed, no crawl errors, forms deliver, analytics records visits.
- Weeks 2–8: pages moving from "Discovered" to "Indexed", first impressions in Performance, Core Web Vitals report once there's traffic.
- Ongoing: publish useful content on a steady schedule, add internal links from new posts to service/product pages, fix new 404s with redirects, re-run the audits after every change.
