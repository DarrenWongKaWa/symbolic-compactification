"""Parse model JSON into hypotheses. No silent scientific repair."""
from __future__ import annotations

import json
import re
from typing import Any

from research.llm_abstraction.quality import flag_unnecessary
from research.llm_abstraction.schema import (
    ABSTAIN,
    HYPOTHESIS_TYPES,
    LLMStructureHypothesis,
    OK,
    PARSE_FAILURE,
    ProposeResult,
    REQUIRED_FIELDS,
)

_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.S)


def extract_json_object(text: str) -> tuple[dict | None, str | None]:
    """Format-only extraction. Does not invent fields."""
    if not text or not str(text).strip():
        return None, "empty_content"
    raw = str(text).strip()
    m = _FENCE.search(raw)
    if m:
        raw = m.group(1).strip()
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj, None
        return None, "json_not_object"
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                obj = json.loads(raw[start:end + 1])
                if isinstance(obj, dict):
                    return obj, None
            except json.JSONDecodeError:
                pass
        return None, "json_decode_error"


def _as_list(v: Any) -> list:
    if v is None:
        return []
    if isinstance(v, list):
        return v
    return [v]


def parse_one(raw: Any) -> LLMStructureHypothesis:
    if not isinstance(raw, dict):
        return LLMStructureHypothesis.parse_failure("hypothesis_not_object")
    missing = [f for f in REQUIRED_FIELDS if f not in raw]
    if missing:
        return LLMStructureHypothesis.parse_failure(
            f"missing_fields:{','.join(missing)}", raw,
        )
    htype = raw.get("hypothesis_type")
    if htype not in HYPOTHESIS_TYPES:
        return LLMStructureHypothesis.parse_failure(
            f"unknown_hypothesis_type:{htype}", raw,
        )
    members = raw.get("target_members")
    if not isinstance(members, list) or not all(isinstance(x, str) for x in members):
        return LLMStructureHypothesis.parse_failure("target_members_not_string_list", raw)
    latent = raw.get("latent_object")
    if not isinstance(latent, str) or not latent.strip():
        return LLMStructureHypothesis.parse_failure("latent_object_empty", raw)
    params = raw.get("parameters")
    if not isinstance(params, list):
        return LLMStructureHypothesis.parse_failure("parameters_not_list", raw)
    ops = raw.get("operators")
    if not isinstance(ops, list):
        return LLMStructureHypothesis.parse_failure("operators_not_list", raw)
    imaps = raw.get("instance_maps")
    if not isinstance(imaps, list):
        return LLMStructureHypothesis.parse_failure("instance_maps_not_list", raw)
    plan = raw.get("construction_plan")
    if not isinstance(plan, str):
        return LLMStructureHypothesis.parse_failure("construction_plan_not_string", raw)
    assum = raw.get("required_assumptions")
    if not isinstance(assum, list):
        return LLMStructureHypothesis.parse_failure("required_assumptions_not_list", raw)
    oblig = raw.get("proof_obligations")
    if not isinstance(oblig, list):
        return LLMStructureHypothesis.parse_failure("proof_obligations_not_list", raw)
    rationale = raw.get("rationale")
    if not isinstance(rationale, str):
        return LLMStructureHypothesis.parse_failure("rationale_not_string", raw)
    conf = raw.get("confidence")
    try:
        conf_f = float(conf)
    except (TypeError, ValueError):
        return LLMStructureHypothesis.parse_failure("confidence_not_number", raw)
    if not 0.0 <= conf_f <= 1.0:
        return LLMStructureHypothesis.parse_failure("confidence_out_of_range", raw)

    hyp = LLMStructureHypothesis(
        hypothesis_type=htype,
        target_members=members,
        latent_object=latent,
        parameters=[str(p) for p in params],
        operators=ops,
        instance_maps=imaps,
        construction_plan=plan,
        required_assumptions=[str(a) for a in assum],
        proof_obligations=[str(o) for o in oblig],
        rationale=rationale,
        confidence=conf_f,
        parse_status=OK,
    )
    flags = flag_unnecessary(hyp)
    hyp.quality_flags = flags
    return hyp


def parse_model_output(text: str) -> ProposeResult:
    obj, err = extract_json_object(text)
    if obj is None:
        return ProposeResult(
            hypotheses=[],
            parse_status=PARSE_FAILURE,
            parse_error=err,
            raw_content=text or "",
        )
    # Format-only: a single hypothesis object at top level.
    if "hypothesis_type" in obj and "hypotheses" not in obj:
        obj = {"abstain": False, "hypotheses": [obj]}
    if "hypotheses" not in obj:
        if obj.get("abstain") is True:
            return ProposeResult(
                hypotheses=[],
                parse_status=ABSTAIN,
                abstain=True,
                abstain_reason=str(obj.get("abstain_reason") or "abstain"),
                raw_content=text or "",
            )
        return ProposeResult(
            hypotheses=[],
            parse_status=PARSE_FAILURE,
            parse_error="missing_hypotheses",
            raw_content=text or "",
        )
    hyps_raw = obj.get("hypotheses")
    if not isinstance(hyps_raw, list):
        return ProposeResult(
            hypotheses=[],
            parse_status=PARSE_FAILURE,
            parse_error="hypotheses_not_list",
            raw_content=text or "",
        )
    abstain = bool(obj.get("abstain"))
    parsed = [parse_one(h) for h in hyps_raw]
    ok = [h for h in parsed if h.parse_status == OK]
    if abstain and not hyps_raw:
        return ProposeResult(
            hypotheses=[],
            parse_status=ABSTAIN,
            abstain=True,
            abstain_reason=str(obj.get("abstain_reason") or "abstain"),
            raw_content=text or "",
        )
    if not parsed and not abstain:
        return ProposeResult(
            hypotheses=[],
            parse_status=PARSE_FAILURE,
            parse_error="empty_hypotheses",
            abstain=False,
            raw_content=text or "",
        )
    if ok and not any(h.parse_status == PARSE_FAILURE for h in parsed):
        status = ABSTAIN if abstain else OK
    elif ok:
        status = OK  # partial: keep valid hyps, record failures
    else:
        status = PARSE_FAILURE if parsed else (ABSTAIN if abstain else PARSE_FAILURE)
    return ProposeResult(
        hypotheses=parsed,
        parse_status=status,
        parse_error=None if status != PARSE_FAILURE else (
            parsed[0].parse_error if parsed else "all_failed"
        ),
        abstain=abstain and not ok,
        abstain_reason=str(obj.get("abstain_reason") or ""),
        raw_content=text or "",
    )
