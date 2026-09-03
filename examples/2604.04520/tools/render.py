#!/usr/bin/env python3
"""Render V3 HTML and Markdown independently from evidence/audit.json.

V3 = V1 visual grammar (colour bar, coloured chips, → vs ⋯) on V2
scientific semantics (claims, (4)→(5) chain, reviewer queue). Statuses
are copied from audit.json; this renderer does not recertify.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
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
    "UNCERTIFIED": "Uncertified",
}

# V1 hues. Numerical support sits on orange; no third colour language.
HUE = {
    "EXACT": "green",
    "EXACT_IF_ASSUMPTIONS": "green-if",
    "STRUCTURAL": "blue",
    "CITED_RULE": "blue",
    "ASYMPTOTIC_UNCERTIFIED": "orange",
    "HUMAN_REVIEW": "orange",
    "GAP": "orange",
    "NUMERICAL_SUPPORT": "orange",
    "NONZERO_RESIDUAL": "red",
    "UNCERTIFIED": "orange",
}

HUE_CLASS = {
    "green": "ok",
    "green-if": "ok-if",
    "blue": "cite",
    "orange": "inspect",
    "red": "wrong",
}

# Worse hue wins when an equation appears in several edges.
HUE_RANK = {"red": 5, "orange": 4, "blue": 2, "green-if": 1, "green": 0}

LANE_TITLE = {
    "main": "Main text",
    "appendix A": "Appendix A",
    "appendix B": "Appendix B",
    "appendix C": "Appendix C",
    "appendix D": "Appendix D",
    "appendix E": "Appendix E",
}

LANE_HINT = {
    "main": "published (1)–(11)",
    "appendix A": "DC response",
    "appendix B": "injection / shift",
    "appendix C": "Drude / BCD / QMD",
    "appendix D": r"derivation of \(\sigma^{\alpha\alpha\alpha}\)",
    "appendix E": "order estimation",
}

# Explicit physicist destinations. Other chips are routed from the model.
CHIP_HREF_OVERRIDE = {
    "(5)": "#claim-C2",
    "(4)": "#edge-E-green-kernel",
    "D-1": "#edge-E-D-longitudinal",
    "D-8": "#edge-E-D-shift",
    "C-1": "#edge-E-C-static-from-green",
    "C-2": "#edge-E-C-band-basis",
    "D-2": "#edge-E-D-TR-matrix",
    "D-4": "#edge-E-D-antisym",
    "(1)": "#edge-E-unitarity",
    "(3)": "#edge-E-static-sigma",
}

C2_EDGE_IDS = [
    "E-green-kernel",
    "E-C-static-from-green",
    "E-C-band-basis",
    "E-D-longitudinal",
    "E-D-TR-matrix",
    "E-D-antisym",
    "E-D-shift",
    "E-D-to-sigma2",
]

EQ_TOKEN_RE = re.compile(r"\((\d+)\)|([A-E]-\d+)")

CSS = """
:root{--ink:#22272b;--muted:#5c6770;--rule:#b7c0c7;--band:#f3f5f7;--accent:#2e5a88;--accent-fill:#e7f0f6;--paper:#ffffff;--warn-band:#f4f1ea;--ok:#2d6a4f;--cite:#2e5a88;--inspect:#b86a12;--wrong:#9b2c2c;--max:62rem}
*{box-sizing:border-box}html{font-size:17px}body{margin:0;color:var(--ink);background:var(--paper);font-family:"Iowan Old Style","Palatino Linotype",Palatino,"Times New Roman",Times,serif;line-height:1.45}
.wrap{max-width:var(--max);margin:0 auto;padding:1.25rem 1.25rem 4rem}
.kicker{font-family:system-ui,sans-serif;font-size:.78rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin:0 0 .35rem}
h1{font-size:1.7rem;margin:0 0 .35rem;line-height:1.2}h2{font-size:1.2rem;margin:1.6rem 0 .5rem}h3{font-size:1.02rem;margin:.25rem 0 .4rem}
.source,.judged-line,.muted,.hint,.note,.ev,.meta{font-family:system-ui,sans-serif;font-size:.9rem;color:var(--muted)}
.completeness{border:2px dashed #8a5a12;background:var(--warn-band);padding:.7rem .85rem;margin:0 0 1rem;font-family:system-ui,sans-serif;font-size:.9rem}
.completeness p{margin:.25rem 0}.completeness strong{letter-spacing:.04em;text-transform:uppercase;font-size:.78rem}
.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(9.2rem,1fr));gap:.55rem;margin:0 0 .85rem;font-family:system-ui,sans-serif}
.metric{border:1px solid var(--rule);padding:.55rem .65rem}.metric .n{font-size:1.15rem;font-weight:700;font-variant-numeric:tabular-nums}
.metric .l{display:block;font-size:.78rem;font-weight:650;margin-top:.15rem}.metric .hint{display:block;color:var(--muted);font-size:.72rem;margin-top:.25rem}
.stack{display:flex;width:100%;height:1.15rem;border:1px solid var(--ink)}
.seg{border:0;padding:0;height:100%;cursor:pointer;min-width:0}
.seg.green{background:var(--ok)}.seg.green-if{background:repeating-linear-gradient(-45deg,#2d6a4f,#2d6a4f 4px,#e8f3ec 4px,#e8f3ec 8px)}
.seg.blue{background:var(--cite)}.seg.orange{background:var(--inspect)}.seg.red{background:var(--wrong);flex:0 0 5px;min-width:5px}
.stack-counts{display:flex;font-family:system-ui,sans-serif;font-size:.68rem;color:var(--muted);margin:.2rem 0 .5rem;text-align:center}
.tone-key{display:flex;flex-wrap:wrap;gap:.45rem .85rem;font-family:system-ui,sans-serif;font-size:.82rem;font-weight:650;margin:0 0 .4rem}
.tone.ok{color:var(--ok)}.tone.cite{color:var(--cite)}.tone.inspect{color:var(--inspect)}.tone.wrong{color:var(--wrong)}
.chip{display:inline-block;font-family:system-ui,sans-serif;font-size:.72rem;font-weight:700;padding:.1rem .38rem;border:1.5px solid;margin-right:.2rem;white-space:nowrap}
.chip.ok{background:#1e5c3a;color:#fff;border-color:var(--ok)}.chip.ok-if{background:#cfe8d8;color:var(--ok);border-color:var(--ok)}
.chip.cite{background:#e7f0f6;color:var(--cite);border-color:var(--cite)}
.chip.inspect{background:#fff6e8;color:var(--inspect);border-color:var(--inspect)}
.chip.wrong{background:var(--wrong);color:#fff;border-color:var(--wrong)}
.card{border:1px solid var(--rule);padding:.65rem .75rem;margin:.5rem 0;background:var(--band)}
.card.ob{background:#fff}
.stmt{margin:.2rem 0 .45rem}
.meta{margin:.15rem 0}
table.ledger{width:100%;border-collapse:collapse;font-family:system-ui,sans-serif;font-size:.84rem}
table.ledger th,table.ledger td{border-bottom:1px solid var(--rule);text-align:left;vertical-align:top;padding:.38rem .45rem}
table.ledger tr[data-hue="green"] td:first-child{box-shadow:inset 4px 0 0 var(--ok)}
table.ledger tr[data-hue="green-if"] td:first-child{box-shadow:inset 4px 0 0 var(--ok)}
table.ledger tr[data-hue="blue"] td:first-child{box-shadow:inset 4px 0 0 var(--cite)}
table.ledger tr[data-hue="orange"] td:first-child{box-shadow:inset 4px 0 0 var(--inspect)}
table.ledger tr[data-hue="red"] td:first-child{box-shadow:inset 4px 0 0 var(--wrong)}
.lanes{margin:.4rem 0 1rem}
.lane{border:1px solid var(--rule);margin:.4rem 0;background:var(--paper)}
.lane-head{font-family:system-ui,sans-serif;font-size:.92rem;font-weight:650;padding:.4rem .65rem;background:var(--band);display:flex;justify-content:space-between;gap:.5rem;align-items:center}
.lane-body{padding:.45rem .65rem .7rem}
.lane-nodes{display:flex;flex-wrap:wrap;align-items:center;gap:.35rem .4rem;font-family:system-ui,sans-serif;font-size:.86rem}
.eq-node{border:1.5px solid var(--ink);padding:.12rem .32rem;background:var(--paper);font-weight:700;text-decoration:none;color:var(--ink);font-size:.78rem}
.eq-node.EXACT{border-style:solid;border-width:2px;border-color:var(--ok);color:var(--ok);background:#e8f3ec}
.eq-node.EXACT_IF_ASSUMPTIONS{border-style:dashed;border-width:2px;border-color:var(--ok);color:var(--ok);background:#e8f3ec}
.eq-node.STRUCTURAL,.eq-node.CITED_RULE{border-color:var(--cite);color:var(--cite);background:#e7f0f6}
.eq-node.GAP,.eq-node.HUMAN_REVIEW,.eq-node.NUMERICAL_SUPPORT,.eq-node.UNCERTIFIED{border-style:dashed;color:var(--inspect);border-color:var(--inspect);background:#fff6e8}
.eq-node.ASYMPTOTIC_UNCERTIFIED{border-style:dotted;color:var(--inspect);border-color:var(--inspect);background:#fff6e8}
.eq-node.NONZERO_RESIDUAL{border-color:var(--wrong);color:#fff;background:var(--wrong)}
.edge-lab{font-size:.75rem;color:var(--accent)}
.dots{color:var(--muted);letter-spacing:.12em}
.mini-counts{font-weight:400;color:var(--muted);font-size:.8rem}
header.mast{border-bottom:1px solid var(--rule);padding-bottom:1.25rem;margin-bottom:1.25rem}
.rev{font:700 .78rem system-ui;margin:.15rem .2rem 0 0;min-height:32px;padding:.25rem .5rem;border:2px solid #8a5a12;background:#fff;cursor:pointer}
.rev[data-on="1"]{background:#f4f1ea}
.tex{margin:.25rem 0;font-size:.95rem}
.warn{margin:.4rem 0 1rem}
.filter-pills{display:flex;flex-wrap:wrap;gap:.28rem;margin:.4rem 0}
.filter-pills button{font:inherit;font-size:.78rem;min-height:32px;border:1px solid var(--rule);background:var(--paper);cursor:pointer;font-family:system-ui,sans-serif;padding:.2rem .55rem}
.filter-pills button[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-fill)}
.hidden{display:none!important}
code,.mono{font-family:ui-monospace,Menlo,monospace;font-size:.88em}
footer{margin-top:2rem;padding-top:.9rem;border-top:1px solid var(--ink);font-family:system-ui,sans-serif;font-size:.88rem}
[data-tip]{position:relative}[data-tip]::after{content:attr(data-tip);position:absolute;left:0;bottom:calc(100% + 6px);background:var(--ink);color:#fff;font:400 .72rem system-ui,sans-serif;padding:.35rem .5rem;max-width:22rem;width:max-content;white-space:normal;opacity:0;visibility:hidden;z-index:20;pointer-events:none}
[data-tip]:hover::after,[data-tip]:focus-visible::after{opacity:1;visibility:visible}
""".strip()

JS = r"""
(function(){
  const KEY="paper-audit-v3:2604.04520";
  function load(){try{return JSON.parse(localStorage.getItem(KEY)||"{}");}catch(e){return {};}}
  function save(m){try{localStorage.setItem(KEY, JSON.stringify(m));}catch(e){}}
  function paint(){
    const m=load();
    document.querySelectorAll(".rev").forEach(function(b){
      const k=b.getAttribute("data-ob")+"|"+b.getAttribute("data-act");
      b.setAttribute("data-on", m[k]?"1":"0");
    });
  }
  function apply(hue){
    document.querySelectorAll("#obligation-table tbody tr").forEach(function(el){
      const ok = !hue || hue==="all" || el.getAttribute("data-hue")===hue;
      el.classList.toggle("hidden", !ok);
    });
    document.querySelectorAll(".filter-pills button").forEach(function(b){
      b.setAttribute("aria-pressed", b.getAttribute("data-hue")===hue ? "true":"false");
    });
  }
  document.addEventListener("click", function(ev){
    const b=ev.target.closest(".rev");
    if(b){
      ev.preventDefault();
      const m=load(); const k=b.getAttribute("data-ob")+"|"+b.getAttribute("data-act");
      if(m[k]) delete m[k]; else m[k]=true; save(m); paint();
      return;
    }
    const pill=ev.target.closest(".filter-pills button");
    if(pill){ apply(pill.getAttribute("data-hue")); return; }
    const seg=ev.target.closest(".stack .seg");
    if(seg){ apply(seg.getAttribute("data-hue")); }
  });
  paint();
})();
""".strip()


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def md_escape_cell(s: object) -> str:
    t = "" if s is None else str(s)
    return t.replace("|", "\\|").replace("\n", " ")


def eq_tokens(s: str) -> list[str]:
    out = []
    for m in EQ_TOKEN_RE.finditer(s or ""):
        out.append(f"({m.group(1)})" if m.group(1) else m.group(2))
    return out


def chip(status: str) -> str:
    lab = STATUS_LABEL.get(status, status)
    cls = HUE_CLASS[HUE.get(status, "orange")]
    return f'<span class="chip {cls}">{esc(lab)}</span>'


def hue_of(status: str) -> str:
    return HUE.get(status, "orange")


class Model:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.edges = data["edges"]
        self.claims = data["claims"]
        self.obs = data["reviewer_obligations"]
        self.eqs = data["inventory"]["equations"]
        self.by_id = {e["id"]: e for e in self.edges}
        self.public = {eq["public"]: eq for eq in self.eqs}
        self.edges_by_eq: dict[str, list[dict]] = defaultdict(list)
        for e in self.edges:
            seen = set()
            for tok in eq_tokens(e["from_eq"]) + eq_tokens(e["to_eq"]):
                if tok not in seen:
                    self.edges_by_eq[tok].append(e)
                    seen.add(tok)
        self.claims_by_eq: dict[str, list[dict]] = defaultdict(list)
        for c in self.claims:
            for tok in c.get("supporting_equations") or []:
                self.claims_by_eq[tok].append(c)
        self.obs_by_eq: dict[str, list[dict]] = defaultdict(list)
        for o in self.obs:
            for tok in eq_tokens(o.get("claim_used", "")) + eq_tokens(
                o.get("paper_evidence", "")
            ):
                self.obs_by_eq[tok].append(o)
        self.status_of = {eq["public"]: self._status(eq["public"]) for eq in self.eqs}
        self.href_of = {eq["public"]: self._href(eq["public"]) for eq in self.eqs}

    def _status(self, public: str) -> str:
        related = self.edges_by_eq.get(public) or []
        if not related:
            return "UNCERTIFIED"
        best = related[0]
        best_rank = HUE_RANK[hue_of(best["status"])]
        for e in related[1:]:
            r = HUE_RANK[hue_of(e["status"])]
            if r > best_rank or (
                r == best_rank and e.get("load_bearing") and not best.get("load_bearing")
            ):
                best, best_rank = e, r
        return best["status"]

    def _href(self, public: str) -> str:
        if public in CHIP_HREF_OVERRIDE:
            return CHIP_HREF_OVERRIDE[public]
        related = self.edges_by_eq.get(public) or []
        # Prefer an edge whose *to* token is this equation (result of a move).
        to_hits = [e for e in related if public in eq_tokens(e["to_eq"])]
        from_hits = [e for e in related if public in eq_tokens(e["from_eq"])]
        load_to = [e for e in to_hits if e.get("load_bearing")]
        load_from = [e for e in from_hits if e.get("load_bearing")]
        if len(load_to) == 1:
            return f"#edge-{load_to[0]['id']}"
        if load_to:
            return f"#edge-{load_to[0]['id']}"
        if len(load_from) == 1:
            return f"#edge-{load_from[0]['id']}"
        if load_from:
            return f"#edge-{load_from[0]['id']}"
        claims = self.claims_by_eq.get(public) or []
        if claims:
            return f"#claim-{claims[0]['id']}"
        obs = self.obs_by_eq.get(public) or []
        if obs:
            return f"#ob-{obs[0]['id']}"
        return f"#eq-detail-{self.public[public]['id']}"

    def adjacent_is_edge(self, a: str, b: str) -> bool:
        for e in self.edges:
            if a in eq_tokens(e["from_eq"]) and b in eq_tokens(e["to_eq"]):
                return True
        return False

    def hue_counts(self) -> dict[str, int]:
        counts = {"green": 0, "green-if": 0, "blue": 0, "orange": 0, "red": 0}
        for e in self.edges:
            counts[hue_of(e["status"])] += 1
        return counts


def edge_row(e: dict) -> str:
    aid = f"edge-{e['id']}"
    tex = ""
    if e.get("target_tex"):
        tex = f'<div class="tex">\\({esc(e["target_tex"])}\\)</div>'
    elif e.get("source_tex"):
        tex = f'<div class="tex">\\({esc(e["source_tex"])}\\)</div>'
    ev = f'<p class="ev">{esc(e["evidence"])}</p>' if e.get("evidence") else ""
    note = f'<p class="note">{esc(e["note"])}</p>' if e.get("note") else ""
    hue = hue_of(e["status"])
    return (
        f'<tr id="{esc(aid)}" data-status="{esc(e["status"])}" data-hue="{esc(hue)}">'
        f'<td><a href="#{esc(aid)}"><code>{esc(e["id"])}</code></a></td>'
        f'<td>{esc(e["from_eq"])} → {esc(e["to_eq"])}</td>'
        f'<td>{esc(e["transformation"])}</td>'
        f'<td>{esc("; ".join(e["assumptions"]) or "—")}</td>'
        f'<td>{chip(e["status"])}</td>'
        f'<td>{esc(e["locator"])}{tex}{ev}{note}</td>'
        f"</tr>"
    )


def render_map(model: Model, *, header: bool) -> str:
    by_sec: dict[str, list] = {}
    for eq in model.eqs:
        by_sec.setdefault(eq["section"], []).append(eq)
    lanes = []
    for sec, eqs in by_sec.items():
        nodes = []
        for i, eq in enumerate(eqs):
            st = model.status_of[eq["public"]]
            href = model.href_of[eq["public"]]
            tip = STATUS_LABEL.get(st, st)
            if eq.get("tex_label"):
                tip += f" · {eq['tex_label']}"
            elif eq.get("cue"):
                tip += f" · {eq['cue'][:80]}"
            nodes.append(
                f'<a class="eq-node {esc(st)}" id="map-{esc(eq["id"])}" '
                f'href="{esc(href)}" title="{esc(tip)}" data-tip="{esc(tip)}" '
                f'data-status="{esc(st)}">{esc(eq["public"])}</a>'
            )
            if i + 1 < len(eqs):
                nxt = eqs[i + 1]["public"]
                if model.adjacent_is_edge(eq["public"], nxt):
                    nodes.append('<span class="edge-lab">→</span>')
                else:
                    nodes.append('<span class="dots">⋯</span>')
        title = LANE_TITLE.get(sec, sec)
        hint = LANE_HINT.get(sec, "")
        lanes.append(
            f'<div class="lane"><div class="lane-head">{esc(title)}'
            f'<span class="mini-counts">{esc(hint)} · {len(eqs)} numbered lines</span></div>'
            f'<div class="lane-body"><div class="lane-nodes eq-seq">'
            f'{"".join(nodes)}</div></div></div>'
        )
    sid = "map-sec" if header else "map-detail-lanes"
    note = (
        "Coloured chips use the V1 status grammar. "
        "<strong>→</strong> is a reconstructed derivation edge; "
        "<strong>⋯</strong> is consecutive numbering only. "
        "Orange is not Exact. Click a chip to open the edge, claim, or obligation."
    )
    return (
        f'<section id="{sid}">'
        f"<h2>{'Main + appendix map A–E' if header else 'Equation detail'}</h2>"
        f"<p>{note}</p>"
        f'<div class="lanes" id="{"derivation-map" if header else "derivation-map-detail"}">'
        f'{"".join(lanes)}</div></section>'
    )


def flagship_path(model: Model) -> str:
    """Visual (4)→(5) path from reconstructed edges, not adjacency."""
    rows = [
        ["(3)", "(4)"],
        ["C-1", "C-2", "D-1", "D-2", "D-4"],
        ["D-1", "D-8", "(5)"],
    ]
    blocks = []
    for row in rows:
        bits = []
        for i, pub in enumerate(row):
            st = model.status_of.get(pub, "UNCERTIFIED")
            href = model.href_of.get(pub, f"#eq-detail-{pub}")
            bits.append(
                f'<a class="eq-node {esc(st)}" href="{esc(href)}">{esc(pub)}</a>'
            )
            if i + 1 < len(row):
                nxt = row[i + 1]
                if model.adjacent_is_edge(pub, nxt):
                    bits.append('<span class="edge-lab">→</span>')
                else:
                    bits.append('<span class="dots">⋯</span>')
        blocks.append(f'<div class="lane-nodes">{"".join(bits)}</div>')
    return (
        "<p>Reconstructed load-bearing path, not a certificate. "
        "There is no compiled local identity Eq.&nbsp;(4)=Eq.&nbsp;(5). "
        "The Green kernel is Eq.&nbsp;(4); Appendix C then D rewrite it "
        "to the geometric formula Eq.&nbsp;(5).</p>"
        f'<div class="lane"><div class="lane-body">{"".join(blocks)}</div></div>'
    )


def render_html(data: dict) -> str:
    model = Model(data)
    s = data["summary"]
    inv = data["inventory"]["v2"]
    counts = model.hue_counts()
    warns = "".join(f"<li>{esc(w)}</li>" for w in data["warnings"])

    claims_html = []
    for c in data["claims"]:
        unres = ", ".join(
            f'<a href="#ob-{esc(u)}">{esc(u)}</a>' for u in c.get("unresolved") or []
        ) or "—"
        eqs = ", ".join(esc(x) for x in c["supporting_equations"])
        blockers = "".join(f"<li>{esc(b)}</li>" for b in c.get("blockers") or [])
        claims_html.append(
            f'<article class="card" id="claim-{esc(c["id"])}">'
            f'<header><h3>{esc(c["id"])} {chip(c["status"])}</h3></header>'
            f'<p class="stmt">{esc(c["statement"])}</p>'
            f'<p class="meta"><strong>Where.</strong> {esc(c["locator"])}</p>'
            f'<p class="meta"><strong>Equations.</strong> {eqs}</p>'
            f'<p class="meta"><strong>Appendix chain.</strong> {esc(" → ".join(c["appendix_chain"]))}</p>'
            f'<p class="meta"><strong>Assumptions.</strong> {esc("; ".join(c["assumptions"]))}</p>'
            f'<p class="meta"><strong>Unresolved.</strong> {unres}</p>'
            f'<p class="meta"><strong>Downstream.</strong> {esc(c["downstream"])}</p>'
            f'<ul class="blockers">{blockers}</ul></article>'
        )

    c2_rows = "".join(edge_row(model.by_id[i]) for i in C2_EDGE_IDS if i in model.by_id)
    other_lb = "".join(
        edge_row(e)
        for e in model.edges
        if e.get("load_bearing") and e["id"] not in set(C2_EDGE_IDS)
    )
    all_rows = "".join(edge_row(e) for e in model.edges)

    obs = []
    for o in sorted(data["reviewer_obligations"], key=lambda x: x["priority"]):
        acts = "".join(
            f'<button type="button" class="rev" data-ob="{esc(o["id"])}" '
            f'data-act="{esc(a)}">{esc(a)}</button>'
            for a in o["actions"]
        )
        blocks = ", ".join(
            f'<a href="#{esc("claim-" + b if b.startswith("C") else "edge-" + b)}">{esc(b)}</a>'
            if b.startswith("C") or b.startswith("E-")
            else esc(b)
            for b in o["blocks"]
        )
        obs.append(
            f'<article class="card ob" id="ob-{esc(o["id"])}">'
            f"<h3>{esc(o['id'])} · priority {o['priority']} {chip(o['status'])}</h3>"
            f"<p><strong>Claim being used.</strong> {esc(o['claim_used'])}</p>"
            f"<p><strong>Why not certified.</strong> {esc(o['why_not_certified'])}</p>"
            f"<p><strong>Paper evidence.</strong> {esc(o['paper_evidence'])}</p>"
            f"<p><strong>Reviewer must decide.</strong> {esc(o['reviewer_must_decide'])}</p>"
            f"<p><strong>Blocks.</strong> {blocks}</p>"
            f'<p class="hint">Accepting does not stamp Exact.</p>'
            f'<div class="actions">{acts}</div></article>'
        )

    nums = []
    for n in data["numerical_evidence"]:
        nums.append(
            f'<article class="card" id="num-{esc(n["id"])}">'
            f"<h3>{esc(n['id'])} {chip(n['evidence_type'])}</h3>"
            f'<p class="meta"><strong>Quantity.</strong> {esc(n["quantity"])}</p>'
            f'<p class="meta"><strong>Supports.</strong> {esc(n["supports"])}</p>'
            f'<p class="meta"><strong>Regime.</strong> {esc(n["regime"])}</p>'
            f'<p class="meta"><strong>Does not prove.</strong> {esc(n["proves_not"])}</p>'
            f'<p class="meta"><strong>Where.</strong> {esc(n["locator"])}</p></article>'
        )

    detail_rows = []
    for eq in model.eqs:
        st = model.status_of[eq["public"]]
        href = model.href_of[eq["public"]]
        detail_rows.append(
            f'<tr id="eq-detail-{esc(eq["id"])}" data-hue="{esc(hue_of(st))}" data-status="{esc(st)}">'
            f"<td>{esc(eq['public'])}</td>"
            f"<td><code>{esc(eq['id'])}</code></td>"
            f"<td>{esc(eq['section'])}</td>"
            f"<td>{chip(st)}</td>"
            f'<td><a href="{esc(href)}">{esc(href)}</a></td>'
            f"<td>{esc(eq.get('tex_label') or '—')}</td>"
            f"<td class=\"mono\">{esc((eq.get('cue') or '')[:140])}</td>"
            f"</tr>"
        )

    flex = counts.copy()
    # Keep a visible red tick even at count 0, matching V1.
    red_style = "flex:0 0 5px" if counts["red"] == 0 else f"flex:{counts['red']}"
    stack = (
        f'<div class="stack" role="group">'
        f'<button type="button" class="seg green" data-hue="green" style="flex:{flex["green"]}" title="{counts["green"]} Exact" data-tip="{counts["green"]} Exact"></button>'
        f'<button type="button" class="seg green-if" data-hue="green-if" style="flex:{max(flex["green-if"], 1) if flex["green-if"] else 0}" title="{counts["green-if"]} Exact if A" data-tip="{counts["green-if"]} Exact if A"></button>'
        f'<button type="button" class="seg blue" data-hue="blue" style="flex:{flex["blue"]}" title="{counts["blue"]} def/cite" data-tip="{counts["blue"]} structural / cited rule"></button>'
        f'<button type="button" class="seg orange" data-hue="orange" style="flex:{flex["orange"]}" title="{counts["orange"]} reviewer looks" data-tip="{counts["orange"]} gap, review, remainder, numerics"></button>'
        f'<button type="button" class="seg red" data-hue="red" style="{red_style}" title="{counts["red"]} ≠0" data-tip="{counts["red"]} nonzero residual"></button>'
        f"</div>"
        f'<div class="stack-counts">'
        f'<span style="flex:{flex["green"]}">{counts["green"]}</span>'
        f'<span style="flex:{max(flex["green-if"], 1) if flex["green-if"] else 0}">{counts["green-if"]}</span>'
        f'<span style="flex:{flex["blue"]}">{counts["blue"]}</span>'
        f'<span style="flex:{flex["orange"]}">{counts["orange"]}</span>'
        f'<span style="flex:0 0 1.4rem;color:var(--wrong)">{counts["red"]}</span>'
        f"</div>"
    )

    authors = esc(s.get("authors") or "Anan, Kitamura, Morimoto")
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence ledger — {authors}, arXiv:{esc(data["paper"]["id"])}</title>
<style>
{CSS}
</style>
<script>
window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"],["$","$"]],displayMath:[["\\\\[","\\\\]"],["$$","$$"]]}}}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body><div class="wrap">
<header class="mast">
<p class="kicker">Evidence ledger · V3</p>
<h1>{esc(data["paper"]["title"])}</h1>
<p class="source">{authors}
 · Source: <a href="{esc(data["paper"]["source"])}">{esc(data["paper"]["source"])}</a>
 · <strong>Presentation is not a certificate</strong></p>

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
<div class="metric"><span class="n">{inv["total"]}</span><span class="l">numbered equations</span><span class="hint">main {inv["main"]} · appendix {inv["appendix"]}</span></div>
<div class="metric"><span class="n">{s["relations_reconstructed"]}</span><span class="l">reconstructed relations</span></div>
<div class="metric"><span class="n">{s["machine_certified_edges"]}</span><span class="l">machine-certified edges</span><span class="hint">Exact if A only</span></div>
<div class="metric"><span class="n">{s["assumption_dependent_edges"]}</span><span class="l">assumption-dependent edges</span></div>
<div class="metric"><span class="n">{s["unresolved_load_bearing"]}</span><span class="l">unresolved load-bearing</span></div>
</div>

{stack}
<div class="tone-key">
<span class="tone ok">Dark green = Exact · hatched = Exact if A</span>
<span class="tone cite">Blue = structural / cited rule</span>
<span class="tone inspect">Orange = inspect (gap, review, remainder, numerics)</span>
<span class="tone wrong">Dark red = local residual ≠ 0</span>
</div>
<p class="judged-line">Labels sit on V1 colours. Numerical support is orange, not a new colour. Orange is large on purpose.</p>
<ul class="warn">{warns}</ul>

{render_map(model, header=True)}
</header>

<main id="main">
<section id="claims">
<h2>B. Major scientific claims</h2>
{"".join(claims_html)}
</section>

<section id="graph">
<h2>C. Load-bearing derivation graph</h2>
<p>Central chain: Green-function kernel <strong>Eq. (4)</strong>
<code>eq:currentbyExcitation</code> → Appendix C → Appendix D
(TR identities, antisymmetrization, shift vector) → geometric
<strong>Eq. (5)</strong> <code>eq:sigma2</code>.</p>
{flagship_path(model)}
<table class="ledger">
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{c2_rows}</tbody>
</table>
<h3>Other load-bearing edges</h3>
<table class="ledger">
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{other_lb}</tbody>
</table>
</section>

<section id="queue">
<h2>D. Reviewer queue</h2>
<p>Sorted by scientific importance. Human Accept / Reject / Needs derivation
does not stamp machine Exact.</p>
{"".join(obs)}
</section>

<section id="numeric">
<h2>Numerical evidence (not a proof)</h2>
{"".join(nums)}
</section>

<section id="map-detail">
<h2>E. Equation detail</h2>
<p>The coloured chip map is on the first screen. This table is the locator
index: TeX labels, cues, and the chip destination. It is not a second map.</p>
<table class="ledger">
<thead><tr><th>Public</th><th>ID</th><th>Section</th><th>Status</th><th>Goes to</th><th>TeX label</th><th>Cue</th></tr></thead>
<tbody>{"".join(detail_rows)}</tbody>
</table>
</section>

<section id="ledger">
<h2>F. Full obligation ledger</h2>
<nav class="filter-pills">
<button type="button" data-hue="all" aria-pressed="true">all {len(model.edges)}</button>
<button type="button" data-hue="green-if">Exact if A {counts["green-if"]}</button>
<button type="button" data-hue="blue">blue {counts["blue"]}</button>
<button type="button" data-hue="orange">orange {counts["orange"]}</button>
<button type="button" data-hue="red">red {counts["red"]}</button>
</nav>
<table class="ledger" id="obligation-table">
<thead><tr><th>Edge</th><th>From → to</th><th>Transformation</th><th>Assumptions</th><th>Status</th><th>Locator / evidence</th></tr></thead>
<tbody>{all_rows}</tbody>
</table>
</section>
</main>

<footer>
<p><strong>Presentation is not a certificate.</strong> {esc(data["v1_frozen_note"])}</p>
<p>Canonical model: <code>evidence/audit.json</code>. Markdown twin: <code>v3/audit.md</code>.
V1 and V2 are historical baselines under <code>v1/</code> and <code>v2/</code>.</p>
</footer>
</div>
<script>
{JS}
</script>
</body></html>
"""


def _md_map_line(model: Model, eqs: list[dict]) -> str:
    bits = []
    for i, eq in enumerate(eqs):
        st = model.status_of[eq["public"]]
        bits.append(f"{eq['public']} (`{st}`)")
        if i + 1 < len(eqs):
            nxt = eqs[i + 1]["public"]
            bits.append("→" if model.adjacent_is_edge(eq["public"], nxt) else "⋯")
    return " ".join(bits)


def render_markdown(data: dict) -> str:
    model = Model(data)
    s = data["summary"]
    inv = data["inventory"]["v2"]
    counts = model.hue_counts()
    lines = [
        f"# Paper audit V3 — arXiv:{data['paper']['id']}",
        "",
        f"**{data['paper']['title']}**",
        "",
        f"Authors: {s.get('authors') or 'Anan, Kitamura, Morimoto'}",
        "",
        f"Source: {data['paper']['source']}",
        "",
        "**Presentation is not a certificate.**",
        "",
        f"- Overall state: `{s['overall_state']}`",
        f"- Claims: {s['claim_count']}",
        f"- Numbered equations: {inv['total']} = main {inv['main']} + appendix {inv['appendix']}",
        f"- V1 claimed: {data['inventory']['v1_claimed']['total']} = main {data['inventory']['v1_claimed']['main']} + appendix {data['inventory']['v1_claimed']['appendix']}",
        f"- Relations reconstructed: {s['relations_reconstructed']}",
        f"- Machine-certified edges: {s['machine_certified_edges']}",
        f"- Assumption-dependent edges: {s['assumption_dependent_edges']}",
        f"- Unresolved load-bearing edges: {s['unresolved_load_bearing']}",
        "",
        "Status colour grammar (HTML only; Markdown is the semantic twin):",
        "",
        f"- Dark green / Exact: {counts['green']}",
        f"- Hatched green / Exact if A: {counts['green-if']}",
        f"- Blue / structural or cited rule: {counts['blue']}",
        f"- Orange / inspect: {counts['orange']}",
        f"- Dark red / nonzero residual: {counts['red']}",
        "",
        data["inventory"]["correction"],
        "",
        "### Warnings",
        "",
    ]
    for w in data["warnings"]:
        lines.append(f"- {w}")

    lines += ["", "## Main + appendix map A–E", ""]
    lines.append(
        "`→` is a reconstructed derivation edge. `⋯` is consecutive numbering only."
    )
    lines.append("")
    by_sec: dict[str, list] = {}
    for eq in model.eqs:
        by_sec.setdefault(eq["section"], []).append(eq)
    for sec, eqs in by_sec.items():
        title = LANE_TITLE.get(sec, sec)
        lines += [f"### {title} ({len(eqs)})", "", _md_map_line(model, eqs), ""]

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
        "Visual path (reconstructed edges, not adjacency):",
        "",
        "- `(3) → (4)` Green kernel",
        "- `C-1 → C-2 → D-1 → D-2 → D-4` band basis, longitudinal, TR, antisymmetrization",
        "- `D-1 → D-8 → (5)` shift-vector rewrite to geometric conductivity",
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

    for i in C2_EDGE_IDS:
        if i in model.by_id:
            e = model.by_id[i]
            lines.append(md_edge(e))
            if e.get("target_tex"):
                lines += ["", f"$$ {e['target_tex']} $$", ""]
            elif e.get("source_tex"):
                lines += ["", f"$$ {e['source_tex']} $$", ""]

    lines += [
        "",
        "### Other load-bearing edges",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in model.edges:
        if e.get("load_bearing") and e["id"] not in set(C2_EDGE_IDS):
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
        "## E. Equation detail",
        "",
        f"Method: {data['inventory']['method']}",
        "",
        "| Public | ID | Section | Status | Destination | TeX label |",
        "|---|---|---|---|---|---|",
    ]
    for eq in model.eqs:
        lines.append(
            f"| {eq['public']} | `{eq['id']}` | {md_escape_cell(eq['section'])} | "
            f"`{model.status_of[eq['public']]}` | `{model.href_of[eq['public']]}` | "
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
    for e in model.edges:
        lines.append(md_edge(e))

    lines += [
        "",
        "## Provenance",
        "",
        data["v1_frozen_note"],
        "",
        "Canonical model: `evidence/audit.json`. HTML twin: `v3/audit.html`.",
        "V1 (`v1/`) is the visual-ledger baseline. V2 (`v2/`) is the claim-ledger baseline.",
        "",
    ]
    return "\n".join(lines) + "\n"


def semantic_index(data: dict) -> dict:
    return {
        "claims": {c["id"]: c["status"] for c in data["claims"]},
        "edges": {e["id"]: e["status"] for e in data["edges"]},
        "obligations": {o["id"]: o["status"] for o in data["reviewer_obligations"]},
        "inventory_total": data["inventory"]["v2"]["total"],
        "eq4": any(
            e["from_eq"] == "(4)" or "(4)" in e["from_eq"] for e in data["edges"]
        ),
        "eq5": any(e["to_eq"] == "(5)" for e in data["edges"]),
    }


def check_rendered(data: dict, html_page: str, md_page: str) -> list[str]:
    idx = semantic_index(data)
    err = []
    for cid, st in idx["claims"].items():
        if cid not in html_page or cid not in md_page:
            err.append(f"claim {cid} missing from a renderer")
        if f"`{st}`" not in md_page and st not in md_page:
            err.append(f"status {st} for {cid} missing from Markdown")
    for eid in idx["edges"]:
        if eid not in html_page or eid not in md_page:
            err.append(f"edge {eid} missing from a renderer")
        if f"`{idx['edges'][eid]}`" not in md_page:
            err.append(f"edge status {idx['edges'][eid]} missing from Markdown for {eid}")
    for oid, st in idx["obligations"].items():
        if oid not in html_page or oid not in md_page:
            err.append(f"obligation {oid} missing")
        if f"`{st}`" not in md_page:
            err.append(f"obligation status {st} missing from Markdown for {oid}")
    if "Eq. (4)" not in html_page and "(4)" not in html_page:
        err.append("HTML missing Eq. (4)")
    if "Eq. (5)" not in html_page and "(5)" not in html_page:
        err.append("HTML missing Eq. (5)")
    if "eq:currentbyExcitation" not in md_page:
        err.append("Markdown missing Green-kernel label")
    if "eq:sigma2" not in md_page:
        err.append("Markdown missing geometric-conductivity label")
    if r"\sigma^{\alpha\alpha\alpha}" not in md_page and "sigma2" not in md_page:
        err.append("Markdown lost geometric conductivity TeX")
    if re.search(r"0\*|ws-zero", html_page):
        err.append("HTML contains invalid 0*")
    if "Rice" not in html_page or "Rice" not in md_page:
        err.append("Rice–Mele missing")
    if "NUMERICAL_SUPPORT" not in html_page and "Numerical support" not in html_page:
        err.append("HTML missing numerical-support label")
    if data["inventory"]["v2"]["total"] != 93:
        err.append("inventory total is not 93")
    if 'id="map-sec"' not in html_page.split('id="main"')[0]:
        err.append("coloured map is not on the first screen")
    if "class=\"stack\"" not in html_page and 'class="stack"' not in html_page:
        err.append("HTML missing colour stack")
    if ">→</span>" not in html_page or ">⋯</span>" not in html_page:
        err.append("HTML map missing → / ⋯ distinction")
    if "Appendix F" in html_page or "Appendix G" in html_page:
        err.append("HTML fabricates Appendix F/G")
    if "Sign" in html_page and "sign-btn" in html_page:
        err.append("HTML restored V1 Sign semantics")
    if "Accept assumption/reasoning" not in html_page:
        err.append("HTML missing V2 reviewer actions")
    if 'href="#edge-E-D-longitudinal"' not in html_page:
        err.append("D-1 / longitudinal chip routing missing")
    if 'href="#edge-E-D-shift"' not in html_page:
        err.append("D-8 / shift chip routing missing")
    if 'href="#claim-C2"' not in html_page:
        err.append("Eq. (5) / C2 chip routing missing")
    if ">Sign<" in html_page:
        err.append("HTML contains Sign button")
    for e in data["edges"]:
        if e["status"] == "EXACT" and "asymptotic" in e["transformation"]:
            err.append(f"{e['id']} Exact on asymptotic")
    c2 = next(c for c in data["claims"] if c["id"] == "C2")
    if c2["status"] == "EXACT":
        err.append("C2 promoted to Exact")
    # Chip destinations must not collapse onto one generic table.
    hrefs = re.findall(r'class="eq-node[^"]*" id="map-[^"]+" href="([^"]+)"', html_page)
    if hrefs and all(h == "#obligation-table" for h in hrefs):
        err.append("all map chips still point at #obligation-table")
    if len(set(hrefs)) < 8:
        err.append(f"map chip destinations not diverse enough: {sorted(set(hrefs))}")
    return err


INDEX_HTML = """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=v3/audit.html">
<link rel="canonical" href="v3/audit.html">
<title>Anan et al. audit — canonical V3</title>
</head>
<body>
<p>Canonical reviewer HTML: <a href="v3/audit.html">v3/audit.html</a></p>
<p>Markdown twin: <a href="v3/audit.md">v3/audit.md</a></p>
<p>Historical baselines: <a href="v1/audit.html">V1 visual ledger</a> ·
<a href="v2/audit.html">V2 claim ledger</a>.</p>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = json.loads((ROOT / "evidence" / "audit.json").read_text(encoding="utf-8"))
    html_page = render_html(data)
    md_page = render_markdown(data)
    v3 = ROOT / "v3"
    v3.mkdir(exist_ok=True)
    (v3 / "audit.html").write_text(html_page, encoding="utf-8")
    (v3 / "audit.md").write_text(md_page, encoding="utf-8")
    (ROOT / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    err = check_rendered(data, html_page, md_page)
    print("wrote v3/audit.html", len(html_page), "v3/audit.md", len(md_page))
    if err:
        print("CHECK_FAIL")
        for e in err:
            print(" -", e)
        return 1
    print("CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
