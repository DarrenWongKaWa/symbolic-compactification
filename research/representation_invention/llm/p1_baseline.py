"""Read-only loaders for frozen Grounded-Proposer-v1 JSON.

`confluent_representation` → `local_confluence` is evaluation-only.
It is not a parse repair and is never written back to P1 files.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from research.representation_invention.schema import P1_TYPE_ALIASES

P1_RUNS_DIR = Path(__file__).resolve().parents[2] / "grounded_proposer" / "runs"

# Evaluation-only. Do not feed this map to parse_hypothesis_v2.
P1_TYPE_TO_V2 = dict(P1_TYPE_ALIASES)


def map_p1_type(name: str) -> str:
    return P1_TYPE_TO_V2.get(name, name)


def load_p1_run(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_p1_runs(directory: Optional[Path] = None) -> list[dict[str, Any]]:
    d = Path(directory) if directory is not None else P1_RUNS_DIR
    return [load_p1_run(p) for p in sorted(d.glob("*.json"))]


def _types_of(record: dict) -> list[str]:
    types = list(record.get("types_ok") or [])
    if types:
        return types
    out = []
    for h in record.get("hypotheses") or []:
        if not isinstance(h, dict):
            continue
        if h.get("parse_status") == "PARSE_FAILURE":
            continue
        t = h.get("representation_type")
        if t:
            out.append(str(t))
    return out


def _verdict_counts(record: dict) -> dict[str, int]:
    scores = record.get("scores") or []
    if scores:
        n_zero = sum(
            1
            for s in scores
            if s.get("layer") == "OK" or "ZERO" in (s.get("verdicts") or [])
        )
        n_nonzero = sum(1 for s in scores if s.get("detail") == "wrong_structure")
        n_unknown = sum(1 for s in scores if s.get("layer") == "V")
        n_gfail = sum(1 for s in scores if s.get("layer") == "G")
        return {
            "n_zero": n_zero,
            "n_nonzero": n_nonzero,
            "n_unknown": n_unknown,
            "n_gfail": n_gfail,
        }
    return {
        "n_zero": int(record.get("n_zero") or 0),
        "n_nonzero": int(record.get("n_nonzero") or 0),
        "n_unknown": int(record.get("n_unknown") or 0),
        "n_gfail": int(record.get("n_gfail") or 0),
    }


def summarize_record(record: dict) -> dict[str, Any]:
    types = _types_of(record)
    mapped = [map_p1_type(t) for t in types]
    verdicts = _verdict_counts(record)
    return {
        "item_id": record.get("item_id"),
        "seed": record.get("seed"),
        "parse_status": record.get("parse_status"),
        "types": types,
        "types_v2": mapped,
        "type_counts": dict(Counter(types)),
        "type_counts_v2": dict(Counter(mapped)),
        **verdicts,
    }


def summarize_p1(records: Optional[list[dict]] = None) -> dict[str, Any]:
    recs = records if records is not None else load_p1_runs()
    type_counts: Counter[str] = Counter()
    type_counts_v2: Counter[str] = Counter()
    totals = Counter()
    by_item: dict[str, Any] = {}
    rows = []
    for rec in recs:
        row = summarize_record(rec)
        rows.append(row)
        type_counts.update(row["types"])
        type_counts_v2.update(row["types_v2"])
        for k in ("n_zero", "n_nonzero", "n_unknown", "n_gfail"):
            totals[k] += int(row.get(k) or 0)
        iid = str(row.get("item_id") or rec.get("item_id") or "?")
        slot = by_item.setdefault(
            iid,
            {
                "n_records": 0,
                "type_counts": Counter(),
                "type_counts_v2": Counter(),
                "n_zero": 0,
                "n_nonzero": 0,
                "n_unknown": 0,
                "n_gfail": 0,
            },
        )
        slot["n_records"] += 1
        slot["type_counts"].update(row["types"])
        slot["type_counts_v2"].update(row["types_v2"])
        for k in ("n_zero", "n_nonzero", "n_unknown", "n_gfail"):
            slot[k] += int(row.get(k) or 0)
    by_item_out = {}
    for iid, slot in by_item.items():
        by_item_out[iid] = {
            **slot,
            "type_counts": dict(slot["type_counts"]),
            "type_counts_v2": dict(slot["type_counts_v2"]),
        }
    return {
        "n_records": len(recs),
        "type_counts": dict(type_counts),
        "type_counts_v2": dict(type_counts_v2),
        "n_zero": int(totals["n_zero"]),
        "n_nonzero": int(totals["n_nonzero"]),
        "n_unknown": int(totals["n_unknown"]),
        "n_gfail": int(totals["n_gfail"]),
        "by_item": by_item_out,
        "records": rows,
    }
