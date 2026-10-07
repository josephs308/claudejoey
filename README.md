# Thompson Law STL: concept site

A concept redesign of [thompsonlawstl.com](https://thompsonlawstl.com/) for Thompson Law STL,
a St. Louis personal injury firm led by Tyler Thompson. Prepared by Vincere Legal Marketing.
The header and hero follow the Kessler demo: dark navy and gold, a heavy Unbounded caps
headline, a case review card and Tyler's portrait. Everything below follows McMillan & Black:
Source Serif 4 headlines, Source Sans body, one navy accent, square corners, the firm's own logo,
plus credited Unsplash photography.

Every page carries a "concept design" banner and a `noindex` tag so it can't be mistaken
for, or outrank, the firm's live site.

## Pages

| File | What it is |
| --- | --- |
| `index.html` | Home: hero with Tyler's portrait and case review form, client quote strip, About Tyler, practice tiles, insurer callout, FAQ, Google reviews, contact |
| `car-accidents.html` and 7 more | One page per practice area: car, truck, motorcycle, slip and fall, workplace, medical malpractice, dog bites, wrongful death |
| `assets/css/site.css` | The whole design system. Change `--accent` (body) and `--gold` (hero) to recolor the site |
| `assets/js/site.js` | Scroll reveals, mobile menu, demo form notice, guided intake chat |
| `assets/fonts/` | Self-hosted fonts (no Google Fonts request) |
| `assets/img/` | Firm logo (navy for light backgrounds, white for dark), favicon, Tyler's headshot |

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
3. **Get a larger headshot.** The one on the site is 400 x 465 px, which looks soft on high-resolution
   screens. A version at least 1000 px wide would be crisper. A vector (SVG) logo would also help.
4. **Reviews** are quoted word for word from the firm's Google Business Profile, shown as first name
   and last initial. Reviews that Google cuts off end at the last visible sentence. Star ratings are
   not shown because we don't have them. Confirm the firm is happy featuring these reviewers.
5. **Confirm the suite number.** Public listings disagree (Suite 226 vs. Suite 236). The site uses 226.
6. **Legal review.** Practice pages state general Missouri and Illinois rules (filing deadlines,
   dog-bite strict liability, medical malpractice affidavits). The firm should confirm them.
7. **Photos** are hotlinked from Unsplash and credited. Swap in the firm's own photography if it has any.
