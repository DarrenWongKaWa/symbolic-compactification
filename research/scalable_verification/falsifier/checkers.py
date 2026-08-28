"""Local residual audits plus engine probes. Attack only; do not fix engines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sympy

from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.falsifier.cases import (
    ATTACK_CASES,
    CONTROL_CASES,
)
from research.scalable_verification.falsifier.engines import probe_engines
from research.scalable_verification.falsifier.expr import (
    eval_probe,
    is_infinity,
    parse_math,
    probe_nonzero,
    residual_verdict,
    take_limit,
)

_DIR_PLUS = "+"
_DIR_MINUS = "-"


@dataclass
class AttackResult:
    case_id: str
    verdict: str
    kind: str
    should_be_zero: bool
    false_zero: bool
    note: str = ""
    residual: Optional[str] = None
    local_verdict: Optional[str] = None
    engine_verdicts: list[dict[str, Any]] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)
    backend: str = "local_sympy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "verdict": self.verdict,
            "kind": self.kind,
            "should_be_zero": self.should_be_zero,
            "false_zero": self.false_zero,
            "note": self.note,
            "residual": self.residual,
            "local_verdict": self.local_verdict,
            "engine_verdicts": list(self.engine_verdicts),
            "extra": dict(self.extra),
            "backend": self.backend,
        }


def _result(
    case: dict[str, Any],
    *,
    local_verdict: str,
    note: str,
    residual: Any = None,
    extra: Optional[dict[str, Any]] = None,
    engine_rows: Optional[list[dict[str, Any]]] = None,
) -> AttackResult:
    should = bool(case.get("should_be_zero") is True)
    engine_rows = list(engine_rows or [])
    engine_zeros = [r for r in engine_rows if r.get("verdict") == ZERO]
    engine_nonzero = [r for r in engine_rows if r.get("verdict") == NONZERO]
    if should:
        verdict = local_verdict
        false_zero = False
        backend = "local_sympy"
    elif local_verdict == ZERO or engine_zeros:
        verdict = ZERO
        false_zero = True
        backend = engine_zeros[0]["engine"] if engine_zeros and local_verdict != ZERO else "local_sympy"
    elif local_verdict == NONZERO or engine_nonzero:
        verdict = NONZERO
        false_zero = False
        backend = "local_sympy" if local_verdict == NONZERO else engine_nonzero[0]["engine"]
    else:
        verdict = local_verdict
        false_zero = False
        backend = "local_sympy"
    return AttackResult(
        case_id=str(case["id"]),
        verdict=verdict,
        kind=str(case.get("kind") or ""),
        should_be_zero=should,
        false_zero=false_zero,
        note=note,
        residual=None if residual is None else str(residual)[:500],
        local_verdict=local_verdict,
        engine_verdicts=engine_rows,
        extra=extra or {},
        backend=backend,
    )


def _apply_probes(verdict: str, residual: Any, parsed: dict[str, Any]) -> tuple[str, Any]:
    if verdict in {ZERO, NONZERO}:
        return verdict, residual
    hit, val = probe_nonzero(residual, parsed.get("probes") or [], parsed.get("smap") or {})
    if hit == NONZERO:
        return NONZERO, val
    return verdict, residual


def _limit_claim(case: dict[str, Any], parsed: dict[str, Any]) -> tuple[str, Any, dict[str, Any], str]:
    math = parsed["math"]
    expr = parsed.get("expr")
    claimed = parsed.get("claimed")
    var = parsed.get("var")
    point = parsed.get("to")
    extra: dict[str, Any] = {}
    if expr is None or claimed is None or var is None or point is None:
        return UNKNOWN, None, extra, "unparseable_limit"
    two = take_limit(expr, var, point)
    plus = take_limit(expr, var, point, dir=_DIR_PLUS)
    minus = take_limit(expr, var, point, dir=_DIR_MINUS)
    extra.update(
        {
            "two_sided": None if two is None else str(two),
            "dir_plus": None if plus is None else str(plus),
            "dir_minus": None if minus is None else str(minus),
            "claimed": str(claimed),
        }
    )
    dirs_disagree = plus is not None and minus is not None and plus != minus
    extra["directional_disagree"] = bool(dirs_disagree)
    if math.get("substitute_diagonal"):
        smap = parsed.get("smap") or {}
        x, y = smap.get("x"), smap.get("y")
        if x is not None and y is not None:
            diag = eval_probe(expr, {y: x})
            extra["diagonal"] = None if diag is None else str(diag)
            if diag is not None:
                dv, dr = residual_verdict(diag, claimed)
                extra["diagonal_verdict"] = dv
                if dv != ZERO:
                    if dv == UNKNOWN and diag != claimed:
                        dv, dr = NONZERO, diag - claimed
                    if dv != ZERO:
                        return NONZERO, dr, extra, "diagonal_neq_claimed_sketch"
    sketch_var = math.get("sketch_var")
    if sketch_var:
        svar = (parsed.get("smap") or {}).get(str(sketch_var))
        if svar is not None:
            sketch_to = math.get("sketch_to")
            try:
                point = sympy.Integer(sketch_to)
            except Exception:
                point = sympy.Integer(0)
            sketch = take_limit(expr, svar, point)
            extra["generic_sketch"] = None if sketch is None else str(sketch)
    if math.get("check_directional") and (
        dirs_disagree or is_infinity(two) or is_infinity(plus) or is_infinity(minus)
    ):
        return NONZERO, two, extra, "no_finite_two_sided_limit"
    if two is None:
        return UNKNOWN, None, extra, "limit_failed"
    if is_infinity(two):
        return NONZERO, two, extra, "infinite_limit"
    verdict, residual = residual_verdict(two, claimed)
    verdict, residual = _apply_probes(verdict, residual if residual is not None else (two - claimed), parsed)
    if verdict == ZERO:
        return ZERO, residual, extra, "limit_matched_claimed"
    if verdict == UNKNOWN:
        try:
            if sympy.expand(two - claimed) != 0:
                verdict, residual = NONZERO, two - claimed
        except Exception:
            pass
    return verdict, residual, extra, "limit_vs_claimed"


def _equality_claim(case: dict[str, Any], parsed: dict[str, Any]) -> tuple[str, Any, dict[str, Any], str]:
    math = parsed["math"]
    left = parsed.get("left") or parsed.get("expr") or parsed.get("member")
    right = parsed.get("claimed") or parsed.get("right")
    extra = {
        "left": None if left is None else str(left),
        "claimed": None if right is None else str(right),
    }
    if left is None or right is None:
        return UNKNOWN, None, extra, "unparseable_equality"
    if math.get("use_expand_func"):
        try:
            expanded = sympy.expand_func(left - right)
            extra["expand_func"] = str(expanded)
            if expanded == 0:
                return ZERO, expanded, extra, "expand_func_identity"
            if expanded != 0:
                return NONZERO, expanded, extra, "expand_func_nonzero"
        except Exception as exc:
            extra["expand_func_error"] = type(exc).__name__
    verdict, residual = residual_verdict(left, right)
    verdict, residual = _apply_probes(
        verdict, residual if residual is not None else (left - right), parsed
    )
    if verdict == UNKNOWN:
        try:
            if sympy.expand(left - right) != 0:
                verdict, residual = NONZERO, left - right
        except Exception:
            pass
    return verdict, residual, extra, "equality_vs_claimed"


def _fake_dd(case: dict[str, Any], parsed: dict[str, Any]) -> tuple[str, Any, dict[str, Any], str]:
    member = parsed.get("member")
    claimed = parsed.get("claimed")
    F = parsed.get("F")
    z = parsed.get("z")
    x = parsed.get("x")
    y = parsed.get("y")
    extra: dict[str, Any] = {}
    if member is None or claimed is None:
        return UNKNOWN, None, extra, "unparseable_dd"
    if F is not None and z is not None and x is not None and y is not None:
        true_newton = (F.xreplace({z: x}) - F.xreplace({z: y})) / (x - y)
        true_rep = sympy.diff(F, z).xreplace({z: x})
        extra["true_newton"] = str(true_newton)
        extra["true_repeated"] = str(true_rep)
        v_true, _ = residual_verdict(member, true_newton)
        extra["member_equals_true_newton"] = v_true
    verdict, residual = residual_verdict(member, claimed)
    verdict, residual = _apply_probes(
        verdict, residual if residual is not None else (member - claimed), parsed
    )
    if verdict == UNKNOWN:
        try:
            if sympy.expand(member - claimed) != 0:
                verdict, residual = NONZERO, member - claimed
        except Exception:
            pass
    extra["member"] = str(member)
    extra["claimed"] = str(claimed)
    return verdict, residual, extra, "member_vs_repeated_node"


def _local_kind(case: dict[str, Any], parsed: dict[str, Any]) -> tuple[str, Any, dict[str, Any], str]:
    math_kind = (parsed.get("math") or {}).get("kind")
    kind = case.get("kind")
    if kind == "fake_dd_structure" or math_kind == "HERMITE_DD":
        return _fake_dd(case, parsed)
    if math_kind == "LIMIT":
        return _limit_claim(case, parsed)
    return _equality_claim(case, parsed)


def local_check(case: dict[str, Any]) -> tuple[str, Any, dict[str, Any], str, dict[str, Any]]:
    parsed = parse_math(case)
    verdict, residual, extra, note = _local_kind(case, parsed)
    return verdict, residual, extra, note, parsed


def check_attack(
    case: dict[str, Any],
    *,
    extra_engines: Optional[dict[str, Any]] = None,
) -> AttackResult:
    local_verdict, residual, extra, note, parsed = local_check(case)
    engine_rows = probe_engines(case, parsed, extra=extra_engines)
    extra = dict(extra)
    extra["n_engine_rows"] = len(engine_rows)
    extra["engine_zero_fns"] = [
        f"{r.get('engine')}.{r.get('fn')}" for r in engine_rows if r.get("verdict") == ZERO
    ]
    return _result(
        case,
        local_verdict=local_verdict,
        note=note,
        residual=residual,
        extra=extra,
        engine_rows=engine_rows,
    )


def check_all(
    cases: Optional[list[dict[str, Any]]] = None,
    *,
    extra_engines: Optional[dict[str, Any]] = None,
) -> list[AttackResult]:
    if cases is None:
        cases = ATTACK_CASES
    return [check_attack(c, extra_engines=extra_engines) for c in cases]


def check_controls() -> list[AttackResult]:
    return [check_attack(c) for c in CONTROL_CASES]


def false_zero_count(results: Optional[list[AttackResult]] = None) -> int:
    if results is None:
        results = check_all()
    return sum(1 for r in results if r.false_zero or (r.verdict == ZERO and not r.should_be_zero))


def report() -> dict[str, Any]:
    from research.scalable_verification.falsifier.engines import discover_engines

    results = check_all()
    controls = check_controls()
    info = discover_engines()
    return {
        "n": len(results),
        "n_false_zero": false_zero_count(results),
        "false_zero_ids": [r.case_id for r in results if r.false_zero],
        "engines": {k: {kk: vv for kk, vv in rec.items() if kk != "module"} for k, rec in info["engines"].items()},
        "usable_engines": [k for k, rec in info["engines"].items() if rec.get("usable")],
        "control_verdicts": {r.case_id: r.verdict for r in controls},
        "rows": [r.to_dict() for r in results],
    }
