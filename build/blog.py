"""Blog: turns build/content/blog/*.md into /blog/ and /blog/<slug>/ pages.

Each post is a Markdown file with a YAML header between --- lines. Files that
start with an underscore, or have `draft: true`, are skipped. See
build/content/blog/_TEMPLATE.md for every supported field.
"""
import datetime, html, os, re
import yaml

WORDS_PER_MIN = 230


def md_inline(t):
    t = html.escape(t, quote=False)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', t)
    t = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![*\w])\*([^*\n]+)\*(?!\*)', r'<em>\1</em>', t)
    return t


def img_url(pid, w, h):
    if pid.startswith('http') or pid.startswith('/'):
        return pid
    return f'https://images.unsplash.com/{pid}?fm=jpg&auto=format&fit=crop&crop=entropy&q=80&w={w}&h={h}'

def img_tag(pid, alt, w, h, cls='', sizes='100vw', eager=False):
    ss = ', '.join(f'{img_url(pid, x, round(x*h/w))} {x}w' for x in (480, 800, 1200, 1600, 2000))
    load = 'eager" fetchpriority="high' if eager else 'lazy'
    return (f'<img class="{cls}" src="{img_url(pid, w, h)}" srcset="{ss}" sizes="{sizes}" width="{w}" height="{h}" '
            f'alt="{html.escape(alt, quote=True)}" loading="{load}" decoding="async" onerror="this.parentNode.classList.add(\'noimg\');this.remove()">')


def md_to_html(src):
    """Small Markdown subset: ## and ### headings, paragraphs, - and 1. lists, > quotes, links, bold, italic."""
    out, para, lst, lst_kind = [], [], [], None

    def flush_para():
        if para:
            out.append('<p>' + md_inline(' '.join(para)) + '</p>')
            para.clear()

    def flush_list():
        nonlocal lst_kind
        if lst:
            out.append(f'<{lst_kind}>' + ''.join(f'<li>{md_inline(x)}</li>' for x in lst) + f'</{lst_kind}>')
            lst.clear()
        lst_kind = None

    for raw in src.strip().splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para(); flush_list(); continue
        mi = re.match(r'^!\[([^\]]*)\]\(([^)\s]+)(?:\s+"([^"]*)")?\)\s*$', line.strip())
        if mi:
            flush_para(); flush_list()
            cap = f'<figcaption>{md_inline(mi.group(3))}</figcaption>' if mi.group(3) else ''
            out.append(f'<figure class="post-fig">{img_tag(mi.group(2), mi.group(1), 1600, 900, sizes="(max-width: 1000px) 100vw, 900px")}{cap}</figure>')
            continue
        m = re.match(r'^(#{2,3})\s+(.*)', line)
        if m:
            flush_para(); flush_list()
            lvl = len(m.group(1))
            out.append(f'<h{lvl}>{md_inline(m.group(2))}</h{lvl}>')
            continue
        m = re.match(r'^\s*[-*]\s+(.*)', line) or re.match(r'^\s*\d+[.)]\s+(.*)', line)
        if m:
            flush_para()
            kind = 'ol' if re.match(r'^\s*\d', line) else 'ul'
            if lst_kind and lst_kind != kind:
                flush_list()
            lst_kind = kind
            lst.append(m.group(1))
            continue
        if line.startswith('>'):
            flush_para(); flush_list()
            out.append('<blockquote><p>' + md_inline(line.lstrip('> ')) + '</p></blockquote>')
            continue
        flush_list()
        para.append(line.strip())
    flush_para(); flush_list()
    return '\n'.join(out)


def load_posts(content_dir):
    posts = []
    d = os.path.join(content_dir, 'blog')
    if not os.path.isdir(d):
        return posts
    for f in sorted(os.listdir(d)):
        if not f.endswith('.md') or f.startswith('_'):
            continue
        raw = open(os.path.join(d, f)).read()
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', raw, re.S)
        if not m:
            raise ValueError(f'{f}: missing the --- header block at the top')
        meta, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
        if meta.get('draft'):
            continue
        for k in ('title', 'description', 'date'):
            if not meta.get(k):
                raise ValueError(f'{f}: "{k}" is required')
        meta['slug'] = meta.get('slug') or f[:-3]
        meta['date'] = str(meta['date'])
        meta['updated'] = str(meta.get('updated') or meta['date'])
        meta['html'] = md_to_html(body)
        meta['cover'] = meta.get('cover') or ''
        meta['cover_alt'] = meta.get('cover_alt') or meta['title']
        words = len(re.sub(r'<[^>]+>', ' ', meta['html']).split())
        meta['minutes'] = max(1, round(words / WORDS_PER_MIN))
        posts.append(meta)
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%B %-d, %Y')


FILTER_JS = "<script>(function(){var cs=document.querySelectorAll('.bh-chip'),cards=document.querySelectorAll('.blog-card');cs.forEach(function(b){b.addEventListener('click',function(){var c=b.dataset.cat;cs.forEach(function(x){x.classList.toggle('on',x===b)});cards.forEach(function(k){k.hidden=!(c==='all'||k.dataset.cat===c)});});});})();</script>"

def build_blog(B):
    """B is the build module (helpers, constants, SITEMAP)."""
    e, DOMAIN = B.e, B.DOMAIN
    posts = load_posts(B.CONTENT)
    if not posts:
        return []
    ARTICLE = {'@type': 'Organization', '@id': B.ORG_ID}
    for p in posts:
        if not p['cover']:
            for sv in p.get('related_services', []):
                if sv in B.SVC_PHOTOS:
                    p['cover'], p['cover_alt'] = B.SVC_PHOTOS[sv][0], B.SVC_PHOTOS[sv][1]; break

    for p in posts:
        url = f'/blog/{p["slug"]}/'
        crumbs = [('Home', '/'), ('Blog', '/blog/'), (p['title'], url)]
        title = p.get('seo_title') or f'{p["title"]} | Vincere'
        schema = [B.org_node(), B.website_node(),
                  B.webpage_node(url, 'WebPage', title, p['description'], {'mainEntity': {'@id': f'{DOMAIN}{url}#article'}}),
                  B.crumbs_node(url, crumbs),
                  {'@type': 'BlogPosting', '@id': f'{DOMAIN}{url}#article', 'headline': p['title'],
                   'description': p['description'], 'datePublished': p['date'], 'dateModified': p['updated'],
                   'author': ARTICLE, 'publisher': ARTICLE, 'mainEntityOfPage': {'@id': f'{DOMAIN}{url}#webpage'},
                   'image': (img_url(p['cover'], 1200, 630) if p['cover'] else f'{DOMAIN}/assets/og-image.png'), 'inLanguage': 'en-US',
                   'articleSection': p.get('category', 'Law firm marketing'), 'wordCount': len(re.sub(r'<[^>]+>', ' ', p['html']).split())}]
        if p.get('faqs'):
            schema.append(B.faq_node(url, p['faqs']))
        meta_line = f'<span>{e(p.get("category", "Law firm marketing"))}</span><span>{nice_date(p["date"])}</span><span>{p["minutes"]} min read</span>'
        if p['updated'] != p['date']:
            meta_line += f'<span>Updated {nice_date(p["updated"])}</span>'
        lead = (f'<div class="answer post-answer"><span class="answer-tag">Quick answer</span><div><h2 class="qa-h">{e(p["summary_question"])}</h2><p>{e(p["summary"])}</p></div></div>') if p.get('summary') and p.get('summary_question') else ''
        related_svc = ''.join(f'<a class="rel-c" href="{B.svc_url(s)}"><div class="rel-tag">Service</div><h3>{e(B.SVC[s][1])}</h3><p>{e(B.SVC[s][2])}.</p><span class="rel-arr">See the service &rarr;</span></a>'
                              for s in p.get('related_services', []) if s in B.SVC)
        others = [o for o in posts if o['slug'] != p['slug']][:3]
        more = ''.join(f'<a class="rel-c" href="/blog/{o["slug"]}/"><div class="rel-tag">{e(o.get("category", "Blog"))}</div><h3>{e(o["title"])}</h3><p>{e(o["description"])}</p><span class="rel-arr">Read the post &rarr;</span></a>' for o in others)
        body = f'''<header class="phero post-hero">
  <div class="wrap phero-in">
    {B.crumb_html(crumbs)}
    <h1>{e(p["title"])}</h1>
    <p class="post-meta">{meta_line}</p>
  </div>
</header>
{f'<div class="wrap post-cover-wrap"><figure class="post-cover">{img_tag(p["cover"], p["cover_alt"], 1600, 640, sizes="(max-width: 1400px) 100vw, 1280px", eager=True)}</figure></div>' if p["cover"] else ""}
<article class="sec post">
  <div class="wrap">{B.article_layout(p["html"], lead)}</div>
</article>
{B.faq_html(p["faqs"], "Questions about this topic") if p.get("faqs") else ""}
{f'<section class="sec sec-tight"><div class="wrap"><div class="sec-head"><h2>Services mentioned in this post.</h2></div><div class="rel">{related_svc}</div></div></section>' if related_svc else ""}
{f'<section class="sec sec-tight"><div class="wrap"><div class="sec-head"><h2>More from the blog.</h2></div><div class="rel">{more}</div></div></section>' if more else ""}'''
        B.write(url, B.page(url, title, p['description'], schema, body).replace('<main id="main">', '<main id="main" class="svcp blogp">', 1))
        B.SITEMAP.append((url, '0.7'))

    # index
    url = '/blog/'
    crumbs = [('Home', '/'), ('Blog', url)]
    title = 'Law Firm Marketing Blog | Vincere Legal Marketing'
    desc = 'Plain-English guides on law firm marketing: SEO, AEO, Local Services Ads, PPC, intake and budgets, written for managing partners who want signed cases.'
    def card(p, feat=False):
        pic = f'<div class="bc-img">{img_tag(p["cover"], p["cover_alt"], 1200 if feat else 800, 700 if feat else 480, sizes="(max-width: 900px) 100vw, " + ("720px" if feat else "420px"))}</div>' if p['cover'] else '<div class="bc-img noimg"></div>'
        return (f'<a class="blog-card{" feat" if feat else ""}" data-cat="{e(p.get("category", "Law firm marketing"))}" href="/blog/{p["slug"]}/">{pic}<div class="bc-body">'
                f'<span class="bc-cat">{e(p.get("category", "Law firm marketing"))}</span><h2>{e(p["title"])}</h2><p>{e(p["description"])}</p>'
                f'<span class="bc-meta">{nice_date(p["date"])} &middot; {p["minutes"]} min read</span></div></a>')
    cards = card(posts[0], True) + ''.join(card(p) for p in posts[1:])
    faqs = [
        {'q': 'Who is the Vincere blog for?', 'a': 'The Vincere blog is written for managing partners, firm owners and marketing leads at US law firms who want more signed cases. Each post explains one marketing topic in plain language, with steps you can act on.'},
        {'q': 'How can I get marketing advice for my own firm?', 'a': 'Book a free 30-minute strategy call with Vincere. We price your market, look at your intake and recommend a channel mix and launch order for your practice area and city, with no obligation.'},
        {'q': 'Can I suggest a topic for the blog?', 'a': f'Yes. Email {B.EMAIL} with the question you want answered, and we will consider it for a future post.'},
    ]
    schema = [B.org_node(), B.website_node(),
              B.webpage_node(url, 'CollectionPage', title, desc, {'mainEntity': {'@id': f'{DOMAIN}{url}#posts'}}),
              B.crumbs_node(url, crumbs),
              {'@type': 'ItemList', '@id': f'{DOMAIN}{url}#posts', 'name': 'Vincere blog posts',
               'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{DOMAIN}/blog/{p["slug"]}/', 'name': p['title']} for i, p in enumerate(posts)]},
              B.faq_node(url, faqs)]
    cats = []
    for p in posts:
        c = p.get('category', 'Law firm marketing')
        if c not in cats: cats.append(c)
    chips = '<button type="button" class="bh-chip on" data-cat="all">All posts</button>' + ''.join(f'<button type="button" class="bh-chip" data-cat="{e(c)}">{e(c)}</button>' for c in cats)
    body = f'''<header class="phero blog-hero">
  <div class="wrap phero-in">
    {B.crumb_html(crumbs)}
    <p class="bh-kick">The Vincere blog</p>
    <h1>Law firm marketing, <em>explained.</em></h1>
    <p class="lede">Straight answers on getting more signed cases: what each channel costs, how long it takes to work, and what to fix first. No fluff, no jargon.</p>
    <div class="bh-chips" role="group" aria-label="Filter posts by topic">{chips}</div>
  </div>
</header>
<section class="sec">
  <div class="wrap"><div class="blog-grid">{cards}</div></div>
</section>
{B.faq_html(faqs)}
{FILTER_JS}'''
    B.write(url, B.page(url, title, desc, schema, body).replace('<main id="main">', '<main id="main" class="svcp blogp">', 1))
    B.SITEMAP.append((url, '0.8'))

    # RSS feed
    def rfc822(iso):
        return datetime.datetime.fromisoformat(iso + 'T09:00:00+00:00').strftime('%a, %d %b %Y %H:%M:%S +0000')
    items = ''.join(f'''  <item>
    <title>{html.escape(p["title"])}</title>
    <link>{DOMAIN}/blog/{p["slug"]}/</link>
    <guid>{DOMAIN}/blog/{p["slug"]}/</guid>
    <pubDate>{rfc822(p["date"])}</pubDate>
    <description>{html.escape(p["description"])}</description>
  </item>
''' for p in posts)
    rss = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
<channel>
  <title>Vincere Legal Marketing Blog</title>
  <link>{DOMAIN}/blog/</link>
  <atom:link href="{DOMAIN}/blog/feed.xml" rel="self" type="application/rss+xml"/>
  <description>{html.escape(desc)}</description>
  <language>en-us</language>
{items}</channel>
</rss>
'''
    open(os.path.join(B.SITE, 'blog', 'feed.xml'), 'w').write(rss)
    return posts
