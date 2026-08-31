"""Typed-edge lowering to executable residuals. E4 implements the body.

Do not pretend every derivation is a scalar subtraction. Asymptotic remainder
claims must not be rewritten as F - A/gamma = 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .edges import AuditEdge, GroundingResult
from .schema import AuditError, lowering_applicability
from .workspace import AuditWorkspace


@dataclass(frozen=True)
class LoweringResult:
    edge_id: str
    executable: bool
    status: str
    residual_text: Optional[str]
    residual_path: Optional[str]
    obligation_id: Optional[str]
    left: Optional[str]
    right: Optional[str]
    warnings: tuple[str, ...]
    applicability: str


def lower_edge(
    edge: AuditEdge,
    workspace: AuditWorkspace,
    grounding: GroundingResult,
) -> LoweringResult:
    """E4: produce an explicit residual or a typed non-executable status."""
    applicability = lowering_applicability(edge.edge_type)
    raise AuditError(
        "NOT_IMPLEMENTED",
        f"lowering for {edge.edge_type} ({applicability}) is implemented "
        "by the obligation-lowering layer",
        path=str(workspace.root),
    )
