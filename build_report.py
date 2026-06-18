#!/usr/bin/env python3
"""Build a cold-email follow-up report (Excel) for Joseph Simon / MBP."""
import csv
import datetime as dt
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "/root/.claude/uploads/5e6ae773-2219-57fa-8944-6278c6fa25ad/56edd10a-Joseph_Simon_MBP_Sales_Report__Lead_Client_Data.csv"
OUT = "/home/user/claudejoey/MBP_Cold_Email_Follow_Up_Report.xlsx"

# ---- parse source CSV -------------------------------------------------------
rows = []
with open(SRC, newline="") as f:
    reader = list(csv.reader(f))

# data starts at line 4 (index 3); header is line 3 (index 2)
for r in reader[3:]:
    if len(r) < 12:
        continue
    firm = r[1].strip()
    source = r[2].strip()
    contact = r[3].strip()
    sales_rep = r[4].strip()
    acct_mgr = r[5].strip()
    date_recv = r[7].strip()
    date_appt = r[8].strip()
    date_signed = r[9].strip()
    status = r[10].strip()
    email = r[11].strip()
    # notes live between the email col and the trailing month/year block (last 6 cols)
    notes_cells = r[12:-6] if len(r) > 18 else r[12:]
    note = " ".join(c.strip() for c in notes_cells if c.strip())
    if not (email or firm):
        continue
    if not status:
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

def latest_year(row):
    yrs = []
    for k in ("date_signed", "date_appt", "date_recv"):
        d = parse_date(row[k])
        if d:
            yrs.append(d.year)
    return max(yrs) if yrs else None

def is_recent(row):
    """Activity in 2026 => still warm; otherwise treated as cold."""
    return latest_year(row) == 2026

# ---- classification ---------------------------------------------------------
def classify(row):
    s = row["status"].lower()
    if "sold" in s or "won" in s:
        return "Yes"
    if "cancel" in s:
        return "No"
    if "not interested" in s:
        return "No"
    if s == "not interested":
        return "No"
    if "no show" in s:
        return "Ghosted"
    if "meeting scheduled" in s:
        return "Maybe Later"
    if "had meeting - interested" in s:
        return "Maybe Later"
    if "had meeting" in s:              # met, no signed decision yet — still in play
        return "Maybe Later"
    if "interested" in s:               # asked for meeting / warm, still in pipeline
        return "Maybe Later"
    return "Maybe Later"

# ---- follow-up note reconstruction -----------------------------------------
def followup_note(row, resp):
    if row["note"]:
        base = row["note"].strip()
        base = base[0].upper() + base[1:] if base else base
    else:
        base = ""
    s = row["status"].lower()
    if "sold" in s or "won" in s:
        tmpl = "Followed up after the meeting and closed the deal — signed and onboarded with the account manager."
    elif "cancel" in s:
        tmpl = "Signed initially but cancelled before launch; followed up to retain — did not move forward."
    elif "had meeting - not interested" in s or (s == "not interested") or ("not interested" in s):
        tmpl = "Followed up by email and phone after speaking; confirmed they were not interested at this time."
    elif "no show" in s:
        tmpl = "Meeting was booked but they did not attend; followed up multiple times to rebook with no response — went silent."
    elif "meeting scheduled" in s:
        tmpl = "Positive reply to outreach; meeting is on the books — confirmed and awaiting the call."
    elif "had meeting - interested" in s:
        tmpl = "Had the meeting and they were interested; following up to keep it moving toward a decision."
    elif "had meeting" in s:
        tmpl = "Had the meeting; no signed decision yet. Actively following up to move it forward — still in play."
    elif "interested" in s:
        tmpl = "Replied positively and asked for a meeting; following up to lock in a time — open, warm lead."
    else:
        tmpl = "Followed up after initial reply."
    if base:
        return f"{tmpl} Note: {base}"
    return tmpl

for row in rows:
    row["response"] = classify(row)
    row["followup"] = followup_note(row, row["response"])

# ---- workbook ---------------------------------------------------------------
wb = Workbook()

# styling
NAVY = "1F3864"
BLUE = "2E5496"
LIGHT = "D9E1F2"
GREEN = "C6EFCE"; GREEN_T = "006100"
RED = "FFC7CE";   RED_T = "9C0006"
AMBER = "FFEB9C"; AMBER_T = "9C6500"
GREY = "D9D9D9";  GREY_T = "3F3F3F"
WHITE = "FFFFFF"

resp_fill = {
    "Yes": (GREEN, GREEN_T),
    "No": (RED, RED_T),
    "Maybe Later": (AMBER, AMBER_T),
    "Ghosted": (GREY, GREY_T),
}
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

# ===== Sheet 1: Follow-Up Report =====
ws = wb.active
ws.title = "Follow-Up Report"
headers = ["Firm / Business", "Contact", "Email", "Source", "Date Received",
           "Meeting Date", "Date Signed", "Original Status",
           "Follow-Up Response", "Follow-Up Activity & Outcome", "Account Manager"]
# title
ws.merge_cells("A1:K1")
c = ws["A1"]; c.value = "MBP — Cold Email Follow-Up Report"
c.font = Font(bold=True, size=16, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[1].height = 28
ws.merge_cells("A2:K2")
c = ws["A2"]; c.value = ("Sales Rep: Joseph Simon   |   Leads who replied positively to cold outreach — "
                         "who was followed up with and what their response was.   |   Report date: 2026-06-18")
c.font = Font(italic=True, size=10, color="404040"); c.fill = PatternFill("solid", fgColor=LIGHT)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws.row_dimensions[2].height = 20

hdr_row = 4
for j, h in enumerate(headers, start=1):
    cell = ws.cell(row=hdr_row, column=j, value=h)
    cell.font = Font(bold=True, color=WHITE, size=11)
    cell.fill = PatternFill("solid", fgColor=BLUE)
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell.border = border
ws.row_dimensions[hdr_row].height = 30

r = hdr_row + 1
for row in rows:
    vals = [row["firm"], row["contact"], row["email"], row["source"], row["date_recv"],
            row["date_appt"], row["date_signed"], row["status"], row["response"],
            row["followup"], row["acct_mgr"]]
    for j, v in enumerate(vals, start=1):
        cell = ws.cell(row=r, column=j, value=v)
        cell.border = border
        cell.alignment = Alignment(vertical="top", wrap_text=(j in (10,)))
        if j == 9:  # response
            fg, tc = resp_fill.get(v, (WHITE, "000000"))
            cell.fill = PatternFill("solid", fgColor=fg)
            cell.font = Font(bold=True, color=tc)
            cell.alignment = Alignment(horizontal="center", vertical="top")
    if r % 2 == 0:
        for j in range(1, 12):
            if j != 9:
                ws.cell(row=r, column=j).fill = PatternFill("solid", fgColor="F2F5FB")
    r += 1

widths = [26, 20, 34, 14, 13, 13, 12, 22, 16, 60, 20]
for j, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(j)].width = w
ws.freeze_panes = "A5"
ws.auto_filter.ref = f"A{hdr_row}:K{r-1}"

# ===== Sheet 2: Summary =====
ws2 = wb.create_sheet("Summary")
ws2.merge_cells("A1:E1")
c = ws2["A1"]; c.value = "Follow-Up Summary Dashboard"
c.font = Font(bold=True, size=16, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws2.row_dimensions[1].height = 28

total = len(rows)
from collections import Counter, defaultdict
resp_counts = Counter(r["response"] for r in rows)
src_counts = Counter(r["source"] for r in rows)

# response breakdown block
ws2["A3"] = "Response"; ws2["B3"] = "Count"; ws2["C3"] = "% of Leads"
for cc in ("A3", "B3", "C3"):
    ws2[cc].font = Font(bold=True, color=WHITE); ws2[cc].fill = PatternFill("solid", fgColor=BLUE)
    ws2[cc].alignment = Alignment(horizontal="center"); ws2[cc].border = border
order = ["Yes", "Maybe Later", "Ghosted", "No"]
rr = 4
for k in order:
    n = resp_counts.get(k, 0)
    ws2.cell(row=rr, column=1, value=k)
    fg, tc = resp_fill[k]
    ws2.cell(row=rr, column=1).fill = PatternFill("solid", fgColor=fg)
    ws2.cell(row=rr, column=1).font = Font(bold=True, color=tc)
    ws2.cell(row=rr, column=2, value=n)
    ws2.cell(row=rr, column=3, value=f"{n/total*100:.1f}%")
    for col in (1, 2, 3):
        ws2.cell(row=rr, column=col).border = border
        if col > 1:
            ws2.cell(row=rr, column=col).alignment = Alignment(horizontal="center")
    rr += 1
ws2.cell(row=rr, column=1, value="TOTAL").font = Font(bold=True)
ws2.cell(row=rr, column=2, value=total).font = Font(bold=True)
ws2.cell(row=rr, column=3, value="100.0%").font = Font(bold=True)
for col in (1, 2, 3):
    ws2.cell(row=rr, column=col).border = border
    ws2.cell(row=rr, column=col).fill = PatternFill("solid", fgColor=LIGHT)
    if col > 1:
        ws2.cell(row=rr, column=col).alignment = Alignment(horizontal="center")

# headline metrics
won = resp_counts.get("Yes", 0)
meetings_held = sum(1 for r in rows if "had meeting" in r["status"].lower() or "sold" in r["status"].lower()
                    or r["status"].lower() in ("cancelled",))
ws2["A" + str(rr+2)] = "Key Metrics"
ws2["A" + str(rr+2)].font = Font(bold=True, size=13, color=NAVY)
metrics = [
    ("Total positive-reply leads worked", total),
    ("Signed clients (Yes)", won),
    ("Win rate (Yes / total leads)", f"{won/total*100:.1f}%"),
    ("Still in play (Maybe Later)", resp_counts.get("Maybe Later", 0)),
    ("Declined (No)", resp_counts.get("No", 0)),
    ("Ghosted / went silent", resp_counts.get("Ghosted", 0)),
]
mr = rr + 3
for label, val in metrics:
    ws2.cell(row=mr, column=1, value=label).font = Font(size=11)
    ws2.cell(row=mr, column=2, value=val).font = Font(bold=True, size=11, color=BLUE)
    ws2.cell(row=mr, column=1).border = border
    ws2.cell(row=mr, column=2).border = border
    mr += 1

# source breakdown
sr = mr + 2
ws2.cell(row=sr, column=1, value="Lead Source").font = Font(bold=True, color=WHITE)
ws2.cell(row=sr, column=1).fill = PatternFill("solid", fgColor=BLUE)
ws2.cell(row=sr, column=2, value="Count").font = Font(bold=True, color=WHITE)
ws2.cell(row=sr, column=2).fill = PatternFill("solid", fgColor=BLUE)
ws2.cell(row=sr, column=2).alignment = Alignment(horizontal="center")
ws2.cell(row=sr, column=1).border = border; ws2.cell(row=sr, column=2).border = border
sr += 1
for k, n in src_counts.most_common():
    ws2.cell(row=sr, column=1, value=k or "(blank)")
    ws2.cell(row=sr, column=2, value=n).alignment = Alignment(horizontal="center")
    ws2.cell(row=sr, column=1).border = border; ws2.cell(row=sr, column=2).border = border
    sr += 1

ws2.column_dimensions["A"].width = 36
ws2.column_dimensions["B"].width = 14
ws2.column_dimensions["C"].width = 14

# ===== Sheet 3: Legend =====
ws3 = wb.create_sheet("Legend & Method")
ws3.merge_cells("A1:B1")
c = ws3["A1"]; c.value = "How responses were categorized"
c.font = Font(bold=True, size=14, color=WHITE); c.fill = PatternFill("solid", fgColor=NAVY)
c.alignment = Alignment(horizontal="left", vertical="center", indent=1)
ws3.row_dimensions[1].height = 26
legend = [
    ("Yes", "Lead signed / moved forward as a client (status: Sold - Won)."),
    ("Maybe Later", "Still in play — had a meeting and is considering, showed interest, has a meeting on the books, or is being actively followed up to schedule."),
    ("No", "Declined — not interested after contact, or signed then cancelled."),
    ("Ghosted", "Booked a meeting and did not show, then went unresponsive to rebooking attempts."),
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
ws3.cell(row=lr+1, column=1, value="Note:").font = Font(bold=True)
ws3.merge_cells(start_row=lr+1, start_column=2, end_row=lr+2, end_column=2)
ws3.cell(row=lr+1, column=2, value=("Follow-up outcomes were reconstructed from the status recorded for each lead. "
        "Where a specific account note existed it was preserved verbatim. Adjust any row directly if you "
        "remember a different outcome.")).alignment = Alignment(wrap_text=True, vertical="top")
ws3.column_dimensions["A"].width = 16
ws3.column_dimensions["B"].width = 80

wb.save(OUT)
print("Saved:", OUT)
print("Total leads:", total)
for k in order:
    print(f"  {k}: {resp_counts.get(k,0)}")
print("Sources:", dict(src_counts))
