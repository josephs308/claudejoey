#!/usr/bin/env python3
"""Find contact emails on law firm websites.

Reads a CSV of firms (a name column and a website column), visits each
firm's own site (home page plus contact, about, attorney and team pages),
and writes every email it finds to a CSV, ranked so the most useful one
for each firm comes first.

Only public pages on the firm's own website are fetched. robots.txt is
respected, and requests to a site are spaced out.

Usage:
    python3 lead-tools/find_emails.py firms.csv
    python3 lead-tools/find_emails.py firms.csv -o leads/emails.csv --max-pages 15

Standard library only, so it runs anywhere Python 3.8+ does.
"""

import argparse
import csv
import html
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser

USER_AGENT = "VincereLeadFinder/1.0 (+https://vincerelegalmarketing.com)"

# Pages most likely to list attorneys or a contact email.
LINK_KEYWORDS = (
    "contact", "about", "attorney", "lawyer", "team", "people", "staff",
    "our-firm", "firm", "partner", "bio", "profile", "meet",
)
GUESSED_PATHS = (
    "/contact", "/contact-us", "/about", "/about-us", "/attorneys",
    "/our-attorneys", "/our-team", "/team", "/lawyers", "/people",
)

# Mailboxes that reach the front desk rather than a person.
GENERIC_PREFIXES = {
    "info", "contact", "office", "admin", "hello", "intake", "help",
    "support", "mail", "email", "inquiries", "inquiry", "law", "legal",
    "frontdesk", "reception", "service", "consult", "consultation",
    "newclient", "newclients", "clients", "team", "staff", "marketing",
    "billing", "accounting", "careers", "jobs", "hr", "noreply", "no-reply",
}

# Emails that show up in site code but never belong to the firm.
JUNK_DOMAINS = {
    "example.com", "domain.com", "email.com", "yourdomain.com", "sentry.io",
    "wixpress.com", "sentry-next.wixpress.com", "godaddy.com", "squarespace.com",
    "wordpress.com", "w3.org", "schema.org", "googleapis.com", "google.com",
    "gstatic.com", "cloudflare.com", "jquery.com", "gravatar.com",
}
JUNK_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
# "jane [at] firm [dot] com" and "jane (at) firm (dot) com"
OBFUSCATED_RE = re.compile(
    r"([A-Za-z0-9._%+-]+)\s*[\[\(]\s*at\s*[\]\)]\s*([A-Za-z0-9-]+(?:\s*[\[\(]\s*dot\s*[\]\)]\s*[A-Za-z0-9-]+)+)",
    re.IGNORECASE,
)


class PageParser(HTMLParser):
    """Collects links, mailto addresses and Cloudflare-protected emails."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []          # (href, anchor text)
        self.mailtos = []        # (email, anchor text)
        self.cf_emails = []
        self.text_parts = []
        self._href = None
        self._anchor_text = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("data-cfemail"):
            self.cf_emails.append(attrs["data-cfemail"])
        if tag == "a":
            self._href = attrs.get("href") or ""
            self._anchor_text = []

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            text = " ".join("".join(self._anchor_text).split())
            href = self._href.strip()
            if href.lower().startswith("mailto:"):
                address = urllib.parse.unquote(href[7:].split("?")[0]).strip()
                self.mailtos.append((address, text))
            elif "/cdn-cgi/l/email-protection#" in href:
                self.cf_emails.append(href.split("#", 1)[1])
            else:
                self.links.append((href, text))
            self._href = None

    def handle_data(self, data):
        self.text_parts.append(data)
        if self._href is not None:
            self._anchor_text.append(data)


def decode_cfemail(encoded):
    """Decode Cloudflare's email obfuscation (XOR with the first byte)."""
    try:
        key = int(encoded[:2], 16)
        return "".join(chr(int(encoded[i:i + 2], 16) ^ key) for i in range(2, len(encoded), 2))
    except ValueError:
        return ""


def normalize_site(url):
    url = url.strip()
    if not url:
        return ""
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}"


def base_domain(netloc):
    netloc = netloc.lower().split(":")[0]
    return netloc[4:] if netloc.startswith("www.") else netloc


def clean_email(raw):
    email = raw.strip().strip(".,;:'\"<>()[]").lower()
    if not EMAIL_RE.fullmatch(email):
        return ""
    local, domain = email.rsplit("@", 1)
    if domain in JUNK_DOMAINS or any(domain.endswith("." + d) for d in JUNK_DOMAINS):
        return ""
    if email.endswith(JUNK_EXTENSIONS) or len(local) > 40:
        return ""
    # Hex-looking hashes from tracking scripts.
    if re.fullmatch(r"[0-9a-f]{16,}", local):
        return ""
    return email


def name_from_local(local):
    """Best guess at a person's name from john.smith / john_smith / jsmith."""
    pieces = [p for p in re.split(r"[._-]+", local) if p.isalpha()]
    if len(pieces) >= 2:
        return " ".join(p.capitalize() for p in pieces[:3])
    return ""


def looks_like_name(text):
    words = text.split()
    return 2 <= len(words) <= 4 and all(w[:1].isupper() and w.replace(".", "").isalpha() for w in words)


class Fetcher:
    def __init__(self, timeout, delay):
        self.timeout = timeout
        self.delay = delay
        self.robots = {}

    def allowed(self, url):
        parts = urllib.parse.urlsplit(url)
        root = f"{parts.scheme}://{parts.netloc}"
        if root not in self.robots:
            rp = urllib.robotparser.RobotFileParser()
            try:
                req = urllib.request.Request(root + "/robots.txt", headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    rp.parse(resp.read().decode("utf-8", "replace").splitlines())
            except Exception:
                rp.parse([])  # No readable robots.txt: everything allowed.
            self.robots[root] = rp
        return self.robots[root].can_fetch(USER_AGENT, url)

    def get(self, url):
        if not self.allowed(url):
            return None, url
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if "html" not in (resp.headers.get("Content-Type") or "html"):
                    return None, resp.geturl()
                body = resp.read(2_000_000).decode(resp.headers.get_content_charset() or "utf-8", "replace")
                return body, resp.geturl()
        except (urllib.error.URLError, TimeoutError, ValueError, ConnectionError, OSError):
            return None, url
        finally:
            time.sleep(self.delay)


def crawl_firm(firm, site, fetcher, max_pages):
    """Visit up to max_pages pages on one firm's site and collect emails."""
    root = normalize_site(site)
    if not root:
        return firm, site, {}, "no website"
    home_domain = base_domain(urllib.parse.urlsplit(root).netloc)

    queue = [root + "/"] + [root + p for p in GUESSED_PATHS]
    seen, found = set(), {}  # email -> {"page", "name"}
    pages_ok = 0

    while queue and len(seen) < max_pages:
        url = queue.pop(0).split("#")[0]
        if url in seen:
            continue
        seen.add(url)
        body, final_url = fetcher.get(url)
        if not body and pages_ok == 0 and url == root + "/" and root.startswith("https://"):
            # Some small-firm sites still only answer on plain http.
            root = "http://" + root[len("https://"):]
            queue = [root + "/"] + [root + p for p in GUESSED_PATHS]
            body, final_url = fetcher.get(root + "/")
            seen.add(root + "/")
        if not body:
            continue
        pages_ok += 1
        # Follow redirects to the firm's real domain (e.g. http -> https://www).
        home_domain = base_domain(urllib.parse.urlsplit(final_url).netloc) if pages_ok == 1 else home_domain

        parser = PageParser()
        try:
            parser.feed(body)
        except Exception:
            continue

        def add(email, name=""):
            email = clean_email(email)
            if email and email not in found:
                found[email] = {"page": final_url, "name": name}
            elif email and name and not found[email]["name"]:
                found[email]["name"] = name

        for address, text in parser.mailtos:
            add(address, text if looks_like_name(text) else "")
        for encoded in parser.cf_emails:
            add(decode_cfemail(encoded))
        text = html.unescape(" ".join(parser.text_parts))
        for match in EMAIL_RE.findall(text):
            add(match)
        for user, rest in OBFUSCATED_RE.findall(text):
            domain = re.sub(r"\s*[\[\(]\s*dot\s*[\]\)]\s*", ".", rest, flags=re.IGNORECASE)
            add(f"{user}@{domain}")

        # Queue same-site pages that look like contact/about/attorney pages.
        for href, anchor in parser.links:
            absolute = urllib.parse.urljoin(final_url, href)
            parts = urllib.parse.urlsplit(absolute)
            if parts.scheme not in ("http", "https") or base_domain(parts.netloc) != home_domain:
                continue
            if parts.path.lower().endswith((".pdf",) + JUNK_EXTENSIONS):
                continue
            haystack = (parts.path + " " + anchor).lower()
            if any(k in haystack for k in LINK_KEYWORDS):
                queue.append(f"{parts.scheme}://{parts.netloc}{parts.path}")

    status = "ok" if pages_ok else "site unreachable"
    return firm, root, {"emails": found, "domain": home_domain}, status


def rank(email, info, firm_domain):
    """Higher is better: on the firm's own domain, and a person over a shared inbox."""
    local, domain = email.split("@")
    on_domain = domain == firm_domain or domain.endswith("." + firm_domain)
    generic = local in GENERIC_PREFIXES or local.split(".")[0] in GENERIC_PREFIXES
    score = (2 if on_domain else 0) + (0 if generic else 1)
    return score, ("generic" if generic else "personal"), on_domain


def read_firms(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.lower().strip(): c for c in reader.fieldnames or []}
        name_col = next((cols[c] for c in ("firm", "name", "firm name", "company") if c in cols), None)
        site_col = next((cols[c] for c in ("website", "url", "site", "domain") if c in cols), None)
        if not site_col:
            sys.exit(f"{path} needs a website column (website, url, site or domain). Found: {reader.fieldnames}")
        for row in reader:
            yield (row.get(name_col, "") if name_col else "").strip(), row[site_col].strip()


def main():
    ap = argparse.ArgumentParser(description="Find contact emails on law firm websites.")
    ap.add_argument("input", help="CSV with a firm name column and a website column")
    ap.add_argument("-o", "--output", default="leads/emails.csv", help="output CSV (default: leads/emails.csv)")
    ap.add_argument("--max-pages", type=int, default=12, help="pages to visit per firm (default 12)")
    ap.add_argument("--workers", type=int, default=4, help="firms to crawl at once (default 4)")
    ap.add_argument("--delay", type=float, default=1.0, help="seconds between requests to a site (default 1)")
    ap.add_argument("--timeout", type=float, default=15, help="seconds before a page request gives up (default 15)")
    args = ap.parse_args()

    firms = list(read_firms(args.input))
    print(f"Checking {len(firms)} firms...", file=sys.stderr)

    rows, no_email = [], []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(crawl_firm, firm, site, Fetcher(args.timeout, args.delay), args.max_pages)
                   for firm, site in firms]
        for done, future in enumerate(as_completed(futures), 1):
            firm, site, result, status = future.result()
            emails = result.get("emails", {}) if result else {}
            if not emails:
                no_email.append((firm, site, status if status != "ok" else "no email found"))
            ranked = sorted(
                ((email, info) + rank(email, info, result["domain"]) for email, info in emails.items()),
                key=lambda r: -r[2],
            )
            for position, (email, info, score, kind, on_domain) in enumerate(ranked, 1):
                rows.append({
                    "firm": firm,
                    "website": site,
                    "email": email,
                    "type": kind,
                    "on_firm_domain": "yes" if on_domain else "no",
                    "name_guess": info["name"] or (name_from_local(email.split("@")[0]) if kind == "personal" else ""),
                    "rank": position,
                    "found_on": info["page"],
                })
            print(f"  [{done}/{len(firms)}] {firm or site}: {len(emails)} email(s)", file=sys.stderr)

    import os
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    fields = ["firm", "website", "email", "type", "on_firm_domain", "name_guess", "rank", "found_on"]
    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: (r["firm"].lower(), r["rank"])))
        for firm, site, reason in no_email:
            writer.writerow({"firm": firm, "website": site, "email": "", "type": reason})

    with_email = len(firms) - len(no_email)
    personal = len({r["firm"] for r in rows if r["type"] == "personal"})
    print(f"\nDone. {with_email}/{len(firms)} firms had at least one email; "
          f"{personal} had a personal (non-generic) address.\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
