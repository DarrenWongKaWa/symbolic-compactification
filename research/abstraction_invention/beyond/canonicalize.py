"""Declared-safe canonicalization. Recovery after canon is NOT invention."""
from __future__ import annotations

import sympy
from sympy.core.function import AppliedUndef


def _sorted_args(args):
    return tuple(sorted(args, key=lambda a: sympy.srepr(a)))


def canon_ac(expr: sympy.Expr) -> sympy.Expr:
    """Associative-commutative flattening + srepr sort of Add/Mul."""
    if isinstance(expr, AppliedUndef):
        return expr.func(*[canon_ac(a) for a in expr.args])
    if not expr.args:
        return expr
    args = [canon_ac(a) for a in expr.args]
    if expr.func is sympy.Add:
        flat = []
        for a in args:
            flat.extend(sympy.Add.make_args(a))
        return sympy.Add(*_sorted_args(flat), evaluate=False)
    if expr.func is sympy.Mul:
        flat = []
        for a in args:
            flat.extend(sympy.Mul.make_args(a))
        return sympy.Mul(*_sorted_args(flat), evaluate=False)
    return expr.func(*args)


def canon_expand(expr: sympy.Expr) -> sympy.Expr:
    try:
        if isinstance(expr, AppliedUndef):
            return expr.func(*[sympy.expand(a) for a in expr.args])
        return sympy.expand(expr)
    except Exception:
        return expr


def canon_pipeline(expr: sympy.Expr) -> sympy.Expr:
    """Expand then AC-sort. For F2 control only."""
    return canon_ac(canon_expand(expr))
