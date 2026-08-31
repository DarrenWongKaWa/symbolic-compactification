"""Edge manifest load and source grounding. E3 implements the body."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .schema import AuditError
from .workspace import AuditWorkspace


@dataclass(frozen=True)
class AuditEdge:
    edge_id: str
    source_from: Optional[str]
    source_to: Optional[str]
    edge_type: str
    lhs: Optional[str] = None
    rhs: Optional[str] = None
    residual: Optional[str] = None
    children: tuple[str, ...] = ()
    assumptions_used: tuple[str, ...] = ()
    claim: str = ""
    notes: str = ""


@dataclass(frozen=True)
class GroundingResult:
    edge: AuditEdge
    ok: bool
    status: str
    issues: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_snapshot_hash: str


def load_edges(workspace: AuditWorkspace) -> tuple[AuditEdge, ...]:
    """E3: parse edges/edges.yaml. LHS/RHS are optional."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "edge manifest load is implemented by the edge-grounding layer",
        path=str(workspace.root),
    )


def ground_edge(edge: AuditEdge, workspace: AuditWorkspace) -> GroundingResult:
    """E3: bind an edge to declared equation/expression sources."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "edge grounding is implemented by the edge-grounding layer",
        path=str(workspace.root),
    )
