#!/usr/bin/env bash
# Make a single-file preview of a built page that loads its CSS, images and
# links from a live or deploy-preview domain, so it can be opened anywhere
# (phone, chat attachment) without running a server.
#
# Usage: make_preview.sh PAGE.html https://example.com OUT.html
#
# Note: assets that exist only locally (not yet deployed) will not load from the
# domain. If the page's CSS changed and isn't deployed yet, inline it first or
# point the base at the host's deploy-preview URL for the branch.
set -euo pipefail
page="$1"; base="${2%/}/"; out="$3"
# put <base> first inside <head> so relative URLs resolve and the doctype stays first
python3 - "$page" "$base" "$out" <<'PY'
import re, sys
page, base, out = sys.argv[1:4]
s = open(page, encoding='utf-8').read()
tag = f'<base href="{base}">'
s, n = re.subn(r'(<head(?:\s[^>]*)?>)', r'\1' + tag, s, count=1, flags=re.I)
if not n: s = tag + s
open(out, 'w', encoding='utf-8').write(s)
PY
echo "wrote $out (base $base)"
