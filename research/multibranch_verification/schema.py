"""ConfluentFamilyCertificate — experimental Track-V2 proof object.

A family is not certified because members share a list. Every edge must
be machine-checkable. FAMILY_ZERO requires all required edges ZERO plus
recurrence and path consistency. Majority vote is forbidden.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

FAMILY_ZERO = "FAMILY_ZERO"
FAMILY_NONZERO = "FAMILY_NONZERO"
FAMILY_UNKNOWN = "FAMILY_UNKNOWN"

EDGE_RELATIONS = (
    "limit",
    "substitution",
    "derivative",
    "dd_recurrence",
    "hermite_dd_recurrence",
    "one_parameter_confluence",
    "repeated_node_confluence",
)

EDGE_VERDICTS = ("ZERO", "NONZERO", "UNKNOWN")


@dataclass
class LocalEdge:
    source: str
    target: str
    relation: str
    variable: str = ""
    target_value: str = ""
    obligation_id: str = ""
    verdict: str = "UNKNOWN"
    provenance: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ConfluentFamilyCertificate:
    family_id: str
    member_ids: list[str]
    generic_members: list[str] = field(default_factory=list)
    degenerate_members: list[str] = field(default_factory=list)
    degeneracy_variables: list[str] = field(default_factory=list)
    node_multiplicities: dict[str, int] = field(default_factory=dict)
    local_edges: list[LocalEdge] = field(default_factory=list)
    recurrence_obligations: list[dict[str, Any]] = field(default_factory=list)
    consistency_obligations: list[dict[str, Any]] = field(default_factory=list)
    composition_rule: str = (
        "FAMILY_ZERO iff connected required graph, all required edges ZERO, "
        "recurrence ZERO, path consistency ZERO, latent compatible; "
        "any required NONZERO => FAMILY_NONZERO; else FAMILY_UNKNOWN. No majority."
    )
    assumptions: list[str] = field(default_factory=list)
    provenance: list[str] = field(default_factory=list)
    family_verdict: str = FAMILY_UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["local_edges"] = [
            e.to_dict() if isinstance(e, LocalEdge) else e for e in self.local_edges
        ]
        return d


def compose_family_verdict(
    *,
    required_edge_verdicts: list[str],
    recurrence_verdicts: list[str],
    path_verdicts: list[str],
    connected: bool,
    multiplicities_consistent: bool,
    latent_compatible: bool = True,
) -> str:
    """Global family rule. Pairwise ZERO is not enough."""
    req = list(required_edge_verdicts) + list(recurrence_verdicts) + list(path_verdicts)
    if not connected or not multiplicities_consistent or not latent_compatible:
        if any(v == "NONZERO" for v in req):
            return FAMILY_NONZERO
        return FAMILY_UNKNOWN
    if any(v == "NONZERO" for v in req):
        return FAMILY_NONZERO
    if req and all(v == "ZERO" for v in req):
        return FAMILY_ZERO
    return FAMILY_UNKNOWN
