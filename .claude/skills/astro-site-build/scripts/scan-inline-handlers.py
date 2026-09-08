#!/usr/bin/env python3
"""Fail if any inline event handler survives in the built output.

    python3 scan-inline-handlers.py dist

Every HTML attribute beginning with "on" is an event handler, so scan
generically -- a hand-written list will miss onerror, onkeydown, onfocus,
and whatever the next page uses. Each one forces 'unsafe-inline' into
script-src, which is the directive worth keeping strict.
"""
import collections
import pathlib
import re
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
found = collections.Counter()
where: dict[str, set[str]] = collections.defaultdict(set)

for f in root.rglob("*.html"):
    text = f.read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"\s(on[a-z]+)\s*=\s*[\"']", text):
        found[m.group(1)] += 1
        where[m.group(1)].add(f.name)

if not found:
    print(f"clean: no inline event handlers in {root}")
    sys.exit(0)

print(f"{sum(found.values())} inline handler(s) in {root}:")
for name, n in found.most_common():
    print(f"  {name:<14} {n:>3}   {', '.join(sorted(where[name])[:4])}")
print("\nEach of these forces 'unsafe-inline' in script-src.")
sys.exit(1)
