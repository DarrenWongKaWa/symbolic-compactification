"""Bounded structural transformation primitives (structure-first).

A *primitive* is a small, targeted SymPy-backed rewrite. Each returns a
``TransformResult`` carrying the before/after expressions so the step is
LOCALLY CHECKABLE through the verifier's residual ``before - after`` (run it
through ``verify_equivalent`` on the two text forms to certify). Primitives
record their own ``primitive`` name for telemetry.

Deliberately NOT a rewrite framework: these are a fixed handful of bounded
operations. They never expand/lower structural representations (Sum /
Piecewise / indexed calls); the structural form stays primary.

Every primitive is op-count capped via ``TRANSFORM_POLICY['ops_cap']``: if a
candidate result would exceed the cap the transform is reported as not
applied, so a primitive can never blow up an expression silently.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import sympy

from .budgets import BudgetExceeded, run_symbolic_operation
from .models import AdapterError

__all__ = [
    "TransformResult", "TRANSFORM_POLICY", "get_transform_policy",
    "set_transform_policy",
    "combine_identical_sums", "factor_common_kernel", "collect_common_factor",
    "canonicalize_equivalent_arguments", "factor_terms", "together", "cancel",
    "residual_of",
]


# --------------------------------------------------------------------------- #
# transform policy (limits are POLICY, never silently edited constants)
# --------------------------------------------------------------------------- #

_DEFAULT_TRANSFORM_POLICY: dict = {
    # a primitive's result may not exceed this op count; over-cap results are
    # discarded (transform reported as not applied)
    "ops_cap": 8000,
}

TRANSFORM_POLICY: dict = dict(_DEFAULT_TRANSFORM_POLICY)


def get_transform_policy() -> dict:
    return dict(TRANSFORM_POLICY)


def set_transform_policy(**overrides) -> dict:
    unknown = set(overrides) - set(_DEFAULT_TRANSFORM_POLICY)
    if unknown:
        raise AdapterError("TRANSFORM_POLICY_KEY_UNKNOWN")
    candidate = dict(TRANSFORM_POLICY)
    candidate.update(overrides)
    cap = candidate["ops_cap"]
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
        raise AdapterError("TRANSFORM_POLICY_VALUE_INVALID")
    TRANSFORM_POLICY.update(overrides)
    return get_transform_policy()


# --------------------------------------------------------------------------- #
# result record
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class TransformResult:
    """Outcome of one primitive: before/after plus a telemetry name.

    ``applied`` is True only when the primitive actually changed the
    expression AND stayed within the op-count cap. ``note`` explains the
    no-op reason when ``applied`` is False.
    """

    primitive: str
    applied: bool
    before: sympy.Expr
    after: sympy.Expr
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "primitive": self.primitive,
            "applied": self.applied,
            "before": str(self.before),
            "after": str(self.after),
            "note": self.note,
        }


def residual_of(result: TransformResult) -> sympy.Expr:
    """Local checkability: a bounded expansion of ``before - after``.

    The before/after views remain stored on the result; only this explicit
    local proof diagnostic is lowered, under the central expansion budget.
    """
    return run_symbolic_operation(
        "expand", sympy.expand, (result.before - result.after,),
        budget_key="expand_seconds")


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #

def _no_op(name: str, expr: sympy.Expr, note: str) -> TransformResult:
    return TransformResult(primitive=name, applied=False,
                           before=expr, after=expr, note=note)


def _capped(name: str, expr: sympy.Expr, candidate: sympy.Expr,
            ops_cap: Optional[int] = None) -> TransformResult:
    """Accept ``candidate`` iff it changed the expression and fits the cap."""
    cap = ops_cap if ops_cap is not None else TRANSFORM_POLICY["ops_cap"]
    if not isinstance(cap, int) or isinstance(cap, bool) or cap <= 0:
        raise AdapterError("TRANSFORM_POLICY_VALUE_INVALID")
    if sympy.count_ops(candidate, visual=False) > cap:
        return _no_op(name, expr, "ops_cap_exceeded")
    if candidate == expr:
        return _no_op(name, expr, "no_change")
    return TransformResult(primitive=name, applied=True,
                           before=expr, after=candidate)


def _factor_text(expr):
    return str(sympy.factor(expr))


def _factor_terms_text(expr):
    return str(sympy.factor_terms(expr))


def _together_text(expr):
    return str(sympy.together(expr))


def _cancel_text(expr):
    return str(sympy.cancel(expr))


def _budgeted_candidate(name: str, expr: sympy.Expr, text_fn,
                        budget_key: str, *, preserve_factoring: bool = False
                        ) -> sympy.Expr:
    """Execute a transform in a worker and reconstruct its structural text.

    SymPy's default pickle reducer may evaluate intentionally factored nodes
    while crossing a process boundary. Returning trusted engine-generated
    text and rebuilding it with ``evaluate=False`` preserves that structure
    without introducing a custom symbolic IR.
    """
    text = run_symbolic_operation(
        name, text_fn, (expr,), budget_key=budget_key)
    local = {symbol.name: symbol for symbol in expr.atoms(sympy.Symbol)}
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.core.function.AppliedUndef):
            local[type(sub).__name__] = sympy.Function(type(sub).__name__)
    return sympy.sympify(
        text, locals=local, evaluate=not preserve_factoring)


# --------------------------------------------------------------------------- #
# primitives
# --------------------------------------------------------------------------- #

def combine_identical_sums(expr: sympy.Expr,
                           ops_cap: Optional[int] = None) -> TransformResult:
    """Combine ``Sum(K*A) + Sum(K*B)`` over IDENTICAL index sets.

    Works SYMBOLICALLY on the structural Sum nodes (no concrete-index
    expansion): top-level Sum terms of an ``Add`` that share the exact same
    limits are folded into one Sum whose body is the sum of the bodies.
    Linearity of summation makes ``before - after`` expand to 0.
    """
    name = "combine_identical_sums"
    if not isinstance(expr, sympy.Add):
        return _no_op(name, expr, "not_an_Add")
    by_limits: dict = {}
    others: list = []
    for term in expr.args:
        if isinstance(term, sympy.Sum):
            by_limits.setdefault(term.limits, []).append(term)
        else:
            others.append(term)
    if not any(len(v) >= 2 for v in by_limits.values()):
        return _no_op(name, expr, "no_identical_sum_limits")
    new_terms = list(others)
    for limits, sums in by_limits.items():
        if len(sums) >= 2:
            body = sympy.Add(*[s.args[0] for s in sums])
            new_terms.append(sympy.Sum(body, *limits))
        else:
            new_terms.append(sums[0])
    candidate = sympy.Add(*new_terms)
    return _capped(name, expr, candidate, ops_cap)


def factor_common_kernel(expr: sympy.Expr,
                         ops_cap: Optional[int] = None) -> TransformResult:
    """``sympy.factor``-based common-kernel extraction (bounded)."""
    name = "factor_common_kernel"
    try:
        candidate = _budgeted_candidate(
            name, expr, _factor_text, "factor_seconds",
            preserve_factoring=True)
    except BudgetExceeded:
        raise
    except Exception:
        return _no_op(name, expr, "factor_failed")
    return _capped(name, expr, candidate, ops_cap)


def collect_common_factor(expr: sympy.Expr,
                          ops_cap: Optional[int] = None) -> TransformResult:
    """``sympy.factor_terms``-based common-factor collection (bounded)."""
    name = "collect_common_factor"
    try:
        candidate = _budgeted_candidate(
            name, expr, _factor_terms_text, "factor_terms_seconds",
            preserve_factoring=True)
    except BudgetExceeded:
        raise
    except Exception:
        return _no_op(name, expr, "factor_terms_failed")
    return _capped(name, expr, candidate, ops_cap)


def canonicalize_equivalent_arguments(
        expr: sympy.Expr,
        symmetric_functions: frozenset = frozenset(),
        ops_cap: Optional[int] = None) -> TransformResult:
    """Normalize argument order where it is SAFE to do so.

    Only functions explicitly declared ``symmetric_functions`` are rewritten
    (their arguments sorted canonically). SymPy's own commutative builtins
    are already canonical. Sorting arguments of an arbitrary undefined
    function is NOT safe and is therefore never done by default.
    """
    name = "canonicalize_equivalent_arguments"
    if not symmetric_functions:
        return _no_op(name, expr, "no_symmetric_functions_declared")

    def _rewrite(sub):
        if isinstance(sub, sympy.core.function.AppliedUndef):
            fname = type(sub).__name__
            if fname in symmetric_functions:
                ordered = sorted(sub.args, key=sympy.default_sort_key)
                if tuple(ordered) != tuple(sub.args):
                    return sympy.Function(fname)(*ordered)
        return sub

    candidate = expr.replace(
        lambda sub: isinstance(sub, sympy.core.function.AppliedUndef)
        and type(sub).__name__ in symmetric_functions,
        _rewrite)
    return _capped(name, expr, candidate, ops_cap)


def factor_terms(expr: sympy.Expr,
                 ops_cap: Optional[int] = None) -> TransformResult:
    """Thin bounded wrapper over ``sympy.factor_terms``."""
    name = "factor_terms"
    try:
        candidate = _budgeted_candidate(
            name, expr, _factor_terms_text, "factor_terms_seconds",
            preserve_factoring=True)
    except BudgetExceeded:
        raise
    except Exception:
        return _no_op(name, expr, "factor_terms_failed")
    return _capped(name, expr, candidate, ops_cap)


def together(expr: sympy.Expr, ops_cap: Optional[int] = None) -> TransformResult:
    """Thin bounded wrapper over ``sympy.together`` (common denominator)."""
    name = "together"
    try:
        candidate = _budgeted_candidate(
            name, expr, _together_text, "together_seconds")
    except BudgetExceeded:
        raise
    except Exception:
        return _no_op(name, expr, "together_failed")
    return _capped(name, expr, candidate, ops_cap)


def cancel(expr: sympy.Expr, ops_cap: Optional[int] = None) -> TransformResult:
    """Thin bounded wrapper over ``sympy.cancel`` (cancel common factors)."""
    name = "cancel"
    try:
        candidate = _budgeted_candidate(
            name, expr, _cancel_text, "cancel_seconds")
    except BudgetExceeded:
        raise
    except Exception:
        return _no_op(name, expr, "cancel_failed")
    return _capped(name, expr, candidate, ops_cap)


# Ordered set of primitives the verifier may attempt on large residuals
# (structure-first: targeted primitives only, never a global simplify).
TARGETED_PRIMITIVES = (
    combine_identical_sums,
    collect_common_factor,
    together,
    cancel,
)
