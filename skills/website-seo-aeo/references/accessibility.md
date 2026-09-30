# Accessibility (and the PageSpeed Accessibility score)

Accessibility overlaps heavily with SEO: alt text, headings, link text, language and semantic HTML are read by search engines and AI parsers the same way screen readers read them. PageSpeed's Accessibility category is built from automated axe-core checks; getting to 100 is realistic for a static site.

## The checks that come up most

**Color contrast (WCAG AA)**
- Normal text needs a contrast ratio ≥ **4.5:1** against its background; large text (≥ 24px, or ≥ 18.66px bold) needs ≥ **3:1**. UI components/icons that convey meaning need ≥ 3:1.
- Common offenders: light grey footer text, placeholder text, small captions, "muted" labels on tinted cards, white text on mid-tone brand colors, text over photos.
- Text over images: put a solid or gradient overlay behind the text area so contrast holds at every image position and screen size; a text-shadow alone isn't counted.
- Run `node scripts/browser_check.js SITE_DIR --contrast` after changing colors. It computes the ratio for every text element against its effective background (skipping elements over background images, which need a manual look).
- When fixing, darken/lighten the text color minimally to pass rather than redesigning — e.g. `#999` on white (2.85:1) → `#6b6b6b` (5.3:1).

**Images**
- Every `<img>` has `alt`. Describe what matters in context ("Attorney reviewing a contract with a client"); use `alt=""` for decorative images and `aria-hidden="true"` on decorative inline SVGs.
- Don't put essential text inside images.

**Names for controls**
- Icon-only buttons and links need an accessible name: `aria-label="Open menu"`, or visually hidden text.
- Links say where they go: avoid multiple "Learn more" links with no context (add `aria-label="Learn more about SEO"` or make the text specific).
- Form inputs have a `<label>` (visible, or `aria-label` at minimum). Placeholder is not a label.

**Document**
- `<html lang="en-US">` (or the right language).
- `<meta name="viewport" content="width=device-width,initial-scale=1">` — never `user-scalable=no` or `maximum-scale=1`; blocking zoom is an accessibility failure.
- Unique `id`s (duplicate ids break labels and anchors — the audit script checks this).
- One `<h1>`, sequential headings.
- Landmarks: `<header>`, `<nav aria-label="Main">`, `<main>`, `<footer>`.

**Keyboard and focus**
- Everything clickable is a real `<a href>` or `<button>`, reachable with Tab, with a visible focus style (`:focus-visible` outline — don't remove outlines without a replacement).
- Dropdown menus open on focus/Enter as well as hover, and close with Escape. Only one open at a time.
- A "Skip to content" link as the first focusable element helps keyboard users on pages with big navs.
- Modals trap focus and return it on close.

**Motion**
- Wrap non-essential animation (parallax, drifting glows, auto-playing carousels, looping borders) in `@media (prefers-reduced-motion: no-preference)` or disable it under `reduce`.
- No content that flashes more than 3 times per second.

**Touch targets**
- Tap targets at least ~44×44 px with spacing, especially in mobile nav and footers.

## Quick manual pass

1. Tab through the page start to finish: can you see where focus is, and reach every link, menu item, and form field?
2. Zoom to 200%: does anything overlap or become unreadable? No horizontal scroll at 320–390px wide? (`browser_check.js` flags horizontal overflow.)
3. Turn images off: does the page still make sense?
4. Run PageSpeed / Lighthouse Accessibility and fix each listed element.
