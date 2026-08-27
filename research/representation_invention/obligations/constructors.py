"""Newton / Hermite reconstructions used by the experimental compiler.

Prefer ``research.representation_invention.dd`` when it exposes the public
constructors. Otherwise use the local formulas below.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import sympy

from research.llm_abstraction.constructor import _sym_named, parse_flex

_DD_PKG = None
try:
    from research.representation_invention import dd as _DD_PKG  # type: ignore
except Exception:  # pragma: no cover - import surface
    _DD_PKG = None

_F_HEAD = re.compile(
    r"^\s*([A-Za-z_]\w*)\s*\(\s*([A-Za-z_]\w*)\s*\)\s*=",
)

# True when reconstructions came from this module rather than package dd/.
USED_LOCAL_DD_FALLBACK = not callable(getattr(_DD_PKG, "newton_first", None))


def dd_backend_name() -> str:
    if callable(getattr(_DD_PKG, "newton_first", None)):
        return "research.representation_invention.dd"
    return "local_dd"


def parse_latent(
    text: str,
    latent_variables: Optional[list[str]],
    symbols: list,
    functions: Optional[list],
) -> tuple[Optional[sympy.Expr], Optional[sympy.Symbol], str]:
    """Return (F, z, z_name). F is the latent body after stripping F(z)=."""
    raw = (text or "").strip()
    if not raw:
        return None, None, ""
    if len(raw) > 2500:
        return None, None, ""
    zname = ""
    m = _F_HEAD.match(raw)
    if m:
        zname = m.group(2)
    elif latent_variables:
        zname = str(latent_variables[0])
    expr = parse_flex(raw, symbols, functions)
    if expr is None:
        return None, None, zname
    z = _sym_named(expr, zname) if zname else None
    if z is None and zname:
        z = sympy.Symbol(zname)
    if z is None:
        fsyms = [s for s in expr.free_symbols if s.name not in {"pi", "E"}]
        if len(fsyms) == 1:
            z = next(iter(fsyms))
            zname = z.name
    return expr, z, zname


def eval_F(F: sympy.Expr, z: Optional[sympy.Symbol], point: sympy.Expr) -> Optional[sympy.Expr]:
    if F is None or z is None or point is None:
        return None
    return F.xreplace({z: point})


def _nodes_equal(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.expand(a - b) == 0
    except Exception:
        return False


def _local_newton_first(F: sympy.Expr, z: sympy.Symbol, x: sympy.Expr, y: sympy.Expr) -> sympy.Expr:
    return (eval_F(F, z, x) - eval_F(F, z, y)) / (x - y)


def newton_first(F: sympy.Expr, z: sympy.Symbol, x: sympy.Expr, y: sympy.Expr) -> sympy.Expr:
    fn = getattr(_DD_PKG, "newton_first", None) if _DD_PKG is not None else None
    if callable(fn):
        return fn(F, z, x, y)
    return _local_newton_first(F, z, x, y)


def _local_repeated_diagonal(F: sympy.Expr, z: sympy.Symbol, x: sympy.Expr) -> sympy.Expr:
    return sympy.diff(F, z).xreplace({z: x})


def repeated_diagonal(F: sympy.Expr, z: sympy.Symbol, x: sympy.Expr) -> sympy.Expr:
    fn = getattr(_DD_PKG, "repeated_diagonal", None) if _DD_PKG is not None else None
    if callable(fn):
        return fn(F, z, x)
    return _local_repeated_diagonal(F, z, x)


def _all_equal_dd(F: sympy.Expr, z: sympy.Symbol, x: sympy.Expr, times: int) -> sympy.Expr:
    k = times - 1
    if k <= 0:
        return eval_F(F, z, x)
    return sympy.diff(F, z, k).xreplace({z: x}) / sympy.factorial(k)


def divided_difference(F: sympy.Expr, z: sympy.Symbol, xs: list[sympy.Expr]) -> sympy.Expr:
    """F[x0,...,xk] with the listed (possibly repeated) nodes."""
    if not xs:
        raise ValueError("empty_nodes")
    if len(xs) == 1:
        return eval_F(F, z, xs[0])
    if all(_nodes_equal(xi, xs[0]) for xi in xs):
        return _all_equal_dd(F, z, xs[0], len(xs))
    if _nodes_equal(xs[0], xs[-1]):
        for i in range(1, len(xs)):
            rot = xs[i:] + xs[:i]
            if not _nodes_equal(rot[0], rot[-1]):
                return divided_difference(F, z, rot)
        return _all_equal_dd(F, z, xs[0], len(xs))
    return (
        divided_difference(F, z, xs[:-1]) - divided_difference(F, z, xs[1:])
    ) / (xs[0] - xs[-1])


def _group_nodes(nodes: list[Any]) -> list[tuple[sympy.Expr, int]]:
    grouped: list[tuple[sympy.Expr, int]] = []
    for item in nodes:
        if isinstance(item, (tuple, list)) and len(item) == 2 and isinstance(item[1], (int, float, str)):
            grouped.append((item[0], int(item[1])))
            continue
        if grouped and _nodes_equal(grouped[-1][0], item):
            expr, n = grouped[-1]
            grouped[-1] = (expr, n + 1)
        else:
            grouped.append((item, 1))
    return grouped


class LatentTooLarge(ValueError):
    """Generic constructor refuses a too-large latent (fail closed, not ZERO)."""


def hermite_nodes(F: sympy.Expr, z: sympy.Symbol, nodes: list[Any]) -> sympy.Expr:
    """``nodes`` is either expanded exprs or ``(expr, multiplicity)`` pairs."""
    try:
        n_ops = int(sympy.count_ops(F))
    except Exception:
        n_ops = 0
    if n_ops > 120:
        raise LatentTooLarge(f"hermite_latent_ops={n_ops}")
    grouped = _group_nodes(nodes)
    fn = None
    if _DD_PKG is not None:
        fn = getattr(_DD_PKG, "hermite_nodes", None) or getattr(_DD_PKG, "hermite_dd", None)
    if callable(fn):
        return fn(F, z, grouped)
    seq: list[sympy.Expr] = []
    for expr, mult in grouped:
        seq.extend([expr] * max(1, int(mult)))
    return divided_difference(F, z, seq)


def split_piecewise(expr: sympy.Expr) -> tuple[Optional[sympy.Expr], Optional[sympy.Expr]]:
    """True-branch (generic) and first non-True branch (degenerate)."""
    if not isinstance(expr, sympy.Piecewise):
        return None, None
    generic = None
    degenerate = None
    for val, cond in expr.args:
        if cond is True or cond == sympy.true:
            generic = val
        elif degenerate is None:
            degenerate = val
    return generic, degenerate


def take_limit(expr: sympy.Expr, var: sympy.Expr, point: sympy.Expr) -> sympy.Expr:
    from symbolic_compactification.budgets import run_with_budget

    target = var
    body = expr
    if not isinstance(var, sympy.Symbol):
        target = sympy.Dummy("lim_var")
        body = expr.xreplace({var: target})
    try:
        ops = int(sympy.count_ops(body))
    except Exception:
        ops = 0
    if ops < 80:
        return sympy.limit(body, target, point)
    return run_with_budget(
        sympy.limit,
        (body, target, point),
        seconds=8.0,
        operation="sympy.limit",
        mode="process",
    )



