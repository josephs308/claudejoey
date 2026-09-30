#!/usr/bin/env python3
"""Static SEO / AEO / HTML audit for a folder of built .html files.

Usage:
  python3 audit_site.py SITE_DIR [--domain https://example.com] [--ignore /portal/ ...]
                        [--title-max 60] [--desc-min 120] [--desc-max 160] [--banned WORD ...]

Checks every page for: title and meta description (present, length, unique),
canonical (present, equals domain + URL), sitemap membership for indexable pages,
exactly one <h1>, heading level skips, JSON-LD (parses, @id refs resolve, FAQ
questions visible on the page, breadcrumb targets exist), broken internal links
and #anchors (same page and cross page), duplicate ids, unclosed/stray tags,
<img> without alt, missing lang / viewport, missing OG / Twitter tags.

Prints one line per issue and ends with "ISSUES <n>". Exit code 1 if n > 0.
If --domain is omitted it is inferred from the homepage canonical.
"""
import argparse, html, json, os, re, sys
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr',
        'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'stop', 'use', 'ellipse'}
OPTIONAL_CLOSE = {'li', 'p', 'td', 'tr', 'th', 'option', 'dt', 'dd', 'thead', 'tbody', 'tfoot'}


class TagCheck(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.errors = []; self.ids = []

    def _id(self, attrs):
        d = dict(attrs)
        if d.get('id'): self.ids.append(d['id'])

    def handle_starttag(self, tag, attrs):
        self._id(attrs)
        if tag not in VOID: self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self._id(attrs)

    def handle_endtag(self, tag):
        if tag in VOID: return
        if self.stack and self.stack[-1] == tag: self.stack.pop(); return
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i] == tag:
                unclosed = [t for t in self.stack[i + 1:] if t not in OPTIONAL_CLOSE]
                if unclosed: self.errors.append(f'unclosed {unclosed} before </{tag}> (line {self.getpos()[0]})')
                del self.stack[i:]; return
        self.errors.append(f'stray </{tag}> (line {self.getpos()[0]})')


def text_of(s):
    s = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', ' ', s, flags=re.S | re.I)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).replace('’', "'").strip()


def norm(t):
    return re.sub(r'\s+', ' ', html.unescape(t)).replace('’', "'").strip()


def walk_graph(node, found):
    """Collect every @type / @id node from nested JSON-LD."""
    if isinstance(node, dict):
        if '@type' in node: found.append(node)
        for v in node.values(): walk_graph(v, found)
    elif isinstance(node, list):
        for v in node: walk_graph(v, found)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('root')
    ap.add_argument('--domain')
    ap.add_argument('--ignore', nargs='*', default=[], help='URL prefixes whose links are not checked (e.g. an app served elsewhere)')
    ap.add_argument('--title-max', type=int, default=60)
    ap.add_argument('--desc-min', type=int, default=120)
    ap.add_argument('--desc-max', type=int, default=160)
    ap.add_argument('--banned', nargs='*', default=['lorem ipsum', 'TODO', 'PLACEHOLDER'],
                    help='strings that must not appear in page text')
    a = ap.parse_args()
    root = os.path.abspath(a.root)

    pages = {}
    for d, _, fs in os.walk(root):
        for f in fs:
            if f.endswith('.html'):
                p = os.path.join(d, f)
                rel = '/' + os.path.relpath(p, root).replace(os.sep, '/')
                url = rel[:-len('index.html')] if rel.endswith('/index.html') or rel == '/index.html' else rel
                pages[url] = (p, open(p, encoding='utf-8', errors='replace').read())

    domain = a.domain
    if not domain and '/' in pages:
        m = re.search(r'<link rel="canonical" href="(https?://[^/"]+)', pages['/'][1])
        domain = m.group(1) if m else ''
    domain = (domain or '').rstrip('/')

    sm_path = os.path.join(root, 'sitemap.xml')
    sm_urls = set(re.findall(r'<loc>\s*(.*?)\s*</loc>', open(sm_path).read())) if os.path.exists(sm_path) else None

    def exists(path):
        path = path.split('#')[0].split('?')[0]
        if not path or any(path.startswith(x) for x in a.ignore): return True
        fp = os.path.join(root, path.lstrip('/'))
        return os.path.isfile(fp) or os.path.isfile(os.path.join(fp, 'index.html')) or os.path.isfile(fp + '.html')

    def file_for(path):
        fp = os.path.join(root, path.lstrip('/'))
        for c in (fp, os.path.join(fp, 'index.html'), fp + '.html'):
            if os.path.isfile(c): return c

    issues = []
    add = lambda u, msg: issues.append((u, msg))
    titles, descs = {}, {}
    if sm_urls is None: add('/sitemap.xml', 'missing sitemap.xml')
    if not os.path.exists(os.path.join(root, 'robots.txt')): add('/robots.txt', 'missing robots.txt')

    for url, (path, s) in sorted(pages.items()):
        head = s.split('</head>')[0]
        body_nostyle = re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '', s, flags=re.S | re.I)
        visible = text_of(s)
        rob = re.search(r'<meta name="robots" content="([^"]*)"', head)
        noindex = bool(rob and 'noindex' in rob.group(1)) or os.path.basename(path) == '404.html'

        t = re.search(r'<title>(.*?)</title>', head, re.S)
        d = re.search(r'<meta name="description" content="([^"]*)"', head)
        c = re.search(r'<link rel="canonical" href="([^"]*)"', head)
        t = norm(t.group(1)) if t else None
        d = norm(d.group(1)) if d else None
        if not t: add(url, 'no <title>')
        elif not noindex and len(t) > a.title_max: add(url, f'title {len(t)} chars (max {a.title_max}): {t}')
        if not d: add(url, 'no meta description') if not noindex else None
        elif not noindex and not (a.desc_min <= len(d) <= a.desc_max): add(url, f'description {len(d)} chars (want {a.desc_min}-{a.desc_max})')
        if not noindex:
            if not c: add(url, 'no canonical')
            elif domain and c.group(1) != domain + url: add(url, f'canonical {c.group(1)} != {domain + url}')
            if t: titles.setdefault(t, []).append(url)
            if d: descs.setdefault(d, []).append(url)
            if sm_urls is not None and domain and domain + url not in sm_urls: add(url, 'indexable page not in sitemap')
            for m in ['og:title', 'og:description', 'og:image', 'og:url', 'twitter:card']:
                if m not in head: add(url, 'missing ' + m)
        elif sm_urls is not None and domain and domain + url in sm_urls:
            add(url, 'noindex page listed in sitemap')

        if not re.search(r'<html[^>]*\blang=', s): add(url, 'no lang on <html>')
        if 'name="viewport"' not in head: add(url, 'no viewport meta')
        vp = re.search(r'name="viewport" content="([^"]*)"', head)
        if vp and re.search(r'user-scalable=no|maximum-scale=1(\.0)?\b', vp.group(1)): add(url, 'viewport blocks zoom')

        h1 = len(re.findall(r'<h1[\s>]', body_nostyle))
        if h1 != 1: add(url, f'{h1} <h1> tags')
        hs = [int(h) for h in re.findall(r'<h([1-6])[\s>]', body_nostyle)]
        for x, y in zip(hs, hs[1:]):
            if y > x + 1: add(url, f'heading skip h{x} -> h{y}'); break

        tc = TagCheck(); tc.feed(body_nostyle)
        for e in tc.errors[:5]: add(url, e)
        left = [x for x in tc.stack if x not in ('html', 'body', 'head') and x not in OPTIONAL_CLOSE]
        if left: add(url, f'left open {left[:6]}')
        dup = sorted({i for i in tc.ids if tc.ids.count(i) > 1})
        if dup: add(url, f'duplicate ids {dup[:6]}')
        for im in re.findall(r'<img\b[^>]*>', s):
            if not re.search(r'\balt=', im): add(url, 'img without alt: ' + im[:80])

        for href in sorted(set(re.findall(r'href="([^"]+)"', s))):
            h = html.unescape(href)
            if h.startswith(('mailto:', 'tel:', 'data:', 'javascript:', 'sms:')): continue
            if h.startswith(('http://', 'https://', '//')):
                if domain and h.startswith(domain): h = h[len(domain):] or '/'
                else: continue
            if h.startswith('#'):
                if len(h) > 1 and h[1:] not in tc.ids: add(url, f'missing anchor {h}')
                continue
            if not h.startswith('/'):
                h = os.path.normpath(os.path.join(os.path.dirname(url if url.endswith('/') else url), h)).replace(os.sep, '/')
            if not exists(h): add(url, 'broken link ' + href); continue
            if '#' in h:
                target, frag = h.split('#', 1)
                fp = file_for(target.split('?')[0])
                if fp and frag and f'id="{frag}"' not in open(fp, encoding='utf-8', errors='replace').read():
                    add(url, f'broken cross-page anchor {href}')

        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
        if not noindex and not blocks: add(url, 'no JSON-LD structured data')
        for blk in blocks:
            try:
                data = json.loads(blk)
            except Exception as ex:
                add(url, f'JSON-LD does not parse: {ex}'); continue
            nodes = []; walk_graph(data, nodes)
            ids = {n.get('@id') for n in nodes if n.get('@id')}
            for n in nodes:
                ty = n['@type'] if isinstance(n['@type'], list) else [n['@type']]
                if 'FAQPage' in ty:
                    for q in n.get('mainEntity', []):
                        if norm(q.get('name', '')) not in visible: add(url, 'FAQ schema question not visible on page: ' + q.get('name', '')[:60])
                if 'BreadcrumbList' in ty:
                    for it in n.get('itemListElement', []):
                        item = it.get('item')
                        item = item.get('@id') if isinstance(item, dict) else item
                        if item and domain and item.startswith(domain) and not exists(item[len(domain):] or '/'):
                            add(url, 'breadcrumb target missing ' + item)
            for ref in set(re.findall(r'\{"@id":\s*"([^"]+)"\}', blk)):
                if ref not in ids: add(url, 'dangling @id reference ' + ref)

        low = visible.lower()
        for bad in a.banned:
            if bad.lower() in low: add(url, f'contains "{bad}"')

    for t, us in titles.items():
        if len(us) > 1: add(', '.join(us), 'duplicate title: ' + t)
    for d, us in descs.items():
        if len(us) > 1: add(', '.join(us), 'duplicate description')

    print(f'{len(pages)} pages; {len(sm_urls) if sm_urls is not None else 0} sitemap urls; domain {domain or "(unknown)"}')
    for u, m in issues: print(f'{u}  {m}')
    print('ISSUES', len(issues))
    sys.exit(1 if issues else 0)


if __name__ == '__main__':
    main()
