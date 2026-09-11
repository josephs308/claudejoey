# MBP Results - Local Services Ads landing page

`index.html` is the whole page. No build step, no dependencies. Open it, or drop it on
any static host. Fonts load from Google Fonts; everything else ships in the file.

## Drop your assets in

Each slot shows a short note until the real file exists, so nothing ever renders broken.

| Path | What it is | Ratio |
| --- | --- | --- |
| `assets/hero.mp4` + `assets/hero-poster.jpg` | Hero video | 16:9 |
| `assets/frustrated-owner.jpg` | "Does this sound like your last LSA campaign?" photo | 4:3 |
| `assets/onboarding.jpg` | Onboarding block photo | 4:3 |
| `assets/lsa-ranking.jpg` | LSA Infrastructure block photo | 4:3 |
| `assets/logos/*.svg` | Six client logos: strike-roofing, simply-dental, mr-amp, zaf, renovate-ease, express-home-services | any |

Until a logo file exists, that slot prints the client name as a wordmark.

## Calendar

The booking section has an empty container marked `class="calendar"`. Paste your
GoHighLevel calendar iframe inside it and delete the note paragraph. Every
"Book A Free Strategy Call" button already points at the strategy call page.

## Budget calculator

The calculator in the Qualified Local Leads block is real. Cost per lead bands live
in the `CPL` object at the bottom of `index.html`. Edit those numbers to match what
you actually see per market.
