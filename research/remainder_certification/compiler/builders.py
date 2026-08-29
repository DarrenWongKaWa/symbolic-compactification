"""Builders for atom-local RemainderCertificate fields.

Does not mint hop ZERO. Class C/D cannot remain CERTIFIED.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Optional

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    METHOD_VERSION,
    NEIGHBORHOOD_CERTIFIED,
    NONANALYTIC,
    REMAINDER_VERDICTS,
    RemainderCertificate,
    UNKNOWN,
    validate_certificate,
)

EMPTY_DOMAIN_CONDITION = "unproved: no domain condition supplied"

_BLOCKING_CLASSES = frozenset({C_GENERICITY, D_HUMAN_REQUIRED})
_AB_CLASSES = frozenset({A_DECLARED, B_DERIVED})


def sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def hash_assumptions(items: Iterable[dict[str, Any]] | None) -> str:
    payload = json.dumps(
        list(items or []),
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return sha256_text(payload)


def remainder_form_for_order(n: int) -> str:
    k = n + 1
    return f"R_{{{k}}}(t) = O(t^{{{k}}})"


def as_nonneg_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    return None


def pick(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default


def as_step_dict(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
    if isinstance(result, dict):
        return dict(result)
    to_dict = getattr(result, "to_dict", None)
    if callable(to_dict):
        data = to_dict()
        if isinstance(data, dict):
            return dict(data)
    out: dict[str, Any] = {}
    for key in (
        "ok",
        "verdict",
        "domain_conditions",
        "conditions",
        "remainder_form",
        "bound",
        "expansion_point",
        "perturbation",
        "argument",
        "analyticity_certificate",
        "distance_to_singularity",
        "required_small_t_condition",
        "assumptions_used",
        "proof_dependencies",
        "function_family",
        "function_order",
        "note",
        "unsupported",
        "error",
    ):
        if hasattr(result, key):
            out[key] = getattr(result, key)
    return out


def coerce_assumption(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        out = dict(item)
        if "class" not in out and "klass" in out:
            out["class"] = out["klass"]
        if "class" not in out:
            out["class"] = "UNCLASSIFIED"
        return out
    return {"class": "UNCLASSIFIED", "predicate": str(item)}


def merge_assumptions(*groups: Iterable[Any] | None) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for group in groups:
        if not group:
            continue
        for raw in group:
            item = coerce_assumption(raw)
            key = (str(item.get("class") or ""), str(item.get("predicate") or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def merge_texts(*groups: Iterable[Any] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for group in groups:
        if not group:
            continue
        for raw in group:
            text = str(raw).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
    return out


def uses_blocking_assumptions(items: Iterable[dict[str, Any]] | None) -> bool:
    for item in items or []:
        klass = item.get("class") if isinstance(item, dict) else None
        if klass in _BLOCKING_CLASSES:
            return True
        if klass not in _AB_CLASSES:
            return True
    return False


def uses_class_cd(items: Iterable[dict[str, Any]] | None) -> bool:
    for item in items or []:
        klass = item.get("class") if isinstance(item, dict) else None
        if klass in _BLOCKING_CLASSES:
            return True
    return False


def neighborhood_is_certified(verdict: str) -> bool:
    return verdict == NEIGHBORHOOD_CERTIFIED


def domain_fields(source: Any) -> dict[str, Any]:
    data = as_step_dict(source) if not isinstance(source, dict) else dict(source)
    if not data and source not in (None, ""):
        if isinstance(source, str):
            data = {"domain_conditions": [source], "verdict": UNKNOWN}
        else:
            data = as_step_dict(source)
    conditions = data.get("domain_conditions")
    if conditions is None:
        conditions = data.get("conditions")
    if isinstance(conditions, str):
        conditions = [conditions]
    assumptions = data.get("assumptions_used") or data.get("assumptions") or []
    deps = data.get("proof_dependencies") or data.get("dependencies") or []
    analyticity = data.get("analyticity_certificate")
    if analyticity is None:
        analyticity = data.get("analyticity")
    if not isinstance(analyticity, dict):
        analyticity = {}
    verdict = str(data.get("verdict") or UNKNOWN)
    if verdict not in REMAINDER_VERDICTS:
        verdict = UNKNOWN
    return {
        "verdict": verdict,
        "domain_conditions": [str(c) for c in (conditions or []) if str(c).strip()],
        "analyticity_certificate": analyticity,
        "distance_to_singularity": str(
            pick(data, "distance_to_singularity", "distance") or ""
        ),
        "assumptions_used": merge_assumptions(assumptions),
        "proof_dependencies": merge_texts(deps),
        "function_family": str(pick(data, "function_family", "family") or ""),
        "function_order": str(pick(data, "function_order", "order") or ""),
        "required_small_t_condition": str(
            pick(data, "required_small_t_condition", "small_t") or ""
        ),
    }


def atom_fields(atom: Any) -> dict[str, str]:
    if atom is None:
        return {"function_family": "", "function_order": "", "argument": ""}
    if isinstance(atom, str):
        return {"function_family": atom, "function_order": "", "argument": ""}
    if isinstance(atom, dict):
        family = str(
            atom.get("function_family")
            or atom.get("function_head")
            or atom.get("family")
            or ""
        )
        order = str(atom.get("function_order") or atom.get("order") or "")
        argument = str(atom.get("argument") or "")
        return {
            "function_family": family,
            "function_order": order,
            "argument": argument,
        }
    family = str(
        getattr(atom, "function_family", "")
        or getattr(atom, "function_head", "")
        or ""
    )
    if not family:
        func = getattr(atom, "func", None)
        if func is not None:
            family = str(getattr(func, "__name__", func) or "")
    order = str(
        getattr(atom, "function_order", "") or getattr(atom, "order", "") or ""
    )
    argument = str(getattr(atom, "argument", "") or "")
    return {
        "function_family": family,
        "function_order": order,
        "argument": argument,
    }


def affine_fields(source: Any) -> dict[str, Any]:
    if source is None:
        return {
            "ok": False,
            "expansion_point": "",
            "perturbation": "",
            "argument": "",
            "structured": False,
        }
    if isinstance(source, str):
        return {
            "ok": False,
            "expansion_point": "",
            "perturbation": "",
            "argument": source,
            "structured": False,
        }
    data = source if isinstance(source, dict) else as_step_dict(source)
    expansion_point = str(
        pick(data, "expansion_point", "z0", "alpha_0", "alpha", "expansion") or ""
    )
    perturbation = str(pick(data, "perturbation", "c", "beta") or "")
    argument = str(pick(data, "argument", "argument_text") or "")
    structured = bool(expansion_point or perturbation)
    explicit_ok = data.get("ok")
    if explicit_ok is False:
        ok = False
    elif explicit_ok is True:
        ok = True
    else:
        ok = structured
    return {
        "ok": ok,
        "expansion_point": expansion_point,
        "perturbation": perturbation,
        "argument": argument,
        "structured": structured,
        "unsupported": bool(data.get("unsupported")),
        "assumptions_used": data.get("assumptions_used") or [],
        "proof_dependencies": data.get("proof_dependencies") or [],
        "domain_conditions": data.get("domain_conditions")
        or data.get("conditions")
        or [],
        "note": str(data.get("note") or ""),
    }


def merge_domain_verdicts(verdicts: Iterable[str]) -> str:
    found = [v for v in verdicts if v]
    if any(v == NONANALYTIC for v in found):
        return NONANALYTIC
    if not found:
        return UNKNOWN
    if any(v == ASSUMPTION_REQUIRED for v in found):
        return ASSUMPTION_REQUIRED
    if any(v == UNKNOWN for v in found):
        return UNKNOWN
    if found and all(v == CERTIFIED for v in found):
        return CERTIFIED
    return UNKNOWN


def finalize_certificate(cert: RemainderCertificate) -> RemainderCertificate:
    """Fill hashes, force nonempty domain, never emit hop ZERO."""
    if not cert.domain_conditions:
        cert.domain_conditions = [EMPTY_DOMAIN_CONDITION]
        if cert.verdict == CERTIFIED:
            cert.verdict = UNKNOWN
    if uses_class_cd(cert.assumptions_used) and cert.verdict == CERTIFIED:
        cert.verdict = ASSUMPTION_REQUIRED
    if uses_blocking_assumptions(cert.assumptions_used) and cert.verdict == CERTIFIED:
        cert.verdict = ASSUMPTION_REQUIRED
    if cert.verdict == HOP_ZERO or cert.verdict not in REMAINDER_VERDICTS:
        cert.verdict = UNKNOWN
    if cert.neighborhood_verdict == HOP_ZERO:
        cert.neighborhood_verdict = UNKNOWN
    cert.method_version = METHOD_VERSION
    cert.assumptions_hash = hash_assumptions(cert.assumptions_used)
    cert.argument_text_hash = sha256_text(cert.argument)
    cert.verdict = validate_certificate(cert)
    return cert
