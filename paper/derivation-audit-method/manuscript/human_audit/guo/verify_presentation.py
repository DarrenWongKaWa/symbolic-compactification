#!/usr/bin/env python3
"""Check that the human-facing ledger is a projection, not a certificate.

No API. No engine. Compares hashes and required copy.
"""
from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FORBIDDEN = [
    "full derivation verified",
    "189 equations verified",
    "five papers fully verified",
    "the derivation holds",
]
REQUIRED = [
    "Presentation is not a certificate",
    "inventoried equations",
    "extracted relations",
    "executable obligations",
    "none of the submitted executable relations",
    "does not mean the paper has no incorrect steps",
    "Eq. (D-117) → Eq. (5)",
]


def main() -> int:
    data = HERE / "report-data.json"
    html = HERE / "index.html"
    rec = HERE / "PRESENTATION_SHA256.txt"
    digest = hashlib.sha256(data.read_bytes()).hexdigest()
    recorded = rec.read_text()
    page = html.read_text()
    visible = re.sub(
        r'<script type="application/json"[^>]*>.*?</script>',
        "",
        page,
        flags=re.S | re.I,
    )
    errors: list[str] = []
    if digest not in recorded:
        errors.append(f"PRESENTATION_SHA256.txt missing {digest}")
    m = re.search(r'data-sha256="([0-9a-f]{64})"', page)
    if not m or m.group(1) != digest:
        errors.append("index.html data-sha256 does not match report-data.json")
    if page.count("<tr class=") != 146:
        errors.append(f"expected 146 ledger rows, got {page.count('<tr class=')}")
    if 'id="rel-R007"' not in page:
        errors.append("missing flagship residual card id rel-R007")
    low = visible.lower()
    for phrase in FORBIDDEN:
        if phrase in low:
            errors.append(f"forbidden copy: {phrase}")
    for phrase in REQUIRED:
        if phrase not in page:
            errors.append(f"missing required copy: {phrase}")
    # no-JS floor: strip scripts; ledger and card must remain
    noscript = re.sub(r"<script\b[^>]*>.*?</script>", "", page, flags=re.S | re.I)
    if noscript.count("<tr class=") != 146:
        errors.append("no-JS table lost rows")
    if "R_{\\mathrm{direct}}" not in noscript and r"R_{\mathrm{direct}}" not in noscript:
        errors.append("no-JS flagship residual missing")
    if errors:
        print("VERIFY_FAIL")
        for e in errors:
            print(" -", e)
        return 1
    print("VERIFY_OK")
    print("report-data.json", digest)
    print("presentation is not certificate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
