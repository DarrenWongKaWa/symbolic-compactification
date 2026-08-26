"""DEV-only structure-discovery experiments. Must not read test gold for tuning.

Writes research/structure_discovery/dev/RESULTS.csv and DEV_DECISION.md.
"""
from __future__ import annotations

import csv
import json
import time
from collections import Counter
from pathlib import Path

from research.structure_discovery.prototype.baselines import (
    run_b0,
    run_b1,
    run_b6_direct,
    run_b9,
    run_b9_conservative,
    run_b9_no_obs,
)
from research.structure_discovery.prototype.build_benchmark import OUT, write_benchmark
from research.structure_discovery.prototype.downstream import score_downstream
from research.structure_discovery.prototype.evaluator import score_run
from research.structure_discovery.prototype.leakage import context_leaks_gold_names

ROOT = Path(__file__).resolve().parents[3]
DEV_OUT = ROOT / "research" / "structure_discovery" / "dev"


def load_split(split: str) -> list[dict]:
    write_benchmark()
    items = []
    for p in sorted((OUT / split).glob("*.json")):
        items.append(json.loads(p.read_text()))
    return items


def _flat(score: dict, run: dict, method: str) -> dict:
    row = dict(score)
    row["method"] = method
    row["n_hypotheses"] = run.get("n_hypotheses")
    row["n_zero"] = run.get("n_zero")
    row["n_nonzero"] = run.get("n_nonzero")
    row["n_unknown"] = run.get("n_unknown")
    row["false_promotion"] = run.get("false_promotion")
    row["d_attempted"] = "|".join(run.get("d_attempted") or [])
    row["d_certified"] = "|".join(run.get("d_certified") or [])
    row["types"] = "|".join(run.get("hypothesis_types") or [])
    return row


def run_matrix(items: list[dict]) -> tuple[list[dict], list[dict]]:
    runners = [
        ("B0", run_b0),
        ("B1", run_b1),
        ("B6_direct", run_b6_direct),
        ("B9_full", run_b9),
        ("B9_conservative", run_b9_conservative),
        ("B9_no_obs", run_b9_no_obs),
        ("B9_no_perm", lambda it: run_b9(it, feature_mask={"permutation": False})),
        ("B9_no_repeated", lambda it: run_b9(it, feature_mask={"repeated": False})),
        ("B9_no_denoms", lambda it: run_b9(it, feature_mask={"denominators": False})),
    ]
    rows = []
    dumps = []
    for item in items:
        leaks = context_leaks_gold_names(item)
        if leaks:
            raise RuntimeError(f"context leaks gold names {leaks} on {item['id']}")
        for name, fn in runners:
            t0 = time.time()
            try:
                run = fn(item)
            except Exception as exc:
                run = {
                    "baseline": name, "hypothesis_types": [], "hypotheses": [],
                    "n_hypotheses": 0, "n_zero": 0, "n_nonzero": 0, "n_unknown": 1,
                    "false_promotion": False, "d_attempted": [], "d_certified": [],
                    "graph": {"nodes": []}, "certified_structured": item["current"],
                    "error": f"{type(exc).__name__}:{exc}",
                }
            run["wall_s"] = round(time.time() - t0, 4)
            run["id"] = item["id"]
            if run.get("error"):
                print("ERR", item["id"], name, run["error"], flush=True)
            print(f"{item['id']:28} {name:18} {run['wall_s']:.2f}s nZ={run.get('n_zero')}", flush=True)
            sc = score_run(item, run)
            ds = score_downstream(item, run)
            row = _flat(sc, run, name)
            row["wall_s"] = run["wall_s"]
            row["n_named_aux"] = ds.get("n_named_aux")
            row["symmetry_exposed"] = ds.get("symmetry_exposed")
            row["kernel_exposed"] = ds.get("kernel_exposed")
            row["swap_match"] = ds.get("swap_match")
            rows.append(row)
            dumps.append({
                "id": item["id"], "method": name, "score": sc, "downstream": ds,
                "n_zero": run.get("n_zero"), "types": run.get("hypothesis_types"),
                "d_certified": run.get("d_certified"),
                "false_promotion": run.get("false_promotion"),
                "certified_structured": run.get("certified_structured"),
            })
    return rows, dumps


def summarize(rows: list[dict]) -> dict:
    by_m: dict[str, list[dict]] = {}
    for r in rows:
        by_m.setdefault(r["method"], []).append(r)
    out = {}
    for m, rs in by_m.items():
        pos = [r for r in rs if r["polarity"] == "positive"]
        neg = [r for r in rs if r["polarity"] == "negative"]
        out[m] = {
            "n": len(rs),
            "pos_type_hit": sum(bool(r["axis_A_type_hit"]) for r in pos) / max(len(pos), 1),
            "pos_gold_certified": sum(bool(r["axis_C_gold_type_certified"]) for r in pos) / max(len(pos), 1),
            "neg_unsafe_merge": sum(bool(r["axis_C_unsafe_merge"]) for r in neg),
            "false_promotion": sum(bool(r["axis_C_false_promotion"]) for r in rs),
            "mean_n_zero": sum(int(r["n_zero"] or 0) for r in rs) / max(len(rs), 1),
            "mean_n_nonzero": sum(int(r["n_nonzero"] or 0) for r in rs) / max(len(rs), 1),
            "d3plus_attempted": sum(
                any(x in (r.get("d_attempted") or "") for x in ("D3", "D4", "D5"))
                for r in rs
            ),
            "d3plus_certified": sum(
                any(x in (r.get("d_certified") or "") for x in ("D3", "D4", "D5"))
                for r in rs
            ),
        }
    return out


def write_dev_decision(summary: dict, rows: list[dict]) -> str:
    b9 = summary.get("B9_full", {})
    b6 = summary.get("B6_direct", {})
    b1 = summary.get("B1", {})
    noobs = summary.get("B9_no_obs", {})
    lines = [
        "# DEV decision (structure discovery)",
        "",
        "Split: DEV only. Test items were generated but **not used to select**",
        "features, thresholds, or constructors.",
        "",
        "## Headline",
        "",
        f"- B9 type-hit (positive): {b9.get('pos_type_hit')}",
        f"- B6 direct type-hit (positive): {b6.get('pos_type_hit')}",
        f"- B1 type-hit (positive): {b1.get('pos_type_hit')}",
        f"- B9 gold-type certified (positive): {b9.get('pos_gold_certified')}",
        f"- B9 unsafe merges on negatives: {b9.get('neg_unsafe_merge')}",
        f"- B9 false promotions: {b9.get('false_promotion')}",
        f"- B9 D3+ attempted / certified counts: "
        f"{b9.get('d3plus_attempted')} / {b9.get('d3plus_certified')}",
        f"- B9_no_obs type-hit: {noobs.get('pos_type_hit')}",
        "",
        "## Did the intervention attack the diagnosed bottleneck?",
        "",
        "The diagnosed bottleneck was *shallow proposal* (expressions, not",
        "typed structure). B9 emits typed hypotheses; B1/B6 generally do not",
        "match gold *types* even when they rewrite algebra.",
        "",
        "## Causal check",
        "",
        "If B9 ≉ B9_no_obs on type-hit, observations matter.",
        "If B9 > B6 on type-hit, decomposed search helps the *type* axis.",
        "If unsafe_merge stays 0, C3 is supported on DEV.",
        "",
        "## Summary table",
        "",
        "```json",
        json.dumps(summary, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    DEV_OUT.mkdir(parents=True, exist_ok=True)
    items = load_split("dev")
    rows, dumps = run_matrix(items)
    summary = summarize(rows)
    fields = sorted({k for r in rows for k in r})
    with (DEV_OUT / "RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (DEV_OUT / "RESULTS.json").write_text(json.dumps(dumps, indent=2) + "\n")
    (DEV_OUT / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    (DEV_OUT / "DEV_DECISION.md").write_text(write_dev_decision(summary, rows))
    # type diversity
    types = Counter()
    for r in rows:
        if r["method"] == "B9_full":
            for t in (r.get("types") or "").split("|"):
                if t:
                    types[t] += 1
    (DEV_OUT / "HYPOTHESIS_DIVERSITY.json").write_text(
        json.dumps(types, indent=2) + "\n"
    )
    print(json.dumps({"n_dev": len(items), "n_rows": len(rows), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
