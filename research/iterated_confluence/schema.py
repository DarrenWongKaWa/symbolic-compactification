"""IteratedConfluenceCertificate — Track V3 proof object.

PATH_ZERO is not FAMILY_ZERO. Iterated limits are not joint limits unless
path consistency is itself certified. Majority vote is forbidden.
Timeout, size-guard, and missing consistency are UNKNOWN, never ZERO.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

PATH_ZERO = "PATH_ZERO"
PATH_NONZERO = "PATH_NONZERO"
PATH_UNKNOWN = "PATH_UNKNOWN"

FAMILY_ZERO = "FAMILY_ZERO"
FAMILY_NONZERO = "FAMILY_NONZERO"
FAMILY_UNKNOWN = "FAMILY_UNKNOWN"

CONSISTENT_ZERO = "CONSISTENT_ZERO"
INCONSISTENT_NONZERO = "INCONSISTENT_NONZERO"
CONSISTENCY_UNKNOWN = "UNKNOWN"

EDGE_RELATIONS = (
    "one_parameter_confluence",
    "substitution",
    "derivative",
    "limit",
    "repeated_node_confluence",
)

PATH_VERDICTS = (PATH_ZERO, PATH_NONZERO, PATH_UNKNOWN)
FAMILY_VERDICTS = (FAMILY_ZERO, FAMILY_NONZERO, FAMILY_UNKNOWN)
CONSISTENCY_VERDICTS = (CONSISTENT_ZERO, INCONSISTENT_NONZERO, CONSISTENCY_UNKNOWN)
EDGE_VERDICTS = (ZERO, NONZERO, UNKNOWN)

COMPOSITION_RULE = (
    "PATH_ZERO iff every required step is ZERO; any step NONZERO => PATH_NONZERO; "
    "else PATH_UNKNOWN. FAMILY_ZERO iff every required path is PATH_ZERO, every "
    "required local edge is ZERO, branch reconstruction is ZERO, and — whenever "
    "the claim needs order independence — path consistency is CONSISTENT_ZERO. "
    "Any required NONZERO or INCONSISTENT_NONZERO => FAMILY_NONZERO. Otherwise "
    "FAMILY_UNKNOWN. PATH_ZERO is not FAMILY_ZERO. Majority is forbidden. "
    "Iterated limit is not joint limit unless consistency is certified."
)


@dataclass
class PathStep:
    """One one-parameter edge, possibly after spectator split."""

    source: str
    target: str
    variable: str = ""
    target_value: str = ""
    spectator_map: dict[str, Any] = field(default_factory=dict)
    local_kernel_id: str = ""
    old_ops: Optional[int] = None
    local_ops: Optional[int] = None
    verdict: str = UNKNOWN
    provenance: str = ""
    relation: str = "one_parameter_confluence"
    obligation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PathCertificate:
    """Ordered one-parameter path. Does not by itself certify a family."""

    path_id: str
    start_member: str
    end_member: str = ""
    steps: list[PathStep] = field(default_factory=list)
    path_verdict: str = PATH_UNKNOWN
    provenance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["steps"] = [
            s.to_dict() if isinstance(s, PathStep) else s for s in self.steps
        ]
        return d


@dataclass
class PathConsistencyObligation:
    """Agreement of two iterated paths with a common start and end.

    CONSISTENT_ZERO is not assumed from commuting-looking coordinates.
    """

    path_a: str
    path_b: str
    start: str
    end: str
    verdict: str = CONSISTENCY_UNKNOWN
    provenance: str = ""
    obligation_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IntermediateExpression:
    """Source-derived intermediate. No heuristic interpolation."""

    intermediate_id: str
    parent_id: str
    transformation: str
    reconstruction_ok: bool = False
    provenance: str = ""
    expr_sha256: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class IteratedConfluenceCertificate:
    """Family-level certificate. Not accepted because members share a list."""

    family_id: str
    members: list[str]
    degeneracy_coordinates: list[str] = field(default_factory=list)
    paths: list[PathCertificate] = field(default_factory=list)
    path_consistency_obligations: list[PathConsistencyObligation] = field(
        default_factory=list
    )
    branch_reconstruction_obligations: list[dict[str, Any]] = field(
        default_factory=list
    )
    family_verdict: str = FAMILY_UNKNOWN
    composition_rule: str = COMPOSITION_RULE
    assumptions: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    require_path_independence: bool = True

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["paths"] = [
            p.to_dict() if isinstance(p, PathCertificate) else p for p in self.paths
        ]
        d["path_consistency_obligations"] = [
            c.to_dict() if isinstance(c, PathConsistencyObligation) else c
            for c in self.path_consistency_obligations
        ]
        return d


def _is_nonzero(v: str) -> bool:
    return v in (NONZERO, PATH_NONZERO, FAMILY_NONZERO, INCONSISTENT_NONZERO)


def _is_path_zero(v: str) -> bool:
    return v in (PATH_ZERO, ZERO)


def _is_edge_zero(v: str) -> bool:
    return v == ZERO


def _is_consistent_zero(v: str) -> bool:
    return v in (CONSISTENT_ZERO, ZERO)


def compose_path_verdict(step_verdicts: list[str]) -> str:
    """Compose one path from local step verdicts.

    Empty path is PATH_UNKNOWN, not PATH_ZERO.
    """
    if not step_verdicts:
        return PATH_UNKNOWN
    if any(_is_nonzero(v) for v in step_verdicts):
        return PATH_NONZERO
    if all(_is_edge_zero(v) for v in step_verdicts):
        return PATH_ZERO
    return PATH_UNKNOWN


def compose_family_verdict(
    *,
    path_verdicts: list[str],
    consistency_verdicts: list[str],
    reconstruction_verdicts: list[str],
    required_edge_verdicts: list[str] | None = None,
    require_path_independence: bool = True,
) -> str:
    """Global family rule.

    PATH_ZERO of one or more paths is never FAMILY_ZERO by itself.
    If the representation claim needs order independence and consistency
    is missing or UNKNOWN, FAMILY_ZERO is forbidden.
    """
    edges = list(required_edge_verdicts or [])
    recs = list(reconstruction_verdicts or [])
    paths = list(path_verdicts or [])
    cons = list(consistency_verdicts or [])
    pool = paths + cons + recs + edges
    if not pool:
        return FAMILY_UNKNOWN
    if any(_is_nonzero(v) for v in pool):
        return FAMILY_NONZERO
    if not (paths or edges):
        return FAMILY_UNKNOWN
    paths_ok = all(_is_path_zero(v) for v in paths)
    recs_ok = all(_is_edge_zero(v) for v in recs)
    edges_ok = all(_is_edge_zero(v) for v in edges)
    if require_path_independence:
        if not cons or not all(_is_consistent_zero(v) for v in cons):
            return FAMILY_UNKNOWN
    if paths_ok and recs_ok and edges_ok:
        return FAMILY_ZERO
    return FAMILY_UNKNOWN
