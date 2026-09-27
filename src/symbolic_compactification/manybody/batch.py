"""Run a directory of step cards: one table, cross-card conventions, HTML.

    symbolic-compactification manybody steps cards/ --require-source --html report.html

Cards that quote the same source document must use the same conventions:
a notation token, a definition or a symbol's sign assumption that means
different things in two cards is reported as a convention warning (the
e_nm = e_n - e_m versus e_m - e_n kind of slip). Warnings do not change a
card's decision; a conflict *inside* one card (against its include file)
does, see cards.resolve_includes.
"""
from __future__ import annotations

import html
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

import yaml

from .cards import CardError, load_card, resolve_includes, run_card


def collect_cards(paths: Iterable[str | Path]) -> list[Path]:
    out: list[Path] = []
    for item in paths:
        path = Path(item)
        if path.is_dir():
            out += sorted(p for p in path.glob("*.yaml")
                          if not p.name.startswith("_") and p.name != "conventions.yaml")
        else:
            out.append(path)
    return out


def _conventions(card: dict) -> dict[str, str]:
    table = {f"notation {k}": " ".join(str(v).split()) for k, v in (card.get("notation") or {}).items()}
    for k, v in (card.get("define") or {}).items():
        table[f"define {str(k).split('(')[0].strip()}"] = " ".join(str(v).split())
    for s in card.get("symbols") or []:
        if isinstance(s, dict):
            table[f"symbol {s['name']}"] = "positive" if s.get("positive") else "real/complex"
    return table


def convention_warnings(cards: list[Path]) -> list[dict[str, Any]]:
    seen: dict[tuple[str, str], dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for path in cards:
        try:
            card, _ = resolve_includes(load_card(path), path.resolve().parent)
        except (CardError, OSError, yaml.YAMLError):
            continue
        doc = str(card.get("source_document") or "")
        for key, value in _conventions(card).items():
            seen[(doc, key)][value].append(path.stem)
    warnings = []
    for (doc, key), values in sorted(seen.items()):
        if len(values) > 1:
            warnings.append({"source_document": doc, "convention": key,
                             "values": {v: sorted(c) for v, c in values.items()}})
    return warnings


def run_cards(paths: Iterable[str | Path], *, require_source: bool | None = None) -> dict[str, Any]:
    cards = collect_cards(paths)
    rows = []
    for path in cards:
        try:
            result = run_card(path, require_source=require_source)
        except (CardError, OSError, ValueError, yaml.YAMLError) as exc:
            result = {"decision": "NOT_DECIDED", "decision_blocked_by": [f"CARD_ERROR:{str(exc)[:200]}"]}
        rows.append({"card": path.stem, "path": str(path), **result})
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["decision"]] += 1
    return {"cards": rows, "counts": dict(counts),
            "convention_warnings": convention_warnings(cards)}


_CSS = """
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#6b6a64;--line:#dedbd2;--valid:#1f7a4a;
--invalid:#b3261e;--open:#a15c00;--card:#fff}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ecebe6;
--muted:#a3a29b;--line:#34343a;--valid:#5cc68d;--invalid:#ff8a80;--open:#f0b45a;--card:#202024}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ecebe6;--muted:#a3a29b;--line:#34343a;
--valid:#5cc68d;--invalid:#ff8a80;--open:#f0b45a;--card:#202024}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px}
h1{font-size:22px;margin:0 0 4px}p.sub{color:var(--muted);margin:0 0 20px}
.counts{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px}
.counts div{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 14px}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;background:var(--card)}
th,td{border-bottom:1px solid var(--line);padding:8px;text-align:left;vertical-align:top}
th{font-size:13px;color:var(--muted);font-weight:600}
code{font:13px/1.4 ui-monospace,monospace;white-space:pre-wrap;word-break:break-word}
.VALID{color:var(--valid);font-weight:700}.INVALID{color:var(--invalid);font-weight:700}
.NOT_DECIDED{color:var(--open);font-weight:700}
"""


def _cell(value: Any) -> str:
    if value in (None, "", [], {}):
        return ""
    return f"<code>{html.escape(str(value))}</code>"


def to_html(report: dict[str, Any], title: str = "Step-card report") -> str:
    rows = []
    for r in report["cards"]:
        tr = r.get("transcription") or {}
        claim_quote = next((f.get("quote") for k, f in (tr.get("fields") or {}).items()
                            if k in ("claim", "rhs")), None)
        rows.append(
            "<tr>"
            f"<td>{html.escape(r['card'])}</td>"
            f"<td>{html.escape(str(r.get('check', '')))}</td>"
            f"<td class=\"{html.escape(r['decision'])}\">{html.escape(r['decision'])}</td>"
            f"<td>{html.escape(str(r.get('status') or r.get('verdict') or ''))}</td>"
            f"<td>{html.escape(str(tr.get('status', '')))}</td>"
            f"<td>{_cell(claim_quote)}</td>"
            f"<td>{_cell(r.get('decision_blocked_by'))}{_cell(r.get('diagnosis'))}"
            f"{_cell((r.get('counterexample') or {}).get('point'))}</td>"
            "</tr>")
    counts = "".join(f"<div><b>{n}</b> {html.escape(k)}</div>"
                     for k, n in sorted(report["counts"].items()))
    warn = "".join(
        f"<li><code>{html.escape(w['convention'])}</code> in {html.escape(Path(w['source_document']).name or 'no document')}: "
        + "; ".join(f"<code>{html.escape(v)}</code> ({html.escape(', '.join(c))})" for v, c in w["values"].items())
        + "</li>" for w in report["convention_warnings"])
    warn_block = f"<h2>Convention warnings</h2><ul>{warn}</ul>" if warn else ""
    return (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{html.escape(title)}</title><style>{_CSS}</style></head><body><main>"
            f"<h1>{html.escape(title)}</h1><p class=\"sub\">Decision is VALID or INVALID only when "
            f"the checker decided and the card matches its quoted source.</p>"
            f"<div class=\"counts\">{counts}</div>{warn_block}<div class=\"wrap\"><table>"
            "<tr><th>Card</th><th>Check</th><th>Decision</th><th>Checker</th><th>Transcription</th>"
            "<th>Quoted claim</th><th>Notes</th></tr>"
            + "".join(rows) + "</table></div></main></body></html>")
