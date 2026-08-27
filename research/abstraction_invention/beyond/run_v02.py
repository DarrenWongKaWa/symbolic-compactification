"""v0.2 DEV/TEST matrix. Frozen B9 and frozen LGG imported, not edited."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from research.abstraction_invention.beyond.build_v02 import OUT, write
from research.abstraction_invention.beyond.invent_beyond import (
    b2_filtered_lgg,
    b3_canon_equal,
    b4_ac_lgg,
    b5_operator_graph,
)
from research.abstraction_invention.beyond.score import rank_records
from research.abstraction_invention.prototype.orchestrator import run_b9_frozen, run_inventor
from research.abstraction_invention.prototype.inventor import invent_from_parsed
from research.structure_discovery.prototype.leakage import proposer_view, assert_no_leakage
from symbolic_compactification.adapters import extract_expression_text, translate_wolfram_text

ROOT = Path(__file__).resolve().parents[3]


def load(split):
    write()
    return [json.loads(p.read_text()) for p in sorted((OUT / split).glob("*.json"))]


def eval_item(it: dict) -> dict:
    pub = proposer_view(it)
    assert_no_leakage(pub, extra_forbidden=("gold_mode", "gold_members", "expected_lgg_fail"))
    text, syms, fns = it["current"], it["symbols"], it.get("functions") or []
    mode, pol = it.get("gold_mode"), it.get("polarity")
    b9 = run_b9_frozen(it)
    lgg = run_inventor(it)
    filt = b2_filtered_lgg(text, syms, fns)
    alg = b3_canon_equal(text, syms, fns)
    ac = b4_ac_lgg(text, syms, fns)
    op = b5_operator_graph(text, syms, fns)

    def pos_alg():
        return pol == "positive" and mode == "algebraic_equivalence"

    def neg_alg():
        return pol == "negative" and mode == "algebraic_equivalence"

    hits = {
        "B0_b9": False,
        "B1_lgg": bool((lgg.get("n_certified_abstractions") or 0) > 0) and pol == "positive",
        "B2_filtered": bool(filt) and pol == "positive",
        "B3_canon": bool(alg) if pol == "positive" else (not alg),
        "B4_ac_lgg": any(r.get("exact_after_canon") or r.get("useful_lgg") for r in ac) if pol == "positive" else not any(r.get("exact_after_canon") for r in ac),
        "B5_operator": (op["n_derivative"] + op["n_permutation"] + op["n_algebraic"]) > 0 if pol == "positive" else (op["n_derivative"] == 0 and mode == "operator"),
        "B6_llm": None,
    }
    # mode-specific success
    if mode == "algebraic_equivalence":
        hits["target_B3"] = bool(alg) if pol == "positive" else (not alg)
        hits["target_B4"] = any(r.get("exact_after_canon") for r in ac) if pol == "positive" else not any(r.get("exact_after_canon") for r in ac)
        hits["target_B1"] = hits["B1_lgg"] if pol == "positive" else not hits["B1_lgg"]
    elif mode == "operator":
        hits["target_B5"] = (op["n_derivative"] > 0 or op["n_permutation"] > 0) if pol == "positive" else (op["n_derivative"] == 0)
        hits["target_B1"] = hits["B1_lgg"] if pol == "positive" else True
    else:
        hits["target_B5"] = False
        hits["target_B3"] = False

    return {
        "id": it["id"], "split": it["split"], "family": it["family"],
        "polarity": pol, "gold_mode": mode,
        "n_lgg": lgg.get("n_hypotheses"),
        "n_lgg_cert": lgg.get("n_certified_abstractions"),
        "n_filtered": len(filt),
        "n_canon_eq": len(alg),
        "n_ac": len(ac),
        "ac_exact": any(r.get("exact_after_canon") for r in ac),
        "n_deriv": op["n_derivative"],
        "n_perm": op["n_permutation"],
        "n_alg_edge": op["n_algebraic"],
        "hits": hits,
        "llm": "BLOCKED",
    }


def summarize(rows):
    out = {}
    for key in ("B3_canon", "B4_ac_lgg", "B5_operator", "B1_lgg"):
        # use target_* when present
        pass
    alg_pos = [r for r in rows if r["gold_mode"] == "algebraic_equivalence" and r["polarity"] == "positive"]
    alg_neg = [r for r in rows if r["gold_mode"] == "algebraic_equivalence" and r["polarity"] == "negative"]
    op_pos = [r for r in rows if r["gold_mode"] == "operator" and r["polarity"] == "positive"]
    op_neg = [r for r in rows if r["gold_mode"] == "operator" and r["polarity"] == "negative"]
    def frac(rs, pred):
        return f"{sum(1 for r in rs if pred(r))}/{len(rs)}"
    out["F2_pos_canon_eq"] = frac(alg_pos, lambda r: r["n_canon_eq"] > 0)
    out["F2_pos_ac_exact"] = frac(alg_pos, lambda r: r["ac_exact"])
    out["F2_pos_lgg_cert"] = frac(alg_pos, lambda r: (r["n_lgg_cert"] or 0) > 0)
    out["F2_neg_canon_none"] = frac(alg_neg, lambda r: r["n_canon_eq"] == 0)
    out["F3_pos_deriv_or_perm"] = frac(op_pos, lambda r: r["n_deriv"] > 0 or r["n_perm"] > 0)
    out["F3_pos_lgg_cert"] = frac(op_pos, lambda r: (r["n_lgg_cert"] or 0) > 0)
    out["F3_neg_no_deriv"] = frac(op_neg, lambda r: r["n_deriv"] == 0)
    out["llm"] = "BLOCKED"
    return out


def score_guo():
    raw = (ROOT / "examples/long/Guo_Sigma_abc_dc_exact.txt").read_text()
    rec = json.loads((ROOT / "research/abstraction_invention/case_studies/GUO.json").read_text())
    ranked = rank_records(rec.get("templates") or [])
    return [{
        "rank": i + 1,
        "operator": r.get("operator"),
        "template": r.get("template"),
        "S": r["score"]["S"],
        "gain": r["score"]["gain"],
        "depth": r["score"]["depth"],
        "keep": r["score"]["keep"],
        "family0": (r.get("family") or [""])[0][:80],
    } for i, r in enumerate(ranked)]


def main(split="dev"):
    write()
    dest = ROOT / "research/abstraction_invention" / ("dev_v02" if split == "dev" else "final_v02")
    dest.mkdir(parents=True, exist_ok=True)
    rows = [eval_item(it) for it in load(split)]
    fields = sorted({k for r in rows for k in r if k != "hits"})
    with (dest / "RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields + ["hits"])
        w.writeheader()
        for r in rows:
            row = {k: r.get(k) for k in fields}
            row["hits"] = json.dumps(r["hits"])
            w.writerow(row)
    summary = summarize(rows)
    if split == "dev":
        summary["guo_rank"] = score_guo()
    (dest / "SUMMARY.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2)[:4000])


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "dev")
