#!/usr/bin/env python3
"""Write sitemap.xml (and robots.txt if missing) for a folder of built .html files.

Usage: python3 gen_sitemap.py SITE_DIR --domain https://example.com [--exclude /drafts/ ...]

- Skips pages with a robots noindex meta tag, 404.html, and --exclude prefixes.
- <lastmod> is the last git commit date of the built file when it is tracked in
  git, otherwise the file's modification date.
- URLs use the folder style: /about/index.html -> https://example.com/about/
"""
import argparse, datetime, os, re, subprocess
from xml.sax.saxutils import escape


def git_date(path):
    try:
        out = subprocess.run(['git', 'log', '-1', '--format=%cs', '--', path], cwd=os.path.dirname(path) or '.',
                             capture_output=True, text=True, timeout=10).stdout.strip()
        return out or None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root'); ap.add_argument('--domain', required=True)
    ap.add_argument('--exclude', nargs='*', default=[])
    a = ap.parse_args()
    root = os.path.abspath(a.root); domain = a.domain.rstrip('/')
    entries = []
    for d, _, fs in os.walk(root):
        for f in fs:
            if not f.endswith('.html') or f == '404.html': continue
            p = os.path.join(d, f)
            rel = '/' + os.path.relpath(p, root).replace(os.sep, '/')
            url = rel[:-len('index.html')] if rel.endswith('index.html') else rel
            if any(url.startswith(x) for x in a.exclude): continue
            head = open(p, encoding='utf-8', errors='replace').read().split('</head>')[0]
            m = re.search(r'<meta name="robots" content="([^"]*)"', head)
            if m and 'noindex' in m.group(1): continue
            lastmod = git_date(p) or datetime.date.fromtimestamp(os.path.getmtime(p)).isoformat()
            entries.append((url, lastmod))
    entries.sort(key=lambda e: (e[0].count('/'), e[0]))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lm in entries:
        xml.append(f'  <url><loc>{escape(domain + url)}</loc><lastmod>{lm}</lastmod></url>')
    xml.append('</urlset>')
    open(os.path.join(root, 'sitemap.xml'), 'w').write('\n'.join(xml) + '\n')
    robots = os.path.join(root, 'robots.txt')
    if not os.path.exists(robots):
        open(robots, 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {domain}/sitemap.xml\n')
        print('wrote robots.txt')
    print(f'wrote sitemap.xml with {len(entries)} urls')


if __name__ == '__main__':
    main()
