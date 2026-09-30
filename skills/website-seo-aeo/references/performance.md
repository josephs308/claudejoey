# Performance: PageSpeed and Core Web Vitals

## Contents
1. The targets
2. LCP — the biggest element loads fast
3. CLS — nothing jumps
4. INP — the page responds quickly
5. Images
6. Fonts
7. CSS and JavaScript delivery
8. Caching and cache busting
9. Third-party embeds
10. Common PageSpeed warnings → fixes
11. Measuring

## 1. The targets

Core Web Vitals, "good" thresholds at the 75th percentile of real users:
- **LCP** (Largest Contentful Paint) ≤ 2.5 s
- **INP** (Interaction to Next Paint, replaced FID in 2024) ≤ 200 ms
- **CLS** (Cumulative Layout Shift) ≤ 0.1

PageSpeed Insights shows two things: **field data** (real Chrome users, 28-day window — what Google ranks on) and a **Lighthouse lab score** (a single simulated mobile load on a throttled connection). Optimize for mobile; it's the stricter test and what most visitors use. A static site with the practices below should score 95–100.

## 2. LCP

The LCP element is usually the hero image or the H1 block.
- **Never lazy-load the LCP image.** Give it `fetchpriority="high"` and `loading="eager"` (the default). Lazy-load everything below the fold instead.
- If the LCP image is a CSS background or is discovered late, add `<link rel="preload" as="image" href="…" imagesrcset="…" imagesizes="…" fetchpriority="high">`.
- Serve it from your own domain (a third-party image CDN adds a DNS + TLS connection; if you must, `<link rel="preconnect">` to it).
- Size it for the slot with `srcset`/`sizes` (see Images) — a 2000px image in a 400px phone slot is the most common LCP killer.
- **Different art per breakpoint**: if a big decorative photo only shows on desktop, don't make phones download it. Use `<picture>` with a mobile `<source>` pointing at a tiny placeholder (e.g. a 1×1 transparent GIF data URI) or omit the image under a media query — `display:none` alone does **not** stop the download of an `<img>`:
  ```html
  <picture>
    <source media="(max-width: 980px)" srcset="data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==">
    <source type="image/avif" srcset="/img/hero-960.avif 960w, /img/hero-1440.avif 1440w, /img/hero-2000.avif 2000w" sizes="54vw">
    <source type="image/webp" srcset="/img/hero-960.webp 960w, /img/hero-1440.webp 1440w, /img/hero-2000.webp 2000w" sizes="54vw">
    <img src="/img/hero-1440.jpg" width="1440" height="960" alt="…" fetchpriority="high" decoding="async">
  </picture>
  ```
- Keep render-blocking CSS small (see §7) so text-based LCP paints immediately.
- Fast hosting with a CDN and HTTP/2+ (Netlify, Vercel, Cloudflare Pages all qualify) keeps TTFB low.

## 3. CLS

- `width` and `height` attributes on every `<img>`, `<video>`, `<iframe>` (or CSS `aspect-ratio`) so space is reserved before load.
- Reserve space for anything injected later: cookie banners (overlay, don't push), embeds, ads, "sticky" bars.
- Fonts: use `font-display: swap` with a fallback whose metrics are close (or `size-adjust`/`ascent-override` on the fallback `@font-face`) — or use system fonts and skip the problem.
- Animate with `transform`/`opacity` only; never animate `top`, `height`, `margin`.
- Don't insert content above existing content after load (e.g. a promo bar that slides in on top of the nav).

## 4. INP

- Keep JavaScript small; a static marketing site should need a few KB of vanilla JS, not a framework runtime.
- **Avoid forced reflow / layout thrashing** in scroll and resize handlers: read all layout values (`getBoundingClientRect`, `offsetTop`, `innerHeight`) first, then write styles, inside one `requestAnimationFrame` per frame. Interleaving reads and writes in a loop is a classic PageSpeed "forced reflow" warning.
  ```js
  let ticking = false;
  addEventListener('scroll', () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      const rects = items.map(el => el.getBoundingClientRect());   // all reads
      items.forEach((el, i) => el.classList.toggle('on', rects[i].top < innerHeight * .6)); // then writes
      ticking = false;
    });
  }, { passive: true });
  ```
- Prefer `IntersectionObserver` over scroll handlers for reveal-on-scroll effects.
- Use `{ passive: true }` on scroll/touch listeners.
- Break up long tasks; defer non-critical work with `requestIdleCallback` or `setTimeout(…, 0)`.
- Respect `prefers-reduced-motion`.

## 5. Images

- **Formats**: AVIF first, WebP second, JPEG/PNG fallback via `<picture>`, or let an image CDN negotiate (`auto=format`). SVG for logos and icons (inline small icons to save requests).
- **Responsive**: `srcset` with 3–4 widths (e.g. 640/960/1440/2000) and an accurate `sizes`.
- **Compression**: quality ~75–82 for photos is usually indistinguishable.
- **Lazy-load** below-the-fold images with `loading="lazy"` and `decoding="async"`.
- Provide a graceful fallback if an external image fails (`onerror` hiding the figure) so a dead CDN link doesn't leave a broken-image icon.
- Generate sizes with a script (Pillow / sharp / squoosh) rather than by hand, so every image gets every size.

## 6. Fonts

In order of preference:
1. **System font stacks** (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif`; `Georgia, "Times New Roman", serif`) — zero bytes, zero CLS.
2. **Self-hosted, subset WOFF2** for a brand font. If a font is only used for a logo wordmark, subset it to just those letters — it can be ~1 KB and even inlined as a data URI in the CSS so there's no extra request.
3. Google Fonts etc. only with `display=swap`, preconnect to both `fonts.googleapis.com` and `fonts.gstatic.com`, and only the weights you use.

Preload at most 1–2 critical font files (`<link rel="preload" as="font" type="font/woff2" crossorigin>`); preloading many hurts LCP.

## 7. CSS and JavaScript delivery

- One small site-wide stylesheet (tens of KB) is fine; for larger CSS, inline the critical above-the-fold CSS in `<head>` and load the rest non-blocking.
- Remove unused CSS from old experiments — it adds up.
- Scripts at the end of `<body>` or with `defer`; `async` only for independent third-party scripts.
- No jQuery or UI framework for a brochure site; a few hundred lines of vanilla JS covers nav menus, tabs, accordions and scroll effects.
- Minify HTML/CSS/JS in the build (or let the host do it).

## 8. Caching and cache busting

The failure mode to avoid: a browser pairs new HTML with an old cached stylesheet and the page looks broken.
- **Either** fingerprint asset URLs (`site.3f9a1c.css` or `site.css?v=<hash>`) and cache them long (`Cache-Control: public, max-age=31536000, immutable`)…
- **or** don't fingerprint and use `Cache-Control: public, max-age=0, must-revalidate` so browsers revalidate (cheap 304s on a CDN).
- Never long-cache an un-fingerprinted file.
- HTML itself: short/no cache (hosts default to this).

Netlify `_headers` example:
```
/assets/*
  Cache-Control: public, max-age=0, must-revalidate
/fonts/*
  Cache-Control: public, max-age=31536000, immutable
```

## 9. Third-party embeds

Chat widgets, calendars, maps, video players and tag managers are the usual reason a fast site scores 60.
- Load them on interaction (click-to-load facade for YouTube/maps/chat) or after the page is idle.
- Replace a heavy scheduling embed with a link or a lightweight form when possible.
- Audit Google Tag Manager containers — every tag is JS on the main thread.
- Use `loading="lazy"` on iframes below the fold.

## 10. Common PageSpeed warnings → fixes

| Warning | Fix |
|---|---|
| Largest Contentful Paint image was lazily loaded | Remove `loading="lazy"` from the hero; add `fetchpriority="high"` |
| Properly size images / Serve images in next-gen formats | `srcset`/`sizes`; AVIF/WebP via `<picture>` |
| Eliminate render-blocking resources | Inline critical CSS, `defer` scripts, drop unused font files |
| Reduce unused JavaScript / CSS | Remove libraries and dead rules; lazy-load widgets |
| Avoid large layout shifts | `width`/`height` on media; reserve space for injected UI |
| Forced reflow | Batch DOM reads before writes in one rAF (see §4) |
| Image elements do not have explicit width and height | Add the attributes |
| Serve static assets with an efficient cache policy | Fingerprint + long cache (see §8) — or accept the warning if you chose revalidation deliberately |
| Avoid enormous network payloads | Compress images, drop unused fonts, lazy-load below-fold media |
| Background and foreground colors do not have a sufficient contrast ratio | See `accessibility.md` |
| Links do not have a discernible name | `aria-label` on icon-only links/buttons |

## 11. Measuring

- PageSpeed Insights: https://pagespeed.web.dev — test the homepage and one page per template, mobile first.
- Chrome DevTools → Lighthouse and Performance panel (look for long tasks and layout shifts).
- `scripts/browser_check.js` catches runtime errors, failed requests and mobile overflow before you get to PageSpeed.
- Search Console → Core Web Vitals report shows field data once there's enough traffic.
