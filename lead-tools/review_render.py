"""Render a market review (data.json from market_review.py) as a slide deck,
rep notes, and growth plan fields."""

import datetime as dt
import glob
import html
import os
import shutil
import subprocess
import urllib.parse

DARK, PLUM, LILAC, GREY = "#0B0A0B", "#492141", "#D6C3D2", "#A6A6A6"
PAPER, LINE, INK, MUTED, BAR = "#F7F5F1", "#E6E3DC", "#0A0A0A", "#6B6B6B", "#BDB6AD"
RED, AMBER, GREEN = "#9B1C1C", "#8A5A00", "#1F6B3A"

V_LOGO = ('<svg width="34" height="34" viewBox="0 0 64 64" aria-hidden="true"><defs>'
          '<linearGradient id="vg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6A3660"/>'
          '<stop offset="1" stop-color="#2A1027"/></linearGradient><linearGradient id="vt" x1="0" y1="0" x2="1" y2="0">'
          '<stop offset=".5" stop-color="#fff"/><stop offset=".5" stop-color="#D6C3D2"/></linearGradient></defs>'
          '<rect width="64" height="64" rx="14" fill="url(#vg)"/><path d="M53.11 12Q53.31 12 53.31 12.38Q53.31 12.76 '
          '53.11 12.76Q50.89 12.76 48.97 14.48Q47.06 16.2 45.85 19.45L33.43 51.75Q33.37 52 32.76 52Q32.16 52 32.03 '
          '51.75L15.92 17.29Q14.83 14.99 13.69 13.88Q12.54 12.76 10.89 12.76Q10.69 12.76 10.69 12.38Q10.69 12 10.89 '
          '12Q11.71 12 12.25 12.06Q12.8 12.13 13.59 12.16Q14.39 12.19 15.73 12.19Q18.78 12.19 20.73 12.16Q22.67 12.13 '
          '23.97 12.06Q25.28 12 26.3 12Q26.49 12 26.49 12.38Q26.49 12.76 26.3 12.76Q23.62 12.76 22.7 14.1Q21.78 15.44 '
          '22.99 17.92L35.28 44.55L32.67 48.94L44.13 19.2Q45.22 16.33 44.26 14.55Q43.31 12.76 40.06 12.76Q39.87 12.76 '
          '39.87 12.38Q39.87 12 40.06 12Q41.78 12 43.37 12.1Q44.96 12.19 47.51 12.19Q49.29 12.19 50.41 12.1Q51.52 12 '
          '53.11 12Z" fill="url(#vt)"/></svg>')

STAGES = [("search", "Search"), ("website", "Website"), ("call", "Call or form"),
          ("follow-up", "Follow-up"), ("consult", "Consultation"), ("signed", "Signed case")]
SEVERITY = {3: "Major leak", 2: "Leak", 1: "Minor"}


def e(s):
    return html.escape(str(s if s is not None else ""))


def domain(url):
    if not url:
        return ""
    host = urllib.parse.urlsplit(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def status_color(status):
    return {"Strong": GREEN, "Needs work": AMBER, "Leaking leads": RED}.get(status, MUTED)


def yesno(v, unknown="Not checked"):
    if v is None:
        return f'<span class="tag muted">{unknown}</span>'
    return '<span class="tag good">Yes</span>' if v else '<span class="tag bad">No</span>'


# ---------------------------------------------------------------- slides

class Deck:
    def __init__(self, d):
        self.d = d
        self.slides = []  # (html, notes)
        self.city_short = d["city"].split(",")[0]

    def add(self, body, notes, dark=False, cls=""):
        n = len(self.slides) + 1
        foot = (f'<div class="foot"><span>{e(self.d["firm"])} · Market review · {e(self.d["practice"]).title()} in '
                f'{e(self.city_short)}</span><span>Vincere Legal Marketing · {n}</span></div>')
        self.slides.append((f'<section class="slide {"dark" if dark else ""} {cls}">{body}{foot}</section>', notes))

    def head(self, eyebrow, title, sub=""):
        return (f'<div class="eyebrow">{e(eyebrow)}</div><h2>{title}</h2>'
                + (f'<p class="sub">{sub}</p>' if sub else ""))


def build(d):
    deck = Deck(d)
    sc, fs = d["score"], d["findings"]
    areas = {a["key"]: a for a in sc["areas"]}
    w, ps, g, ai, man = (d.get(k) or {} for k in ("website", "pagespeed", "google", "ai", "manual"))
    answers = man.get("call_answers", {})
    prof = dict((g.get("profile") or {}))
    if man.get("rating") is not None:
        prof["rating"] = man["rating"]
    if man.get("reviews") is not None:
        prof["reviews"] = man["reviews"]
    comps = sorted(list(g.get("competitors") or []) + man.get("competitors", []), key=lambda c: -(c.get("reviews") or 0))
    practice, city = d["practice"], d["city"]
    when = dt.date.fromisoformat(d["date"]).strftime("%B %-d, %Y")

    # 1. Cover
    deck.add(f'''
      <div class="brand">{V_LOGO}<span class="wordmark">Vincere</span></div>
      <div class="cover">
        <div class="eyebrow lilac">MARKET REVIEW · PREPARED FOR {e(d["firm"]).upper()}</div>
        <h1>How new clients find you, <span class="soft">and where they slip away.</span></h1>
        <p class="sub light">{e(practice).title()} in {e(city)} · {e(when)}{(" · For " + e(d["attorney"])) if d.get("attorney") else ""}</p>
      </div>''',
             f"Thank them for the time. Set the frame: “In 15 minutes I'll show you what a new client sees when they look "
             f"for a {practice} lawyer in {deck.city_short}, where leads are leaking, and what we'd fix first. Then you decide "
             f"if you want the free growth plan.” Confirm you have 15 minutes.", dark=True, cls="cover-slide")

    # 2. Scorecard
    rows = ""
    for a in sc["areas"]:
        pct = None if a["score"] is None else round(a["score"] * 100)
        bar = (f'<div class="track"><div class="fill" style="width:{pct}%;background:{status_color(a["status"])}"></div></div>'
               if pct is not None else '<div class="track"></div>')
        rows += (f'<div class="score-row"><span class="area">{e(a["label"])}</span>{bar}'
                 f'<span class="pct">{"–" if pct is None else pct}</span>'
                 f'<span class="tag" style="color:{status_color(a["status"])};border-color:{status_color(a["status"])}">{e(a["status"])}</span></div>')
    total = sc["total"]
    deck.add(f'''{deck.head("YOUR SCORECARD", "Your marketing system, scored")}
      <div class="split">
        <div class="hero-num"><b>{"–" if total is None else total}</b><span>out of 100</span>
          <div class="grade" style="color:{status_color("Leaking leads" if (total or 0) < 60 else "Needs work" if (total or 0) < 80 else "Strong")}">{e(sc["grade"])}</div>
          <p class="small">We checked {sc["checked"]} of 6 areas. Each area is weighted by how much it affects signed cases.</p></div>
        <div class="score-list">{rows}</div>
      </div>''',
             "Walk the scorecard top to bottom in 30 seconds; don't explain every row. Land on the lowest area: "
             "“This is where you're losing the most, so let's start there.” "
             + ("Areas marked Not checked: fill them in on this call." if sc["checked"] < 6 else ""))

    # 3. Where cases leak
    worst = {}
    for f in fs:
        worst[f["stage"]] = max(worst.get(f["stage"], 0), f["severity"])
    chips = ""
    for i, (key, label) in enumerate(STAGES):
        sev = worst.get(key, 0)
        cls = "leak3" if sev == 3 else "leak2" if sev == 2 else "leak1" if sev == 1 else "ok"
        word = SEVERITY.get(sev, "No leak found" if key not in ("consult",) else "Ask on this call")
        chips += (f'<div class="stage {cls}"><span class="n">{i + 1:02d}</span><b>{label}</b><span class="lab">{word}</span></div>'
                  + ('<div class="arrow">→</div>' if i < len(STAGES) - 1 else ""))
    leak_lines = "".join(
        f'<li><b>{dict(STAGES)[f["stage"]]}:</b> {e(f["title"])}</li>' for f in fs[:5])
    deck.add(f'''{deck.head("THE PATH TO A SIGNED CASE", "Where new clients slip away",
                            "Every signed case passes through these six steps. A leak at any step means a case that went to another firm.")}
      <div class="stages">{chips}</div>
      <ul class="leaks">{leak_lines or "<li>No leaks found in the checks we ran.</li>"}</ul>''',
             "This is the core slide. Say: “Most firms think they have a lead problem. Usually it's a leak problem. "
             "More ads into a leaky system just costs more.” Point to the first red step.")

    # 4. Website
    perf = ps.get("mobile_score") if ps.get("ok") else man.get("mobile_score")
    perf_color = RED if perf is not None and perf < 50 else AMBER if perf is not None and perf < 80 else GREEN
    checks = [("Tap-to-call phone number", w.get("click_to_call")), ("Contact form", w.get("contact_form")),
              ("Chat or text option", bool(w.get("chat")) if w.get("ok") else None),
              ("Online booking", bool(w.get("booking")) if w.get("ok") else None),
              ("Secure (https)", w.get("https")), ("Built for phones", w.get("viewport")),
              ("Spanish-language content", w.get("spanish"))]
    check_rows = "".join(f'<div class="check"><span>{e(l)}</span>{yesno(v if w.get("ok") else None)}</div>' for l, v in checks)
    metrics = "".join(f'<div class="metric"><span>{l}</span><b>{e(v)}</b></div>' for l, v in
                      (("Main content appears", ps.get("lcp")), ("First thing appears", ps.get("fcp")),
                       ("Real Chrome users rate it", (ps.get("real_user_rating") or "").title() or None)) if v)
    deck.add(f'''{deck.head("YOUR WEBSITE", "What a new client sees on their phone")}
      <div class="split">
        <div class="hero-num"><b style="color:{perf_color}">{"–" if perf is None else int(perf)}</b><span>mobile speed, out of 100</span>
          <p class="small">Google PageSpeed Insights, mobile test. 90+ is good; under 50 is poor.</p>
          <div class="metrics">{metrics}</div></div>
        <div class="checks"><h3>Can a visitor reach you?</h3>{check_rows}
          {f'<p class="small">Site: {e(domain(w.get("final_url") or d["site"]))}</p>' if w.get("ok") else f'<p class="small">{e(w.get("error", "Website not checked"))}</p>'}</div>
      </div>''',
             "Have them open their site on their phone while you talk. Ask: “If you'd just been in a car accident, "
             "would you wait for this to load?” Don't criticize whoever built it; say the site wasn't built to convert.")

    # 5. Google profile and reviews
    you_reviews = prof.get("reviews")
    bars_src = [(c["name"], c.get("reviews") or 0, c.get("rating"), False) for c in comps[:5]]
    if you_reviews is not None:
        bars_src.append((d["firm"] + " (you)", int(you_reviews), prof.get("rating"), True))
    bars_src.sort(key=lambda x: -x[1])
    mx = max([b[1] for b in bars_src] + [1])
    bars = "".join(
        f'<div class="bar-row{" you" if you else ""}"><span class="bn">{e(n)}</span>'
        f'<div class="bt"><div class="bf" style="width:{max(1.5, 100 * r / mx):.1f}%"></div></div>'
        f'<span class="bv">{r:,}{(" · " + format(rt, ".1f") + "★") if rt else ""}</span></div>'
        for n, r, rt, you in bars_src)
    rank = g.get("local_rank")
    stats = [("Star rating", f'{prof["rating"]:.1f}★' if prof.get("rating") else "–"),
             ("Google reviews", f'{int(you_reviews):,}' if you_reviews is not None else "–"),
             ("Local results rank", (f"#{rank}" if rank else "Not in top 10") if g.get("ok") else "–")]
    stat_html = "".join(f'<div class="stat"><span>{l}</span><b>{v}</b></div>' for l, v in stats)
    bench = sc.get("benchmark_reviews")
    gap_line = (f"The top 3 firms average {bench:,} reviews. Closing that gap means about "
                f"{max(0, bench - int(you_reviews)):,} more." if bench and you_reviews is not None and you_reviews < bench else "")
    deck.add(f'''{deck.head("GOOGLE", "How you compare on Google",
                            e(f"Reviews for firms in Google's local results for “{practice} lawyer in {city}”") if comps else "")}
      <div class="stats">{stat_html}</div>
      <div class="bars">{bars or '<p class="small">Add competitors to compare (--competitor).</p>'}</div>
      <p class="callout">{e(gap_line) or "Reviews are one of the main things Google uses to rank firms on the map."}</p>''',
             "Let the chart do the talking. Ask: “Do you ask every client for a review? Who does it?” If they say "
             "referrals are their main source, remind them referred clients check Google too.")

    # 6. Competitors
    comp_rows = "".join(
        f'<tr><td><b>{e(c["name"])}</b></td><td>{(format(c["rating"], ".1f") + "★") if c.get("rating") else "–"}</td>'
        f'<td>{(c.get("reviews") or 0):,}</td><td>{e(domain(c.get("website"))) or "–"}</td>'
        f'<td>{"24/7" if c.get("open_24_7") else ("Listed" if c.get("hours_listed") else "–")}</td></tr>'
        for c in comps[:6])
    deck.add(f'''{deck.head("YOUR MARKET", f"Who new clients see before they see you",
                            e(f"Firms in Google's local results for “{practice} lawyer in {city}”"))}
      <table class="tbl"><tr><th style="width:38%">Firm</th><th>Rating</th><th>Reviews</th><th>Website</th><th>Hours on Google</th></tr>
      {comp_rows or '<tr><td colspan="5">Add competitors with a Google API key or --competitor.</td></tr>'}</table>
      <p class="small">Public Google data on {e(when)}. Only one firm per practice area per city can work with Vincere.</p>''',
             "Ask: “Which of these do you lose cases to?” Facts only: never criticize a named firm. If a top firm "
             "shows 24/7 hours, point out that they answer around the clock.")

    # 7. AI search
    ai_named = ai.get("named") if ai.get("ok") else man.get("ai_named")
    ai_firms = ai.get("firms") or man.get("ai_firms") or []
    q = ai.get("question") or f"Who are the best {practice} lawyers in {city}?"
    verdict = ("Not checked yet" if ai_named is None else "You were named" if ai_named else "You weren't named")
    vcolor = MUTED if ai_named is None else GREEN if ai_named else RED
    firm_list = "".join(f"<li>{e(f)}</li>" for f in ai_firms[:6]) or "<li>Run the check live on this call.</li>"
    deck.add(f'''{deck.head("AI SEARCH", "What AI tells people who ask for a lawyer")}
      <div class="split">
        <div><div class="quote">“{e(q)}”</div>
          <div class="verdict" style="color:{vcolor}">{verdict}</div>
          <p class="small">More people ask ChatGPT, Gemini or Google's AI before calling anyone. {e(ai.get("engine", ""))}</p></div>
        <div class="card"><h3>Firms the AI recommended</h3><ol class="named">{firm_list}</ol></div>
      </div>''',
             "If it wasn't run ahead of time, ask ChatGPT live while screen-sharing; it lands harder. Ask: “Have you "
             "ever tried this?” AI answers change from day to day, so present it as a snapshot.")

    # 8. After-hours call test
    call = man.get("call_test") or {}
    labels = {"live": "A person answered", "service": "An answering service or AI answered",
              "voicemail": "It went to voicemail", "no-answer": "It rang with no answer",
              "full-mailbox": "The voicemail box was full"}
    if call.get("result"):
        result_html = (f'<div class="verdict" style="color:{GREEN if call["result"] in ("live", "service") else RED}">'
                       f'{e(labels.get(call["result"], call["result"]))}</div>'
                       f'<div class="metrics">'
                       + (f'<div class="metric"><span>When we called</span><b>{e(call.get("when"))}</b></div>' if call.get("when") else "")
                       + (f'<div class="metric"><span>Called back</span><b>{e(call.get("callback") or "No")}</b></div>' if call["result"] == "voicemail" else "")
                       + '</div>')
    else:
        result_html = ('<div class="verdict" style="color:#6B6B6B">Not tested yet</div>'
                       '<p class="small">Call the main line as a new client after 6 pm before the review.</p>')
    deck.add(f'''{deck.head("AFTER HOURS", "We called after hours, as a new client")}
      <div class="split">
        <div>{result_html}</div>
        <div class="card"><h3>Why it matters</h3>
          <p>People call when something happens, and that's often evenings and weekends.</p>
          <p>A caller who reaches voicemail can call the next firm on the list in seconds.</p>
          <p><b>With Vincere:</b> AI answers after hours, takes their details and books the consultation. Any missed call gets a text back within 60 seconds. Your staff still answers during the day.</p></div>
      </div>''',
             "Ask before showing the result: “What happens when someone calls at 8 pm on a Saturday?” Then show "
             "what actually happened. Never say we do their intake or answer all their calls.")

    # 9. Tracking
    track_rows = [("Website analytics", ", ".join(w.get("analytics", [])) or None, bool(w.get("analytics")) if w.get("ok") else None),
                  ("Ad conversion tracking", ", ".join(w.get("ads_tags", [])) or None, bool(w.get("ads_tags")) if w.get("ok") else None),
                  ("Call tracking", ", ".join(w.get("call_tracking", [])) or None, bool(w.get("call_tracking")) if w.get("ok") else None),
                  ("Lead follow-up software (CRM)", ", ".join(w.get("crm", [])) or None, bool(w.get("crm")) if w.get("ok") else None)]
    tr = "".join(f'<div class="check"><span>{e(l)}{(" <i>· " + e(x) + "</i>") if x else ""}</span>{yesno(v, "Ask")}</div>'
                 for l, x, v in track_rows)
    gtm_note = ("You use Google Tag Manager, so some tracking may be hidden inside it; worth confirming."
                if "Google Tag Manager" in w.get("analytics", []) else "")
    deck.add(f'''{deck.head("TRACKING", "Can you see what a signed case cost?")}
      <div class="split">
        <div class="checks"><h3>What we found on your site</h3>{tr}<p class="small">{e(gtm_note)}</p></div>
        <div class="card"><h3>The question that matters</h3>
          <p>If you spent $5,000 on marketing last month, could you tell which calls it produced, and which of those signed?</p>
          <p>Most reports stop at clicks and traffic. We track every lead from the first click to the signed case.</p></div>
      </div>''',
             "Ask: “Does your report show signed cases, or traffic and clicks?” Then: “How many companies handle your "
             "marketing right now?” Write the answers down for the growth plan.")

    # 10. Biggest leaks (statement slide)
    top = fs[:3]
    cards = "".join(f'''<div class="leak-card"><span class="sev">{SEVERITY[f["severity"]].upper()}</span>
        <h3>{e(f["title"])}</h3><p>{e(f["evidence"])}</p><p class="why">{e(f["why"])}</p></div>''' for f in top)
    deck.add(f'''<div class="eyebrow lilac">WHAT WE'D FIX FIRST</div><h2>Your three biggest leaks</h2>
      <div class="leak-cards">{cards or '<p>No major leaks found in the checks we ran.</p>'}</div>''',
             "Read each title, not the whole card. Ask: “Which of these would you fix first?” Let them pick; it "
             "becomes the first line of their growth plan.", dark=True)

    # 11. What it's costing (their numbers only)
    calls = answers.get("monthly_calls")
    share = answers.get("after_hours_share")
    value = answers.get("case_value")
    close = answers.get("close_rate")
    if calls and share and value and close:
        missed = round(calls * share / 100)
        cases = missed * close / 100
        at_risk = round(cases * value)
        body = f'''<div class="math">
          <div class="m"><b>{calls}</b><span>new-client calls a month</span></div><div class="op">×</div>
          <div class="m"><b>{share}%</b><span>come in after hours</span></div><div class="op">=</div>
          <div class="m"><b>{missed}</b><span>after-hours calls a month</span></div></div>
          <div class="math"><div class="m"><b>{missed}</b><span>after-hours calls</span></div><div class="op">×</div>
          <div class="m"><b>{close}%</b><span>your sign rate</span></div><div class="op">×</div>
          <div class="m"><b>${value:,}</b><span>average fee</span></div><div class="op">=</div>
          <div class="m big"><b>${at_risk:,}</b><span>a month in cases at stake</span></div></div>
          <p class="small">Built from your own estimates, assuming after-hours callers sign at your usual rate. Not every one is lost; the question is how many call the next firm instead.</p>'''
    else:
        body = '''<div class="blanks">
          <div class="blank"><span>New-client calls a month</span><b>____</b></div>
          <div class="blank"><span>Share that come in after hours</span><b>____%</b></div>
          <div class="blank"><span>Consultations that sign</span><b>____%</b></div>
          <div class="blank"><span>Average fee per case</span><b>$____</b></div></div>
          <p class="small">Your numbers, not ours. We'll do the math together and put it in your growth plan.</p>'''
    deck.add(f'''{deck.head("WHAT IT'S WORTH", "Let's put a number on it")}{body}''',
             "Ask each number and fill it in live (rerun with --monthly-calls, --after-hours-share, --close-rate, "
             "--case-value). Never supply the numbers yourself; it has to be their math.")

    # 12. How Vincere fixes it
    by_area = {}
    for f in fs:
        by_area.setdefault(f["area"], []).append(f["fix"])
    cols = [("01", "Attract", "Get found by new clients", ["google", "ai"],
             ["Local Services Ads", "Google Ads", "SEO", "AI search (AEO)", "Google Business Profile"]),
            ("02", "Convert", "Turn visitors into leads", ["website", "capture"],
             ["New fast website", "Landing pages", "Lead forms", "Online booking"]),
            ("03", "Capture", "Never miss a lead", ["calls"],
             ["After-hours AI answering", "Missed-call texts in 60 sec", "CRM pipeline", "SMS & email follow-up"]),
            ("04", "Measure", "Know what's working", ["tracking"],
             ["Call tracking", "Cost per lead", "Cost per signed case", "Monthly strategy call"])]
    col_html = ""
    for n, name, desc, keys, items in cols:
        hits = [x for k in keys for x in by_area.get(k, [])]
        col_html += (f'<div class="pillar{" hit" if hits else ""}"><span class="n">{n}</span><h3>{name}</h3><p class="desc">{desc}</p>'
                     + "".join(f"<li>{e(i)}</li>" for i in items)
                     + (f'<p class="fixes"><b>Fixes your:</b> {len(hits)} leak{"s" if len(hits) != 1 else ""}</p>' if hits else "")
                     + "</div>")
    deck.add(f'''{deck.head("THE FIX", "One team, one system, one monthly price",
                            "Your website, ads, Google and AI search, and lead follow-up, run together and tracked to signed cases.")}
      <div class="pillars">{col_html}</div>''',
             "Tie each highlighted column back to a leak they agreed with. Keep it short; the offer is next.")

    # 13. Founding partner offer
    deck.add(f'''<div class="eyebrow lilac">FOUNDING PARTNER PROGRAM · 3 SPOTS</div>
      <h2>Pay nothing until your growth plan is ready. <span class="soft" style="white-space:nowrap">Then month-to-month.</span></h2>
      <div class="offer">
        <div class="price"><span>Founding rate</span><b>$2,500<small>/month</small></b><span>+ performance-based lead generation</span>
          <p>Rises to $4,000 after the founding spots fill.</p></div>
        <ul class="offer-list">
          <li>Free growth plan first. You pay nothing until it's in your hands.</li>
          <li>Month-to-month. No long-term contract.</li>
          <li>You own your domain, content and lead data.</li>
          <li>Ad spend is paid directly to Google and Meta, never marked up.</li>
          <li>One firm per practice area per city. <b>{e(practice).title()} in {e(deck.city_short)} is still open.</b></li>
        </ul>
      </div>''',
             "State the offer, then stop talking. If asked about price: “Most agencies charge that for SEO alone.” "
             "If they're under contract: “Let's build the plan now so it's ready before your renewal.”",
             dark=True)

    # 14. Next step
    deck.add(f'''{deck.head("NEXT STEP", "Your free growth plan")}
      <div class="split">
        <div class="card"><h3>What's in it</h3><ul class="plain">
          <li>Your market: search demand and cost per click for {e(practice)} in {e(deck.city_short)}</li>
          <li>Where you stand, from this review</li>
          <li>Your competitors and the channels they use</li>
          <li>Recommended channels and budget</li>
          <li>A lead guarantee, in writing</li>
          <li>Timeline and monthly investment</li></ul></div>
        <div class="cta"><h3>To build it we need</h3><ul class="plain">
          <li>A 60-minute kickoff call</li><li>Access to your Google Business Profile</li>
          <li>Your current phone setup</li><li>The case types you want more of</li></ul>
          <div class="book">Book your kickoff call · joe@vincerelegalmarketing.com</div></div>
      </div>''',
             "Close: “Let's get your kickoff on the calendar. Does [day] or [day] work better?” Send the offer sheet "
             "and calendar invite the same day.")
    return deck


# ---------------------------------------------------------------- page

CSS = f"""
*{{box-sizing:border-box}}html,body{{margin:0;background:#2a2729}}
body{{font-family:system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:{INK}}}
.slide{{width:1280px;height:720px;position:relative;overflow:hidden;background:{PAPER};padding:56px 72px 70px;
  display:flex;flex-direction:column;gap:18px;margin:24px auto;box-shadow:0 10px 40px rgba(0,0,0,.35)}}
.slide.dark{{background:radial-gradient(60% 90% at 95% 0%,rgba(106,54,96,.6),rgba(106,54,96,0) 70%),{DARK};color:#fff}}
h1,h2,h3{{font-family:Arial,'Helvetica Neue',sans-serif;margin:0;letter-spacing:-.03em}}
h1{{font-size:64px;line-height:1.02;letter-spacing:-.045em;max-width:1000px}}
h2{{font-size:44px;line-height:1.05}} h3{{font-size:22px;margin-bottom:10px}}
.soft{{color:{GREY}}} .eyebrow{{font-size:14px;letter-spacing:.14em;font-weight:700;color:{PLUM}}}
.eyebrow.lilac{{color:{LILAC}}} .sub{{font-size:20px;color:{MUTED};margin:0;max-width:1000px;line-height:1.4}}
.sub.light{{color:rgba(255,255,255,.72)}} .small{{font-size:15px;color:{MUTED};line-height:1.45;margin:6px 0 0}}
.dark .small{{color:rgba(255,255,255,.65)}}
.foot{{position:absolute;left:72px;right:72px;bottom:24px;display:flex;justify-content:space-between;font-size:13px;color:{MUTED}}}
.dark .foot{{color:rgba(255,255,255,.5)}}
.brand{{display:flex;align-items:center;gap:12px}} .wordmark{{font-family:Georgia,serif;font-weight:700;font-size:26px}}
.cover{{margin-top:auto;margin-bottom:40px;display:flex;flex-direction:column;gap:20px}}
.split{{display:grid;grid-template-columns:400px 1fr;gap:48px;flex:1;align-items:start}}
.hero-num b{{display:block;font-family:Arial,sans-serif;font-size:150px;line-height:.9;letter-spacing:-.06em;color:{PLUM}}}
.hero-num>span{{font-size:18px;color:{MUTED}}} .grade{{font-family:Arial,sans-serif;font-weight:700;font-size:30px;margin-top:14px}}
.score-list{{display:flex;flex-direction:column;gap:24px;padding-top:16px}}
.score-row{{display:grid;grid-template-columns:270px 1fr 46px 150px;align-items:center;gap:16px;font-size:21px}}
.track{{height:14px;background:{LINE};border-radius:6px;overflow:hidden}} .fill{{height:100%;border-radius:6px}}
.pct{{font-weight:700;text-align:right;font-variant-numeric:tabular-nums}}
.tag{{display:inline-block;border:1.5px solid currentColor;border-radius:999px;padding:3px 12px;font-size:14px;font-weight:700;text-align:center;white-space:nowrap}}
.tag.good{{color:{GREEN}}} .tag.bad{{color:{RED}}} .tag.muted{{color:{MUTED}}}
.stages{{display:flex;align-items:stretch;gap:8px;margin-top:10px}} .arrow{{align-self:center;color:{GREY};font-size:22px}}
.stage{{flex:1;border-radius:14px;padding:20px 16px;display:flex;flex-direction:column;gap:6px;background:#fff;border:1.5px solid {LINE}}}
.stage .n{{font-size:13px;font-weight:700;color:{MUTED}}} .stage b{{font-size:19px}} .stage .lab{{font-size:14px;font-weight:700}}
.stage.ok .lab{{color:{GREEN}}} .stage.leak1 .lab{{color:{AMBER}}}
.stage.leak2{{border-color:{RED}}} .stage.leak2 .lab{{color:{RED}}}
.stage.leak3{{background:{RED};border-color:{RED};color:#fff}} .stage.leak3 .n,.stage.leak3 .lab{{color:#fff}}
.leaks{{margin:18px 0 0;padding-left:24px;font-size:23px;line-height:1.55;display:flex;flex-direction:column;gap:4px}}
.checks{{display:flex;flex-direction:column}} .check{{display:flex;justify-content:space-between;align-items:center;gap:16px;
  padding:14px 0;border-bottom:1px solid {LINE};font-size:19px}} .check i{{color:{MUTED};font-style:normal;font-size:15px}}
.metrics{{display:flex;flex-direction:column;gap:8px;margin-top:18px}}
.metric{{display:flex;justify-content:space-between;border-top:1px solid {LINE};padding-top:8px;font-size:17px}} .metric span{{color:{MUTED}}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:6px}}
.stat{{background:#fff;border:1px solid {LINE};border-radius:14px;padding:14px 18px;display:flex;justify-content:space-between;align-items:baseline}}
.stat span{{color:{MUTED};font-size:16px}} .stat b{{font-family:Arial,sans-serif;font-size:30px;letter-spacing:-.03em}}
.bars{{display:flex;flex-direction:column;gap:14px;margin-top:8px}}
.bar-row{{display:grid;grid-template-columns:330px 1fr 130px;align-items:center;gap:14px;font-size:20px}}
.bn{{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} .bt{{height:30px}}
.bf{{height:100%;background:{BAR};border-radius:0 4px 4px 0}} .bv{{font-variant-numeric:tabular-nums;color:{MUTED}}}
.bar-row.you .bn,.bar-row.you .bv{{font-weight:700;color:{PLUM}}} .bar-row.you .bf{{background:{PLUM}}}
.callout{{margin:auto 0 0;font-size:19px;font-weight:600;color:{PLUM}}}
.tbl{{width:100%;border-collapse:collapse;font-size:21px}} .tbl th{{text-align:left;font-size:13px;letter-spacing:.1em;
  text-transform:uppercase;color:{MUTED};border-bottom:2px solid {INK};padding:8px 10px}}
.tbl td{{padding:17px 10px;border-bottom:1px solid {LINE}}}
.quote{{font-family:Georgia,serif;font-size:28px;line-height:1.3;border-left:4px solid {PLUM};padding-left:20px}}
.verdict{{font-family:Arial,sans-serif;font-size:40px;font-weight:700;letter-spacing:-.03em;margin-top:22px}}
.card{{background:#fff;border:1px solid {LINE};border-radius:18px;padding:28px 32px;font-size:20px;line-height:1.5}}
.card p{{margin:0 0 10px}} .named{{margin:0;padding-left:26px;font-size:22px;line-height:1.7}}
.leak-cards{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:8px}}
.leak-card{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.14);border-radius:18px;padding:22px;
  display:flex;flex-direction:column;gap:8px}} .leak-card h3{{font-size:26px;margin:0}}
.leak-card p{{margin:0;font-size:18px;line-height:1.45;color:rgba(255,255,255,.85)}} .leak-card .why{{color:rgba(255,255,255,.6)}}
.sev{{font-size:12px;letter-spacing:.14em;font-weight:700;color:{LILAC}}}
.math{{display:flex;align-items:center;gap:14px;margin-top:6px}} .op{{font-size:34px;color:{GREY}}}
.m{{background:#fff;border:1px solid {LINE};border-radius:16px;padding:16px 20px;display:flex;flex-direction:column;min-width:150px}}
.m b{{font-family:Arial,sans-serif;font-size:40px;letter-spacing:-.03em}} .m span{{font-size:15px;color:{MUTED}}}
.m.big{{background:{PLUM};border-color:{PLUM};color:#fff}} .m.big span{{color:{LILAC}}}
.blanks{{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;margin-top:20px}}
.blank{{background:#fff;border:1px solid {LINE};border-radius:16px;padding:36px 32px;display:flex;justify-content:space-between;align-items:baseline;font-size:23px}}
.blank b{{font-family:Arial,sans-serif;font-size:36px;color:{GREY}}}
.pillars{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;align-items:stretch}}
.pillar{{background:#fff;border:1px solid {LINE};border-radius:18px;padding:24px;font-size:18px;line-height:1.75}}
.pillar.hit{{border:2px solid {PLUM};background:#F4EEF3}} .pillar .n{{font-size:13px;font-weight:700;color:{PLUM}}}
.pillar h3{{margin:4px 0 0;font-size:26px}} .pillar .desc{{color:{MUTED};margin:0 0 8px;font-size:15px}}
.pillar li{{list-style:none}} .fixes{{margin:10px 0 0;color:{PLUM};font-size:15px}}
.offer{{display:grid;grid-template-columns:400px 1fr;gap:40px;margin-top:16px}}
.price{{background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);border-radius:20px;padding:26px;display:flex;flex-direction:column;gap:6px}}
.price span{{color:{LILAC};font-size:16px}} .price b{{font-family:Arial,sans-serif;font-size:72px;letter-spacing:-.05em}}
.price small{{font-size:22px;color:{GREY};letter-spacing:0}} .price p{{margin:8px 0 0;color:rgba(255,255,255,.6);font-size:15px}}
.offer-list{{margin:0;padding-left:24px;font-size:21px;line-height:1.55;display:flex;flex-direction:column;gap:8px}}
.plain{{margin:0;padding-left:22px;font-size:20px;line-height:1.7}}
.cta{{background:{DARK};color:#fff;border-radius:18px;padding:24px 28px}} .cta .plain{{color:rgba(255,255,255,.85)}}
.book{{margin-top:18px;background:{PLUM};border-radius:12px;padding:14px 18px;font-weight:700;font-size:18px}}
.notes{{display:none}}
body.present{{background:#000;overflow:hidden}} body.present .slide{{display:none;margin:0;position:absolute;left:50%;top:50%;box-shadow:none}}
body.present .slide.on{{display:flex}}
body.present .notes.on{{display:block;position:fixed;left:0;right:0;bottom:0;background:#111;color:#eee;font-size:17px;
  line-height:1.5;padding:14px 24px;max-height:30vh;overflow:auto;border-top:2px solid {PLUM}}}
.help{{position:fixed;right:14px;top:10px;color:#bbb;font-size:13px}} body.present .help{{display:none}}
@page{{size:1280px 720px;margin:0}}
@media print{{html,body{{background:none}} .help,.notes{{display:none!important}}
  .slide{{margin:0;box-shadow:none;break-after:page;page-break-after:always}}}}
"""

JS = """
const S=[...document.querySelectorAll('.slide')],N=[...document.querySelectorAll('.notes')];let i=0,notes=false;
function fit(){const k=Math.min(innerWidth/1280,innerHeight/720);S.forEach(s=>s.style.transform=`translate(-50%,-50%) scale(${k})`)}
function show(){S.forEach((s,j)=>s.classList.toggle('on',j===i));N.forEach((n,j)=>n.classList.toggle('on',notes&&j===i))}
function present(on){document.body.classList.toggle('present',on);if(on){fit();show()}else S.forEach(s=>s.style.transform='')}
addEventListener('resize',()=>document.body.classList.contains('present')&&fit());
addEventListener('keydown',ev=>{const p=document.body.classList.contains('present');
 if(ev.key==='p'||ev.key==='P'){present(!p);return}
 if(!p)return; if(['ArrowRight','PageDown',' '].includes(ev.key))i=Math.min(S.length-1,i+1);
 else if(['ArrowLeft','PageUp'].includes(ev.key))i=Math.max(0,i-1);
 else if(ev.key==='n'||ev.key==='N')notes=!notes; else if(ev.key==='Escape')present(false); else return;
 ev.preventDefault();show()});
document.addEventListener('click',ev=>{if(document.body.classList.contains('present')){i=Math.min(S.length-1,i+1);show()}});
"""


def render_html(d, deck):
    slides = "\n".join(s for s, _ in deck.slides)
    notes = "\n".join(f'<div class="notes"><b>Slide {k + 1} notes:</b> {e(n)}</div>' for k, (_, n) in enumerate(deck.slides))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(d["firm"])} · Market review</title><style>{CSS}</style></head>
<body><div class="help">Press P to present · ← → to move · N for notes</div>
{slides}
{notes}
<script>{JS}</script></body></html>"""


def find_chrome():
    for name in (os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if name and shutil.which(name):
            return shutil.which(name)
    for p in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              *sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))]:
        if os.path.exists(p):
            return p
    return None


def make_pdf(html_path, pdf_path):
    chrome = find_chrome()
    if not chrome:
        return False
    url = "file://" + os.path.abspath(html_path)
    r = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={os.path.abspath(pdf_path)}", url], capture_output=True, timeout=120)
    return r.returncode == 0 and os.path.exists(pdf_path)


# ---------------------------------------------------------------- notes & growth plan

AGENCY_ANGLES = {
    "Scorpion": "Usually 12–36 month contracts and the site may not transfer. Ask when it ends and whether they'd keep the site and domain.",
    "FindLaw": "PPC often needs $8K+/mo ad spend; long contracts. Ask what they spend on Google Ads and when the contract ends.",
    "Juris Digital": "Not exclusive to one firm per market. Lead with exclusivity and the full bundle.",
    "Grow Law": "Services priced separately. Lead with one price for the whole system.",
    "Superpractice": "Closest rival; they answer 24/7. Win on price, website and exclusivity; don't compete on daytime call handling.",
    "Justia": "Often a directory-style site. Lead with conversion: speed, tap-to-call, follow-up.",
}


def rep_notes(d, deck):
    w, man = d.get("website") or {}, d.get("manual", {})
    lines = [f"# Rep notes: {d['firm']}", "",
             f"{d['practice'].title()} in {d['city']} · {d['site']} · review dated {d['date']}",
             f"Score {d['score']['total']}/100 ({d['score']['grade']}), {d['score']['checked']} of 6 areas checked.", "",
             "## Internal intel (never say this to the firm)", ""]
    for label, key in (("Agency or site vendor", "agency"), ("Site platform", "platform"), ("Chat", "chat"),
                       ("Booking", "booking"), ("CRM", "crm"), ("Call tracking", "call_tracking"), ("Ad tags", "ads_tags")):
        lines.append(f"- {label}: {', '.join(w.get(key) or []) or 'none found'}")
    for a in w.get("agency") or []:
        if a in AGENCY_ANGLES:
            lines.append(f"- **{a} angle:** {AGENCY_ANGLES[a]}")
    if man.get("call_answers"):
        lines.append("- Their answers: " + ", ".join(f"{k.replace('_', ' ')} = {v}" for k, v in man["call_answers"].items()))
    errors = [f"{k}: {(d.get(k) or {}).get('error')}" for k in ("website", "pagespeed", "google", "ai")
              if (d.get(k) or {}).get("error")]
    if errors:
        lines += ["", "## Checks that didn't run", ""] + [f"- {x}" for x in errors]
    lines += ["", "## Leaks, most serious first", ""]
    for f in d["findings"]:
        lines.append(f"- **{f['title']}** ({['', 'minor', 'leak', 'major leak'][f['severity']]}). {f['evidence']}"
                     + (f" Ask: “{f['ask']}”" if f["ask"] else ""))
    lines += ["", "## Questions to get answered on the call", "",
              "- How long is your current contract, and when does it end?",
              "- How many companies handle your marketing right now?",
              "- If you left your agency tomorrow, would you keep your website and domain?",
              "- New-client calls a month? Share after hours? Sign rate? Average fee?",
              "- Who answers new calls during the day, and how fast are web leads called back?",
              "", "## Talk track, slide by slide", ""]
    lines += [f"{k + 1}. {n}" for k, (_, n) in enumerate(deck.slides)]
    lines += ["", "Never say: “we guarantee signed cases”, “we do your intake”, “we answer all your calls”, "
              "or anything negative about a named competitor or agency."]
    return "\n".join(lines) + "\n"


def growth_plan(d):
    w, ps, g, ai, man = (d.get(k) or {} for k in ("website", "pagespeed", "google", "ai", "manual"))
    prof = dict(g.get("profile") or {})
    for k in ("rating", "reviews"):
        if man.get(k) is not None:
            prof[k] = man[k]
    comps = sorted(list(g.get("competitors") or []) + man.get("competitors", []), key=lambda c: -(c.get("reviews") or 0))
    perf = ps.get("mobile_score") if ps.get("ok") else man.get("mobile_score")
    web_issue = next((f["title"] for f in d["findings"] if f["area"] in ("website", "capture")), "[main issue]")
    ai_named = ai.get("named") if ai.get("ok") else man.get("ai_named")
    ai_firms = ai.get("firms") or man.get("ai_firms") or []
    call = man.get("call_test") or {}
    top = comps[0] if comps else {}
    fmt = lambda v, f="{}": f.format(v) if v is not None else "[X]"
    lines = [f"# Growth plan fields: {d['firm']}", "",
             "Copy these into the growth plan template. Anything in [brackets] still needs research.", "",
             "## Page 1: cover", "",
             f"- Firm name: {d['firm']}", f"- Practice area: {d['practice']}", f"- City: {d['city']}",
             f"- Attorney: {d.get('attorney') or '[Attorney name]'}", "",
             "## Page 1: where you stand today", "",
             f"- **Website:** Mobile speed score {fmt(perf)}/100. {web_issue}.",
             f"- **Google reviews:** {fmt(prof.get('reviews'))} reviews, {fmt(prof.get('rating'), '{:.1f}')}★. "
             f"Top competitor: {top.get('name', '[name]')}, {fmt(top.get('reviews'))} reviews.",
             f"- **AI search:** Asked “best {d['practice']} lawyer in {d['city']}”: "
             f"{'named' if ai_named else 'not named' if ai_named is False else '[named / not named]'}. "
             f"Firms named: {', '.join(ai_firms[:3]) or '[X, Y]'}.",
             f"- **Call test:** Called as a new client on {call.get('when') or '[day, time]'}: "
             f"{call.get('result') or '[answered / voicemail]'}"
             + (f"; callback {call.get('callback') or 'none'}." if call.get("result") == "voicemail" else "."), "",
             "## Page 2: competitors", "", "| Firm | Reviews | Rating | Ads running | AI mention |", "|---|---|---|---|---|",
             f"| {d['firm']} | {fmt(prof.get('reviews'))} | {fmt(prof.get('rating'), '{:.1f}')} | [Y/N] | "
             f"{'Yes' if ai_named else 'No' if ai_named is False else '[Y/N]'} |"]
    for c in comps[:3]:
        mention = "Yes" if any(c["name"].lower()[:12] in f.lower() for f in ai_firms) else "No" if ai_firms else "[Y/N]"
        lines.append(f"| {c['name']} | {c.get('reviews', 0)} | {fmt(c.get('rating'), '{:.1f}')} | [Y/N] | {mention} |")
    lines += ["", "## Still to research for the plan", "",
              "- Monthly searches and cost per click for the top terms (Google Keyword Planner)",
              "- Typical cost per Local Services Ads lead in this market",
              "- Which competitors run Google Ads or LSA (search the main terms on a phone)",
              "", "## The firm's own numbers (from the call)", ""]
    ans = man.get("call_answers", {})
    lines += [f"- {k.replace('_', ' ').capitalize()}: {v}" for k, v in ans.items()] or ["- [not collected yet]"]
    return "\n".join(lines) + "\n"


def write_all(d, folder, pdf=True):
    deck = build(d)
    paths = []
    html_path = os.path.join(folder, "market-review.html")
    with open(html_path, "w") as f:
        f.write(render_html(d, deck))
    paths.append(html_path)
    if pdf:
        pdf_path = os.path.join(folder, "market-review.pdf")
        if make_pdf(html_path, pdf_path):
            paths.append(pdf_path)
    for name, text in (("rep-notes.md", rep_notes(d, deck)), ("growth-plan.md", growth_plan(d))):
        p = os.path.join(folder, name)
        with open(p, "w") as f:
            f.write(text)
        paths.append(p)
    return paths
