"""Compare Laurent C_0 to a diagonal target without full-kernel together.

Allowed: ``expand(C0 - tgt) == 0``, ``cancel`` when ops are small, group
by polygamma atoms then compare rational coefficients. If
``count_ops(C0) + count_ops(tgt)`` exceeds ``OPS_CAP``, return UNKNOWN
not ZERO. Never ``together`` the pair.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.coefficient_laurent.schema import NONZERO, UNKNOWN, ZERO

OPS_CAP = 800
CANCEL_OPS_CAP = 80

_ZERO = sympy.Integer(0)
_ONE = sympy.Integer(1)


@dataclass(frozen=True)
class ConstantMatchResult:
    """Verdict of ``C_0`` vs a diagonal target."""

    verdict: str
    provenance: str
    steps: tuple[str, ...]
    ops: int
    residual: Optional[str] = None
    used_full_together: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def match_constant(c0: Any, target: Any) -> ConstantMatchResult:
    """Compare Laurent ``t^0`` coefficient ``c0`` to ``target``.

    Size-guard and every exception path are UNKNOWN, never ZERO.
    ``used_full_together`` is always False.
    """
    steps: list[str] = []
    try:
        return _match(c0, target, steps)
    except Exception as exc:
        steps.append(f"error:{type(exc).__name__}")
        return _result(UNKNOWN, "UNKNOWN", steps, ops=OPS_CAP + 1)


def _match(c0: Any, target: Any, steps: list[str]) -> ConstantMatchResult:
    left = _to_expr(c0)
    right = _to_expr(target)
    if left is None or right is None:
        steps.append("parse")
        return _result(UNKNOWN, "parse", steps, ops=OPS_CAP + 1)

    ops = _count_ops(left) + _count_ops(right)
    steps.append(f"ops:{ops}")
    if ops > OPS_CAP:
        steps.append("size_guard")
        return _result(UNKNOWN, "size_guard", steps, ops=ops)

    if left == right:
        steps.append("identical")
        return _zero("identical", steps, ops)

    decided = _by_expand(left, right, steps, ops)
    if decided is not None:
        return decided

    decided = _by_cancel(left, right, steps, ops)
    if decided is not None:
        return decided

    decided = _by_polygamma_atoms(left, right, steps, ops)
    if decided is not None:
        return decided

    steps.append("undecided")
    return _result(UNKNOWN, "UNKNOWN", steps, ops=ops)


def _by_expand(
    left: sympy.Expr, right: sympy.Expr, steps: list[str], ops: int,
) -> Optional[ConstantMatchResult]:
    try:
        diff = sympy.expand(left - right)
    except Exception as exc:
        steps.append(f"expand:{type(exc).__name__}")
        return None
    steps.append("expand")
    z = _is_identically_zero(diff)
    if z is True:
        steps.append("expand:ZERO")
        return _zero("expand", steps, ops)
    if z is False:
        steps.append("expand:NONZERO")
        return _nonzero("expand", steps, ops, diff)
    return None


def _by_cancel(
    left: sympy.Expr, right: sympy.Expr, steps: list[str], ops: int,
) -> Optional[ConstantMatchResult]:
    try:
        diff = left - right
        diff_ops = _count_ops(diff)
    except Exception as exc:
        steps.append(f"cancel:{type(exc).__name__}")
        return None
    if diff_ops > CANCEL_OPS_CAP:
        steps.append(f"cancel:skip:{diff_ops}")
        return None
    try:
        cancelled = sympy.cancel(diff)
    except Exception as exc:
        steps.append(f"cancel:{type(exc).__name__}")
        return None
    steps.append("cancel")
    z = _is_identically_zero(cancelled)
    if z is True:
        steps.append("cancel:ZERO")
        return _zero("cancel", steps, ops)
    if z is False:
        steps.append("cancel:NONZERO")
        return _nonzero("cancel", steps, ops, cancelled)
    return None


def _by_polygamma_atoms(
    left: sympy.Expr, right: sympy.Expr, steps: list[str], ops: int,
) -> Optional[ConstantMatchResult]:
    try:
        map_l = _group_by_polygamma(left)
        map_r = _group_by_polygamma(right)
    except Exception as exc:
        steps.append(f"pg_atoms:{type(exc).__name__}")
        return None
    steps.append(f"pg_atoms:n={len(set(map_l) | set(map_r))}")
    proven_unequal = False
    unknown = False
    residual: Optional[sympy.Expr] = None
    for key in set(map_l) | set(map_r):
        coeff_l = map_l.get(key, _ZERO)
        coeff_r = map_r.get(key, _ZERO)
        eq = _rational_coeffs_equal(coeff_l, coeff_r)
        if eq is True:
            continue
        if eq is False:
            proven_unequal = True
            residual = sympy.expand(coeff_l - coeff_r) * key
            continue
        unknown = True
    if proven_unequal:
        steps.append("pg_atoms:NONZERO")
        return _nonzero("pg_atoms", steps, ops, residual)
    if unknown:
        steps.append("pg_atoms:UNKNOWN")
        return None
    steps.append("pg_atoms:ZERO")
    return _zero("pg_atoms", steps, ops)


def _group_by_polygamma(expr: sympy.Expr) -> dict[sympy.Expr, sympy.Expr]:
    """Map polygamma-atom product -> sum of rational coefficients.

    Terms with no polygamma factor accumulate under ``1``. Does not
    call ``together``.
    """
    try:
        expanded = sympy.expand(expr)
    except Exception:
        expanded = expr
    acc: dict[sympy.Expr, sympy.Expr] = {}
    for term in sympy.Add.make_args(expanded):
        pg: list[sympy.Expr] = []
        rest: list[sympy.Expr] = []
        for factor in sympy.Mul.make_args(term):
            if _is_polygamma_factor(factor):
                pg.append(factor)
            else:
                rest.append(factor)
        pg.sort(key=sympy.default_sort_key)
        key = sympy.Mul(*pg) if pg else _ONE
        coeff = sympy.Mul(*rest) if rest else _ONE
        acc[key] = acc.get(key, _ZERO) + coeff
    return acc


def _is_polygamma_factor(expr: sympy.Expr) -> bool:
    if expr.func is sympy.polygamma:
        return True
    if isinstance(expr, sympy.Pow) and expr.base.func is sympy.polygamma:
        return True
    return False


def _rational_coeffs_equal(a: sympy.Expr, b: sympy.Expr) -> Optional[bool]:
    if a == b:
        return True
    try:
        expanded = sympy.expand(a - b)
    except Exception:
        expanded = None
    if expanded is not None:
        z = _is_identically_zero(expanded)
        if z is not None:
            return z
    ops = _count_ops(a) + _count_ops(b)
    if ops > OPS_CAP:
        return None
    try:
        cancelled = sympy.cancel(a - b)
    except Exception:
        return None
    return _is_identically_zero(cancelled)


def _is_identically_zero(expr: sympy.Expr) -> Optional[bool]:
    """True if identically 0, False if a polynomial coeff proves nonzero.

    ``as_coefficients_dict`` is used only on polynomials. Rational
    functions can share a numeric coeff map and still cancel to 0.
    """
    if expr == 0:
        return True
    try:
        if expr.is_zero is True:
            return True
    except Exception:
        pass
    if getattr(expr, "is_number", False):
        try:
            return bool(expr == 0)
        except Exception:
            return None
    poly = False
    try:
        poly = bool(expr.is_polynomial())
    except Exception:
        poly = False
    if not poly:
        return None
    try:
        coeffs = expr.as_coefficients_dict()
    except Exception:
        return None
    saw_nonzero = False
    for coeff in coeffs.values():
        c = _as_numeric_coeff(coeff)
        if c is None:
            return None
        if c == 0:
            continue
        if c != 0:
            saw_nonzero = True
    return False if saw_nonzero else True


def _as_numeric_coeff(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, sympy.Expr) and getattr(value, "is_number", False):
        return value
    return None


def _to_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    return None


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return OPS_CAP + 1


def _zero(provenance: str, steps: list[str], ops: int) -> ConstantMatchResult:
    if ops > OPS_CAP:
        steps.append("blocked_zero")
        return _result(UNKNOWN, "size_guard", steps, ops=ops)
    return _result(ZERO, provenance, steps, ops=ops)


def _nonzero(
    provenance: str,
    steps: list[str],
    ops: int,
    residual: Optional[sympy.Expr],
) -> ConstantMatchResult:
    text = None
    if residual is not None:
        try:
            text = str(residual)
        except Exception:
            text = None
    return _result(NONZERO, provenance, steps, ops=ops, residual=text)


def _result(
    verdict: str,
    provenance: str,
    steps: list[str],
    *,
    ops: int,
    residual: Optional[str] = None,
) -> ConstantMatchResult:
    if verdict == ZERO and ops > OPS_CAP:
        verdict = UNKNOWN
        provenance = "size_guard"
        steps = list(steps) + ["blocked_zero"]
    return ConstantMatchResult(
        verdict=verdict,
        provenance=provenance,
        steps=tuple(steps),
        ops=ops,
        residual=residual,
        used_full_together=False,
    )
