#!/usr/bin/env python3
"""Render V3.1 HTML and Markdown from audit.json.

Paper-agnostic. Statuses are copied from audit.json; this script does
not recertify. Optional presentation hints live under
audit.json['presentation'] and never change a scientific status.
"""
from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path

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

HUE_RANK = {"red": 5, "orange": 4, "blue": 2, "green-if": 1, "green": 0}

DISCHARGED = {
    "EXACT",
    "EXACT_IF_ASSUMPTIONS",
    "STRUCTURAL",
    "CITED_RULE",
}

ACCEPT_WARN = (
    "Human acceptance records reviewer judgment; it does not change a "
    "machine status to Exact."
)

LANE_TITLE = {
    "main": "Main text",
    "appendix A": "Appendix A",
    "appendix B": "Appendix B",
    "appendix C": "Appendix C",
    "appendix D": "Appendix D",
    "appendix E": "Appendix E",
}

LANE_HINT: dict[str, str] = {}

EQ_TOKEN_RE = re.compile(r"\((\d+)\)|([A-Z]-\d+)")
LABEL_RE = re.compile(r"\\label\{[^}]*\}?")
WS_RE = re.compile(r"\s+")
SKIP_CUE_RE = re.compile(r"begin\{(tikzpicture|feynhand)\}")
ARRAY_RE = re.compile(
    r"(?:\\left\s*\(\s*)?\\begin\{array\}\{[^}]*\}(.*?)\\end\{array\}(?:\s*\\right\s*\))?",
    re.S,
)
PMATRIX_SPLIT_RE = re.compile(r"(\\begin\{pmatrix\}.*?\\end\{pmatrix\})", re.S)

CSS = """
:root{--ink:#22272b;--muted:#5c6770;--rule:#b7c0c7;--band:#f3f5f7;--accent:#2e5a88;--accent-fill:#e7f0f6;--paper:#ffffff;--warn-band:#f4f1ea;--ok:#2d6a4f;--cite:#2e5a88;--inspect:#b86a12;--wrong:#9b2c2c;--max:62rem}
*{box-sizing:border-box}html{font-size:17px}body{margin:0;color:var(--ink);background:var(--paper);font-family:"Iowan Old Style","Palatino Linotype",Palatino,"Times New Roman",Times,serif;line-height:1.45}
.wrap{max-width:var(--max);margin:0 auto;padding:1.25rem 1.25rem 4rem}
.kicker{font-family:system-ui,sans-serif;font-size:.78rem;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin:0 0 .35rem}
h1{font-size:1.7rem;margin:0 0 .35rem;line-height:1.2}h2{font-size:1.2rem;margin:1.6rem 0 .5rem}h3{font-size:1.02rem;margin:.25rem 0 .35rem}
.source,.judged-line,.muted,.hint,.note,.ev,.meta,.one-line,.path,.ass,.blocks,.edge-op{font-family:system-ui,sans-serif;font-size:.9rem;color:var(--muted)}
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
.card{border:1px solid var(--rule);padding:.55rem .7rem;margin:.4rem 0;background:var(--band)}
.card.ob{background:#fff}
.stmt{margin:.15rem 0 .3rem}
.path,.ass,.blocks{margin:.1rem 0}
.one-line{margin:.35rem 0 .7rem}
table.ledger{width:100%;border-collapse:collapse;font-family:system-ui,sans-serif;font-size:.84rem}
table.ledger th,table.ledger td{border-bottom:1px solid var(--rule);text-align:left;vertical-align:top;padding:.38rem .45rem}
table.ledger tr[data-hue="green"] td:first-child,table.ledger tr[data-hue="green-if"] td:first-child{box-shadow:inset 4px 0 0 var(--ok)}
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
.filter-pills{display:flex;flex-wrap:wrap;gap:.28rem;margin:.4rem 0}
.filter-pills button{font:inherit;font-size:.78rem;min-height:32px;border:1px solid var(--rule);background:var(--paper);cursor:pointer;font-family:system-ui,sans-serif;padding:.2rem .55rem}
.filter-pills button[aria-pressed="true"]{border-color:var(--accent);background:var(--accent-fill)}
.hidden{display:none!important}
code,.mono{font-family:ui-monospace,Menlo,monospace;font-size:.88em}
footer{margin-top:2rem;padding-top:.9rem;border-top:1px solid var(--ink);font-family:system-ui,sans-serif;font-size:.88rem}
[data-tip]{position:relative}[data-tip]::after{content:attr(data-tip);position:absolute;left:0;bottom:calc(100% + 6px);background:var(--ink);color:#fff;font:400 .72rem system-ui,sans-serif;padding:.35rem .5rem;max-width:22rem;width:max-content;white-space:normal;opacity:0;visibility:hidden;z-index:20;pointer-events:none}
[data-tip]:hover::after,[data-tip]:focus-visible::after{opacity:1;visibility:visible}
.chain{font-family:system-ui,sans-serif;font-size:.95rem;margin:.2rem 0 .7rem}
.edge-line{border:1px solid var(--rule);margin:.3rem 0;background:var(--paper)}
.edge-line[data-hue="green"],.edge-line[data-hue="green-if"]{box-shadow:inset 4px 0 0 var(--ok)}
.edge-line[data-hue="blue"]{box-shadow:inset 4px 0 0 var(--cite)}
.edge-line[data-hue="orange"]{box-shadow:inset 4px 0 0 var(--inspect)}
.edge-line[data-hue="red"]{box-shadow:inset 4px 0 0 var(--wrong)}
.edge-head{display:flex;flex-wrap:wrap;gap:.3rem .7rem;align-items:baseline;padding:.35rem .6rem;font-family:system-ui,sans-serif;font-size:.88rem}
.edge-move{font-weight:650}
.edge-ev{padding:0 .6rem .4rem;font-family:system-ui,sans-serif;font-size:.86rem}
.drawer{margin:1.2rem 0;border:1px solid var(--rule);padding:.45rem .65rem;background:var(--paper);font-family:system-ui,sans-serif}
.drawer>summary{cursor:pointer;font-weight:650}
.eq-rec{border-bottom:1px solid var(--rule);padding:.28rem 0;font-size:.84rem}
.eq-rec .tex{margin:.2rem 0 .1rem}
.need{margin:.25rem 0 .15rem}
.need-lab{font-family:system-ui,sans-serif;font-size:.78rem;font-weight:650;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.judge-strip{border:2px solid var(--inspect);background:#fff6e8;padding:.7rem .85rem;margin:0 0 1rem;font-family:system-ui,sans-serif}
.judge-lead{margin:0 0 .35rem;color:var(--inspect);font-weight:700}
.judge-lead a{color:var(--inspect)}
.judge-list{margin:0;font-size:.88rem;line-height:1.55}
.judge-list a{color:var(--ink);font-weight:650;text-decoration:none;border-bottom:1px solid var(--inspect)}
#queue{border:2px solid var(--inspect);padding:.85rem .9rem 1.1rem;background:#fffaf3;margin:1.8rem 0}
#queue h2{margin-top:.1rem;color:var(--inspect)}
.card.ob{border-color:var(--inspect);box-shadow:inset 4px 0 0 var(--inspect)}
.ob-source{font-family:system-ui,sans-serif;font-size:.82rem;color:var(--muted);margin:.15rem 0 .35rem}
.discharged{margin:.55rem 0 1rem;border:1px dashed var(--ok);padding:.35rem .6rem;background:#f4faf6;font-family:system-ui,sans-serif}
.discharged>summary{cursor:pointer;font-weight:650;color:var(--ok)}
.discharged-line{font-family:system-ui,sans-serif;font-size:.88rem;color:var(--ok);margin:.35rem 0}
.tex-fallback{white-space:pre-wrap;font-family:ui-monospace,Menlo,monospace;font-size:.82rem;background:var(--band);padding:.35rem .5rem;overflow:auto;margin:.2rem 0}
""".strip()

JS = r"""
(function(){
  const KEY="paper-audit:"+(document.documentElement.getAttribute("data-audit-key")||"default");
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
  function openHash(){
    const h=location.hash||"";
    if(!h) return;
    const el=document.getElementById(h.slice(1));
    if(!el) return;
    let node=el;
    while(node){
      if(node.tagName==="DETAILS") node.open=true;
      node=node.parentElement;
    }
    el.scrollIntoView({block:"start"});
  }
  function mathFallback(){
    document.querySelectorAll(".tex").forEach(function(el){
      if(el.querySelector("mjx-container, .MathJax, .mjx-chtml")) return;
      var pre=el.querySelector(".tex-fallback");
      if(pre) pre.hidden=false;
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
  document.addEventListener("toggle", function(ev){
    const d=ev.target;
    if(d && d.tagName==="DETAILS" && d.open && window.MathJax && MathJax.typesetPromise){
      MathJax.typesetPromise([d]).catch(function(){});
    }
  }, true);
  window.addEventListener("hashchange", openHash);
  window.addEventListener("load", function(){
    if(window.MathJax && MathJax.startup && MathJax.startup.promise){
      MathJax.startup.promise.then(mathFallback).catch(mathFallback);
    } else {
      setTimeout(mathFallback, 1200);
    }
  });
  paint();
  openHash();
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


def presentation(data: dict) -> dict:
    return data.get("presentation") or {}


def central_edge_ids(data: dict) -> list[str]:
    p = presentation(data)
    if p.get("central_edge_ids"):
        return list(p["central_edge_ids"])
    marked = [e["id"] for e in data.get("edges") or [] if e.get("central")]
    if marked:
        return marked
    return [e["id"] for e in data.get("edges") or [] if e.get("load_bearing")]


def claim_view(c: dict, data: dict) -> dict:
    extra = (presentation(data).get("claims") or {}).get(c["id"]) or {}
    if extra:
        return extra
    return {
        "line": c.get("statement") or "",
        "path": " → ".join(c.get("supporting_equations") or []),
        "assumptions": " · ".join(c.get("assumptions") or []) or None,
        "note": None,
    }


def edge_op(e: dict, data: dict) -> str:
    ops = presentation(data).get("edge_ops") or {}
    return ops.get(e["id"], e.get("transformation") or "")


def ob_title(o: dict, data: dict) -> str:
    titles = presentation(data).get("obligation_titles") or {}
    return titles.get(o["id"], o["id"])


def ob_need(o: dict, data: dict) -> str:
    needs = presentation(data).get("obligation_need") or {}
    return needs.get(o["id"], o.get("reviewer_must_decide") or o.get("why_not_certified") or "")


def paper_macros(tex: str) -> str:
    t = tex.replace(r"\uprm", r"\mathrm").replace(r"\smrm", r"\mathrm")
    t = re.sub(
        r"\\mel\{([^{}]*)\}\{([^{}]*)\}\{([^{}]*)\}",
        r"\\langle \1|\2|\3\\rangle",
        t,
    )
    t = re.sub(r"\\ket\{([^{}]*)\}", r"|{\1}\\rangle", t)
    t = re.sub(r"\\bra\{([^{}]*)\}", r"\\langle{\1}|", t)
    return t


def array_to_pmatrix(tex: str) -> str:
    def repl(m: re.Match) -> str:
        return r"\begin{pmatrix}" + m.group(1).strip() + r"\end{pmatrix}"

    return ARRAY_RE.sub(repl, tex)


def strip_align_outside_pmatrix(tex: str) -> str:
    parts = PMATRIX_SPLIT_RE.split(tex)
    out = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            out.append(part)
            continue
        part = part.replace("&", "")
        part = part.replace("\\\\", " ")
        out.append(part)
    return "".join(out)


def salvage_tex(tex: str) -> str | None:
    t = tex.strip().rstrip(",;")
    t = re.sub(r"\\[A-Za-z]+\{[^{}]*$", "", t)
    t = re.sub(r"\\[A-Za-z]+$", "", t)
    t = re.sub(r"[-+]\\frac\{[^{}]+\}\{\s*$", "", t)
    t = t.rstrip("\\").strip()
    if not t or SKIP_CUE_RE.search(t):
        return None
    if t.count("}") > t.count("{"):
        return None
    t += "}" * (t.count("{") - t.count("}"))
    lefts = len(re.findall(r"\\left\b", t))
    rights = len(re.findall(r"\\right\b", t))
    if lefts > rights:
        t += r"\right." * (lefts - rights)
    return t or None


def tex_html(math_src: str | None, raw: str = "") -> str:
    """MathJax first; escaped <pre> if typesetting fails. Never drop TeX."""
    raw = raw or math_src or ""
    if not raw and not math_src:
        return ""
    fallback = f'<pre class="tex-fallback" hidden>{esc(raw)}</pre>'
    if math_src:
        return (
            f'<div class="tex" data-tex="{esc(math_src)}">'
            f"\\({esc(math_src)}\\){fallback}</div>"
        )
    return (
        f'<div class="tex tex-raw" data-tex="{esc(raw)}">'
        f'<pre class="tex-fallback">{esc(raw)}</pre></div>'
    )


def display_cue(cue: str) -> str:
    """Turn an inventory cue into MathJax, matching ledger quality.

    Inventory rows are align fragments. Arrays become pmatrix. Truncated
    source is salvaged, then shown as raw LaTeX if MathJax cannot take it.
    """
    if not cue:
        return ""
    raw = clean_cue(cue)
    if SKIP_CUE_RE.search(cue):
        return tex_html(None, raw or cue)
    t = LABEL_RE.sub("", cue)
    t = paper_macros(t)
    t = array_to_pmatrix(t)
    t = strip_align_outside_pmatrix(t)
    t = WS_RE.sub(" ", t).strip()
    t = salvage_tex(t)
    if not t:
        return tex_html(None, raw or cue)
    return tex_html(t)


def clean_cue(cue: str) -> str:
    t = LABEL_RE.sub("", cue or "")
    t = t.replace("&", " ")
    t = t.replace("\\\\", " ")
    t = WS_RE.sub(" ", t).strip()
    return t


def tip_of(eq: dict, status: str) -> str:
    lab = STATUS_LABEL.get(status, status)
    if eq.get("tex_label"):
        return f"{lab} · {eq['tex_label']}"
    return lab


def act_label(action: str) -> str:
    if action.startswith("Accept"):
        return "Accept reasoning"
    return action


class Model:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.edges = data.get("edges") or []
        self.claims = data.get("claims") or []
        self.obs = data.get("reviewer_obligations") or []
        self.eqs = (data.get("inventory") or {}).get("equations") or []
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
        self.chip_href = presentation(data).get("chip_href") or {}
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
        if public in self.chip_href:
            return self.chip_href[public]
        related = self.edges_by_eq.get(public) or []
        to_hits = [e for e in related if public in eq_tokens(e["to_eq"])]
        from_hits = [e for e in related if public in eq_tokens(e["from_eq"])]
        load_to = [e for e in to_hits if e.get("load_bearing")]
        load_from = [e for e in from_hits if e.get("load_bearing")]
        if load_to:
            return f"#edge-{load_to[0]['id']}"
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


def linkify_tokens(text: str, model: Model) -> str:
    out: list[str] = []
    last = 0
    src = text or ""
    for m in EQ_TOKEN_RE.finditer(src):
        out.append(esc(src[last : m.start()]))
        tok = f"({m.group(1)})" if m.group(1) else m.group(2)
        href = model.href_of.get(tok)
        if href:
            out.append(f'<a href="{esc(href)}">{esc(tok)}</a>')
        else:
            out.append(esc(tok))
        last = m.end()
    out.append(esc(src[last:]))
    return "".join(out)


def link_obs(ids: list[str]) -> str:
    return " · ".join(f'<a href="#ob-{esc(u)}">{esc(u)}</a>' for u in ids) or "—"


def edge_row(e: dict, *, with_id: bool) -> str:
    aid = f"edge-{e['id']}"
    id_attr = f' id="{esc(aid)}"' if with_id else ""
    tex = ""
    if e.get("target_tex"):
        tex = tex_html(e["target_tex"])
    elif e.get("source_tex"):
        tex = tex_html(e["source_tex"])
    ev = f'<p class="ev">{esc(e["evidence"])}</p>' if e.get("evidence") else ""
    note = f'<p class="note">{esc(e["note"])}</p>' if e.get("note") else ""
    hue = hue_of(e["status"])
    return (
        f'<tr{id_attr} data-status="{esc(e["status"])}" data-hue="{esc(hue)}">'
        f'<td><a href="#{esc(aid)}"><code>{esc(e["id"])}</code></a></td>'
        f'<td>{esc(e["from_eq"])} → {esc(e["to_eq"])}</td>'
        f'<td>{esc(e["transformation"])}</td>'
        f'<td>{esc("; ".join(e["assumptions"]) or "—")}</td>'
        f'<td>{chip(e["status"])}</td>'
        f'<td>{esc(e["locator"])}{tex}{ev}{note}</td>'
        f"</tr>"
    )


def compact_edge(e: dict, data: dict) -> str:
    op = edge_op(e, data)
    aid = f"edge-{e['id']}"
    bits = []
    if e.get("locator"):
        bits.append(f'<p class="meta">{esc(e["locator"])}</p>')
    if e.get("assumptions"):
        bits.append(
            f'<p class="meta">Assumptions: {esc("; ".join(e["assumptions"]))}</p>'
        )
    if e.get("evidence"):
        bits.append(f'<p class="ev">{esc(e["evidence"])}</p>')
    if e.get("note"):
        bits.append(f'<p class="note">{esc(e["note"])}</p>')
    if e.get("target_tex"):
        bits.append(tex_html(e["target_tex"]))
    elif e.get("source_tex"):
        bits.append(tex_html(e["source_tex"]))
    extra = "".join(bits) or '<p class="meta">See <code>evidence/audit.json</code>.</p>'
    hue = hue_of(e["status"])
    return (
        f'<article class="edge-line" id="{esc(aid)}" data-hue="{esc(hue)}" '
        f'data-status="{esc(e["status"])}">'
        f'<div class="edge-head">'
        f'<span class="edge-move">{esc(e["from_eq"])} → {esc(e["to_eq"])}</span>'
        f'<span class="edge-op">{esc(op)}</span>'
        f"{chip(e['status'])}"
        f"</div>"
        f'<details class="edge-ev"><summary>Evidence</summary>{extra}</details>'
        f"</article>"
    )


def render_map(model: Model) -> str:
    by_sec: dict[str, list] = {}
    for eq in model.eqs:
        by_sec.setdefault(eq["section"], []).append(eq)
    lanes = []
    for sec, eqs in by_sec.items():
        nodes = []
        for i, eq in enumerate(eqs):
            st = model.status_of[eq["public"]]
            href = model.href_of[eq["public"]]
            tip = tip_of(eq, st)
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
    note = (
        "Coloured chips use the V1 status grammar. "
        "<strong>→</strong> is a reconstructed derivation edge; "
        "<strong>⋯</strong> is consecutive numbering only. "
        "Orange is not Exact. Click a chip for the claim, edge, or equation record."
    )
    return (
        '<section id="map-sec">'
        "<h2>Equation map</h2>"
        f"<p>{note}</p>"
        f'<div class="lanes" id="derivation-map">'
        f'{"".join(lanes)}</div></section>'
    )


def render_claims(data: dict, model: Model) -> str:
    cards = []
    for c in data["claims"]:
        view = claim_view(c, data)
        line = view.get("line") or c["statement"]
        parts = [
            f'<article class="card claim-card" id="claim-{esc(c["id"])}">',
            f'<header><h3>{esc(c["id"])} {chip(c["status"])}</h3></header>',
            f'<p class="stmt">{line}</p>',
        ]
        if view.get("note"):
            parts.append(f'<p class="stmt">{esc(view["note"])}</p>')
        if view.get("path"):
            parts.append(
                f'<p class="path">Path: {linkify_tokens(view["path"], model)}</p>'
            )
        if view.get("assumptions"):
            # Compact assumption lines may contain already-delimited TeX.
            parts.append(f'<p class="ass">Assumptions: {view["assumptions"]}</p>')
        parts.append(
            f'<p class="blocks">Blocks: {link_obs(c.get("unresolved") or [])}</p>'
        )
        parts.append("</article>")
        cards.append("".join(parts))
    return "".join(cards)


def render_queue(data: dict) -> str:
    cards = []
    for o in sorted(data.get("reviewer_obligations") or [], key=lambda x: x.get("priority", 99)):
        acts = "".join(
            f'<button type="button" class="rev" data-ob="{esc(o["id"])}" '
            f'data-act="{esc(a)}">{esc(act_label(a))}</button>'
            for a in o["actions"]
        )
        blocks = []
        for b in o["blocks"]:
            if b.startswith("C"):
                blocks.append(f'<a href="#claim-{esc(b)}">{esc(b)}</a>')
            elif b.startswith("E-"):
                blocks.append(f'<a href="#edge-{esc(b)}">{esc(b)}</a>')
            else:
                blocks.append(esc(b))
        title = ob_title(o, data)
        need = ob_need(o, data)
        src = o.get("paper_evidence") or o.get("locator") or ""
        src_html = (
            f'<p class="ob-source">Source: {esc(src)}</p>' if src else ""
        )
        cards.append(
            f'<article class="card ob ob-card" id="ob-{esc(o["id"])}">'
            f"<h3>{esc(o['id'])} · {esc(title)} {chip(o['status'])}</h3>"
            f'<p class="need"><span class="need-lab">Need to verify</span><br>{need}</p>'
            f"{src_html}"
            f'<p class="blocks">Blocks: {" · ".join(blocks)}</p>'
            f'<div class="actions">{acts}</div></article>'
        )
    return "".join(cards)


def render_judge_strip(data: dict) -> str:
    obs = sorted(
        data.get("reviewer_obligations") or [],
        key=lambda x: x.get("priority", 99),
    )
    n = len(obs)
    items = []
    for o in obs:
        title = ob_title(o, data)
        items.append(
            f'<a href="#ob-{esc(o["id"])}">{esc(o["id"])} {esc(title)}</a>'
        )
    return (
        f'<nav class="judge-strip" id="judge-strip" aria-label="Need your judgment">'
        f'<p class="judge-lead">Need your judgment · {n} items · '
        f'<a href="#queue">open reviewer queue</a></p>'
        f'<p class="judge-list">{" · ".join(items) or "None recorded."}</p>'
        f"</nav>"
    )


def render_central_edges(data: dict, model: Model) -> str:
    cids = central_edge_ids(data)
    need, quiet = [], []
    for i in cids:
        if i not in model.by_id:
            continue
        e = model.by_id[i]
        (quiet if e["status"] in DISCHARGED else need).append(e)
    parts = [compact_edge(e, data) for e in need]
    if quiet:
        n = len(quiet)
        label = "step" if n == 1 else "steps"
        parts.append(
            f'<p class="discharged-line" id="discharged-count">'
            f"✓ {n} machine-discharged {label} on this path.</p>"
            f'<details class="discharged" id="discharged-steps">'
            f"<summary>✓ {n} machine-discharged {label}</summary>"
            f'{"".join(compact_edge(e, data) for e in quiet)}'
            f"</details>"
        )
    return "".join(parts)


def render_eq_drawer(model: Model) -> str:
    rows = []
    for eq in model.eqs:
        st = model.status_of[eq["public"]]
        href = model.href_of[eq["public"]]
        if href.startswith(("#edge-", "#claim-", "#ob-")):
            dest_html = f' · <a href="{esc(href)}">{esc(href)}</a>'
        else:
            dest_html = ""
        label_html = f" · {esc(eq['tex_label'])}" if eq.get("tex_label") else ""
        cue_html = display_cue(eq.get("cue") or "")
        rows.append(
            f'<div class="eq-rec" id="eq-detail-{esc(eq["id"])}" '
            f'data-status="{esc(st)}" data-hue="{esc(hue_of(st))}">'
            f"<strong>{esc(eq['public'])}</strong> "
            f"<code>{esc(eq['id'])}</code> · {esc(eq['section'])} · {chip(st)}"
            f"{dest_html}{label_html}{cue_html}"
            f"</div>"
        )
    return (
        f'<details class="drawer" id="eq-drawer">'
        f"<summary>Equation records ({len(model.eqs)}) — provenance, not a second map</summary>"
        f"<p class=\"one-line\">Inventory cues are cleaned for MathJax the same way as the ledger. "
        f"Full source remains in <code>evidence/audit.json</code>.</p>"
        f'{"".join(rows)}</details>'
    )


def inv_counts(data: dict) -> dict:
    inv = data.get("inventory") or {}
    v2 = inv.get("v2") or {}
    eqs = inv.get("equations") or []
    return {
        "total": v2.get("total") or len(eqs),
        "main": v2.get("main") or sum(1 for e in eqs if e.get("section") == "main"),
        "appendix": v2.get("appendix") or sum(
            1 for e in eqs if str(e.get("section", "")).startswith("appendix")
        ),
    }


def render_html(data: dict) -> str:
    model = Model(data)
    s = data.get("summary") or {}
    inv = inv_counts(data)
    s.setdefault("overall_state", "AUDIT_INCOMPLETE")
    s.setdefault("claim_count", len(data.get("claims") or []))
    s.setdefault("relations_reconstructed", len(data.get("edges") or []))
    s.setdefault("machine_certified_edges", sum(
        1 for e in data.get("edges") or [] if e.get("status") in {"EXACT", "EXACT_IF_ASSUMPTIONS"}
    ))
    s.setdefault("assumption_dependent_edges", sum(
        1 for e in data.get("edges") or [] if e.get("status") == "EXACT_IF_ASSUMPTIONS"
    ))
    s.setdefault("unresolved_load_bearing", sum(
        1 for e in data.get("edges") or []
        if e.get("load_bearing") and e.get("status") not in {"EXACT", "EXACT_IF_ASSUMPTIONS", "STRUCTURAL"}
    ))
    counts = model.hue_counts()
    cids = central_edge_ids(data)
    chain = presentation(data).get("central_path") or " → ".join(
        f"{model.by_id[i]['from_eq']} → {model.by_id[i]['to_eq']}"
        for i in cids if i in model.by_id
    )

    c2_edges = render_central_edges(data, model)
    other_ids = {e["id"] for e in model.edges if e["id"] not in set(cids)}
    all_rows = "".join(
        edge_row(e, with_id=e["id"] in other_ids) for e in model.edges
    )

    flex = counts.copy()
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

    authors = esc(s.get("authors") or data.get("paper", {}).get("authors") or "")
    return f"""<!DOCTYPE html>
<html lang="en" data-audit-key="{esc(data["paper"]["id"])}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence ledger — {authors}, arXiv:{esc(data["paper"]["id"])}</title>
<style>
{CSS}
</style>
<script>
window.MathJax={{tex:{{inlineMath:[["\\\\(","\\\\)"]],displayMath:[["\\\\[","\\\\]"]],processEnvironments:false}},options:{{skipHtmlTags:["script","noscript","style","textarea","pre","code"]}}}};
</script>
<script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-chtml.js"></script>
</head>
<body><div class="wrap">
<header class="mast">
<p class="kicker">Evidence ledger</p>
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
<p>Local certification is not a paper-level certificate.</p>
</div>

{render_judge_strip(data)}

{stack}
<div class="tone-key">
<span class="tone ok">Dark green = Exact · hatched = Exact if A</span>
<span class="tone cite">Blue = structural / cited rule</span>
<span class="tone inspect">Orange = inspect (gap, review, remainder, numerics)</span>
<span class="tone wrong">Dark red = local residual ≠ 0</span>
</div>

{render_map(model)}
</header>

<main id="main">
<section id="claims">
<h2>Major claims</h2>
{render_claims(data, model)}
</section>

<section id="graph">
<h2>Central derivation</h2>
<p class="chain">{esc(chain) if chain else "Load-bearing reconstructed edges"}</p>
<p class="one-line">Reconstructed path, not a certificate. Adjacent numbering is not a derivation.</p>
{c2_edges}
</section>

<section id="queue">
<h2>Reviewer queue</h2>
<p class="one-line">{ACCEPT_WARN}</p>
{render_queue(data)}
</section>

{render_eq_drawer(model)}

<details class="drawer" id="ledger">
<summary>Full relation ledger ({len(model.edges)}) — provenance</summary>
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
</details>
</main>

<footer>
<p><strong>Presentation is not a certificate.</strong> {esc(data.get("v1_frozen_note") or "Statuses are copied from audit.json.")}</p>
<p>Canonical model: <code>audit.json</code>. Markdown twin: <code>audit.md</code>.</p>
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


def md_edge(e: dict) -> str:
    return (
        f"| `{e['id']}` | {md_escape_cell(e['from_eq'])} | {md_escape_cell(e['to_eq'])} | "
        f"{md_escape_cell(e['transformation'])} | {md_escape_cell('; '.join(e['assumptions']))} | "
        f"`{e['status']}` | {md_escape_cell(e['locator'])} |"
    )


def render_markdown(data: dict) -> str:
    model = Model(data)
    s = data.get("summary") or {}
    s.setdefault("overall_state", "AUDIT_INCOMPLETE")
    s.setdefault("claim_count", len(data.get("claims") or []))
    s.setdefault("relations_reconstructed", len(data.get("edges") or []))
    s.setdefault("machine_certified_edges", 0)
    s.setdefault("assumption_dependent_edges", 0)
    s.setdefault("unresolved_load_bearing", 0)
    inv = inv_counts(data)
    counts = model.hue_counts()
    cids = central_edge_ids(data)
    chain = presentation(data).get("central_path") or " → ".join(cids)
    lines = [
        f"# Paper audit — {data['paper']['id']}",
        "",
        f"**{data['paper']['title']}**",
        "",
        f"Authors: {s.get('authors') or data.get('paper', {}).get('authors') or ''}",
        "",
        f"Source: {data['paper']['source']}",
        "",
        "**Presentation is not a certificate.**",
        "",
        "Local certification is not a paper-level certificate.",
        "",
        f"- Overall state: `{s['overall_state']}`",
        f"- Claims: {s['claim_count']}",
        f"- Numbered equations: {inv['total']} = main {inv['main']} + appendix {inv['appendix']}",
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
        "## Need your judgment",
        "",
        f"{len(data.get('reviewer_obligations') or [])} reviewer items. See Reviewer queue.",
        "",
    ]
    for o in sorted(
        data.get("reviewer_obligations") or [],
        key=lambda x: x.get("priority", 99),
    ):
        title = ob_title(o, data)
        lines.append(f"- {o['id']} · {title} (`{o['status']}`)")
    lines += [
        "",
        (data.get("inventory") or {}).get("correction") or "",
        "",
        "## Equation map",
        "",
        "`→` is a reconstructed derivation edge. `⋯` is consecutive numbering only.",
        "",
    ]
    by_sec: dict[str, list] = {}
    for eq in model.eqs:
        by_sec.setdefault(eq["section"], []).append(eq)
    for sec, eqs in by_sec.items():
        title = LANE_TITLE.get(sec, sec)
        lines += [f"### {title} ({len(eqs)})", "", _md_map_line(model, eqs), ""]

    lines += ["## Major claims", ""]
    for c in data["claims"]:
        view = claim_view(c, data)
        lines += [
            f"### {c['id']} — {STATUS_LABEL.get(c['status'], c['status'])}",
            "",
            view.get("line") or c["statement"],
            "",
        ]
        if view.get("note"):
            lines += [view["note"], ""]
        if view.get("path"):
            lines.append(f"- **Path:** {view['path']}")
        if view.get("assumptions"):
            lines.append(f"- **Assumptions:** {view['assumptions']}")
        lines += [
            f"- **Blocks:** {', '.join(c.get('unresolved') or []) or '—'}",
            f"- **Status:** `{c['status']}`",
            "",
        ]

    lines += [
        "## Central derivation",
        "",
        chain,
        "",
        "Load-bearing path reconstructed from the source, not a certificate.",
        "",
        "| From | To | Operation | Status |",
        "|---|---|---|---|",
    ]
    quiet_md = []
    for i in cids:
        if i not in model.by_id:
            continue
        e = model.by_id[i]
        op = edge_op(e, data)
        row = (
            f"| {md_escape_cell(e['from_eq'])} | {md_escape_cell(e['to_eq'])} | "
            f"{md_escape_cell(op)} | `{e['status']}` |"
        )
        if e["status"] in DISCHARGED:
            quiet_md.append(row)
        else:
            lines.append(row)
    if quiet_md:
        n = len(quiet_md)
        label = "step" if n == 1 else "steps"
        lines += [
            "",
            f"✓ {n} machine-discharged {label} on this path.",
            "",
            "| From | To | Operation | Status |",
            "|---|---|---|---|",
        ]
        lines.extend(quiet_md)

    lines += [
        "",
        "## Reviewer queue",
        "",
        ACCEPT_WARN,
        "",
    ]
    for o in sorted(data.get("reviewer_obligations") or [], key=lambda x: x.get("priority", 99)):
        title = ob_title(o, data)
        need = ob_need(o, data)
        src = o.get("paper_evidence") or o.get("locator") or ""
        lines += [
            f"### {o['id']} · {title} — `{o['status']}`",
            "",
            f"**Need to verify.** {need}",
            "",
        ]
        if src:
            lines += [f"**Source.** {src}", ""]
        lines += [
            f"**Blocks.** {', '.join(o['blocks'])}",
            "",
        ]

    lines += [
        "## Provenance",
        "",
        "The visible layers above are a presentation of this model. "
        "Nothing below changes a status.",
        "",
        "### Full claims",
        "",
    ]
    for c in data["claims"]:
        lines += [
            f"#### {c['id']} — `{c['status']}`",
            "",
            c["statement"],
            "",
            f"- **Locator:** {c.get('locator') or '—'}",
            f"- **Supporting equations:** {', '.join(c.get('supporting_equations') or [])}",
            f"- **Appendix chain:** {' → '.join(c.get('appendix_chain') or [])}",
            f"- **Assumptions:** {'; '.join(c.get('assumptions') or [])}",
            f"- **Unresolved obligations:** {', '.join(c.get('unresolved') or [])}",
            f"- **Downstream:** {c.get('downstream') or '—'}",
            "",
        ]
        for b in c.get("blockers") or []:
            lines.append(f"- Blocker: {b}")
        lines.append("")

    lines += [
        "### Central-chain edges",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]
    for i in cids:
        if i in model.by_id:
            e = model.by_id[i]
            lines.append(md_edge(e))
            if e.get("target_tex"):
                lines += ["", f"$$ {e['target_tex']} $$", ""]
            elif e.get("source_tex"):
                lines += ["", f"$$ {e['source_tex']} $$", ""]

    lines += [
        "",
        "### Other reconstructed edges",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in model.edges:
        if e["id"] not in set(cids):
            lines.append(md_edge(e))

    lines += [
        "",
        "### Reviewer obligations (full)",
        "",
    ]
    for o in sorted(data.get("reviewer_obligations") or [], key=lambda x: x.get("priority", 99)):
        lines += [
            f"#### {o['id']} (priority {o['priority']}) — `{o['status']}`",
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
        ]

    lines += ["### Numerical evidence", ""]
    for n in data.get("numerical_evidence") or []:
        lines += [
            f"#### {n['id']} — `{n['evidence_type']}`",
            "",
            f"- Quantity: {n['quantity']}",
            f"- Supports: {n['supports']}",
            f"- Regime: {n['regime']}",
            f"- Does not prove: {n['proves_not']}",
            f"- Locator: {n['locator']}",
            "",
        ]

    lines += [
        "### Equation records",
        "",
        f"Method: {(data.get('inventory') or {}).get('method') or 'numbered outer equation rows'}",
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
    for k, v in ((data.get("inventory") or {}).get("main_public_map") or {}).items():
        lines.append(f"| {k} | {md_escape_cell(v)} |")

    lines += [
        "",
        "### Full relation ledger",
        "",
        "| ID | From | To | Transformation | Assumptions | Status | Locator |",
        "|---|---|---|---|---|---|---|",
    ]
    for e in model.edges:
        lines.append(md_edge(e))

    lines += [
        "",
        data.get("v1_frozen_note") or "Statuses are copied from audit.json.",
        "",
        "Canonical model: `audit.json`. HTML twin: `audit.html`.",
        "",
    ]
    return "\n".join(lines) + "\n"


def semantic_index(data: dict) -> dict:
    return {
        "claims": {c["id"]: c["status"] for c in data["claims"]},
        "edges": {e["id"]: e["status"] for e in data["edges"]},
        "obligations": {
            o["id"]: o["status"] for o in data.get("reviewer_obligations") or []
        },
        "inventory_total": inv_counts(data)["total"],
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
    if re.search(r"0\*|ws-zero", html_page):
        err.append("HTML contains invalid 0*")
    if 'id="map-sec"' not in html_page.split('id="main"')[0]:
        err.append("coloured map is not on the first screen")
    if "class=\"stack\"" not in html_page and 'class="stack"' not in html_page:
        err.append("HTML missing colour stack")
    if ">Sign<" in html_page:
        err.append("HTML contains Sign button")
    for e in data["edges"]:
        if e["status"] == "EXACT" and "asymptotic" in (e.get("transformation") or ""):
            err.append(f"{e['id']} Exact on asymptotic")
    hrefs = re.findall(r'class="eq-node[^"]*" id="map-[^"]+" href="([^"]+)"', html_page)
    if hrefs and all(h == "#obligation-table" for h in hrefs):
        err.append("all map chips still point at #obligation-table")
    if "Local certification is not a paper-level certificate." not in html_page:
        err.append("missing one-sentence certificate warning")
    if "<strong>Where.</strong>" in html_page:
        err.append("claim cards still dump Where.")
    if "<h2>Numerical evidence" in html_page:
        err.append("standalone numerical section still visible")
    if "<h2>E. Equation detail</h2>" in html_page:
        err.append("giant equation-detail heading still visible")
    n_eq = html_page.count('id="eq-detail-')
    n_inv = inv_counts(data)["total"]
    if n_eq != n_inv:
        err.append(f"equation-record ids: {n_eq} != inventory {n_inv}")
    if '["$","$"]' in html_page:
        err.append("MathJax still uses $ delimiters")
    if "Human acceptance records reviewer judgment" not in html_page:
        err.append("missing queue-level accept warning")
    if "it does not change a machine status to Exact." not in html_page:
        err.append("accept warning must not convert Accept into Exact")
    if 'id="judge-strip"' not in html_page.split('id="main"')[0]:
        err.append("Need-your-judgment strip missing from first screen")
    if "class=\"ob-source\">Source:" not in html_page and 'class="ob-source">Source:' not in html_page:
        if data.get("reviewer_obligations"):
            err.append("queue cards missing Source")
    if "tex-fallback" not in html_page:
        err.append("missing LaTeX fallback for math-render failure")
    if "Main + appendix map A–E" in html_page:
        err.append("generic renderer must not hard-code Anan map title A–E")
    return err


def main() -> int:
    ap = argparse.ArgumentParser(description="Render V3.1 audit.html + audit.md")
    ap.add_argument("--audit", required=True, type=Path, help="audit.json")
    ap.add_argument("--out", required=True, type=Path, help="output directory")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    data = json.loads(args.audit.read_text(encoding="utf-8"))
    html_page = render_html(data)
    md_page = render_markdown(data)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "audit.html").write_text(html_page, encoding="utf-8")
    (args.out / "audit.md").write_text(md_page, encoding="utf-8")
    err = check_rendered(data, html_page, md_page)
    print("wrote", args.out / "audit.html", len(html_page), args.out / "audit.md", len(md_page))
    if err:
        print("CHECK_FAIL")
        for e in err:
            print(" -", e)
        return 1 if args.check else 0
    print("CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
