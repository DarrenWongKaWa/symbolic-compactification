"""Held-out evaluation. Call only after freeze. No method changes."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from research.structure_discovery.prototype.run_dev import (
    _flat,
    load_split,
    run_matrix,
    summarize,
)

ROOT = Path(__file__).resolve().parents[3]
FINAL = ROOT / "research" / "structure_discovery" / "final"


def main() -> None:
    FINAL.mkdir(parents=True, exist_ok=True)
    items = load_split("test")
    rows, dumps = run_matrix(items)
    summary = summarize(rows)
    fields = sorted({k for r in rows for k in r})
    with (FINAL / "RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (FINAL / "RESULTS.json").write_text(json.dumps(dumps, indent=2) + "\n")
    (FINAL / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    failures = [
        r for r in rows
        if r["method"] == "B9_full"
        and (
            (r["polarity"] == "positive" and not r["axis_A_type_hit"])
            or r["axis_C_unsafe_merge"]
            or r["axis_C_false_promotion"]
        )
    ]
    (FINAL / "FAILURES.md").write_text(
        "# Held-out failures (B9_full)\n\n"
        + "\n".join(
            f"- `{r['id']}` polarity={r['polarity']} types={r.get('types')} "
            f"quality={r['axis_A_hypothesis_quality']} unsafe={r['axis_C_unsafe_merge']}"
            for r in failures
        )
        + ("\n\nNone.\n" if not failures else "\n")
    )
    print(json.dumps({"n_test": len(items), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
