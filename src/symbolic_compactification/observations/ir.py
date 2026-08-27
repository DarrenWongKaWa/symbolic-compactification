"""Backend-independent observation IR.

Epistemic classes are exclusive. DESCRIPTIVE_FACT is never equivalence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

EXACT_FACT = "EXACT_FACT"
DESCRIPTIVE_FACT = "DESCRIPTIVE_FACT"
CANDIDATE_RELATION = "CANDIDATE_RELATION"
EXACTNESS_CLASSES = (EXACT_FACT, DESCRIPTIVE_FACT, CANDIDATE_RELATION)

RELATION_TYPES = (
    "IDENTICAL",
    "CSE_SHARED",
    "AC_EQUIVALENT",
    "CANONICALLY_EQUIVALENT",
    "SUBSTITUTION_INSTANCE",
    "LGG_FAMILY",
    "PATTERN_MATCH",
    "PERMUTATION_RELATED",
    "INDEX_RENAMING_RELATED",
    "DERIVATIVE_RELATED",
    "KNOWN_REWRITE_EQUIVALENT",
    "EGRAPH_EQUIVALENT",
    "TENSOR_SYMMETRY_RELATED",
    "SAME_FUNCTION_FAMILY",
    "SAME_POLE_SIGNATURE",
    "SAME_DENOMINATOR_FAMILY",
    "SAME_BRANCH_DEPENDENCY",
    "SAME_INDEX_ORBIT",
    "RECURRENCE_CANDIDATE",
    "LIMIT_CANDIDATE",
)

# Never upgrade these to EXACT_FACT in adapters.
DESCRIPTIVE_ONLY = frozenset({
    "SAME_FUNCTION_FAMILY",
    "SAME_POLE_SIGNATURE",
    "SAME_DENOMINATOR_FAMILY",
    "SAME_BRANCH_DEPENDENCY",
    "SAME_INDEX_ORBIT",
    "RECURRENCE_CANDIDATE",
    "LIMIT_CANDIDATE",
    "PATTERN_MATCH",
})

FORBIDDEN_INTERPRETATION = (
    "Phi_Gamma", "PhiGamma", "Hermite", "divided difference",
    "nine generator", "physical generator", "thermal master",
    "therefore define", "PRB", "Phi_Gamma",
)


@dataclass
class ExpressionNode:
    node_id: str
    text: str
    srepr: str
    structural_hash: str
    free_symbols: list[str] = field(default_factory=list)
    functions: list[str] = field(default_factory=list)
    indexed_symbols: list[str] = field(default_factory=list)
    ops: int = 0
    provenance: str = "parser"
    source_span: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RelationEdge:
    source_ids: list[str]
    relation_type: str
    backend: str
    exactness_class: str
    evidence: str
    assumptions: list[str] = field(default_factory=list)
    confidence_class: str = "deterministic"
    witness: Optional[str] = None
    theory: Optional[str] = None
    backend_version: Optional[str] = None

    def __post_init__(self) -> None:
        if self.relation_type not in RELATION_TYPES:
            raise ValueError(f"unknown relation_type {self.relation_type}")
        if self.exactness_class not in EXACTNESS_CLASSES:
            raise ValueError(self.exactness_class)
        if self.relation_type in DESCRIPTIVE_ONLY and self.exactness_class == EXACT_FACT:
            raise ValueError(f"{self.relation_type} cannot be EXACT_FACT")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObservationFamily:
    family_id: str
    member_ids: list[str]
    kind: str
    backend: str
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CanonicalVariant:
    node_id: str
    variant_text: str
    method: str
    backend: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ObservationBundle:
    expression_summary: dict
    nodes: list[ExpressionNode]
    families: list[ObservationFamily]
    relations: list[RelationEdge]
    canonical_variants: list[CanonicalVariant]
    backend_status: dict[str, str]
    provenance: dict
    packets: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "expression_summary": self.expression_summary,
            "nodes": [n.to_dict() for n in self.nodes],
            "families": [f.to_dict() for f in self.families],
            "relations": [r.to_dict() for r in self.relations],
            "canonical_variants": [c.to_dict() for c in self.canonical_variants],
            "backend_status": self.backend_status,
            "provenance": self.provenance,
            "packets": self.packets,
        }
