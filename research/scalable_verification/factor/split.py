"""Exact spectator-factor split of a pair of expressions.

Multiplicative: A = S * A_local, B = S * B_local, with S = gcd(num)/gcd(den).
Additive:       A = S + A_local, B = S + B_local, with S the same-sign
                min-coefficient common part of additive terms.

Only sympy gcd / factor / cancel. No guessed physics, no simplify().
False decomposition acceptance = 0: certify only on exact reconstruction
plus divisibility / coefficient containment. Units and zero are not spectators.
"""
from __future__ import annotations

from typing import Any, Mapping, TypedDict

import sympy


class SplitResult(TypedDict):
    S: sympy.Expr
    A_local: sympy.Expr
    B_local: sympy.Expr
    certified: bool
    note: str


_ONE = sympy.Integer(1)
_ZERO = sympy.Integer(0)
_NEG_ONE = sympy.Integer(-1)


def split_multiplicative(A: Any, B: Any) -> SplitResult:
    """Return the exact common multiplicative spectator of ``A`` and ``B``."""
    try:
        a = _to_expr(A)
        b = _to_expr(B)
    except (TypeError, ValueError, sympy.SympifyError) as exc:
        return _uncert_mul(_ZERO, _ZERO, f"bad_input:{type(exc).__name__}")

    try:
        n_a, d_a = _num_den(a)
        n_b, d_b = _num_den(b)
        g_n = _gcd(n_a, n_b)
        g_d = _gcd(d_a, d_b)
        if g_n == 0 and g_d == 0:
            return _uncert_mul(a, b, "zero_spectator")
        S = sympy.cancel(g_n / g_d)
    except Exception:
        return _uncert_mul(a, b, "gcd_failed")

    if S == 0:
        return _uncert_mul(a, b, "zero_spectator")
    if _is_unit(S):
        return _uncert_mul(a, b, "no_exact_common_factor")

    n_s, d_s = _num_den(S)
    if not (
        _divides_exact(n_s, n_a)
        and _divides_exact(n_s, n_b)
        and _divides_exact(d_s, d_a)
        and _divides_exact(d_s, d_b)
    ):
        return _uncert_mul(a, b, "pole_mismatch")

    try:
        a_local = sympy.cancel(a / S)
        b_local = sympy.cancel(b / S)
    except Exception:
        return _uncert_mul(a, b, "reconstruction_failed")

    if not (_exact_eq(S * a_local, a) and _exact_eq(S * b_local, b)):
        return _uncert_mul(a, b, "reconstruction_failed")

    return _payload(S, a_local, b_local, True, "exact_common_factor")


def split_additive(A: Any, B: Any) -> SplitResult:
    """Return the exact common additive spectator of ``A`` and ``B``."""
    try:
        a = _to_expr(A)
        b = _to_expr(B)
    except (TypeError, ValueError, sympy.SympifyError) as exc:
        return _uncert_add(_ZERO, _ZERO, f"bad_input:{type(exc).__name__}")

    try:
        map_a = _coeff_map(a)
        map_b = _coeff_map(b)
        S = _common_addend(map_a, map_b)
    except Exception:
        return _uncert_add(a, b, "no_exact_common_factor")

    if S == 0:
        return _uncert_add(a, b, "no_exact_common_factor")

    map_s = _coeff_map(S)
    if not (_coeffs_contained(map_s, map_a) and _coeffs_contained(map_s, map_b)):
        return _uncert_add(a, b, "coefficient_mismatch")

    a_local = a - S
    b_local = b - S
    if not (_exact_eq(S + a_local, a) and _exact_eq(S + b_local, b)):
        return _uncert_add(a, b, "reconstruction_failed")

    return _payload(S, a_local, b_local, True, "exact_common_factor")


def _payload(
    S: sympy.Expr,
    a_local: sympy.Expr,
    b_local: sympy.Expr,
    certified: bool,
    note: str,
) -> SplitResult:
    return {
        "S": S,
        "A_local": a_local,
        "B_local": b_local,
        "certified": bool(certified),
        "note": note,
    }


def _uncert_mul(a: sympy.Expr, b: sympy.Expr, note: str) -> SplitResult:
    return _payload(_ONE, a, b, False, note)


def _uncert_add(a: sympy.Expr, b: sympy.Expr, note: str) -> SplitResult:
    return _payload(_ZERO, a, b, False, note)


def _to_expr(value: Any) -> sympy.Expr:
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not a symbolic expression")
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, float):
        return sympy.Float(value)
    raise TypeError(type(value).__name__)


def _num_den(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    try:
        packed = sympy.together(expr)
    except Exception:
        packed = expr
    num, den = sympy.fraction(packed)
    return num, den


def _gcd(a: sympy.Expr, b: sympy.Expr) -> sympy.Expr:
    try:
        g = sympy.gcd(a, b)
    except Exception:
        return _ONE
    if g is None:
        return _ONE
    return g


def _is_unit(expr: sympy.Expr) -> bool:
    return expr in (1, -1, _ONE, _NEG_ONE, sympy.S.One, sympy.S.NegativeOne)


def _divides_exact(part: sympy.Expr, whole: sympy.Expr) -> bool:
    """``part`` divides ``whole`` iff cancel(whole/part) is a polynomial (den=1)."""
    if part == 0:
        return whole == 0
    try:
        quot = sympy.cancel(whole / part)
        _num, den = sympy.fraction(quot)
    except Exception:
        return False
    return _is_unit(den) or den == 1


def _exact_eq(left: sympy.Expr, right: sympy.Expr) -> bool:
    if left == right:
        return True
    try:
        if sympy.cancel(left - right) == 0:
            return True
    except Exception:
        pass
    try:
        if sympy.cancel(sympy.together(left) - sympy.together(right)) == 0:
            return True
    except Exception:
        pass
    return False


def _coeff_map(expr: sympy.Expr) -> dict[sympy.Expr, sympy.Expr]:
    acc: dict[sympy.Expr, sympy.Expr] = {}
    for term in sympy.Add.make_args(expr):
        try:
            cancelled = sympy.cancel(term)
        except Exception:
            cancelled = term
        for key, coeff in cancelled.as_coefficients_dict().items():
            k = key if isinstance(key, sympy.Expr) else sympy.sympify(key)
            c = coeff if isinstance(coeff, sympy.Expr) else sympy.sympify(coeff)
            acc[k] = acc.get(k, _ZERO) + c
    return acc


def _common_coeff(c_a: sympy.Expr, c_b: sympy.Expr) -> sympy.Expr:
    if c_a == 0 or c_b == 0:
        return _ZERO
    if c_a == c_b:
        return c_a
    if not (c_a.is_number and c_b.is_number):
        return _ZERO
    if sympy.sign(c_a) * sympy.sign(c_b) <= 0:
        return _ZERO
    mag_a = sympy.Abs(c_a)
    mag_b = sympy.Abs(c_b)
    mag = mag_a if mag_a <= mag_b else mag_b
    return sympy.sign(c_a) * mag


def _common_addend(
    map_a: Mapping[sympy.Expr, sympy.Expr],
    map_b: Mapping[sympy.Expr, sympy.Expr],
) -> sympy.Expr:
    keys = [k for k in map_a if k in map_b]
    keys.sort(key=sympy.default_sort_key)
    terms: list[sympy.Expr] = []
    for key in keys:
        coeff = _common_coeff(map_a[key], map_b[key])
        if coeff == 0:
            continue
        terms.append(coeff * key)
    if not terms:
        return _ZERO
    return sympy.Add(*terms)


def _coeffs_contained(
    inner: Mapping[sympy.Expr, sympy.Expr],
    outer: Mapping[sympy.Expr, sympy.Expr],
) -> bool:
    for key, c_s in inner.items():
        if c_s == 0:
            continue
        if key not in outer:
            return False
        c_o = outer[key]
        if c_s == c_o:
            continue
        if not (c_s.is_number and c_o.is_number):
            return False
        if sympy.sign(c_s) != sympy.sign(c_o):
            return False
        if not (sympy.Abs(c_s) <= sympy.Abs(c_o)):
            return False
    return True
