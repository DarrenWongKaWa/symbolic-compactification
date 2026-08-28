"""One-parameter edge verifier (Track V3-D).

Split spectators first. Size-guard and ``check_limit`` apply to local
kernels, not the unsplit pair. Timeout and size-guard are UNKNOWN, never
ZERO. No Guo identities. No LLM. Numeric agreement is not exact.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.multibranch_verification.edges import OPS_CAP, certify_edge
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.confluence import LIMIT_OPS_CAP, check_limit
from research.scalable_verification.factor import split_multiplicative
from symbolic_compactification.budgets import BudgetExceeded
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import parse_expression

# V2 rescore skipped FULL pairs at 250 before split. Unsplit fallback only.
FULL_OPS_CAP = 250
RELATION = "one_parameter_confluence"
if LIMIT_OPS_CAP <= 0 or FULL_OPS_CAP <= 0 or OPS_CAP <= 0:
    raise RuntimeError("ops caps must be positive; timeout/size-guard is UNKNOWN")

_BLOCKED_ZERO = frozenset({
    "timeout",
    "size_guard",
    "parse",
    "UNKNOWN",
    "sympy.limit:timeout",
    "sympy.limit:skip_count_ops",
})


@dataclass(frozen=True)
class OneParameterCertificate:
    """Verdict of one local one-parameter edge after spectator split."""

    verdict: str
    provenance: str
    full_ops: int
    local_ops: int
    reduction_ratio: float
    steps: tuple[str, ...]
    source: str = ""
    target: str = ""
    variable: str = ""
    target_value: str = ""
    split_certified: bool = False
    residual: Optional[str] = None
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def certify_one_parameter(
    source: Any,
    target: Any,
    variable: Any,
    target_value: Any,
    symbols: Any,
    functions: Any = None,
) -> OneParameterCertificate:
    """Certify ``lim_{variable -> target_value} source = target``.

    Spectator split always runs first (including when full ops > 250).
    ``sympy.limit`` is never called here; ``check_limit`` skips it when
    ``count_ops(F) > LIMIT_OPS_CAP`` (80) and otherwise budgets it.
    """
    steps: list[str] = []
    try:
        return _certify(
            source, target, variable, target_value, symbols, functions, steps,
        )
    except BudgetExceeded:
        steps.append("timeout")
        return _result(
            UNKNOWN, "timeout", 0, 0, 1.0, steps,
            source, target, variable, target_value, False,
        )
    except Exception as exc:
        steps.append(f"error:{type(exc).__name__}")
        return _result(
            UNKNOWN, "UNKNOWN", 0, 0, 1.0, steps,
            source, target, variable, target_value, False,
        )


def _certify(
    source_expr: Any,
    target_expr: Any,
    variable: Any,
    target_value: Any,
    symbols: Any,
    functions: Any,
    steps: list[str],
) -> OneParameterCertificate:
    declared = _normalize_declared(
        symbols, source_expr, target_expr, variable, target_value,
    )
    funcs = list(functions) if functions else None

    source = _coerce(source_expr, declared, funcs)
    target = _coerce(target_expr, declared, funcs)
    if source is None or target is None:
        steps.append("parse:failed")
        return _result(
            UNKNOWN, "parse", 0, 0, 1.0, steps,
            source_expr, target_expr, variable, target_value, False,
        )

    cmap = _canon_map(source, target)
    source = _align(source, cmap)
    target = _align(target, cmap)
    var = _coerce_in_context(variable, (source, target), declared, funcs)
    point = _coerce_in_context(
        target_value, (source, target, var), declared, funcs,
    )
    cmap = _canon_map(source, target, var, point)
    source, target, var, point = (
        _align(source, cmap),
        _align(target, cmap),
        _align(var, cmap) if var is not None else None,
        _align(point, cmap) if point is not None else None,
    )

    full_ops = _pair_ops(source, target)
    work_s, work_t, split_ok = _split_first(source, target, steps)
    local_ops = _pair_ops(work_s, work_t)
    ratio = _reduction_ratio(full_ops, local_ops)

    if not split_ok and _unsplit_too_large(full_ops):
        steps.append("size_guard:unsplit")
        return _result(
            UNKNOWN, "size_guard", full_ops, local_ops, ratio, steps,
            source, target, var, point, False,
        )

    if _ops_too_large_local(work_s, work_t):
        steps.append("size_guard")
        return _result(
            UNKNOWN, "size_guard", full_ops, local_ops, ratio, steps,
            source, target, var, point, split_ok,
        )

    got = _step_special(work_s, work_t, var, point, steps)
    if got is not None:
        return _finish(
            got, full_ops, local_ops, ratio, steps,
            source, target, var, point, split_ok,
        )

    if var is not None and point is not None:
        got = _step_check_limit(work_s, work_t, var, point, steps)
        if got is not None:
            return _finish(
                got, full_ops, local_ops, ratio, steps,
                source, target, var, point, split_ok,
            )

    got = _step_certify_edge(
        work_s, work_t, var, point, declared, funcs, steps,
    )
    if got is not None:
        return _finish(
            got, full_ops, local_ops, ratio, steps,
            source, target, var, point, split_ok,
        )

    steps.append("UNKNOWN")
    return _result(
        UNKNOWN, "UNKNOWN", full_ops, local_ops, ratio, steps,
        source, target, var, point, split_ok,
    )


def _split_first(
    source: sympy.Expr,
    target: sympy.Expr,
    steps: list[str],
) -> tuple[sympy.Expr, sympy.Expr, bool]:
    """Always attempt spectator split, including when full ops > 250."""
    payload, name = _split_pair(source, target)
    if payload is None:
        steps.append("split:unavailable")
        return source, target, False
    certified = bool(payload.get("certified"))
    note = str(payload.get("note") or "")
    if not certified:
        steps.append(f"{name}:uncertified:{note}")
        return source, target, False
    a_loc = payload.get("A_local")
    b_loc = payload.get("B_local")
    if not isinstance(a_loc, sympy.Expr) or not isinstance(b_loc, sympy.Expr):
        steps.append(f"{name}:bad_payload")
        return source, target, False
    steps.append(f"{name}:certified:{note}")
    return a_loc, b_loc, True


def _split_pair(source: sympy.Expr, target: sympy.Expr) -> tuple[Optional[dict], str]:
    splitter = _load_split_edge()
    if splitter is not None:
        try:
            raw = splitter(source, target)
            payload = _as_split_payload(raw)
            if payload is not None:
                return payload, "split_edge"
        except Exception:
            pass
    try:
        out = split_multiplicative(source, target)
    except Exception as exc:
        return (
            {
                "S": sympy.Integer(1),
                "A_local": source,
                "B_local": target,
                "certified": False,
                "note": type(exc).__name__,
            },
            "split_multiplicative",
        )
    return out, "split_multiplicative"


def _load_split_edge() -> Any:
    try:
        from research.iterated_confluence.spectator import split_edge
    except ImportError:
        return None
    return split_edge


def _as_split_payload(out: Any) -> Optional[dict]:
    if out is None:
        return None
    if isinstance(out, dict):
        get = out.get
    else:
        def get(key: str, default: Any = None) -> Any:
            return getattr(out, key, default)

    a_loc = get("A_local", get("source_local", get("local_source")))
    b_loc = get("B_local", get("target_local", get("local_target")))
    if not isinstance(a_loc, sympy.Expr) or not isinstance(b_loc, sympy.Expr):
        return None
    S = get("S", get("spectator"))
    return {
        "S": S,
        "A_local": a_loc,
        "B_local": b_loc,
        "certified": bool(get("certified", False)),
        "note": str(get("note", get("provenance", "")) or ""),
    }


def _step_special(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    steps: list[str],
) -> Optional[tuple[str, str, Optional[str], Optional[str]]]:
    if not (_has_special(source) or _has_special(target)):
        return None
    try:
        from research.multibranch_verification.special import prove_local
    except ImportError:
        steps.append("prove_local:unavailable")
        return None
    try:
        proof = prove_local(
            source,
            target,
            relation=RELATION,
            variable=var,
            target=point,
        )
    except Exception as exc:
        steps.append(f"prove_local:{type(exc).__name__}")
        return None
    for s in getattr(proof, "steps", ()) or ():
        steps.append(f"prove_local:{s}")
    verdict = getattr(proof, "verdict", UNKNOWN)
    provenance = f"prove_local:{getattr(proof, 'provenance', '') or 'prove_local'}"
    if verdict == ZERO:
        steps.append("prove_local:ZERO")
        return ZERO, provenance, "0", getattr(proof, "witness", None)
    if verdict == NONZERO:
        steps.append("prove_local:NONZERO")
        return NONZERO, provenance, None, getattr(proof, "witness", None)
    steps.append("prove_local:undecided")
    return None


def _step_check_limit(
    source: sympy.Expr,
    target: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
    steps: list[str],
) -> Optional[tuple[str, str, Optional[str], Optional[str]]]:
    try:
        r = check_limit(source, var, point, target)
    except BudgetExceeded:
        steps.append("check_limit:timeout")
        return UNKNOWN, "timeout", None, None
    except Exception as exc:
        steps.append(f"check_limit:{type(exc).__name__}")
        return None
    inner = r.provenance or "check_limit"
    for s in r.steps:
        steps.append(f"check_limit:{s}")
    if r.verdict == ZERO:
        steps.append("check_limit:ZERO")
        return ZERO, f"check_limit:{inner}", "0", r.witness
    if r.verdict == NONZERO:
        steps.append("check_limit:NONZERO")
        return NONZERO, f"check_limit:{inner}", None, r.witness
    steps.append(f"check_limit:{inner}")
    if "timeout" in inner:
        return UNKNOWN, "timeout", None, None
    return None


def _step_certify_edge(
    source: sympy.Expr,
    target: sympy.Expr,
    var: Optional[sympy.Expr],
    point: Optional[sympy.Expr],
    symbols: list,
    functions: Optional[list],
    steps: list[str],
) -> Optional[tuple[str, str, Optional[str], Optional[str]]]:
    try:
        cert = certify_edge(
            source, target, RELATION, var, point, symbols, functions,
        )
    except BudgetExceeded:
        steps.append("certify_edge:timeout")
        return UNKNOWN, "timeout", None, None
    except Exception as exc:
        steps.append(f"certify_edge:{type(exc).__name__}")
        return None
    for s in cert.steps:
        steps.append(f"certify_edge:{s}")
    if cert.verdict == ZERO:
        steps.append("certify_edge:ZERO")
        return ZERO, f"certify_edge:{cert.provenance}", cert.residual, cert.witness
    if cert.verdict == NONZERO:
        steps.append("certify_edge:NONZERO")
        return NONZERO, f"certify_edge:{cert.provenance}", cert.residual, cert.witness
    steps.append(f"certify_edge:{cert.provenance}")
    if "timeout" in (cert.provenance or ""):
        return UNKNOWN, "timeout", None, None
    if _is_size_unknown(cert.provenance or ""):
        return UNKNOWN, "size_guard", None, None
    return None


def _has_special(expr: sympy.Expr) -> bool:
    try:
        from research.scalable_verification.special.classify import _has_special_fn
    except ImportError:
        return bool(expr.has(sympy.polygamma, sympy.gamma, sympy.loggamma))
    try:
        return bool(_has_special_fn(expr))
    except Exception:
        return False


def _count_ops(expr: Any) -> int:
    if expr is None or not isinstance(expr, sympy.Basic):
        return 0
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return OPS_CAP + 1


def _pair_ops(a: Any, b: Any) -> int:
    return max(_count_ops(a), _count_ops(b))


def _reduction_ratio(full_ops: int, local_ops: int) -> float:
    if full_ops <= 0:
        return 1.0
    return float(local_ops) / float(full_ops)


def _unsplit_too_large(full_ops: int) -> bool:
    return int(full_ops) > FULL_OPS_CAP


def _ops_too_large_local(*exprs: Any) -> bool:
    for expr in exprs:
        if expr is None or not isinstance(expr, sympy.Basic):
            continue
        if _count_ops(expr) > OPS_CAP:
            return True
    return False


def _is_size_unknown(provenance: str) -> bool:
    p = provenance or ""
    return "size_guard" in p or "skip_count_ops" in p


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


def _sanitize(verdict: str, provenance: str) -> str:
    if verdict != ZERO:
        return verdict
    p = provenance or ""
    if p in _BLOCKED_ZERO or "timeout" in p or _is_size_unknown(p):
        return UNKNOWN
    return ZERO


def _finish(
    got: tuple[str, str, Optional[str], Optional[str]],
    full_ops: int,
    local_ops: int,
    ratio: float,
    steps: list[str],
    source: Any,
    target: Any,
    var: Any,
    point: Any,
    split_ok: bool,
) -> OneParameterCertificate:
    verdict, provenance, residual, witness = got
    return _result(
        verdict, provenance, full_ops, local_ops, ratio, steps,
        source, target, var, point, split_ok,
        residual=residual, witness=witness,
    )


def _result(
    verdict: str,
    provenance: str,
    full_ops: int,
    local_ops: int,
    ratio: float,
    steps: list[str],
    source: Any,
    target: Any,
    var: Any,
    point: Any,
    split_ok: bool,
    residual: Optional[str] = None,
    witness: Optional[str] = None,
) -> OneParameterCertificate:
    verdict = _sanitize(verdict, provenance)
    return OneParameterCertificate(
        verdict=verdict,
        provenance=provenance,
        full_ops=int(full_ops),
        local_ops=int(local_ops),
        reduction_ratio=float(ratio),
        steps=tuple(steps),
        source="" if source is None else str(source),
        target="" if target is None else str(target),
        variable="" if var is None else str(var),
        target_value="" if point is None else str(point),
        split_certified=bool(split_ok),
        residual=residual,
        witness=witness,
    )
