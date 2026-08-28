"""Algebraic grouping of additive Laurent-coefficient terms.

Terms are bucketed by (polygamma order, canonical argument, denominator
signature) *before* any coefficient simplification. This module does not
call ``simplify``, does not ``together`` a sum, and does not emit a hop
verdict. No LLM. No scientific interpretation.
"""
from __future__ import annotations

from typing import Any, Mapping, NamedTuple, Sequence

import sympy


class GroupKey(NamedTuple):
    """Hashable bucket for like polygamma-rational terms.

    ``polygamma_order`` is an ``int`` when the order is an integer, ``None``
    when the term has no polygamma, and the tag ``"KERNEL"`` when several
    polygamma factors share the term. ``argument`` is the cancelled
    polygamma argument (or the unsplit kernel for ``KERNEL``).
    ``denom_signature`` is a sorted tuple of ``(srepr(base), exponent)``
    after stripping rational content and sign-normalizing each factor.
    """

    polygamma_order: object
    argument: object
    denom_signature: tuple


def group_terms(expr: Any) -> dict[GroupKey, list[sympy.Expr]]:
    """Partition additive terms by the grouping triple.

    ``expr`` may be a SymPy expression or a sequence of terms. Nested
    ``Add`` is flattened with ``Add.make_args``. Terms are stored as
    given; only the key uses ``together`` / ``cancel`` / content
    primitive. Fail-closed: an unreadable input is one unsplit bucket.
    """
    try:
        terms = _flatten(expr)
    except Exception:
        return {GroupKey(None, None, ()): [expr]}
    grouped: dict[GroupKey, list[sympy.Expr]] = {}
    for term in terms:
        key = _term_key(term)
        grouped.setdefault(key, []).append(term)
    return grouped


def sum_groups(
    groups: Mapping[Any, Sequence[Any]],
) -> dict[Any, sympy.Expr]:
    """Sum terms inside each group. Does not ``together`` across groups."""
    out: dict[Any, sympy.Expr] = {}
    for key, terms in groups.items():
        exprs = [_as_expr(t) for t in terms]
        if not exprs:
            out[key] = sympy.Integer(0)
        else:
            out[key] = sympy.Add(*exprs)
    return out


def _flatten(expr: Any) -> list[sympy.Expr]:
    if isinstance(expr, (list, tuple)):
        out: list[sympy.Expr] = []
        for item in expr:
            out.extend(_flatten(item))
        return out
    flat: list[sympy.Expr] = []
    for term in sympy.Add.make_args(_as_expr(expr)):
        flat.extend(_distribute_one_add(term))
    return flat


def _distribute_one_add(term: sympy.Expr) -> list[sympy.Expr]:
    """Distribute ``pref * Add`` only when the ``Add`` contains polygamma.

    Polynomial numerators such as ``(gamma + I*epsilon)*polygamma/den`` are
    left intact. ``(polygamma(1)+polygamma(2))/d`` is flattened.
    """
    add: sympy.Expr | None = None
    pref: list[sympy.Expr] = []
    for factor in sympy.Mul.make_args(term):
        if isinstance(factor, sympy.Add) and factor.has(sympy.polygamma):
            if add is not None:
                return [term]
            add = factor
        else:
            pref.append(factor)
    if add is None:
        return [term]
    p = sympy.Mul(*pref) if pref else sympy.Integer(1)
    out: list[sympy.Expr] = []
    for arg in sympy.Add.make_args(add):
        out.extend(_distribute_one_add(p * arg))
    return out


def _as_expr(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    raise TypeError(f"expected sympy.Expr, got {type(value).__name__}")


def _term_key(term: sympy.Expr) -> GroupKey:
    order, argument, coeff = _peel_polygamma(term)
    return GroupKey(order, argument, _denom_signature(coeff))


def _peel_polygamma(
    term: sympy.Expr,
) -> tuple[object, object, sympy.Expr]:
    """Return ``(order, argument, coefficient)`` without rewriting ``term``."""
    try:
        if not term.has(sympy.polygamma):
            return None, None, term
        coeff, kernel = term.as_independent(sympy.polygamma, as_Add=False)
        if not _mul_recovers(coeff, kernel, term):
            return "KERNEL", kernel, sympy.Integer(1)
        pgs = list(kernel.atoms(sympy.polygamma))
        if len(pgs) == 1 and kernel == pgs[0] and len(pgs[0].args) >= 2:
            pg = pgs[0]
            return _canon_order(pg.args[0]), _canon_arg(pg.args[1]), coeff
        return "KERNEL", kernel, coeff
    except Exception:
        return None, None, term


def _mul_recovers(coeff: sympy.Expr, kernel: sympy.Expr, term: sympy.Expr) -> bool:
    return coeff * kernel == term


def _canon_order(n: sympy.Expr) -> object:
    try:
        if n.is_Integer:
            return int(n)
        c = sympy.cancel(sympy.together(n))
        if c.is_Integer:
            return int(c)
        return c
    except Exception:
        return n


def _canon_arg(arg: sympy.Expr) -> sympy.Expr:
    try:
        return sympy.cancel(sympy.together(arg))
    except Exception:
        return arg


def _denom_signature(coeff: sympy.Expr) -> tuple:
    try:
        den = sympy.fraction(sympy.together(coeff))[1]
    except Exception:
        den = sympy.Integer(1)
    acc: dict[str, int] = {}
    for factor in sympy.Mul.make_args(den):
        base, exp = _split_pow(factor)
        if getattr(base, "is_number", False):
            continue
        can = _primitive_positive(base)
        if getattr(can, "is_number", False):
            continue
        name = sympy.srepr(can)
        acc[name] = acc.get(name, 0) + exp
    return tuple(sorted((name, exp) for name, exp in acc.items() if exp != 0))


def _split_pow(expr: sympy.Expr) -> tuple[sympy.Expr, int]:
    if isinstance(expr, sympy.Pow) and getattr(expr.exp, "is_Integer", False):
        return expr.base, int(expr.exp)
    return expr, 1


def _primitive_positive(expr: sympy.Expr) -> sympy.Expr:
    try:
        _content, prim = expr.as_content_primitive()
    except Exception:
        prim = expr
    try:
        if prim.could_extract_minus_sign():
            prim = -prim
    except Exception:
        pass
    return prim
