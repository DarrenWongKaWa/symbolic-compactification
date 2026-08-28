"""Certified local-kernel complexity reduction (Track V3-H).

Allowed rewrites: factor, cancel, together, collect, exact child
substitution, and common-subexpression names recorded in the trace.
No CAS-global simplifier, no truncated expansions, no dropped
Piecewise branches, no undeclared identities.

Equivalence is ``==`` or ``cancel(original - reduced) == 0``, plus
preservation of Piecewise / Sum / Product / Integral / Limit shape.
Uncertified proposals are discarded: the original expression is
returned with ``equivalent=False``. This module does not emit ZERO.
"""
from __future__ import annotations

from typing import Any, Callable, Optional, Sequence, TypedDict

import sympy

_MAX_ROUNDS = 8
_FACTOR_OPS_CAP = 80
_COLLECT_OPS_CAP = 80
_TRACE_EXPR_LIMIT = 160

_PROTECTED_HEADS = (
    sympy.Piecewise,
    sympy.Sum,
    sympy.Product,
    sympy.Integral,
    sympy.Limit,
)


class ReduceResult(TypedDict):
    original_ops: int
    reduced_ops: int
    expr_reduced: sympy.Basic
    trace: list[str]
    equivalent: bool


def count_ops(expr: Any) -> int:
    """Local operation count. ``sympy.count_ops(..., visual=False)``."""
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return 0


def reduce_kernel(expr: Any) -> ReduceResult:
    """Return a certified lower-ops form of a local kernel, or the original.

    Keys: ``original_ops``, ``reduced_ops``, ``expr_reduced``, ``trace``,
    ``equivalent``. ``equivalent`` is True only when ``expr_reduced`` is
    certified equal to the input. A failed rewrite never returns a
    different expression.
    """
    try:
        original = _as_expr(expr)
    except Exception:
        return {
            "original_ops": 0,
            "reduced_ops": 0,
            "expr_reduced": expr,
            "trace": ["rejected: bad_input"],
            "equivalent": False,
        }

    original_ops = count_ops(original)
    proposed, trace = _propose_reduced(original)

    if proposed == original:
        return {
            "original_ops": original_ops,
            "reduced_ops": original_ops,
            "expr_reduced": original,
            "trace": list(trace),
            "equivalent": True,
        }

    if not _certified_equivalent(original, proposed):
        rejected = list(trace)
        rejected.append("rejected: not certified equivalent")
        return {
            "original_ops": original_ops,
            "reduced_ops": original_ops,
            "expr_reduced": original,
            "trace": rejected,
            "equivalent": False,
        }

    proposed_ops = count_ops(proposed)
    if proposed_ops >= original_ops:
        kept = list(trace)
        kept.append("kept_original: no_ops_decrease")
        return {
            "original_ops": original_ops,
            "reduced_ops": original_ops,
            "expr_reduced": original,
            "trace": kept,
            "equivalent": True,
        }

    return {
        "original_ops": original_ops,
        "reduced_ops": proposed_ops,
        "expr_reduced": proposed,
        "trace": list(trace),
        "equivalent": True,
    }


def _propose_reduced(expr: sympy.Basic) -> tuple[sympy.Basic, list[str]]:
    """Uncertified candidate plus an explicit rewrite trace."""
    trace: list[str] = []
    reduced = _reduce_tree(expr, trace)
    _record_lets(reduced, trace)
    return reduced, trace


def _reduce_tree(expr: sympy.Basic, trace: list[str]) -> sympy.Basic:
    if not isinstance(expr, sympy.Basic):
        return expr
    if isinstance(expr, sympy.Piecewise):
        return _reduce_piecewise(expr, trace)
    if isinstance(expr, (sympy.Sum, sympy.Product)):
        return _reduce_sum_or_product(expr, trace)
    if isinstance(expr, (sympy.Integral, sympy.Limit)):
        return _reduce_protected_head(expr, trace)
    if not expr.args:
        return expr

    new_args: list[Any] = []
    changed = False
    for arg in expr.args:
        if isinstance(arg, sympy.Basic) and arg.args:
            new_arg = _reduce_tree(arg, trace)
        else:
            new_arg = arg
        new_args.append(new_arg)
        if new_arg != arg:
            changed = True

    current: sympy.Basic = expr
    if changed:
        rebuilt = _rebuild(expr, new_args)
        if (
            rebuilt is not expr
            and _protected_signature(rebuilt) == _protected_signature(expr)
            and _certified_equivalent(expr, rebuilt)
        ):
            trace.append(
                f"exact_substitution:{type(expr).__name__}: "
                f"{_fmt(expr)} -> {_fmt(rebuilt)}"
            )
            current = rebuilt

    if _has_protected(current):
        return current
    return _reduce_algebraic(current, trace)


def _reduce_piecewise(expr: sympy.Piecewise, trace: list[str]) -> sympy.Basic:
    pairs: list[tuple[sympy.Basic, Any]] = []
    for i, (val, cond) in enumerate(expr.args):
        new_val = _reduce_tree(val, trace) if isinstance(val, sympy.Basic) else val
        if new_val != val:
            trace.append(
                f"piecewise_branch[{i}]: {_fmt(val)} -> {_fmt(new_val)}"
            )
        pairs.append((new_val, cond))
    if len(pairs) != len(expr.args):
        return expr
    rebuilt = _piecewise(pairs)
    if not isinstance(rebuilt, sympy.Piecewise):
        return expr
    if len(rebuilt.args) != len(expr.args):
        return expr
    for (_, ca), (_, cb) in zip(expr.args, rebuilt.args):
        if ca != cb:
            return expr
    trace.append(f"piecewise: preserved {len(rebuilt.args)} branches")
    return rebuilt


def _reduce_sum_or_product(expr: sympy.Expr, trace: list[str]) -> sympy.Basic:
    body = expr.function
    new_body = _reduce_tree(body, trace) if isinstance(body, sympy.Basic) else body
    if new_body == body:
        return expr
    try:
        rebuilt = expr.func(new_body, *expr.limits)
    except Exception:
        return expr
    if type(rebuilt) is not type(expr):
        return expr
    if rebuilt.limits != expr.limits:
        return expr
    if not _certified_equivalent(body, new_body):
        return expr
    trace.append(
        f"{type(expr).__name__}: {_fmt(body)} -> {_fmt(new_body)}"
    )
    return rebuilt


def _reduce_protected_head(expr: sympy.Expr, trace: list[str]) -> sympy.Basic:
    if not expr.args:
        return expr
    head, *rest = expr.args
    if not isinstance(head, sympy.Basic):
        return expr
    new_head = _reduce_tree(head, trace)
    if new_head == head:
        return expr
    rebuilt = _rebuild(expr, [new_head, *rest])
    if type(rebuilt) is not type(expr):
        return expr
    if _protected_signature(rebuilt) != _protected_signature(expr):
        return expr
    if not _certified_equivalent(expr, rebuilt):
        return expr
    trace.append(
        f"{type(expr).__name__}: {_fmt(head)} -> {_fmt(new_head)}"
    )
    return rebuilt


def _reduce_algebraic(expr: sympy.Basic, trace: list[str]) -> sympy.Basic:
    current = expr
    for _ in range(_MAX_ROUNDS):
        best = current
        best_ops = count_ops(current)
        best_name: Optional[str] = None
        for name, fn in _iter_transforms():
            try:
                cand = fn(current)
            except Exception:
                continue
            if cand is None or cand == current:
                continue
            if not isinstance(cand, sympy.Basic):
                continue
            if _protected_signature(cand) != _protected_signature(current):
                continue
            try:
                ops = count_ops(cand)
            except Exception:
                continue
            if ops < best_ops:
                best = cand
                best_ops = ops
                best_name = name
        if best_name is None:
            break
        trace.append(f"{best_name}: {_fmt(current)} -> {_fmt(best)}")
        current = best
    return current


def _transform_cancel(expr: sympy.Basic) -> Optional[sympy.Basic]:
    return sympy.cancel(expr)


def _transform_together(expr: sympy.Basic) -> Optional[sympy.Basic]:
    return sympy.together(expr)


def _transform_factor(expr: sympy.Basic) -> Optional[sympy.Basic]:
    if count_ops(expr) > _FACTOR_OPS_CAP:
        return None
    return sympy.factor(expr)


def _transform_collect(expr: sympy.Basic) -> Optional[sympy.Basic]:
    if count_ops(expr) > _COLLECT_OPS_CAP:
        return None
    symbols = sorted(expr.free_symbols, key=sympy.default_sort_key)
    if not symbols:
        return None
    best: Optional[sympy.Basic] = None
    best_ops = count_ops(expr)
    for symbol in symbols:
        try:
            cand = sympy.collect(expr, symbol)
        except Exception:
            continue
        ops = count_ops(cand)
        if ops < best_ops:
            best = cand
            best_ops = ops
    if len(symbols) > 1:
        try:
            cand = sympy.collect(expr, symbols)
        except Exception:
            cand = None
        if cand is not None:
            ops = count_ops(cand)
            if ops < best_ops:
                best = cand
    return best


_TRANSFORM_NAMES: tuple[str, ...] = ("cancel", "together", "factor", "collect")


def _iter_transforms() -> list[tuple[str, Callable[[sympy.Basic], Optional[sympy.Basic]]]]:
    """Resolve transform callables at call time so tests can monkeypatch."""
    return [
        (name, globals()[f"_transform_{name}"])
        for name in _TRANSFORM_NAMES
    ]


def _certified_equivalent(original: sympy.Basic, reduced: sympy.Basic) -> bool:
    if original == reduced:
        return True
    if _protected_signature(original) != _protected_signature(reduced):
        return False
    if isinstance(original, sympy.Piecewise) or isinstance(reduced, sympy.Piecewise):
        return _piecewise_equivalent(original, reduced)
    if isinstance(original, (sympy.Sum, sympy.Product)) and type(original) is type(reduced):
        if original.limits != reduced.limits:
            return False
        return _certified_equivalent(original.function, reduced.function)
    try:
        if sympy.cancel(original - reduced) == 0:
            return True
    except Exception:
        pass
    if type(original) is type(reduced) and original.args and reduced.args:
        if len(original.args) == len(reduced.args):
            if all(
                _certified_equivalent(a, b)
                if isinstance(a, sympy.Basic) and isinstance(b, sympy.Basic)
                else a == b
                for a, b in zip(original.args, reduced.args)
            ):
                return True
    return False


def _piecewise_equivalent(original: sympy.Basic, reduced: sympy.Basic) -> bool:
    if not isinstance(original, sympy.Piecewise):
        return False
    if not isinstance(reduced, sympy.Piecewise):
        return False
    if len(original.args) != len(reduced.args):
        return False
    for (va, ca), (vb, cb) in zip(original.args, reduced.args):
        if ca != cb:
            return False
        if not _certified_equivalent(va, vb):
            return False
    return True


def _protected_signature(expr: sympy.Basic) -> tuple[Any, ...]:
    sig: list[Any] = []
    try:
        nodes = sympy.preorder_traversal(expr)
    except Exception:
        return tuple()
    for node in nodes:
        if isinstance(node, sympy.Piecewise):
            sig.append(
                ("Piecewise", tuple(_cond_key(cond) for _, cond in node.args))
            )
        elif isinstance(node, (sympy.Sum, sympy.Product)):
            sig.append((type(node).__name__, tuple(node.limits)))
        elif isinstance(node, sympy.Integral):
            sig.append(("Integral", tuple(node.limits)))
        elif isinstance(node, sympy.Limit):
            sig.append(("Limit", tuple(node.args[1:])))
    return tuple(sig)


def _has_protected(expr: sympy.Basic) -> bool:
    try:
        return bool(expr.has(*_PROTECTED_HEADS))
    except Exception:
        return isinstance(expr, _PROTECTED_HEADS)


def _piecewise(pairs: Sequence[tuple[Any, Any]]) -> sympy.Basic:
    return sympy.Piecewise(*pairs, evaluate=False)


def _rebuild(expr: sympy.Basic, new_args: Sequence[Any]) -> sympy.Basic:
    if isinstance(expr, sympy.Piecewise):
        rebuilt = _piecewise(new_args)  # type: ignore[arg-type]
        return rebuilt
    try:
        return expr.func(*new_args)
    except Exception:
        return expr


def _cond_key(cond: Any) -> str:
    try:
        return sympy.srepr(cond)
    except Exception:
        return str(cond)


def _record_lets(expr: sympy.Basic, trace: list[str]) -> None:
    if _has_protected(expr):
        return
    try:
        replacements, _reduced = sympy.cse([expr])
    except Exception:
        return
    for symbol, value in replacements:
        trace.append(f"let {symbol} = {value}")


def _as_expr(value: Any) -> sympy.Basic:
    if isinstance(value, sympy.Basic):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return sympy.Integer(value)
    raise TypeError(f"unsupported kernel type: {type(value).__name__}")


def _fmt(expr: Any, limit: int = _TRACE_EXPR_LIMIT) -> str:
    text = str(expr)
    if len(text) > limit:
        return text[: limit - 3] + "..."
    return text
