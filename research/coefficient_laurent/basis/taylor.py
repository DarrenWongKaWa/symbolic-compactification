"""Polygamma derivative-basis Taylor CONTROL.

Not a verifier. Not a proposer. Never a hop certificate. No LLM.

Documented identity (SymPy ``polygamma`` fdiff; higher polygamma is
the ordinary derivative of lower polygamma):

    d/dz polygamma(k, z) = polygamma(k + 1, z)

hence

    d^n/dz^n polygamma(k, z) = polygamma(k + n, z)

Taylor rewrite of the regular argument shift, without CAS series:

    polygamma(k, z0 + b t)
        = sum_n polygamma(k + n, z0) * (b t)^n / n!

CAS ``Expr.series`` is comparison-only. Size-guard and series failure
are UNKNOWN on the comparison fields; they do not invent a polynomial.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import sympy

CONTROL = "CONTROL"
UNKNOWN = "UNKNOWN"

NTERMS_CAP = 16
CHAR_CAP = 2048

DERIVATIVE_IDENTITY = "d^n/dz^n polygamma(k, z) = polygamma(k+n, z)"

_NOTE = (
    "CONTROL only, not a verifier, not a proposer; derivative-basis "
    "Taylor of polygamma(k, z0 + b t); not a hop certificate."
)
_NOTE_UNKNOWN = (
    "UNKNOWN: parse, nterms cap, or construction failure; CONTROL only, "
    "not a verifier, not a proposer; never a hop certificate."
)


@dataclass(frozen=True)
class TaylorBasisControl:
    """Derivative-basis Taylor report. Not a hop verdict."""

    polynomial: Optional[Any]
    terms: tuple = ()
    basis_ops: Optional[int] = None
    raw_ops: Optional[int] = None
    raw_core_ops: Optional[int] = None
    raw_series: Optional[Any] = None
    nterms: int = 0
    identity: str = DERIVATIVE_IDENTITY
    note: str = _NOTE
    status: str = CONTROL

    def to_dict(self) -> dict[str, Any]:
        return {
            "polynomial": _s(self.polynomial),
            "terms": [_s(t) for t in self.terms],
            "basis_ops": self.basis_ops,
            "raw_ops": self.raw_ops,
            "raw_core_ops": self.raw_core_ops,
            "raw_series": _s(self.raw_series),
            "nterms": self.nterms,
            "identity": self.identity,
            "note": self.note,
            "status": self.status,
        }


def polygamma_taylor_basis(
    k: Any,
    z0: Any,
    b: Any,
    t: Any,
    nterms: int = 2,
) -> TaylorBasisControl:
    """Rewrite ``polygamma(k, z0 + b t)`` in the derivative basis.

    Returns a CONTROL report. Does not certify a hop. Does not propose.
    """
    try:
        return _polygamma_taylor_basis(k, z0, b, t, nterms)
    except Exception:
        return _unknown(nterms=_safe_nterms(nterms), extra="exception")


def _polygamma_taylor_basis(
    k: Any,
    z0: Any,
    b: Any,
    t: Any,
    nterms: Any,
) -> TaylorBasisControl:
    parsed_n = _parse_nterms(nterms)
    if parsed_n is None:
        return _unknown(nterms=_safe_nterms(nterms), extra="nterms")
    k_e = _as_expr(k)
    z0_e = _as_expr(z0)
    b_e = _as_expr(b)
    t_e = _as_expr(t)
    if k_e is None or z0_e is None or b_e is None or t_e is None:
        return _unknown(nterms=parsed_n, extra="unparsed")

    terms: list[sympy.Expr] = []
    for n in range(parsed_n):
        n_e = sympy.Integer(n)
        # (b t)^n / n! * polygamma(k+n, z0); do not expand z0.
        weight = (b_e * t_e) ** n_e / sympy.factorial(n_e)
        terms.append(sympy.polygamma(k_e + n_e, z0_e) * weight)
    polynomial = sympy.Add(*terms) if terms else sympy.Integer(0)
    basis_ops = _count_ops(polynomial)

    raw_series, raw_ops, raw_core_ops = _raw_series_ops(
        k_e, z0_e, b_e, t_e, parsed_n
    )
    return TaylorBasisControl(
        polynomial=polynomial,
        terms=tuple(terms),
        basis_ops=basis_ops,
        raw_ops=raw_ops,
        raw_core_ops=raw_core_ops,
        raw_series=raw_series,
        nterms=parsed_n,
        identity=DERIVATIVE_IDENTITY,
        note=_NOTE,
        status=CONTROL,
    )


def _raw_series_ops(
    k: sympy.Expr,
    z0: sympy.Expr,
    b: sympy.Expr,
    t: sympy.Expr,
    nterms: int,
) -> tuple[Optional[sympy.Expr], Optional[int], Optional[int]]:
    """CAS series of polygamma(k, z0 + b t), comparison only."""
    try:
        expr = sympy.polygamma(k, z0 + b * t)
        raw = expr.series(t, 0, nterms)
    except Exception:
        return None, None, None
    if not isinstance(raw, sympy.Expr):
        return None, None, None
    raw_ops = _count_ops(raw)
    core = raw.removeO() if raw.has(sympy.Order) else raw
    core_ops = _count_ops(core) if isinstance(core, sympy.Expr) else None
    return raw, raw_ops, core_ops


def _parse_nterms(nterms: Any) -> Optional[int]:
    if isinstance(nterms, bool) or not isinstance(nterms, int):
        return None
    if nterms < 1 or nterms > NTERMS_CAP:
        return None
    return nterms


def _safe_nterms(nterms: Any) -> int:
    if isinstance(nterms, int) and not isinstance(nterms, bool):
        return nterms
    return 0


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, str):
        if len(value) > CHAR_CAP:
            return None
        try:
            value = sympy.sympify(value)
        except (sympy.SympifyError, TypeError, ValueError):
            return None
        except Exception:
            return None
    if not isinstance(value, sympy.Expr):
        try:
            value = sympy.sympify(value)
        except Exception:
            return None
    if not isinstance(value, sympy.Expr):
        return None
    if getattr(value, "is_Relational", False):
        return None
    return value


def _count_ops(expr: sympy.Expr) -> Optional[int]:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return None


def _unknown(*, nterms: int, extra: str = "") -> TaylorBasisControl:
    note = _NOTE_UNKNOWN
    if extra:
        note = f"{_NOTE_UNKNOWN} ({extra})"
    return TaylorBasisControl(
        polynomial=None,
        terms=(),
        basis_ops=None,
        raw_ops=None,
        raw_core_ops=None,
        raw_series=None,
        nterms=nterms,
        identity=DERIVATIVE_IDENTITY,
        note=note,
        status=UNKNOWN,
    )


def _s(expr: Any) -> Optional[str]:
    if expr is None:
        return None
    return str(expr)
