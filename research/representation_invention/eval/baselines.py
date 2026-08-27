"""Frozen symbolic baselines on representation-bench DEV. Callees not edited."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.llm_abstraction.baselines_wrap import run_all_frozen
from research.representation_invention.bench.loader import load_dev, proposer_view

OUT = Path(__file__).resolve().parents[1] / "RESULTS_BASELINES.json"


def _item(task: dict) -> dict:
    pub = proposer_view(task)
    current = pub.get("current") or ""
    return {
        "id": pub.get("id") or task.get("id"),
        "current": current,
        "symbols": pub.get("symbols") or [],
        "functions": pub.get("functions") or [],
        "scientific_context": pub.get("scientific_context") or [],
    }


def hypothesis_types(blob: Any) -> list[str]:
    if not isinstance(blob, dict):
        return []
    types = blob.get("hypothesis_types")
    if isinstance(types, list) and types:
        return [str(t) for t in types]
    out = []
    for h in blob.get("hypotheses") or []:
        if hasattr(h, "to_dict"):
            h = h.to_dict()
        if isinstance(h, dict):
            t = h.get("hypothesis_type") or h.get("representation_type")
            if t:
                out.append(str(t))
    return out


def claims_dd(blob: Any) -> bool:
    return any(
        t in {"divided_difference", "hermite_divided_difference", "confluent_representation"}
        for t in hypothesis_types(blob)
    )


def has_explicit_latent_F(blob: Any) -> bool:
    for h in (blob or {}).get("hypotheses") or [] if isinstance(blob, dict) else []:
        if hasattr(h, "to_dict"):
            h = h.to_dict()
        if not isinstance(h, dict):
            continue
        latent = str(h.get("latent_object") or "")
        aux = h.get("proposed_auxiliaries") or []
        if "F(" in latent or "F[" in latent:
            return True
        for a in aux:
            if isinstance(a, dict) and str(a.get("definition") or "").startswith("F"):
                return True
    return False


def run() -> dict[str, Any]:
    rows = []
    for task in load_dev():
        item = _item(task)
        if not item["current"]:
            rows.append({"id": item["id"], "skipped": True, "reason": "no_current"})
            continue
        try:
            raw = run_all_frozen(item)
        except Exception as exc:
            rows.append({"id": item["id"], "error": type(exc).__name__})
            continue
        b0 = raw.get("B0") or {}
        b1 = raw.get("B1") or {}
        rows.append({
            "id": item["id"],
            "target": task.get("hidden_target_type"),
            "b9_n": b0.get("n_hypotheses"),
            "b9_types": hypothesis_types(b0),
            "b9_n_zero": b0.get("n_zero"),
            "b9_explicit_F": has_explicit_latent_F(b0),
            "lgg_n": b1.get("n_hypotheses"),
            "lgg_types": hypothesis_types(b1),
            "b9_typed_dd_or_confluence": claims_dd(b0),
            "lgg_typed_dd_or_confluence": claims_dd(b1),
            "errors": {
                "B0": b0.get("error"),
                "B1": b1.get("error"),
                "B2": (raw.get("B2") or {}).get("error"),
                "B3": (raw.get("B3") or {}).get("error"),
            },
        })
    report = {"n": len(rows), "rows": rows}
    OUT.write_text(json.dumps(report, indent=2, default=str))
    return report


if __name__ == "__main__":
    r = run()
    print("n", r["n"])
    for row in r["rows"]:
        print(row.get("id"), "b9", row.get("b9_n"), "lgg", row.get("lgg_n"),
              "dd?", row.get("b9_mentions_dd"), row.get("lgg_mentions_dd"))
