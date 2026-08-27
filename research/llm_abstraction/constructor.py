"""Instantiate LLM hypotheses. Fail-closed. Does not modify frozen obligations."""
from __future__ import annotations

from typing import Any

import sympy

from research.llm_abstraction.schema import LLMStructureHypothesis, OK
from symbolic_compactification import NONZERO, UNKNOWN, ZERO, parse_expression, verify_equivalent
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget
from symbolic_compactification.models import AdapterError


def _theta(imap: Any) -> dict[str, str]:
    if isinstance(imap, dict):
        t = imap.get("theta") or imap.get("map") or {}
        if isinstance(t, dict):
            return {str(k): str(v) for k, v in t.items()}
    return {}


def _member(imap: Any, fallback: str = "") -> str:
    if isinstance(imap, dict):
        return str(imap.get("member") or fallback)
    return fallback


def _op_name(imap: Any, operators: list, member: str) -> str:
    if isinstance(imap, dict) and imap.get("O"):
        return str(imap.get("O")).lower()
    for op in operators or []:
        if isinstance(op, dict) and str(op.get("member")) == member:
            return str(op.get("O") or "identity").lower()
        if isinstance(op, str):
            return op.lower()
    if isinstance(imap, dict):
        return str(imap.get("operator_on_template") or "identity").lower()
    return "identity"


def _rhs_if_definition(template: str) -> str:
    """Format only: 'Name(...) = expr' → expr. Does not invent symbols."""
    import re
    m = re.match(r"^[A-Za-zΑ-ω][A-Za-z0-9_θΘ]*\s*(\([^;]*\))?\s*=\s*(.+)$", template.strip())
    if m and "=" not in m.group(2):
        return m.group(2).strip()
    return template


def _subs_text(template: str, theta: dict[str, str]) -> str:
    out = _rhs_if_definition(template)
    # longest keys first so theta0 is not split by theta
    for k, v in sorted(theta.items(), key=lambda kv: -len(kv[0])):
        out = out.replace(k, f"({v})")
    return out


def _diff_ok(template: str, member: str, theta: dict, symbols, functions) -> str:
    try:
        tmpl = parse_expression(template, symbols, functions=functions or None)
        mem = parse_expression(member, symbols, functions=functions or None)
        xname = next(iter(theta), None)
        x = next((s for s in tmpl.free_symbols if s.name == xname), None)
        if x is None and tmpl.free_symbols:
            x = next(iter(tmpl.free_symbols))
        if x is None:
            return UNKNOWN
        d = sympy.diff(tmpl, x)
        if d == mem or sympy.expand(d - mem) == 0:
            return ZERO
        return NONZERO
    except Exception:
        return UNKNOWN


def _permute_ok(template: str, member: str, symbols, functions) -> str:
    try:
        tmpl = parse_expression(template, symbols, functions=functions or None)
        mem = parse_expression(member, symbols, functions=functions or None)
        syms = list(tmpl.free_symbols)
        if len(syms) < 2:
            return UNKNOWN
        a, b = syms[0], syms[1]
        swapped = tmpl.xreplace({a: b, b: a})
        if swapped == mem or sympy.expand(swapped - mem) == 0:
            return ZERO
        return NONZERO
    except Exception:
        return UNKNOWN


def construct_and_verify(
    hyp: LLMStructureHypothesis,
    symbols: list,
    functions: list | None,
) -> dict[str, Any]:
    functions = functions or []
    if hyp.parse_status != OK:
        return {
            "constructable": False,
            "certified": False,
            "n_zero": 0, "n_nonzero": 0, "n_unknown": 1,
            "obligations": [],
            "note": hyp.parse_error or "parse_failure",
        }
    maps = list(hyp.instance_maps or [])
    if not maps and hyp.target_members:
        maps = [{"member": m, "theta": {}, "O": "identity"} for m in hyp.target_members]
    results = []
    n_zero = n_nz = n_unk = 0
    for imap in maps:
        member = _member(imap)
        theta = _theta(imap)
        op = _op_name(imap, hyp.operators, member)
        instantiated = _subs_text(hyp.latent_object, theta)
        if any(k in op for k in ("d/d", "diff", "deriv")):
            v = _diff_ok(hyp.latent_object, member, theta, symbols, functions)
            note = "sympy.diff_identity"
        elif "perm" in op or op == "swap":
            v = _permute_ok(hyp.latent_object, member, symbols, functions)
            note = "permute"
        else:
            note = "identity_or_specialize"
            try:
                r = run_with_budget(
                    verify_equivalent,
                    (member, instantiated, symbols),
                    kwargs={"functions": functions or None},
                    seconds=6.0,
                    operation="llm_obligation",
                )
                v = r.verdict
            except (BudgetExceeded, AdapterError, Exception):
                v = UNKNOWN
        if v == ZERO:
            n_zero += 1
        elif v == NONZERO:
            n_nz += 1
        else:
            n_unk += 1
        results.append({
            "member": member,
            "instantiated": instantiated,
            "operator": op,
            "verdict": v,
            "note": note,
        })
    certified = n_zero >= 1 and n_nz == 0 and n_unk == 0 and n_zero == len(results)
    return {
        "constructable": bool(results) and n_unk < len(results),
        "certified": bool(certified),
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "obligations": results,
        "hypothesis_type": hyp.hypothesis_type,
        "d_level": hyp.d_level,
        "latent_object": hyp.latent_object,
    }
