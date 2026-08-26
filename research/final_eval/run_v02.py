#!/usr/bin/env python3
"""v0.2-hard evaluation: B0, B1, B4-unsafe, M0, Method v2.

Does not modify v0.1. Method v2 code is already frozen for this eval.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.method_v2.orchestrator import run_m0, run_method_v2
import sympy as _sympy

from symbolic_compactification import ZERO, parse_expression, verify_equivalent
from symbolic_compactification.budgets import BudgetExceeded, run_symbolic_operation
from symbolic_compactification.models import AdapterError

BENCH = ROOT / "benchmark_v0.2"
OUT = ROOT / "research/final_eval"


def load_items():
    for p in sorted(BENCH.rglob("*.json")):
        if p.name in {"schema.json", "freeze_manifest.json"}:
            continue
        d = json.loads(p.read_text())
        if d.get("task") == "compactify" and d.get("current"):
            yield d


def b4_unsafe(cur, symbols, functions):
    """Unrestricted CAS claim: ship simplify as the result (no promotion gate)."""
    try:
        expr = parse_expression(cur, symbols, functions=functions or None)
        if expr.atoms(_sympy.Sum, _sympy.Product):
            claimed = str(expr)
        else:
            try:
                claimed = str(run_symbolic_operation(
                    "simplify", _sympy.simplify, (expr,),
                    budget_key="simplify_seconds"))
            except (BudgetExceeded, Exception):
                claimed = str(expr)
    except AdapterError:
        claimed = cur
    vr = verify_equivalent(cur, claimed, symbols, functions=functions or None)
    return claimed, vr.verdict


def main():
    rows = []
    for it in load_items():
        cur, syms, fns = it["current"], it["symbols"], it.get("functions") or []
        m0 = run_m0(cur, syms, fns)
        m1 = run_method_v2(cur, syms, fns, max_steps=4)
        claimed, b4v = b4_unsafe(cur, syms, fns)
        b4_fp = b4v != ZERO and claimed != cur
        # B4 that "promotes" claimed even if not ZERO
        row = {
            "id": it["id"],
            "split": it.get("split"),
            "d_floor": it.get("d_floor", ""),
            "family": it.get("family", ""),
            "M0_zero": m0["n_zero"],
            "M1_zero": m1["n_zero"],
            "M1_named": m1["named_aux_zero"],
            "M1_extra": m1["extra_certified_after_first_zero"],
            "M0_fp": int(m0["false_promotion"]),
            "M1_fp": int(m1["false_promotion"]),
            "B4_verdict": b4v,
            "B4_would_false_promote": int(b4_fp),
            "M1_changed": int(m1["changed"]),
        }
        rows.append(row)
        print(row["id"], row["split"], "M1z", row["M1_zero"],
              "named", row["M1_named"], "B4", b4v, "B4fp", b4_fp)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "RESULTS.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (OUT / "RESULTS.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    test = [r for r in rows if r["split"] == "test"]
    print("TEST n", len(test),
          "M1_fp", sum(r["M1_fp"] for r in test),
          "B4_fp", sum(r["B4_would_false_promote"] for r in test),
          "M1_named", sum(r["M1_named"] for r in test))


if __name__ == "__main__":
    main()
