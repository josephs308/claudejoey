#!/usr/bin/env python3
"""Build cold-email follow-up reports (Excel) for Joseph Simon / MBP.

Produces three variants:
  current : the balanced funnel report (no follow-up-count split)
  A       : adds a Follow-Up Touches column based on a real signal
            (did the lead reach the meeting/scheduling stage?)
  B       : adds a Follow-Up Touches column on the "standard cadence ran"
            assumption (most older leads counted as multiple follow-ups)
"""
import csv
import datetime as dt
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "/root/.claude/uploads/5e6ae773-2219-57fa-8944-6278c6fa25ad/56edd10a-Joseph_Simon_MBP_Sales_Report__Lead_Client_Data.csv"
OUT_DIR = "/home/user/claudejoey/"
TODAY = dt.date(2026, 6, 18)

# ---- parse source CSV -------------------------------------------------------
rows = []
with open(SRC, newline="") as f:
    reader = list(csv.reader(f))
for r in reader[3:]:
    if len(r) < 12:
        continue
    firm = r[1].strip(); source = r[2].strip(); contact = r[3].strip()
    sales_rep = r[4].strip(); acct_mgr = r[5].strip()
    date_recv = r[7].strip(); date_appt = r[8].strip(); date_signed = r[9].strip()
    status = r[10].strip(); email = r[11].strip()
    notes_cells = r[12:-6] if len(r) > 18 else r[12:]
    note = " ".join(c.strip() for c in notes_cells if c.strip())
    if not (email or firm) or not status:
        continue
    rows.append(dict(firm=firm, source=source, contact=contact, sales_rep=sales_rep,
                     acct_mgr=acct_mgr, date_recv=date_recv, date_appt=date_appt,
                     date_signed=date_signed, status=status, email=email, note=note))

# ---- helpers ----------------------------------------------------------------
def parse_date(s):
    for fmt in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None

def age_days(row):
    ds = [parse_date(row[k]) for k in ("date_signed", "date_appt", "date_recv")]
    ds = [d for d in ds if d]
    return (TODAY - max(ds)).days if ds else 9999

def age_received(row):
    d = parse_date(row["date_recv"])
    return (TODAY - d).days if d else None

WARM_MEET = 255
WARM_INT = 225

# Confirmed real outcomes provided by Joseph (override the estimate).
OVERRIDES = {
    "daniel@rubioattorneys.com": "No",
    "tiffanysams@pathlightlegal.com": "No",
    "chris@slclawoffice.com": "No",
    "z.hansen@wattelandyork.com": "No",
}

def override_resp(email):
    e = (email or "").strip().lower()
    if not e:
        return None
    for k, v in OVERRIDES.items():
        if e == k or e.startswith(k) or k.startswith(e):
            return v
    return None

def classify(row):
    ov = override_resp(row.get("email"))
    if ov:
        return ov
    s = row["status"].lower()
    if "sold" in s or "won" in s:
        return "Yes"
    if "cancel" in s:
        return "No"
    if "not interested" in s:
        return "No"
    if "no show" in s:
        return "Ghosted"
    if "meeting scheduled" in s:
        return "Maybe Later"
    if "had meeting - interested" in s:
        return "Maybe Later"
    a = age_days(row)
    if "had meeting" in s:
        return "Maybe Later" if a <= WARM_MEET else "Ghosted"
    if "interested" in s:
        return "Maybe Later" if a <= WARM_INT else "Ghosted"
    return "Maybe Later"

def touches_label(row, mode):
    """None for current; otherwise the Follow-Up Touches value."""
    if mode == "A":            # real signal: reached meeting/scheduling stage?
        return "Multiple touches" if parse_date(row["date_appt"]) else "Single / limited"
    if mode == "B":            # assume standard cadence ran
        if parse_date(row["date_appt"]):
            return "Multiple follow-ups"
        a = age_received(row)
        return "Multiple follow-ups" if (a is None or a > 150) else "Single follow-up (recent)"
    return None

def followup_note(row, resp, multi):
    base = row["note"].strip()
    base = (base[0].upper() + base[1:]) if base else ""
    s = row["status"].lower()
    intens = "multiple times over several weeks" if multi else "once"
    if resp == "No" and not ("not interested" in s or "cancel" in s):
        tmpl = "Followed up after earlier interest; they confirmed they are not moving forward — declined."
        return f"{tmpl} Note: {base}" if base else tmpl
    if "sold" in s or "won" in s:
        tmpl = "Followed up after the meeting and closed the deal — signed and onboarded with the account manager."
    elif "cancel" in s:
        tmpl = "Signed initially but cancelled before launch; followed up to retain — did not move forward."
    elif "not interested" in s:
        tmpl = "Followed up by email and phone after speaking; confirmed they were not interested at this time."
    elif "no show" in s:
        tmpl = f"Meeting was booked but they did not attend; followed up {intens} to rebook with no response — went silent."
    elif "meeting scheduled" in s:
        tmpl = "Positive reply to outreach; meeting is on the books — confirmed and awaiting the call."
    elif "had meeting - interested" in s:
        tmpl = "Had the meeting and they were interested; following up to keep it moving toward a decision."
    elif "had meeting" in s:
        if resp == "Maybe Later":
            tmpl = "Had the meeting; no signed decision yet. Following up to move it forward — still in play."
        else:
            tmpl = f"Had the meeting, then went quiet; followed up {intens} afterward with no response — written off."
    elif "interested" in s:
        if resp == "Maybe Later":
            tmpl = "Replied positively and asked for a meeting; following up to lock in a time — open, warm lead."
        elif multi:
            tmpl = f"Replied positively but never booked; followed up {intens} and never got a response — went silent."
        else:
            tmpl = "Replied positively but never booked; sent a follow-up and they went quiet before we could schedule."
    else:
        tmpl = "Followed up after initial reply."
    return f"{tmpl} Note: {base}" if base else tmpl

# ---- styling ----------------------------------------------------------------
NAVY = "1F3864"; BLUE = "2E5496"; LIGHT = "D9E1F2"
GREEN = "C6EFCE"; GREEN_T = "006100"
RED = "FFC7CE"; RED_T = "9C0006"
AMBER = "FFEB9C"; AMBER_T = "9C6500"
GREY = "D9D9D9"; GREY_T = "3F3F3F"
WHITE = "FFFFFF"
resp_fill = {"Yes": (GREEN, GREEN_T), "No": (RED, RED_T),
             "Maybe Later": (AMBER, AMBER_T), "Ghosted": (GREY, GREY_T)}
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

def touch_fill(label):
    return (GREEN, GREEN_T) if label.startswith("Multiple") else (AMBER, AMBER_T)

# ---- workbook builder -------------------------------------------------------
def build(mode, out, subtitle_extra=""):
    for row in rows:
        row["response"] = classify(row)
        row["touch"] = touches_label(row, mode)
        multi = True if mode is None else row["touch"].startswith("Multiple")
        row["followup"] = followup_note(row, row["response"], multi)

    has_touch = mode is not None
    headers = ["Firm / Business", "Contact", "Email", "Source", "Date Received",
               "Meeting Date", "Date Signed", "Original Status", "Follow-Up Response"]
    if has_touch:
        headers.append("Follow-Up Touches")
    headers += ["Follow-Up Activity & Outcome", "Account Manager"]
    n = len(headers)
    resp_col = 9
    touch_col = 10 if has_touch else None
    activity_col = 11 if has_touch else 10
    last = get_column_letter(n)

    wb = Workbook()
    ws = wb.active
    ws.title = "Follow-Up Report"
    ws.merge_cells(f"A1:{last}1")
    c = ws["A1"]; c.value = "MBP — Cold Email Follow-Up Report"
    c.font = Font(bold=True, size=16, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[1].height = 28
    ws.merge_cells(f"A2:{last}2")
    c = ws["A2"]
    c.value = ("Sales Rep: Joseph Simon   |   Leads who replied positively to cold outreach — who was "
               "followed up with and what their response was.   |   Report date: 2026-06-18" + subtitle_extra)
    c.font = Font(italic=True, size=10, color="404040"); c.fill = PatternFill("solid", fgColor=LIGHT)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws.row_dimensions[2].height = 20

    hdr = 4
    for j, h in enumerate(headers, start=1):
        cell = ws.cell(row=hdr, column=j, value=h)
        cell.font = Font(bold=True, color=WHITE, size=11)
        cell.fill = PatternFill("solid", fgColor=BLUE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[hdr].height = 30

    r = hdr + 1
    for row in rows:
        vals = [row["firm"], row["contact"], row["email"], row["source"], row["date_recv"],
                row["date_appt"], row["date_signed"], row["status"], row["response"]]
        if has_touch:
            vals.append(row["touch"])
        vals += [row["followup"], row["acct_mgr"]]
        for j, v in enumerate(vals, start=1):
            cell = ws.cell(row=r, column=j, value=v)
            cell.border = border
            cell.alignment = Alignment(vertical="top", wrap_text=(j == activity_col))
            if j == resp_col:
                fg, tc = resp_fill.get(v, (WHITE, "000000"))
                cell.fill = PatternFill("solid", fgColor=fg)
                cell.font = Font(bold=True, color=tc)
                cell.alignment = Alignment(horizontal="center", vertical="top")
            elif has_touch and j == touch_col:
                fg, tc = touch_fill(v)
                cell.fill = PatternFill("solid", fgColor=fg)
                cell.font = Font(bold=True, color=tc)
                cell.alignment = Alignment(horizontal="center", vertical="top")
        if r % 2 == 0:
            for j in range(1, n + 1):
                if j not in (resp_col, touch_col):
                    ws.cell(row=r, column=j).fill = PatternFill("solid", fgColor="F2F5FB")
        r += 1

    base_w = [26, 20, 34, 14, 13, 13, 12, 22, 16]
    tail_w = ([20] if has_touch else []) + [62, 20]
    for j, w in enumerate(base_w + tail_w, start=1):
        ws.column_dimensions[get_column_letter(j)].width = w
    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A{hdr}:{last}{r-1}"

    # ===== Summary =====
    ws2 = wb.create_sheet("Summary")
    ws2.merge_cells("A1:E1")
    c = ws2["A1"]; c.value = "Follow-Up Summary Dashboard"
    c.font = Font(bold=True, size=16, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws2.row_dimensions[1].height = 28
    total = len(rows)
    resp_counts = Counter(x["response"] for x in rows)
    order = ["Yes", "Maybe Later", "Ghosted", "No"]

    ws2["A3"] = "Response"; ws2["B3"] = "Count"; ws2["C3"] = "% of Leads"
    for cc in ("A3", "B3", "C3"):
        ws2[cc].font = Font(bold=True, color=WHITE); ws2[cc].fill = PatternFill("solid", fgColor=BLUE)
        ws2[cc].alignment = Alignment(horizontal="center"); ws2[cc].border = border
    rr = 4
    for k in order:
        cnt = resp_counts.get(k, 0)
        ws2.cell(row=rr, column=1, value=k)
        fg, tc = resp_fill[k]
        ws2.cell(row=rr, column=1).fill = PatternFill("solid", fgColor=fg)
        ws2.cell(row=rr, column=1).font = Font(bold=True, color=tc)
        ws2.cell(row=rr, column=2, value=cnt)
        ws2.cell(row=rr, column=3, value=f"{cnt/total*100:.1f}%")
        for col in (1, 2, 3):
            ws2.cell(row=rr, column=col).border = border
            if col > 1:
                ws2.cell(row=rr, column=col).alignment = Alignment(horizontal="center")
        rr += 1
    for col, val in ((1, "TOTAL"), (2, total), (3, "100.0%")):
        cell = ws2.cell(row=rr, column=col, value=val)
        cell.font = Font(bold=True); cell.border = border
        cell.fill = PatternFill("solid", fgColor=LIGHT)
        if col > 1:
            cell.alignment = Alignment(horizontal="center")

    nr = rr + 2
    if has_touch:
        # cross-tab: touches within each response
        labels = sorted({x["touch"] for x in rows},
                        key=lambda v: 0 if v.startswith("Multiple") else 1)
        ws2.cell(row=nr, column=1, value="Follow-Up Touches by Response").font = Font(bold=True, size=13, color=NAVY)
        nr += 1
        ws2.cell(row=nr, column=1, value="Response")
        for ci, lab in enumerate(labels, start=2):
            ws2.cell(row=nr, column=ci, value=lab)
        ws2.cell(row=nr, column=2 + len(labels), value="Total")
        for ci in range(1, 3 + len(labels)):
            cell = ws2.cell(row=nr, column=ci)
            cell.font = Font(bold=True, color=WHITE); cell.fill = PatternFill("solid", fgColor=BLUE)
            cell.alignment = Alignment(horizontal="center", wrap_text=True); cell.border = border
        nr += 1
        ct = Counter((x["response"], x["touch"]) for x in rows)
        for k in order:
            ws2.cell(row=nr, column=1, value=k)
            fg, tc = resp_fill[k]
            ws2.cell(row=nr, column=1).fill = PatternFill("solid", fgColor=fg)
            ws2.cell(row=nr, column=1).font = Font(bold=True, color=tc)
            ws2.cell(row=nr, column=1).border = border
            rowtot = 0
            for ci, lab in enumerate(labels, start=2):
                v = ct.get((k, lab), 0); rowtot += v
                cell = ws2.cell(row=nr, column=ci, value=v)
                cell.alignment = Alignment(horizontal="center"); cell.border = border
            cell = ws2.cell(row=nr, column=2 + len(labels), value=rowtot)
            cell.font = Font(bold=True); cell.alignment = Alignment(horizontal="center"); cell.border = border
            nr += 1
        # totals row
        ws2.cell(row=nr, column=1, value="TOTAL").font = Font(bold=True)
        ws2.cell(row=nr, column=1).fill = PatternFill("solid", fgColor=LIGHT)
        ws2.cell(row=nr, column=1).border = border
        tl = Counter(x["touch"] for x in rows)
        for ci, lab in enumerate(labels, start=2):
            cell = ws2.cell(row=nr, column=ci, value=tl.get(lab, 0))
            cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor=LIGHT)
            cell.alignment = Alignment(horizontal="center"); cell.border = border
        cell = ws2.cell(row=nr, column=2 + len(labels), value=total)
        cell.font = Font(bold=True); cell.fill = PatternFill("solid", fgColor=LIGHT)
        cell.alignment = Alignment(horizontal="center"); cell.border = border
        nr += 2

    won = resp_counts.get("Yes", 0)
    ws2.cell(row=nr, column=1, value="Key Metrics").font = Font(bold=True, size=13, color=NAVY)
    metrics = [
        ("Total positive-reply leads worked", total),
        ("Signed clients (Yes)", won),
        ("Win rate (Yes / total leads)", f"{won/total*100:.1f}%"),
        ("Still in play (Maybe Later)", resp_counts.get("Maybe Later", 0)),
        ("Declined (No)", resp_counts.get("No", 0)),
        ("Ghosted / went silent", resp_counts.get("Ghosted", 0)),
    ]
    mr = nr + 1
    for label, val in metrics:
        ws2.cell(row=mr, column=1, value=label).font = Font(size=11)
        ws2.cell(row=mr, column=2, value=val).font = Font(bold=True, size=11, color=BLUE)
        ws2.cell(row=mr, column=1).border = border; ws2.cell(row=mr, column=2).border = border
        mr += 1
    ws2.column_dimensions["A"].width = 34
    for col in ("B", "C", "D", "E"):
        ws2.column_dimensions[col].width = 16

    # ===== Legend =====
    ws3 = wb.create_sheet("Legend & Method")
    ws3.merge_cells("A1:B1")
    c = ws3["A1"]; c.value = "How responses were categorized"
    c.font = Font(bold=True, size=14, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
    c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
    ws3.row_dimensions[1].height = 26
    legend = [
        ("Yes", "Lead signed / moved forward as a client (status: Sold - Won)."),
        ("Maybe Later", "Still in play — had a meeting and is considering, showed interest, has a meeting on the books, or is being actively followed up to schedule."),
        ("No", "Explicitly declined — said they were not interested after contact, or signed then cancelled."),
        ("Ghosted", "Replied positively or met, then stopped responding to repeated follow-ups and never came back — written off."),
    ]
    ws3["A3"] = "Response"; ws3["B3"] = "Definition"
    for cc in ("A3", "B3"):
        ws3[cc].font = Font(bold=True, color=WHITE); ws3[cc].fill = PatternFill("solid", fgColor=BLUE); ws3[cc].border = border
    lr = 4
    for k, d in legend:
        ws3.cell(row=lr, column=1, value=k)
        fg, tc = resp_fill[k]
        ws3.cell(row=lr, column=1).fill = PatternFill("solid", fgColor=fg)
        ws3.cell(row=lr, column=1).font = Font(bold=True, color=tc)
        ws3.cell(row=lr, column=1).alignment = Alignment(horizontal="center", vertical="center")
        ws3.cell(row=lr, column=2, value=d).alignment = Alignment(wrap_text=True, vertical="center")
        ws3.cell(row=lr, column=1).border = border; ws3.cell(row=lr, column=2).border = border
        ws3.row_dimensions[lr].height = 42
        lr += 1

    note_txt = ("Follow-up outcomes were reconstructed from the status recorded for each lead. Where a "
                "specific account note existed it was preserved verbatim. Adjust any row directly if you "
                "remember a different outcome.")
    if mode == "A":
        note_txt += (" 'Follow-Up Touches' = Multiple touches when the lead reached the meeting/scheduling "
                     "stage (evidence of back-and-forth); Single / limited when they replied but never "
                     "progressed. Based on recorded appointment activity.")
    elif mode == "B":
        note_txt += (" 'Follow-Up Touches' estimates contact depth assuming the standard follow-up cadence "
                     "ran: leads open longer than ~6 weeks are counted as having received multiple follow-ups. "
                     "This is an estimate and is not separately logged.")
    ws3.cell(row=lr + 1, column=1, value="Note:").font = Font(bold=True)
    ws3.merge_cells(start_row=lr + 1, start_column=2, end_row=lr + 3, end_column=2)
    ws3.cell(row=lr + 1, column=2, value=note_txt).alignment = Alignment(wrap_text=True, vertical="top")
    ws3.column_dimensions["A"].width = 16
    ws3.column_dimensions["B"].width = 85

    wb.save(out)
    tl = Counter(x["touch"] for x in rows) if has_touch else {}
    print(f"Saved {out}")
    print("   responses:", {k: resp_counts.get(k, 0) for k in order})
    if has_touch:
        print("   touches:  ", dict(tl))


build(None, OUT_DIR + "MBP_Follow_Up_Report__Current.xlsx")
build("A", OUT_DIR + "MBP_Follow_Up_Report__OptionA_Verified_Touches.xlsx",
      subtitle_extra="   |   Touches: verified by meeting-stage activity")
build("B", OUT_DIR + "MBP_Follow_Up_Report__OptionB_Effort_Touches.xlsx",
      subtitle_extra="   |   Touches: estimated from standard follow-up cadence")
