#!/bin/sh
# Review of Jauho, Wingreen, Meir, PRB 50, 5528 (1994) with step cards.
# Downloads the arXiv TeX source (cond-mat/9404027, ~28 KB) into a copy of
# the workspace, then verifies, reports and packages it. Nothing is
# written to this directory.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${1:-/tmp/jwm1994-review}
rm -rf "$OUT" && cp -R "$HERE/workspace" "$OUT"
curl -sL https://arxiv.org/e-print/cond-mat/9404027 | gunzip -c > "$OUT/manuscript/source.tex"
[ "${MUTATE:-0}" = 1 ] && python3 "$HERE/mutate.py" "$OUT"
symbolic-compactification audit verify "$OUT" || test $? -eq 2
symbolic-compactification audit package "$OUT"
echo "open $OUT/reviewer-verification-package/REVIEWER_SUMMARY.html"
