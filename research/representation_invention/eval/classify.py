"""Layer and DD-gate labels for P2 hypotheses. Evaluation-only."""
from __future__ import annotations

from typing import Any

from research.representation_invention.labels import DD_CLASSES
from research.representation_invention.ladder import type_r_hint

DD_TYPES = {"divided_difference", "hermite_divided_difference"}
CONFLUENCE_TYPES = {"local_confluence"}


def dd_class(score: dict[str, Any], hyp: dict[str, Any] | None = None) -> str:
    """Phase 7 gate. Verbal confluence is not DD-OK."""
    rtype = (hyp or {}).get("representation_type") or score.get("type") or ""
    parse = score.get("parse_status")
    grounded = bool(score.get("grounded"))
    cstatus = score.get("compile_status")
    n_zero = int(score.get("n_zero") or 0)
    n_nz = int(score.get("n_nonzero") or 0)
    n_unk = int(score.get("n_unknown") or 0)
    if rtype not in DD_TYPES:
        return "DD-D"
    if parse == "PARSE_FAILURE" or not grounded:
        return "DD-G"
    if cstatus in {"COMPILE_FAILURE", "not_wired", "skipped"}:
        return "DD-C"
    if n_nz:
        return "DD-V0"
    if n_unk and not n_zero:
        return "DD-VU"
    if n_zero and not n_nz and not n_unk:
        return "DD-OK"
    if n_zero and n_unk:
        return "DD-VU"
    return "DD-D"


def r_proposed(hyp: dict[str, Any]) -> str | None:
    return type_r_hint(str(hyp.get("representation_type") or ""))


def summarize_record(rec: dict[str, Any]) -> dict[str, Any]:
    hyps = rec.get("hypotheses") or []
    scores = rec.get("scores") or []
    rows = []
    for h, s in zip(hyps, scores):
        if not isinstance(h, dict):
            continue
        rows.append({
            "type": h.get("representation_type"),
            "r_hint": r_proposed(h),
            "member_ids": h.get("member_ids"),
            "dd_class": dd_class(s, h),
            "layer": s.get("layer"),
            "compile_status": s.get("compile_status"),
            "n_zero": s.get("n_zero"),
            "n_nonzero": s.get("n_nonzero"),
            "n_unknown": s.get("n_unknown"),
        })
    return {
        "item_id": rec.get("item_id"),
        "condition": rec.get("condition"),
        "seed": rec.get("seed"),
        "blocked": rec.get("blocked"),
        "parse_status": rec.get("parse_status"),
        "n_hypotheses": rec.get("n_hypotheses"),
        "n_ok": rec.get("n_ok"),
        "n_grounded": rec.get("n_grounded"),
        "n_zero": rec.get("n_zero"),
        "n_nonzero": rec.get("n_nonzero"),
        "n_unknown": rec.get("n_unknown"),
        "compile_status": rec.get("compile_status"),
        "n_dd_ok": sum(1 for r in rows if r["dd_class"] == "DD-OK"),
        "n_local_confluence": sum(
            1 for r in rows if r["type"] in CONFLUENCE_TYPES
        ),
        "n_dd_type": sum(1 for r in rows if r["type"] in DD_TYPES),
        "rows": rows,
    }


assert set(DD_CLASSES) >= {
    "DD-D", "DD-G", "DD-C", "DD-V0", "DD-VU", "DD-OK",
}
