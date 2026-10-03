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
