"""D / C / V failure labels. Do not collapse them."""
from __future__ import annotations

from typing import Any, Optional

from research.llm_abstraction.evaluator import _type_hit
from research.llm_abstraction.schema import LLMStructureHypothesis, OK, PARSE_FAILURE, ProposeResult
from research.obligation_ir.schema import C, COMPILE_OK, D, V
from research.obligation_ir.schema import VerifyResult

ZERO_S = "ZERO"


def layer_label(
    item: dict,
    result: ProposeResult,
    compile_n_ok: int,
    compile_n_fail: int,
    verifications: list[VerifyResult],
) -> dict[str, Any]:
    """Assign a single primary miss layer for this (item, proposal).

    D: gold type not proposed (positives) / forbidden type proposed (negatives)
    C: type present but compilation failed
    V: compiled, but not all ZERO (NONZERO or UNKNOWN)
    OK: compiled and all ZERO on at least one matching hypothesis
    """
    polarity = item.get("polarity") or "positive"
    ok_hyps = [h for h in result.hypotheses if h.parse_status == OK]
    type_hit = any(_type_hit(h.hypothesis_type, item) for h in ok_hyps)
    n_zero = sum(1 for v in verifications if v.verdict == "ZERO" and v.compile_status == COMPILE_OK)
    n_nz = sum(1 for v in verifications if v.verdict == "NONZERO")
    n_unk = sum(1 for v in verifications if v.verdict == "UNKNOWN")

    if polarity in {"negative", "trap"}:
        if result.parse_status == PARSE_FAILURE:
            return {"layer": C, "detail": "parse_failure"}
        if type_hit or n_zero:
            return {"layer": D, "detail": "false_or_forbidden_type"}
        return {"layer": "OK", "detail": "abstain_or_no_false_type"}

    gold = item.get("gold_types") or []
    if gold and not type_hit:
        if not ok_hyps:
            return {"layer": D, "detail": "no_proposal"}
        return {"layer": D, "detail": "wrong_type"}
    if compile_n_ok == 0 and compile_n_fail > 0:
        return {"layer": C, "detail": "compile_failure"}
    if n_zero > 0 and n_nz == 0 and compile_n_fail == 0 and n_unk == 0:
        return {"layer": "OK", "detail": "certified"}
    if n_zero > 0 and n_nz == 0:
        return {"layer": V, "detail": "partial_zero_rest_unknown"}
    if n_nz > 0:
        return {"layer": V, "detail": "nonzero"}
    if n_unk > 0:
        return {"layer": V, "detail": "unknown"}
    if compile_n_fail:
        return {"layer": C, "detail": "compile_failure"}
    return {"layer": D, "detail": "unclassified"}
