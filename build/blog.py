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
        words = len(re.sub(r'<[^>]+>', ' ', meta['html']).split())
        meta['minutes'] = max(1, round(words / WORDS_PER_MIN))
        posts.append(meta)
    posts.sort(key=lambda p: p['date'], reverse=True)
    return posts


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%B %-d, %Y')


def build_blog(B):
    """B is the build module (helpers, constants, SITEMAP)."""
    e, DOMAIN = B.e, B.DOMAIN
    posts = load_posts(B.CONTENT)
    if not posts:
        return []
    ARTICLE = {'@type': 'Organization', '@id': B.ORG_ID}

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
                   'image': f'{DOMAIN}{p.get("image") or "/assets/og-image.png"}', 'inLanguage': 'en-US',
                   'articleSection': p.get('category', 'Law firm marketing'), 'wordCount': len(re.sub(r'<[^>]+>', ' ', p['html']).split())}]
        if p.get('faqs'):
            schema.append(B.faq_node(url, p['faqs']))
        meta_line = f'<span>{e(p.get("category", "Law firm marketing"))}</span><span>{nice_date(p["date"])}</span><span>{p["minutes"]} min read</span>'
        if p['updated'] != p['date']:
            meta_line += f'<span>Updated {nice_date(p["updated"])}</span>'
        quick = B.answer({'question': p['summary_question'], 'text': p['summary']}) if p.get('summary') and p.get('summary_question') else ''
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
{quick}
<article class="sec post">
  <div class="wrap"><div class="post-body">{p["html"]}</div></div>
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
    cards = ''.join(f'''<a class="blog-card" href="/blog/{p["slug"]}/">
      <span class="bc-cat">{e(p.get("category", "Law firm marketing"))}</span>
      <h2>{e(p["title"])}</h2>
      <p>{e(p["description"])}</p>
      <span class="bc-meta">{nice_date(p["date"])} &middot; {p["minutes"]} min read</span>
    </a>''' for p in posts)
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
    body = f'''<header class="phero">
  <div class="wrap phero-in">
    {B.crumb_html(crumbs)}
    <h1>Law firm marketing, explained.</h1>
    <p class="lede">Straight answers on getting more signed cases: what each channel costs, how long it takes to work, and what to fix first. No fluff, no jargon.</p>
  </div>
</header>
<section class="sec">
  <div class="wrap"><div class="blog-grid">{cards}</div></div>
</section>
{B.faq_html(faqs)}'''
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
