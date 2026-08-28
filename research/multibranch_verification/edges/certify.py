"""Local edge certifier cascade (Track V2-B).

``certify_edge`` decides a single typed edge. Timeout and size-guard are
UNKNOWN, never ZERO. Track V packages are imported, not copied. No Guo
pairing and no LLM.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.multibranch_verification.schema import (
    EDGE_RELATIONS,
    LocalEdge,
)
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.confluence import check_limit
from research.scalable_verification.dd_cert import (
    hermite_xxx_ok,
    hermite_xxy_ok,
    hermite_xyy_ok,
    newton_first_ok,
    repeated_ok,
)
from research.scalable_verification.factor import split_multiplicative
from symbolic_compactification.budgets import BudgetExceeded
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import parse_expression

OPS_CAP = 200

LIMIT_RELATIONS = {
    "limit",
    "one_parameter_confluence",
    "repeated_node_confluence",
}
SUBSTITUTION_RELATIONS = {"substitution"}
DERIVATIVE_RELATIONS = {"derivative"}
DD_RELATIONS = {"dd_recurrence", "hermite_dd_recurrence"}

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


@dataclass(frozen=True)
class EdgeCertificate:
    """Verdict of one local edge plus cascade provenance."""

    verdict: str
    provenance: str
    steps: tuple[str, ...]
    relation: str = ""
    source: str = ""
    target: str = ""
    variable: str = ""
    target_value: str = ""
    residual: Optional[str] = None
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_local_edge(self) -> LocalEdge:
        return LocalEdge(
            source=self.source,
            target=self.target,
            relation=self.relation,
            variable=self.variable,
            target_value=self.target_value,
            verdict=self.verdict,
            provenance=self.provenance,
        )


def certify_edge(
    source_expr: Any,
    target_expr: Any,
    relation: Any,
    variable: Any,
    target_value: Any,
    symbols: Any,
    functions: Any = None,
) -> EdgeCertificate:
    """Certify ``source --relation--> target`` at ``variable = target_value``.

    Cascade: substitution, cancel, ``split_multiplicative``, together,
    ``check_limit``, derivative, ``dd_cert`` (dd/hermite only), else UNKNOWN.
    """
    steps: list[str] = []
    rel = str(relation or "").strip()
    try:
        return _certify(
            source_expr,
            target_expr,
            rel,
            variable,
            target_value,
            symbols,
            functions,
            steps,
        )
    except BudgetExceeded:
        steps.append("timeout")
        return _result(UNKNOWN, "timeout", steps, rel, source_expr, target_expr, variable, target_value)
    except Exception as exc:
        steps.append(f"error:{type(exc).__name__}")
        return _result(UNKNOWN, "UNKNOWN", steps, rel, source_expr, target_expr, variable, target_value)


def _ops_too_large(*exprs: Any) -> bool:
    for expr in exprs:
        if expr is None or not isinstance(expr, sympy.Basic):
            continue
        try:
            n = int(sympy.count_ops(expr, visual=False))
        except Exception:
            return True
        if n > OPS_CAP:
            return True
    return False


def _certify(
    source_expr: Any,
    target_expr: Any,
    rel: str,
    variable: Any,
    target_value: Any,
    symbols: Any,
    functions: Any,
    steps: list[str],
) -> EdgeCertificate:
    declared = _normalize_declared(symbols, source_expr, target_expr, variable, target_value)
    funcs = list(functions) if functions else None

    source = _coerce(source_expr, declared, funcs)
    target = _coerce(target_expr, declared, funcs)
    if source is None or target is None:
        steps.append("parse:failed")
        return _result(UNKNOWN, "parse", steps, rel, source_expr, target_expr, variable, target_value)

    cmap = _canon_map(source, target)
    source = _align(source, cmap)
    target = _align(target, cmap)
    var = _coerce_in_context(variable, (source, target), declared, funcs)
    point = _coerce_in_context(target_value, (source, target, var), declared, funcs)
    cmap = _canon_map(source, target, var, point)
    source, target, var, point = (
        _align(source, cmap),
        _align(target, cmap),
        _align(var, cmap) if var is not None else None,
        _align(point, cmap) if point is not None else None,
    )

    if _ops_too_large(source, target, var, point):
        steps.append("size_guard")
        return _result(
            UNKNOWN, "size_guard", steps, rel, source, target, var, point,
        )

    work_s, work_t = source, target

    got = _step_substitution(work_s, work_t, var, point, rel, steps)
    if got is not None:
        return _finish(got, rel, source, target, var, point)

    got = _step_cancel(work_s, work_t, var, point, rel, steps)
    if got is not None:
        return _finish(got, rel, source, target, var, point)

    split_s, split_t = _step_split(work_s, work_t, rel, steps)
    if isinstance(split_s, EdgeCertificate):
        return _finish(split_s, rel, source, target, var, point)
    if split_s is not None and split_t is not None:
        work_s, work_t = split_s, split_t
        got = _step_substitution(work_s, work_t, var, point, rel, steps, prefix="split_multiplicative:")
        if got is not None:
            return _finish(got, rel, source, target, var, point)
        got = _step_cancel(work_s, work_t, var, point, rel, steps, prefix="split_multiplicative:")
        if got is not None:
            return _finish(got, rel, source, target, var, point)

    got = _step_together(work_s, work_t, var, point, rel, steps)
    if got is not None:
        return _finish(got, rel, source, target, var, point)

    if _is_limit_like(rel) and var is not None and point is not None:
        got = _step_check_limit(work_s, work_t, var, point, steps)
        if got is not None:
            return _finish(got, rel, source, target, var, point)

    if _is_derivative_like(rel) or _is_dd_or_hermite(rel):
        got = _step_derivative(source, target, var, point, rel, steps)
        if got is not None:
            return _finish(got, rel, source, target, var, point)

    if _is_dd_or_hermite(rel):
        got = _step_dd_cert(source, target, var, point, rel, declared, steps)
        if got is not None:
            return _finish(got, rel, source, target, var, point)

    steps.append("UNKNOWN")
    return _result(UNKNOWN, "UNKNOWN", steps, rel, source, target, var, point)


def _step_substitution(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    rel: str,
    steps: list[str],
    *,
    prefix: str = "",
) -> Optional[EdgeCertificate]:
    step = f"{prefix}substitution"
    if var is None or point is None:
        steps.append(f"{step}:skipped")
        return None
    val = _finite_eval(source, var, point)
    if val is None:
        steps.append(f"{step}:not_finite")
        return None
    eq = _algebraic_equal(val, target)
    if eq is True and _sub_proves_zero(rel):
        steps.append(f"{step}:ZERO")
        return _bare(ZERO, step, steps, witness=str(val))
    if eq is False and _sub_proves_nonzero(rel):
        steps.append(f"{step}:NONZERO")
        return _bare(NONZERO, step, steps, residual=str(val - target), witness=str(val))
    steps.append(f"{step}:undecided")
    return None


def _step_cancel(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    rel: str,
    steps: list[str],
    *,
    prefix: str = "",
) -> Optional[EdgeCertificate]:
    step = f"{prefix}cancel"
    eq = _algebraic_equal(source, target)
    if eq is True:
        steps.append(f"{step}:ZERO")
        return _bare(ZERO, step, steps, residual="0")
    if eq is False and _is_substitution(rel):
        steps.append(f"{step}:NONZERO")
        return _bare(NONZERO, step, steps, residual=str(source - target))

    reduced = _safe_cancel(source)
    if reduced is None:
        steps.append(f"{step}:failed")
        return None
    if var is not None and point is not None:
        val = _finite_eval(reduced, var, point)
        if val is None:
            steps.append(f"{step}:not_finite")
            return None
        eqv = _algebraic_equal(val, target)
        if eqv is True and _sub_proves_zero(rel):
            steps.append(f"{step}:ZERO")
            return _bare(ZERO, step, steps, witness=str(val), residual="0")
        if eqv is False and _sub_proves_nonzero(rel):
            steps.append(f"{step}:NONZERO")
            return _bare(NONZERO, step, steps, residual=str(val - target), witness=str(val))
        steps.append(f"{step}:undecided")
        return None

    eqr = _algebraic_equal(reduced, target)
    if eqr is True:
        steps.append(f"{step}:ZERO")
        return _bare(ZERO, step, steps, residual="0")
    if eqr is False and _is_substitution(rel):
        steps.append(f"{step}:NONZERO")
        return _bare(NONZERO, step, steps, residual=str(reduced - target))
    steps.append(f"{step}:undecided")
    return None


def _step_split(
    source: sympy.Expr,
    target: sympy.Expr,
    rel: str,
    steps: list[str],
) -> tuple[Any, Any]:
    try:
        out = split_multiplicative(source, target)
    except Exception as exc:
        steps.append(f"split_multiplicative:{type(exc).__name__}")
        return None, None
    certified = bool(out.get("certified"))
    note = str(out.get("note") or "")
    if not certified:
        steps.append(f"split_multiplicative:uncertified:{note}")
        return None, None
    a_loc = out.get("A_local")
    b_loc = out.get("B_local")
    if not isinstance(a_loc, sympy.Expr) or not isinstance(b_loc, sympy.Expr):
        steps.append("split_multiplicative:bad_payload")
        return None, None
    steps.append(f"split_multiplicative:certified:{note}")
    eq = _algebraic_equal(a_loc, b_loc)
    if eq is True:
        return _bare(ZERO, "split_multiplicative", steps, residual="0"), None
    if eq is False and _is_substitution(rel):
        return _bare(NONZERO, "split_multiplicative", steps, residual=str(a_loc - b_loc)), None
    return a_loc, b_loc


def _step_together(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    rel: str,
    steps: list[str],
) -> Optional[EdgeCertificate]:
    step = "together"
    reduced = _safe_together_cancel(source)
    tgt = _safe_together_cancel(target)
    if reduced is None:
        steps.append(f"{step}:failed")
        return None
    if tgt is not None:
        eq = _algebraic_equal(reduced, tgt)
        if eq is True:
            steps.append(f"{step}:ZERO")
            return _bare(ZERO, step, steps, residual="0")
        if eq is False and _is_substitution(rel):
            steps.append(f"{step}:NONZERO")
            return _bare(NONZERO, step, steps, residual=str(reduced - tgt))
    if var is not None and point is not None:
        val = _finite_eval(reduced, var, point)
        if val is None:
            steps.append(f"{step}:not_finite")
            return None
        eqv = _algebraic_equal(val, target)
        if eqv is True and _sub_proves_zero(rel):
            steps.append(f"{step}:ZERO")
            return _bare(ZERO, step, steps, witness=str(val), residual="0")
        if eqv is False and _sub_proves_nonzero(rel):
            steps.append(f"{step}:NONZERO")
            return _bare(NONZERO, step, steps, residual=str(val - target), witness=str(val))
        steps.append(f"{step}:undecided")
        return None
    steps.append(f"{step}:undecided")
    return None


def _step_check_limit(
    source: sympy.Expr,
    target: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
    steps: list[str],
) -> Optional[EdgeCertificate]:
    try:
        r = check_limit(source, var, point, target)
    except BudgetExceeded:
        steps.append("check_limit:timeout")
        return _bare(UNKNOWN, "timeout", steps)
    except Exception as exc:
        steps.append(f"check_limit:{type(exc).__name__}")
        return None
    inner = r.provenance or "check_limit"
    for s in r.steps:
        steps.append(f"check_limit:{s}")
    if r.verdict == ZERO:
        steps.append("check_limit:ZERO")
        return _bare(ZERO, f"check_limit:{inner}", steps, witness=r.witness)
    if r.verdict == NONZERO:
        steps.append("check_limit:NONZERO")
        return _bare(NONZERO, f"check_limit:{inner}", steps, witness=r.witness)
    steps.append(f"check_limit:{inner}")
    if inner in {"timeout", "sympy.limit:timeout"} or "timeout" in inner:
        return _bare(UNKNOWN, "timeout", steps)
    if "skip_count_ops" in inner or inner == "size_guard":
        return _bare(UNKNOWN, "size_guard", steps)
    return None


def _step_derivative(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    rel: str,
    steps: list[str],
) -> Optional[EdgeCertificate]:
    step = "derivative"
    if var is None:
        steps.append(f"{step}:skipped")
        return None
    try:
        d1 = sympy.diff(source, var)
        if point is not None:
            d1 = d1.xreplace({var: point})
    except Exception:
        steps.append(f"{step}:failed")
        return None
    if not _is_finite(d1):
        steps.append(f"{step}:not_finite")
        return None
    eq = _algebraic_equal(d1, target)
    if eq is True:
        steps.append(f"{step}:ZERO")
        return _bare(ZERO, step, steps, witness=str(d1), residual="0")
    # F[x,x,x] = F''(x)/2
    try:
        d2 = sympy.diff(source, var, 2) / sympy.Integer(2)
        if point is not None:
            d2 = d2.xreplace({var: point})
    except Exception:
        d2 = None
    if d2 is not None and _is_finite(d2):
        eq2 = _algebraic_equal(d2, target)
        if eq2 is True and _is_dd_or_hermite(rel):
            steps.append(f"{step}:ZERO:second")
            return _bare(ZERO, step, steps, witness=str(d2), residual="0")
    if eq is False and _is_derivative(rel):
        steps.append(f"{step}:NONZERO")
        return _bare(NONZERO, step, steps, residual=str(d1 - target), witness=str(d1))
    steps.append(f"{step}:undecided")
    return None


def _step_dd_cert(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    rel: str,
    declared: list,
    steps: list[str],
) -> Optional[EdgeCertificate]:
    z = var
    if z is None:
        z = _pick_dummy(source, target, declared)
    if z is None:
        steps.append("dd_cert:missing_dummy")
        return None
    nodes = _dd_nodes(source, target, z, point, declared)
    certs: list[tuple[str, Any]] = []
    hermite = _is_hermite(rel)
    dd = _is_dd(rel) or hermite
    if hermite and len(nodes) >= 2:
        certs.append(("hermite_xxy", hermite_xxy_ok(source, z, nodes[0], nodes[1], target)))
        certs.append(("hermite_xyy", hermite_xyy_ok(source, z, nodes[0], nodes[1], target)))
    if hermite:
        node = point if point is not None else (nodes[0] if nodes else None)
        if node is not None:
            certs.append(("hermite_xxx", hermite_xxx_ok(source, z, node, target)))
            certs.append(("repeated", repeated_ok(source, z, node, target)))
    if dd and len(nodes) >= 2:
        certs.append(("newton_first", newton_first_ok(source, z, nodes[0], nodes[1], target)))
    if dd and not hermite:
        node = point if point is not None else (nodes[0] if nodes else None)
        if node is not None:
            certs.append(("repeated", repeated_ok(source, z, node, target)))

    if not certs:
        steps.append("dd_cert:no_applicable")
        return None

    saw_nonzero = False
    saw_unknown = False
    for label, cert in certs:
        verdict = getattr(cert, "verdict", UNKNOWN)
        note = getattr(cert, "note", "")
        steps.append(f"dd_cert:{label}:{verdict}:{note}")
        if verdict == ZERO:
            return _bare(ZERO, f"dd_cert:{label}", steps, residual="0")
        if verdict == NONZERO:
            saw_nonzero = True
        else:
            saw_unknown = True
    if saw_nonzero and not saw_unknown:
        return _bare(NONZERO, "dd_cert", steps)
    steps.append("dd_cert:undecided")
    return None


def _dd_nodes(
    source: sympy.Expr,
    target: sympy.Expr,
    z: sympy.Expr,
    point: Optional[sympy.Expr],
    declared: list,
) -> list[sympy.Expr]:
    exclude = set()
    if isinstance(z, sympy.Symbol):
        exclude.add(z.name)
    nodes: list[sympy.Expr] = []
    cmap = _canon_map(source, target, z, point)

    def _add(expr: Any) -> None:
        if expr is None:
            return
        if isinstance(expr, sympy.Symbol):
            if expr.name in exclude:
                return
            if any(isinstance(n, sympy.Symbol) and n.name == expr.name for n in nodes):
                return
            nodes.append(_align(expr, cmap))
            return
        if isinstance(expr, sympy.Expr) and expr.free_symbols:
            for s in sorted(expr.free_symbols, key=lambda s: s.name):
                _add(s)

    _add(point)
    if isinstance(target, sympy.Expr):
        for s in sorted(target.free_symbols, key=lambda s: s.name):
            _add(s)
    for item in declared or []:
        name = item["name"] if isinstance(item, dict) else str(item)
        if name in exclude:
            continue
        if name in cmap:
            _add(cmap[name])
        else:
            _add(sympy.Symbol(name))
    return nodes


def _pick_dummy(source: sympy.Expr, target: sympy.Expr, declared: list) -> Optional[sympy.Expr]:
    src_names = {s.name for s in source.free_symbols if isinstance(s, sympy.Symbol)}
    tgt_names = {s.name for s in target.free_symbols if isinstance(s, sympy.Symbol)}
    only = src_names - tgt_names
    if len(only) == 1:
        name = next(iter(only))
        for s in source.free_symbols:
            if isinstance(s, sympy.Symbol) and s.name == name:
                return s
    for item in declared or []:
        name = item["name"] if isinstance(item, dict) else str(item)
        if name in src_names and name not in tgt_names:
            for s in source.free_symbols:
                if isinstance(s, sympy.Symbol) and s.name == name:
                    return s
    return None


def _sub_proves_zero(rel: str) -> bool:
    return _is_limit_like(rel) or _is_substitution(rel)


def _sub_proves_nonzero(rel: str) -> bool:
    return _is_limit_like(rel) or _is_substitution(rel)


def _is_limit_like(rel: str) -> bool:
    return rel in LIMIT_RELATIONS


def _is_substitution(rel: str) -> bool:
    return rel in SUBSTITUTION_RELATIONS


def _is_derivative(rel: str) -> bool:
    return rel in DERIVATIVE_RELATIONS


def _is_derivative_like(rel: str) -> bool:
    return rel in DERIVATIVE_RELATIONS


def _is_dd_or_hermite(rel: str) -> bool:
    return rel in DD_RELATIONS


def _is_hermite(rel: str) -> bool:
    return rel == "hermite_dd_recurrence"


def _is_dd(rel: str) -> bool:
    return rel == "dd_recurrence"


def _finite_eval(expr: sympy.Expr, var: sympy.Expr, point: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        val = expr.xreplace({var: point})
    except Exception:
        return None
    if _is_finite(val):
        return val
    return None


def _safe_cancel(expr: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        return sympy.cancel(expr)
    except Exception:
        return None


def _safe_together_cancel(expr: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        return sympy.cancel(sympy.together(expr))
    except Exception:
        return None


def _is_finite(expr: Any) -> bool:
    if expr is None:
        return False
    if not isinstance(expr, sympy.Basic):
        try:
            expr = sympy.sympify(expr)
        except Exception:
            return False
    if any(expr == sentinel for sentinel in _NONFINITE):
        return False
    try:
        if expr.has(*_NONFINITE) or expr.has(sympy.nan):
            return False
    except Exception:
        return False
    if isinstance(expr, sympy.Limit) or expr.has(sympy.Limit):
        return False
    try:
        if expr.is_infinite is True:
            return False
    except Exception:
        pass
    return True


def _algebraic_equal(a: sympy.Expr, b: sympy.Expr) -> Optional[bool]:
    if a == b:
        return True
    try:
        d = sympy.expand(a - b)
    except Exception:
        return None
    if d == 0:
        return True
    try:
        d = sympy.cancel(sympy.together(d))
    except Exception:
        pass
    if d == 0:
        return True
    try:
        ops = int(sympy.count_ops(d, visual=False))
    except Exception:
        return None
    if ops > OPS_CAP:
        return None
    if getattr(d, "is_number", False):
        if d.has(*_NONFINITE) or d.has(sympy.nan):
            return None
        try:
            ez = d.equals(0)
        except Exception:
            ez = None
        if ez is True:
            return True
        if ez is False:
            return False
        return None
    try:
        ez = d.equals(0)
    except Exception:
        return None
    if ez is True:
        return True
    if ez is False:
        return False
    return None


def _normalize_declared(symbols: Any, *exprs: Any) -> list:
    out: list[Any] = []
    seen: set[str] = set()
    for item in list(symbols or []):
        name = item["name"] if isinstance(item, dict) else str(item)
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(item)
    for expr in exprs:
        if isinstance(expr, sympy.Basic):
            for s in expr.free_symbols:
                if isinstance(s, sympy.Symbol) and s.name not in seen:
                    seen.add(s.name)
                    out.append(s.name)
        elif isinstance(expr, str) and expr.isidentifier() and expr not in seen:
            seen.add(expr)
            out.append(expr)
    return out


def _parse(text: str, symbols: list, functions: Optional[list]) -> Optional[sympy.Expr]:
    try:
        expr = parse_expression(text, symbols or [], functions=functions or None)
    except (AdapterError, Exception):
        return None
    if not isinstance(expr, sympy.Expr):
        return None
    return expr


def _coerce(obj: Any, symbols: list, functions: Optional[list]) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, bool):
        return None
    if isinstance(obj, sympy.Expr):
        return obj
    if isinstance(obj, int):
        return sympy.Integer(obj)
    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None
        return _parse(s, symbols, functions)
    try:
        return sympy.sympify(obj)
    except Exception:
        return None


def _coerce_in_context(
    obj: Any,
    context: tuple[Optional[sympy.Expr], ...],
    symbols: list,
    functions: Optional[list],
) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, str) and not obj.strip():
        return None
    cmap = _canon_map(*[e for e in context if e is not None])
    if isinstance(obj, str) and obj in cmap:
        return cmap[obj]
    got = _coerce(obj, symbols, functions)
    if got is None and isinstance(obj, str) and obj.isidentifier():
        extra = list(symbols or []) + [obj]
        got = _coerce(obj, extra, functions)
    if got is None:
        return None
    return _align(got, cmap)


def _canon_map(*exprs: Any) -> dict[str, sympy.Symbol]:
    out: dict[str, sympy.Symbol] = {}
    for expr in exprs:
        if not isinstance(expr, sympy.Basic):
            continue
        for s in expr.free_symbols:
            if isinstance(s, sympy.Symbol):
                out.setdefault(s.name, s)
    return out


def _align(expr: Any, cmap: dict[str, sympy.Symbol]) -> Any:
    if expr is None or not isinstance(expr, sympy.Basic) or not cmap:
        return expr
    mapping = {
        s: cmap[s.name]
        for s in expr.free_symbols
        if isinstance(s, sympy.Symbol) and s.name in cmap and cmap[s.name] != s
    }
    return expr.xreplace(mapping) if mapping else expr


def _bare(
    verdict: str,
    provenance: str,
    steps: list[str],
    *,
    residual: Optional[str] = None,
    witness: Optional[str] = None,
) -> EdgeCertificate:
    return EdgeCertificate(
        verdict=verdict,
        provenance=provenance,
        steps=tuple(steps),
        residual=residual,
        witness=witness,
    )


def _finish(
    cert: EdgeCertificate,
    rel: str,
    source: Any,
    target: Any,
    var: Any,
    point: Any,
) -> EdgeCertificate:
    return _result(
        cert.verdict,
        cert.provenance,
        list(cert.steps),
        rel,
        source,
        target,
        var,
        point,
        residual=cert.residual,
        witness=cert.witness,
    )


def _result(
    verdict: str,
    provenance: str,
    steps: list[str],
    rel: str,
    source: Any,
    target: Any,
    var: Any,
    point: Any,
    residual: Optional[str] = None,
    witness: Optional[str] = None,
) -> EdgeCertificate:
    if verdict == ZERO and provenance in {"timeout", "size_guard", "parse", "UNKNOWN"}:
        verdict = UNKNOWN
    return EdgeCertificate(
        verdict=verdict,
        provenance=provenance,
        steps=tuple(steps),
        relation=rel if rel in EDGE_RELATIONS else rel,
        source="" if source is None else str(source),
        target="" if target is None else str(target),
        variable="" if var is None else str(var),
        target_value="" if point is None else str(point),
        residual=residual,
        witness=witness,
    )
