#!/usr/bin/env python3
"""Check URL-form canonicalization on a live static site.

Answers, in one pass, the question that Search Console takes weeks to answer:
does every indexable URL exist in exactly one form, and does every alternate
form 301 to it?

Usage:
    python3 check_canonical.py https://example.com
    python3 check_canonical.py https://example.com/sitemap.xml

Exit code 0 = clean, 1 = problems found. Standard library only.
"""

import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0 (compatible; canonical-check/1.0)"
TIMEOUT = 20


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Report redirects instead of following them -- the status IS the finding."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


opener = urllib.request.build_opener(NoRedirect)


def fetch(url):
    """Return (status, headers, body). Never raises on HTTP status."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        body = ""
        if e.code >= 300 and e.code < 400:
            body = ""
        return e.code, dict(e.headers), body
    except Exception as e:
        return None, {"_error": str(e)}, ""


def tag(pattern, html):
    m = re.search(pattern, html, re.I)
    return m.group(1).strip() if m else None


def canonical_of(html):
    return tag(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)', html) or tag(
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+rel=["\']canonical["\']', html
    )


def og_url_of(html):
    return tag(r'<meta[^>]+property=["\']og:url["\'][^>]+content=["\']([^"\']+)', html)


def is_noindex(html, headers):
    meta = tag(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\']([^"\']+)', html) or ""
    xrt = headers.get("X-Robots-Tag", "")
    return "noindex" in meta.lower() or "noindex" in xrt.lower()


def html_links(html):
    """Internal references that carry a .html extension."""
    refs = re.findall(r'(?:href|action)=["\']([^"\']+)["\']', html, re.I)
    return sorted({r for r in refs if ".html" in r.lower() and not r.lower().startswith("http")})


def alternate_forms(url):
    """The other spellings of this URL that a crawler might find."""
    p = urllib.parse.urlparse(url)
    path = p.path
    out = []
    if path in ("", "/"):
        out.append("/index.html")
    elif path.endswith(".html"):
        out.append(path[: -len(".html")])
    else:
        out.append(path + ".html")
    return [urllib.parse.urlunparse(p._replace(path=a)) for a in out]


def sitemap_urls(target):
    if target.endswith(".xml"):
        sm = target
    else:
        base = target.rstrip("/")
        status, _, body = fetch(base + "/robots.txt")
        found = re.search(r"(?im)^\s*sitemap:\s*(\S+)", body or "")
        sm = found.group(1) if found else base + "/sitemap.xml"
    status, _, body = fetch(sm)
    if status != 200:
        print(f"  sitemap {sm} returned {status}")
        return sm, []
    return sm, re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", body)


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2

    target = sys.argv[1]
    sm, urls = sitemap_urls(target)
    print(f"sitemap: {sm}")
    print(f"listed:  {len(urls)} URL(s)\n")
    if not urls:
        return 1

    problems = []
    notes = []

    for url in urls:
        status, headers, html = fetch(url)
        print(f"{url}")
        print(f"  status              {status}")

        if status is None:
            problems.append(f"{url}: unreachable ({headers.get('_error')})")
            print()
            continue
        if status != 200:
            problems.append(f"{url}: sitemap lists it but it returns {status}")
            print()
            continue

        can = canonical_of(html)
        og = og_url_of(html)
        print(f"  canonical           {can or '(missing)'}")

        if not can:
            problems.append(f"{url}: no canonical tag")
        else:
            cp = urllib.parse.urlparse(can)
            up = urllib.parse.urlparse(url)
            if cp.path.rstrip("/") != up.path.rstrip("/"):
                problems.append(f"{url}: canonical points to a different page -> {can}")
            elif cp.netloc != up.netloc:
                # Normal on a deploy preview: canonicals name the production host.
                notes.append(f"{url}: canonical uses host {cp.netloc} (expected on a preview)")
        if og and can and urllib.parse.urlparse(og).path.rstrip("/") != urllib.parse.urlparse(can).path.rstrip("/"):
            problems.append(f"{url}: og:url {og} disagrees with canonical {can}")

        if is_noindex(html, headers):
            problems.append(f"{url}: in sitemap but marked noindex")
            print("  robots              noindex  <-- conflicts with sitemap")

        for alt in alternate_forms(url):
            astatus, aheaders, _ = fetch(alt)
            loc = aheaders.get("Location", "")
            print(f"  alt {alt}  ->  {astatus} {loc}".rstrip())
            if astatus in (301, 308):
                dest = urllib.parse.urljoin(alt, loc)
                if dest.rstrip("/") != url.rstrip("/"):
                    problems.append(f"{alt}: redirects to {dest}, expected {url}")
            elif astatus == 200:
                problems.append(
                    f"{alt}: serves 200 -- duplicate of {url}. Google may pick this "
                    "form as canonical. Add a forced 301."
                )
            elif astatus not in (404, 410, None):
                problems.append(f"{alt}: unexpected status {astatus}")

        stale = html_links(html)
        if stale:
            problems.append(f"{url}: internal .html references: {', '.join(stale)}")
            print(f"  internal .html refs {', '.join(stale)}")

        print()

    if notes:
        print(f"{len(notes)} note(s):\n")
        for n in notes:
            print(f"  . {n}")
        print()

    if problems:
        print(f"{len(problems)} problem(s):\n")
        for p in problems:
            print(f"  - {p}")
        return 1

    print("Clean: every URL is single-form, self-canonical, and alternates redirect.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
