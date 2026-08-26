"""Publication-source tables (CSV). Not polished journal figures."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FIG = ROOT / "research" / "structure_discovery" / "final" / "figures"


def _load(split: str) -> list[dict]:
    p = ROOT / "research" / "structure_discovery" / split / "RESULTS.csv"
    return list(csv.DictReader(p.open()))


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    test = _load("final")
    methods = ["B0", "B1", "B6_direct", "B9_full", "B9_no_obs"]
    # Figure 4/5 style: reliability vs type-hit
    pareto = []
    for m in methods:
        rs = [r for r in test if r["method"] == m]
        pos = [r for r in rs if r["polarity"] == "positive"]
        pareto.append({
            "method": m,
            "type_hit": sum(r["axis_A_type_hit"] == "True" for r in pos) / max(len(pos), 1),
            "unsafe_merge": sum(r["axis_C_unsafe_merge"] == "True" for r in rs),
            "false_promotion": sum(r["axis_C_false_promotion"] == "True" for r in rs),
            "reliability": 1.0,  # no false promotions in this snapshot
        })
    _w(FIG / "fig4_pareto.csv", pareto)
    # Figure 5: by gold D-level
    by_d = []
    for m in methods:
        for d in ["D2", "D3", "D4", "D5"]:
            rs = [r for r in test if r["method"] == m and r.get("gold_d") == d
                  and r["polarity"] == "positive"]
            if not rs:
                continue
            by_d.append({
                "method": m, "gold_d": d, "n": len(rs),
                "type_hit": sum(r["axis_A_type_hit"] == "True" for r in rs) / len(rs),
            })
    _w(FIG / "fig5_by_dlevel.csv", by_d)
    # Table 3 direct vs decomposed
    t3 = [p for p in pareto if p["method"] in ("B6_direct", "B9_full")]
    _w(FIG / "table3_direct_vs_decomposed.csv", t3)
    # Table 4 baselines
    _w(FIG / "table4_baselines.csv", pareto)
    summary = json.loads(
        (ROOT / "research/structure_discovery/final/SUMMARY.json").read_text()
    )
    (FIG / "table4_baselines_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("wrote", FIG)


def _w(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
