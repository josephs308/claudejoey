# Thompson Law STL: concept site

A concept redesign of [thompsonlawstl.com](https://thompsonlawstl.com/) for Thompson Law STL,
a St. Louis personal injury firm led by Tyler Thompson. Prepared by Vincere Legal Marketing,
using the same design system as the McMillan & Black demo: Cormorant Garamond headlines,
Source Sans body, one accent color (navy here), square corners and real photography.

Every page carries a "concept design" banner and a `noindex` tag so it can't be mistaken
for, or outrank, the firm's live site.

## Pages

| File | What it is |
| --- | --- |
| `index.html` | Home: hero with case review form, client quote strip, firm intro, practice tiles, insurer callout, attorney bio, FAQ, testimonials, contact |
| `car-accidents.html` and 7 more | One page per practice area: car, truck, motorcycle, slip and fall, workplace, medical malpractice, dog bites, wrongful death |
| `assets/css/site.css` | The whole design system. Change `--accent` to recolor the site |
| `assets/js/site.js` | Scroll reveals, mobile menu, demo form notice, guided intake chat |
| `assets/fonts/` | Self-hosted fonts (no Google Fonts request) |

## The four pillars

- **Speed and security:** hand-written HTML and CSS, one 5 KB script, self-hosted fonts, responsive
  images. No CMS, database or plugins.
- **Legal SEO:** a dedicated page per practice area with its own title, description and canonical
  URL, internal links between related areas, breadcrumbs, `sitemap.xml`.
- **Answer engine optimization:** answer-first copy, FAQ sections whose `FAQPage` structured data
  matches the visible questions word for word, plus `LegalService`, `Person` and `BreadcrumbList` data.
- **Conversion:** case review form in every hero, a guided intake chat, click-to-call throughout,
  and a call / free review bar pinned to the bottom on phones.

## Preview

```bash
python3 -m http.server 8000   # then open http://localhost:8000
```

No build step. It deploys to Netlify, GitHub Pages or any static host as is (publish directory: `.`).

## Before it goes live

1. **Remove the concept markers:** the `noindex` meta tag and the concept banner on every page.
2. **Connect the forms.** They show a "demo only" notice. On Netlify, Netlify Forms is the simplest option.
3. **Add Tyler's portrait** in place of the placeholder in the Attorney section.
4. **Confirm the testimonials.** They are taken from the firm's current website; confirm the exact
   wording, or replace them with reviews from the Google Business Profile.
5. **Confirm the suite number.** Public listings disagree (Suite 226 vs. Suite 236). The site uses 226.
6. **Legal review.** Practice pages state general Missouri and Illinois rules (filing deadlines,
   dog-bite strict liability, medical malpractice affidavits). The firm should confirm them.
7. **Photos** are hotlinked from Unsplash and credited. Swap in the firm's own photography if it has any.
