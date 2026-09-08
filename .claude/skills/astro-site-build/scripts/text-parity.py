#!/usr/bin/env python3
"""Compare visible text between an old build and a new one, page by page.

    python3 text-parity.py old_dir new_dir

Use when porting existing pages to a framework. Matching word counts with
zero missing words is the evidence that a migration moved the content
rather than quietly dropping some of it -- which is easy to do when the
old markup mixes content with nav, footer and trailing markup.
"""
import pathlib
import re
import sys


def visible(html: str) -> str:
    s = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", html, flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    for a, b in [("&amp;", "&"), ("&nbsp;", " "), ("&mdash;", "—"), ("&quot;", '"'),
                 ("&#39;", "'"), ("&lt;", "<"), ("&gt;", ">"), ("&times;", "×")]:
        s = s.replace(a, b)
    return " ".join(s.split())


old_dir, new_dir = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
bad = 0

for old in sorted(old_dir.glob("*.html")):
    new = new_dir / old.name
    if not new.exists():
        print(f"{old.name:<26} MISSING in {new_dir}")
        bad += 1
        continue
    ow = visible(old.read_text(encoding="utf-8", errors="replace")).split()
    nw = visible(new.read_text(encoding="utf-8", errors="replace")).split()
    missing = {w for w in ow if w not in set(nw)}
    flag = "" if not missing else "  <-- CONTENT LOST"
    if missing:
        bad += 1
    print(f"{old.name:<26} old {len(ow):>5}w  new {len(nw):>5}w  "
          f"delta {len(nw) - len(ow):+5}  missing {len(missing)}{flag}")
    if missing:
        print("    e.g. " + " ".join(list(missing)[:12]))

sys.exit(1 if bad else 0)
