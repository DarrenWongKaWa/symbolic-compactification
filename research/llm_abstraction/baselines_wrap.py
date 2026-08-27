"""Frozen baselines under experiment numbering. Callees are not edited.

B0 = frozen B9
B1 = frozen LGG
B2 = frozen LGG + canon/AC
B3 = frozen operator graph
"""
from __future__ import annotations

from typing import Any

from research.abstraction_invention.beyond.invent_beyond import (
    b2_filtered_lgg,
    b4_ac_lgg,
    b5_operator_graph,
)
from research.abstraction_invention.prototype.orchestrator import (
    run_b9_frozen,
    run_inventor,
)
from research.structure_discovery.prototype.leakage import proposer_view


def _pub(item: dict) -> dict:
    return proposer_view(item)


def run_b0_b9(item: dict) -> dict[str, Any]:
    try:
        run = run_b9_frozen(item)
        run["baseline"] = "B0_frozen_B9"
        return run
    except Exception as exc:
        return {"baseline": "B0_frozen_B9", "error": type(exc).__name__, "n_hypotheses": 0}


def run_b1_lgg(item: dict) -> dict[str, Any]:
    try:
        run = run_inventor(item)
        run["baseline"] = "B1_frozen_LGG"
        return run
    except Exception as exc:
        return {"baseline": "B1_frozen_LGG", "error": type(exc).__name__, "n_hypotheses": 0}


def run_b2_ac(item: dict) -> dict[str, Any]:
    pub = _pub(item)
    text, syms, fns = pub.get("current") or item.get("current"), pub.get("symbols") or [], pub.get("functions") or []
    try:
        filt = b2_filtered_lgg(text, syms, fns)
        ac = b4_ac_lgg(text, syms, fns)
        return {
            "baseline": "B2_lgg_canon_ac",
            "n_filtered": len(filt),
            "n_ac": len(ac),
            "ac_exact": any(r.get("exact_after_canon") for r in ac),
            "filtered": [h.to_dict() if hasattr(h, "to_dict") else h for h in filt],
            "ac": ac,
        }
    except Exception as exc:
        return {"baseline": "B2_lgg_canon_ac", "error": type(exc).__name__}


def run_b3_op(item: dict) -> dict[str, Any]:
    pub = _pub(item)
    text, syms, fns = pub.get("current") or item.get("current"), pub.get("symbols") or [], pub.get("functions") or []
    try:
        op = b5_operator_graph(text, syms, fns)
        op["baseline"] = "B3_operator_graph"
        return op
    except Exception as exc:
        return {"baseline": "B3_operator_graph", "error": type(exc).__name__}


def run_all_frozen(item: dict) -> dict[str, Any]:
    return {
        "id": item.get("id"),
        "B0": run_b0_b9(item),
        "B1": run_b1_lgg(item),
        "B2": run_b2_ac(item),
        "B3": run_b3_op(item),
    }
