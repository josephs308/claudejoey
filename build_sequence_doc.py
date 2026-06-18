#!/usr/bin/env python3
"""Render the re-engagement sequence as a Word document."""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "/home/user/claudejoey/MBP_ReEngagement_Sequence.docx"
NAVY = RGBColor(0x1F, 0x38, 0x64)
BLUE = RGBColor(0x2E, 0x54, 0x96)
GREY = RGBColor(0x40, 0x40, 0x40)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"
style.font.size = Pt(11)

def h1(t):
    p = doc.add_paragraph(); r = p.add_run(t)
    r.bold = True; r.font.size = Pt(18); r.font.color.rgb = NAVY
    return p

def h2(t):
    p = doc.add_paragraph(); p.space_before = Pt(8); r = p.add_run(t)
    r.bold = True; r.font.size = Pt(14); r.font.color.rgb = BLUE
    return p

def h3(t):
    p = doc.add_paragraph(); r = p.add_run(t)
    r.bold = True; r.font.size = Pt(12); r.font.color.rgb = NAVY
    return p

def body(t, italic=False, color=None):
    p = doc.add_paragraph(); r = p.add_run(t)
    r.italic = italic
    if color: r.font.color.rgb = color
    return p

def subject(t):
    p = doc.add_paragraph(); r = p.add_run("Subject: ")
    r.bold = True; r2 = p.add_run(t); r2.bold = True; r2.font.color.rgb = BLUE
    return p

def quote(lines):
    for ln in lines:
        p = doc.add_paragraph(ln)
        p.paragraph_format.left_indent = Inches(0.3)
        p.paragraph_format.space_after = Pt(2)
        for r in p.runs: r.font.color.rgb = GREY

def bullet(t):
    doc.add_paragraph(t, style="List Bullet")

h1("MBP Re-Engagement Sequence — 211 Unsettled Leads")
body("Goal: re-open every lead who isn't a signed client or a hard no, and let their "
     "replies surface the real status (Yes / Maybe Later / No / Ghosted). As replies come "
     "in, tag them in GoHighLevel — the campaign becomes your tracking system.", italic=True)

h3("Audience (from MBP_ReEngagement_Audience.csv)")
bullet("reengage-hot (36) — had a meeting / booked, no decision yet. Closest to signing.")
bullet("reengage-warm (43) — asked for a meeting, never scheduled. Get them on the calendar.")
bullet("reengage-dormant (128) — went quiet after earlier interest. One clean re-open + breakup.")
body("Personalize {{first_name}} and {{business_name}} with GHL merge fields. "
     "Send from your real inbox/domain, not a no-reply.", italic=True)

# ---- Segment 1 ----
h2("SEGMENT 1 — HOT (had a meeting, no decision)")
body("Direct, low-friction, assume the relationship.", italic=True)
h3("Email 1 — Day 1")
subject("picking this back up, {{first_name}}?")
quote(["{{first_name}} — we spoke a while back about getting {{business_name}} more signed cases "
       "and the timing wasn't right to pull the trigger. Things have moved since then and I think "
       "it's a better fit now.",
       "Worth a quick 15 minutes to see if it makes sense? Here's my calendar: [LINK]"])
h3("Email 2 — Day 4")
subject("the one number that matters")
quote(["Quick one — the firms we work with care about one thing: signed cases per dollar in. "
       "That's all we optimize for. If I could show you what that would look like for "
       "{{business_name}}, would that be worth 15 minutes? [LINK]"])
h3("Email 3 — Day 9 (breakup)")
subject("should I close your file?")
quote(["{{first_name}}, haven't heard back so I'll assume the timing still isn't right — no problem "
       "at all. Want me to keep your file open and check back next quarter, or close it out for now? "
       'Just reply "open" or "close."'])

# ---- Segment 2 ----
h2("SEGMENT 2 — WARM (interested, never booked)")
body("Re-spark the original interest, make scheduling effortless.", italic=True)
h3("Email 1 — Day 1")
subject("we never got you on the calendar, {{first_name}}")
quote(["{{first_name}} — you'd reached out about getting {{business_name}} more cases and we never "
       "managed to lock in a time. My fault for not chasing it down.",
       "Still want to take a look? Grab whatever slot works: [LINK]"])
h3("Email 2 — Day 5")
subject("60-second version")
quote(["If a full call is too much right now, here's the 60-second version: [1-line offer / short "
       "Loom link]. If it's interesting, the next step is a quick 15-min walkthrough: [LINK]"])
h3("Email 3 — Day 10 (breakup)")
subject("bad timing?")
quote(["Sounds like the timing might be off, {{first_name}} — totally fine. Want me to circle back "
       'in 90 days, or are you set for now? Just hit reply with "later" or "set."'])

# ---- Segment 3 ----
h2("SEGMENT 3 — DORMANT (went quiet)")
body("Pattern-interrupt, no guilt, easy out. This is the big batch — keep it short.", italic=True)
h3("Email 1 — Day 1")
subject("still worth a conversation, {{first_name}}?")
quote(["{{first_name}} — we connected a while back about more signed cases for {{business_name}} and "
       "then life happened on both ends. Reopening the door: still something you'd want to explore, "
       "or should I take you off my list? A one-word reply is plenty."])
h3("Email 2 — Day 6")
subject("quick proof, then I'll leave you alone")
quote(["Not here to nag — just one data point: [short result / case study, e.g. \"added 18 signed "
       "cases in 90 days for a firm your size\"]. If that's worth 15 minutes: [LINK]. If not, no "
       "hard feelings."])
h3("Email 3 — Day 12 (breakup)")
subject("closing your file, {{first_name}}")
quote(["Last one from me — I'll close your file so I'm not cluttering your inbox. If you ever want to "
       "revisit getting {{business_name}} more cases, just reply and I'll pick it right back up. "
       "Appreciate you either way."])

# ---- Run guide ----
h2("How to run it in GHL")
doc.add_paragraph("1.  Import MBP_ReEngagement_Audience.csv (maps Email + Tag).")
doc.add_paragraph("2.  Build 3 workflows, one per tag (reengage-hot / warm / dormant), with the emails above.")
doc.add_paragraph("3.  Reply handling = your live tracker: as replies land, tag the contact "
                  "status-yes, status-maybe, or status-no. No reply after the breakup = status-ghosted.")
doc.add_paragraph("4.  Weekly, pull counts per status tag — that's the report your boss asked for, "
                  "now built from real responses.")

doc.save(OUT)
print("Saved", OUT)
