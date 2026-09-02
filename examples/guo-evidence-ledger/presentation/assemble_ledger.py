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
import re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

BEGIN_ROWS = "<!-- BEGIN_LEDGER_ROWS -->"
END_ROWS = "<!-- END_LEDGER_ROWS -->"
BEGIN_CORR = "<!-- BEGIN_MAIN_CORR -->"
END_CORR = "<!-- END_MAIN_CORR -->"
BEGIN_SEQ = "<!-- BEGIN_EQ_SEQ -->"
END_SEQ = "<!-- END_EQ_SEQ -->"
BEGIN_MUST = "<!-- BEGIN_MUST_REVIEW -->"
END_MUST = "<!-- END_MUST_REVIEW -->"
BEGIN_ENCODE = "<!-- BEGIN_ENCODE_GAP -->"
END_ENCODE = "<!-- END_ENCODE_GAP -->"
BEGIN_DATA = "<!-- BEGIN_AUDIT_DATA -->"
END_DATA = "<!-- END_AUDIT_DATA -->"
BEGIN_CSS = "<!-- BEGIN_INLINE_CSS -->"
END_CSS = "<!-- END_INLINE_CSS -->"
BEGIN_JS = "<!-- BEGIN_INLINE_JS -->"
END_JS = "<!-- END_INLINE_JS -->"


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _dollars_to_paren(t: str) -> str:
    parts: list[str] = []
    i = 0
    n = len(t)
    while i < n:
        a = t.find("$", i)
        if a < 0:
            parts.append(html.escape(t[i:]))
            break
        if a > i:
            parts.append(html.escape(t[i:a]))
        b = t.find("$", a + 1)
        if b < 0:
            parts.append(html.escape(t[a:]))
            break
        inner = t[a + 1 : b].strip()
        if inner:
            parts.append("\\(" + html.escape(inner) + "\\)")
        i = b + 1
    return "".join(parts)


def _looks_like_tex(t: str) -> bool:
    if re.search(r"\\[A-Za-z]", t):
        return True
    if re.search(r"[_^]\{", t):
        return True
    if re.search(r"f_n'|\\epsilon|\\Omega|\\Gamma", t):
        return True
    if re.match(r"^O\([^)]+\)$", t):
        return True
    return False


def math_cell(tex: str | None) -> str:
    """MathJax \\(...\\) for formulas. Do not wrap English as TeX."""
    if not tex:
        return ""
    t = tex.strip()
    if t in {"none", "N/A", "—", "-"}:
        return html.escape(t)
    if "$" in t:
        return _dollars_to_paren(t)
    if re.search(r"\b(periodic|Leibniz|author-declared)\b", t, re.I) and not _looks_like_tex(t):
        return html.escape(t)
    if _looks_like_tex(t):
        return "\\(" + html.escape(t) + "\\)"
    return html.escape(t)


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


# Presentation overlay only. Not a RESULTS status.
# encoding_gap = local algebra not compiled (class B). Not a pass.
# needs_judgment = remainder / limit / special function / cancel / named
# identity. Fail closed: unmarked orange → needs_judgment.
# claimed move "definition" is out of engine (class A), never encoding_gap.
# must_review (class C) is a separate unsigned human queue, not the 30.
_NEEDS_JUDGMENT_CLAIMED = {
    "ASYMPTOTIC_CLAIM",
    "LIMIT_CLAIM",
    "SPECIAL_FUNCTION_IDENTITY",
    "INTEGRAL_ARGUMENT",
    "GLOBAL_SYMMETRY_PAIRING",
}
_NEEDS_JUDGMENT_MARKS = (
    "approximat",
    "vanishes identically",
    "mathcal{m}",
    "feynman",
    "hellmann",
    "equation of motion",
    "convolution",
    "residue",
    "cauchy",
    "geometric contributions cancel",
    "commutator",
    "quantum metric",
    "band-renormalized",
    "purely intraband",
)
_ENCODING_GAP_CLAIMED = {
    "ALGEBRAIC_EQUIVALENCE",
    "INDEX_RELABELING",
}
MUST_REVIEW_IDS = {"R050", "R066", "R110", "R132"}
ENCODE_LATER_IDS = ("R046", "R096", "R093", "R072")

# Hover copy. Frozen status names stay in comments / data-status only.
TIPS = {
    "0": "Machine checked left\u2212right = 0. Local residual only, not a paper pass.",
    "0 if A": "Machine checked 0 after the substitution in column A?. Does not prove A.",
    "cite": "Author invoked a named rule. Local identity + declared rule, not a CAS integral.",
    "def": "Definition or bookkeeping. No equality to check.",
    "sign": "Claimed cancel or vanishing. You must decide if that claim holds.",
    "remainder": "Finite terms do not prove the O(\u00b7) or the limit.",
    "look": "Not compiled. Special function, named identity, or similar. Do not treat as algebra 0.",
    "gap": "Local algebra was not in the frozen table. Not a pass.",
    "\u22600": "Submitted residual is not 0.",
    "Sign": "Record that you accept this cancel. Does not change frozen RESULTS.",
    "Signed": "Local sign-off. Click again to undo. Parent stays orange.",
}


def chip_span(kind: str, word: str) -> str:
    tip = html.escape(TIPS[word])
    return (
        f'<span class="chip {html.escape(kind)}" title="{tip}" data-tip="{tip}">'
        f"{html.escape(word)}</span>"
    )


def you_cell(rel: dict) -> str:
    _hue, you = hue_you(rel)
    if you != "sign":
        return html.escape(you)
    rid = rel.get("id") or ""
    tip = html.escape(TIPS["Sign"])
    return (
        f'<button type="button" class="sign-btn" data-sign="{html.escape(rid)}" '
        f'title="{tip}" data-tip="{tip}" aria-pressed="false">Sign</button>'
    )


def _is_definition(rel: dict) -> bool:
    move = (rel.get("author_move") or "").strip().lower()
    claimed = rel.get("claimed_type") or ""
    return move == "definition" or claimed == "DEFINITION_INSERTION"


def deviation_kind(rel: dict | None) -> str | None:
    if not rel:
        return None
    st = rel.get("final_status") or ""
    if st not in {"UNKNOWN_REMAINDER", "UNKNOWN", "UNSUPPORTED"}:
        return None
    if _is_definition(rel):
        return None
    if st in {"UNKNOWN_REMAINDER", "UNKNOWN"}:
        return "needs_judgment"
    claimed = rel.get("claimed_type") or ""
    if claimed in _NEEDS_JUDGMENT_CLAIMED:
        return "needs_judgment"
    blob = " ".join(
        [
            rel.get("author_move") or "",
            rel.get("math_summary_tex") or "",
            ((rel.get("author_source_anchor") or {}).get("prose_paraphrase") or ""),
        ]
    ).lower().replace("\\", "")
    if any(m in blob for m in _NEEDS_JUDGMENT_MARKS):
        return "needs_judgment"
    if claimed in _ENCODING_GAP_CLAIMED:
        return "encoding_gap"
    return "needs_judgment"


def lowered_zeros() -> set[str]:
    path = HERE / "lowering_queue.json"
    if not path.exists():
        return set()
    q = json.loads(path.read_text())
    return {
        e.get("id") or ""
        for e in q.get("edges") or []
        if e.get("engine_verdict") == "ZERO"
    }


_LOWERED_ZERO = None


def workspace_zero(rid: str) -> bool:
    global _LOWERED_ZERO
    if _LOWERED_ZERO is None:
        _LOWERED_ZERO = lowered_zeros()
    return rid in _LOWERED_ZERO


def status_chips(rel: dict) -> str:
    st = rel.get("final_status") or ""
    rid = rel.get("id") or ""
    q = queue_kind(rel)
    if q == "must_review":
        return ""
    if st == "EXACT_ZERO":
        return chip_span("zero", "0")
    if st == "ZERO_UNDER_SUBSTITUTION":
        return chip_span("zero-if-a", "0 if A")
    if st == "CERTIFIED_BY_RULE":
        return chip_span("cite", "cite")
    if st == "STRUCTURAL" or _is_definition(rel):
        return chip_span("def", "def")
    if st in {"UNKNOWN", "UNKNOWN_REMAINDER"}:
        return chip_span("remainder", "remainder")
    if st == "NONZERO":
        return chip_span("nonzero", "\u22600")
    if rid in set(ENCODE_LATER_IDS) or deviation_kind(rel) == "encoding_gap":
        return chip_span("gap", "gap")
    if st == "UNSUPPORTED":
        return chip_span("look", "look")
    return chip_span("look", "look")


def hue_you(rel: dict) -> tuple[str, str]:
    st = rel.get("final_status") or ""
    q = queue_kind(rel)
    if q == "must_review":
        return "orange", "sign"
    if rel.get("id") == "R007":
        return "green", "check A"
    if st == "EXACT_ZERO":
        return "green", "skip"
    if st == "ZERO_UNDER_SUBSTITUTION":
        return "green", "skip"
    if st == "CERTIFIED_BY_RULE" or st == "STRUCTURAL" or _is_definition(rel):
        return "blue", "skip"
    if st == "NONZERO":
        return "red", "—"
    return "orange", "—"


def queue_kind(rel: dict | None) -> str | None:
    if not rel:
        return None
    rid = rel.get("id") or ""
    if rid in MUST_REVIEW_IDS:
        return "must_review"
    if rid in set(ENCODE_LATER_IDS):
        return "encode_later"
    st = rel.get("final_status") or ""
    if st in {"UNKNOWN_REMAINDER", "UNKNOWN", "UNSUPPORTED"}:
        return "out_of_engine"
    return None


def row(rel: dict) -> str:
    st = rel.get("final_status") or ""
    kind = deviation_kind(rel)
    queue = queue_kind(rel)
    hue, you = hue_you(rel)
    hay = " ".join(
        [
            rel.get("public_display") or "",
            rel.get("author_move") or "",
            st,
            kind or "",
            queue or "",
            hue,
            you,
            rel.get("math_summary_tex") or "",
            (rel.get("condition") or {}).get("tex") or "",
            (rel.get("direct") or {}).get("residual_tex") or "",
            who(rel),
        ]
    ).lower()
    cond = rel.get("condition") or {}
    cond_tex = cond.get("tex") or cond.get("text") or ""
    show_a = bool(cond_tex) and cond_tex != "none" and (
        st == "ZERO_UNDER_SUBSTITUTION" or queue == "must_review"
    )
    a_cell = math_cell(cond_tex) if show_a else "—"
    dev_attr = f' data-deviation="{html.escape(kind)}"' if kind else ""
    q_attr = f' data-queue="{html.escape(queue)}"' if queue else ""
    return (
        f'<tr class="{html.escape(st)}" id="row-{html.escape(rel.get("id") or "")}" '
        f'data-status="{html.escape(st)}" data-hue="{html.escape(hue)}" '
        f'data-you="{html.escape(you)}" '
        f'data-section="{html.escape(rel.get("section") or "")}"{dev_attr}{q_attr} '
        f'data-hay="{esc(hay)}">'
        f'<td><a href="#row-{html.escape(rel.get("id") or "")}" data-open="rel-{html.escape(rel.get("id") or "")}">'
        f'{html.escape(rel.get("public_display") or "")}</a></td>'
        f"<td>{math_cell(rel.get('math_summary_tex'))}</td>"
        f"<td>{a_cell}</td>"
        f"<td class=\"status-cell\">{status_chips(rel)}</td>"
        f"<td class=\"you-cell\">{you_cell(rel)}</td>"
        "</tr>"
    )


def parse_eq(label: str) -> tuple[str, int, str] | None:
    s = label or ""
    m = re.search(r"\(([A-G])-(\d+)\)", s)
    if m:
        return m.group(1), int(m.group(2)), f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"\((\d+)\)", s)
    if m:
        return "main", int(m.group(1)), f"({m.group(1)})"
    return None


def short_label(label: str) -> str:
    p = parse_eq(label)
    return p[2] if p else label.replace("Eq. ", "")


def node_status_and_row(rels: list[dict], eq: str) -> tuple[str, str]:
    """Status and row id for a printed equation."""
    for r in rels:
        disp = r.get("public_display") or ""
        if disp == eq or disp == f"Eq. ({eq})" or disp.endswith(eq):
            if "→" not in disp and "->" not in disp:
                return r.get("final_status") or "STRUCTURAL", r.get("id") or ""
    for r in reversed(rels):
        tos = r.get("public_to") or []
        if eq in tos or any(eq in t for t in tos):
            return r.get("final_status") or "STRUCTURAL", r.get("id") or ""
    for r in rels:
        fr = r.get("public_from") or []
        if eq in fr or any(eq in t for t in fr):
            return r.get("final_status") or "STRUCTURAL", r.get("id") or ""
    return "STRUCTURAL", ""


def frozen_edge(rels: list[dict], a: str, b: str) -> bool:
    for r in rels:
        fr = r.get("public_from") or []
        to = r.get("public_to") or []
        if any(a in x for x in fr) and any(b in x for x in to):
            return True
    return False


def chip(
    eq_full: str,
    st: str,
    rid: str,
    kind: str | None = None,
    queue: str | None = None,
) -> str:
    lab = short_label(eq_full)
    href = f"#row-{html.escape(rid)}" if rid else "#"
    dev = f' data-deviation="{html.escape(kind)}"' if kind else ""
    q = f' data-queue="{html.escape(queue)}"' if queue else ""
    return (
        f'<a class="eq-node {html.escape(st)}" href="{href}" '
        f'data-status="{html.escape(st)}"{dev}{q} '
        f'data-open="rel-{html.escape(rid)}" title="{html.escape(st)} {html.escape(eq_full)}">'
        f"{html.escape(lab)}</a>"
    )


def main_corr_html(payload: dict) -> str:
    items: list[tuple[int, str, str, str, str, str]] = []
    seen: set[str] = set()
    for r in payload["relations"]:
        if r.get("section") != "main":
            continue
        fr = r.get("public_from") or []
        to = r.get("public_to") or []
        app = ""
        mains: list[int] = []
        for lab in fr:
            p = parse_eq(lab)
            if p and p[0] in "ABCDEFG":
                app = short_label(lab)
        for lab in fr + to:
            p = parse_eq(lab)
            if p and p[0] == "main" and p[1] not in mains:
                mains.append(p[1])
        if not mains:
            continue
        mains.sort()
        if mains == [7, 8] or set(mains) == {7, 8}:
            key, label, order = "7-8", "(7)→(8)", 7
        else:
            key = str(mains[0])
            label = f"({mains[0]})"
            order = mains[0]
        if key in seen and not app:
            continue
        if key in seen and app:
            items[:] = [x for x in items if x[1] != key]
        seen.add(key)
        items.append((order, key, label, app or "—", r.get("final_status") or "", r.get("id") or ""))
    items.sort()
    by_id = {r.get("id"): r for r in payload["relations"]}
    rows_html = []
    for _order, _key, label, src, st, rid in items:
        rel = by_id.get(rid)
        status_cell = status_chips(rel) if rel else chip_span("look", "look")
        rows_html.append(
            f'<tr id="corr-{html.escape(rid)}" data-status="{html.escape(st)}">'
            f'<td><a href="#row-{html.escape(rid)}" data-open="rel-{html.escape(rid)}">{html.escape(label)}</a></td>'
            f"<td>{html.escape(src)}</td>"
            f"<td class=\"status-cell\">{status_cell}</td>"
            "</tr>"
        )
    return (
        '<table class="ledger corr">'
        "<thead><tr><th>Main</th><th>Appendix source</th><th>Status</th></tr></thead>"
        "<tbody>"
        + "".join(rows_html)
        + "</tbody></table>"
    )


def must_review_html(payload: dict) -> str:
    by_id = {r.get("id"): r for r in payload["relations"]}
    order = ["R050", "R066", "R110", "R132"]
    rows_html = []
    for rid in order:
        rel = by_id.get(rid)
        if not rel:
            continue
        cond = rel.get("condition") or {}
        cond_tex = cond.get("tex") or cond.get("text") or ""
        a = math_cell(cond_tex) if cond_tex and cond_tex != "none" else "—"
        rows_html.append(
            f'<tr data-status="{html.escape(rel.get("final_status") or "")}" '
            f'data-queue="must_review" data-hue="orange" data-you="sign">'
            f'<td><a href="#row-{html.escape(rid)}" data-open="rel-{html.escape(rid)}">'
            f'{html.escape(rel.get("public_display") or "")}</a></td>'
            f"<td>{math_cell(rel.get('math_summary_tex'))}</td>"
            f"<td>{a}</td>"
            f'<td class="status-cell">{status_chips(rel)}</td>'
            f'<td class="you-cell">{you_cell(rel)}</td>'
            "</tr>"
        )
    return (
        '<table class="ledger must-review">'
        "<thead><tr><th>Step</th><th>What</th><th>A?</th><th>Status</th>"
        "<th>You</th></tr></thead><tbody>"
        + "".join(rows_html)
        + "</tbody></table>"
    )


def encode_gap_html(payload: dict) -> str:
    by_id = {r.get("id"): r for r in payload["relations"]}
    queue_path = HERE / "lowering_queue.json"
    lowered: dict[str, str] = {}
    if queue_path.exists():
        q = json.loads(queue_path.read_text())
        for e in q.get("edges") or []:
            if e.get("engine_verdict") == "ZERO":
                lowered[e.get("id") or ""] = "ZERO"
    rows_html = []
    for rid in ENCODE_LATER_IDS:
        rel = by_id.get(rid)
        if not rel:
            continue
        rows_html.append(
            f'<tr data-status="UNSUPPORTED" data-deviation="encoding_gap" data-hue="orange">'
            f'<td><a href="#row-{html.escape(rid)}" data-open="rel-{html.escape(rid)}">'
            f'{html.escape(rel.get("public_display") or "")}</a></td>'
            f"<td>{math_cell(rel.get('math_summary_tex'))}</td>"
            f'<td class="status-cell">{chip_span("gap", "gap")}</td>'
            "</tr>"
        )
    return (
        '<table class="ledger encoding-gap">'
        "<thead><tr><th>Step</th><th>What</th><th>Status</th></tr></thead>"
        "<tbody>"
        + "".join(rows_html)
        + "</tbody></table>"
    )


def section_seq_html(payload: dict) -> str:
    rels_by = defaultdict(list)
    for r in payload["relations"]:
        rels_by[r.get("section") or ""].append(r)
    blocks = []
    titles = {
        "A": "Appendix A",
        "B": "Appendix B",
        "C": "Appendix C",
        "D": "Appendix D",
        "E": "Appendix E",
        "F": "Appendix F",
        "G": "Appendix G",
    }
    for sec in "ABCDEFG":
        rels = rels_by.get(sec, [])
        eqs: dict[int, str] = {}
        for r in rels:
            for lab in (r.get("public_from") or []) + (r.get("public_to") or []):
                p = parse_eq(lab)
                if p and p[0] == sec:
                    eqs[p[1]] = lab if lab.startswith("Eq.") else f"Eq. ({p[2]})"
        ordered = [eqs[n] for n in sorted(eqs)]
        chips = []
        by_id = {r.get("id"): r for r in rels}
        for i, eq in enumerate(ordered):
            st, rid = node_status_and_row(rels, eq)
            if i:
                prev = ordered[i - 1]
                if frozen_edge(rels, prev, eq):
                    chips.append('<span class="edge-lab">→</span>')
                else:
                    chips.append('<span class="dots">⋯</span>')
            rel = by_id.get(rid)
            chips.append(chip(eq, st, rid, deviation_kind(rel), queue_kind(rel)))
        n = len(rels)
        counts = Counter(r.get("final_status") for r in rels)
        nice = {
            "EXACT_ZERO": "exact",
            "ZERO_UNDER_SUBSTITUTION": "subst",
            "CERTIFIED_BY_RULE": "rule",
            "UNKNOWN_REMAINDER": "remainder",
            "UNKNOWN": "unknown",
            "STRUCTURAL": "structural",
            "UNSUPPORTED": "unsupported",
        }
        bits = [f"{n} relations"]
        for k, lab in nice.items():
            if counts.get(k):
                bits.append(f"{lab} {counts[k]}")
        blocks.append(
            '<div class="lane">'
            f'<div class="lane-head">{titles[sec]}'
            f'<span class="mini-counts">{" · ".join(bits)}</span></div>'
            f'<div class="lane-body"><div class="lane-nodes eq-seq">{"".join(chips)}</div></div>'
            "</div>"
        )
    return "\n".join(blocks)


def replace_block(text: str, begin: str, end: str, inner: str) -> str:
    i = text.index(begin)
    j = text.index(end, i)
    return text[: i + len(begin)] + "\n" + inner + "\n" + text[j:]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "report-data.json"))
    ap.add_argument("--src", default=str(HERE / "index.src.html"))
    ap.add_argument("--html", default=str(HERE.parent / "output" / "index.html"))
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
    text = replace_block(text, BEGIN_CORR, END_CORR, main_corr_html(payload))
    text = replace_block(text, BEGIN_SEQ, END_SEQ, section_seq_html(payload))
    text = replace_block(text, BEGIN_MUST, END_MUST, must_review_html(payload))
    text = replace_block(text, BEGIN_ENCODE, END_ENCODE, encode_gap_html(payload))
    text = replace_block(text, BEGIN_DATA, END_DATA, data_tag)
    text = replace_block(text, BEGIN_CSS, END_CSS, "<style>\n" + css + "\n</style>")
    text = replace_block(text, BEGIN_JS, END_JS, "<script>\n" + js + "\n</script>")
    html_path.write_text(text)
    sha_path = HERE.parent / "expected" / "PRESENTATION_SHA256.txt"
    sha_path.parent.mkdir(parents=True, exist_ok=True)
    sha_path.write_text(
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
