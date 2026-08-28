"""Probe Track-V confluence / dd_cert / factor if they expose a callable API.

Empty packages are not ZERO. Type errors and timeouts are UNKNOWN.
A ZERO on an attack is a false certification.
"""
from __future__ import annotations

import inspect
import types
from typing import Any, Callable, Optional

import sympy

from research.scalable_verification.api import (
    COMPILE_FAILURE,
    NONZERO,
    UNKNOWN,
    ZERO,
)
from research.scalable_verification.falsifier.expr import residual_verdict

ENGINE_MODULES = (
    "confluence",
    "dd_cert",
    "factor",
)

VERDICT_NAMES = frozenset(
    {
        "verify",
        "check",
        "certify",
        "verify_claim",
        "check_claim",
        "evaluate_claim",
        "decide",
        "verdict",
        "verify_limit",
        "check_limit",
        "verify_confluence",
        "check_confluence",
        "certify_limit",
        "verify_newton",
        "certify_newton",
        "verify_hermite",
        "certify_hermite",
        "verify_dd",
        "certify_dd",
        "check_dd",
        "verify_factor",
        "verify_factorization",
        "check_factor",
        "certify_factor",
        "check_kernel",
        "verify_kernel",
    }
)

LIMIT_CTOR_NAMES = frozenset(
    {
        "limit_generic_to_degenerate",
        "take_limit",
        "confluence_limit",
        "limit",
    }
)

NEWTON_CTOR_NAMES = frozenset({"newton_first", "newton_table"})

FACTOR_CTOR_NAMES = frozenset({"factor_local", "factor", "split_kernel"})

# repeated_diagonal / hermite_dd rebuild the claimed RHS from F; that is
# not a verdict on the member. Skip as automatic ZERO sources.


def _load(name: str):
    try:
        return __import__(name, fromlist=["*"])
    except Exception:
        return None


def _callables(mod: Any) -> dict[str, Callable]:
    out: dict[str, Callable] = {}
    for n in dir(mod):
        if n.startswith("_"):
            continue
        obj = getattr(mod, n, None)
        if obj is None or isinstance(obj, (types.ModuleType, type)):
            continue
        if callable(obj):
            out[n] = obj
    return out


def discover_engines() -> dict[str, Any]:
    found: dict[str, Any] = {}
    modules: dict[str, Any] = {}
    for short in ENGINE_MODULES:
        qual = f"research.scalable_verification.{short}"
        mod = _load(qual)
        names = []
        usable = False
        if mod is not None:
            fns = _callables(mod)
            names = sorted(
                n
                for n in fns
                if n in VERDICT_NAMES
                or n in LIMIT_CTOR_NAMES
                or n in NEWTON_CTOR_NAMES
                or n in FACTOR_CTOR_NAMES
            )
            usable = bool(names)
            modules[short] = mod
        found[short] = {
            "importable": mod is not None,
            "usable": usable,
            "module": qual,
            "names": names,
        }
        for sub in ("engine", "limits", "newton", "hermite", "cert", "local", "split"):
            sub_qual = f"{qual}.{sub}"
            sub_mod = _load(sub_qual)
            if sub_mod is None:
                continue
            fns = _callables(sub_mod)
            extra = sorted(
                n
                for n in fns
                if n in VERDICT_NAMES
                or n in LIMIT_CTOR_NAMES
                or n in NEWTON_CTOR_NAMES
                or n in FACTOR_CTOR_NAMES
            )
            if extra:
                found[short]["usable"] = True
                found[short]["names"] = sorted(set(found[short]["names"]) | set(extra))
                modules[f"{short}.{sub}"] = sub_mod
    return {"engines": found, "modules": modules}


def _normalize_verdict(value: Any, *, bool_is_verdict: bool) -> Optional[str]:
    if value is None:
        return UNKNOWN
    if isinstance(value, bool):
        if not bool_is_verdict:
            return None
        return ZERO if value else NONZERO
    if isinstance(value, str):
        u = value.strip().upper()
        if u in {ZERO, NONZERO, UNKNOWN, COMPILE_FAILURE}:
            return u
        return UNKNOWN
    if isinstance(value, dict) and "verdict" in value:
        return _normalize_verdict(value.get("verdict"), bool_is_verdict=bool_is_verdict)
    inner = getattr(value, "verdict", None)
    if inner is not None:
        return _normalize_verdict(inner, bool_is_verdict=bool_is_verdict)
    if isinstance(value, sympy.Expr):
        return None
    return UNKNOWN


def _pool(case: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    math = case.get("math") or {}
    math_kind = math.get("kind")
    # check_limit(F, y, x, G) is lim_{y→x} F = G, not the latent F(z).
    if math_kind == "LIMIT":
        F = parsed.get("expr")
        y = parsed.get("var")
        x = parsed.get("to")
    else:
        F = parsed.get("F")
        y = parsed.get("y")
        x = parsed.get("x")
    return {
        "case": case,
        "claim": case,
        "payload": case,
        "math": math,
        "expr": parsed.get("expr"),
        "generic": parsed.get("expr"),
        "var": parsed.get("var"),
        "point": parsed.get("to"),
        "to": parsed.get("to"),
        "claimed": parsed.get("claimed"),
        "degenerate": parsed.get("claimed"),
        "target": parsed.get("claimed"),
        "G": parsed.get("claimed"),
        "right": parsed.get("claimed") or parsed.get("right"),
        "left": parsed.get("left") or parsed.get("expr") or parsed.get("member"),
        "member": parsed.get("member") or parsed.get("left") or parsed.get("expr"),
        "F": F,
        "z": parsed.get("z"),
        "x": x,
        "y": y,
        "symbols": case.get("symbols"),
        "functions": case.get("functions"),
        "kind": case.get("kind"),
        "nodes": math.get("nodes"),
    }


_CASE_PARAM_NAMES = frozenset({"case", "claim", "payload"})


def _invoke(fn: Callable, case: dict[str, Any], parsed: dict[str, Any]) -> tuple[Any, Optional[str]]:
    pool = _pool(case, parsed)
    strategies: list[tuple[tuple, dict]] = []
    try:
        sig = inspect.signature(fn)
        params = [
            p
            for p in sig.parameters.values()
            if p.name not in {"self", "cls"}
            and p.kind not in {inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD}
        ]
    except (TypeError, ValueError):
        params = None
    if params is not None:
        required = [p for p in params if p.default is inspect.Parameter.empty]
        if len(required) == 1 and required[0].name in _CASE_PARAM_NAMES:
            strategies.append(((case,), {}))
            strategies.append(((), {required[0].name: case}))
        kwargs: dict[str, Any] = {}
        missing = False
        for p in required:
            if p.name in _CASE_PARAM_NAMES:
                kwargs[p.name] = case
                continue
            if p.name in pool and pool[p.name] is not None:
                kwargs[p.name] = pool[p.name]
            else:
                missing = True
                break
        if not missing and kwargs:
            for p in params:
                if p.name in kwargs or p.name not in pool:
                    continue
                if pool[p.name] is not None:
                    kwargs[p.name] = pool[p.name]
            strategies.append(((), dict(kwargs)))
    math_kind = (case.get("math") or {}).get("kind")
    if math_kind == "LIMIT" and parsed.get("expr") is not None:
        strategies.append(
            (
                (parsed["expr"], parsed["var"], parsed["to"], parsed.get("claimed")),
                {},
            )
        )
        strategies.append(((parsed["expr"], parsed["var"], parsed["to"]), {}))
    if math_kind in {"EQUALITY", "FACTOR"} and parsed.get("left") is not None:
        strategies.append(((parsed.get("left"), parsed.get("claimed")), {}))
    if math_kind == "HERMITE_DD" and parsed.get("member") is not None:
        strategies.append(((parsed.get("member"), parsed.get("F")), {}))
        strategies.append(
            (
                (parsed.get("F"), parsed.get("z"), parsed.get("x"), parsed.get("y")),
                {},
            )
        )
    last_type = None
    for args, kwargs in strategies:
        try:
            return fn(*args, **kwargs), None
        except TypeError as exc:
            last_type = str(exc)
            continue
        except Exception as exc:
            return None, type(exc).__name__
    return None, last_type or "signature_mismatch"


def _row(
    *,
    engine: str,
    fn: str,
    verdict: str,
    note: str = "",
    residual: Any = None,
) -> dict[str, Any]:
    return {
        "engine": engine,
        "fn": fn,
        "verdict": verdict,
        "note": note,
        "residual": None if residual is None else str(residual)[:300],
    }


def _compare_expr(got: Any, claimed: Any) -> tuple[str, Any]:
    if got is None:
        return UNKNOWN, None
    if isinstance(got, tuple):
        exprs = [g for g in got if isinstance(g, sympy.Expr)]
        if not exprs:
            return UNKNOWN, None
        prod = exprs[0]
        for g in exprs[1:]:
            prod = prod * g
        got = prod
    if not isinstance(got, sympy.Expr):
        return UNKNOWN, got
    return residual_verdict(got, claimed)


def _probe_one(
    engine: str,
    fname: str,
    fn: Callable,
    case: dict[str, Any],
    parsed: dict[str, Any],
) -> Optional[dict[str, Any]]:
    math_kind = (case.get("math") or {}).get("kind")
    bool_is_verdict = fname in VERDICT_NAMES
    if fname in VERDICT_NAMES:
        got, err = _invoke(fn, case, parsed)
        if err and got is None:
            return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=err)
        verdict = _normalize_verdict(got, bool_is_verdict=bool_is_verdict)
        if verdict is None and isinstance(got, sympy.Expr):
            claimed = parsed.get("claimed")
            if claimed is None:
                return _row(engine=engine, fn=fname, verdict=UNKNOWN, note="expr_without_claimed")
            verdict, residual = residual_verdict(got, claimed)
            return _row(engine=engine, fn=fname, verdict=verdict, residual=residual, note="expr_vs_claimed")
        if verdict is None:
            return _row(engine=engine, fn=fname, verdict=UNKNOWN, note="unnormalized")
        return _row(engine=engine, fn=fname, verdict=verdict, note="verdict_fn")
    if fname in LIMIT_CTOR_NAMES:
        if math_kind != "LIMIT":
            return None
        expr, var, point, claimed = (
            parsed.get("expr"),
            parsed.get("var"),
            parsed.get("to"),
            parsed.get("claimed"),
        )
        if expr is None or var is None or point is None or claimed is None:
            return None
        try:
            got = fn(expr, var, point)
        except TypeError:
            got, err = _invoke(fn, case, parsed)
            if err and got is None:
                return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=err)
        except Exception as exc:
            return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=type(exc).__name__)
        if not isinstance(got, sympy.Expr):
            verdict = _normalize_verdict(got, bool_is_verdict=False)
            return _row(
                engine=engine,
                fn=fname,
                verdict=verdict or UNKNOWN,
                note="limit_ctor_non_expr",
            )
        verdict, residual = residual_verdict(got, claimed)
        return _row(engine=engine, fn=fname, verdict=verdict, residual=residual, note="limit_ctor")
    if fname in NEWTON_CTOR_NAMES:
        if case.get("kind") != "fake_dd_structure":
            return None
        F, z, x, y, claimed = (
            parsed.get("F"),
            parsed.get("z"),
            parsed.get("x"),
            parsed.get("y"),
            parsed.get("claimed"),
        )
        if F is None or z is None or x is None or y is None or claimed is None:
            return None
        try:
            if fname == "newton_table":
                got = fn(F, z, [x, y])
            else:
                got = fn(F, z, x, y)
        except TypeError:
            got, err = _invoke(fn, case, parsed)
            if err and got is None:
                return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=err)
        except Exception as exc:
            return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=type(exc).__name__)
        verdict, residual = _compare_expr(got, claimed)
        return _row(engine=engine, fn=fname, verdict=verdict, residual=residual, note="newton_ctor_vs_claimed")
    if fname in FACTOR_CTOR_NAMES:
        if case.get("kind") != "coefficient_corruption":
            return None
        left, claimed = parsed.get("left"), parsed.get("claimed")
        if left is None or claimed is None:
            return None
        try:
            got = fn(left)
        except TypeError:
            got, err = _invoke(fn, case, parsed)
            if err and got is None:
                return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=err)
        except Exception as exc:
            return _row(engine=engine, fn=fname, verdict=UNKNOWN, note=type(exc).__name__)
        verdict, residual = _compare_expr(got, claimed)
        return _row(engine=engine, fn=fname, verdict=verdict, residual=residual, note="factor_ctor")
    return None


def probe_module(mod: Any, case: dict[str, Any], parsed: dict[str, Any], engine: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fname, fn in _callables(mod).items():
        if (
            fname not in VERDICT_NAMES
            and fname not in LIMIT_CTOR_NAMES
            and fname not in NEWTON_CTOR_NAMES
            and fname not in FACTOR_CTOR_NAMES
        ):
            continue
        row = _probe_one(engine, fname, fn, case, parsed)
        if row is not None:
            rows.append(row)
    return rows


def probe_engines(
    case: dict[str, Any],
    parsed: dict[str, Any],
    extra: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    info = discover_engines()
    modules = dict(info["modules"])
    if extra:
        modules.update(extra)
    rows: list[dict[str, Any]] = []
    seen_fn: set[int] = set()
    for name, mod in modules.items():
        for fname, fn in _callables(mod).items():
            if id(fn) in seen_fn:
                continue
            if (
                fname not in VERDICT_NAMES
                and fname not in LIMIT_CTOR_NAMES
                and fname not in NEWTON_CTOR_NAMES
                and fname not in FACTOR_CTOR_NAMES
            ):
                continue
            row = _probe_one(name, fname, fn, case, parsed)
            if row is not None:
                seen_fn.add(id(fn))
                rows.append(row)
    return rows


def probe_callable(fn: Callable, case: dict[str, Any], parsed: dict[str, Any], *, name: str = "verify_claim") -> dict[str, Any]:
    row = _probe_one("injected", name, fn, case, parsed)
    if row is None:
        return _row(engine="injected", fn=name, verdict=UNKNOWN, note="not_applicable")
    return row
