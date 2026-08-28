"""Attack FAMILY_ZERO. Do not improve the composer or sibling verifiers.

Local exact checks fill edge / recurrence / path verdicts, then
``compose_family_verdict`` is the only family rule. Majority of Hermite
branches is recorded as a trap, never as a certificate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import sympy

from research.multibranch_verification.schema import (
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    ConfluentFamilyCertificate,
    LocalEdge,
    compose_family_verdict,
)
from research.multibranch_verification.falsifier.cases import (
    ATTACK_CASES,
    CONTROL_CASES,
)
from research.multibranch_verification.falsifier.expr import (
    NONZERO,
    UNKNOWN,
    ZERO,
    is_infinity,
    parse_text,
    residual_verdict,
    substitute_or_limit,
    symbol_map,
    take_limit,
)
from research.representation_invention.dd import (
    hermite_dd,
    newton_first,
    repeated_diagonal,
)

_KIND_MULT = {
    "newton_first": {"x": 1, "y": 1},
    "repeated_diagonal": {"x": 2},
    "hermite_xxy": {"x": 2, "y": 1},
    "hermite_xyy": {"x": 1, "y": 2},
    "hermite_xxx": {"x": 3},
}


@dataclass
class FamilyResult:
    case_id: str
    kind: str
    should_be_zero: bool
    family_verdict: str
    false_zero: bool
    majority_verdict: str
    required_edge_verdicts: list[str]
    recurrence_verdicts: list[str]
    path_verdicts: list[str]
    reconstruction_verdicts: list[str]
    connected: bool
    multiplicities_consistent: bool
    latent_compatible: bool
    note: str = ""
    extra: dict[str, Any] = field(default_factory=dict)
    certificate: Optional[ConfluentFamilyCertificate] = None

    def to_dict(self) -> dict[str, Any]:
        cert = None
        if self.certificate is not None:
            cert = self.certificate.to_dict()
        return {
            "case_id": self.case_id,
            "kind": self.kind,
            "should_be_zero": self.should_be_zero,
            "family_verdict": self.family_verdict,
            "false_zero": self.false_zero,
            "majority_verdict": self.majority_verdict,
            "required_edge_verdicts": list(self.required_edge_verdicts),
            "recurrence_verdicts": list(self.recurrence_verdicts),
            "path_verdicts": list(self.path_verdicts),
            "reconstruction_verdicts": list(self.reconstruction_verdicts),
            "connected": self.connected,
            "multiplicities_consistent": self.multiplicities_consistent,
            "latent_compatible": self.latent_compatible,
            "note": self.note,
            "extra": dict(self.extra),
            "certificate": cert,
        }

    @property
    def compose_kwargs(self) -> dict[str, Any]:
        return {
            "required_edge_verdicts": list(self.required_edge_verdicts),
            "recurrence_verdicts": list(self.recurrence_verdicts),
            "path_verdicts": list(self.path_verdicts),
            "connected": self.connected,
            "multiplicities_consistent": self.multiplicities_consistent,
            "latent_compatible": self.latent_compatible,
        }


def majority_branch_vote(verdicts: list[str]) -> str:
    """Forbidden composer: FAMILY_ZERO if a majority of branches are ZERO."""
    if not verdicts:
        return FAMILY_UNKNOWN
    n_zero = sum(v == ZERO for v in verdicts)
    if n_zero > len(verdicts) / 2:
        return FAMILY_ZERO
    if any(v == NONZERO for v in verdicts):
        return FAMILY_NONZERO
    return FAMILY_UNKNOWN


def _parse_family(
    case: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, sympy.Symbol], dict[str, str]]:
    symbols = list(case.get("symbols") or [])
    members_text: dict[str, str] = dict(case.get("members") or {})
    members = {mid: parse_text(text, symbols) for mid, text in members_text.items()}
    latent_map = dict(case.get("latent_F_by_member") or {})
    default_F = case.get("latent_F")
    F_text: dict[str, str] = {}
    F_by: dict[str, Any] = {}
    for mid in members_text:
        text = latent_map.get(mid, default_F)
        F_text[mid] = "" if text is None else str(text)
        F_by[mid] = parse_text(text, symbols) if text else None
    smap = symbol_map(*[e for e in members.values() if e is not None], *[e for e in F_by.values() if e is not None])
    for spec in symbols:
        name = spec["name"] if isinstance(spec, dict) else str(spec)
        real = True if not isinstance(spec, dict) else spec.get("real", True)
        if name not in smap:
            smap[name] = sympy.Symbol(name, real=bool(real))
    return members, F_by, smap, F_text


def _recon_expr(kind: str, F: Any, smap: dict[str, sympy.Symbol]):
    t, x, y = smap["t"], smap["x"], smap["y"]
    if F is None:
        return None
    if kind == "newton_first":
        return newton_first(F, t, x, y)
    if kind == "repeated_diagonal":
        return repeated_diagonal(F, t, x)
    if kind == "repeated_yy":
        return repeated_diagonal(F, t, y)
    if kind == "hermite_xxy":
        return hermite_dd(F, t, [(x, 2), (y, 1)])
    if kind == "hermite_xyy":
        return hermite_dd(F, t, [(x, 1), (y, 2)])
    if kind == "hermite_xxx":
        return hermite_dd(F, t, [(x, 3)])
    return None


def _row(
    *,
    source: str,
    target: str,
    relation: str,
    verdict: str,
    residual: Any = None,
    note: str = "",
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    return {
        "source": source,
        "target": target,
        "relation": relation,
        "verdict": verdict,
        "residual": None if residual is None else str(residual)[:300],
        "note": note,
        "extra": dict(extra or {}),
    }


def _check_reconstructions(
    case: dict[str, Any],
    members: dict[str, Any],
    F_by: dict[str, Any],
    smap: dict[str, sympy.Symbol],
) -> list[dict[str, Any]]:
    rows = []
    for spec in case.get("reconstructions") or []:
        mid = spec["member_id"]
        kind = spec["kind"]
        member = members.get(mid)
        F = F_by.get(mid)
        true = _recon_expr(kind, F, smap)
        if member is None or true is None:
            rows.append(
                _row(
                    source=mid,
                    target=kind,
                    relation="substitution",
                    verdict=UNKNOWN,
                    note="unparseable_reconstruction",
                )
            )
            continue
        verdict, residual = residual_verdict(member, true)
        rows.append(
            _row(
                source=mid,
                target=kind,
                relation="substitution",
                verdict=verdict,
                residual=residual,
                note="member_vs_true_dd",
                extra={"kind": kind, "true": str(true), "member": str(member)},
            )
        )
    return rows


def _limit_claim(expr: Any, var: Any, point: Any, claimed: Any) -> tuple[str, Any, dict[str, Any], str]:
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
        return NONZERO, plus if plus is not None else minus, extra, "no_finite_two_sided_limit"
    got, how = substitute_or_limit(expr, var, point)
    extra["limit_how"] = how
    extra["limit"] = None if got is None else str(got)
    if got is None:
        return UNKNOWN, None, extra, "limit_failed"
    if is_infinity(got):
        return NONZERO, got, extra, "infinite_limit"
    verdict, residual = residual_verdict(got, claimed)
    return verdict, residual, extra, "limit_vs_claimed"


def _check_confluence(
    case: dict[str, Any],
    members: dict[str, Any],
    smap: dict[str, sympy.Symbol],
) -> list[dict[str, Any]]:
    rows = []
    for spec in case.get("confluence") or []:
        src = spec["source"]
        tgt = spec["target"]
        var = smap.get(str(spec.get("variable") or ""))
        point = smap.get(str(spec.get("target_value") or ""))
        expr = members.get(src)
        claimed = members.get(tgt)
        relation = str(spec.get("relation") or "one_parameter_confluence")
        verdict, residual, extra, note = _limit_claim(expr, var, point, claimed)
        extra.update({"variable": spec.get("variable"), "target_value": spec.get("target_value")})
        rows.append(
            _row(
                source=src,
                target=tgt,
                relation=relation,
                verdict=verdict,
                residual=residual,
                note=note,
                extra=extra,
            )
        )
    return rows


def _resolve(
    name: str,
    spec: dict[str, Any],
    members: dict[str, Any],
    F_by: dict[str, Any],
    smap: dict[str, sympy.Symbol],
    role: str,
):
    if name in members:
        return members[name]
    if role == "left" and spec.get("left_from") == "repeated_yy":
        F = F_by.get(spec.get("target")) or F_by.get(spec.get("right"))
        return _recon_expr("repeated_yy", F, smap)
    return None


def _check_recurrences(
    case: dict[str, Any],
    members: dict[str, Any],
    F_by: dict[str, Any],
    smap: dict[str, sympy.Symbol],
) -> list[dict[str, Any]]:
    rows = []
    for spec in case.get("recurrences") or []:
        left = _resolve(str(spec["left"]), spec, members, F_by, smap, "left")
        right = _resolve(str(spec["right"]), spec, members, F_by, smap, "right")
        target = _resolve(str(spec["target"]), spec, members, F_by, smap, "target")
        denom = spec.get("denom") or ["x", "y"]
        d0 = smap.get(str(denom[0]))
        d1 = smap.get(str(denom[1]))
        if left is None or right is None or target is None or d0 is None or d1 is None:
            rows.append(
                _row(
                    source=str(spec.get("left")),
                    target=str(spec.get("target")),
                    relation="hermite_dd_recurrence",
                    verdict=UNKNOWN,
                    note="unparseable_recurrence",
                )
            )
            continue
        recon = (left - right) / (d0 - d1)
        verdict, residual = residual_verdict(recon, target)
        rows.append(
            _row(
                source=f"{spec['left']}-{spec['right']}",
                target=str(spec["target"]),
                relation="hermite_dd_recurrence",
                verdict=verdict,
                residual=residual,
                note="recurrence_vs_target",
                extra={"denom": list(denom), "recon": str(recon)},
            )
        )
    return rows


def _check_paths(
    case: dict[str, Any],
    members: dict[str, Any],
    smap: dict[str, sympy.Symbol],
) -> list[dict[str, Any]]:
    rows = []
    for spec in case.get("paths") or []:
        src = spec["source"]
        tgt = spec["target"]
        var = smap.get(str(spec.get("variable") or ""))
        point = smap.get(str(spec.get("target_value") or ""))
        verdict, residual, extra, note = _limit_claim(
            members.get(src), var, point, members.get(tgt)
        )
        extra["path_id"] = spec.get("id")
        rows.append(
            _row(
                source=src,
                target=tgt,
                relation="repeated_node_confluence",
                verdict=verdict,
                residual=residual,
                note=note,
                extra=extra,
            )
        )
    if len(rows) >= 2:
        a_src = case["paths"][0]["source"]
        b_src = case["paths"][1]["source"]
        a_tgt = case["paths"][0]["target"]
        b_tgt = case["paths"][1]["target"]
        var = smap.get(str(case["paths"][0].get("variable") or "y"))
        point = smap.get(str(case["paths"][0].get("target_value") or "x"))
        if a_tgt == b_tgt:
            la, _ = substitute_or_limit(members.get(a_src), var, point)
            lb, _ = substitute_or_limit(members.get(b_src), var, point)
            verdict, residual = residual_verdict(la, lb)
            rows.append(
                _row(
                    source=a_src,
                    target=b_src,
                    relation="dd_recurrence",
                    verdict=verdict,
                    residual=residual,
                    note="path_values_agree",
                )
            )
    return rows


def _connected(member_ids: list[str], edges: list[list[str]]) -> bool:
    if not member_ids:
        return False
    adj: dict[str, set[str]] = {m: set() for m in member_ids}
    for edge in edges or []:
        if len(edge) != 2:
            continue
        a, b = str(edge[0]), str(edge[1])
        if a in adj and b in adj:
            adj[a].add(b)
            adj[b].add(a)
    start = member_ids[0]
    seen = {start}
    stack = [start]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen == set(member_ids)


def _multiplicities_consistent(case: dict[str, Any]) -> bool:
    declared = case.get("node_multiplicities") or {}
    for spec in case.get("reconstructions") or []:
        expect = _KIND_MULT.get(spec.get("kind") or "")
        if expect is None:
            continue
        got = declared.get(spec["member_id"]) or {}
        try:
            got_i = {str(k): int(v) for k, v in got.items()}
        except (TypeError, ValueError):
            return False
        if got_i != expect:
            return False
        if any(v < 1 for v in got_i.values()):
            return False
    return True


def _latent_compatible(F_text: dict[str, str]) -> bool:
    texts = {v for v in F_text.values() if v}
    return len(texts) <= 1


def _edges_to_local(rows: list[dict[str, Any]]) -> list[LocalEdge]:
    out = []
    for r in rows:
        out.append(
            LocalEdge(
                source=str(r["source"]),
                target=str(r["target"]),
                relation=str(r["relation"]),
                variable=str((r.get("extra") or {}).get("variable") or ""),
                target_value=str((r.get("extra") or {}).get("target_value") or ""),
                verdict=str(r["verdict"]),
                provenance=str(r.get("note") or ""),
            )
        )
    return out


def check_family(case: dict[str, Any]) -> FamilyResult:
    members, F_by, smap, F_text = _parse_family(case)
    recon = _check_reconstructions(case, members, F_by, smap)
    conf = _check_confluence(case, members, smap)
    rec = _check_recurrences(case, members, F_by, smap)
    paths = _check_paths(case, members, smap)
    member_ids = list((case.get("members") or {}).keys())
    connected = _connected(member_ids, list(case.get("graph_edges") or []))
    multiplicities_consistent = _multiplicities_consistent(case)
    latent_compatible = _latent_compatible(F_text)
    reconstruction_verdicts = [r["verdict"] for r in recon]
    required = [r["verdict"] for r in recon + conf]
    recurrence_verdicts = [r["verdict"] for r in rec]
    path_verdicts = [r["verdict"] for r in paths]
    family_verdict = compose_family_verdict(
        required_edge_verdicts=required,
        recurrence_verdicts=recurrence_verdicts,
        path_verdicts=path_verdicts,
        connected=connected,
        multiplicities_consistent=multiplicities_consistent,
        latent_compatible=latent_compatible,
    )
    should = bool(case.get("should_be_zero") is True)
    false_zero = family_verdict == FAMILY_ZERO and not should
    majority = majority_branch_vote(reconstruction_verdicts)
    cert = ConfluentFamilyCertificate(
        family_id=str(case["id"]),
        member_ids=member_ids,
        generic_members=[m for m in member_ids if m.endswith("_xy")],
        degenerate_members=[m for m in member_ids if not m.endswith("_xy")],
        degeneracy_variables=list(case.get("degeneracy_variables") or []),
        node_multiplicities={
            mid: int(sum(mult.values()))
            for mid, mult in (case.get("node_multiplicities") or {}).items()
        },
        local_edges=_edges_to_local(recon + conf + rec + paths),
        recurrence_obligations=[{"verdict": v} for v in recurrence_verdicts],
        consistency_obligations=[{"verdict": v} for v in path_verdicts],
        assumptions=[],
        provenance=["research.multibranch_verification.falsifier"],
        family_verdict=family_verdict,
    )
    notes = []
    if false_zero:
        notes.append("false_FAMILY_ZERO")
    if majority == FAMILY_ZERO and family_verdict != FAMILY_ZERO:
        notes.append("majority_trap")
    return FamilyResult(
        case_id=str(case["id"]),
        kind=str(case.get("kind") or ""),
        should_be_zero=should,
        family_verdict=family_verdict,
        false_zero=false_zero,
        majority_verdict=majority,
        required_edge_verdicts=required,
        recurrence_verdicts=recurrence_verdicts,
        path_verdicts=path_verdicts,
        reconstruction_verdicts=reconstruction_verdicts,
        connected=connected,
        multiplicities_consistent=multiplicities_consistent,
        latent_compatible=latent_compatible,
        note=",".join(notes),
        extra={
            "reconstructions": recon,
            "confluence": conf,
            "recurrences": rec,
            "paths": paths,
            "trap": case.get("trap"),
            "n_members": len(member_ids),
            "latent_F_by_member": dict(F_text),
        },
        certificate=cert,
    )


def check_all(
    cases: Optional[list[dict[str, Any]]] = None,
) -> list[FamilyResult]:
    if cases is None:
        cases = ATTACK_CASES
    return [check_family(c) for c in cases]


def check_controls() -> list[FamilyResult]:
    return [check_family(c) for c in CONTROL_CASES]


def false_zero_count(results: Optional[list[FamilyResult]] = None) -> int:
    if results is None:
        results = check_all()
    return sum(1 for r in results if r.false_zero or (r.family_verdict == FAMILY_ZERO and not r.should_be_zero))


def report() -> dict[str, Any]:
    results = check_all()
    controls = check_controls()
    return {
        "n": len(results),
        "n_false_zero": false_zero_count(results),
        "false_zero_ids": [r.case_id for r in results if r.false_zero],
        "family_verdicts": {r.case_id: r.family_verdict for r in results},
        "majority_verdicts": {r.case_id: r.majority_verdict for r in results},
        "control_verdicts": {r.case_id: r.family_verdict for r in controls},
        "rows": [r.to_dict() for r in results],
    }
