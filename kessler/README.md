# Kessler & Associates — site rebuild

Ten static pages, no build step. Open `authority-site.html` or serve the folder.

    python3 -m http.server -d kessler 8000

## Files

| File | Page |
| --- | --- |
| `authority-site.html` | Home |
| `authority-car-accident.html` | Car, Truck & Rideshare Accidents |
| `authority-construction.html` | Construction & Labor Law |
| `authority-malpractice.html` | Medical Malpractice |
| `authority-wrongful-death.html` | Wrongful Death |
| `authority-catastrophic.html` | Catastrophic Injuries |
| `authority-premises.html` | Premises Liability |
| `authority-blog-1.html` | After a car accident in NYC |
| `authority-blog-2.html` | New York no-fault explained |
| `authority-blog-3.html` | What a case is worth in New York |
| `assets/site.css` | All styles, tokens first |
| `assets/site.js` | FAQ disclosure, review rail, forms, case screener |

Filenames are unchanged from the previous site so this drops in without breaking
existing URLs or inbound links.

## Design system

Concept is documentary — the firm's authority comes from the record, so the site is
built like one: statutes cited, deadlines tabulated, verdicts in a docket ledger.

**Colour.** Limestone paper `#f6f5f2`, sunken panel `#ecebe5`, ink `#16161a`,
oxblood seal `#8a1c2b` as the single accent, secondary text `#565761`.

**Type.** Bodoni Moda for display, IBM Plex Sans for body, IBM Plex Mono for docket
figures, statute citations and labels. Loaded from Google Fonts with real fallback
stacks.

**Theming.** Every colour is a token declared in the bare `:root`. Dark is a
token-level swap, redefined twice: under `@media (prefers-color-scheme: dark)`
guarded as `:root:not([data-theme="light"])`, and again under
`:root[data-theme="dark"]`. Never style through a media query directly.

**Spacing.** Sections use one `.band` rhythm class; `.band-head` is a two-column
grid. Layout does the spacing via grid/flex `gap`, not per-element margins.

## Before going live

1. **Headshots.** The three attorney photos are Unsplash placeholders. Swap the
   `src` on each `.person img` for real photography. If an image fails to load the
   CSS falls back to a ledger plate plus the attorney's monogram, so the layout
   never breaks.
2. **Forms.** `assets/site.js` validates and shows a confirmation but posts
   nowhere. Point `handleIntake()` at your intake endpoint or CRM.
3. **Case screener.** The widget is a scripted four-question triage, client side
   only — nothing is stored or transmitted. It makes no AI claim.
4. **Review link.** `https://g.page/r/leave-review` is a placeholder; replace with
   the firm's real Google review URL.
5. **Borough pages.** The footer and "where we practice" grid link to
   `authority-manhattan.html` and siblings, which do not exist yet.
6. **Canonicals and schema.** `<link rel="canonical">` and the JSON-LD `@id`s use
   relative paths and `https://kesslerlaw.com`. Point both at the production
   domain.
7. **Verify every figure.** Recoveries, case counts and the statute table carry
   over from the previous site. Statutes cited: CPLR 214(5), 214-a, 208;
   EPTL 5-4.1, 11-3.2; Gen. Mun. Law 50-e; Ins. Law 5102(d); Labor Law 240, 241(6),
   200; NYC Admin. Code 7-210; 11 NYCRR 65-1.1. Have an attorney confirm all of it
   before publication — nothing here has been checked against current law.

## Accessibility

Skip link, landmarks, one `h1` per page, visible focus rings, labelled form
controls with stable ids, `aria-expanded` on every disclosure, `prefers-reduced-motion`
honoured, and no horizontal scroll at 390px.
