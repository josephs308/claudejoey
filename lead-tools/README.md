# Lead tools

## find_emails.py

Finds contact emails on law firm websites, so outreach can go straight to the
attorney or office manager instead of the front desk.

For each firm it visits the home page plus the pages most likely to list
people (contact, about, attorneys, team, bios), up to 12 pages per firm, and
collects every email it finds: `mailto:` links, plain-text addresses,
Cloudflare-protected addresses, and "name [at] firm [dot] com" spellings.

### Run it

1. Make a CSV with a firm name column and a website column:

   ```csv
   Firm Name,Website
   Smith Law,smithlaw.com
   Lopez & Partners,https://www.lopezpartners.com
   ```

   Column names are flexible: `firm`/`name`/`company` and
   `website`/`url`/`site`/`domain` all work.

2. Run:

   ```bash
   python3 lead-tools/find_emails.py firms.csv
   ```

   Results go to `leads/emails.csv` (change it with `-o`). No installs needed;
   it only uses Python's standard library.

### What you get

One row per email, best first for each firm:

| Column | Meaning |
|---|---|
| `type` | `personal` (jsmith@, john.smith@) or `generic` (info@, intake@). Firms with nothing found say why: `no email found`, `site unreachable` or `no website`. |
| `on_firm_domain` | `yes` if the email is on the firm's own domain |
| `name_guess` | From the link text or the address, e.g. john.smith@ becomes John Smith |
| `rank` | 1 is the best address for that firm: personal and on the firm's domain first |
| `found_on` | The page it was found on, so you can check the person's title |

### Options

| Flag | Default | What it does |
|---|---|---|
| `--max-pages` | 12 | Pages to visit per firm |
| `--workers` | 4 | Firms checked at the same time |
| `--delay` | 1 | Seconds between requests to the same site |
| `-o` | `leads/emails.csv` | Output file |

### Rules for using the results

- It only reads firms' own public websites, follows robots.txt, and spaces out
  requests. Don't point it at state bar directories or Avvo; their terms ban
  scraping.
- `leads/` is in `.gitignore`. Keep lead lists out of the repo.
- Cold email to businesses is legal in the US under the CAN-SPAM Act only if every
  email has a real reply-to address, your business's physical mailing address,
  and a clear way to opt out, and you honor opt-outs within 10 business days.
- Check `found_on` before emailing: a personal address on a bio page usually
  belongs to that attorney, but confirm the name and title first.

## market_review.py

Builds the market review deck for a prospect. Give it the firm's website,
name, practice area and city; it checks what it can automatically, scores the
firm, ranks the biggest leaks, and writes a 14-slide deck you screen-share on
the 15-minute market review.

### Run it

```bash
python3 lead-tools/market_review.py --site smithlaw.com --firm "Smith Law" \
    --practice "personal injury" --city "Austin, TX" --attorney "Jane Smith"
```

Everything lands in `leads/reviews/<firm>/` (kept out of git):

| File | What it is |
|---|---|
| `market-review.html` | The deck. Open it in Chrome, press **P** to present, ← → to move, **N** for your notes |
| `market-review.pdf` | The same deck as a PDF, to send after the call (needs Chrome installed) |
| `rep-notes.md` | Internal only: which agency built their site, their CRM and tracking, the angle to take, questions to ask, a talk track per slide |
| `growth-plan.md` | The "where you stand" and competitor fields, ready to paste into the growth plan template |
| `data.json` | Everything collected. Edit it and re-render with `--from` |

### What it checks

| Area | How | Automatic? |
|---|---|---|
| Website and speed | Reads the home and contact pages; Google PageSpeed mobile score | Yes |
| Turning visitors into leads | Tap-to-call, contact form, chat or text, online booking | Yes |
| Google profile and reviews | Rating, reviews and hours from the Places API; top competitors for "[practice] lawyer in [city]" | With `GOOGLE_API_KEY` |
| AI search | Asks Claude (with web search) for the best [practice] lawyers in [city] and checks if the firm is named | With `ANTHROPIC_API_KEY` |
| After-hours calls | You call the main line after 6 pm as a new client | By hand: `--call-test` |
| Tracking leads to cases | Analytics, ad conversion tags, call tracking, CRM | Yes |

A check that can't run is marked "Not checked" and left out of the score, not
failed. The deck still builds.

### Before the review

1. Run it with the website, name, practice and city.
2. Call the firm after hours as a new client, then re-run with the result:

   ```bash
   python3 lead-tools/market_review.py --from leads/reviews/smith-law/data.json \
       --call-test voicemail --call-when "Tue 7:40 pm" --callback "next morning"
   ```

   `--call-test` is `live`, `service`, `voicemail`, `no-answer` or `full-mailbox`.
   For voicemail, `--callback` is how long until they called back (`12 min`,
   `3 hours`, `next morning`) or `none`.
3. Read `rep-notes.md`.

### On or after the call

The "What it's worth" slide shows blanks until you have the firm's own numbers.
Re-run with them and the slide does the math:

```bash
python3 lead-tools/market_review.py --from leads/reviews/smith-law/data.json \
    --monthly-calls 120 --after-hours-share 35 --close-rate 30 --case-value 9000 \
    --contract-end "March 2027" --vendors 3
```

### Without API keys

Fill the gaps by hand:

```bash
--rating 4.6 --reviews 41 \
--competitor "Hartley Injury Lawyers; 4.9; 612" --competitor "Lone Star Accident; 4.8; 388" \
--mobile-score 38 \
--ai-named no --ai-firms "Hartley Injury Lawyers; Lone Star Accident"
```

(Get the mobile score from pagespeed.web.dev and ask ChatGPT yourself.)

### Keys

- `GOOGLE_API_KEY`: one Google Cloud key with **PageSpeed Insights API** and
  **Places API (New)** turned on. PageSpeed works without a key but gets rate
  limited. Places is billed per request; a review uses 2 searches.
- `ANTHROPIC_API_KEY`: for the AI search check. Needs `pip install anthropic`.
  One review is one request with a few web searches.

### Rules

- The deck states facts about competing law firms from public Google data. It
  never criticizes them. Agency names stay in `rep-notes.md` only.
- The cost slide only uses the firm's own numbers. Never fill them in for them.
- It reads only the firm's own public pages and follows robots.txt.
