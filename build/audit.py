import os,re,json,html,sys,urllib.request,urllib.parse
ROOT=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'vincere-site')
DOMAIN='https://vincerelegalmarketing.com'
pages={}
for d,_,fs in os.walk(ROOT):
    for f in fs:
        if f.endswith('.html'):
            p=os.path.join(d,f);rel='/'+os.path.relpath(p,ROOT).replace('index.html','')
            pages[rel]=open(p).read()
issues=[];titles={};descs={}
sm=open(os.path.join(ROOT,'sitemap.xml')).read();smurls=set(re.findall(r'<loc>(.*?)</loc>',sm))
def exists(path):
    path=path.split('#')[0].split('?')[0]
    if path.startswith('/portal'):return True
    fp=os.path.join(ROOT,path.lstrip('/'))
    return os.path.isfile(fp) or os.path.isfile(os.path.join(fp,'index.html'))
for url,s in sorted(pages.items()):
    t=re.search(r'<title>(.*?)</title>',s);d=re.search(r'<meta name="description" content="([^"]*)"',s)
    c=re.search(r'<link rel="canonical" href="([^"]*)"',s);r=re.search(r'<meta name="robots" content="([^"]*)"',s)
    t=html.unescape(t.group(1)) if t else None;d=html.unescape(d.group(1)) if d else None
    noindex=r and 'noindex' in r.group(1)
    if not t: issues.append((url,'no title'))
    elif len(t)>60 and not noindex: issues.append((url,f'title {len(t)} chars'))
    if not d: issues.append((url,'no description'))
    elif not noindex and not(120<=len(d)<=160): issues.append((url,f'desc {len(d)} chars'))
    if not c: issues.append((url,'no canonical'))
    elif c.group(1)!=DOMAIN+url: issues.append((url,'canonical mismatch '+c.group(1)))
    if not noindex:
        titles.setdefault(t,[]).append(url);descs.setdefault(d,[]).append(url)
        if DOMAIN+url not in smurls: issues.append((url,'not in sitemap'))
    h1=re.findall(r'<h1[\s>]',s)
    if len(h1)!=1: issues.append((url,f'{len(h1)} h1'))
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>',s,re.S):
        try:
            g=json.loads(blk)['@graph']
            types=[n['@type'] for n in g]
            ids=[n.get('@id') for n in g]
            for n in g:
                if n['@type']=='FAQPage':
                    for q in n['mainEntity']:
                        if html.escape(q['name']).replace('&#x27;','&rsquo;').replace("'",'&rsquo;') not in s and q['name'] not in html.unescape(s):
                            issues.append((url,'faq not visible: '+q['name'][:40]))
                if n['@type']=='BreadcrumbList':
                    for it in n['itemListElement']:
                        if it['item'].replace(DOMAIN,'') and not exists(it['item'].replace(DOMAIN,'')): issues.append((url,'bad crumb '+it['item']))
            # referenced ids resolve within graph
            refs=set(re.findall(r'"@id": ?"([^"]+)"',blk))
            for ref in refs:
                if ref not in ids and not ref.endswith('#logo'): issues.append((url,'dangling @id '+ref))
        except Exception as ex: issues.append((url,'jsonld error '+str(ex)))
    for h in re.findall(r'href="([^"]+)"',s):
        if h.startswith(('http','mailto:','tel:','#','data:')): continue
        if not exists(h): issues.append((url,'broken link '+h))
    for bad in ['mbpresults','MBP','Marketing Best Practices','filesafe']:
        if bad in s: issues.append((url,'contains '+bad))
for t,u in titles.items():
    if len(u)>1: issues.append((u,'duplicate title'))
for d,u in descs.items():
    if len(u)>1: issues.append((u,'duplicate description'))
print(len(pages),'pages;',len(smurls),'sitemap urls')
for i in issues: print(i)
print('ISSUES',len(issues))
