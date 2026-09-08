---
name: astro-site-build
description: >
  Build a static marketing site on Astro to a verifiable quality bar —
  shared components, an SEO head derived rather than hand-written, a strict
  Content-Security-Policy with no inline handlers, WCAG AA colour and
  labelling, and a browser + Lighthouse harness that proves it. Also covers
  porting an existing hand-written HTML site onto that structure without
  losing content. Use this skill whenever building a new marketing or
  brochure site, rebuilding or modernising an old one, migrating hand-edited
  HTML to a framework, taking over someone else's site, or when a site needs
  to hit 100s on Lighthouse — even if Astro is never mentioned by name.
---

# Building a static marketing site that holds up

The failure mode this prevents is not ugliness. It is a site that looks fine
and is quietly wrong: duplicate pages competing in Google, a CSP that claims
protection it doesn't provide, four class names resolving to the same colour,
and eight copies of a nav that drift apart until nobody can safely change one.

Every rule below exists because something specific broke. Where a check is
cheap, run it — the point of this skill is that quality claims come with
numbers attached.

## Set up the project

```bash
npm create astro@latest -- --template minimal
npm install astro@^5
```

`astro.config.mjs` — three settings matter more than the rest:

```js
export default defineConfig({
  site: 'https://example.com',
  build: { format: 'file' },   // /about.html on disk, served at /about
  trailingSlash: 'never',
  compressHTML: true,
  vite: { build: { assetsInlineLimit: 0 } },  // keeps scripts external
});
```

**`build.format`** decides your URL shape, and changing it later splits your
indexed pages in two. `'directory'` (Astro's default) emits
`/about/index.html` and canonicalises to `/about/`. `'file'` emits
`/about.html`, which Netlify and most static hosts serve at `/about`. Pick one
before launch. When adopting a site that is already indexed, match what is
already indexed — do not "improve" it.

**`assetsInlineLimit: 0`** stops Astro inlining small scripts. An inline
`<script>` forces `'unsafe-inline'` into `script-src`, which is the single
directive most worth keeping strict.

## Derive the head, never hand-write it

Give the layout one `name` per page and generate everything from it. Hand-
written heads drift: a real site had five different names for one page across
`<title>`, `og:title`, `twitter:title`, the JSON-LD headline and its
breadcrumb, which split the relevance signal five ways.

```astro
---
const SITE = 'https://example.com';
// With format:'file', Astro.url.pathname is '/about.html'. The canonical is
// the extensionless URL the host actually serves -- emitting the .html form
// is exactly how pages end up as "Duplicate, Google chose different canonical".
const path = Astro.url.pathname
  .replace(/index\.html$/, '').replace(/\.html$/, '').replace(/\/+$/, '');
const canonical = `${SITE}${path || '/'}`;
---
<title>{title}</title>
<link rel="canonical" href={canonical} />
<meta property="og:url" content={canonical} />
<meta property="og:title" content={name} />
<meta name="twitter:title" content={name} />
<script type="application/ld+json" set:html={JSON.stringify(schema)} />
```

Then a page carries only its own facts:

```astro
<BaseLayout
  name="Technical SEO for Law Firm Websites"
  title="Technical SEO for Law Firm Websites — Vincere"
  description="…"
  breadcrumb="Technical SEO"
>
```

Keep the rendered `<title>` at or under 60 characters or Google truncates it.
Check the rendered length, not the source — `&amp;` is one character on screen.

**Sitemap:** write a small endpoint at `src/pages/sitemap.xml.ts` listing only
indexable routes. `@astrojs/sitemap` emits `/sitemap-index.xml`, which 404s the
`/sitemap.xml` already submitted to Search Console. List only pages you want
indexed, so submitted count and indexable count stay equal and any future drift
is visible.

## One definition per thing

| Concern | Home |
|---|---|
| `<head>`, canonical, OG, JSON-LD | `src/layouts/BaseLayout.astro` |
| Header / footer, with variants | `src/components/Site{Header,Footer}.astro` |
| Logo | `src/components/Logo.astro` |
| Tokens, shared components | `src/styles/global.css` |
| Genuinely page-specific CSS | `src/styles/pages/<page>.css` |

Pages differ in chrome more than you expect — a homepage usually has a fuller
nav and footer than inner pages. Give the component a `variant` prop rather
than letting the inner-page version quietly become the only version; that
silently deletes homepage links.

An inlined logo SVG that appears twice per page needs **namespaced gradient
ids**. Duplicate SVG ids are invalid, and the second copy will reference the
first one's gradients.

## Keep the CSP strict

Target `script-src 'self'` with no `'unsafe-inline'`. That holds only while
there are zero inline handlers and zero inline `<script>` blocks.

Replace handlers rather than deleting them:

- **hover** → a CSS class. `:hover` does what `onmouseover` did.
- **click** → `data-action="fnName"` plus one delegated listener on
  `document`. Delegate on `document`, not on a NodeList at load — delegation
  is what covers markup injected at runtime.
- **Enter to submit** → `data-enter="fnName"`, same delegation.
- **image fallback** → a real `error` listener.
- **focus/blur styling** → `:focus` in CSS; the handler is usually redundant.

Then prove it, generically:

```bash
python3 scripts/scan-inline-handlers.py dist
```

Scan for *any* attribute starting with `on`. A hand-written list of the common
ones will miss `onerror`, `onkeydown`, `onfocus` — on one real site that list
undercounted by three and the browser caught what the grep did not.

`style-src` usually still needs `'unsafe-inline'` when inline `style`
attributes remain. Say so plainly rather than implying the whole CSP is strict.

## Accessibility, concretely

Most Lighthouse a11y failures on a marketing site are two things:

- **Contrast.** Mid-greys and brand colours on tinted backgrounds fail AA.
  Check against the background actually used — a green that passes on white
  can fail on a pale green wash. Fix the token, not the instance.
- **Names.** Icon-only buttons and logo links that wrap only an SVG have no
  accessible name. Add `aria-label`. Where a link has visible text, the label
  should contain that text.

Also: one `<h1>` per page, a skip link on every page including utility pages,
and `prefers-reduced-motion` honoured.

## Verify — this is the part that makes the claim real

Build, serve the output **with the production headers**, then:

```bash
npm install --no-save playwright lighthouse

python3 scripts/scan-inline-handlers.py dist
node    scripts/check-browser.mjs   http://localhost:4321 / /about /contact
node    scripts/lighthouse.mjs      http://localhost:4321/ http://localhost:4321/about
```

`check-browser.mjs` catches what static analysis cannot: CSP violations from
handlers created at runtime, JS errors, missing or duplicate `h1`, horizontal
overflow. The CSP must actually be sent by the server or violations never fire.

Keep this tooling out of `dependencies` — otherwise the host downloads a
browser on every deploy. `--no-save` is deliberate.

Expect 100 on all four categories for a static marketing page. Investigate
anything lower rather than accepting it; the one score worth explaining away is
a network failure caused by the sandbox rather than the site.

## Porting an existing hand-written site

Script the transcription. Retyping pages by hand introduces errors that are
invisible until a client notices missing copy.

1. Extract per page: title, description, `og:title`, breadcrumb, body.
2. Strip header/footer — but **remove the footer block itself, not everything
   after it**. Cookie banners, scroll nudges and modals often live past
   `</footer>` and get truncated by a naive split.
3. Carry each page's `<head>` `<style>` across, dropping rules the new global
   stylesheet already defines. Sanitize stray closing braces while you are
   there; hand-edited CSS accumulates orphan `}` from deleted media queries.
4. Convert handlers as above.

Then prove nothing was lost:

```bash
python3 scripts/text-parity.py old_build/ dist/
```

Matching word counts with zero missing words is the evidence. A small positive
delta is expected where you added a skip link.

## Deployment (Netlify)

```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "22"
```

Pin the Node version — once a site has a build step, the deploy depends on the
runtime and a change to the host's default image will fail it. Put `_redirects`
and `_headers` in `public/`, with a `301!` line for every page's alternate URL
form.

Moving a site from "copy files to CDN" to "run a build" introduces a failure
mode that did not exist before: the build can fail. Say so when handing over,
and check the deploy log rather than assuming.
