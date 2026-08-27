"""Fail-closed instantiation of A = O[F] for schema operator kinds.

Reuses constructor parse/instantiate/diff helpers when present. Missing
arguments, unknown kinds, and unparseable F yield None — never a guess.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.representation_invention.schema import OPERATOR_KINDS, OperatorSpec

try:
    from research.llm_abstraction.constructor import (
        _diff_repeat,
        instantiate as subst_instantiate,
        parse_flex,
    )
except Exception:  # pragma: no cover
    parse_flex = None  # type: ignore[assignment]
    subst_instantiate = None  # type: ignore[assignment]
    _diff_repeat = None  # type: ignore[assignment]

_DIFF_META = frozenset({"order", "n_diff", "times"})
_THETA_META = frozenset(
    {
        "member",
        "member_id",
        "O",
        "kind",
        "operator",
        "theta",
        "map",
        "note",
        "nodes",
        "order",
        "n_diff",
        "times",
        "var",
        "wrt",
        "variable",
        "index",
        "at",
        "to",
        "point",
        "delta",
        "step",
        "perm",
        "swap",
        "x",
        "y",
        "multiplicity",
    }
)


def _spec_parts(spec: OperatorSpec | dict[str, Any]) -> tuple[str, dict[str, Any], str]:
    if isinstance(spec, OperatorSpec):
        return spec.kind, dict(spec.args or {}), spec.member_id
    if not isinstance(spec, dict):
        return "", {}, ""
    kind = str(spec.get("kind") or spec.get("O") or "").strip()
    args = spec.get("args") if isinstance(spec.get("args"), dict) else {}
    if not args:
        args = {
            k: v
            for k, v in spec.items()
            if k not in {"kind", "O", "member_id", "member", "args"}
        }
    mid = str(spec.get("member_id") or spec.get("member") or "").strip()
    return kind, dict(args or {}), mid


def _theta(args: dict[str, Any], extra: Optional[dict[str, str]]) -> dict[str, str]:
    out: dict[str, str] = {}
    nested = args.get("theta") if isinstance(args.get("theta"), dict) else None
    if not nested:
        nested = args.get("map") if isinstance(args.get("map"), dict) else {}
    if isinstance(nested, dict):
        out.update({str(k): str(v) for k, v in nested.items()})
    for k, v in args.items():
        if k in _THETA_META:
            continue
        if isinstance(v, (str, int, float)):
            out[str(k)] = str(v)
    if extra:
        out.update({str(k): str(v) for k, v in extra.items()})
    return out


def _as_int(value: Any) -> Optional[int]:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return None
    return n


def _sym_named(expr: sympy.Expr, name: str) -> Optional[sympy.Symbol]:
    for s in expr.free_symbols:
        if s.name == name:
            return s
    return None


def _free_symbols(expr: sympy.Expr) -> list[sympy.Symbol]:
    return [s for s in expr.free_symbols if s.name not in {"pi", "E"}]


def _var_symbol(expr: sympy.Expr, args: dict[str, Any]) -> Optional[sympy.Symbol]:
    for key in ("var", "wrt", "variable", "index"):
        raw = args.get(key)
        if raw in (None, ""):
            continue
        found = _sym_named(expr, str(raw))
        if found is None:
            return None
        return found
    free = _free_symbols(expr)
    if len(free) == 1:
        return free[0]
    return None


def _parse_point(text: Any, symbols, functions) -> Optional[sympy.Expr]:
    if isinstance(text, sympy.Expr):
        return text
    if parse_flex is None:
        return None
    return parse_flex(str(text), symbols, functions)


def _eval_at(
    expr: sympy.Expr,
    var: sympy.Symbol,
    point: Any,
    symbols,
    functions,
) -> Optional[sympy.Expr]:
    pt = _parse_point(point, symbols, functions)
    if pt is None:
        return None
    return expr.xreplace({var: pt})


def _apply_theta(expr: sympy.Expr, theta: dict[str, str], symbols, functions) -> Optional[sympy.Expr]:
    if not theta:
        return expr
    if subst_instantiate is None:
        return None
    cleaned = {k: v for k, v in theta.items() if k not in _DIFF_META}
    if not cleaned:
        return expr
    return subst_instantiate(expr, cleaned, symbols, functions)


def _nodes_from_args(args: dict[str, Any]) -> list[Any]:
    raw = args.get("nodes")
    if isinstance(raw, (list, tuple)) and raw:
        out = []
        for item in raw:
            if isinstance(item, dict):
                out.append(item.get("expression") or item.get("name") or item.get("expr"))
            else:
                out.append(item)
        return [x for x in out if x not in (None, "")]
    if args.get("x") not in (None, "") and args.get("y") not in (None, ""):
        return [args["x"], args["y"]]
    return []


def _newton_table(
    expr: sympy.Expr,
    var: sympy.Symbol,
    nodes: list[Any],
    symbols,
    functions,
) -> Optional[sympy.Expr]:
    if len(nodes) < 2:
        return None
    points: list[sympy.Expr] = []
    values: list[sympy.Expr] = []
    for node in nodes:
        pt = _parse_point(node, symbols, functions)
        if pt is None:
            return None
        val = expr.xreplace({var: pt})
        points.append(pt)
        values.append(val)

    def rec(vals: list[sympy.Expr], pts: list[sympy.Expr]) -> Optional[sympy.Expr]:
        if len(vals) == 1:
            return vals[0]
        denom = pts[-1] - pts[0]
        if denom == 0:
            return None
        left = rec(vals[:-1], pts[:-1])
        right = rec(vals[1:], pts[1:])
        if left is None or right is None:
            return None
        return (right - left) / denom

    return rec(values, points)


def _permute(expr: sympy.Expr, args: dict[str, Any]) -> Optional[sympy.Expr]:
    swap = args.get("swap")
    if isinstance(swap, (list, tuple)) and len(swap) == 2:
        a = _sym_named(expr, str(swap[0]))
        b = _sym_named(expr, str(swap[1]))
        if a is None or b is None:
            return None
        tmp = sympy.Dummy()
        return expr.xreplace({a: tmp}).xreplace({b: a, tmp: b})
    perm = args.get("perm")
    if not isinstance(perm, (list, tuple)) or not perm:
        return None
    try:
        idx = [int(x) for x in perm]
    except (TypeError, ValueError):
        return None
    target = expr
    if not (isinstance(expr, AppliedUndef) and expr.args):
        found = None
        for sub in sympy.preorder_traversal(expr):
            if isinstance(sub, AppliedUndef) and sub.args:
                found = sub
                break
        if found is None:
            return None
        target = found
    args_t = list(target.args)
    if sorted(idx) != list(range(len(args_t))) or len(idx) != len(args_t):
        return None
    new_args = tuple(args_t[i] for i in idx)
    swapped = target.func(*new_args)
    if target is expr:
        return swapped
    return expr.xreplace({target: swapped})


def _identity(expr, args, theta, symbols, functions):
    return _apply_theta(expr, theta, symbols, functions)


def _substitution(expr, args, theta, symbols, functions):
    return _apply_theta(expr, theta, symbols, functions)


def _derivative(expr, args, theta, symbols, functions):
    if _diff_repeat is None:
        return None
    var = _var_symbol(expr, args)
    if var is None:
        return None
    order = _as_int(args.get("order"))
    if order is None:
        for k in _DIFF_META:
            if k in args:
                order = _as_int(args.get(k))
                break
        if order is None:
            order = _as_int(theta.get("order")) if theta else None
    if order is None:
        order = 1
    if order < 1:
        return None
    out = _diff_repeat(expr, var, order)
    at = args.get("at")
    if at not in (None, ""):
        out = _eval_at(out, var, at, symbols, functions)
        if out is None:
            return None
        rest = {k: v for k, v in theta.items() if k != var.name} if theta else {}
        return _apply_theta(out, rest, symbols, functions)
    return _apply_theta(out, theta, symbols, functions)


def _shift(expr, args, theta, symbols, functions):
    var = _var_symbol(expr, args)
    delta = args.get("delta")
    if delta in (None, ""):
        delta = args.get("step")
    if delta in (None, ""):
        delta = args.get("h")
    if var is None or delta in (None, ""):
        return None
    d_expr = _parse_point(delta, symbols, functions)
    if d_expr is None:
        return None
    out = expr.xreplace({var: var + d_expr})
    at = args.get("at")
    if at not in (None, ""):
        out = _eval_at(out, var, at, symbols, functions)
        if out is None:
            return None
    return _apply_theta(out, theta, symbols, functions)


def _recurrence(expr, args, theta, symbols, functions):
    return _shift(expr, args, theta, symbols, functions)


def _newton_dd(expr, args, theta, symbols, functions):
    var = _var_symbol(expr, args)
    nodes = _nodes_from_args(args)
    if var is None or len(nodes) < 2:
        return None
    out = _newton_table(expr, var, nodes, symbols, functions)
    if out is None:
        return None
    return _apply_theta(out, theta, symbols, functions)


def _hermite_dd(expr, args, theta, symbols, functions):
    if _diff_repeat is None:
        return None
    var = _var_symbol(expr, args)
    if var is None:
        return None
    nodes = _nodes_from_args(args)
    multiplicity = _as_int(args.get("multiplicity"))
    at = args.get("at")
    if at in (None, "") and len(nodes) == 1:
        at = nodes[0]
        if multiplicity is None:
            multiplicity = 2
    if at in (None, "") and len(nodes) == 2 and str(nodes[0]).strip() == str(nodes[1]).strip():
        at = nodes[0]
        if multiplicity is None:
            multiplicity = 2
    if at in (None, "") or multiplicity != 2:
        return None
    out = _diff_repeat(expr, var, 1)
    out = _eval_at(out, var, at, symbols, functions)
    if out is None:
        return None
    rest = {k: v for k, v in theta.items() if k != var.name} if theta else {}
    return _apply_theta(out, rest, symbols, functions)


def _permutation(expr, args, theta, symbols, functions):
    out = _permute(expr, args)
    if out is None:
        return None
    return _apply_theta(out, theta, symbols, functions)


def _limit(expr, args, theta, symbols, functions):
    var = _var_symbol(expr, args)
    point = args.get("to")
    if point in (None, ""):
        point = args.get("point")
    if point in (None, ""):
        point = args.get("at")
    if var is None or point in (None, ""):
        return None
    pt = _parse_point(point, symbols, functions)
    if pt is None:
        return None
    try:
        out = sympy.limit(expr, var, pt)
    except Exception:
        return None
    if out.has(sympy.Limit) or out in (sympy.nan, sympy.zoo, sympy.oo, -sympy.oo):
        return None
    return _apply_theta(out, theta, symbols, functions)


_DISPATCH = {
    "identity": _identity,
    "substitution": _substitution,
    "derivative": _derivative,
    "shift": _shift,
    "recurrence": _recurrence,
    "newton_dd": _newton_dd,
    "hermite_dd": _hermite_dd,
    "permutation": _permutation,
    "limit": _limit,
}


def instantiate_operator(
    f_expr: str | sympy.Expr,
    spec: OperatorSpec | dict[str, Any],
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
    *,
    theta: Optional[dict[str, str]] = None,
) -> Optional[sympy.Expr]:
    """Apply one schema operator to F. Returns None on any underspecification."""
    try:
        kind, args, _mid = _spec_parts(spec)
        if kind not in OPERATOR_KINDS or kind == "other":
            return None
        symbols = list(symbols or [])
        functions = list(functions or [])
        if isinstance(f_expr, sympy.Expr):
            expr = f_expr
        else:
            if parse_flex is None or not str(f_expr).strip():
                return None
            expr = parse_flex(str(f_expr), symbols, functions)
        if expr is None or not isinstance(expr, sympy.Expr):
            return None
        mapping = _theta(args, theta)
        handler = _DISPATCH.get(kind)
        if handler is None:
            return None
        out = handler(expr, args, mapping, symbols, functions)
        if out is None or not isinstance(out, sympy.Expr):
            return None
        return out
    except Exception:
        return None
