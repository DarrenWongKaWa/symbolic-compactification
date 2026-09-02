#!/usr/bin/env python3
"""Assemble the Guo evidence-ledger HTML from the frozen view model.

Does not adjudicate mathematics. Statuses are copied from report-data.json,
which was projected from v0.3.0-alpha RESULTS.md.

Writes:
  ledger-rows.html  (fragment)
  injects tbody + inlined JSON into index.html between markers
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

BEGIN_ROWS = "<!-- BEGIN_LEDGER_ROWS -->"
END_ROWS = "<!-- END_LEDGER_ROWS -->"
BEGIN_DATA = "<!-- BEGIN_AUDIT_DATA -->"
END_DATA = "<!-- END_AUDIT_DATA -->"
BEGIN_CSS = "<!-- BEGIN_INLINE_CSS -->"
END_CSS = "<!-- END_INLINE_CSS -->"
BEGIN_JS = "<!-- BEGIN_INLINE_JS -->"
END_JS = "<!-- END_INLINE_JS -->"


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def math_cell(tex: str | None) -> str:
    if not tex:
        return ""
    t = tex.strip()
    if t.startswith("$") and t.endswith("$") and t.count("$") == 2:
        t = t[1:-1]
    return f"\\({html.escape(t)}\\)"


def who(rel: dict) -> str:
    cond = rel.get("condition") or {}
    if cond.get("who_certifies"):
        return str(cond["who_certifies"])
    kind = str(cond.get("kind") or "")
    if kind == "source-grounded substitution":
        return "SOURCE"
    if kind == "author-declared remainder":
        return "SOURCE"
    if "rule" in kind or "domain" in kind:
        return "DOMAIN"
    if not kind or kind == "none":
        return ""
    if "auditor" in kind.lower():
        return "AUDITOR"
    return "UPSTREAM"


def row(rel: dict) -> str:
    st = rel.get("final_status") or ""
    hay = " ".join(
        [
            rel.get("public_display") or "",
            rel.get("author_move") or "",
            st,
            rel.get("math_summary_tex") or "",
            (rel.get("condition") or {}).get("tex") or "",
            (rel.get("direct") or {}).get("residual_tex") or "",
            who(rel),
        ]
    ).lower()
    cond = rel.get("condition") or {}
    cond_tex = cond.get("tex") or cond.get("text") or ""
    return (
        f'<tr class="{html.escape(st)}" id="row-{html.escape(rel.get("id") or "")}" data-status="{html.escape(st)}" '
        f'data-section="{html.escape(rel.get("section") or "")}" '
        f'data-hay="{esc(hay)}">'
        f'<td><a href="#rel-{html.escape(rel.get("id") or "")}">'
        f'{html.escape(rel.get("public_display") or "")}</a></td>'
        f"<td>{math_cell(rel.get('math_summary_tex'))}</td>"
        f"<td>{html.escape(rel.get('author_move') or '')}</td>"
        f"<td>{math_cell(cond_tex) if cond_tex and cond_tex != 'none' else '—'}</td>"
        f'<td><span class="badge {html.escape(st)}">{html.escape(st)}</span></td>'
        "</tr>"
    )


def replace_block(text: str, begin: str, end: str, inner: str) -> str:
    i = text.index(begin)
    j = text.index(end, i)
    return text[: i + len(begin)] + "\n" + inner + "\n" + text[j:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "report-data.json"))
    ap.add_argument("--src", default=str(HERE / "index.src.html"))
    ap.add_argument("--html", default=str(HERE / "index.html"))
    args = ap.parse_args()
    data_path = Path(args.data)
    src_path = Path(args.src)
    html_path = Path(args.html)
    payload = json.loads(data_path.read_text())
    rows = "\n".join(row(r) for r in payload["relations"])
    digest = hashlib.sha256(data_path.read_bytes()).hexdigest()
    data_tag = (
        f'<script type="application/json" id="audit-data" '
        f'data-sha256="{digest}">\n'
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + "\n</script>"
    )
    css = (HERE / "report.css").read_text()
    js = (HERE / "report.js").read_text()
    text = src_path.read_text()
    text = replace_block(text, BEGIN_ROWS, END_ROWS, rows)
    text = replace_block(text, BEGIN_DATA, END_DATA, data_tag)
    text = replace_block(text, BEGIN_CSS, END_CSS, "<style>\n" + css + "\n</style>")
    text = replace_block(text, BEGIN_JS, END_JS, "<script>\n" + js + "\n</script>")
    html_path.write_text(text)
    (HERE / "PRESENTATION_SHA256.txt").write_text(
        f"report-data.json sha256 {digest}\n"
        f"relations {len(payload['relations'])}\n"
        "presentation is not certificate\n"
    )
    print("wrote", html_path)
    print("relations", len(payload["relations"]))
    print("report-data.json sha256", digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
