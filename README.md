# Thompson Law STL — Website

A modern, custom-coded static website for **Thompson Law STL**, a St. Louis
personal injury law firm led by attorney Tyler Thompson.

Rebuilt from the ground up — no WordPress, no page builder, no database — to
hit the **Vincere four pillars** of a high-performing law firm site.

---

## The four pillars (and how this build delivers them)

### 1. Blazing Speed & Security
- Pure, hand-written **HTML + CSS**, with one small (~6 KB) vanilla-JS file.
- **Zero web-font requests** — the type stack uses system fonts (Helvetica/Georgia),
  so there's nothing to download and no layout shift.
- No framework, no jQuery, no plugins. SVG icons are inlined (no icon font, no
  image sprites).
- **Static = secure**: no CMS, no database, no admin login — nothing to hack.
- Built to pass Core Web Vitals and WCAG 2.1 AA (semantic landmarks, skip link,
  visible focus states, labelled controls, `prefers-reduced-motion` support,
  accessible accordions and nav).

### 2. Legal SEO
- A dedicated, individually optimized page for **every practice area** (not one
  generic "Services" page): car, truck, motorcycle, slip & fall, workplace,
  medical malpractice, dog bites, wrongful death.
- Per-page `<title>`, meta description, canonical URL, Open Graph / Twitter tags.
- Semantic heading hierarchy, descriptive link text, clean file-based URLs.
- `sitemap.xml` and `robots.txt` included.

### 3. Answer Engine Optimization (AEO)
- **Answer-first content**: each practice page opens with a direct, bolded answer
  to the core question, the way featured snippets and AI Overviews extract.
- **FAQPage JSON-LD** on the home page and every practice page (the visible FAQ
  accordion mirrors the structured data exactly).
- **LegalService / Attorney JSON-LD** describing the firm, the attorney, address,
  hours, and service area, plus **BreadcrumbList** on inner pages.
- `robots.txt` explicitly welcomes GPTBot, PerplexityBot, Google-Extended and
  ClaudeBot so the firm can be cited as the answer.

### 4. Conversion Systems
- A **guided-flow intake assistant** (bottom-right chat bubble) that engages
  instantly, qualifies the matter through a few taps, and routes the visitor to
  call or request a consultation — pure client-side, works 24/7, needs no backend.
- Click-to-call phone CTAs in the top bar, header, hero, every page, and footer.
- A hero lead-capture form and a full contact form, both with graceful `mailto:`
  fallback so leads are never lost before a real endpoint is wired up.
- "No fee unless we win" / "free consultation" reinforced throughout.

---

## Project structure

```
.
├── index.html                 # Home
├── about.html                 # Attorney bio (Tyler Thompson)
├── practice-areas.html        # Practice areas overview
├── contact.html               # Contact + lead form
├── car-accidents.html         # Practice area pages ─┐
├── truck-accidents.html                              │
├── motorcycle-accidents.html                         │
├── slip-and-fall.html                                ├─ 8 practice areas
├── workplace-injuries.html                           │
├── medical-malpractice.html                          │
├── dog-bites.html                                    │
├── wrongful-death.html        # ──────────────────────┘
├── robots.txt
├── sitemap.xml
└── assets/
    ├── css/styles.css         # Full design system (one file)
    ├── js/main.js             # Nav, FAQ, scroll reveal, intake assistant
    └── img/
        ├── favicon.svg        # Scales-of-justice mark
        └── og-image.svg       # Social share image
```

## Running locally

It's a static site — just open `index.html` in a browser, or serve the folder:

```bash
python3 -m http.server 8000
# then visit http://localhost:8000
```

## Deploying

Upload the folder to any static host — Netlify, Cloudflare Pages, GitHub Pages,
Vercel, S3/CloudFront, or any plain web server. There is no build step.

## Before going live — customize these

1. **Form endpoint.** The hero and contact forms currently fall back to a
   prefilled `mailto:` to `tyler@thompsonlawstl.com`. To capture leads directly,
   set each `<form>`'s `action` to a real endpoint (e.g. Formspree, Basin, or a
   serverless function) — the JS automatically defers to a real `http(s)` action.
2. **Attorney photo.** `about.html` and the home page use a lettered "TT" avatar
   placeholder. Drop in a professional headshot where marked.
3. **Testimonials.** Reviews use client initials and are representative; replace
   with verified reviews (and link your Google Business Profile) before launch.
4. **Legal review.** Practice-area pages state general Missouri/Illinois rules
   (statutes of limitation, dog-bite strict liability, etc.) with hedging
   language. Have the firm confirm every legal statement for the current year.
5. **Domain & analytics.** Canonicals, sitemap and OG tags assume
   `https://thompsonlawstl.com/`. Add your analytics snippet if desired.

---

_Firm: Thompson Law STL · 167 Lamp and Lantern Village, Suite 226, Chesterfield,
MO 63017 · 314-650-8520 · tyler@thompsonlawstl.com_
