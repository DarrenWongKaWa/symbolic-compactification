"""Frozen B0–B5 on DEV. TYPE_ONLY is not operational success. No Guo."""
from __future__ import annotations

import csv
import json
import traceback
from pathlib import Path

import sympy

from research.abstraction_invention.beyond.invent_beyond import (
    b2_filtered_lgg,
    b3_canon_equal,
    b4_ac_lgg,
    b5_operator_graph,
)
from research.abstraction_invention.prototype.orchestrator import run_b9_frozen, run_inventor
from research.assumption_complete_representation.eval.dev_items import items

HERE = Path(__file__).resolve().parents[1]
OUT_JSON = HERE / "BASELINES_DEV.json"
OUT_CSV = HERE / "BASELINES_DEV.csv"
OUT_MD = HERE / "BASELINES_DEV.md"
MANIFEST = HERE / "BASELINE_FREEZE_MANIFEST.json"


def _b0(item: dict) -> dict:
    if not item.get("parseable") or not item.get("current"):
        return {"ok": False, "zero": False, "note": "unparseable"}
    try:
        from symbolic_compactification import parse_expression

        expr = parse_expression(item["current"], item["symbols"], item.get("functions") or None)
        simp = sympy.simplify(expr)
        zero = simp == 0
        if not zero:
            try:
                val = complex(expr.evalf(20))
                zero = abs(val) < 1e-12
            except Exception:
                zero = False
        return {"ok": True, "zero": bool(zero), "note": "residual_only"}
    except Exception as exc:
        return {"ok": False, "zero": False, "note": type(exc).__name__}


def _operational(b9: dict, lgg: dict) -> bool:
    """Newton/Hermite reconstruction with explicit F. LGG templates are not that."""
    return False


def run() -> dict:
    rows = []
    for it in items():
        cid = it["id"]
        row = {
            "id": cid,
            "tag": it["tag"],
            "ladder": it["ladder"],
            "parseable": it["parseable"],
            "B0_zero": False,
            "B1_type_only": False,
            "B2_lgg_n": 0,
            "B2_lgg_cert": 0,
            "B3_canon_n": 0,
            "B4_ac_n": 0,
            "B5_deriv": 0,
            "operational_baseline": False,
            "quality": "FAILED_OPERATIONAL",
            "error": "",
        }
        b0 = _b0(it)
        row["B0_zero"] = b0["zero"]
        if not it["parseable"]:
            row["quality"] = "UNPARSEABLE_WHITELIST"
            rows.append(row)
            continue
        try:
            b9 = run_b9_frozen(it)
            types = [h.get("hypothesis_type") for h in (b9.get("hypotheses") or [])]
            row["B1_type_only"] = bool(types) and not _operational(b9, {})
            lgg = run_inventor(it)
            row["B2_lgg_n"] = int(lgg.get("n_hypotheses") or 0)
            row["B2_lgg_cert"] = int(lgg.get("n_certified_abstractions") or 0)
            text, syms, fns = it["current"], it["symbols"], it.get("functions") or []
            row["B3_canon_n"] = len(b3_canon_equal(text, syms, fns))
            row["B4_ac_n"] = len(b4_ac_lgg(text, syms, fns))
            op = b5_operator_graph(text, syms, fns)
            row["B5_deriv"] = int(op.get("n_derivative") or 0)
            row["operational_baseline"] = _operational(b9, lgg)
            if row["operational_baseline"]:
                row["quality"] = "OPERATIONAL_CORRECT"
            elif row["B1_type_only"] or types:
                row["quality"] = "TYPE_ONLY"
            elif b0["zero"]:
                row["quality"] = "SHALLOW_REPACKAGING"
            else:
                row["quality"] = "NO_HYPOTHESIS"
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}:{exc}"
            row["quality"] = "FAILED_OPERATIONAL"
        rows.append(row)

    n_op = sum(1 for r in rows if r["operational_baseline"])
    report = {
        "n": len(rows),
        "n_operational_baseline": n_op,
        "ai_unique_success": 0,
        "guo": False,
        "type_only_is_not_success": True,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    lines = [
        "# DEV frozen baselines",
        "",
        "TYPE_ONLY is not operational success. B0 residual ZERO is not discovery.",
        f"operational_baseline={n_op}/{len(rows)}  AI_UNIQUE_SUCCESS=0  Guo=false",
        "",
        "| id | tag | B0_zero | quality | B2_cert | B5_deriv |",
        "|---|---|---|---|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['tag']} | {r['B0_zero']} | {r['quality']} | {r['B2_lgg_cert']} | {r['B5_deriv']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    MANIFEST.write_text(
        json.dumps(
            {
                "n": len(rows),
                "authorities": {
                    "B9": "4237f6b",
                    "LGG": "efc0924",
                    "beyond": "3214a5a",
                },
                "no_modification": True,
                "type_only_not_success": True,
            },
            indent=2,
        )
        + "\n"
    )
    return report


if __name__ == "__main__":
    r = run()
    print(json.dumps({k: r[k] for k in ("n", "n_operational_baseline", "ai_unique_success")}))
