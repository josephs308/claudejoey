#!/usr/bin/env python3
"""Generate the Vincere service, practice-area, hub and about pages.

Content lives in build/content/*.json. Shared shell (nav, footer, contact
form, schema) is defined here so every page stays consistent. Run from the
repo root:  python3 build/build.py
"""
import html, json, os, re, datetime, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, 'vincere-site')
BUILD = os.path.join(ROOT, 'build')
CONTENT = os.path.join(BUILD, 'content')

DOMAIN = 'https://vincerelegalmarketing.com'
BRAND = 'Vincere Legal Marketing'
PHONE_DISPLAY = '(555) 010-0199'  # placeholder until Vincere's real number is set
PHONE_TEL = '+15550100199'
PHONE_E164 = '+1-555-010-0199'
EMAIL = 'joe@vincerelegalmarketing.com'
PORTAL = '/portal/'
LINKEDIN = 'https://www.linkedin.com/company/vincere-legal-marketing'
TODAY = datetime.date.today().isoformat()
# Paste a Google Calendar appointment-schedule or Calendly embed URL here to
# replace the built-in booking calendar with the live embed.
BOOKING_URL = ''

SERVICES = [  # slug, nav label, short dropdown blurb, icon key, old url
    ('law-firm-consulting', 'Consulting', 'Intake, CRM and lead-to-client systems', 'CONSULT', None),
    ('law-firm-branding', 'Branding', 'Positioning, messaging and identity', 'BRAND', 'branding.html'),
    ('local-services-ads-for-lawyers', 'Local Services Ads', 'Google Screened, pay-per-lead calls', 'LSA', 'lsa.html'),
    ('law-firm-seo', 'SEO', 'Rank in Google search and the map pack', 'SEO', 'seo.html'),
    ('law-firm-aeo', 'AEO', 'Get named by ChatGPT and AI Overviews', 'AEO', 'aeo.html'),
    ('law-firm-ppc', 'PPC', 'Google Search Ads for case intake', 'PPC', 'ppc.html'),
    ('meta-ads-for-lawyers', 'Meta Ads', 'Facebook and Instagram campaigns', 'META', 'meta-ads.html'),
    ('law-firm-traditional-advertising', 'Traditional', 'Billboards, TV, radio and direct mail', 'TRAD', None),
    ('law-firm-website-design', 'Websites', 'Fast, custom-coded firm websites', 'WEB', 'websites.html'),
]
SVC = {s[0]: s for s in SERVICES}

PRACTICES = [
    ('personal-injury-lawyer-marketing', 'Personal Injury'),
    ('criminal-defense-lawyer-marketing', 'Criminal Defense'),
    ('family-law-marketing', 'Family Law'),
    ('estate-planning-attorney-marketing', 'Estate Planning'),
    ('real-estate-attorney-marketing', 'Real Estate'),
    ('business-lawyer-marketing', 'Business Law'),
    ('litigation-attorney-marketing', 'Litigation'),
    ('employment-lawyer-marketing', 'Employment Law'),
    ('immigration-lawyer-marketing', 'Immigration'),
    ('bankruptcy-attorney-marketing', 'Bankruptcy'),
    ('workers-compensation-lawyer-marketing', "Workers' Compensation"),
    ('medical-malpractice-lawyer-marketing', 'Medical Malpractice'),
    ('dui-lawyer-marketing', 'DUI / DWI'),
    ('intellectual-property-attorney-marketing', 'Intellectual Property'),
    ('tax-attorney-marketing', 'Tax Law'),
]
PRA = dict(PRACTICES)

SVC_PHOTOS = {
    'law-firm-consulting': ('photo-1686061593213-98dad7c599b9', 'Marketing analytics dashboard showing spend and results', 'Every lead, tracked to a signed case', 'Intake, follow-up and results in one view.'),
    'law-firm-branding': ('photo-1655945702696-e4ede55f938b', 'Brand identity applied across laptop and phone', 'One firm, every surface', 'The ad, the site and the intake call saying the same thing.'),
    'local-services-ads-for-lawyers': ('photo-1525182008055-f88b95ff7980', 'Taking an inbound call from a new client', 'The phone rings first', 'Pay-per-lead calls from people who need a lawyer now.'),
    'law-firm-seo': ('photo-1586125674857-4eb86880905d', 'A computer screen showing Google search results', 'Rankings you keep', 'The page that keeps working after the ad budget stops.'),
    'law-firm-aeo': ('photo-1745674684498-1547fd240f5d', 'Laptop screen showing an AI assistant response', 'Named in the answer', 'When a client asks AI for a lawyer, your firm is in it.'),
    'law-firm-ppc': ('photo-1557200134-90327ee9fafa', 'Laptop showing a Google search results page', 'The top of the page, tomorrow', 'Search ads built around signed cases, not clicks.'),
    'meta-ads-for-lawyers': ('photo-1745848413078-f85af10e5bf2', 'Instagram and Facebook among social apps on a smartphone', 'Where your clients scroll', 'Awareness and retargeting that keeps your firm top of mind.'),
    'law-firm-traditional-advertising': ('photo-1658863025658-4a259cc68fc9', 'Design books and printed brochure samples laid out', 'Offline, still measured', 'Every placement gets its own number and landing page.'),
    'law-firm-website-design': ('photo-1510519138101-570d1dca3d66', 'A desk setup with a large monitor showing a live site', 'Built to convert', 'Custom code, fast load, clear path to a consultation.'),
}

ICONS = {
 'CONSULT':'<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/><circle cx="12" cy="18" r="2.5"/><path d="M7.5 6h9M6.3 8.2l4.4 7.6M17.7 8.2l-4.4 7.6"/>',
 'BRAND':'<path d="M12 3l2.4 5.6L20 11l-5.6 2.4L12 19l-2.4-5.6L4 11l5.6-2.4z"/>',
 'LSA':'<path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
 'SEO':'<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
 'AEO':'<path d="M4 5h16v11H9l-5 4z"/><path d="M12 8l.9 2.1L15 11l-2.1.9L12 14l-.9-2.1L9 11l2.1-.9z"/>',
 'PPC':'<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".8"/>',
 'META':'<path d="M3 10v4l11 5V5z"/><path d="M14 8a4 4 0 0 1 0 8M6.5 15.5L8 21h3l-1.2-4"/>',
 'TRAD':'<rect x="3" y="4" width="18" height="10" rx="1.5"/><path d="M8 14v7M16 14v7M6 21h4M14 21h4"/>',
 'WEB':'<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18M6.5 6.5h.01M9 6.5h.01"/>',
 'LAW':'<path d="M12 3v18M7 21h10M4 7h16M6 7l-3 7a3 3 0 0 0 6 0zM18 7l-3 7a3 3 0 0 0 6 0z"/>',
 'LOCK':'<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
 'Q':'<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
}

def icon(key, cls=''):
    c = f' class="{cls}"' if cls else ''
    return (f'<svg{c} viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</svg>')

def e(t):
    return html.escape(t, quote=True).replace('&#x27;', '&rsquo;').replace("'", '&rsquo;')

def svc_url(slug): return f'/services/{slug}/'
def pra_url(slug): return f'/practice-areas/{slug}/'

VMARK = '<svg class="vmark" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="14" fill="#64315A"/><path d="M53.11 12Q53.31 12 53.31 12.38Q53.31 12.76 53.11 12.76Q50.89 12.76 48.97 14.48Q47.06 16.2 45.85 19.45L33.43 51.75Q33.37 52 32.76 52Q32.16 52 32.03 51.75L15.92 17.29Q14.83 14.99 13.69 13.88Q12.54 12.76 10.89 12.76Q10.69 12.76 10.69 12.38Q10.69 12 10.89 12Q11.71 12 12.25 12.06Q12.8 12.13 13.59 12.16Q14.39 12.19 15.73 12.19Q18.78 12.19 20.73 12.16Q22.67 12.13 23.97 12.06Q25.28 12 26.3 12Q26.49 12 26.49 12.38Q26.49 12.76 26.3 12.76Q23.62 12.76 22.7 14.1Q21.78 15.44 22.99 17.92L35.28 44.55L32.67 48.94L44.13 19.2Q45.22 16.33 44.26 14.55Q43.31 12.76 40.06 12.76Q39.87 12.76 39.87 12.38Q39.87 12 40.06 12Q41.78 12 43.37 12.1Q44.96 12.19 47.51 12.19Q49.29 12.19 50.41 12.1Q51.52 12 53.11 12Z" fill="#fff"/></svg>'

CHEV = '<svg viewBox="0 0 10 10" aria-hidden="true"><path d="M1.5 3.5L5 7l3.5-3.5" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/></svg>'

def nav():
    svc = ''.join(f'<a class="dd-link" href="{svc_url(s)}"><span class="dd-ic">{icon(ic)}</span><span><b>{e(lab)}</b><small>{e(blurb)}</small></span></a>'
                  for s, lab, blurb, ic, _ in SERVICES)
    pra = ''.join(f'<a class="dd-link" href="{pra_url(s)}"><span class="dd-ic">{icon("LAW")}</span><span><b>{e(lab)}</b></span></a>'
                  for s, lab in PRACTICES)
    return f'''<a class="skip" href="#main">Skip to content</a>
<div class="scroll-prog" id="scrollProg" aria-hidden="true"></div>
<nav class="nav" id="nav" aria-label="Main">
  <div class="nav-in">
    <a class="nav-brand" href="/" aria-label="{BRAND} home">{VMARK}<span class="nav-word">Vincere</span></a>
    <div class="nav-mid" id="navMid">
      <div class="dd dd-svc"><button class="dd-btn" type="button" aria-expanded="false" aria-controls="dd-services">Services {CHEV}</button>
        <div class="dd-panel" id="dd-services"><div class="dd-grid">{svc}</div>
          <div class="dd-foot"><span>Nine channels, one partner, one plan.</span><a href="/services/">All services &rarr;</a></div></div></div>
      <div class="dd dd-pa"><button class="dd-btn" type="button" aria-expanded="false" aria-controls="dd-practice">Practice Areas {CHEV}</button>
        <div class="dd-panel" id="dd-practice"><div class="dd-grid">{pra}</div>
          <div class="dd-foot"><span>Marketing built around how your clients hire.</span><a href="/practice-areas/">All practice areas &rarr;</a></div></div></div>
      <a href="/#math">Approach</a>
      <a href="/about/">About</a>
      <a href="#contact">Contact</a>
      <a class="nav-tel" href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>
      <a class="nav-portal-m" href="{PORTAL}">{icon("LOCK")} Client Portal</a>
    </div>
    <a class="nav-portal" href="{PORTAL}">{icon("LOCK")}Client Portal</a>
    <a class="nav-cta" href="#contact"><span class="dot"></span>Get Pricing</a>
    <button class="burger" id="burger" type="button" aria-label="Menu" aria-expanded="false" aria-controls="navMid"><span></span><span></span><span></span></button>
  </div>
</nav>'''

def footer():
    svc = ''.join(f'<li><a href="{svc_url(s)}">{e(lab)}</a></li>' for s, lab, *_ in SERVICES)
    p1 = ''.join(f'<li><a href="{pra_url(s)}">{e(lab)}</a></li>' for s, lab in PRACTICES[:8])
    p2 = ''.join(f'<li><a href="{pra_url(s)}">{e(lab)}</a></li>' for s, lab in PRACTICES[8:])
    return f'''<footer class="foot">
  <div class="wrap">
    <div class="foot-in">
      <div>
        <span class="foot-logo nologo">{VMARK}<span class="chip-word">Vincere<small>Legal Marketing</small></span></span>
        <p class="foot-desc">Full-service marketing for law firms. Every channel, one partner, measured in signed cases.</p>
        <a class="foot-tel" href="tel:{PHONE_TEL}">{PHONE_DISPLAY}</a>
        <p style="margin-top:10px"><a href="mailto:{EMAIL}">{EMAIL}</a></p>
      </div>
      <div><h5>Services</h5><ul>{svc}</ul></div>
      <div><h5>Practice areas</h5><ul>{p1}</ul></div>
      <div><h5>&nbsp;</h5><ul>{p2}<li><a href="/practice-areas/">All practice areas</a></li></ul></div>
      <div><h5>Company</h5><ul>
        <li><a href="/about/">About Vincere</a></li>
        <li><a href="/#math">Approach</a></li>
        <li><a href="{PORTAL}">Client Portal</a></li>
        <li><a href="#contact">Get pricing</a></li>
      </ul></div>
    </div>
    <div class="foot-bot">
      <span>&copy; <span id="yr">2026</span> {BRAND}. All Rights Reserved.</span>
      <span>Legal marketing &middot; Measured in signed cases</span>
    </div>
  </div>
</footer>'''

SCRIPTS = '''<script>
(function(){
  var n=document.getElementById('nav'),b=document.getElementById('burger'),m=document.getElementById('navMid');
  function onScroll(){ if(n) n.classList.toggle('stuck',window.scrollY>6); }
  onScroll();addEventListener('scroll',onScroll,{passive:true});
  if(b&&m){b.addEventListener('click',function(){var o=m.classList.toggle('open');b.classList.toggle('on',o);b.setAttribute('aria-expanded',String(o));});
    m.addEventListener('click',function(ev){var a=ev.target.closest('a');if(a&&m.classList.contains('open')){m.classList.remove('open');b.classList.remove('on');b.setAttribute('aria-expanded','false');}});}
  var dds=[].slice.call(document.querySelectorAll('.dd'));
  dds.forEach(function(d){var btn=d.querySelector('.dd-btn');btn.addEventListener('click',function(ev){ev.stopPropagation();var o=!d.classList.contains('open');
    dds.forEach(function(x){x.classList.remove('open');x.querySelector('.dd-btn').setAttribute('aria-expanded','false')});
    d.classList.toggle('open',o);btn.setAttribute('aria-expanded',String(o));});});
  document.addEventListener('click',function(ev){if(!ev.target.closest('.dd'))dds.forEach(function(x){x.classList.remove('open');x.querySelector('.dd-btn').setAttribute('aria-expanded','false')});});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape')dds.forEach(function(x){x.classList.remove('open');x.querySelector('.dd-btn').setAttribute('aria-expanded','false')});});
  document.querySelectorAll('.faq-q').forEach(function(q){q.addEventListener('click',function(){var i=q.closest('.faq-i'),p=i.querySelector('.faq-a'),o=i.classList.toggle('open');q.setAttribute('aria-expanded',String(o));p.style.maxHeight=o?p.scrollHeight+'px':'0px';});});
  addEventListener('resize',function(){document.querySelectorAll('.faq-i.open .faq-a').forEach(function(p){p.style.maxHeight=p.scrollHeight+'px'});});
  var y=document.getElementById('yr');if(y)y.textContent=new Date().getFullYear();
  var sp=document.getElementById('scrollProg');if(sp){var t=false;function u(){var h=document.documentElement,mx=h.scrollHeight-h.clientHeight;sp.style.transform='scaleX('+(mx>0?Math.min(1,h.scrollTop/mx):0)+')';t=false}
    addEventListener('scroll',function(){if(!t){t=true;requestAnimationFrame(u)}},{passive:true});u();}
})();
</script>'''

# ---------------------------------------------------------------- schema
ORG_ID = f'{DOMAIN}/#organization'
SITE_ID = f'{DOMAIN}/#website'

def org_node():
    return {
        '@type': 'Organization', '@id': ORG_ID, 'name': BRAND,
        'alternateName': ['Vincere', 'Vincere Legal'], 'url': f'{DOMAIN}/',
        'logo': {'@type': 'ImageObject', '@id': f'{DOMAIN}/#logo', 'url': f'{DOMAIN}/assets/logo.png', 'width': 512, 'height': 512},
        'image': f'{DOMAIN}/assets/og-image.png',
        'description': 'Vincere Legal Marketing is a full-service marketing partner for law firms: consulting, branding, Local Services Ads, SEO, answer engine optimization, PPC, Meta ads, traditional media and websites, measured in signed cases.',
        'email': EMAIL, 'telephone': PHONE_E164,
        'contactPoint': {'@type': 'ContactPoint', 'telephone': PHONE_E164, 'email': EMAIL, 'contactType': 'sales', 'areaServed': 'US', 'availableLanguage': ['English']},
        'areaServed': {'@type': 'Country', 'name': 'United States'},
        'knowsAbout': ['Law firm marketing', 'Legal marketing', 'SEO for lawyers', 'Answer engine optimization', 'Google Local Services Ads', 'Law firm PPC', 'Legal intake', 'Law firm website design'],
        'sameAs': [LINKEDIN],
    }

def website_node():
    return {'@type': 'WebSite', '@id': SITE_ID, 'url': f'{DOMAIN}/', 'name': BRAND, 'alternateName': 'Vincere',
            'publisher': {'@id': ORG_ID}, 'inLanguage': 'en-US'}

def crumbs_node(url, crumbs):
    return {'@type': 'BreadcrumbList', '@id': f'{DOMAIN}{url}#breadcrumb',
            'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': f'{DOMAIN}{u}'} for i, (n, u) in enumerate(crumbs)]}

def faq_node(url, faqs):
    return {'@type': 'FAQPage', '@id': f'{DOMAIN}{url}#faq', 'isPartOf': {'@id': f'{DOMAIN}{url}#webpage'},
            'mainEntity': [{'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in faqs]}

def webpage_node(url, kind, title, desc, extra=None):
    n = {'@type': kind, '@id': f'{DOMAIN}{url}#webpage', 'url': f'{DOMAIN}{url}', 'name': title, 'description': desc,
         'isPartOf': {'@id': SITE_ID}, 'about': {'@id': ORG_ID}, 'publisher': {'@id': ORG_ID},
         'breadcrumb': {'@id': f'{DOMAIN}{url}#breadcrumb'}, 'inLanguage': 'en-US', 'dateModified': TODAY,
         'primaryImageOfPage': {'@type': 'ImageObject', 'url': f'{DOMAIN}/assets/og-image.png'}}
    if extra: n.update(extra)
    return n

def jsonld(nodes):
    return '<script type="application/ld+json">' + json.dumps({'@context': 'https://schema.org', '@graph': nodes}, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/') + '</script>'

# ---------------------------------------------------------------- page shell
def head(url, title, desc, schema, robots='index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1'):
    canon = f'{DOMAIN}{url}'
    return f'''<!DOCTYPE html>
<html lang="en-US">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{canon}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{BRAND}: full-service marketing for law firms">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(desc)}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">
<meta name="theme-color" content="#64315A">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="preload" href="/fonts/unbounded-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/schibsted-grotesk-var.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/site.css">
{jsonld(schema)}
</head>
<body>
'''

import booking_form as _bf
def booking_form():
    return _bf.render(e, PRACTICES, PHONE_TEL, PHONE_DISPLAY, EMAIL, BOOKING_URL)

SUB_OLD = 'Send this over and we&rsquo;ll come back with projected lead volume, expected cost per new customer, and exactly what our fee looks like against those numbers, before you commit to anything.'
SUB_NEW = 'Book a free 30-minute call. We&rsquo;ll come back with projected lead volume, expected cost per signed case, and exactly what our fee looks like against those numbers, before you commit to anything.'

CONTACT_PHOTO_ID = 'photo-1758873268745-dd2cf0d677b5'
def contact_photo():
    def u(w, h): return f'https://images.unsplash.com/{CONTACT_PHOTO_ID}?fm=jpg&auto=format&fit=crop&crop=entropy&q=80&w={w}&h={h}'
    ss = ', '.join(f'{u(w, h)} {w}w' for w, h in [(640, 320), (960, 480), (1280, 640)])
    return (f'<figure class="contact-photo"><img src="{u(960,480)}" srcset="{ss}" sizes="(max-width: 900px) 100vw, 560px" width="960" height="480" '
            f'alt="A marketing team working together at a shared desk" loading="lazy" decoding="async" onerror="this.parentNode.classList.add(\'nophoto\');this.remove()">'
            f'<figcaption><b>Real people, real numbers.</b>Your call is with the team that builds your plan.</figcaption></figure>')

def swap_form(html_s):
    html_s = re.sub(r'<div class="contact-mark">.*?</p>\s*</div>', lambda m: contact_photo(), html_s, count=1, flags=re.S)
    if 'class="contact-photo"' not in html_s and 'class="email-line"' in html_s:
        html_s = re.sub(r'(<p class="email-line">.*?</p>\s*</div>)', lambda m: m.group(1) + '\n        ' + contact_photo(), html_s, count=1, flags=re.S)
    html_s = re.sub(r'<(form|div) class="form (?:book )?rv".*?</\1>', lambda m: booking_form(), html_s, count=1, flags=re.S)
    return html_s.replace(SUB_OLD, SUB_NEW)

CONTACT = None
def contact():
    global CONTACT
    if CONTACT is None:
        c = open(os.path.join(BUILD, 'contact.html')).read()
        c = c.replace('info@mbpresults.com', EMAIL).replace('action="thanks.html"', 'action="/thanks.html"')
        c = c.replace('<div class="kicker">Get pricing</div>\n', '')
        c = c.replace('<h2>Tell us your market', '<h2 id="contact-h">Tell us your market')
        CONTACT = swap_form(c)
    return CONTACT

def page(url, title, desc, schema, body, robots=None):
    h = head(url, title, desc, schema, robots) if robots else head(url, title, desc, schema)
    return h + nav() + '\n<main id="main">\n' + body + '\n' + contact() + '\n</main>\n' + footer() + '\n' + SCRIPTS + '\n' + open(os.path.join(BUILD, 'booking.js')).read() + '</body>\n</html>\n'

def crumb_html(crumbs):
    parts = []
    for i, (n, u) in enumerate(crumbs):
        if i == len(crumbs) - 1:
            parts.append(f'<span aria-current="page">{e(n)}</span>')
        else:
            parts.append(f'<a href="{u}">{e(n)}</a>')
    return '<nav aria-label="Breadcrumb"><p class="crumb">' + '<span class="sep">/</span>'.join(parts) + '</p></nav>'

def hero(crumbs, eyebrow, h1, lede, cta2=('Call ' + PHONE_DISPLAY, f'tel:{PHONE_TEL}')):
    return f'''<header class="phero">
  <div class="wrap phero-in">
    {crumb_html(crumbs)}
    <div><div class="eyebrow" style="margin-bottom:26px"><span class="pulse"></span>{e(eyebrow)}</div></div>
    <h1>{e(h1)}</h1>
    <p class="lede">{e(lede)}</p>
    <div class="btn-row">
      <a class="btn btn-orange btn-arr" href="#contact">Get my free plan</a>
      <a class="btn btn-out" href="{cta2[1]}">{e(cta2[0])}</a>
    </div>
  </div>
</header>'''

def answer(a):
    return f'''<section class="sec-answer" aria-labelledby="answer-q">
  <div class="wrap"><div class="answer"><span class="answer-tag">Quick answer</span><div><h2 id="answer-q">{e(a["question"])}</h2><p>{e(a["text"])}</p></div></div></div>
</section>'''

def faq_html(faqs, head_txt='Straight answers.'):
    items = ''.join(f'<div class="faq-i"><button class="faq-q" type="button" aria-expanded="false"><span>{e(f["q"])}</span><span class="pl">+</span></button><div class="faq-a"><div>{e(f["a"])}</div></div></div>' for f in faqs)
    return f'''<section class="sec sec-alt sec-lav" id="faq">
  <div class="wrap-narrow">
    <div class="sec-head"><div class="kicker">Questions</div><h2>{e(head_txt)}</h2></div>
    <div class="faq">{items}</div>
  </div>
</section>'''

def callout(h, p):
    return f'''<section class="callout sec-dark">
  <div class="in">
    <div><h2>{e(h)}</h2><p>{e(p)}</p></div>
    <div class="cbtns"><a class="btn btn-orange btn-arr" href="#contact">Get my free plan</a><a class="btn btn-out-white" href="tel:{PHONE_TEL}">Call {PHONE_DISPLAY}</a></div>
  </div>
</section>'''

def photo(pid, alt, cap_b, cap):
    def u(w, h): return f'https://images.unsplash.com/{pid}?fm=jpg&auto=format&fit=crop&crop=entropy&q=80&w={w}&h={h}'
    ss = ', '.join(f'{u(w, h)} {w}w' for w, h in [(960, 403), (1440, 604), (1920, 806), (2560, 1075)])
    return f'''<section class="sec ph-band" style="padding:0 0 72px">
  <div class="wrap"><figure style="margin:0"><div class="ph ph-wide ph-dark sec-ph"><img src="{u(1920,806)}" srcset="{ss}" sizes="(max-width: 980px) 100vw, 1280px" width="1920" height="806" alt="{e(alt)}" loading="lazy" decoding="async" onerror="this.replaceWith(Object.assign(document.createElement('div'),{{className:'ph-fallback',innerHTML:'<span>photo unavailable</span>'}}))"><figcaption class="ph-cap"><b>{e(cap_b)}</b>{e(cap)}</figcaption></div></figure></div>
</section>'''

def prose_sections(sections):
    return ''.join(f'<h2>{e(s["h2"])}</h2>' + ''.join(f'<p>{e(p)}</p>' for p in s['paragraphs']) for s in sections)

def svc_card(slug, text):
    s = SVC[slug]
    return f'<a class="card" href="{svc_url(slug)}"><span class="card-ic">{icon(s[3])}</span><h3>{e(s[1])}</h3><p>{e(text)}</p><span class="card-go">Learn more about {e(s[1])} &rarr;</span></a>'

def pra_card(slug, text):
    return f'<a class="card" href="{pra_url(slug)}"><span class="card-ic">{icon("LAW")}</span><h3>{e(PRA[slug])} marketing</h3><p>{e(text)}</p><span class="card-go">See the playbook &rarr;</span></a>'

def write(url, content):
    path = os.path.join(SITE, url.strip('/'), 'index.html') if url != '/' else os.path.join(SITE, 'index.html')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(content)

def load(slug):
    return json.load(open(os.path.join(CONTENT, slug + '.json')))

def practice_for_note(name):
    n = name.lower()
    for s, lab in PRACTICES:
        l = lab.lower()
        if l in n or n in l or n.split()[0] in l.lower():
            return s
    return None

# ---------------------------------------------------------------- builders
SITEMAP = []

def build_service(slug):
    d = load(slug)
    url = svc_url(slug)
    crumbs = [('Home', '/'), ('Services', '/services/'), (d['nav_label'], url)]
    schema = [org_node(), website_node(),
              webpage_node(url, 'WebPage', d['title'], d['meta_description'], {'mainEntity': {'@id': f'{DOMAIN}{url}#service'}}),
              crumbs_node(url, crumbs),
              {'@type': 'Service', '@id': f'{DOMAIN}{url}#service', 'name': d['service_name'], 'serviceType': d['service_name'],
               'description': d['answer']['text'], 'url': f'{DOMAIN}{url}', 'provider': {'@id': ORG_ID},
               'areaServed': {'@type': 'Country', 'name': 'United States'},
               'audience': {'@type': 'BusinessAudience', 'audienceType': 'Law firms and attorneys'},
               'category': 'Legal marketing'},
              faq_node(url, d['faqs'])]
    incl = ''.join(f'<li><span class="dot"></span><span>{e(x)}</span></li>' for x in d['included'])
    steps = ''.join(f'<div class="step"><div class="step-n">{i+1:02d}</div><div><h3 class="h4">{e(s["title"])}</h3><p>{e(s["text"])}</p></div><div class="step-caret">&rarr;</div></div>' for i, s in enumerate(d['process']))
    metrics = ''.join(f'<div class="metric"><h3 class="k">{e(m["title"])}</h3><p>{e(m["text"])}</p></div>' for m in d['metrics'])
    notes = ''
    for n in d['practice_notes']:
        ps = practice_for_note(n['practice'])
        if ps:
            notes += f'<a class="card" href="{pra_url(ps)}"><span class="card-ic">{icon("LAW")}</span><h3>{e(n["practice"])}</h3><p>{e(n["text"])}</p><span class="card-go">{e(PRA[ps])} marketing &rarr;</span></a>'
        else:
            notes += f'<div class="card"><span class="card-ic">{icon("LAW")}</span><h3>{e(n["practice"])}</h3><p>{e(n["text"])}</p></div>'
    related = ''.join(f'<a class="rel-c" href="{svc_url(r)}"><div class="rel-tag">{e(SVC[r][1])}</div><h3>{e(SVC[r][1])}</h3><p>{e(SVC[r][2])}.</p><span class="rel-arr">See the service &rarr;</span></a>' for r in d['related'] if r in SVC and r != slug)
    ph = SVC_PHOTOS.get(slug)
    body = f'''{hero(crumbs, d["eyebrow"], d["h1"], d["lede"])}
{answer(d["answer"])}
<section class="sec">
  <div class="wrap"><div class="lf">
    <div class="prose">{prose_sections(d["sections"])}</div>
    <aside class="panel"><h2 class="h4" style="font-size:15px">What&rsquo;s included</h2><ul class="checks">{incl}</ul>
      <div style="margin-top:28px;padding-top:24px;border-top:1px solid var(--line)"><h2 class="h4" style="font-size:15px">Best for</h2><p style="font-size:15px;color:var(--ink);line-height:1.7;margin-top:8px">{e(d["best_for"])}</p></div>
      <a class="btn btn-orange btn-arr" href="#contact" style="margin-top:22px;width:100%;justify-content:center">Get my free plan</a></aside>
  </div></div>
</section>
{photo(*ph) if ph else ""}
<section class="sec sec-alt sec-lav">
  <div class="wrap">
    <div class="sec-head"><div class="kicker">How it works</div><h2>How we run {e(d["nav_label"])} for your firm.</h2></div>
    <div class="steps">{steps}</div>
  </div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="sec-head"><div class="kicker">By practice area</div><h2>{e(d["nav_label"])} is not the same for every practice.</h2></div>
    <div class="cards">{notes}</div>
  </div>
</section>
<section class="sec sec-dark">
  <div class="wrap">
    <div class="sec-head"><div class="kicker">What we report</div><h2>The numbers we hold ourselves to.</h2><p class="sub">All of it lives in your client dashboard, live, next to every other channel.</p></div>
    <div class="grid4">{metrics}</div>
  </div>
</section>
{faq_html(d["faqs"], d["nav_label"] + " questions, answered.")}
<section class="sec sec-tight">
  <div class="wrap">
    <div class="sec-head" style="margin-bottom:36px"><div class="kicker">Pairs well with</div><h2>What usually runs alongside this.</h2></div>
    <div class="rel">{related}</div>
  </div>
</section>
{callout("See what " + d["nav_label"] + " would look like for your firm.", "We will price your market, pick the right channels and put the numbers in writing before you commit to anything.")}'''
    write(url, page(url, d['title'], d['meta_description'], schema, body))
    SITEMAP.append((url, '0.9'))
    return d

def build_practice(slug):
    d = load(slug)
    url = pra_url(slug)
    crumbs = [('Home', '/'), ('Practice Areas', '/practice-areas/'), (d['nav_label'], url)]
    schema = [org_node(), website_node(),
              webpage_node(url, 'WebPage', d['title'], d['meta_description'], {'mainEntity': {'@id': f'{DOMAIN}{url}#service'}}),
              crumbs_node(url, crumbs),
              {'@type': 'Service', '@id': f'{DOMAIN}{url}#service', 'name': d['service_name'], 'serviceType': 'Legal marketing',
               'description': d['answer']['text'], 'url': f'{DOMAIN}{url}', 'provider': {'@id': ORG_ID},
               'areaServed': {'@type': 'Country', 'name': 'United States'},
               'audience': {'@type': 'BusinessAudience', 'audienceType': d['nav_label'] + ' law firms'},
               'hasOfferCatalog': {'@type': 'OfferCatalog', 'name': d['service_name'] + ' services',
                                   'itemListElement': [{'@type': 'Offer', 'itemOffered': {'@type': 'Service', 'name': SVC[c['service']][1] + ' for ' + d['practice'] + ' firms', 'url': f'{DOMAIN}{svc_url(c["service"])}'}} for c in d['channels'] if c['service'] in SVC]}},
              faq_node(url, d['faqs'])]
    market = ''.join(f'<div class="card"><h3>{e(m["title"])}</h3><p>{e(m["text"])}</p></div>' for m in d['market'])
    chans = ''.join(svc_card(c['service'], c['why']) for c in d['channels'] if c['service'] in SVC)
    qs = ''.join(f'<li>{icon("Q")}{e(q)}</li>' for q in d['searches'])
    related = ''.join(f'<a class="rel-c" href="{pra_url(r)}"><div class="rel-tag">Practice area</div><h3>{e(PRA[r])}</h3><p>Marketing built around how {e(PRA[r].lower())} clients search and hire.</p><span class="rel-arr">See the playbook &rarr;</span></a>' for r in d['related'] if r in PRA and r != slug)
    body = f'''{hero(crumbs, d["eyebrow"], d["h1"], d["lede"])}
{answer(d["answer"])}
<section class="sec">
  <div class="wrap">
    <div class="sec-head"><div class="kicker">The market</div><h2>What makes {e(d["practice"])} marketing different.</h2></div>
    <div class="cards">{market}</div>
  </div>
</section>
<section class="sec sec-alt sec-lav">
  <div class="wrap"><div class="lf">
    <div class="prose">{prose_sections(d["sections"])}</div>
    <aside class="panel"><h2 class="h4" style="font-size:15px">What your clients search</h2><p style="font-size:14px;color:#4A4A4A;margin:6px 0 14px">The kinds of searches and AI questions we build your visibility around.</p>
      <ul class="qs">{qs}</ul>
      <a class="btn btn-orange btn-arr" href="#contact" style="margin-top:22px;width:100%;justify-content:center">Get my free plan</a></aside>
  </div></div>
</section>
<section class="sec">
  <div class="wrap">
    <div class="sec-head"><div class="kicker">The channels</div><h2>The channels that sign {e(d["practice"])} cases.</h2><p class="sub">Every firm&rsquo;s mix is different. These are where we usually start, and your free plan tells you which ones fit your market.</p></div>
    <div class="cards">{chans}</div>
  </div>
</section>
<section class="sec sec-dark">
  <div class="wrap"><div class="intake">
    <div><div class="kicker">Intake</div><h2>{e(d["intake"]["h2"])}</h2></div>
    <p>{e(d["intake"]["text"])}</p>
  </div></div>
</section>
{faq_html(d["faqs"], d["nav_label"] + " marketing questions, answered.")}
<section class="sec sec-tight">
  <div class="wrap">
    <div class="sec-head" style="margin-bottom:36px"><div class="kicker">Related practice areas</div><h2>Other practices we market.</h2></div>
    <div class="rel">{related}</div>
  </div>
</section>
{callout("Get a " + d["practice"] + " marketing plan for your market.", "We will price your market, pick the right channels and show you the expected cost per signed case before you spend a dollar.")}'''
    write(url, page(url, d['title'], d['meta_description'], schema, body))
    SITEMAP.append((url, '0.9'))
    return d

def build_hub(kind):
    if kind == 'services':
        d = load('services-hub'); url = '/services/'; crumbs = [('Home', '/'), ('Services', url)]
        items = [(s, SVC[s][1], svc_url(s)) for s, *_ in SERVICES]
        cards = ''.join(svc_card(s, d['cards'].get(s, SVC[s][2] + '.')) for s, *_ in SERVICES)
        eyebrow = 'Services'
    else:
        d = load('practice-hub'); url = '/practice-areas/'; crumbs = [('Home', '/'), ('Practice Areas', url)]
        items = [(s, lab + ' marketing', pra_url(s)) for s, lab in PRACTICES]
        cards = ''.join(pra_card(s, d['cards'].get(s, '')) for s, _ in PRACTICES)
        eyebrow = 'Practice areas'
    schema = [org_node(), website_node(),
              webpage_node(url, 'CollectionPage', d['title'], d['meta_description'], {'mainEntity': {'@id': f'{DOMAIN}{url}#list'}}),
              crumbs_node(url, crumbs),
              {'@type': 'ItemList', '@id': f'{DOMAIN}{url}#list', 'numberOfItems': len(items),
               'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': n, 'url': f'{DOMAIN}{u}'} for i, (_, n, u) in enumerate(items)]},
              faq_node(url, d['faqs'])]
    body = f'''{hero(crumbs, eyebrow, d["h1"], d["lede"])}
{answer(d["answer"])}
<section class="sec">
  <div class="wrap"><div class="cards">{cards}</div></div>
</section>
{faq_html(d["faqs"])}
{callout("Not sure where to start?", "Your free plan tells you which channels fit your practice and your market, and what each signed case should cost.")}'''
    write(url, page(url, d['title'], d['meta_description'], schema, body))
    SITEMAP.append((url, '0.9'))

def build_about():
    d = load('about'); url = '/about/'; crumbs = [('Home', '/'), ('About', url)]
    schema = [org_node(), website_node(),
              webpage_node(url, 'AboutPage', d['title'], d['meta_description'], {'mainEntity': {'@id': ORG_ID}}),
              crumbs_node(url, crumbs), faq_node(url, d['faqs'])]
    pr = ''.join(f'<div class="card"><h3>{e(p["title"])}</h3><p>{e(p["text"])}</p></div>' for p in d['principles'])
    svc = ''.join(svc_card(s, SVC[s][2] + '.') for s, *_ in SERVICES)
    body = f'''{hero(crumbs, "About Vincere", d["h1"], d["lede"])}
<section class="sec">
  <div class="wrap"><div class="lf">
    <div class="prose">{prose_sections(d["sections"])}</div>
    <aside class="panel"><h2 class="h4" style="font-size:15px">How we work</h2><ul class="checks">
      <li><span class="dot"></span><span>A free plan before you pay</span></li><li><span class="dot"></span><span>Intake fixed first</span></li>
      <li><span class="dot"></span><span>The right specialists for every channel, connected</span></li><li><span class="dot"></span><span>One point of contact</span></li>
      <li><span class="dot"></span><span>One live dashboard for all of it</span></li><li><span class="dot"></span><span>Measured in signed cases</span></li></ul>
      <a class="btn btn-orange btn-arr" href="#contact" style="margin-top:22px;width:100%;justify-content:center">Get my free plan</a></aside>
  </div></div>
</section>
<section class="sec sec-dark">
  <div class="wrap"><div class="sec-head"><div class="kicker">Principles</div><h2>What we hold ourselves to.</h2></div><div class="cards">{pr}</div></div>
</section>
<section class="sec">
  <div class="wrap"><div class="sec-head"><div class="kicker">Services</div><h2>Nine channels. One partner.</h2></div><div class="cards">{svc}</div></div>
</section>
{faq_html(d["faqs"])}'''
    write(url, page(url, d['title'], d['meta_description'], schema, body))
    SITEMAP.append((url, '0.7'))

# ---------------------------------------------------------------- assets
def build_css():
    css = open(os.path.join(BUILD, 'base.css')).read() + '\n' + open(os.path.join(BUILD, 'extra.css')).read() + '\n' + open(os.path.join(BUILD, 'booking.css')).read()
    css += '\n.h4{font-family:"Schibsted Grotesk",sans-serif!important;font-size:18px;font-weight:700!important;letter-spacing:-.01em!important;line-height:1.25!important;margin:0 0 8px}\n.metric h3.k{margin:0 0 10px}\n'
    os.makedirs(os.path.join(SITE, 'assets'), exist_ok=True)
    open(os.path.join(SITE, 'assets', 'site.css'), 'w').write(css)

FAVICON = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='14' fill='#64315A'/><path d='M53.11 12Q53.31 12 53.31 12.38Q53.31 12.76 53.11 12.76Q50.89 12.76 48.97 14.48Q47.06 16.2 45.85 19.45L33.43 51.75Q33.37 52 32.76 52Q32.16 52 32.03 51.75L15.92 17.29Q14.83 14.99 13.69 13.88Q12.54 12.76 10.89 12.76Q10.69 12.76 10.69 12.38Q10.69 12 10.89 12Q11.71 12 12.25 12.06Q12.8 12.13 13.59 12.16Q14.39 12.19 15.73 12.19Q18.78 12.19 20.73 12.16Q22.67 12.13 23.97 12.06Q25.28 12 26.3 12Q26.49 12 26.49 12.38Q26.49 12.76 26.3 12.76Q23.62 12.76 22.7 14.1Q21.78 15.44 22.99 17.92L35.28 44.55L32.67 48.94L44.13 19.2Q45.22 16.33 44.26 14.55Q43.31 12.76 40.06 12.76Q39.87 12.76 39.87 12.38Q39.87 12 40.06 12Q41.78 12 43.37 12.1Q44.96 12.19 47.51 12.19Q49.29 12.19 50.41 12.1Q51.52 12 53.11 12Z' fill='#fff'/></svg>"

def build_misc():
    open(os.path.join(SITE, 'favicon.svg'), 'w').write(FAVICON)
    urls = [('/', '1.0')] + SITEMAP
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + ''.join(
        f'  <url><loc>{DOMAIN}{u}</loc><lastmod>{TODAY}</lastmod><priority>{p}</priority></url>\n' for u, p in urls) + '</urlset>\n'
    open(os.path.join(SITE, 'sitemap.xml'), 'w').write(xml)
    open(os.path.join(SITE, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\n\nSitemap: {DOMAIN}/sitemap.xml\n')
    red = ['# Old flat URLs -> new service and about pages (301)']
    for s, lab, _, _, old in SERVICES:
        if old:
            red.append(f'/{old}  {svc_url(s)}  301')
            red.append(f'/{old[:-5]}  {svc_url(s)}  301')
    red += ['/about.html  /about/  301', '/about  /about/  301', '/index.html  /  301',
            '/services  /services/  301', '/practice-areas  /practice-areas/  301']
    open(os.path.join(SITE, '_redirects'), 'w').write('\n'.join(red) + '\n')

# ---------------------------------------------------------------- home + thanks
HOME_TITLE = 'Law Firm Marketing Agency | Vincere Legal Marketing'
HOME_DESC = 'Full-service law firm marketing: SEO, AEO, Local Services Ads, PPC, Meta ads, branding, websites, intake and traditional media. Measured in signed cases.'

DD_JS = """<script id="dd-js">
(function(){var dds=[].slice.call(document.querySelectorAll('.dd'));
function shut(){dds.forEach(function(x){x.classList.remove('open');x.querySelector('.dd-btn').setAttribute('aria-expanded','false')});}
dds.forEach(function(d){var btn=d.querySelector('.dd-btn');btn.addEventListener('click',function(ev){ev.stopPropagation();var o=!d.classList.contains('open');shut();d.classList.toggle('open',o);btn.setAttribute('aria-expanded',String(o));});});
document.addEventListener('click',function(ev){if(!ev.target.closest('.dd'))shut();});
document.addEventListener('keydown',function(ev){if(ev.key==='Escape')shut();});})();
</script>"""

def patch_home():
    path = os.path.join(SITE, 'index.html'); s = open(path).read()
    s = re.sub(r'<a class="skip".*?</a>\n', '', s)
    s = re.sub(r'<div class="scroll-prog" id="scrollProg" aria-hidden="true"></div>\n?', '', s)
    s = re.sub(r'<nav class="nav" id="nav".*?</nav>', lambda m: nav(), s, count=1, flags=re.S)
    s = re.sub(r'<footer class="foot">.*?</footer>', lambda m: footer(), s, count=1, flags=re.S)
    s = re.sub(r'<title>.*?</title>', f'<title>{e(HOME_TITLE)}</title>', s, count=1)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(HOME_DESC)}">', s, count=1)
    s = re.sub(r'\n<meta (?:property="(?:og|twitter):[^"]*"|name="(?:twitter:[^"]*|robots)")[^>]*>', '', s)
    s = re.sub(r'\n<link rel="(?:canonical|apple-touch-icon)"[^>]*>', '', s)
    s = re.sub(r'<link rel="icon"[^>]*>', '<link rel="icon" href="/favicon.svg" type="image/svg+xml">', s, count=1)
    social = f"""
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<link rel="canonical" href="{DOMAIN}/">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="en_US">
<meta property="og:url" content="{DOMAIN}/">
<meta property="og:title" content="{e(HOME_TITLE)}">
<meta property="og:description" content="{e(HOME_DESC)}">
<meta property="og:image" content="{DOMAIN}/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{e(HOME_TITLE)}">
<meta name="twitter:description" content="{e(HOME_DESC)}">
<meta name="twitter:image" content="{DOMAIN}/assets/og-image.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">"""
    d = f'<meta name="description" content="{e(HOME_DESC)}">'
    s = s.replace(d, d + social, 1)
    wp = webpage_node('/', 'WebPage', HOME_TITLE, HOME_DESC); wp.pop('breadcrumb'); wp['@id'] = f'{DOMAIN}/#webpage'
    schema = [org_node(), website_node(), wp,
              {'@type': 'ItemList', '@id': f'{DOMAIN}/#services', 'name': 'Law firm marketing services',
               'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'name': lab, 'url': f'{DOMAIN}{svc_url(sl)}'} for i, (sl, lab, *_) in enumerate(SERVICES)]}]
    s = re.sub(r'<script type="application/ld\+json">.*?</script>', lambda m: jsonld(schema), s, count=1, flags=re.S)
    for sl, lab, _, _, old in SERVICES:
        if old: s = s.replace(f'href="{old}"', f'href="{svc_url(sl)}"')
    s = s.replace('<a class="cx-go" href="#contact">Talk to us about Consulting', f'<a class="cx-go" href="{svc_url("law-firm-consulting")}">Learn more about Consulting')
    s = s.replace('<a class="cx-go" href="#contact">Talk to us about Traditional', f'<a class="cx-go" href="{svc_url("law-firm-traditional-advertising")}">Learn more about Traditional')
    s = s.replace('href="about.html"', 'href="/about/"').replace('href="index.html"', 'href="/"').replace('info@mbpresults.com', EMAIL)
    s = s.replace('action="thanks.html"', 'action="/thanks.html"').replace('url("fonts/', 'url("/fonts/')
    s = s.replace('Vincere Marketing, LLC', BRAND)
    extra = open(os.path.join(BUILD, 'extra.css')).read() + '\n' + open(os.path.join(BUILD, 'booking.css')).read()
    s = swap_form(s)
    s = re.sub(r'<script id="bk-js">.*?</script>\n?', '', s, flags=re.S)
    s = s.replace('</body>', open(os.path.join(BUILD, 'booking.js')).read() + '</body>', 1)
    s = re.sub(r'#contact\.sec-grey\{--fd:48px;background:.*?\}', '#contact.sec-grey{background:#F7F1F6!important;padding-top:84px!important;padding-bottom:84px!important}', s, count=1, flags=re.S)
    if '/* nav dropdowns */' in s:
        s = re.sub(r'/\* nav dropdowns \*/.*?(?=</style>)', lambda m: '/* nav dropdowns */\n' + extra + '\n', s, count=1, flags=re.S)
    else:
        s = s.replace('</style>', '/* nav dropdowns */\n' + extra + '\n</style>', 1)
    s = re.sub(r'<script id="dd-js">.*?</script>\n?', '', s, flags=re.S)
    s = s.replace('</body>', DD_JS + '\n</body>', 1)
    if '<main id="main">' not in s:
        s = s.replace('<header class="hero hero-v2">', '<main id="main">\n<header class="hero hero-v2">', 1)
        s = s.replace('<footer class="foot">', '</main>\n<footer class="foot">', 1)
    s = s.replace('<html lang="en">', '<html lang="en-US">', 1)
    open(path, 'w').write(s)

def build_thanks():
    url = '/thanks.html'
    body = f'''<header class="phero" style="min-height:70vh">
  <div class="wrap phero-in">
    <div><div class="eyebrow" style="margin-bottom:26px"><span class="pulse"></span>Got it</div></div>
    <h1>Thanks. That reached us.</h1>
    <p class="lede">Someone from Vincere will be in touch shortly with market data for your practice and your area. If you would rather not wait, call us and we will pull it up on the phone right now.</p>
    <div class="btn-row"><a class="btn btn-orange btn-arr" href="tel:{PHONE_TEL}">Call {PHONE_DISPLAY}</a><a class="btn btn-out" href="/">Back to home</a></div>
  </div>
</header>'''
    h = head(url, 'Thanks, we will be in touch | Vincere Legal Marketing', 'Your request reached Vincere Legal Marketing.', [org_node(), website_node()], robots='noindex,follow')
    out = h + nav() + '\n<main id="main">\n' + body + '\n</main>\n' + footer() + '\n' + SCRIPTS + '\n</body>\n</html>\n'
    open(os.path.join(SITE, 'thanks.html'), 'w').write(out.replace('href="#contact"', 'href="/#contact"'))

def build_portal():
    os.makedirs(os.path.join(SITE, 'portal'), exist_ok=True)
    shutil.copy(os.path.join(BUILD, 'portal.html'), os.path.join(SITE, 'portal', 'index.html'))

def remove_old():
    for _, _, _, _, old in SERVICES:
        if old and os.path.exists(os.path.join(SITE, old)): os.remove(os.path.join(SITE, old))
    if os.path.exists(os.path.join(SITE, 'about.html')): os.remove(os.path.join(SITE, 'about.html'))

def main():
    build_css()
    for s, *_ in SERVICES:
        if os.path.exists(os.path.join(CONTENT, s + '.json')):
            build_service(s)
    for s, _ in PRACTICES:
        if os.path.exists(os.path.join(CONTENT, s + '.json')):
            build_practice(s)
    if os.path.exists(os.path.join(CONTENT, 'services-hub.json')): build_hub('services')
    if os.path.exists(os.path.join(CONTENT, 'practice-hub.json')): build_hub('practice')
    if os.path.exists(os.path.join(CONTENT, 'about.json')): build_about()
    patch_home()
    build_portal()
    build_thanks()
    remove_old()
    build_misc()
    print('built', len(SITEMAP), 'pages')

if __name__ == '__main__':
    main()
