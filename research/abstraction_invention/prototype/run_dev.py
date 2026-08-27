"""DEV matrix: frozen B9 vs LGG inventor. LLM slot recorded as blocked."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from research.abstraction_invention.prototype.build_benchmark import OUT, write_benchmark
from research.abstraction_invention.prototype.evaluator import score_b9_frozen, score_inventor
from research.abstraction_invention.prototype.orchestrator import (
    llm_unavailable,
    run_b9_frozen,
    run_inventor,
)

ROOT = Path(__file__).resolve().parents[3]
DEV = ROOT / "research" / "abstraction_invention" / "dev"


def load(split: str) -> list[dict]:
    write_benchmark()
    return [json.loads(p.read_text()) for p in sorted((OUT / split).glob("*.json"))]


def main() -> None:
    DEV.mkdir(parents=True, exist_ok=True)
    items = load("dev")
    rows = []
    dumps = []
    llm = llm_unavailable()
    for it in items:
        inv = run_inventor(it)
        b9 = run_b9_frozen(it)
        si = score_inventor(it, inv)
        sb = score_b9_frozen(it, b9)
        sl = {"id": it["id"], "method": "M_llm", "blocked": True,
              "invention_success": False, "polarity": it.get("polarity"),
              "family": it.get("family"), "gold_operator": it.get("gold_operator")}
        for method, sc, run in (("M_lgg", si, inv), ("B9_frozen", sb, b9), ("M_llm", sl, llm)):
            row = dict(sc)
            row["method"] = method
            rows.append(row)
            dumps.append({"id": it["id"], "method": method, "score": sc,
                          "run_keys": list(run)})
            print(f"{it['id']:24} {method:12} invent={sc.get('invention_success')} "
                  f"cover={sc.get('family_cover_certified')} types={sc.get('operators') or sc.get('b9_types')}",
                  flush=True)
    fields = sorted({k for r in rows for k in r})
    with (DEV / "RESULTS.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    (DEV / "RESULTS.json").write_text(json.dumps(dumps, indent=2, default=str) + "\n")

    def rate(method, pred):
        sub = [r for r in rows if r["method"] == method and pred(r)]
        hits = [r for r in sub if r.get("invention_success")]
        return len(hits), len(sub)

    summary = {}
    for m in ("M_lgg", "B9_frozen", "M_llm"):
        pos = rate(m, lambda r: r["polarity"] == "positive")
        neg = rate(m, lambda r: r["polarity"] == "negative")
        summary[m] = {
            "pos_invention": f"{pos[0]}/{pos[1]}",
            "neg_success": f"{neg[0]}/{neg[1]}",
        }
    (DEV / "SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
