"""Track A schema only. No search. No SOL edits."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

REPRESENTATION_TYPES = (
    "divided_difference",
    "confluent_piecewise",
    "invariant_basis",
    "generating_function",
    "operator_family",
    "other_language_change",
)


@dataclass
class MemberMap:
    member: str
    form: str
    branch: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepresentationHypothesis:
    representation_type: str
    language_from: str
    language_to: str
    latent_function: str
    nodes: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    member_maps: list[MemberMap] = field(default_factory=list)
    operators: list[Any] = field(default_factory=list)
    required_relations: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    proof_obligations: list[str] = field(default_factory=list)
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.representation_type not in REPRESENTATION_TYPES:
            raise ValueError(self.representation_type)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["member_maps"] = [
            m.to_dict() if isinstance(m, MemberMap) else m
            for m in self.member_maps
        ]
        return d
