"""Parse AC proposer JSON. Format-only wrap; no scientific repair."""
from __future__ import annotations

import json
import re
from typing import Any

REQUIRED = (
    "representation_type",
    "latent_object",
    "member_maps",
    "operators",
    "reconstruction_rule",
    "required_assumptions",
    "proof_obligations",
)

_FENCE = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.S)


def extract_json_object(text: str) -> tuple[dict | None, str | None]:
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


def parse_hypothesis(raw: Any) -> dict:
    if not isinstance(raw, dict):
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "hypothesis_not_object",
            "raw": raw,
        }
    missing = [f for f in REQUIRED if f not in raw]
    if missing:
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "missing_fields:" + ",".join(missing),
            "raw": raw,
        }
    rtype = raw.get("representation_type")
    if not isinstance(rtype, str) or not rtype.strip():
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "representation_type_empty",
            "raw": raw,
        }
    latent = raw.get("latent_object")
    if not isinstance(latent, str):
        latent = "" if latent is None else str(latent)
    maps = raw.get("member_maps")
    if not isinstance(maps, list):
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "member_maps_not_list",
            "raw": raw,
        }
    ops = raw.get("operators")
    if not isinstance(ops, list):
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "operators_not_list",
            "raw": raw,
        }
    recon = raw.get("reconstruction_rule")
    if not isinstance(recon, str):
        recon = "" if recon is None else str(recon)
    return {
        "parse_status": "OK",
        "parse_error": None,
        "representation_type": rtype.strip(),
        "latent_object": latent,
        "variables": _as_list(raw.get("variables")),
        "nodes": _as_list(raw.get("nodes")),
        "member_maps": maps,
        "operators": ops,
        "instance_maps": _as_list(raw.get("instance_maps")),
        "reconstruction_rule": recon,
        "required_assumptions": _as_list(raw.get("required_assumptions")),
        "proof_obligations": _as_list(raw.get("proof_obligations")),
        "rationale": raw.get("rationale") or "",
        "confidence": raw.get("confidence"),
    }


def parse_model_output(text: str) -> dict:
    obj, err = extract_json_object(text)
    if obj is None:
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": err or "json_decode_error",
            "abstain": False,
            "format_wrap": False,
            "hypotheses": [],
            "raw_obj": None,
        }
    format_wrap = False
    if "hypotheses" not in obj and "representation_type" in obj:
        obj = {"abstain": False, "abstain_reason": "", "hypotheses": [obj]}
        format_wrap = True
    if "hypotheses" not in obj:
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "missing_hypotheses",
            "abstain": bool(obj.get("abstain")),
            "format_wrap": format_wrap,
            "hypotheses": [],
            "raw_obj": obj,
        }
    hyps_in = obj.get("hypotheses")
    if not isinstance(hyps_in, list):
        return {
            "parse_status": "PARSE_FAILURE",
            "parse_error": "hypotheses_not_list",
            "abstain": bool(obj.get("abstain")),
            "format_wrap": format_wrap,
            "hypotheses": [],
            "raw_obj": obj,
        }
    hyps = [parse_hypothesis(h) for h in hyps_in[:5]]
    abstain = bool(obj.get("abstain")) and not any(h["parse_status"] == "OK" for h in hyps)
    if not hyps and obj.get("abstain"):
        status = "ABSTAIN"
    elif any(h["parse_status"] == "OK" for h in hyps):
        status = "OK"
    elif hyps:
        status = "PARSE_FAILURE"
    else:
        status = "ABSTAIN" if abstain else "PARSE_FAILURE"
    return {
        "parse_status": status,
        "parse_error": None if status != "PARSE_FAILURE" else (
            hyps[0]["parse_error"] if hyps else "no_hypotheses"
        ),
        "abstain": abstain,
        "abstain_reason": obj.get("abstain_reason") or "",
        "format_wrap": format_wrap,
        "hypotheses": hyps,
        "raw_obj": {k: obj[k] for k in obj if k != "hypotheses"},
    }
