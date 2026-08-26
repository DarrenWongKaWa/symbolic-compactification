"""Baselines that test structure discovery, not AST-size vs CAS.

B0 raw; B1 budgeted SymPy; B6 Method v2 packager (direct E→E');
B9 decomposed observe→H→construct→verify.
Direct vs decomposed is the mandatory ablation.
"""
from __future__ import annotations

from typing import Any

from research.method_v2.expand import expand_and_verify
from research.method_v2.packager import propose as packager_propose
from research.method_v2.packager import cheap_transforms
from research.structure_discovery.prototype.leakage import proposer_view, assert_no_leakage
from research.structure_discovery.prototype.orchestrator import run_decomposed
from symbolic_compactification import UNKNOWN, ZERO, parse_expression, verify_equivalent
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget
from symbolic_compactification.models import AdapterError
from symbolic_compactification.transforms import (
    collect_common_factor,
    combine_identical_sums,
    factor_terms,
    together,
)

try:
    import sympy
except ImportError:  # pragma: no cover
    sympy = None


def _public(item: dict) -> dict:
    view = proposer_view(item)
    assert_no_leakage(view)
    return view


def run_b0(item: dict) -> dict[str, Any]:
    pub = _public(item)
    return {
        "baseline": "B0",
        "certified_closed": pub["current"],
        "certified_structured": pub["current"],
        "hypothesis_types": [],
        "n_hypotheses": 0,
        "n_zero": 0,
        "n_nonzero": 0,
        "n_unknown": 0,
        "false_promotion": False,
        "d_attempted": [],
        "d_certified": [],
        "hypotheses": [],
        "graph": {"nodes": []},
    }


def run_b1(item: dict) -> dict[str, Any]:
    pub = _public(item)
    current = pub["current"]
    symbols = pub["symbols"]
    functions = pub.get("functions") or []
    notes = []
    text = current
    try:
        expr = parse_expression(current, symbols, functions=functions or None)
    except AdapterError as exc:
        return {
            "baseline": "B1",
            "certified_closed": current,
            "notes": f"parse:{exc.code}",
            "hypothesis_types": [],
            "n_hypotheses": 0,
            "n_zero": 0,
            "n_nonzero": 0,
            "n_unknown": 1,
            "false_promotion": False,
            "d_attempted": [],
            "d_certified": [],
            "hypotheses": [],
            "graph": {"nodes": []},
        }
    # Skip global simplify on Sum/Piecewise (known hang class).
    has_struct = bool(expr.atoms(sympy.Sum, sympy.Piecewise, sympy.Product))
    for prim, name in (
        (combine_identical_sums, "combine_identical_sums"),
        (collect_common_factor, "collect_common_factor"),
        (factor_terms, "factor_terms"),
        (together, "together"),
    ):
        try:
            r = prim(expr)
        except Exception:
            continue
        if getattr(r, "applied", False):
            expr = r.after
            notes.append(name)
    if not has_struct:
        try:
            simp = run_with_budget(sympy.simplify, (expr,), seconds=2.0,
                                   operation="simplify")
            if simp is not None and simp != expr:
                expr = simp
                notes.append("simplify")
        except (BudgetExceeded, Exception):
            notes.append("simplify_skipped")
    cand = str(expr)
    try:
        result = verify_equivalent(current, cand, symbols, functions=functions or None)
        verdict = result.verdict
    except AdapterError:
        verdict = UNKNOWN
        cand = current
    zero = verdict == ZERO
    return {
        "baseline": "B1",
        "certified_closed": cand if zero else current,
        "certified_structured": cand if zero else current,
        "hypothesis_types": ["structural_regrouping"] if notes else [],
        "n_hypotheses": 1 if notes else 0,
        "n_zero": int(zero and cand != current),
        "n_nonzero": int(verdict == "NONZERO"),
        "n_unknown": int(verdict == "UNKNOWN"),
        "false_promotion": False,
        "d_attempted": ["D1"] if notes else [],
        "d_certified": ["D1"] if zero and notes else [],
        "hypotheses": [],
        "graph": {"nodes": []},
        "notes": notes,
        "verdict": verdict,
    }


def run_b6_direct(item: dict) -> dict[str, Any]:
    """Direct E→E' via Method v2 packager (no typed hypothesis schema)."""
    pub = _public(item)
    current = pub["current"]
    symbols = pub["symbols"]
    functions = pub.get("functions") or []
    transformed, tnotes = cheap_transforms(current, symbols, functions)
    cands = packager_propose(current, symbols, functions)
    n_zero = n_nz = n_unk = 0
    types = []
    last_closed = current
    last_struct = current
    defs = {}
    nodes = []
    seen = set()
    if transformed != current:
        cands = [{
            "candidate_text": transformed,
            "hypothesis_definitions": {},
            "hypothesis_family": "algebra",
            "abstraction_level": "D1",
        }] + list(cands)
    for i, cand in enumerate(cands):
        text = cand.get("candidate_text") or ""
        d = cand.get("hypothesis_definitions") or {}
        if not text or text in seen:
            continue
        seen.add(text)
        fam = cand.get("hypothesis_family") or "direct"
        types.append(fam)
        try:
            expanded, result = run_with_budget(
                expand_and_verify, (current, text, d, symbols, functions),
                seconds=8.0, operation="b6_verify",
            )
            v = result.verdict
        except BudgetExceeded:
            expanded, v = text, UNKNOWN
        if v == ZERO:
            n_zero += 1
            last_closed = expanded
            last_struct = text
            defs = d
            state = "ZERO_CERTIFIED"
        elif v == "NONZERO":
            n_nz += 1
            state = "NONZERO_REFUTED"
        else:
            n_unk += 1
            state = "UNKNOWN"
        nodes.append({
            "node_id": f"D{i}", "state": state, "verdict": v,
            "hypothesis_type": fam, "closed": expanded, "structured": text,
            "d_level": cand.get("abstraction_level") or "D1",
        })
    return {
        "baseline": "B6",
        "architecture": "direct E→E'",
        "certified_closed": last_closed,
        "certified_structured": last_struct,
        "certified_definitions": defs,
        "hypothesis_types": types,
        "n_hypotheses": len(types),
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "false_promotion": False,
        "d_attempted": sorted({n["d_level"] for n in nodes}),
        "d_certified": sorted({n["d_level"] for n in nodes if n["state"] == "ZERO_CERTIFIED"}),
        "hypotheses": [{"hypothesis_type": t, "target_subexpressions": []} for t in types],
        "graph": {"nodes": nodes},
        "transform_notes": tnotes,
    }


def run_b9(item: dict, **kwargs) -> dict[str, Any]:
    pub = _public(item)
    run = run_decomposed(pub, **kwargs)
    run["baseline"] = "B9"
    return run


def run_b9_no_obs(item: dict) -> dict[str, Any]:
    """Ablation: empty observations → no typed hypotheses."""
    return run_b9(item, feature_mask={
        "repeated": False, "permutation": False, "denominators": False,
        "piecewise": False, "divided_difference": False, "families": False,
        "polygamma": False,
    })


def run_b9_conservative(item: dict) -> dict[str, Any]:
    return run_b9(item, aggressive=False)
