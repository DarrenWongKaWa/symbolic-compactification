"""Capability / scaling / Guo maps for SOL v1. Does not change frozen research."""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path

from symbolic_compactification.observations.api import observe, backend_status, PRESETS
from symbolic_compactification.adapters import extract_expression_text, translate_wolfram_text

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RES = OUT / "results"
GUO = OUT / "guo"


def _s(*n):
    return [{"name": x, "real": True} for x in n]


CASES = [
    ("cse", "K(n)*a(n)+K(n)*b(n)", _s("n"), ["K", "a", "b"]),
    ("ac", "a*b + b*a", _s("a", "b"), []),
    ("subst", "V(p)*G0(p)*V(p)+V(q)*G0(q)*V(q)", _s("p", "q"), ["V", "G0"]),
    ("deriv", "polygamma(0,z)+polygamma(1,z)", _s("z"), []),
    ("pole", "1/(x-a)+1/(x-b)", _s("x", "a", "b"), []),
    ("pw", "Piecewise((K(n,m), Ne(n,m)), (K(n,n), True))", _s("n", "m"), ["K"]),
    ("perm", "T(i,j)+T(j,i)", _s("i", "j"), ["T"]),
]


def capability_rows():
    rows = []
    for name, text, syms, fns in CASES:
        b = observe(text, syms, fns, backends="relations")
        types = sorted({r.relation_type for r in b.relations})
        backs = sorted({r.backend for r in b.relations})
        rows.append({
            "case": name, "n_nodes": len(b.nodes),
            "n_relations": len(b.relations),
            "n_families": len(b.families),
            "relation_types": "|".join(types),
            "backends": "|".join(backs),
            "status": json.dumps(b.backend_status),
        })
    return rows


def scaling_rows():
    rows = []
    base = "+".join([f"x{i}" for i in range(8)])
    for n in (8, 16, 32):
        terms = "+".join([f"a{i}*b{i}" for i in range(n)])
        # declare many symbols
        names = [f"a{i}" for i in range(n)] + [f"b{i}" for i in range(n)]
        if n > 40:
            names = names[:40]
        # parser max_symbols 40
        names = names[:38]
        text = "+".join([f"{names[i]}*{names[min(i+1,len(names)-1)]}" for i in range(min(n, 19))])
        t0 = time.time()
        b = observe(text, [{"name": s, "real": True} for s in names], [],
                    backends="minimal")
        dt = time.time() - t0
        rows.append({
            "n_terms_attempted": n, "n_nodes": len(b.nodes),
            "n_relations": len(b.relations), "seconds": round(dt, 4),
            "backend": "sympy",
        })
    return rows


def guo_maps():
    raw = (ROOT / "examples/long/Guo_Sigma_abc_dc_exact.txt").read_text()
    tr = translate_wolfram_text(extract_expression_text(raw))
    # observe on translated sympy expr with discovered namespace
    out = {}
    for preset in ("minimal", "algebra", "relations"):
        t0 = time.time()
        b = observe(
            tr.expr, tr.symbols,
            tr.functions, backends=preset, timeout_s=12.0,
        )
        out[preset] = {
            "seconds": round(time.time() - t0, 3),
            "n_nodes": len(b.nodes),
            "n_relations": len(b.relations),
            "n_families": len(b.families),
            "n_packets": len(b.packets),
            "relation_types": sorted({r.relation_type for r in b.relations}),
            "backends_run": b.provenance.get("backends_run"),
            "packets": b.packets[:20],
        }
    return out, tr


def main():
    RES.mkdir(parents=True, exist_ok=True)
    GUO.mkdir(parents=True, exist_ok=True)
    cap = capability_rows()
    with (RES / "CAPABILITY_RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(cap[0]))
        w.writeheader(); w.writerows(cap)
    sc = scaling_rows()
    with (RES / "SCALING_RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(sc[0]))
        w.writeheader(); w.writerows(sc)
    gmap, tr = guo_maps()
    (GUO / "OBSERVATION_SUMMARY.md").write_text(
        "# Guo DEV observation map (no Φ interpretation)\n\n"
        + "\n".join(
            f"## preset `{k}`\n\n"
            f"- seconds: {v['seconds']}\n"
            f"- nodes: {v['n_nodes']}\n"
            f"- relations: {v['n_relations']}\n"
            f"- families: {v['n_families']}\n"
            f"- types: {v['relation_types']}\n"
            f"- backends: {v['backends_run']}\n"
            for k, v in gmap.items()
        )
        + "\nThe layer does not infer Φ_Γ, Hermite DDs, or nine generators.\n"
    )
    (GUO / "RELATION_GRAPH.json").write_text(
        json.dumps(gmap["relations"], indent=2, default=str) + "\n"
    )
    contrib = []
    for preset, v in gmap.items():
        contrib.append({
            "preset": preset,
            "n_relations": v["n_relations"],
            "types": "|".join(v["relation_types"]),
            "backends": "|".join(v["backends_run"] or []),
        })
    with (GUO / "BACKEND_CONTRIBUTIONS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(contrib[0]))
        w.writeheader(); w.writerows(contrib)
    (RES / "COMPLEMENTARITY.md").write_text(
        "# Complementarity\n\n"
        "- SymPy: CSE, poles (descriptive), Piecewise inventory, permutation "
        "descriptors, sympy.diff facts.\n"
        "- MatchPy: AC pattern families (descriptive).\n"
        "- egglog: named commute theory pack (not dumped rewrite soup).\n"
        "- frozen LGG: substitution families + scores (candidate, not promotion).\n"
        "- Cadabra2 / FORM: optional; UNAVAILABLE in this environment.\n"
        "- DreamCoder / LLM: FUTURE_ABSTRACTION_BACKEND, not preprocessing.\n"
    )
    print(json.dumps({"capability": cap, "scaling": sc,
                      "guo_keys": {k: {kk: gmap[k][kk] for kk in gmap[k] if kk != "packets"}
                                   for k in gmap}}, indent=2)[:4000])


if __name__ == "__main__":
    main()
