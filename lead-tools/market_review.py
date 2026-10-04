#!/usr/bin/env python3
"""Build a Vincere market review for a law firm.

Give it a firm's website, name, practice area and city. It checks:

  * the website: mobile speed (Google PageSpeed), click-to-call, contact
    form, chat or text, online booking, tracking tags, and which agency or
    platform built it (internal notes only)
  * the firm's Google Business Profile: rating, review count, hours
  * the local competition: the top firms in Google's local results and their
    reviews
  * AI search: whether an AI assistant names the firm when asked for the
    best lawyer in town

Then it scores everything, ranks the biggest leaks, and writes:

  leads/reviews/<firm>/data.json          everything collected (edit, re-render)
  leads/reviews/<firm>/market-review.html the slide deck to screen-share
  leads/reviews/<firm>/market-review.pdf  the same deck as a PDF (needs Chrome)
  leads/reviews/<firm>/rep-notes.md       talk track and internal intel
  leads/reviews/<firm>/growth-plan.md     fields for the growth plan template

Usage:
  python3 lead-tools/market_review.py --site https://smithlaw.com \\
      --firm "Smith Law" --practice "personal injury" --city "Austin, TX"

  # after the after-hours call test, or after editing data.json:
  python3 lead-tools/market_review.py --from leads/reviews/smith-law/data.json \\
      --call-test voicemail --callback "next morning"

Keys (optional; every check without one can be filled in by hand):
  GOOGLE_API_KEY     PageSpeed Insights API + Places API (New), same key
  ANTHROPIC_API_KEY  AI search check (pip install anthropic)

Standard library only, except the optional `anthropic` package.
"""

import argparse
import datetime as dt
import difflib
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import review_render  # noqa: E402

USER_AGENT = "VincereMarketReview/1.0 (+https://vincerelegalmarketing.com)"
PAGESPEED_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PLACES_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_FIELDS = ",".join("places." + f for f in (
    "id", "displayName", "formattedAddress", "rating", "userRatingCount",
    "websiteUri", "googleMapsUri", "regularOpeningHours", "primaryTypeDisplayName",
    "nationalPhoneNumber", "businessStatus",
))

# Signals found in a site's HTML. Each entry: label -> regex.
CHAT_WIDGETS = {
    "Intaker": r"intaker\.", "Ngage": r"ngage", "ApexChat": r"apexchat",
    "Juvo Leads": r"juvoleads", "LiveChat": r"livechatinc", "Intercom": r"intercom",
    "Drift": r"js\.driftt|drift\.com", "Tidio": r"tidio", "Podium": r"podium\.com",
    "Smith.ai chat": r"smith\.ai", "Birdeye": r"birdeye", "Gabby (Scorpion)": r"gabby",
    "HubSpot chat": r"js\.usemessages|hs-scripts", "LeadConnector chat": r"leadconnectorhq|msgsndr",
    "Text-us widget": r"text[- ]?us|sms:",
}
BOOKING = {
    "Calendly": r"calendly\.com", "Acuity": r"acuityscheduling", "Clio Grow": r"grow\.clio|clio\.com",
    "Lawmatics": r"lawmatics", "LeadConnector booking": r"leadconnectorhq\.com/widget/booking",
}
ANALYTICS = {"Google Analytics": r"gtag\(|G-[A-Z0-9]{6,}|google-analytics\.com",
             "Google Tag Manager": r"GTM-[A-Z0-9]{4,}"}
ADS_TAGS = {"Google Ads conversion tag": r"AW-\d{6,}", "Meta pixel": r"fbq\(|connect\.facebook\.net",
            "Microsoft Ads tag": r"bat\.bing\.com"}
CALL_TRACKING = {"CallRail": r"callrail", "CallTrackingMetrics": r"tctm\.co|calltrackingmetrics",
                 "WhatConverts": r"whatconverts", "Invoca": r"invoca"}
CRM = {"Lawmatics": r"lawmatics", "Clio Grow": r"grow\.clio", "HubSpot": r"hs-scripts|hubspot",
       "GoHighLevel": r"leadconnectorhq|msgsndr", "Lead Docket": r"leaddocket",
       "Salesforce": r"salesforce|pardot"}
# Who built or hosts the site. Internal intel for the rep, never shown to the firm.
AGENCIES = {
    "Scorpion": r"scorpion", "FindLaw": r"findlaw|lawinfo\.com",
    "Justia": r"justia", "LawLytics": r"lawlytics", "Juris Digital": r"jurisdigital",
    "Grow Law": r"growlaw", "Rankings.io": r"rankings\.io", "Consultwebs": r"consultwebs",
    "iLawyerMarketing": r"ilawyermarketing", "Martindale-Nolo / Lawyers.com": r"martindale|lawyers\.com|nolo\.com",
    "Esquire Digital": r"esquiredigital", "Nifty Marketing": r"niftymarketing",
    "Superpractice": r"superpractice", "On The Map": r"onthemap", "PaperStreet": r"paperstreet",
}
PLATFORMS = {"WordPress": r"wp-content|wp-includes", "Wix": r"wixstatic|wix\.com",
             "Squarespace": r"squarespace", "Duda": r"dudamobile|multiscreensite|duda\.co",
             "Webflow": r"webflow", "GoDaddy builder": r"godaddysites|img1\.wsimg"}

LEGAL_SUFFIXES = re.compile(
    r"\b(law\s+firm|law\s+offices?(\s+of)?|the\s+law\s+office\s+of|attorneys?(\s+at\s+law)?|lawyers?|"
    r"pllc|llp|llc|p\.?\s?c\.?|p\.?\s?a\.?|ltd|inc|group|associates|&|and|the)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------- fetching

def http_get(url, timeout=25, headers=None):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    start = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read(3_000_000)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.geturl(), resp.status, body.decode(charset, "replace"), time.time() - start


def http_json(url, data=None, headers=None, timeout=90):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers={
        "User-Agent": USER_AGENT, "Content-Type": "application/json", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def robots_allows(url):
    parts = urllib.parse.urlsplit(url)
    rp = urllib.robotparser.RobotFileParser()
    try:
        _, status, text, _ = http_get(f"{parts.scheme}://{parts.netloc}/robots.txt", timeout=10)
        rp.parse(text.splitlines() if status == 200 else [])
    except Exception:
        return True
    return rp.can_fetch(USER_AGENT, url)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.forms, self.inputs, self.title, self._in_title = [], 0, 0, "", False
        self.search_forms = 0
        self.ld_json, self._in_ld = [], False
        self.lang_links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"].strip())
        elif tag == "form":
            self.forms += 1
            blob = " ".join(str(v) for v in a.values()).lower()
            if "search" in blob or a.get("role") == "search":
                self.search_forms += 1
        elif tag in ("input", "textarea"):
            if (a.get("type") or "text").lower() not in ("hidden", "submit", "button", "search"):
                self.inputs += 1
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and (a.get("type") or "").lower() == "application/ld+json":
            self._in_ld = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        if self._in_ld:
            self.ld_json.append(data)


def find_signals(text, table):
    return [name for name, rx in table.items() if re.search(rx, text, re.IGNORECASE)]


AD_CLICK_PARAMS = {"gclid", "gbraid", "wbraid", "gad_source", "gad_campaignid", "msclkid", "fbclid"}


def ad_click_source(url):
    """A pasted link that came from an ad click says which ad network the firm pays."""
    q = set(urllib.parse.parse_qs(urllib.parse.urlsplit(url).query))
    if q & {"gclid", "gbraid", "wbraid", "gad_source", "gad_campaignid"}:
        return "Google Ads"
    if "msclkid" in q:
        return "Microsoft Ads"
    if "fbclid" in q:
        return None  # also added to shared links, so it doesn't prove a Meta ad
    return None


def normalize_site(url):
    """Add https:// if missing and drop ad-click and utm_ tracking parameters."""
    url = url.strip()
    if not re.match(r"https?://", url):
        url = "https://" + url
    parts = urllib.parse.urlsplit(url)
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
             if k not in AD_CLICK_PARAMS and not k.startswith("utm_")]
    return urllib.parse.urlunsplit(parts._replace(query=urllib.parse.urlencode(query), fragment=""))


def site_domain(url):
    host = urllib.parse.urlsplit(normalize_site(url)).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def check_website(site, practice, city):
    """Fetch the home page and the contact page and read what's on them."""
    out = {"url": site, "ok": False}
    try:
        if not robots_allows(site):
            out["error"] = "robots.txt asks crawlers not to fetch this site"
            return out
        final, status, body, secs = http_get(site)
    except Exception as e:
        # Try plain http before giving up.
        try:
            final, status, body, secs = http_get(site.replace("https://", "http://", 1))
        except Exception:
            out["error"] = f"couldn't load the site ({e})"
            return out
    out.update(ok=True, final_url=final, status=status, load_seconds=round(secs, 2),
               page_kb=round(len(body.encode()) / 1024))
    p = LinkParser()
    p.feed(body)

    # Also read the contact page, where the form usually lives.
    pages = body
    contact = next((l for l in p.links if "contact" in l.lower() and not l.startswith(("mailto:", "tel:"))), None)
    if contact:
        contact_url = urllib.parse.urljoin(final, contact)
        if site_domain(contact_url) == site_domain(final):
            try:
                _, _, cbody, _ = http_get(contact_url, timeout=15)
                cp = LinkParser()
                cp.feed(cbody)
                p.forms += cp.forms
                p.inputs += cp.inputs
                p.search_forms += cp.search_forms
                p.links += cp.links
                pages += cbody
                out["contact_page"] = contact_url
            except Exception:
                pass

    low = pages.lower()
    tel_links = sorted({l for l in p.links if l.lower().startswith("tel:")})
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d\d)", pages, re.I)]
    title = " ".join(p.title.split())
    practice_words = [w for w in re.findall(r"[a-z]+", practice.lower()) if len(w) > 3]
    city_name = city.split(",")[0].strip().lower()
    ld = " ".join(p.ld_json)

    out.update(
        https=final.startswith("https://"),
        viewport='name="viewport"' in low or "name='viewport'" in low,
        title=title,
        title_has_practice=any(w in title.lower() for w in practice_words) if practice_words else None,
        title_has_city=city_name in title.lower() if city_name else None,
        click_to_call=bool(tel_links),
        tel_links=tel_links[:3],
        contact_form=(p.forms - p.search_forms) > 0 and p.inputs >= 2,
        chat=find_signals(pages, CHAT_WIDGETS),
        booking=find_signals(pages, BOOKING),
        analytics=find_signals(pages, ANALYTICS),
        ads_tags=find_signals(pages, ADS_TAGS),
        call_tracking=find_signals(pages, CALL_TRACKING),
        crm=find_signals(pages, CRM),
        agency=find_signals(pages, AGENCIES),
        platform=find_signals(pages, PLATFORMS),
        schema=bool(re.search(r"LegalService|Attorney|LocalBusiness|LawFirm", ld)),
        spanish=bool(re.search(r"español|espanol|hablamos", low)),
        copyright_year=max(years) if years else None,
    )
    return out


def check_pagespeed(site, key):
    params = {"url": site, "strategy": "mobile", "category": "performance"}
    if key:
        params["key"] = key
    url = PAGESPEED_URL + "?" + urllib.parse.urlencode(params)
    for attempt in range(2):
        try:
            data = http_json(url, timeout=120)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt == 0:
                time.sleep(8)
                continue
            msg = "rate limited; add GOOGLE_API_KEY" if e.code == 429 else f"HTTP {e.code}"
            return {"ok": False, "error": f"PageSpeed: {msg}"}
        except Exception as e:
            return {"ok": False, "error": f"PageSpeed: {e}"}
    lh = data.get("lighthouseResult", {})
    audits = lh.get("audits", {})
    score = lh.get("categories", {}).get("performance", {}).get("score")
    field = data.get("loadingExperience", {}).get("overall_category")

    def val(k):
        return audits.get(k, {}).get("displayValue")

    return {
        "ok": score is not None,
        "mobile_score": round(score * 100) if score is not None else None,
        "lcp": val("largest-contentful-paint"),
        "fcp": val("first-contentful-paint"),
        "tbt": val("total-blocking-time"),
        "cls": val("cumulative-layout-shift"),
        "real_user_rating": field,  # FAST / AVERAGE / SLOW from Chrome users, when Google has data
    }


def places_search(query, key, n=10):
    data = http_json(PLACES_URL, {"textQuery": query, "pageSize": n},
                     headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": PLACES_FIELDS}, timeout=30)
    out = []
    for p in data.get("places", []):
        out.append({
            "id": p.get("id"),
            "name": (p.get("displayName") or {}).get("text", ""),
            "address": p.get("formattedAddress", ""),
            "rating": p.get("rating"),
            "reviews": p.get("userRatingCount", 0) or 0,
            "website": p.get("websiteUri"),
            "maps_url": p.get("googleMapsUri"),
            "phone": p.get("nationalPhoneNumber"),
            "category": (p.get("primaryTypeDisplayName") or {}).get("text"),
            "hours_listed": bool(p.get("regularOpeningHours")),
            "open_24_7": _is_24_7(p.get("regularOpeningHours")),
            "status": p.get("businessStatus"),
        })
    return out


def _is_24_7(hours):
    if not hours:
        return False
    periods = hours.get("periods") or []
    return len(periods) == 1 and "close" not in periods[0]


def name_key(name):
    return " ".join(LEGAL_SUFFIXES.sub(" ", name.lower()).replace(",", " ").split())


def same_firm(place, firm, domain):
    if place.get("website") and domain and site_domain(place["website"]) == domain:
        return True
    a, b = name_key(place.get("name", "")), name_key(firm)
    return bool(a and b) and (a == b or difflib.SequenceMatcher(None, a, b).ratio() > 0.82)


def gbp_name_from_url(url):
    m = re.search(r"/place/([^/@?]+)", url or "")
    return urllib.parse.unquote_plus(m.group(1)) if m else None


def check_google(firm, site, practice, city, key, gbp_url=None):
    if not key:
        return {"ok": False, "error": "no GOOGLE_API_KEY; add rating and reviews by hand"}
    domain = site_domain(site) if site else None
    lookup = gbp_name_from_url(gbp_url) or firm
    out = {"ok": True, "query": f"{practice} lawyer in {city}"}
    try:
        matches = places_search(f"{lookup} {city}", key, n=5)
        profile = next((p for p in matches if same_firm(p, firm, domain)), None)
        out["profile"] = profile
        out["profile_found"] = profile is not None
        competitors = places_search(out["query"], key, n=10)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:200]
        return {"ok": False, "error": f"Places API HTTP {e.code}: {detail}"}
    except Exception as e:
        return {"ok": False, "error": f"Places API: {e}"}
    rank = next((i + 1 for i, p in enumerate(competitors) if same_firm(p, firm, domain)), None)
    out["local_rank"] = rank  # position in Google's local results for the main search, or None
    out["competitors"] = [p for p in competitors if not same_firm(p, firm, domain)
                          and p.get("status") in (None, "OPERATIONAL")][:6]
    return out


def check_ai_search(firm, practice, city, site):
    """Ask Claude, with web search, what a potential client would ask."""
    try:
        import anthropic
    except ImportError:
        return {"ok": False, "error": "pip install anthropic to run the AI search check"}
    question = (f"I need a {practice} lawyer in {city}. Who are the best {practice} lawyers or "
                f"law firms in {city}? Give me your top recommendations with a one-line reason each.")
    instructions = ("Answer the way you would for someone looking to hire a lawyer. After your answer, "
                    "add one last line that starts with FIRMS: and lists the firm names you "
                    "recommended, separated by semicolons.")
    client = anthropic.Anthropic()
    messages = [{"role": "user", "content": question + "\n\n" + instructions}]
    region = city.split(",")[1].strip() if "," in city else None
    tool = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5,
            "user_location": {"type": "approximate", "city": city.split(",")[0].strip(),
                              "country": "US", **({"region": region} if region else {})}}
    try:
        for _ in range(4):
            resp = client.beta.messages.create(
                model="claude-opus-5-5",
                max_tokens=16000,
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
                output_config={"effort": "medium"},
                tools=[tool],
                messages=messages,
            )
            if resp.stop_reason == "pause_turn":
                messages.append({"role": "assistant", "content": resp.content})
                continue
            break
    except anthropic.AuthenticationError:
        return {"ok": False, "error": "AI search: no valid ANTHROPIC_API_KEY"}
    except anthropic.RateLimitError:
        return {"ok": False, "error": "AI search: rate limited, try again in a minute"}
    except anthropic.APIStatusError as e:
        return {"ok": False, "error": f"AI search: API error {e.status_code}"}
    except anthropic.APIConnectionError:
        return {"ok": False, "error": "AI search: network error"}
    if resp.stop_reason == "refusal":
        return {"ok": False, "error": "AI search: the model declined this question"}
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    m = re.search(r"FIRMS:\s*(.+)$", text, re.MULTILINE)
    firms = [f.strip(" .*") for f in m.group(1).split(";") if f.strip()] if m else []
    answer = text[:m.start()].strip() if m else text
    key = name_key(firm)
    domain = site_domain(site) if site else ""
    named = any(name_key(f) == key or (key and key in name_key(f)) for f in firms) or \
        bool(key and key in name_key(answer)) or bool(domain and domain in answer.lower())
    return {"ok": True, "question": question, "named": named, "firms": firms[:8],
            "answer": answer[:1500], "engine": "Claude with web search"}


# ---------------------------------------------------------------- scoring

CALL_RESULTS = {
    # what happened -> (score 0-1, plain-English label)
    "live": (1.0, "A person answered"),
    "service": (0.8, "An answering service or AI answered"),
    "voicemail": (None, "Went to voicemail"),
    "no-answer": (0.0, "Rang with no answer"),
    "full-mailbox": (0.0, "Voicemail box was full"),
}


def callback_score(callback):
    """Voicemail scores by how fast the firm called back."""
    if not callback or callback.lower() in ("none", "no", "never", "no callback"):
        return 0.0
    c = callback.lower()
    mins = re.search(r"(\d+)\s*min", c)
    if mins and int(mins.group(1)) <= 15:
        return 0.6
    if mins or re.search(r"\b1\s*h|hour\b", c):
        return 0.45
    return 0.25  # next day or later


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def firm_profile(data):
    """The firm's Google numbers: from the API, or typed in by hand."""
    g = data.get("google") or {}
    prof = dict(g.get("profile") or {})
    manual = data.get("manual", {})
    for k_in, k_out in (("rating", "rating"), ("reviews", "reviews")):
        if manual.get(k_in) is not None:
            prof[k_out] = num(manual[k_in])
    found = g.get("profile_found")
    if manual.get("rating") is not None or manual.get("reviews") is not None:
        found = True
    return prof, found


def competitor_list(data):
    g = data.get("google") or {}
    comps = list(g.get("competitors") or [])
    comps += data.get("manual", {}).get("competitors", [])
    return sorted(comps, key=lambda c: -(c.get("reviews") or 0))


def score(data):
    """Score six areas 0-100. A check with no data is left out, not failed."""
    w, ps, g = data.get("website") or {}, data.get("pagespeed") or {}, data.get("google") or {}
    ai, manual = data.get("ai") or {}, data.get("manual", {})
    prof, found = firm_profile(data)
    comps = competitor_list(data)
    year = dt.date.today().year

    def area(key, label, weight, checks):
        have = [(cw, v) for _, cw, v, _ in checks if v is not None]
        s = sum(cw * v for cw, v in have) / sum(cw for cw, _ in have) if have else None
        return {"key": key, "label": label, "weight": weight, "score": s,
                "checks": [{"label": l, "value": v, "detail": d} for l, _, v, d in checks]}

    site_ok = w.get("ok")
    perf = ps.get("mobile_score") if ps.get("ok") else num(manual.get("mobile_score"))
    website = area("website", "Website and speed", 20, [
        ("Mobile speed score", 5, (perf / 100) if perf is not None else None,
         f"{int(perf)}/100 on Google PageSpeed (mobile)" if perf is not None else "Not measured"),
        ("Secure (https)", 2, (1.0 if w.get("https") else 0.0) if site_ok else None, ""),
        ("Built for phones", 1, (1.0 if w.get("viewport") else 0.0) if site_ok else None, ""),
        ("Practice area and city in the page title", 1,
         ((0.5 if w.get("title_has_practice") else 0) + (0.5 if w.get("title_has_city") else 0)) if site_ok else None,
         w.get("title", "")),
        ("Kept up to date", 1,
         (1.0 if (w.get("copyright_year") or 0) >= year - 1 else 0.0) if site_ok and w.get("copyright_year") else None,
         f"Footer says © {w.get('copyright_year')}" if w.get("copyright_year") else ""),
    ])
    capture = area("capture", "Turning visitors into leads", 15, [
        ("Tap-to-call phone number", 3, (1.0 if w.get("click_to_call") else 0.0) if site_ok else None, ""),
        ("Contact form", 3, (1.0 if w.get("contact_form") else 0.0) if site_ok else None, ""),
        ("Chat or text option", 2, (1.0 if w.get("chat") else 0.0) if site_ok else None, ", ".join(w.get("chat", []))),
        ("Online booking", 1, (1.0 if w.get("booking") else 0.0) if site_ok else None, ", ".join(w.get("booking", []))),
    ])

    rating, reviews = num(prof.get("rating")), num(prof.get("reviews"))
    top = [c.get("reviews") or 0 for c in comps[:3]]
    bench = sum(top) / len(top) if top else None
    if found is False:
        google_checks = [("Google Business Profile found", 4, 0.0, "We couldn't find a profile for this firm")]
    else:
        google_checks = [
            ("Star rating", 2, None if rating is None else (1.0 if rating >= 4.7 else 0.7 if rating >= 4.3 else 0.3 if rating >= 4.0 else 0.0),
             f"{rating:.1f}★" if rating is not None else ""),
            ("Reviews compared to the top 3 firms", 4,
             None if reviews is None or not bench else min(1.0, reviews / bench),
             f"{int(reviews)} vs about {int(bench)} for the top 3" if reviews is not None and bench else ""),
            ("Business hours listed", 1, None if not prof.get("id") else (1.0 if prof.get("hours_listed") else 0.0), ""),
            ("Website linked", 1, None if not prof.get("id") else (1.0 if prof.get("website") else 0.0), ""),
        ]
        rank = g.get("local_rank")
        if g.get("ok"):
            google_checks.append(("Shows up in the local results for the main search", 2,
                                  1.0 if rank and rank <= 3 else 0.6 if rank and rank <= 6 else 0.3 if rank else 0.0,
                                  f"#{rank} for “{g.get('query')}”" if rank else f"Not in the top 10 for “{g.get('query')}”"))
    google = area("google", "Google profile and reviews", 25, google_checks)

    ai_named = ai.get("named") if ai.get("ok") else manual.get("ai_named")
    ai_area = area("ai", "AI search", 10, [
        ("Named when someone asks an AI assistant", 1, None if ai_named is None else (1.0 if ai_named else 0.0),
         "; ".join((ai.get("firms") or manual.get("ai_firms") or [])[:5])),
    ])

    call = manual.get("call_test") or {}
    result = (call.get("result") or "").lower() or None
    if result == "voicemail":
        call_v = callback_score(call.get("callback"))
    else:
        call_v = CALL_RESULTS.get(result, (None, ""))[0] if result else None
    calls = area("calls", "After-hours calls", 20, [
        ("After-hours call test", 1, call_v,
         " · ".join(x for x in (call.get("when"), CALL_RESULTS.get(result, (0, result or ""))[1],
                                f"callback: {call.get('callback')}" if result == "voicemail" else "") if x)),
    ])

    gtm = "Google Tag Manager" in w.get("analytics", [])
    tracking = area("tracking", "Tracking leads to cases", 10, [
        ("Website analytics", 1, (1.0 if w.get("analytics") else 0.0) if site_ok else None, ", ".join(w.get("analytics", []))),
        ("Ad conversion tracking", 1, (1.0 if w.get("ads_tags") else (None if gtm else 0.0)) if site_ok else None,
         ", ".join(w.get("ads_tags", [])) or ("May be inside Tag Manager; ask" if gtm else "")),
        ("Call tracking", 2, (1.0 if w.get("call_tracking") else (None if gtm else 0.0)) if site_ok else None,
         ", ".join(w.get("call_tracking", [])) or ("May be inside Tag Manager; ask" if gtm else "")),
    ])

    areas = [website, capture, google, ai_area, calls, tracking]
    scored = [a for a in areas if a["score"] is not None]
    total = round(100 * sum(a["weight"] * a["score"] for a in scored) / sum(a["weight"] for a in scored)) if scored else None
    for a in areas:
        a["status"] = status_of(a["score"])
    return {"total": total, "grade": grade_of(total), "areas": areas,
            "checked": len(scored), "benchmark_reviews": round(bench) if bench else None}


def status_of(s):
    if s is None:
        return "Not checked"
    return "Strong" if s >= 0.8 else "Needs work" if s >= 0.5 else "Leaking leads"


def grade_of(total):
    if total is None:
        return "Not enough data"
    return "Strong" if total >= 80 else "Gaps to fix" if total >= 60 else "Leaking leads"


# ---------------------------------------------------------------- findings

def findings(data, sc):
    """The pain points, most serious first. Each one is something the firm can see."""
    w, ps, g = data.get("website") or {}, data.get("pagespeed") or {}, data.get("google") or {}
    ai, manual = data.get("ai") or {}, data.get("manual", {})
    prof, found = firm_profile(data)
    comps = competitor_list(data)
    city, practice = data["city"], data["practice"]
    out = []

    def add(sev, stage, area, title, evidence, why, fix, ask):
        out.append(dict(severity=sev, stage=stage, area=area, title=title, evidence=evidence,
                        why=why, fix=fix, ask=ask))

    perf = ps.get("mobile_score") if ps.get("ok") else num(manual.get("mobile_score"))
    if perf is not None and perf < 80:
        add(3 if perf < 50 else 2, "website", "website",
            "Your site is slow on phones",
            f"Google scores your mobile speed {int(perf)} out of 100" +
            (f"; the main content takes {ps['lcp']} to appear." if ps.get("lcp") else "."),
            "Most people looking for a lawyer search on their phone, often right after something has gone wrong. "
            "A slow page loses them before they see your number, and Google weighs speed in both "
            "search rankings and what you pay per ad click.",
            "A new fast website, included in the system fee.",
            "When you look at your own site on your phone, how long does it take to load?")
    if w.get("ok"):
        if not w.get("click_to_call"):
            add(3, "website", "capture", "Visitors on phones can't tap to call",
                "We didn't find a tap-to-call phone link on your home page or contact page.",
                "On a phone, someone has to copy your number by hand. That step loses callers.",
                "Tap-to-call buttons on every page, with call tracking.",
                "Where do most of your new cases come from now: phone calls or forms?")
        if not w.get("contact_form"):
            add(2, "website", "capture", "No contact form",
                "We didn't find a contact form on your home page or contact page.",
                "People who can't talk at that moment (at work, late at night) have no way to reach you.",
                "Short lead forms that text the person back within 60 seconds.",
                "What happens to people who visit your site after hours?")
        if not w.get("chat"):
            add(1, "follow-up", "capture", "No chat or text option",
                "We didn't find a chat or text-us option on the site.",
                "A lot of people would rather text than call, especially younger clients.",
                "Two-way texting from your website, connected to your CRM.",
                "Do clients ever ask if they can text you?")
        if not w.get("call_tracking") and "Google Tag Manager" not in w.get("analytics", []):
            add(2, "signed", "tracking", "You can't see which marketing brings in calls",
                "We didn't find call tracking on the site.",
                "Without it, a phone call from a Google ad looks the same as a call from a referral, "
                "so there's no way to know what each signed case cost.",
                "Call tracking and a dashboard that follows each lead to a signed case.",
                "If I asked what a signed case cost you last month, could you tell me?")
        if w.get("analytics") == [] and not w.get("ads_tags"):
            add(2, "signed", "tracking", "No analytics on the website",
                "We didn't find Google Analytics or any ad tracking tags.",
                "You can't tell how many people visit, where they come from, or what they do.",
                "Full tracking from first click to signed case.",
                "Does anyone send you a monthly report? What's in it?")
        yr = w.get("copyright_year")
        if yr and yr < dt.date.today().year - 1:
            add(1, "website", "website", "The site looks out of date",
                f"The footer says © {yr}.",
                "Small signs of neglect make people wonder if the firm is still active.",
                "A new website with content kept current.", "When was the site last updated?")
        if w.get("title") and not (w.get("title_has_practice") and w.get("title_has_city")):
            add(1, "search", "website", f"Your home page doesn't tell Google “{practice} in {city.split(',')[0]}”",
                f"Your page title is “{w['title'][:90]}”.",
                "The page title is one of the first things Google reads to decide what you rank for.",
                "SEO built around your practice areas and city.", "")

    rating, reviews = num(prof.get("rating")), num(prof.get("reviews"))
    if found is False:
        add(3, "search", "google", "We couldn't find your Google Business Profile",
            f"A search for your firm in {city} didn't return a matching Google profile.",
            "Your Google profile is what shows on the map with your reviews and call button. "
            "Without one, you're missing from the map results.",
            "We set up and optimize your Google Business Profile.",
            "Do you have a Google Business Profile, and who manages it?")
    elif comps and reviews is not None:
        leader = comps[0]
        bench = sc.get("benchmark_reviews") or 0
        if bench and reviews < bench * 0.8:
            gap = max(0, int(bench - reviews))
            add(3 if reviews < bench * 0.4 else 2, "search", "google",
                "Competitors have far more Google reviews",
                f"You have {int(reviews)} reviews. The top 3 firms average {bench}; "
                f"{leader['name']} has {leader.get('reviews', 0)}.",
                "Reviews are one of the main things Google uses to rank firms on the map, and the first "
                "thing people compare before they call.",
                "Automatic review requests after every case, through your CRM.",
                f"Do you ask clients for reviews? Closing that gap means about {gap} more.")
    if rating is not None and rating < 4.5:
        add(2, "search", "google", "Your star rating is below the top firms",
            f"Your Google rating is {rating:.1f}★.",
            "People skim stars first. A lower rating gets skipped even when the firm is better.",
            "Review requests to happy clients, and help responding to reviews.", "")
    if g.get("ok") and found and not g.get("local_rank"):
        add(2, "search", "google", f"You're not in the top 10 local results for “{g.get('query')}”",
            "Google's local business results for that search list other firms.",
            "That's the search people type when they need a lawyer now.",
            "Google Business Profile optimization, Local Services Ads and local SEO.", "")
    if prof.get("id") and not prof.get("hours_listed"):
        add(1, "search", "google", "No hours on your Google profile",
            "Your Google profile doesn't list business hours.",
            "Google can show you as closed or hide you from “open now” searches.",
            "We complete and maintain your profile.", "")

    ai_named = ai.get("named") if ai.get("ok") else manual.get("ai_named")
    ai_firms = ai.get("firms") or manual.get("ai_firms") or []
    if ai_named is False:
        add(3 if ai_firms else 2, "search", "ai", "AI assistants don't recommend you",
            f"We asked an AI assistant for the best {practice} lawyers in {city}. "
            + (f"It named {', '.join(ai_firms[:3])}, but not you." if ai_firms else "It didn't name your firm."),
            "More people now ask ChatGPT or Google's AI before they call anyone, including people "
            "who were referred to you and are checking you out.",
            "AI search optimization (AEO): content, reviews and listings that AI tools rely on.",
            "Have you ever asked ChatGPT who the best lawyer in town is?")

    call = manual.get("call_test") or {}
    result = (call.get("result") or "").lower()
    if result in ("voicemail", "no-answer", "full-mailbox"):
        cb = call.get("callback")
        sev = 3 if result != "voicemail" or callback_score(cb) < 0.5 else 2
        what = {"voicemail": "went to voicemail", "no-answer": "rang with no answer",
                "full-mailbox": "hit a full voicemail box"}[result]
        add(sev, "call", "calls", "After-hours calls aren't answered",
            f"We called as a new client{(' on ' + call['when']) if call.get('when') else ''} and it {what}." +
            (f" Callback: {cb}." if result == "voicemail" else ""),
            "People call when it happens: evenings and weekends. A caller who reaches voicemail can call "
            "the next firm on the list in seconds.",
            "After-hours AI call answering that takes details and books consultations, plus a text back within 60 seconds for any missed call.",
            "When someone calls at 8 pm on a Saturday, what happens?")

    out.sort(key=lambda f: -f["severity"])
    return out


STAGES = [("search", "Search"), ("website", "Website"), ("call", "Call or form"),
          ("follow-up", "Follow-up"), ("consult", "Consultation"), ("signed", "Signed case")]


# ---------------------------------------------------------------- main

def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:60] or "firm"


def merge_manual(data, args):
    m = data.setdefault("manual", {})
    if args.rating is not None:
        m["rating"] = args.rating
    if args.reviews is not None:
        m["reviews"] = args.reviews
    if args.mobile_score is not None:
        m["mobile_score"] = args.mobile_score
    if args.ai_named is not None:
        m["ai_named"] = args.ai_named == "yes"
    if args.ai_firms:
        m["ai_firms"] = [f.strip() for f in args.ai_firms.split(";") if f.strip()]
    if args.call_test:
        m["call_test"] = {"result": args.call_test, "when": args.call_when or m.get("call_test", {}).get("when"),
                          "callback": args.callback}
    for k in ("contract_end", "vendors", "monthly_calls", "after_hours_share", "case_value", "close_rate", "ad_spend"):
        v = getattr(args, k)
        if v is not None:
            m.setdefault("call_answers", {})[k] = v
    for c in args.competitor or []:
        parts = [p.strip() for p in c.split(";")]
        m.setdefault("competitors", []).append({
            "name": parts[0], "rating": num(parts[1]) if len(parts) > 1 else None,
            "reviews": int(num(parts[2]) or 0) if len(parts) > 2 else 0})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--site", help="the firm's website")
    ap.add_argument("--firm", help="firm name as it appears on Google")
    ap.add_argument("--practice", help="practice area, e.g. 'personal injury'")
    ap.add_argument("--city", help="city and state, e.g. 'Austin, TX'")
    ap.add_argument("--gbp", help="Google Maps link to the firm's profile (optional)")
    ap.add_argument("--attorney", help="who you're meeting, for the cover slide")
    ap.add_argument("--rep", help="your name, for the cover slide")
    ap.add_argument("--from", dest="from_json", help="re-render from an existing data.json")
    ap.add_argument("--out", default="leads/reviews", help="output folder (default leads/reviews)")
    ap.add_argument("--skip", default="", help="comma list of checks to skip: site,speed,google,ai")
    ap.add_argument("--no-pdf", action="store_true", help="don't make a PDF")
    g = ap.add_argument_group("filled in by hand")
    g.add_argument("--rating", type=float)
    g.add_argument("--reviews", type=int)
    g.add_argument("--mobile-score", type=int, help="from pagespeed.web.dev if the API is rate limited")
    g.add_argument("--competitor", action="append", help="'Name; 4.8; 312' (repeatable)")
    g.add_argument("--ai-named", choices=["yes", "no"], help="did ChatGPT name the firm?")
    g.add_argument("--ai-firms", help="firms ChatGPT named, separated by ;")
    g.add_argument("--call-test", choices=list(CALL_RESULTS), help="what happened on the after-hours call")
    g.add_argument("--call-when", help="when you called, e.g. 'Tue 7:40 pm'")
    g.add_argument("--callback", help="for voicemail: '12 min', '3 hours', 'next morning' or 'none'")
    g.add_argument("--contract-end", help="when their agency contract ends")
    g.add_argument("--vendors", type=int, help="how many companies handle their marketing")
    g.add_argument("--monthly-calls", type=int, help="new-client calls a month (their estimate)")
    g.add_argument("--after-hours-share", type=int, help="percent of calls after hours (their estimate)")
    g.add_argument("--case-value", type=int, help="average fee per signed case (their number)")
    g.add_argument("--close-rate", type=int, help="percent of consultations that sign (their number)")
    g.add_argument("--ad-spend", type=int, help="monthly ad spend")
    args = ap.parse_args()

    if args.from_json:
        with open(args.from_json) as f:
            data = json.load(f)
        folder = os.path.dirname(os.path.abspath(args.from_json))
    else:
        missing = [n for n in ("site", "firm", "practice", "city") if not getattr(args, n)]
        if missing:
            ap.error("need --" + ", --".join(missing) + " (or --from data.json)")
        site = normalize_site(args.site)
        data = {"firm": args.firm, "site": site, "practice": args.practice, "city": args.city,
                "gbp": args.gbp, "attorney": args.attorney, "rep": args.rep,
                "date": dt.date.today().isoformat(), "manual": {},
                "ad_click": ad_click_source(args.site)}
        folder = os.path.join(args.out, slugify(args.firm))
        skip = {s.strip() for s in args.skip.split(",") if s.strip()}
        gkey = os.environ.get("GOOGLE_API_KEY")
        steps = [
            ("site", "Reading the website", lambda: check_website(site, args.practice, args.city), "website"),
            ("speed", "Measuring mobile speed", lambda: check_pagespeed(site, gkey), "pagespeed"),
            ("google", "Checking Google profile and competitors",
             lambda: check_google(args.firm, site, args.practice, args.city, gkey, args.gbp), "google"),
            ("ai", "Asking an AI assistant", lambda: check_ai_search(args.firm, args.practice, args.city, site), "ai"),
        ]
        for key, label, fn, field in steps:
            if key in skip:
                data[field] = {"ok": False, "error": "skipped"}
                continue
            print(f"• {label}…", file=sys.stderr, flush=True)
            data[field] = fn()
            if not data[field].get("ok"):
                print(f"  ↳ {data[field].get('error')}", file=sys.stderr)
    for k in ("attorney", "rep"):
        if getattr(args, k):
            data[k] = getattr(args, k)
    merge_manual(data, args)

    sc = score(data)
    data["score"] = sc
    data["findings"] = findings(data, sc)
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "data.json"), "w") as f:
        json.dump(data, f, indent=2)
    paths = review_render.write_all(data, folder, pdf=not args.no_pdf)

    print(f"\n{data['firm']}: {sc['total'] if sc['total'] is not None else '–'}/100 · {sc['grade']} "
          f"({sc['checked']} of 6 areas checked)")
    for f in data["findings"][:3]:
        print(f"  {'!' * f['severity']:<3} {f['title']}")
    todo = [a["label"] for a in sc["areas"] if a["score"] is None]
    if todo:
        print("  Still to check: " + ", ".join(todo))
    for p in paths:
        print("  → " + p)


if __name__ == "__main__":
    main()
