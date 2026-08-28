"""Local exact residual helpers. Never numeric agreement. Never extra assumptions."""
from __future__ import annotations

from typing import Any, Optional

import sympy

from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError

_INF = (sympy.oo, -sympy.oo, sympy.zoo)


def parse_text(text: Any, symbols: list, functions: Optional[list] = None):
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None
    try:
        return parse_expression(s, symbols, functions=functions or None)
    except (AdapterError, Exception):
        return None


def symbol_map(*exprs: Any) -> dict[str, sympy.Symbol]:
    out: dict[str, sympy.Symbol] = {}
    for e in exprs:
        for s in getattr(e, "free_symbols", set()) or []:
            out[str(s.name)] = s
    return out


def named_symbol(name: str, *exprs: Any, real: bool = True) -> sympy.Symbol:
    found = symbol_map(*exprs).get(name)
    if found is not None:
        return found
    return sympy.Symbol(name, real=real)


def is_infinity(expr: Any) -> bool:
    if expr is None:
        return False
    if expr in _INF:
        return True
    inf = getattr(expr, "is_infinite", None)
    return bool(inf is True)


def is_unevaluated_limit(expr: Any) -> bool:
    if expr is None:
        return False
    if isinstance(expr, sympy.Limit):
        return True
    try:
        return bool(isinstance(expr, sympy.Expr) and expr.has(sympy.Limit))
    except Exception:
        return False


def take_limit(expr: Any, var: Any, point: Any, dir: Optional[str] = None):
    if expr is None or var is None or point is None:
        return None
    try:
        if dir is None:
            got = sympy.limit(expr, var, point)
        else:
            got = sympy.limit(expr, var, point, dir=dir)
    except Exception:
        return None
    if is_unevaluated_limit(got):
        return None
    return got


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
    transforms = (
        (lambda e: e),
        sympy.expand,
        sympy.expand_func,
        sympy.cancel,
        sympy.together,
    )
    for transform in transforms:
        try:
            got = transform(residual)
        except Exception:
            continue
        try:
            if got == 0:
                return ZERO, got
        except Exception:
            pass
        if is_infinity(got):
            return NONZERO, got
        if _is_exact_nonzero_number(got):
            return NONZERO, got
    try:
        simp = sympy.simplify(residual)
        if simp == 0:
            return ZERO, simp
        if is_infinity(simp) or _is_exact_nonzero_number(simp):
            return NONZERO, simp
    except Exception:
        pass
    try:
        expanded = sympy.expand(residual)
        poly = sympy.Poly(expanded, domain="QQ")
        if not poly.is_zero:
            return NONZERO, expanded
        if poly.is_zero:
            return ZERO, expanded
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
        got = sympy.expand(got)
    except Exception:
        pass
    try:
        if got.free_symbols:
            got = sympy.expand_func(got)
    except Exception:
        pass
    return got


def probe_nonzero(residual: Any, probes: list, smap: dict[str, sympy.Symbol]) -> tuple[Optional[str], Any]:
    """Exact rational/complex probes. Float agreement is ignored."""
    for row in probes or []:
        if not isinstance(row, dict):
            continue
        mapping = {}
        ok = True
        for name, raw in row.items():
            sym = smap.get(str(name)) or sympy.Symbol(str(name), real=True)
            try:
                if isinstance(raw, sympy.Basic):
                    val = raw
                else:
                    val = sympy.Integer(raw) if isinstance(raw, int) else sympy.sympify(raw)
            except Exception:
                ok = False
                break
            mapping[sym] = val
        if not ok:
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


def parse_math(case: dict[str, Any]) -> dict[str, Any]:
    symbols = list(case.get("symbols") or [])
    functions = list(case.get("functions") or [])
    math = dict(case.get("math") or {})
    parsed: dict[str, Any] = {"symbols": symbols, "functions": functions, "math": math}
    text_keys = (
        "expr",
        "claimed",
        "true",
        "left",
        "right",
        "F",
        "member",
        "cancelled_left",
        "cancelled_claimed",
        "true_newton",
        "true_derivative",
        "true_factor",
        "sketch_claimed",
        "source_piecewise",
    )
    for key in text_keys:
        if math.get(key) not in (None, ""):
            parsed[key] = parse_text(math[key], symbols, functions)
        else:
            parsed[key] = None
    exprs = [parsed[k] for k in text_keys if parsed.get(k) is not None]
    smap = symbol_map(*exprs)
    for spec in symbols:
        name = spec["name"] if isinstance(spec, dict) else str(spec)
        real = True if not isinstance(spec, dict) else spec.get("real", True)
        if name not in smap:
            smap[name] = sympy.Symbol(name, real=bool(real))
    parsed["smap"] = smap
    var_name = math.get("var")
    to_name = math.get("to")
    parsed["var"] = smap[var_name] if var_name in smap else (
        named_symbol(var_name, *exprs) if var_name else None
    )
    if to_name in smap:
        parsed["to"] = smap[to_name]
    elif to_name not in (None, ""):
        parsed["to"] = parse_text(to_name, symbols, functions)
    else:
        parsed["to"] = None
    parsed["x"] = smap.get("x")
    parsed["y"] = smap.get("y")
    parsed["z"] = smap.get(str(math.get("F_var") or "z"))
    parsed["probes"] = list(math.get("probes") or [])
    return parsed
