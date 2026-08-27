"""Stage A–F evaluation. Gold is evaluator-only."""
from __future__ import annotations

from typing import Any, Optional

import sympy

from research.llm_abstraction.quality import looks_representation_change
from research.llm_abstraction.schema import (
    ABSTAIN,
    BLOCKED,
    LLMStructureHypothesis,
    OK,
    PARSE_FAILURE,
    ProposeResult,
    TYPE_TO_DLEVEL,
    UNNECESSARY_STRUCTURE,
)
from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError

TYPE_ALIASES = {
    "antiunification": {"parameterized_family"},
    "master_derivative": {"derivative_family", "master_function", "recurrence_family"},
    "confluence": {"confluent_representation", "divided_difference"},
    "permutation": {"symmetry_invariant", "tensor_generator"},
    "repeated_kernel": {"repeated_kernel"},
    "algebraic_equivalence": {"parameterized_family", "other_structured"},
    "operator": {"derivative_family", "symmetry_invariant", "tensor_generator"},
}


def _norm(s: str) -> str:
    return "".join((s or "").split())


def _canon(text: str, item: dict) -> str:
    try:
        e = parse_expression(
            text, item.get("symbols") or [],
            functions=item.get("functions") or None,
        )
        return sympy.srepr(e)
    except (AdapterError, Exception):
        return _norm(text)


def _type_hit(htype: str, item: dict) -> bool:
    gold = set(item.get("gold_types") or [])
    if item.get("gold_operator"):
        gold |= TYPE_ALIASES.get(item["gold_operator"], set())
        gold.add(item["gold_operator"])
    if item.get("gold_mode"):
        gold |= TYPE_ALIASES.get(item["gold_mode"], set())
    if not gold:
        return False
    if htype in gold:
        return True
    for g in gold:
        if htype in TYPE_ALIASES.get(g, set()):
            return True
    return False


def _targeting_hit(hyp: LLMStructureHypothesis, item: dict) -> bool:
    gold = [_canon(x, item) for x in (item.get("gold_members") or [])]
    if not gold:
        return False
    got = {_canon(x, item) for x in hyp.target_members}
    # also allow latent covering members
    if hyp.latent_object:
        got.add(_canon(hyp.latent_object, item))
    return set(gold) <= got or all(any(_norm(g) in _norm(m) or _norm(m) in _norm(g)
                                       for m in hyp.target_members + [hyp.latent_object])
                                   for g in (item.get("gold_members") or []))


def _best_construction(constructions: Optional[Any]) -> dict:
    if constructions is None:
        return {}
    if isinstance(constructions, dict) and "n_zero" in constructions:
        return constructions
    if isinstance(constructions, list) and constructions:
        cert = [c for c in constructions if isinstance(c, dict) and c.get("certified")]
        if cert:
            return cert[0]
        return constructions[0] if isinstance(constructions[0], dict) else {}
    return {}


def evaluate(
    item: dict,
    result: ProposeResult,
    constructions: Optional[Any] = None,
) -> dict[str, Any]:
    polarity = item.get("polarity") or "positive"
    forbidden = set(item.get("forbidden_types") or [])
    prefer_abstain = bool(item.get("prefer_abstain")) or polarity in {"negative", "trap"}
    shallow_ok = bool(item.get("shallow_ok"))
    cons = _best_construction(constructions)
    all_cons = constructions if isinstance(constructions, list) else ([constructions] if constructions else [])
    all_cons = [c for c in all_cons if isinstance(c, dict)]

    parse_failure = result.parse_status == PARSE_FAILURE
    blocked = result.parse_status == BLOCKED
    abstain = result.parse_status == ABSTAIN or (result.abstain and not result.hypotheses)
    ok_hyps = [h for h in result.hypotheses if h.parse_status == OK]

    type_hit = any(_type_hit(h.hypothesis_type, item) for h in ok_hyps)
    targeting_hit = any(_targeting_hit(h, item) for h in ok_hyps)
    unnecessary = any(UNNECESSARY_STRUCTURE in (h.quality_flags or []) for h in ok_hyps)
    shallow = any("shallow" in (h.quality_flags or []) for h in ok_hyps)
    taut = any("tautological" in (h.quality_flags or []) for h in ok_hyps)
    repr_chg = any(looks_representation_change(h) for h in ok_hyps)
    construction_ok = any(c.get("constructable") for c in all_cons)
    certified = any(c.get("certified") for c in all_cons)
    n_zero = sum(int(c.get("n_zero") or 0) for c in all_cons)
    n_nz = sum(int(c.get("n_nonzero") or 0) for c in all_cons)
    n_unk = sum(int(c.get("n_unknown") or 0) for c in all_cons)

    d_attempted = sorted({h.d_level for h in ok_hyps})
    d_certified = sorted({c.get("d_level") for c in all_cons if c.get("certified") and c.get("d_level")})

    proposed_forbidden = any(h.hypothesis_type in forbidden for h in ok_hyps) if forbidden else False
    false_abs = False
    if prefer_abstain and certified:
        false_abs = True
    if forbidden and any(h.hypothesis_type in forbidden and certified for h in ok_hyps):
        false_abs = True
    # Shallow hole-product certified on a negative is a false abstraction.
    if polarity == "negative" and certified and any(
        h.hypothesis_type in {"parameterized_family", "master_function", "generating_function"}
        for h in ok_hyps
    ):
        false_abs = True

    if blocked:
        quality = "unverifiable"
    elif parse_failure and not ok_hyps:
        quality = "parse_failure"
    elif abstain:
        quality = "abstain"
    elif unnecessary:
        quality = "unnecessary_structure"
    elif polarity == "trap" and (type_hit or targeting_hit) and not shallow_ok:
        quality = "shallow"
    elif shallow and not type_hit:
        quality = "shallow"
    elif taut and not certified:
        quality = "tautological"
    elif prefer_abstain:
        quality = "incorrect" if (certified or (type_hit and not prefer_abstain)) else (
            "useful" if abstain or not ok_hyps else "incorrect"
        )
        if prefer_abstain and not certified and not (type_hit and not item.get("gold_types")):
            # negative: proposing a family is incorrect unless abstain
            quality = "abstain" if abstain else ("incorrect" if ok_hyps else "abstain")
    elif type_hit and targeting_hit and certified:
        quality = "useful"
    elif type_hit and targeting_hit and not certified:
        quality = "gold-like-but-unsupported"
    elif type_hit and not targeting_hit:
        quality = "incorrect"
    elif ok_hyps and n_unk and not n_zero:
        quality = "unverifiable"
    elif ok_hyps:
        quality = "incorrect"
    else:
        quality = "abstain"

    # trap: shallow proposal is not useful
    if polarity == "trap" and quality == "useful":
        quality = "shallow"
    if unnecessary:
        quality = "unnecessary_structure"

    if prefer_abstain:
        if polarity == "negative":
            success = (not certified) and (not proposed_forbidden) and (not false_abs)
            if abstain or not ok_hyps:
                success = True
        else:
            success = (not certified) and (abstain or not ok_hyps)
    else:
        success = quality == "useful" or (type_hit and targeting_hit and certified)

    return {
        "id": item.get("id"),
        "category": item.get("category"),
        "polarity": polarity,
        "parse_status": result.parse_status,
        "parse_failure": parse_failure,
        "blocked": blocked,
        "abstain": bool(abstain),
        "n_hypotheses": len(ok_hyps),
        "n_parse_failure_hyps": len([h for h in result.hypotheses if h.parse_status == PARSE_FAILURE]),
        "type_hit": bool(type_hit),
        "targeting_hit": bool(targeting_hit),
        "construction_ok": bool(construction_ok),
        "certified": bool(certified),
        "false_abstraction": bool(false_abs),
        "unnecessary": bool(unnecessary),
        "representation_change": bool(repr_chg),
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "d_attempted": d_attempted,
        "d_certified": d_certified,
        "highest_attempted": d_attempted[-1] if d_attempted else None,
        "highest_certified": d_certified[-1] if d_certified else None,
        "quality": quality,
        "success": bool(success),
        "types": [h.hypothesis_type for h in ok_hyps],
    }
