"""Aggregate DEV matrix metrics. Task-weighted and cluster-weighted."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from research.assumption_complete_representation.eval.pack_data import (
    CLUSTER_OF,
    CORE,
    P4_ELIGIBLE,
)

HERE = Path(__file__).resolve().parents[1]
RUNS = HERE / "runs" / "dev_matrix"


def load_runs(model: str = "deepseek-v4-pro") -> list[dict]:
    out = []
    if not RUNS.is_dir():
        return out
    for p in sorted(RUNS.glob("*.json")):
        if p.name.endswith(".tmp"):
            continue
        rec = json.loads(p.read_text())
        if rec.get("model") and model not in str(rec.get("model")):
            continue
        if rec.get("split") and rec.get("split") != "DEV":
            continue
        out.append(rec)
    return out


def _best(rec: dict) -> dict:
    return (rec.get("eval") or {}).get("best") or {}


def cond_task_metrics(runs: list[dict]) -> dict[str, Any]:
    by: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for r in runs:
        if r.get("task_id") not in CORE:
            continue
        by[(r["task_id"], r["condition"])].append(r)
    rows = []
    for (tid, cond), rs in sorted(by.items()):
        n = len(rs)
        def rate(pred) -> float:
            return sum(1 for r in rs if pred(r)) / n if n else 0.0
        type_correct = rate(lambda r: (r.get("eval") or {}).get("any_type_match"))
        op_s = rate(lambda r: (r.get("eval") or {}).get("any_operational_success"))
        grounded = rate(lambda r: _best(r).get("G") == "G_OK")
        compile_ok = rate(lambda r: _best(r).get("C") == "C_OK")
        zero = rate(lambda r: _best(r).get("V") == "ZERO")
        nonzero = rate(lambda r: _best(r).get("V") == "NONZERO")
        unknown = rate(lambda r: _best(r).get("V") == "UNKNOWN")
        type_only = rate(lambda r: (r.get("eval") or {}).get("any_type_only"))
        taut = rate(lambda r: (r.get("eval") or {}).get("any_tautological"))
        toks = [((r.get("usage") or {}).get("total_tokens") or 0) for r in rs]
        lat = [r.get("latency_s") or 0 for r in rs]
        pdepths = [(_best(r).get("PROPOSED_DEPTH")) for r in rs]
        cdepths = [(_best(r).get("CERTIFIED_DEPTH")) for r in rs]
        pnum = [d for d in pdepths if d is not None]
        cnum = [d for d in cdepths if d is not None]
        rows.append({
            "task_id": tid,
            "cluster_id": CLUSTER_OF.get(tid),
            "condition": cond,
            "n_seeds": n,
            "TYPE_CORRECT_RATE": round(type_correct, 4),
            "OPERATIONAL_SUCCESS_RATE": round(op_s, 4),
            "GROUNDED_RATE": round(grounded, 4),
            "COMPILE_RATE": round(compile_ok, 4),
            "ZERO_RATE": round(zero, 4),
            "NONZERO_RATE": round(nonzero, 4),
            "UNKNOWN_RATE": round(unknown, 4),
            "TYPE_ONLY_RATE": round(type_only, 4),
            "TAUTOLOGICAL_RATE": round(taut, 4),
            "mean_PROPOSED_DEPTH": round(sum(pnum) / len(pnum), 3) if pnum else None,
            "mean_CERTIFIED_DEPTH": round(sum(cnum) / len(cnum), 3) if cnum else None,
            "max_CERTIFIED_DEPTH": max(cnum) if cnum else None,
            "mean_tokens": round(sum(toks) / n, 1) if n else 0,
            "mean_latency_s": round(sum(lat) / n, 2) if n else 0,
        })
    return rows


def weighted(rows: list[dict], *, cluster: bool) -> dict[str, dict]:
    """Average rates over tasks or over clusters (mean of cluster-member means)."""
    by_cond: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)

    def avg(items, key):
        vals = [i[key] for i in items if i.get(key) is not None]
        return round(sum(vals) / len(vals), 4) if vals else None

    keys = [
        "TYPE_CORRECT_RATE", "OPERATIONAL_SUCCESS_RATE", "GROUNDED_RATE",
        "COMPILE_RATE", "ZERO_RATE", "NONZERO_RATE", "UNKNOWN_RATE",
        "TYPE_ONLY_RATE", "TAUTOLOGICAL_RATE", "mean_PROPOSED_DEPTH",
        "mean_CERTIFIED_DEPTH", "mean_tokens", "mean_latency_s",
    ]
    out = {}
    for cond, items in by_cond.items():
        if cluster:
            by_cl: dict[str, list[dict]] = defaultdict(list)
            for it in items:
                by_cl[it["cluster_id"]].append(it)
            reduced = []
            for cl, mems in by_cl.items():
                red = {"cluster_id": cl, "condition": cond}
                for k in keys:
                    red[k] = avg(mems, k)
                reduced.append(red)
            items = reduced
        out[cond] = {k: avg(items, k) for k in keys}
        out[cond]["n_units"] = len(items)
    return out


def main() -> dict:
    runs = load_runs()
    rows = cond_task_metrics(runs)
    return {
        "n_runs": len(runs),
        "per_task_condition": rows,
        "TASK_WEIGHTED": weighted(rows, cluster=False),
        "CLUSTER_WEIGHTED": weighted(rows, cluster=True),
        "P4_ELIGIBLE": P4_ELIGIBLE,
        "guo": False,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
