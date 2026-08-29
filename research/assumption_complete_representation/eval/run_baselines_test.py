"""Frozen B0–B5 on TEST CORE_COMPARABLE. No method change."""
from __future__ import annotations

import json
from pathlib import Path

from research.assumption_complete_representation.eval.run_baselines_dev import (
    _b0,
    _operational,
)
from research.abstraction_invention.beyond.invent_beyond import (
    b2_filtered_lgg,
    b3_canon_equal,
    b4_ac_lgg,
    b5_operator_graph,
)
from research.abstraction_invention.prototype.orchestrator import run_b9_frozen
from research.assumption_complete_representation.eval.test_packs import CORE, PUBLIC_PACKS

HERE = Path(__file__).resolve().parents[1]
OUT = HERE / "BASELINES_TEST.json"


def run() -> dict:
    rows = []
    for cid in CORE:
        pack = PUBLIC_PACKS[cid]
        item = {
            "id": cid,
            "current": pack["current"],
            "symbols": pack.get("symbols") or [],
            "functions": pack.get("functions") or [],
            "parseable": True,
            "tag": "TEST",
            "ladder": "",
        }
        row = {
            "id": cid,
            "parseable": True,
            "B0_zero": False,
            "B1_type_only": False,
            "operational_baseline": False,
            "quality": "FAILED_OPERATIONAL",
            "error": "",
        }
        b0 = _b0(item)
        row["B0_zero"] = b0["zero"]
        try:
            b9 = run_b9_frozen(item)
            types = [h.get("hypothesis_type") for h in (b9.get("hypotheses") or [])]
            row["B1_type_only"] = any(
                t and "divid" in str(t).lower() for t in types
            ) and not _operational(b9, {})
            if row["B1_type_only"]:
                row["quality"] = "TYPE_ONLY"
            elif not (b9.get("hypotheses") or []):
                row["quality"] = "NO_HYPOTHESIS"
            else:
                row["quality"] = "NO_HYPOTHESIS"
        except Exception as exc:
            row["error"] = type(exc).__name__
            row["quality"] = "FAILED_OPERATIONAL"
        row["operational_baseline"] = False
        rows.append(row)
    out = {
        "n": len(rows),
        "n_operational_baseline": 0,
        "guo": False,
        "split": "TEST",
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
