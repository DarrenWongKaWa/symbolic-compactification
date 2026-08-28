"""Order-of-limits auditor for two iterated one-parameter paths.

Never assume commuting limits. Timeout, size-guard, and CAS failure are
UNKNOWN, never CONSISTENT_ZERO.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Optional, Sequence, Union

import sympy

from research.iterated_confluence.schema import (
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    INCONSISTENT_NONZERO,
    PathConsistencyObligation,
    PathStep,
)
from research.scalable_verification.api import ZERO
from research.scalable_verification.confluence.engine import (
    LIMIT_OPS_CAP,
    _expr_equal,
    _is_finite,
    _ops_too_large,
    _step_lhopital,
    _step_newton_first_dd,
    _step_series,
    _step_substitution,
    _step_sympy_limit,
    _step_together_cancel,
    _step_valuation,
    check_limit,
)
from symbolic_compactification.budgets import BudgetExceeded

StepLike = Union[PathStep, Mapping[str, Any], Sequence[Any], tuple[Any, ...]]

_CONFIRM_SKIP = frozenset({"sympy.limit", "timeout", "size_guard"})


def _obligation(
    *,
    verdict: str,
    provenance: str,
    path_a: str = "",
    path_b: str = "",
    start: str = "start",
    end: str = "end",
    obligation_id: str = "path_consistency",
) -> PathConsistencyObligation:
    return PathConsistencyObligation(
        path_a=path_a,
        path_b=path_b,
        start=start,
        end=end,
        verdict=verdict,
        provenance=provenance,
        obligation_id=obligation_id,
    )


def _unknown(
    provenance: str,
    *,
    path_a: str = "",
    path_b: str = "",
    start: str = "start",
    end: str = "end",
) -> PathConsistencyObligation:
    return _obligation(
        verdict=CONSISTENCY_UNKNOWN,
        provenance=provenance,
        path_a=path_a,
        path_b=path_b,
        start=start,
        end=end,
    )


def _symbol_env(expr: Any, symbols: Any) -> dict[str, sympy.Expr]:
    env: dict[str, sympy.Expr] = {}
    if isinstance(symbols, Mapping):
        for key, val in symbols.items():
            try:
                env[str(key)] = val if isinstance(val, sympy.Basic) else sympy.sympify(val)
            except Exception:
                continue
    elif symbols is not None:
        for item in symbols:
            try:
                if isinstance(item, sympy.Symbol):
                    env[item.name] = item
                else:
                    parsed = sympy.sympify(item)
                    env[str(parsed)] = parsed
            except Exception:
                continue
    if isinstance(expr, sympy.Basic):
        for sym in expr.free_symbols:
            if isinstance(sym, sympy.Symbol):
                env.setdefault(sym.name, sym)
    return env


def _as_expr(obj: Any, env: Mapping[str, sympy.Expr]) -> sympy.Expr:
    if isinstance(obj, sympy.Basic):
        return obj
    if obj is None or obj == "":
        raise ValueError("empty_expr")
    locals_map = dict(env)
    return sympy.sympify(obj, locals=locals_map)


def _coerce_step(
    step: StepLike,
    env: Mapping[str, sympy.Expr],
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    var: Any = None
    target: Any = None
    if isinstance(step, PathStep):
        var, target = step.variable, step.target_value
    elif isinstance(step, Mapping):
        var = step.get("variable")
        target = step.get("target_value")
    elif isinstance(step, Sequence) and not isinstance(step, (str, bytes)):
        if len(step) < 2:
            return None
        var, target = step[0], step[1]
    else:
        return None
    if var is None or var == "" or target is None or target == "":
        return None
    try:
        return _as_expr(var, env), _as_expr(target, env)
    except Exception:
        return None


def _fmt_steps(steps: Sequence[StepLike], env: Mapping[str, sympy.Expr]) -> str:
    parts: list[str] = []
    for step in steps:
        coerced = _coerce_step(step, env)
        if coerced is None:
            parts.append("?")
            continue
        var, target = coerced
        parts.append(f"{var}->{target}")
    return ";".join(parts)


def _endpoints(
    path_a: Sequence[StepLike],
    path_b: Sequence[StepLike],
) -> tuple[str, str]:
    def _from(steps: Sequence[StepLike]) -> tuple[str, str]:
        if not steps:
            return "", ""
        first, last = steps[0], steps[-1]
        src = first.source if isinstance(first, PathStep) else ""
        dst = last.target if isinstance(last, PathStep) else ""
        return src, dst

    sa, ea = _from(path_a)
    sb, eb = _from(path_b)
    start = sa if sa and sa == sb else (sa or sb or "start")
    end = ea if ea and ea == eb else (ea or eb or "end")
    return start, end


def _confirm_limit(
    F: sympy.Expr,
    y: sympy.Expr,
    x: sympy.Expr,
    cand: sympy.Expr,
    how: str,
) -> tuple[str, Optional[sympy.Expr], str]:
    if how in _CONFIRM_SKIP:
        return "ok", cand, how
    try:
        result = check_limit(F, y, x, cand)
    except BudgetExceeded:
        return "unknown", None, "timeout"
    except Exception as exc:
        return "unknown", None, f"check_limit:{type(exc).__name__}"
    if result.verdict == ZERO:
        return "ok", cand, how
    return "unknown", None, f"{how}:unconfirmed_{result.verdict}"


def _limit_value(
    F: sympy.Expr,
    y: sympy.Expr,
    x: sympy.Expr,
) -> tuple[str, Optional[sympy.Expr], str]:
    """Compute one-parameter ``lim_{y -> x} F``. Fail closed on budget/size."""
    if _ops_too_large(F):
        return "unknown", None, "size_guard"
    steps: list[str] = []
    try:
        sub = _step_substitution(F, y, x)
        if sub is not None:
            return _confirm_limit(F, y, x, sub, "substitution")

        together = _step_together_cancel(F, y, x)
        if together is not None:
            return _confirm_limit(F, y, x, together, "together_cancel")

        valuation = _step_valuation(F, y, x)
        if valuation is not None:
            kind, cand = valuation
            if kind == "pole":
                return "pole", cand, "valuation"
            if _is_finite(cand):
                return _confirm_limit(F, y, x, cand, "valuation")

        series = _step_series(F, y, x)
        if series is not None:
            kind, cand = series
            if kind == "pole":
                return "pole", cand, "series"
            if _is_finite(cand):
                return _confirm_limit(F, y, x, cand, "series")

        lhopital = _step_lhopital(F, y, x)
        if lhopital is not None:
            kind, cand = lhopital
            if kind == "pole":
                return "pole", cand, "lhopital"
            if _is_finite(cand):
                return _confirm_limit(F, y, x, cand, "lhopital")

        newton = _step_newton_first_dd(F, y, x)
        if newton is not None and _is_finite(newton):
            return _confirm_limit(F, y, x, newton, "newton_first_dd")

        lim, early = _step_sympy_limit(F, y, x, steps)
        if early is not None:
            return "unknown", None, early.provenance or "sympy.limit"
        if lim is not None:
            kind, cand = lim
            if kind == "pole":
                return "pole", cand, "sympy.limit"
            if _is_finite(cand):
                return "ok", cand, "sympy.limit"
        return "unknown", None, "UNKNOWN"
    except BudgetExceeded:
        return "unknown", None, "timeout"
    except Exception as exc:
        return "unknown", None, f"error:{type(exc).__name__}"


def _eval_path(
    expr: sympy.Expr,
    steps: Sequence[StepLike],
    env: Mapping[str, sympy.Expr],
) -> tuple[str, Optional[sympy.Expr], str]:
    coerced: list[tuple[sympy.Expr, sympy.Expr]] = []
    for step in steps:
        pair = _coerce_step(step, env)
        if pair is None:
            return "unknown", None, "bad_step"
        coerced.append(pair)
    current = expr
    traces: list[str] = []
    if not coerced:
        if not _is_finite(current):
            return "pole", current, "identity"
        return "ok", current, "identity"
    for var, target in coerced:
        if _ops_too_large(current):
            traces.append("size_guard")
            return "unknown", None, "+".join(traces)
        status, value, how = _limit_value(current, var, target)
        traces.append(how)
        if status != "ok":
            return status, value, "+".join(traces)
        if value is None:
            traces.append("missing_value")
            return "unknown", None, "+".join(traces)
        current = value
    return "ok", current, "+".join(traces)


def _compare_values(
    status_a: str,
    val_a: Optional[sympy.Expr],
    status_b: str,
    val_b: Optional[sympy.Expr],
    trace_a: str,
    trace_b: str,
) -> tuple[str, str]:
    if status_a == "unknown" or status_b == "unknown":
        reason = trace_a if status_a == "unknown" else trace_b
        return CONSISTENCY_UNKNOWN, reason or "UNKNOWN"
    if status_a == "pole" and status_b == "pole":
        return CONSISTENCY_UNKNOWN, "both_nonfinite"
    if status_a == "pole" or status_b == "pole":
        return INCONSISTENT_NONZERO, f"pole_vs_finite:{trace_a} vs {trace_b}"
    if val_a is None or val_b is None:
        return CONSISTENCY_UNKNOWN, "missing_value"
    equal = _expr_equal(val_a, val_b)
    if equal is True:
        return CONSISTENT_ZERO, f"agree:{trace_a}|{trace_b}"
    if equal is False:
        return INCONSISTENT_NONZERO, f"disagree:{trace_a}|{trace_b}"
    return CONSISTENCY_UNKNOWN, "compare_undecided"


def check_two_paths(
    expr: Any,
    path_a_steps: Sequence[StepLike],
    path_b_steps: Sequence[StepLike],
    symbols: Any = None,
) -> PathConsistencyObligation:
    """Compare iterated one-parameter limits of ``expr`` along two paths.

    Each step is ``(variable, target_value)`` or ``PathStep``. Paths are
    evaluated independently; agreement is never assumed from the step lists.
    """
    start, end = _endpoints(path_a_steps, path_b_steps)
    env = _symbol_env(expr, symbols)
    try:
        parsed = _as_expr(expr, env)
    except Exception:
        return _unknown("parse:failed", start=start, end=end)
    if isinstance(parsed, sympy.Basic):
        for sym in parsed.free_symbols:
            if isinstance(sym, sympy.Symbol):
                env.setdefault(sym.name, sym)
    path_a_s = _fmt_steps(path_a_steps, env)
    path_b_s = _fmt_steps(path_b_steps, env)
    try:
        if _ops_too_large(parsed):
            return _unknown(
                "size_guard",
                path_a=path_a_s,
                path_b=path_b_s,
                start=start,
                end=end,
            )
        status_a, val_a, trace_a = _eval_path(parsed, path_a_steps, env)
        status_b, val_b, trace_b = _eval_path(parsed, path_b_steps, env)
        verdict, provenance = _compare_values(
            status_a, val_a, status_b, val_b, trace_a, trace_b,
        )
        return _obligation(
            verdict=verdict,
            provenance=provenance,
            path_a=path_a_s,
            path_b=path_b_s,
            start=start,
            end=end,
        )
    except BudgetExceeded:
        return _unknown(
            "timeout",
            path_a=path_a_s,
            path_b=path_b_s,
            start=start,
            end=end,
        )
    except Exception as exc:
        return _unknown(
            f"error:{type(exc).__name__}",
            path_a=path_a_s,
            path_b=path_b_s,
            start=start,
            end=end,
        )


def family_zero_blocked(
    consistency_verdicts: Iterable[str] | None,
    require_path_independence: bool = True,
) -> bool:
    """True unless every verdict is CONSISTENT_ZERO when independence is required.

    ``INCONSISTENT_NONZERO`` always blocks FAMILY_ZERO. Missing or UNKNOWN
    consistency blocks only when ``require_path_independence`` is true.
    """
    cons = [str(v) for v in (consistency_verdicts or [])]
    if any(v == INCONSISTENT_NONZERO for v in cons):
        return True
    if not require_path_independence:
        return False
    if not cons:
        return True
    return not all(v == CONSISTENT_ZERO for v in cons)


__all__ = [
    "CONSISTENT_ZERO",
    "INCONSISTENT_NONZERO",
    "CONSISTENCY_UNKNOWN",
    "LIMIT_OPS_CAP",
    "check_two_paths",
    "family_zero_blocked",
]
