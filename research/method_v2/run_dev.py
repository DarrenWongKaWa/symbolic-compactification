#!/usr/bin/env python3
"""DEV validation M0 vs M1. Does not touch frozen ssc-bench-v0.1 test."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from research.method_v2.orchestrator import run_m0, run_method_v2

HARD = ROOT / "research/search_bottleneck/dev_hard"
OUT = ROOT / "research/method_v2"


def items():
    for p in sorted(HARD.glob("*.json")):
        if p.name == "manifest.json":
            continue
        d = json.loads(p.read_text())
        if not d.get("current"):
            continue
        yield d


def main():
    rows = []
    for it in items():
        cur, syms, fns = it["current"], it["symbols"], it.get("functions") or []
        m0 = run_m0(cur, syms, fns)
        m1 = run_method_v2(cur, syms, fns, max_steps=4)
        row = {
            "id": it["id"],
            "d_floor": it.get("d_floor", ""),
            "m0_changed": m0["changed"],
            "m1_changed": m1["changed"],
            "m0_n_zero": m0["n_zero"],
            "m1_n_zero": m1["n_zero"],
            "m0_named_aux_zero": m0["named_aux_zero"],
            "m1_named_aux_zero": m1["named_aux_zero"],
            "m1_extra_after_zero": m1["extra_certified_after_first_zero"],
            "m0_false_promotion": m0["false_promotion"],
            "m1_false_promotion": m1["false_promotion"],
            "m0_certified": m0["certified"],
            "m1_certified": m1["certified"],
        }
        rows.append(row)
        print(it["id"], "m0z", m0["n_zero"], "m1z", m1["n_zero"],
              "named", m1["named_aux_zero"], "extra", m1["extra_certified_after_first_zero"])

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "DEV_RESULTS.json").write_text(json.dumps(rows, indent=2) + "\n")
    with (OUT / "DEV_RESULTS.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    fp = sum(r["m1_false_promotion"] for r in rows)
    named = sum(1 for r in rows if r["m1_named_aux_zero"] > r["m0_named_aux_zero"])
    extra = sum(1 for r in rows if r["m1_extra_after_zero"] > 0)
    d2_ok = all(r["m1_n_zero"] >= r["m0_n_zero"] for r in rows)
    print("n", n, "fp", fp, "named_gain", named, "extra_steps", extra, "d2_ok", d2_ok)


if __name__ == "__main__":
    main()
