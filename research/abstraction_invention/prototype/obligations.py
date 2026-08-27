"""Proof obligations: each family member equals the instantiated template.

Not a single E - E' = 0. Fail-closed; UNKNOWN is not success.
"""
from __future__ import annotations

from research.abstraction_invention.prototype.schema import AbstractionHypothesis
from research.method_v2.expand import expand_text
from symbolic_compactification import NONZERO, UNKNOWN, ZERO, verify_equivalent
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget
from symbolic_compactification.models import AdapterError


def _theta_subs(template: str, theta: dict[str, str]) -> str:
    return expand_text(template, theta or {})


def adjudicate_hypothesis(
    hyp: AbstractionHypothesis,
    symbols: list,
    functions: list | None,
) -> dict:
    functions = functions or []
    results = []
    n_zero = n_nz = n_unk = 0
    for im in hyp.instance_maps:
        instantiated = _theta_subs(hyp.template, im.theta)
        if im.operator_on_template == "d/dtheta":
            # Parser has no Derivative node. Re-check with sympy.diff on
            # parsed template vs member. This is exact CAS identity, not a
            # residual ZERO and not numeric agreement.
            try:
                import sympy
                from symbolic_compactification import parse_expression
                tmpl = parse_expression(
                    hyp.template, symbols, functions=functions or None)
                mem = parse_expression(
                    im.member, symbols, functions=functions or None)
                xname = next(iter(im.theta), None)
                x = next((s for s in tmpl.free_symbols if s.name == xname), None)
                if x is None and tmpl.free_symbols:
                    x = next(iter(tmpl.free_symbols))
                ok = x is not None and (
                    sympy.diff(tmpl, x) == mem
                    or sympy.expand(sympy.diff(tmpl, x) - mem) == 0
                )
                v = ZERO if ok else NONZERO
            except Exception:
                v = UNKNOWN
            if v == ZERO:
                n_zero += 1
            elif v == NONZERO:
                n_nz += 1
            else:
                n_unk += 1
            results.append({
                "member": im.member,
                "instantiated": instantiated,
                "verdict": v,
                "note": "sympy.diff_identity",
            })
            continue
        try:
            r = run_with_budget(
                verify_equivalent,
                (im.member, instantiated, symbols),
                kwargs={"functions": functions or None},
                seconds=6.0,
                operation="ai_obligation",
            )
            v = r.verdict
        except (BudgetExceeded, AdapterError):
            v = UNKNOWN
        if v == ZERO:
            n_zero += 1
        elif v == NONZERO:
            n_nz += 1
        else:
            n_unk += 1
        results.append({
            "member": im.member,
            "instantiated": instantiated,
            "verdict": v,
        })
    certified = n_zero == len(hyp.instance_maps) and n_zero >= 2 and n_nz == 0
    return {
        "operator": hyp.operator,
        "template": hyp.template,
        "family": hyp.family,
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "certified_abstraction": certified,
        "false_promotion": False,
        "obligations": results,
        "hypothesis": hyp.to_dict(),
    }
