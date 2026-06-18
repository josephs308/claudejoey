#!/usr/bin/env python3
"""Generate GHL-import-ready re-engagement audience (the 211 unsettled leads)."""
import csv, datetime as dt
from collections import Counter

SRC = "/root/.claude/uploads/5e6ae773-2219-57fa-8944-6278c6fa25ad/56edd10a-Joseph_Simon_MBP_Sales_Report__Lead_Client_Data.csv"
OUT = "/home/user/claudejoey/MBP_ReEngagement_Audience.csv"
TODAY = dt.date(2026, 6, 18)

rows = []
for r in list(csv.reader(open(SRC, newline="")))[3:]:
    if len(r) < 12:
        continue
    d = dict(firm=r[1].strip(), contact=r[3].strip(), date_recv=r[7].strip(),
             date_appt=r[8].strip(), date_signed=r[9].strip(),
             status=r[10].strip(), email=r[11].strip())
    if (d["email"] or d["firm"]) and d["status"]:
        rows.append(d)

def pd(s):
    for f in ("%m/%d/%Y", "%m/%d/%y"):
        try: return dt.datetime.strptime(s, f).date()
        except ValueError: pass
    return None

def last_touch(row):
    ds = [pd(row[k]) for k in ("date_signed", "date_appt", "date_recv")]
    ds = [x for x in ds if x]
    return max(ds) if ds else None

def age(row):
    d = last_touch(row)
    return (TODAY - d).days if d else 9999

WARM_MEET, WARM_INT = 255, 225

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
    if "sold" in s or "won" in s: return "Yes"
    if "cancel" in s: return "No"
    if "not interested" in s: return "No"
    if "no show" in s: return "Ghosted"
    if "meeting scheduled" in s: return "Maybe Later"
    if "had meeting - interested" in s: return "Maybe Later"
    a = age(row)
    if "had meeting" in s: return "Maybe Later" if a <= WARM_MEET else "Ghosted"
    if "interested" in s: return "Maybe Later" if a <= WARM_INT else "Ghosted"
    return "Maybe Later"

def segment(row, resp):
    s = row["status"].lower()
    if resp == "Maybe Later":
        if "meeting scheduled" in s or "had meeting" in s:
            return "reengage-hot"
        return "reengage-warm"
    if resp == "Ghosted":
        return "reengage-dormant"
    return None  # exclude Yes / No

out_rows = []
for row in rows:
    resp = classify(row)
    seg = segment(row, resp)
    if not seg or not row["email"]:
        continue
    lt = last_touch(row)
    out_rows.append({
        "Name": row["contact"] or row["firm"],
        "Email": row["email"],
        "Business Name": row["firm"],
        "Tag": seg,
        "Prior Status": row["status"],
        "Last Activity": lt.strftime("%-m/%-d/%Y") if lt else "",
    })

# stable sort: hot, warm, dormant
order = {"reengage-hot": 0, "reengage-warm": 1, "reengage-dormant": 2}
out_rows.sort(key=lambda r: order[r["Tag"]])

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["Name", "Email", "Business Name", "Tag", "Prior Status", "Last Activity"])
    w.writeheader()
    w.writerows(out_rows)

print("Saved", OUT, "rows:", len(out_rows))
print(Counter(r["Tag"] for r in out_rows))
