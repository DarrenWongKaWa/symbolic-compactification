"""Deterministic scientific packager (one isolated proposer, no ensemble).

Emits named-kernel / named-generator hypotheses that MUST expand to a
closed expression. Never proposes drop-Piecewise or new assumptions.
"""
from __future__ import annotations

import sympy

from symbolic_compactification import (
    collect_common_factor,
    combine_identical_sums,
    parse_expression,
)
from symbolic_compactification.models import AdapterError
from symbolic_compactification.structure import structure_summary


def _parse(text, symbols, functions):
    return parse_expression(text, symbols, functions=functions or None)


def cheap_transforms(text: str, symbols: list, functions: list) -> tuple[str, list]:
    notes = []
    try:
        expr = _parse(text, symbols, functions)
    except AdapterError:
        return text, notes
    r = combine_identical_sums(expr)
    if r.applied:
        expr = r.after
        notes.append("combine_identical_sums")
    r = collect_common_factor(expr)
    if r.applied:
        expr = r.after
        notes.append("collect_common_factor")
    return str(expr), notes


def package_scientific(text: str, symbols: list, functions: list) -> list[dict]:
    """Return 0–3 hypotheses with closed candidate_text + definitions."""
    out = []
    try:
        expr = _parse(text, symbols, functions)
    except AdapterError:
        return out
    # D3: factored A*(u+v) → Phi := u+v  (A may be a symbol, not a numeric coeff)
    if isinstance(expr, sympy.Mul):
        adds = [a for a in expr.args if isinstance(a, sympy.Add)]
        others = [a for a in expr.args if not isinstance(a, sympy.Add)]
        if len(adds) == 1 and others:
            rest = adds[0]
            coeff = sympy.Mul(*others) if len(others) > 1 else others[0]
            out.append({
                "candidate_text": f"({coeff})*Phi",
                "hypothesis_definitions": {"Phi": str(rest)},
                "abstraction_level": "D3",
                "hypothesis_family": "master",
                "rationale": "name the collected parenthesis as a master object",
            })
    # D2/D3: Sum((p+q)*K, limits) already compact; name K if Sum
    for s in expr.atoms(sympy.Sum):
        body = s.args[0]
        if isinstance(body, sympy.Mul):
            lims = ", ".join(str(lim) for lim in s.args[1:])
            out.append({
                "candidate_text": f"Sum(Kbody, {lims})",
                "hypothesis_definitions": {"Kbody": str(body)},
                "abstraction_level": "D2",
                "hypothesis_family": "kernel",
                "rationale": "record the summand as a reusable kernel body",
            })
            break
    # D5: F(n,m)+F(m,n)
    if isinstance(expr, sympy.Add) and len(expr.args) == 2:
        a, b = expr.args
        out.append({
            "candidate_text": "P + Pswap",
            "hypothesis_definitions": {"P": str(a), "Pswap": str(b)},
            "abstraction_level": "D5",
            "hypothesis_family": "symmetry",
            "rationale": "name the ordered-pair factor and its permute",
        })
    return out


def propose(text: str, symbols: list, functions: list) -> list[dict]:
    transformed, notes = cheap_transforms(text, symbols, functions)
    cands = []
    if transformed != text:
        cands.append({
            "candidate_text": transformed,
            "hypothesis_definitions": {},
            "abstraction_level": "D1" if "collect" in "".join(notes) else "D2",
            "hypothesis_family": "algebra",
            "rationale": "named structural transforms: " + ",".join(notes),
        })
    cands.extend(package_scientific(transformed, symbols, functions))
    return cands
