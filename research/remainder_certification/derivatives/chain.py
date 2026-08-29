"""Polygamma derivative chain → Taylor coefficients.

Symbolic-backend identity (SymPy ``diff`` / ``polygamma.fdiff``; DLMF 5.15):

    d/dz polygamma(k, z) = polygamma(k+1, z)

Iterating in the derivative order gives

    d^r/dz^r polygamma(k, z) = polygamma(k+r, z)

and therefore, when ``polygamma(k, ·)`` is holomorphic at ``z0``,

    [t^r] polygamma(k, z0 + c t) = polygamma(k+r, z0) * c^r / r!

Holomorphicity at ``z0`` is the R2/R3 domain (polygamma poles, neighborhood).
This module emits those coefficients only. It does not emit a remainder
verdict, does not mint hop ZERO, and is not Track V6.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import sympy

DIFF_IDENTITY = "d/dz polygamma(k,z) = polygamma(k+1,z)"
TAYLOR_IDENTITY = (
    "[t^r] polygamma(k, z0 + c t) = polygamma(k+r, z0) * c^r / r!"
)
DOMAIN_OWNER = "R2/R3"
METHOD = "rc-pg-derivative-chain-1"

R_MAX_CAP = 16
K_CAP = 32

_NOTE = (
    "coefficients only; remainder CERTIFIED is not emitted; "
    "holomorphicity at z0 is R2/R3; not a hop certificate; D2 LOCKED"
)
_NOTE_FAIL = (
    "construction failure; coefficients only; remainder CERTIFIED is "
    "not emitted; holomorphicity at z0 is R2/R3"
)


@dataclass(frozen=True)
class DerivativeChainCoeffs:
    """Taylor coefficients of polygamma(k, z0 + c t) from the derivative chain.

    Not a remainder certificate. Domain of holomorphicity is R2/R3.
    """

    coefficients: tuple
    k: Any
    z0: Any
    c: Any
    r_max: int
    identity: str = DIFF_IDENTITY
    taylor_identity: str = TAYLOR_IDENTITY
    domain_owner: str = DOMAIN_OWNER
    note: str = _NOTE
    method: str = METHOD

    def coeff(self, r: int) -> Optional[Any]:
        if not isinstance(r, int) or isinstance(r, bool):
            return None
        if r < 0 or r >= len(self.coefficients):
            return None
        return self.coefficients[r]

    def to_dict(self) -> dict[str, Any]:
        return {
            "coefficients": {
                str(i): _s(term) for i, term in enumerate(self.coefficients)
            },
            "k": _s(self.k),
            "z0": _s(self.z0),
            "c": _s(self.c),
            "r_max": self.r_max,
            "identity": self.identity,
            "taylor_identity": self.taylor_identity,
            "domain_owner": self.domain_owner,
            "note": self.note,
            "method": self.method,
        }


def polygamma_diff(k: Any, z: Any) -> Optional[sympy.Expr]:
    """``d/dz polygamma(k, z)`` via ``sympy.diff``.

    Equals ``polygamma(k+1, z)`` on the symbolic backend.
    """
    k_e = _as_nnint(k, cap=K_CAP)
    z_e = _as_expr(z)
    if k_e is None or z_e is None:
        return None
    try:
        return _diff_on_arg(sympy.Integer(k_e), z_e, 1)
    except Exception:
        return None


def polygamma_taylor_coefficient(
    k: Any,
    z0: Any,
    c: Any,
    r: Any,
) -> Optional[sympy.Expr]:
    """``[t^r] polygamma(k, z0 + c t)`` from the derivative chain.

    Valid when holomorphic at ``z0`` (R2/R3). Does not certify a remainder.
    """
    try:
        return _taylor_coeff(k, z0, c, r)
    except Exception:
        return None


def polygamma_taylor_coefficients(
    k: Any,
    z0: Any,
    c: Any,
    r_max: Any = 2,
) -> DerivativeChainCoeffs:
    """Coefficients ``r = 0 .. r_max`` of ``polygamma(k, z0 + c t)``.

    Construction uses ``sympy.diff``, not CAS ``series``. Comparison against
    ``series`` is a test concern only.
    """
    try:
        return _taylor_coeffs(k, z0, c, r_max)
    except Exception:
        return _empty(k, z0, c, r_max, extra="exception")


def _taylor_coeffs(k: Any, z0: Any, c: Any, r_max: Any) -> DerivativeChainCoeffs:
    r_hi = _as_nnint(r_max, cap=R_MAX_CAP)
    k_e = _as_nnint(k, cap=K_CAP)
    z0_e = _as_expr(z0)
    c_e = _as_expr(c)
    if r_hi is None or k_e is None or z0_e is None or c_e is None:
        return _empty(k, z0, c, r_max, extra="unparsed")
    terms: list[sympy.Expr] = []
    for r in range(r_hi + 1):
        coeff = _coeff_from_chain(k_e, z0_e, c_e, r)
        if coeff is None:
            return _empty(k_e, z0_e, c_e, r_hi, extra="chain")
        terms.append(coeff)
    return DerivativeChainCoeffs(
        coefficients=tuple(terms),
        k=sympy.Integer(k_e),
        z0=z0_e,
        c=c_e,
        r_max=r_hi,
        identity=DIFF_IDENTITY,
        taylor_identity=TAYLOR_IDENTITY,
        domain_owner=DOMAIN_OWNER,
        note=_NOTE,
        method=METHOD,
    )


def _taylor_coeff(k: Any, z0: Any, c: Any, r: Any) -> Optional[sympy.Expr]:
    r_e = _as_nnint(r, cap=R_MAX_CAP)
    k_e = _as_nnint(k, cap=K_CAP)
    z0_e = _as_expr(z0)
    c_e = _as_expr(c)
    if r_e is None or k_e is None or z0_e is None or c_e is None:
        return None
    return _coeff_from_chain(k_e, z0_e, c_e, r_e)


def _coeff_from_chain(
    k: int,
    z0: sympy.Expr,
    c: sympy.Expr,
    r: int,
) -> Optional[sympy.Expr]:
    """``f^{(r)}(z0) c^r / r!`` with ``f^{(r)} = d^r/dz^r polygamma(k, z)``."""
    deriv = _diff_on_arg(sympy.Integer(k), z0, r)
    if deriv is None:
        return None
    r_e = sympy.Integer(r)
    weight = (c ** r_e) / sympy.factorial(r_e)
    return deriv * weight


def _diff_on_arg(k: sympy.Integer, z: sympy.Expr, order: int) -> Optional[sympy.Expr]:
    """``d^order/dw^order polygamma(k, w)`` evaluated at ``z``, via ``diff``.

    Always differentiate in a Dummy so ``z`` may be a number or a compound
    expression (not a legal ``diff`` variable).
    """
    w = sympy.Dummy("w")
    out = sympy.diff(sympy.polygamma(k, w), w, order)
    if not isinstance(out, sympy.Expr):
        return None
    return out.xreplace({w: z})


def _as_nnint(value: Any, *, cap: int) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, sympy.Integer):
        value = int(value)
    elif not isinstance(value, int):
        return None
    if value < 0 or value > cap:
        return None
    return int(value)


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, sympy.Expr):
        if getattr(value, "is_Relational", False):
            return None
        return value
    return None


def _empty(k: Any, z0: Any, c: Any, r_max: Any, *, extra: str) -> DerivativeChainCoeffs:
    r_hi = _as_nnint(r_max, cap=R_MAX_CAP)
    note = _NOTE_FAIL if not extra else f"{_NOTE_FAIL} ({extra})"
    return DerivativeChainCoeffs(
        coefficients=(),
        k=k,
        z0=z0,
        c=c,
        r_max=-1 if r_hi is None else r_hi,
        identity=DIFF_IDENTITY,
        taylor_identity=TAYLOR_IDENTITY,
        domain_owner=DOMAIN_OWNER,
        note=note,
        method=METHOD,
    )


def _s(expr: Any) -> Optional[str]:
    if expr is None:
        return None
    return str(expr)
