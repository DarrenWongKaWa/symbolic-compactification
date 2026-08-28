"""Negative Laurent coefficient certifier (Track V5-E).

No LLM. For each p<0 in a sparse map, C_p == 0 only via identity,
``expand==0``, or ``cancel==0``. A matching t^0 term is ignored and must
not skip a leftover t^{-1}. Size-guard is UNKNOWN, never ZERO.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.coefficient_laurent.schema import NONZERO, UNKNOWN, ZERO

OPS_CAP = 120

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    -sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


@dataclass(frozen=True)
class NegativePowerRecord:
    """Exact decision for one negative Laurent power."""

    power: int
    coefficient_expr: str
    verdict: str
    method: str = ""
    exact: bool = False
    provenance: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class NegativeCertificate:
    """LEVEL B: all C_p for p<0 vanish, or a leftover pole, or undecided."""

    verdict: str
    records: tuple[NegativePowerRecord, ...]
    provenance: str = ""
    steps: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return OPS_CAP + 1


def _has_nonfinite(expr: sympy.Expr) -> bool:
    try:
        if any(expr == sentinel for sentinel in _NONFINITE):
            return True
        return bool(expr.has(*_NONFINITE))
    except Exception:
        return True


def _as_power(key: Any) -> Optional[int]:
    if isinstance(key, bool):
        return None
    if isinstance(key, int):
        return int(key)
    if isinstance(key, sympy.Integer):
        return int(key)
    if isinstance(key, str):
        text = key.strip()
        if text.startswith("+"):
            text = text[1:]
        try:
            return int(text)
        except ValueError:
            return None
    return None


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, str):
        try:
            got = sympy.sympify(value)
        except Exception:
            return None
        return got if isinstance(got, sympy.Expr) else None
    return None


def _finite_nonzero_number(expr: sympy.Expr) -> bool:
    if _has_nonfinite(expr):
        return False
    try:
        if expr.is_number is not True:
            return False
        return expr.equals(0) is False
    except Exception:
        return False


def _poly_not_identically_zero(expr: sympy.Expr) -> bool:
    try:
        poly = sympy.Poly(expr)
    except Exception:
        return False
    if poly.is_zero:
        return False
    try:
        coeffs = poly.coeffs()
        return bool(coeffs) and all(c.is_number for c in coeffs) and any(
            c.equals(0) is False for c in coeffs
        )
    except Exception:
        return False


def _classify_coeff(expr: sympy.Expr) -> tuple[str, str, tuple[str, ...]]:
    """Return (verdict, method, provenance) for one coefficient."""
    if expr == 0:
        return ZERO, "identity", ("identity",)
    ops = _count_ops(expr)
    if ops > OPS_CAP:
        return UNKNOWN, "size_guard", (f"size_guard:{ops}",)
    if _has_nonfinite(expr):
        return UNKNOWN, "nonfinite", ("nonfinite",)

    expanded: Optional[sympy.Expr] = None
    try:
        expanded = sympy.expand(expr)
        if expanded == 0:
            return ZERO, "expand", ("expand==0",)
    except Exception as exc:
        expanded = None
        expand_err = f"expand:{type(exc).__name__}"
    else:
        expand_err = ""

    cancelled: Optional[sympy.Expr] = None
    try:
        cancelled = sympy.cancel(expr)
        if cancelled == 0:
            return ZERO, "cancel", ("cancel==0",)
    except Exception as exc:
        cancelled = None
        cancel_err = f"cancel:{type(exc).__name__}"
    else:
        cancel_err = ""

    for form, tag in ((expr, "raw"), (expanded, "expand"), (cancelled, "cancel")):
        if form is None:
            continue
        if _finite_nonzero_number(form):
            return NONZERO, "nonzero", (f"{tag}:nonzero_number",)
        if _poly_not_identically_zero(form):
            return NONZERO, "nonzero", (f"{tag}:nonzero_poly",)

    extra = tuple(s for s in (expand_err, cancel_err) if s)
    return UNKNOWN, "undecided", extra + ("undecided",)


def _record_for(power: int, raw: Any) -> NegativePowerRecord:
    expr = _as_expr(raw)
    if expr is None:
        return NegativePowerRecord(
            power=power,
            coefficient_expr=str(raw),
            verdict=UNKNOWN,
            method="unparsed",
            exact=False,
            provenance=("unparsed",),
        )
    verdict, method, prov = _classify_coeff(expr)
    return NegativePowerRecord(
        power=power,
        coefficient_expr=str(expr),
        verdict=verdict,
        method=method,
        exact=verdict in (ZERO, NONZERO),
        provenance=prov,
    )


def _aggregate(
    records: tuple[NegativePowerRecord, ...],
    *,
    malformed: bool,
    steps: list[str],
) -> NegativeCertificate:
    if any(rec.verdict == NONZERO for rec in records):
        leftover = next(rec.power for rec in records if rec.verdict == NONZERO)
        steps.append(f"t^{leftover}:NONZERO")
        return NegativeCertificate(
            NONZERO, records, provenance=f"t^{leftover}:NONZERO", steps=tuple(steps)
        )
    if malformed or any(rec.verdict == UNKNOWN for rec in records):
        steps.append("undecided")
        return NegativeCertificate(
            UNKNOWN, records, provenance="undecided", steps=tuple(steps)
        )
    steps.append("all_negative_zero")
    return NegativeCertificate(
        ZERO, records, provenance="all_negative_zero", steps=tuple(steps)
    )


def certify_negative(sparse_map: Mapping[Any, Any] | None) -> NegativeCertificate:
    """Decide whether every negative Laurent coefficient vanishes.

    ``sparse_map`` keys are integer powers (or decimal strings of those
    powers). Non-negative powers, including a matching t^0 term, are
    ignored. Every p<0 is classified; the loop does not stop because t^0
    is present or looks like a target match.
    """
    steps: list[str] = []
    if not isinstance(sparse_map, Mapping):
        steps.append("malformed:not_mapping")
        return NegativeCertificate(
            UNKNOWN, (), provenance="malformed", steps=tuple(steps)
        )

    buckets: dict[int, list[Any]] = {}
    malformed = False
    for key, raw in sparse_map.items():
        power = _as_power(key)
        if power is None:
            malformed = True
            steps.append(f"unparsed_key:{key!r}")
            continue
        if power >= 0:
            steps.append(f"skip_nonneg:t^{power}")
            continue
        buckets.setdefault(power, []).append(raw)

    records: list[NegativePowerRecord] = []
    for power in sorted(buckets):
        values = buckets[power]
        if len(values) > 1:
            malformed = True
            steps.append(f"duplicate:t^{power}")
            recs = [_record_for(power, v) for v in values]
            if any(r.verdict == NONZERO for r in recs):
                chosen = next(r for r in recs if r.verdict == NONZERO)
            else:
                chosen = NegativePowerRecord(
                    power=power,
                    coefficient_expr=str(values[0]),
                    verdict=UNKNOWN,
                    method="duplicate",
                    exact=False,
                    provenance=("duplicate",),
                )
            records.append(chosen)
            continue
        rec = _record_for(power, values[0])
        steps.append(f"t^{power}:{rec.verdict}:{rec.method}")
        records.append(rec)

    return _aggregate(tuple(records), malformed=malformed, steps=steps)
