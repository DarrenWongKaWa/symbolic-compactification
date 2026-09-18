#!/usr/bin/env python3
"""Frozen V2 renderer (claim-ledger baseline). Do not use for canonical output.

Canonical V3 renderer: tools/render.py
"""
from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STATUS_LABEL = {
    "EXACT": "Exact",
    "EXACT_IF_ASSUMPTIONS": "Exact if A",
    "STRUCTURAL": "Structural",
    "CITED_RULE": "Cited rule",
    "ASYMPTOTIC_UNCERTIFIED": "Asymptotic, uncertified",
    "HUMAN_REVIEW": "Human review",
    "GAP": "Gap",
    "NONZERO_RESIDUAL": "Nonzero residual",
    "NUMERICAL_SUPPORT": "Numerical support",
}

STATUS_CLASS = {
    "EXACT": "ok",
    "EXACT_IF_ASSUMPTIONS": "ok-if",
    "STRUCTURAL": "cite",
    "CITED_RULE": "cite",
    "ASYMPTOTIC_UNCERTIFIED": "inspect",
    "HUMAN_REVIEW": "inspect",
    "GAP": "inspect",
    "NONZERO_RESIDUAL": "wrong",
    "NUMERICAL_SUPPORT": "num",
}


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def md_escape_cell(s: object) -> str:
    t = "" if s is None else str(s)
    return t.replace("|", "\\|").replace("\n", " ")


def chip(status: str) -> str:
    lab = STATUS_LABEL.get(status, status)
    cls = STATUS_CLASS.get(status, "inspect")
    return f'<span class="chip {cls}">{esc(lab)}</span>'


def render_html(data: dict) -> str:
    s = data["summary"]
    inv = data["inventory"]["v2"]
    warns = "".join(f"<li>{esc(w)}</li>" for w in data["warnings"])
    claims_html = []
    for c in data["claims"]:
        blockers = "".join(f"<li>{esc(b)}</li>" for b in c.get("blockers") or [])
        claims_html.append(
            f'<article class="card" id="claim-{esc(c["id"])}">'
            f'<header><h3>{esc(c["id"])} {chip(c["status"])}</h3></header>'
            f'<p class="stmt">{esc(c["statement"])}</p>'
            f"<p><strong>Where.</strong> {esc(c['locator'])}</p>"
            f"<p><strong>Equations.</strong> {esc(', '.join(c['supporting_equations']))}</p>"
            f"<p><strong>Appendix chain.</strong> {esc(' → '.join(c['appendix_chain']))}</p>"
            f"<p><strong>Assumptions.</strong> {esc('; '.join(c['assumptions']))}</p>"
            f"<p><strong>Unresolved.</strong> {esc(', '.join(c['unresolved']))}</p>"
            f"<p><strong>Downstream.</strong> {esc(c['downstream'])}</p>"
            f'<ul class="blockers">{blockers}</ul></article>'
        )
    lb = [e for e in data["edges"] if e.get("load_bearing")]
    # C2 chain first
    c2_ids = [
        "E-green-kernel",
        "E-C-static-from-green",
        "E-C-band-basis",
        "E-D-longitudinal",
        "E-D-TR-matrix",
        "E-D-antisym",
        "E-D-shift",
        "E-D-to-sigma2",
    ]
    by_id = {e["id"]: e for e in data["edges"]}

    def edge_row(e: dict) -> str:
        aid = f"edge-{e['id']}"
        tex = ""
        if e.get("target_tex"):
            tex = f"<div class=\"tex\">\\({esc(e['target_tex'])}\\)</div>"
        elif e.get("source_tex"):
            tex = f"<div class=\"tex\">\\({esc(e['source_tex'])}\\)</div>"
        ev = f"<p class=\"ev\">{esc(e['evidence'])}</p>" if e.get("evidence") else ""
        note = f"<p class=\"note\">{esc(e['note'])}</p>" if e.get("note") else ""
        return (
            f'<tr id="{esc(aid)}">'
            f'<td><a href="#{esc(aid)}"><code>{esc(e["id"])}</code></a></td>'
            f'<td>{esc(e["from_eq"])} → {esc(e["to_eq"])}</td>'
            f'<td>{esc(e["transformation"])}</td>'
            f'<td>{esc("; ".join(e["assumptions"]) or "—")}</td>'
            f'<td>{chip(e["status"])}</td>'
            f'<td>{esc(e["locator"])}{tex}{ev}{note}</td>'
            f"</tr>"
        )

    c2_rows = "".join(edge_row(by_id[i]) for i in c2_ids if i in by_id)
    other_lb = "".join(
        edge_row(e) for e in lb if e["id"] not in set(c2_ids)
    )
    all_rows = "".join(edge_row(e) for e in data["edges"])

    obs = []
    for o in sorted(data["reviewer_obligations"], key=lambda x: x["priority"]):
        acts = "".join(
            f'<button type="button" class="rev" data-ob="{esc(o["id"])}" data-act="{esc(a)}">{esc(a)}</button>'
            for a in o["actions"]
        )
        obs.append(
            f'<article class="card ob" id="ob-{esc(o["id"])}">'
            f"<h3>{esc(o['id'])} · priority {o['priority']} {chip(o['status'])}</h3>"
            f"<p><strong>Claim being used.</strong> {esc(o['claim_used'])}</p>"
            f"<p><strong>Why not certified.</strong> {esc(o['why_not_certified'])}</p>"
            f"<p><strong>Paper evidence.</strong> {esc(o['paper_evidence'])}</p>"
            f"<p><strong>Reviewer must decide.</strong> {esc(o['reviewer_must_decide'])}</p>"
            f"<p><strong>Blocks.</strong> {esc(', '.join(o['blocks']))}</p>"
            f'<p class="hint">Accepting does not stamp Exact.</p>'
            f'<div class="actions">{acts}</div></article>'
        )

    nums = []
    for n in data["numerical_evidence"]:
        nums.append(
            f'<article class="card" id="num-{esc(n["id"])}">'
            f"<h3>{esc(n['id'])} {chip(n['evidence_type'])}</h3>"
            f"<p><strong>Quantity.</strong> {esc(n['quantity'])}</p>"
            f"<p><strong>Supports.</strong> {esc(n['supports'])}</p>"
            f"<p><strong>Regime.</strong> {esc(n['regime'])}</p>"
            f"<p><strong>Does not prove.</strong> {esc(n['proves_not'])}</p>"
            f"<p><strong>Where.</strong> {esc(n['locator'])}</p></article>"
        )

    lanes = []
    by_sec: dict[str, list] = {}
    for eq in data["inventory"]["equations"]:
        by_sec.setdefault(eq["section"], []).append(eq)
    for sec, eqs in by_sec.items():
        nodes = []
        for eq in eqs:
            nodes.append(
                f'<a class="eq-node" id="eq-{esc(eq["id"])}" href="#eq-{esc(eq["id"])}" '
                f'title="{esc(eq.get("tex_label") or eq["cue"])}">{esc(eq["public"])}</a>'
            )
        lanes.append(
            f'<div class="lane"><div class="lane-head">{esc(sec)} · {len(eqs)}</div>'
            f'<div class="lane-nodes">{" ".join(nodes)}</div></div>'
        )

    pub = data["inventory"]["main_public_map"]
    pub_rows = "".join(
        f"<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>" for k, v in pub.items()
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>V2 paper audit — arXiv:{esc(data["paper"]["id"])}</title>
<style>
:root{{--ink:#22272b;--muted:#5c6770;--rule:#b7c0c7;--band:#f3f5f7;--ok:#2d6a4f;--cite:#2e5a88;--inspect:#b86a12;--wrong:#9b2c2c;--num:#5c4a1f;--max:64rem}}
*{{box-sizing:border-box}}body{{margin:0;color:var(--ink);background:#fff;font:17px/1.45 "Iowan Old Style",Palatino,serif}}
.wrap{{max-width:var(--max);margin:0 auto;padding:1.2rem 1.2rem 4rem}}
.kicker{{font:700 .78rem/1.2 system-ui,sans-serif;letter-spacing:.04em;text-transform:uppercase;color:var(--muted)}}
h1{{font-size:1.65rem;line-height:1.2;margin:.2rem 0 .4rem}}h2{{font-size:1.2rem;margin:1.6rem 0 .5rem}}h3{{font-size:1.02rem;margin:.2rem 0 .4rem}}
.source,.muted,.hint,.note,.ev{{color:var(--muted);font-family:system-ui,sans-serif;font-size:.9rem}}
.completeness{{border:2px dashed #8a5a12;background:#f4f1ea;padding:.7rem .85rem;margin:0 0 1rem}}
.metrics{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.5rem;margin:0 0 1rem}}
.metric{{border:1px solid var(--rule);padding:.5rem .6rem}}.metric .n{{font-weight:700;font-variant-numeric:tabular-nums}}
.metric .l{{display:block;font-size:.78rem;font-weight:650}}
.chip{{display:inline-block;font:700 .72rem system-ui,sans-serif;padding:.08rem .36rem;border:1.5px solid;margin-right:.2rem}}
.chip.ok{{background:#1e5c3a;color:#fff;border-color:var(--ok)}}
.chip.ok-if{{background:#cfe8d8;color:var(--ok);border-color:var(--ok)}}
.chip.cite{{background:#e7f0f6;color:var(--cite);border-color:var(--cite)}}
.chip.inspect{{background:#fff6e8;color:var(--inspect);border-color:var(--inspect)}}
.chip.wrong{{background:var(--wrong);color:#fff;border-color:var(--wrong)}}
.chip.num{{background:#f3ead2;color:var(--num);border-color:var(--num)}}
.card{{border:1px solid var(--rule);padding:.7rem .8rem;margin:.55rem 0;background:var(--band)}}
.card.ob{{background:#fff}}
table{{width:100%;border-collapse:collapse;font:0.84rem/1.35 system-ui,sans-serif}}
th,td{{border-bottom:1px solid var(--rule);text-align:left;vertical-align:top;padding:.35rem .4rem}}
.lane{{border:1px solid var(--rule);margin:.35rem 0}}.lane-head{{background:var(--band);padding:.35rem .55rem;font:650 .9rem system-ui}}
.lane-nodes{{display:flex;flex-wrap:wrap;gap:.3rem;padding:.4rem .55rem}}
.eq-node{{border:1.5px solid var(--ink);padding:.08rem .28rem;text-decoration:none;color:var(--ink);font:700 .75rem system-ui}}
.rev{{font:700 .78rem system-ui;margin:.15rem .2rem 0 0;min-height:32px;padding:.25rem .5rem;border:2px solid #8a5a12;background:#fff;cursor:pointer}}
.rev[data-on="1"]{{background:#f4f1ea}}
.tex{{margin:.25rem 0;font-size:.95rem}}
.warn{{margin:.4rem 0 1rem}}
code{{font-family:ui-monospace,Menlo,monospace;font-size:.88em}}
footer{{margin-top:2rem;border-top:1px solid var(--ink);padding-top:.8rem;font:0.88rem system-ui}}
</style>
<script>
window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"],["$","$"]],displayMath:[["\\\\[","\\\\]"],["$$","$$"]]}}}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body><div class="wrap">
<p class="kicker">Paper audit V2</p>
<h1>{esc(data["paper"]["title"])}</h1>
<p class="source">Source: <a href="{esc(data["paper"]["source"])}">{esc(data["paper"]["source"])}</a>
 · Anan, Kitamura, Morimoto · <strong>Presentation is not a certificate</strong></p>

<section id="summary">
<h2>A. Paper audit summary</h2>
<div class="completeness" role="status">
<p><strong>{esc(s["overall_state"])}</strong>
 · claims {s["claim_count"]}
 · numbered equations {inv["total"]} (main {inv["main"]} + appendix {inv["appendix"]})
 · relations {s["relations_reconstructed"]}
 · machine-certified {s["machine_certified_edges"]}
 · assumption-dependent {s["assumption_dependent_edges"]}
 · unresolved load-bearing {s["unresolved_load_bearing"]}</p>
<p>Green is a local residual, not a paper pass. Inventory coverage is not a derivation pass.</p>
</div>
<div class="metrics">
<div class="metric"><span class="n">{inv["total"]}</span><span class="l">numbered equations (V2)</span><span class="muted">V1 claimed 94 = 12+82; S-matrix was split</span></div>
<div class="metric"><span class="n">{s["relations_reconstructed"]}</span><span class="l">reconstructed relations</span></div>
<div class="metric"><span class="n">{s["machine_certified_edges"]}</span><span class="l">machine-certified edges</span><span class="muted">Exact if A only</span></div>
</div>
<ul class="warn">{warns}</ul>
<p>{esc(data["inventory"]["correction"])}</p>
</section>

<section id="claims">
<h2>B. Major scientific claims</h2>
{"".join(claims_html)}
</section>

<section id="graph">
<h2>C. Load-bearing derivation graph</h2>
<p>Central chain: Green-function kernel <strong>Eq. (4)</strong> → geometric
<strong>Eq. (5)</strong> via Appendix C then Appendix D. Statuses are not greened
for display.</p>
<table>
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{c2_rows}</tbody>
</table>
<h3>Other load-bearing edges</h3>
<table>
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{other_lb}</tbody>
</table>
</section>

<section id="queue">
<h2>D. Reviewer queue</h2>
<p>Sorted by scientific importance. Accepting a row does not stamp Exact.</p>
{"".join(obs)}
</section>

<section id="numeric">
<h2>Numerical evidence (not a proof)</h2>
{"".join(nums)}
</section>

<section id="map-sec">
<h2>E. Full equation / appendix map</h2>
<p>Secondary navigation. Published numbers: main (1)–(11); appendix A–E.
V1’s A–E chip counts 18/18/28/10/8 for the appendix are unchanged.</p>
<table><thead><tr><th>Published</th><th>Identity (V1 offset noted)</th></tr></thead>
<tbody>{pub_rows}</tbody></table>
{"".join(lanes)}
</section>

<section id="ledger">
<h2>F. Full obligation ledger</h2>
<table>
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{all_rows}</tbody>
</table>
</section>

<footer>
<p><strong>Presentation is not a certificate.</strong> {esc(data["v1_frozen_note"])}</p>
<p>Canonical model: <code>evidence/audit.json</code>. Markdown twin: <code>v2/audit.md</code>.</p>
</footer>
</div>
<script>
(function(){{
  const KEY="paper-audit-v2:2604.04520";
  function load(){{try{{return JSON.parse(localStorage.getItem(KEY)||"{{}}");}}catch(e){{return {{}};}}}}
  function save(m){{try{{localStorage.setItem(KEY, JSON.stringify(m));}}catch(e){{}}}}
  function paint(){{
    const m=load();
    document.querySelectorAll(".rev").forEach(function(b){{
      const k=b.getAttribute("data-ob")+"|"+b.getAttribute("data-act");
      b.setAttribute("data-on", m[k]?"1":"0");
    }});
  }}
  document.addEventListener("click", function(ev){{
    const b=ev.target.closest(".rev"); if(!b) return;
    ev.preventDefault();
    const m=load(); const k=b.getAttribute("data-ob")+"|"+b.getAttribute("data-act");
    if(m[k]) delete m[k]; else m[k]=true; save(m); paint();
  }});
  paint();
}})();
</script>
</body></html>
"""


def render_markdown(data: dict) -> str:
    s = data["summary"]
    inv = data["inventory"]["v2"]
    lines = [
        f"# Paper audit V2 — arXiv:{data['paper']['id']}",
        "",
        f"**{data['paper']['title']}**",
        "",
        f"Source: {data['paper']['source']}",
        "",
        "**Presentation is not a certificate.**",
        "",
        "## A. Paper audit summary",
        "",
        f"- Overall state: `{s['overall_state']}`",
        f"- Claims: {s['claim_count']}",
        f"- Numbered equations (V2): {inv['total']} = main {inv['main']} + appendix {inv['appendix']}",
        f"- V1 claimed: {data['inventory']['v1_claimed']['total']} = main {data['inventory']['v1_claimed']['main']} + appendix {data['inventory']['v1_claimed']['appendix']}",
        f"- Relations reconstructed: {s['relations_reconstructed']}",
        f"- Machine-certified edges: {s['machine_certified_edges']}",
        f"- Assumption-dependent edges: {s['assumption_dependent_edges']}",
        f"- Unresolved load-bearing edges: {s['unresolved_load_bearing']}",
        "",
        data["inventory"]["correction"],
        "",
        "### Warnings",
        "",
    ]
    for w in data["warnings"]:
        lines.append(f"- {w}")
    lines += ["", "## B. Major scientific claims", ""]
    for c in data["claims"]:
        lines += [
            f"### {c['id']} — {STATUS_LABEL.get(c['status'], c['status'])}",
            "",
            c["statement"],
            "",
            f"- **Status:** `{c['status']}`",
            f"- **Locator:** {c['locator']}",
            f"- **Supporting equations:** {', '.join(c['supporting_equations'])}",
            f"- **Appendix chain:** {' → '.join(c['appendix_chain'])}",
            f"- **Assumptions:** {'; '.join(c['assumptions'])}",
            f"- **Unresolved obligations:** {', '.join(c['unresolved'])}",
            f"- **Downstream:** {c['downstream']}",
            "",
        ]
        for b in c.get("blockers") or []:
            lines.append(f"- Blocker: {b}")
        lines.append("")

    lines += [
        "## C. Load-bearing derivation graph",
        "",
        "Central chain reconstructed from the TeX: **Eq. (4)** "
        "`eq:currentbyExcitation` → Appendix C band-basis kernel → "
        "Appendix D longitudinal + TR + antisymmetrization + shift vector → "
        "**Eq. (5)** `eq:sigma2`.",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]

    def md_edge(e: dict) -> str:
        return (
            f"| `{e['id']}` | {md_escape_cell(e['from_eq'])} | {md_escape_cell(e['to_eq'])} | "
            f"{md_escape_cell(e['transformation'])} | {md_escape_cell('; '.join(e['assumptions']))} | "
            f"`{e['status']}` | {md_escape_cell(e['locator'])} |"
        )

    c2_ids = [
        "E-green-kernel",
        "E-C-static-from-green",
        "E-C-band-basis",
        "E-D-longitudinal",
        "E-D-TR-matrix",
        "E-D-antisym",
        "E-D-shift",
        "E-D-to-sigma2",
    ]
    by_id = {e["id"]: e for e in data["edges"]}
    for i in c2_ids:
        if i in by_id:
            lines.append(md_edge(by_id[i]))
            if by_id[i].get("target_tex"):
                lines += ["", f"$$ {by_id[i]['target_tex']} $$", ""]
            elif by_id[i].get("source_tex"):
                lines += ["", f"$$ {by_id[i]['source_tex']} $$", ""]

    lines += ["", "### Other load-bearing edges", "",
              "| ID | From | To | Transformation | Assumptions | Status | Locator |",
              "|---|---|---|---|---|---|---|"]
    for e in data["edges"]:
        if e.get("load_bearing") and e["id"] not in set(c2_ids):
            lines.append(md_edge(e))

    lines += ["", "## D. Reviewer queue", ""]
    for o in sorted(data["reviewer_obligations"], key=lambda x: x["priority"]):
        lines += [
            f"### {o['id']} (priority {o['priority']}) — `{o['status']}`",
            "",
            f"**Claim being used.** {o['claim_used']}",
            "",
            f"**Why the system cannot certify it.** {o['why_not_certified']}",
            "",
            f"**Evidence from the paper.** {o['paper_evidence']}",
            "",
            f"**What the reviewer must decide.** {o['reviewer_must_decide']}",
            "",
            f"**Blocks.** {', '.join(o['blocks'])}",
            "",
            "Human approval does not stamp Exact.",
            "",
        ]

    lines += ["", "## Numerical evidence", ""]
    for n in data["numerical_evidence"]:
        lines += [
            f"### {n['id']} — `{n['evidence_type']}`",
            "",
            f"- Quantity: {n['quantity']}",
            f"- Supports: {n['supports']}",
            f"- Regime: {n['regime']}",
            f"- Does not prove: {n['proves_not']}",
            f"- Locator: {n['locator']}",
            "",
        ]

    lines += [
        "## E. Equation inventory",
        "",
        f"Method: {data['inventory']['method']}",
        "",
        "| Public | ID | Section | TeX label |",
        "|---|---|---|---|",
    ]
    for eq in data["inventory"]["equations"]:
        lines.append(
            f"| {eq['public']} | `{eq['id']}` | {md_escape_cell(eq['section'])} | "
            f"{eq.get('tex_label') or '—'} |"
        )

    lines += [
        "",
        "### Published main-text map",
        "",
        "| Number | Content |",
        "|---|---|",
    ]
    for k, v in data["inventory"]["main_public_map"].items():
        lines.append(f"| {k} | {md_escape_cell(v)} |")

    lines += [
        "",
        "## F. Full relation ledger",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in data["edges"]:
        lines.append(md_edge(e))

    lines += [
        "",
        "## Provenance",
        "",
        data["v1_frozen_note"],
        "",
        "Canonical model: `evidence/audit.json`. HTML twin: `v2/audit.html`.",
        "",
    ]
    return "\n".join(lines) + "\n"


def semantic_index(data: dict) -> dict:
    return {
        "claims": {c["id"]: c["status"] for c in data["claims"]},
        "edges": {e["id"]: e["status"] for e in data["edges"]},
        "obligations": {o["id"]: o["status"] for o in data["reviewer_obligations"]},
        "inventory_total": data["inventory"]["v2"]["total"],
        "eq4": any(e["from_eq"] == "(4)" or "(4)" in e["from_eq"] for e in data["edges"]),
        "eq5": any(e["to_eq"] == "(5)" for e in data["edges"]),
    }


def check_rendered(data: dict, html_page: str, md_page: str) -> list[str]:
    idx = semantic_index(data)
    err = []
    for cid, st in idx["claims"].items():
        if cid not in html_page or cid not in md_page:
            err.append(f"claim {cid} missing from a renderer")
        if st not in html_page.replace(" ", "") and cid in html_page:
            pass
        if f"`{st}`" not in md_page and st not in md_page:
            err.append(f"status {st} for {cid} missing from Markdown")
    for eid in idx["edges"]:
        if eid not in html_page or eid not in md_page:
            err.append(f"edge {eid} missing from a renderer")
    if "Eq. (4)" not in html_page and "(4)" not in html_page:
        err.append("HTML missing Eq. (4)")
    if "Eq. (5)" not in html_page and "(5)" not in html_page:
        err.append("HTML missing Eq. (5)")
    if "eq:currentbyExcitation" not in md_page:
        err.append("Markdown missing Green-kernel label")
    if "eq:sigma2" not in md_page:
        err.append("Markdown missing geometric-conductivity label")
    if re.search(r"0\*|ws-zero", html_page):
        err.append("HTML contains invalid 0*")
    if "Rice" not in html_page or "Rice" not in md_page:
        err.append("Rice–Mele missing")
    if "NUMERICAL_SUPPORT" not in html_page and "Numerical support" not in html_page:
        err.append("HTML missing numerical-support class")
    if data["inventory"]["v2"]["total"] != 93:
        err.append("inventory total is not 93")
    # no Exact on remainder claims
    for e in data["edges"]:
        if e["status"] == "EXACT" and "asymptotic" in e["transformation"]:
            err.append(f"{e['id']} Exact on asymptotic")
    return err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = json.loads((ROOT / "evidence" / "audit.json").read_text(encoding="utf-8"))
    html_page = render_html(data)
    md_page = render_markdown(data)
    (ROOT / "v2" / "audit.html").write_text(html_page, encoding="utf-8")
    (ROOT / "v2" / "audit.md").write_text(md_page, encoding="utf-8")
    err = check_rendered(data, html_page, md_page)
    print("wrote v2/audit.html", len(html_page), "v2/audit.md", len(md_page))
    if err:
        print("CHECK_FAIL")
        for e in err:
            print(" -", e)
        return 1
    print("CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
