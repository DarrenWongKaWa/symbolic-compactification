"""Exact Laurent helpers for toy hops. Never numeric agreement as ZERO."""
from __future__ import annotations

from typing import Any, Optional

import sympy

from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

_INF = (sympy.oo, -sympy.oo, sympy.zoo)


def parse_text(text: Any, symbols: list) -> Any:
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    try:
        return parse_expression(s, symbols)
    except (AdapterError, Exception):
        return None


def symbol_map(*exprs: Any) -> dict[str, sympy.Symbol]:
    out: dict[str, sympy.Symbol] = {}
    for e in exprs:
        for s in getattr(e, "free_symbols", set()) or []:
            out[str(s.name)] = s
    return out


def unevaluated_sum(parts: list[Any]) -> Any:
    cleaned = [p for p in parts if p is not None]
    if not cleaned:
        return None
    if len(cleaned) == 1:
        return cleaned[0]
    return sympy.Add(*cleaned, evaluate=False)


def is_infinity(expr: Any) -> bool:
    if expr is None:
        return False
    if expr in _INF:
        return True
    inf = getattr(expr, "is_infinite", None)
    return bool(inf is True)


def is_undefined(expr: Any) -> bool:
    if expr is None:
        return True
    if expr is sympy.nan:
        return True
    try:
        return bool(expr.has(sympy.nan))
    except Exception:
        return True


def _is_exact_nonzero_number(expr: Any) -> bool:
    if expr is None:
        return False
    if is_infinity(expr):
        return True
    try:
        if expr.free_symbols:
            return False
    except Exception:
        return False
    try:
        if expr == 0:
            return False
    except Exception:
        return False
    try:
        if expr.is_number and expr != 0:
            return True
    except Exception:
        pass
    return expr != 0


def residual_verdict(left: Any, right: Any) -> tuple[str, Any]:
    """ZERO only on exact identity. Timeout/failure is UNKNOWN."""
    if left is None or right is None:
        return UNKNOWN, None
    try:
        residual = left - right
    except Exception:
        return UNKNOWN, None
    try:
        if residual == 0 or left == right:
            return ZERO, residual
    except Exception:
        pass
    for transform in (
        (lambda e: e),
        sympy.expand,
        sympy.expand_func,
        sympy.cancel,
        sympy.together,
    ):
        try:
            got = transform(residual)
        except Exception:
            continue
        try:
            if got == 0:
                return ZERO, got
        except Exception:
            pass
        if is_infinity(got) or is_undefined(got):
            return NONZERO, got
        if _is_exact_nonzero_number(got):
            return NONZERO, got
        try:
            cancelled = sympy.cancel(sympy.together(got))
            if cancelled == 0:
                return ZERO, cancelled
        except Exception:
            pass
        try:
            num, den = sympy.fraction(sympy.together(got))
            num_e = sympy.expand(sympy.cancel(num))
            if num_e == 0:
                return ZERO, got
            try:
                poly = sympy.Poly(num_e, domain="QQ")
            except Exception:
                continue
            if poly.is_zero:
                return ZERO, got
            return NONZERO, got
        except Exception:
            pass
    try:
        expanded = sympy.expand(sympy.cancel(residual))
        if expanded == 0:
            return ZERO, expanded
        if is_infinity(expanded) or is_undefined(expanded):
            return NONZERO, expanded
        if _is_exact_nonzero_number(expanded):
            return NONZERO, expanded
        poly = sympy.Poly(expanded, domain="QQ")
        if poly.is_zero:
            return ZERO, expanded
        return NONZERO, expanded
    except Exception:
        pass
    return UNKNOWN, residual


def eval_probe(expr: Any, mapping: dict) -> Any:
    if expr is None:
        return None
    try:
        got = expr.xreplace(mapping)
    except Exception:
        try:
            got = expr.subs(mapping)
        except Exception:
            return None
    try:
        got = sympy.expand_func(sympy.expand(got))
    except Exception:
        pass
    return got


def probe_nonzero(
    residual: Any, probes: list, smap: dict[str, sympy.Symbol]
) -> tuple[Optional[str], Any]:
    """Exact special-value probes. Float agreement is ignored."""
    for row in probes or []:
        if not isinstance(row, dict):
            continue
        mapping: dict[Any, Any] = {}
        ok = True
        for name, raw in row.items():
            sym = smap.get(str(name))
            if sym is None:
                ok = False
                break
            try:
                if isinstance(raw, sympy.Basic):
                    val = raw
                else:
                    val = (
                        sympy.Integer(raw)
                        if isinstance(raw, int)
                        else sympy.sympify(raw)
                    )
            except Exception:
                ok = False
                break
            mapping[sym] = val
        if not ok or not mapping:
            continue
        got = eval_probe(residual, mapping)
        if got is None:
            continue
        if is_infinity(got) or _is_exact_nonzero_number(got):
            return NONZERO, got
        try:
            if got != 0 and not got.free_symbols:
                return NONZERO, got
        except Exception:
            continue
    return None, None


def verdict_with_probes(
    left: Any,
    right: Any,
    probes: list,
    smap: dict[str, sympy.Symbol],
) -> tuple[str, Any]:
    verdict, residual = residual_verdict(left, right)
    if verdict in {ZERO, NONZERO}:
        return verdict, residual
    hit, val = probe_nonzero(
        residual if residual is not None else left,
        probes,
        smap,
    )
    if hit == NONZERO:
        return NONZERO, val
    return verdict, residual


def series_atom(expr: Any, var: Any, nterms: int) -> tuple[Optional[Any], Optional[int], str]:
    """Return (series, order_exponent or None if exact, note)."""
    if expr is None or var is None:
        return None, None, "missing"
    try:
        n = int(nterms)
    except Exception:
        return None, None, "bad_nterms"
    try:
        s = expr.series(var, 0, n)
    except Exception as exc:
        return None, None, f"series:{type(exc).__name__}"
    if not isinstance(s, sympy.Expr):
        return None, None, "series:not_expr"
    order_n: Optional[int] = None
    o = s.getO() if hasattr(s, "getO") else None
    if o is not None:
        try:
            order_n = int(o.getn())
        except Exception:
            order_n = 0
    return s, order_n, "series"


def laurent_coeffs(
    finite: Any,
    var: Any,
    *,
    nmin: int,
    nmax: int,
) -> Optional[dict[int, Any]]:
    if finite is None or var is None:
        return None
    try:
        if finite == 0:
            return {k: sympy.Integer(0) for k in range(nmin, nmax + 1)}
    except Exception:
        pass
    shift = max(8, int(-nmin) + 2)
    try:
        w = sympy.expand(sympy.together(finite * var**shift))
        poly = sympy.Poly(w, var, domain=sympy.EX)
    except Exception:
        return None
    out: dict[int, Any] = {}
    for k in range(nmin, nmax + 1):
        out[k] = poly.nth(k + shift)
    return out
