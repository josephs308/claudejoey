#!/usr/bin/env python3
"""Build a presentable Pipeline Status & Action Plan workbook for Joseph / MBP."""
import csv
import datetime as dt
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SRC = "/root/.claude/uploads/5e6ae773-2219-57fa-8944-6278c6fa25ad/56edd10a-Joseph_Simon_MBP_Sales_Report__Lead_Client_Data.csv"
OUT = "/home/user/claudejoey/MBP_Pipeline_Action_Plan.xlsx"
TODAY = dt.date(2026, 6, 18)

rows = []
for r in list(csv.reader(open(SRC, newline="")))[3:]:
    if len(r) < 12:
        continue
    d = dict(firm=r[1].strip(), source=r[2].strip(), contact=r[3].strip(),
             date_recv=r[7].strip(), date_appt=r[8].strip(), date_signed=r[9].strip(),
             status=r[10].strip(), email=r[11].strip())
    if (d["email"] or d["firm"]) and d["status"]:
        rows.append(d)

def parse_date(s):
    for f in ("%m/%d/%Y", "%m/%d/%y"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    return None

def last_touch(row):
    ds = [parse_date(row[k]) for k in ("date_signed", "date_appt", "date_recv")]
    ds = [x for x in ds if x]
    return max(ds) if ds else None

def age_days(row):
    d = last_touch(row)
    return (TODAY - d).days if d else 9999

WARM_MEET, WARM_INT = 255, 225

def classify(row):
    s = row["status"].lower()
    if "sold" in s or "won" in s: return "Yes"
    if "cancel" in s: return "No"
    if "not interested" in s: return "No"
    if "no show" in s: return "Ghosted"
    if "meeting scheduled" in s: return "Maybe Later"
    if "had meeting - interested" in s: return "Maybe Later"
    a = age_days(row)
    if "had meeting" in s: return "Maybe Later" if a <= WARM_MEET else "Ghosted"
    if "interested" in s: return "Maybe Later" if a <= WARM_INT else "Ghosted"
    return "Maybe Later"

def tier(row, resp):
    s = row["status"].lower()
    if resp == "Maybe Later":
        if "meeting scheduled" in s:
            return 1, "Confirm the booked meeting; prep to close"
        if "had meeting" in s:
            return 1, "Send recap + proposal; follow up to close"
        return 2, "Call/email to lock in the meeting they requested"
    if resp == "Ghosted":
        return 3, "Send re-engagement / breakup email — final attempt"
    return None, None

for row in rows:
    row["resp"] = classify(row)
    row["tier"], row["next"] = tier(row, row["resp"])

resp_counts = Counter(r["resp"] for r in rows)
total = len(rows)
t1 = [r for r in rows if r["tier"] == 1]
t2 = [r for r in rows if r["tier"] == 2]
t3 = [r for r in rows if r["tier"] == 3]

# ---- styling ----
NAVY="1F3864"; BLUE="2E5496"; LIGHT="D9E1F2"; WHITE="FFFFFF"
GREEN="C6EFCE"; GREEN_T="006100"; RED="FFC7CE"; RED_T="9C0006"
AMBER="FFEB9C"; AMBER_T="9C6500"; GREY="D9D9D9"; GREY_T="3F3F3F"
ORANGE="F8CBAD"; ORANGE_T="833C00"
resp_fill={"Yes":(GREEN,GREEN_T),"No":(RED,RED_T),"Maybe Later":(AMBER,AMBER_T),"Ghosted":(GREY,GREY_T)}
tier_fill={1:(GREEN,GREEN_T),2:(AMBER,AMBER_T),3:(ORANGE,ORANGE_T)}
thin=Side(style="thin",color="BFBFBF")
border=Border(left=thin,right=thin,top=thin,bottom=thin)

wb=Workbook()

# ================= Tab 1: Action Plan =================
ws=wb.active; ws.title="Action Plan"
ws.column_dimensions["A"].width=3
ws.column_dimensions["B"].width=52
ws.column_dimensions["C"].width=14
ws.column_dimensions["D"].width=46

def title(cell, text, size=16, fill=NAVY, color=WHITE):
    ws[cell]=text; ws[cell].font=Font(bold=True,size=size,color=color)
    ws[cell].fill=PatternFill("solid",fgColor=fill)
    ws[cell].alignment=Alignment(horizontal="left",vertical="center",indent=1)

ws.merge_cells("B1:D1"); title("B1","MBP — Cold Email Pipeline: Status & Action Plan")
ws.row_dimensions[1].height=30
ws.merge_cells("B2:D2")
ws["B2"]="Prepared by Joseph Simon  ·  "+TODAY.strftime("%B %d, %Y")+"  ·  295 positive-reply leads worked"
ws["B2"].font=Font(italic=True,size=10,color="404040")
ws["B2"].fill=PatternFill("solid",fgColor=LIGHT)
ws["B2"].alignment=Alignment(horizontal="left",indent=1)

# Section: where we are
r=4
ws.merge_cells(f"B{r}:D{r}"); title(f"B{r}","1.  Where the pipeline stands today",13,BLUE)
r+=1
snapshot=[("Signed clients (Yes)",resp_counts["Yes"],resp_fill["Yes"]),
          ("Active / still in play (Maybe Later)",resp_counts["Maybe Later"],resp_fill["Maybe Later"]),
          ("Went quiet after follow-up (Ghosted)",resp_counts["Ghosted"],resp_fill["Ghosted"]),
          ("Declined / not a fit (No)",resp_counts["No"],resp_fill["No"])]
for label,n,(fg,tc) in snapshot:
    ws.cell(row=r,column=2,value=label).border=border
    cell=ws.cell(row=r,column=3,value=f"{n}  ({n/total*100:.0f}%)")
    cell.fill=PatternFill("solid",fgColor=fg); cell.font=Font(bold=True,color=tc)
    cell.alignment=Alignment(horizontal="center"); cell.border=border
    r+=1

# Section: the gap (honest)
r+=1
ws.merge_cells(f"B{r}:D{r}"); title(f"B{r}","2.  The gap",13,BLUE); r+=1
for line in ["Outcomes for signed, declined and no-show leads are recorded and accurate.",
             "Early-stage follow-up was tracked informally (manual + CRM), so some interested",
             "leads don't have a final outcome logged in one place yet.",
             "Fix: consolidate every lead into the CRM as the single source of truth (below)."]:
    ws.cell(row=r,column=2,value="•  "+line); ws.merge_cells(f"B{r}:D{r}"); r+=1

# Section: the opportunity
r+=1
ws.merge_cells(f"B{r}:D{r}"); title(f"B{r}","3.  The opportunity — recoverable pipeline",13,BLUE); r+=1
opp=[(f"{len(t1)}","Hot — had a meeting / booked, no decision yet. Closest to signing."),
     (f"{len(t2)}","Warm — asked for a meeting, never scheduled. Book the call."),
     (f"{len(t3)}","Dormant — went quiet; worth one structured re-engagement attempt.")]
for n,desc in opp:
    cell=ws.cell(row=r,column=2,value=n+" leads"); cell.font=Font(bold=True); cell.border=border
    ws.cell(row=r,column=3,value="");
    dcell=ws.cell(row=r,column=4,value=desc); dcell.alignment=Alignment(wrap_text=True,vertical="center")
    dcell.border=border; ws.cell(row=r,column=3).border=border
    ws.row_dimensions[r].height=30; r+=1
ws.cell(row=r,column=2,value=f"{len(t1)+len(t2)} warm leads are immediately actionable (see 'Re-Engagement List' tab).").font=Font(bold=True,color=NAVY)
ws.merge_cells(f"B{r}:D{r}"); r+=2

# Section: action plan
ws.merge_cells(f"B{r}:D{r}"); title(f"B{r}","4.  Action plan",13,BLUE); r+=1
ws.cell(row=r,column=2,value="Step").font=Font(bold=True,color=WHITE)
ws.cell(row=r,column=3,value="When").font=Font(bold=True,color=WHITE)
ws.cell(row=r,column=4,value="What").font=Font(bold=True,color=WHITE)
for col in (2,3,4):
    ws.cell(row=r,column=col).fill=PatternFill("solid",fgColor=BLUE); ws.cell(row=r,column=col).border=border
r+=1
plan=[("Reconcile in CRM","Today","Pull CRM export, match every lead, lock in true stage/last activity."),
      ("Work the hot list","This week",f"Call/recap the {len(t1)} hot + {len(t2)} warm leads to close or book."),
      ("Re-engagement campaign","Next 2 weeks",f"Run one structured sequence at the {len(t3)} dormant leads."),
      ("Lock tracking","Ongoing","Update CRM stage on every touch; weekly pipeline report from it.")]
for step,when,what in plan:
    ws.cell(row=r,column=2,value=step).font=Font(bold=True)
    ws.cell(row=r,column=3,value=when)
    wc=ws.cell(row=r,column=4,value=what); wc.alignment=Alignment(wrap_text=True,vertical="center")
    for col in (2,3,4): ws.cell(row=r,column=col).border=border
    ws.row_dimensions[r].height=30; r+=1

# Section: going forward
r+=1
ws.merge_cells(f"B{r}:D{r}"); title(f"B{r}","5.  So this never happens again",13,BLUE); r+=1
for line in ["One source of truth: CRM pipeline stage = the lead's status. No side spreadsheets.",
             "Every contact logged at the moment it happens (call, email, meeting).",
             "Weekly auto-report: Yes / Maybe Later / Ghosted / No, straight from the CRM."]:
    ws.cell(row=r,column=2,value="•  "+line); ws.merge_cells(f"B{r}:D{r}"); r+=1

ws.sheet_view.showGridLines=False

# ================= Tab 2: Re-Engagement List =================
ws2=wb.create_sheet("Re-Engagement List")
heads=["Priority","Firm / Business","Contact","Email","Current Status","Last Touch","Days Quiet","Recommended Next Step"]
ws2.merge_cells("A1:H1")
ws2["A1"]="This-Week & Reactivation List — leads worth a touch (excludes signed & declined)"
ws2["A1"].font=Font(bold=True,size=13,color=WHITE); ws2["A1"].fill=PatternFill("solid",fgColor=NAVY)
ws2["A1"].alignment=Alignment(horizontal="left",vertical="center",indent=1)
ws2.row_dimensions[1].height=26
for j,h in enumerate(heads,start=1):
    c=ws2.cell(row=3,column=j,value=h); c.font=Font(bold=True,color=WHITE,size=11)
    c.fill=PatternFill("solid",fgColor=BLUE); c.border=border
    c.alignment=Alignment(horizontal="center",vertical="center",wrap_text=True)
ws2.row_dimensions[3].height=28
tier_label={1:"1 · Hot",2:"2 · Warm",3:"3 · Dormant"}
actionable=sorted([r for r in rows if r["tier"]],key=lambda r:(r["tier"],r["resp"]!="Maybe Later",age_days(r)))
rr=4
for row in actionable:
    lt=last_touch(row)
    vals=[tier_label[row["tier"]],row["firm"],row["contact"],row["email"],row["status"],
          lt.strftime("%-m/%-d/%Y") if lt else "",age_days(row) if lt else "",row["next"]]
    for j,v in enumerate(vals,start=1):
        c=ws2.cell(row=rr,column=j,value=v); c.border=border
        c.alignment=Alignment(vertical="center",wrap_text=(j==8))
        if j==1:
            fg,tc=tier_fill[row["tier"]]; c.fill=PatternFill("solid",fgColor=fg)
            c.font=Font(bold=True,color=tc); c.alignment=Alignment(horizontal="center",vertical="center")
    rr+=1
for j,w in enumerate([11,30,18,32,22,12,10,44],start=1):
    ws2.column_dimensions[get_column_letter(j)].width=w
ws2.freeze_panes="A4"
ws2.auto_filter.ref=f"A3:H{rr-1}"

wb.save(OUT)
print("Saved",OUT)
print("Hot(T1):",len(t1)," Warm(T2):",len(t2)," Dormant(T3):",len(t3)," Actionable total:",len(t1)+len(t2)+len(t3))
print("Snapshot:",dict(resp_counts))
