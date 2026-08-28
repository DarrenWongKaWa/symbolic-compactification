"""Attack FAMILY_ZERO. Do not improve schema or sibling verifiers.

Local exact checks fill step / reconstruction / consistency verdicts.
``schema.compose_path_verdict`` and ``schema.compose_family_verdict``
are the only composition rules. Majority PATH_ZERO and one-path
PATH_ZERO are recorded as traps, never as certificates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sympy

from research.iterated_confluence.schema import (
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_ZERO,
    UNKNOWN,
    IteratedConfluenceCertificate,
    PathCertificate,
    PathConsistencyObligation,
    PathStep,
    compose_family_verdict,
    compose_path_verdict,
)
from research.iterated_confluence.falsifier.cases import (
    ATTACK_CASES,
    CONTROL_CASES,
    load_all_cases,
)
from research.iterated_confluence.falsifier.expr import (
    NONZERO,
    ZERO,
    is_infinity,
    parse_text,
    residual_verdict,
    resolve_point,
    substitute_or_limit,
    symbol_map,
    take_limit,
)


@dataclass
class CaseResult:
    case_id: str
    kind: str
    expect: str
    got: str
    false_family_zero: bool
    path_verdicts: list[str]
    consistency_verdicts: list[str]
    reconstruction_verdicts: list[str]
    required_edge_verdicts: list[str]
    trap_leap: str
    trap_majority: str
    require_path_independence: bool
    extra: dict[str, Any] = field(default_factory=dict)
    certificate: Optional[IteratedConfluenceCertificate] = None

    def row(self) -> dict[str, str]:
        return {"id": self.case_id, "expect": self.expect, "got": self.got}

    @property
    def compose_kwargs(self) -> dict[str, Any]:
        return {
            "path_verdicts": list(self.path_verdicts),
            "consistency_verdicts": list(self.consistency_verdicts),
            "reconstruction_verdicts": list(self.reconstruction_verdicts),
            "required_edge_verdicts": list(self.required_edge_verdicts),
            "require_path_independence": self.require_path_independence,
        }


def forbidden_pairwise_leap(path_verdicts: list[str]) -> str:
    """Forbidden composer: any PATH_ZERO without PATH_NONZERO => FAMILY_ZERO."""
    if any(v == PATH_NONZERO for v in path_verdicts):
        return FAMILY_NONZERO
    if any(v == PATH_ZERO for v in path_verdicts):
        return FAMILY_ZERO
    return FAMILY_UNKNOWN


def forbidden_majority_paths(path_verdicts: list[str]) -> str:
    """Forbidden composer: majority PATH_ZERO => FAMILY_ZERO."""
    if not path_verdicts:
        return FAMILY_UNKNOWN
    n_zero = sum(v == PATH_ZERO for v in path_verdicts)
    if n_zero > len(path_verdicts) / 2:
        return FAMILY_ZERO
    if any(v == PATH_NONZERO for v in path_verdicts):
        return FAMILY_NONZERO
    return FAMILY_UNKNOWN


def _parse_members(
    case: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    symbols = list(case.get("symbols") or [])
    members_text: dict[str, str] = dict(case.get("members") or {})
    members = {mid: parse_text(text, symbols) for mid, text in members_text.items()}
    smap = symbol_map(*[e for e in members.values() if e is not None])
    for spec in symbols:
        name = spec["name"] if isinstance(spec, dict) else str(spec)
        real = True if not isinstance(spec, dict) else spec.get("real", True)
        if name not in smap:
            smap[name] = sympy.Symbol(name, real=bool(real))
    return members, smap


def _limit_claim(
    expr: Any, var: Any, point: Any, claimed: Any
) -> tuple[str, Any, dict[str, Any], str]:
    extra: dict[str, Any] = {}
    if expr is None or var is None or point is None or claimed is None:
        return UNKNOWN, None, extra, "unparseable_limit"
    plus = take_limit(expr, var, point, dir="+")
    minus = take_limit(expr, var, point, dir="-")
    extra["dir_plus"] = None if plus is None else str(plus)
    extra["dir_minus"] = None if minus is None else str(minus)
    dirs_disagree = (
        plus is not None
        and minus is not None
        and residual_verdict(plus, minus)[0] != ZERO
    )
    extra["directional_disagree"] = bool(dirs_disagree)
    if dirs_disagree or is_infinity(plus) or is_infinity(minus):
        return (
            NONZERO,
            plus if plus is not None else minus,
            extra,
            "no_finite_two_sided_limit",
        )
    got, how = substitute_or_limit(expr, var, point)
    extra["limit_how"] = how
    extra["limit"] = None if got is None else str(got)
    if got is None:
        return UNKNOWN, None, extra, "limit_failed"
    if is_infinity(got):
        return NONZERO, got, extra, "infinite_limit"
    verdict, residual = residual_verdict(got, claimed)
    return verdict, residual, extra, "limit_vs_claimed"


def _eval_step(
    step: dict[str, Any],
    members: dict[str, Any],
    smap: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    info: dict[str, Any] = {
        "source": step.get("source"),
        "target": step.get("target"),
        "relation": step.get("relation") or "one_parameter_confluence",
        "variable": step.get("variable") or "",
        "target_value": step.get("target_value") or "",
        "opaque": bool(step.get("opaque")),
        "unknown_reason": str(step.get("unknown_reason") or ""),
    }
    if step.get("opaque") or step.get("unknown_reason"):
        info["verdict"] = UNKNOWN
        info["note"] = str(step.get("unknown_reason") or "opaque")
        return UNKNOWN, info
    src = members.get(str(step.get("source") or ""))
    tgt = members.get(str(step.get("target") or ""))
    relation = str(step.get("relation") or "one_parameter_confluence")
    if relation == "substitution":
        verdict, residual = residual_verdict(src, tgt)
        info["verdict"] = verdict
        info["residual"] = None if residual is None else str(residual)[:300]
        info["note"] = "identical_residual"
        return verdict, info
    var = resolve_point(str(step.get("variable") or ""), smap)
    point = resolve_point(str(step.get("target_value") or ""), smap)
    if var is None and step.get("variable"):
        info["verdict"] = UNKNOWN
        info["note"] = "missing_variable"
        return UNKNOWN, info
    if point is None and str(step.get("target_value") or ""):
        info["verdict"] = UNKNOWN
        info["note"] = "missing_target_value"
        return UNKNOWN, info
    if var is None or point is None:
        verdict, residual = residual_verdict(src, tgt)
        info["verdict"] = verdict
        info["residual"] = None if residual is None else str(residual)[:300]
        info["note"] = "identical_residual_fallback"
        return verdict, info
    verdict, residual, extra, note = _limit_claim(src, var, point, tgt)
    info.update(extra)
    info["verdict"] = verdict
    info["residual"] = None if residual is None else str(residual)[:300]
    info["note"] = note
    return verdict, info


def _apply_step_to_expr(
    expr: Any, step: dict[str, Any], smap: dict[str, Any]
) -> Any:
    if expr is None:
        return None
    if step.get("opaque") or step.get("unknown_reason"):
        return None
    var_name = str(step.get("variable") or "")
    point_name = str(step.get("target_value") or "")
    if not var_name:
        return expr
    var = resolve_point(var_name, smap)
    point = resolve_point(point_name, smap)
    if var is None or point is None:
        return None
    got, _how = substitute_or_limit(expr, var, point)
    return got


def _iterated_value(
    start: Any, steps: list[dict[str, Any]], smap: dict[str, Any]
) -> Any:
    cur = start
    for step in steps:
        cur = _apply_step_to_expr(cur, step, smap)
        if cur is None:
            return None
    return cur


def _path_end_value(
    spec: dict[str, Any],
    members: dict[str, Any],
    smap: dict[str, Any],
) -> Any:
    steps = list(spec.get("steps") or [])
    if any(s.get("opaque") or s.get("unknown_reason") for s in steps):
        return None
    start_id = str(spec.get("start_member") or (steps[0]["source"] if steps else ""))
    start = members.get(start_id)
    if start is None:
        return None
    return _iterated_value(start, steps, smap)


def _consistency_verdict(left: Any, right: Any) -> str:
    if left is None or right is None:
        return CONSISTENCY_UNKNOWN
    if is_infinity(left) or is_infinity(right):
        verdict, _ = residual_verdict(left, right)
        if verdict == ZERO:
            return CONSISTENCY_UNKNOWN
        return INCONSISTENT_NONZERO
    verdict, _ = residual_verdict(left, right)
    if verdict == ZERO:
        return CONSISTENT_ZERO
    if verdict == NONZERO:
        return INCONSISTENT_NONZERO
    return CONSISTENCY_UNKNOWN


def _paths_by_id(case: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(p["path_id"]): p for p in case.get("paths") or []}


def check_case(case: dict[str, Any]) -> CaseResult:
    members, smap = _parse_members(case)
    symbols = list(case.get("symbols") or [])
    require_pi = bool(case.get("require_path_independence", True))
    path_rows: list[dict[str, Any]] = []
    path_certs: list[PathCertificate] = []
    path_verdicts: list[str] = []
    edge_verdicts: list[str] = []
    for spec in case.get("paths") or []:
        step_verdicts: list[str] = []
        step_infos: list[dict[str, Any]] = []
        step_objs: list[PathStep] = []
        for raw in spec.get("steps") or []:
            verdict, info = _eval_step(raw, members, smap)
            step_verdicts.append(verdict)
            edge_verdicts.append(verdict)
            step_infos.append(info)
            step_objs.append(
                PathStep(
                    source=str(raw.get("source") or ""),
                    target=str(raw.get("target") or ""),
                    variable=str(raw.get("variable") or ""),
                    target_value=str(raw.get("target_value") or ""),
                    verdict=verdict,
                    provenance=str(info.get("note") or ""),
                    relation=str(raw.get("relation") or "one_parameter_confluence"),
                )
            )
        path_v = compose_path_verdict(step_verdicts)
        path_verdicts.append(path_v)
        end = _path_end_value(spec, members, smap)
        path_rows.append(
            {
                "path_id": spec.get("path_id"),
                "path_verdict": path_v,
                "step_verdicts": step_verdicts,
                "steps": step_infos,
                "end_value": None if end is None else str(end),
            }
        )
        path_certs.append(
            PathCertificate(
                path_id=str(spec.get("path_id") or ""),
                start_member=str(spec.get("start_member") or ""),
                end_member=str(spec.get("end_member") or ""),
                steps=step_objs,
                path_verdict=path_v,
                provenance=["schema.compose_path_verdict"],
            )
        )

    rec_rows: list[dict[str, Any]] = []
    rec_verdicts: list[str] = []
    rec_obs: list[dict[str, Any]] = []
    for spec in case.get("reconstructions") or []:
        mid = str(spec.get("member_id") or "")
        claimed = members.get(mid)
        true = parse_text(spec.get("reconstructed"), symbols)
        verdict, residual = residual_verdict(claimed, true)
        rec_verdicts.append(verdict)
        rec_rows.append(
            {
                "member_id": mid,
                "verdict": verdict,
                "reconstructed": spec.get("reconstructed"),
                "residual": None if residual is None else str(residual)[:300],
            }
        )
        rec_obs.append({"member_id": mid, "verdict": verdict})

    by_id = _paths_by_id(case)
    cons_rows: list[dict[str, Any]] = []
    cons_verdicts: list[str] = []
    cons_objs: list[PathConsistencyObligation] = []
    for spec in case.get("consistency") or []:
        pa = by_id.get(str(spec.get("path_a") or ""))
        pb = by_id.get(str(spec.get("path_b") or ""))
        left = _path_end_value(pa, members, smap) if pa else None
        right = _path_end_value(pb, members, smap) if pb else None
        verdict = _consistency_verdict(left, right)
        cons_verdicts.append(verdict)
        cons_rows.append(
            {
                "path_a": spec.get("path_a"),
                "path_b": spec.get("path_b"),
                "verdict": verdict,
                "value_a": None if left is None else str(left),
                "value_b": None if right is None else str(right),
            }
        )
        cons_objs.append(
            PathConsistencyObligation(
                path_a=str(spec.get("path_a") or ""),
                path_b=str(spec.get("path_b") or ""),
                start=str(spec.get("start") or ""),
                end=str(spec.get("end") or ""),
                verdict=verdict,
                provenance="iterated_end_values",
            )
        )

    family = compose_family_verdict(
        path_verdicts=path_verdicts,
        consistency_verdicts=cons_verdicts,
        reconstruction_verdicts=rec_verdicts,
        required_edge_verdicts=edge_verdicts,
        require_path_independence=require_pi,
    )
    expect = str(case.get("expect") or FAMILY_UNKNOWN)
    false_zero = family == FAMILY_ZERO and expect != FAMILY_ZERO
    trap_leap = forbidden_pairwise_leap(path_verdicts)
    trap_majority = forbidden_majority_paths(path_verdicts)
    extra = dict(case.get("extra") or {})
    extra.update(
        {
            "paths": path_rows,
            "reconstructions": rec_rows,
            "consistency": cons_rows,
            "trap": case.get("trap"),
        }
    )
    surface = extra.get("surface") if isinstance(extra.get("surface"), dict) else None
    if surface and "A" in members and "B" in members:
        var = resolve_point(str(surface.get("variable") or ""), smap)
        point = resolve_point(str(surface.get("value") or ""), smap)
        if var is not None and point is not None:
            left_s, _ = substitute_or_limit(members["A"], var, point)
            right_s, _ = substitute_or_limit(members["B"], var, point)
            sv, _ = residual_verdict(left_s, right_s)
            extra["surface_restricted_verdict"] = sv
    cert = IteratedConfluenceCertificate(
        family_id=str(case["id"]),
        members=list((case.get("members") or {}).keys()),
        paths=path_certs,
        path_consistency_obligations=cons_objs,
        branch_reconstruction_obligations=rec_obs,
        family_verdict=family,
        provenance=["schema.compose_family_verdict"],
        require_path_independence=require_pi,
    )
    return CaseResult(
        case_id=str(case["id"]),
        kind=str(case.get("kind") or ""),
        expect=expect,
        got=family,
        false_family_zero=false_zero,
        path_verdicts=path_verdicts,
        consistency_verdicts=cons_verdicts,
        reconstruction_verdicts=rec_verdicts,
        required_edge_verdicts=edge_verdicts,
        trap_leap=trap_leap,
        trap_majority=trap_majority,
        require_path_independence=require_pi,
        extra=extra,
        certificate=cert,
    )


def check_all(
    cases: Optional[list[dict[str, Any]]] = None,
) -> list[CaseResult]:
    if cases is None:
        cases = ATTACK_CASES
    return [check_case(c) for c in cases]


def check_controls() -> list[CaseResult]:
    return [check_case(c) for c in CONTROL_CASES]


def false_family_zero_count(results: Optional[list[CaseResult]] = None) -> int:
    if results is None:
        results = check_all(load_all_cases())
    return sum(1 for r in results if r.false_family_zero or (r.got == FAMILY_ZERO and r.expect != FAMILY_ZERO))


def run_cases() -> dict[str, Any]:
    results = [check_case(c) for c in load_all_cases()]
    n_false = sum(1 for r in results if r.got == FAMILY_ZERO and r.expect != FAMILY_ZERO)
    return {
        "n": len(results),
        "n_false_family_zero": n_false,
        "rows": [r.row() for r in results],
    }
