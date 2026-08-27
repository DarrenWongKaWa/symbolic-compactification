"""Held-out evaluation. Frozen B9 vs M_lgg. No method edits."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from research.abstraction_invention.prototype.run_dev import load
from research.abstraction_invention.prototype.evaluator import score_b9_frozen, score_inventor
from research.abstraction_invention.prototype.orchestrator import (
    llm_unavailable, run_b9_frozen, run_inventor,
)

ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "research" / "abstraction_invention" / "final"


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    items = load("test")
    rows, dumps = [], []
    llm = llm_unavailable()
    for it in items:
        inv, b9 = run_inventor(it), run_b9_frozen(it)
        si, sb = score_inventor(it, inv), score_b9_frozen(it, b9)
        sl = {"id": it["id"], "method": "M_llm", "blocked": True,
              "invention_success": False, "polarity": it.get("polarity"),
              "family": it.get("family")}
        for method, sc, run in (("M_lgg", si, inv), ("B9_frozen", sb, b9), ("M_llm", sl, llm)):
            row = dict(sc); row["method"] = method
            rows.append(row)
            dumps.append({"id": it["id"], "method": method, "score": sc})
            print(f"{it['id']:24} {method:12} invent={sc.get('invention_success')}", flush=True)
    fields = sorted({k for r in rows for k in r})
    with (FINAL / "RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    (FINAL / "RESULTS.json").write_text(json.dumps(dumps, indent=2, default=str) + "\n")

    def pack(m):
        pos = [r for r in rows if r["method"] == m and r.get("polarity") == "positive"]
        neg = [r for r in rows if r["method"] == m and r.get("polarity") == "negative"]
        return {
            "pos": f"{sum(bool(r.get('invention_success')) for r in pos)}/{len(pos)}",
            "neg": f"{sum(bool(r.get('invention_success')) for r in neg)}/{len(neg)}",
        }
    summary = {m: pack(m) for m in ("M_lgg", "B9_frozen", "M_llm")}
    (FINAL / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
