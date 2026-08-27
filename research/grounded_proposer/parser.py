"""Parse P1 JSON. Aliases are PARSE_FAILURE. No silent repair of members."""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from research.grounded_proposer.schema import (
    ABSTAIN,
    Fingerprint,
    GroundedHypothesis,
    MemberMap,
    OK,
    PARSE_FAILURE,
    REPRESENTATION_TYPES,
)
from research.llm_abstraction.parser import extract_json_object

_ALIAS = re.compile(
    r"^(S\d|C\d|O\d|G\d\(|branch_|generic|degenerate|diag|off)",
    re.I,
)


def _fp(raw: Any) -> Optional[Fingerprint]:
    if not isinstance(raw, dict):
        return None
    return Fingerprint(
        functions=[str(x) for x in (raw.get("functions") or [])],
        indices=[str(x) for x in (raw.get("indices") or [])],
        branch_condition=str(raw.get("branch_condition") or ""),
    )


def _maps(raw: Any) -> tuple[list[MemberMap] | None, str | None]:
    if not isinstance(raw, list):
        return None, "member_maps_not_list"
    out = []
    for m in raw:
        if not isinstance(m, dict):
            return None, "member_map_not_object"
        nid = str(m.get("source_node_id") or "").strip()
        if not nid:
            return None, "missing_source_node_id"
        if _ALIAS.match(nid) or not re.fullmatch(r"G\d{4}", nid):
            return None, f"alias_or_bad_id:{nid}"
        out.append(MemberMap(
            source_node_id=nid,
            role=str(m.get("role") or ""),
            source_fingerprint=_fp(m.get("source_fingerprint")),
        ))
    return out, None


def parse_one(raw: dict, catalog: set[str]) -> GroundedHypothesis:
    rtype = raw.get("representation_type")
    if rtype not in REPRESENTATION_TYPES:
        return GroundedHypothesis(
            representation_type="other_structured", latent_object="",
            member_maps=[], parse_status=PARSE_FAILURE,
            parse_error=f"unknown_type:{rtype}",
        )
    maps, err = _maps(raw.get("member_maps"))
    if err:
        return GroundedHypothesis(
            representation_type=rtype, latent_object=str(raw.get("latent_object") or ""),
            member_maps=[], parse_status=PARSE_FAILURE, parse_error=err,
        )
    ids = [m.source_node_id for m in maps]
    for k in ("generic_member", "degenerate_member"):
        v = str(raw.get(k) or "").strip()
        if v:
            if v not in catalog or not re.fullmatch(r"G\d{4}", v):
                return GroundedHypothesis(
                    representation_type=rtype, latent_object="",
                    member_maps=maps, parse_status=PARSE_FAILURE,
                    parse_error=f"id_not_in_catalog:{v}",
                )
            ids.append(v)
    for i in ids:
        if i not in catalog:
            return GroundedHypothesis(
                representation_type=rtype, latent_object="",
                member_maps=maps, parse_status=PARSE_FAILURE,
                parse_error=f"id_not_in_catalog:{i}",
            )
    latent = raw.get("latent_object")
    if not isinstance(latent, str) or not latent.strip():
        return GroundedHypothesis(
            representation_type=rtype, latent_object="",
            member_maps=maps, parse_status=PARSE_FAILURE,
            parse_error="latent_object_empty",
        )
    conf = raw.get("confidence")
    try:
        cf = float(conf)
    except (TypeError, ValueError):
        return GroundedHypothesis(
            representation_type=rtype, latent_object=latent,
            member_maps=maps, parse_status=PARSE_FAILURE,
            parse_error="confidence_not_number",
        )
    if not 0.0 <= cf <= 1.0:
        return GroundedHypothesis(
            representation_type=rtype, latent_object=latent,
            member_maps=maps, parse_status=PARSE_FAILURE,
            parse_error="confidence_out_of_range",
        )
    return GroundedHypothesis(
        representation_type=rtype,
        latent_object=latent,
        member_maps=maps,
        operators=list(raw.get("operators") or []),
        proof_obligations=[str(x) for x in (raw.get("proof_obligations") or [])],
        required_assumptions=[str(x) for x in (raw.get("required_assumptions") or [])],
        rationale=str(raw.get("rationale") or ""),
        confidence=cf,
        generic_member=str(raw.get("generic_member") or ""),
        degenerate_member=str(raw.get("degenerate_member") or ""),
        limit_variable=str(raw.get("limit_variable") or ""),
        parse_status=OK,
    )


def parse_p1(text: str, catalog: set[str]) -> dict:
    obj, err = extract_json_object(text)
    if obj is None:
        return {"parse_status": PARSE_FAILURE, "parse_error": err, "hypotheses": [], "abstain": False}
    if obj.get("abstain") and not obj.get("hypotheses"):
        return {
            "parse_status": ABSTAIN, "hypotheses": [], "abstain": True,
            "abstain_reason": str(obj.get("abstain_reason") or "abstain"),
        }
    raw_h = obj.get("hypotheses")
    if not isinstance(raw_h, list):
        return {"parse_status": PARSE_FAILURE, "parse_error": "hypotheses_not_list", "hypotheses": []}
    hyps = [parse_one(h, catalog) if isinstance(h, dict) else GroundedHypothesis(
        "other_structured", "", [], parse_status=PARSE_FAILURE, parse_error="not_object",
    ) for h in raw_h]
    ok = [h for h in hyps if h.parse_status == OK]
    status = OK if ok and all(h.parse_status == OK for h in hyps) else (
        OK if ok else PARSE_FAILURE
    )
    return {
        "parse_status": status,
        "hypotheses": hyps,
        "abstain": bool(obj.get("abstain")) and not ok,
        "n_ok": len(ok),
        "n_parse_failure": len(hyps) - len(ok),
    }
