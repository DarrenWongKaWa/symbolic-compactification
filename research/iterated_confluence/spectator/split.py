"""Exact spectator split of a one-parameter edge pair (A, B).

Wraps Track V ``split_multiplicative`` / ``split_additive``. A local kernel
is returned only after exact reconstruction:

  multiplicative: S * A_local == A and S * B_local == B
  additive:       S + A_local == A and S + B_local == B

False decomposition acceptance = 0. Units and zero are not spectators.
Track V size-guard (gcd ops cap 80) does not invent S. This package does
not decide confluence and does not evaluate frozen five-branch families.
"""
from __future__ import annotations

from typing import Any, Optional, TypedDict

import sympy
from sympy.core.function import AppliedUndef

from research.scalable_verification.factor import split_additive, split_multiplicative

MODE_MULTIPLICATIVE = "multiplicative"
MODE_ADDITIVE = "additive"
MODE_NONE = "none"

_ONE = sympy.Integer(1)
_ZERO = sympy.Integer(0)
_NEG_ONE = sympy.Integer(-1)

_NOTE_PRIORITY = (
    "reconstruction_failed",
    "spectator_depends_on_degeneration",
    "expansion_not_reduction",
    "too_large_for_gcd",
    "gcd_failed",
    "pole_mismatch",
    "coefficient_mismatch",
    "zero_spectator",
    "unit_or_zero_spectator",
    "no_exact_common_factor",
)


class SplitEdgeResult(TypedDict):
    certified: bool
    mode: str
    S: sympy.Expr
    A_local: sympy.Expr
    B_local: sympy.Expr
    full_ops_A: int
    full_ops_B: int
    local_ops_A: int
    local_ops_B: int
    spectator_ops: int
    reduction_ratio_A: Optional[float]
    reduction_ratio_B: Optional[float]
    note: str
    reconstruction_ok: bool


def count_ops(expr: Any) -> int:
    """``sympy.count_ops`` of ``expr`` (visual=False). Fail-closed to 0."""
    try:
        if not isinstance(expr, sympy.Basic):
            expr = _to_expr(expr)
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return 0


def split_edge(A: Any, B: Any, degeneration: Any = None) -> SplitEdgeResult:
    """Factor exact spectator structure of the pair ``(A, B)``.

    Multiplicative mode is tried first, then additive. Certified only when
    Track V reports a split **and** reconstruction holds. A failed
    reconstruction discards that kernel (it is not returned for proving).

    ``degeneration`` is the one-parameter limit variable. A spectator that
    depends on it is not peeled (``lim y*f(y)`` is not ``y * lim f``).
    """
    try:
        a = _to_expr(A)
        b = _to_expr(B)
    except (TypeError, ValueError, sympy.SympifyError) as exc:
        return _none_payload(_ZERO, _ZERO, f"bad_input:{type(exc).__name__}")

    deg = None
    if degeneration is not None:
        try:
            deg = degeneration if isinstance(degeneration, sympy.Basic) else _to_expr(degeneration)
        except Exception:
            deg = None

    reasons: list[str] = []

    undef = _mul_undef_peel(a, b)
    accepted, reason = _try_mode(undef, MODE_MULTIPLICATIVE, a, b, degeneration=deg)
    if accepted is not None:
        return accepted
    if reason:
        reasons.append(reason)

    mul = _call_split(split_multiplicative, a, b, multiplicative=True)
    accepted, reason = _try_mode(mul, MODE_MULTIPLICATIVE, a, b, degeneration=deg)
    if accepted is not None:
        return accepted
    reasons.append(reason or mul["note"])

    add = _call_split(split_additive, a, b, multiplicative=False)
    accepted, reason = _try_mode(add, MODE_ADDITIVE, a, b, degeneration=deg)
    if accepted is not None:
        return accepted
    reasons.append(reason or add["note"])

    return _none_payload(a, b, _pick_note(reasons))


def split_report(A: Any, B: Any) -> dict[str, Any]:
    """JSON-serializable view of ``split_edge`` (expressions as ``str``)."""
    out = split_edge(A, B)
    return {
        "certified": out["certified"],
        "mode": out["mode"],
        "S": str(out["S"]),
        "A_local": str(out["A_local"]),
        "B_local": str(out["B_local"]),
        "full_ops_A": out["full_ops_A"],
        "full_ops_B": out["full_ops_B"],
        "local_ops_A": out["local_ops_A"],
        "local_ops_B": out["local_ops_B"],
        "spectator_ops": out["spectator_ops"],
        "reduction_ratio_A": out["reduction_ratio_A"],
        "reduction_ratio_B": out["reduction_ratio_B"],
        "note": out["note"],
        "reconstruction_ok": out["reconstruction_ok"],
    }


def _call_split(
    fn: Any,
    a: sympy.Expr,
    b: sympy.Expr,
    *,
    multiplicative: bool,
) -> dict[str, Any]:
    fallback_s = _ONE if multiplicative else _ZERO
    try:
        out = fn(a, b)
    except Exception:
        return {
            "S": fallback_s,
            "A_local": a,
            "B_local": b,
            "certified": False,
            "note": "gcd_failed",
        }
    if not isinstance(out, dict):
        return {
            "S": fallback_s,
            "A_local": a,
            "B_local": b,
            "certified": False,
            "note": "gcd_failed",
        }
    return out


def _depends_on_degeneration(S: sympy.Expr, degeneration: Optional[sympy.Expr]) -> bool:
    if degeneration is None:
        return False
    try:
        return bool(S.has(degeneration))
    except Exception:
        return True


def _try_mode(
    raw: dict[str, Any],
    mode: str,
    a: sympy.Expr,
    b: sympy.Expr,
    degeneration: Optional[sympy.Expr] = None,
) -> tuple[Optional[SplitEdgeResult], Optional[str]]:
    if not raw.get("certified"):
        return None, None
    try:
        S = raw["S"]
        a_local = raw["A_local"]
        b_local = raw["B_local"]
    except Exception:
        return None, "reconstruction_failed"
    if not isinstance(S, sympy.Expr):
        return None, "reconstruction_failed"
    if not isinstance(a_local, sympy.Expr) or not isinstance(b_local, sympy.Expr):
        return None, "reconstruction_failed"
    if _trivial_spectator(S):
        return None, "unit_or_zero_spectator"
    if _depends_on_degeneration(S, degeneration):
        return None, "spectator_depends_on_degeneration"
    if not _reconstruction_ok(mode, S, a_local, b_local, a, b):
        return None, "reconstruction_failed"
    if count_ops(a_local) + count_ops(b_local) > count_ops(a) + count_ops(b):
        return None, "expansion_not_reduction"
    note = raw.get("note") if isinstance(raw.get("note"), str) and raw.get("note") else "exact_common_factor"
    return (
        _payload(
            certified=True,
            mode=mode,
            S=S,
            a_local=a_local,
            b_local=b_local,
            a=a,
            b=b,
            note=note,
            reconstruction_ok=True,
        ),
        None,
    )


def _reconstruction_ok(
    mode: str,
    S: sympy.Expr,
    a_local: sympy.Expr,
    b_local: sympy.Expr,
    a: sympy.Expr,
    b: sympy.Expr,
) -> bool:
    if mode == MODE_MULTIPLICATIVE:
        return _exact_eq(S * a_local, a) and _exact_eq(S * b_local, b)
    if mode == MODE_ADDITIVE:
        return _exact_eq(S + a_local, a) and _exact_eq(S + b_local, b)
    return False


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


def _trivial_spectator(S: sympy.Expr) -> bool:
    if S == 0:
        return True
    return S in (1, -1, _ONE, _NEG_ONE, sympy.S.One, sympy.S.NegativeOne)


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


def _ratio(local: int, full: int) -> Optional[float]:
    if full > 0:
        return local / full
    return None


def _drop_mul_factors(expr: sympy.Expr, factors: list[sympy.Expr]) -> Optional[sympy.Expr]:
    remaining = list(sympy.Mul.make_args(expr))
    for factor in factors:
        try:
            remaining.remove(factor)
        except ValueError:
            return None
    if not remaining:
        return _ONE
    return sympy.Mul(*remaining)


def _mul_undef_peel(a: sympy.Expr, b: sympy.Expr) -> dict[str, Any]:
    """Common AppliedUndef factors from Mul.args. No cancel expansion."""
    fa = [x for x in sympy.Mul.make_args(a) if isinstance(x, AppliedUndef)]
    fb = [x for x in sympy.Mul.make_args(b) if isinstance(x, AppliedUndef)]
    common: list[sympy.Expr] = []
    fb_left = list(fb)
    for xa in fa:
        for i, xb in enumerate(fb_left):
            if xa == xb:
                common.append(xa)
                fb_left.pop(i)
                break
    if not common:
        return {
            "S": _ONE,
            "A_local": a,
            "B_local": b,
            "certified": False,
            "note": "no_exact_common_factor",
        }
    S = sympy.Mul(*common) if len(common) > 1 else common[0]
    a_local = _drop_mul_factors(a, common)
    b_local = _drop_mul_factors(b, common)
    if a_local is None or b_local is None:
        return {
            "S": _ONE,
            "A_local": a,
            "B_local": b,
            "certified": False,
            "note": "reconstruction_failed",
        }
    return {
        "S": S,
        "A_local": a_local,
        "B_local": b_local,
        "certified": True,
        "note": "exact_applied_undef_mul_args",
    }


def _payload(
    *,
    certified: bool,
    mode: str,
    S: sympy.Expr,
    a_local: sympy.Expr,
    b_local: sympy.Expr,
    a: sympy.Expr,
    b: sympy.Expr,
    note: str,
    reconstruction_ok: bool,
) -> SplitEdgeResult:
    full_a = count_ops(a)
    full_b = count_ops(b)
    loc_a = count_ops(a_local)
    loc_b = count_ops(b_local)
    return {
        "certified": bool(certified),
        "mode": mode,
        "S": S,
        "A_local": a_local,
        "B_local": b_local,
        "full_ops_A": full_a,
        "full_ops_B": full_b,
        "local_ops_A": loc_a,
        "local_ops_B": loc_b,
        "spectator_ops": count_ops(S),
        "reduction_ratio_A": _ratio(loc_a, full_a),
        "reduction_ratio_B": _ratio(loc_b, full_b),
        "note": note,
        "reconstruction_ok": bool(reconstruction_ok),
    }


def _none_payload(a: sympy.Expr, b: sympy.Expr, note: str) -> SplitEdgeResult:
    # Identity S=1 with original locals is not a proving kernel.
    return _payload(
        certified=False,
        mode=MODE_NONE,
        S=_ONE,
        a_local=a,
        b_local=b,
        a=a,
        b=b,
        note=note,
        reconstruction_ok=False,
    )


def _pick_note(reasons: list[str]) -> str:
    cleaned = [r for r in reasons if r]
    if not cleaned:
        return "no_exact_common_factor"
    for r in cleaned:
        if r.startswith("bad_input"):
            return r
    for key in _NOTE_PRIORITY:
        if key in cleaned:
            return key
    return cleaned[0]
