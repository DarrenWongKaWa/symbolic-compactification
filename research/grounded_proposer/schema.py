"""Grounded representation hypothesis. Members are catalog IDs only."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

REPRESENTATION_TYPES = (
    "divided_difference",
    "confluent_representation",
    "derivative_family",
    "symmetry_invariant",
    "repeated_kernel",
    "parameterized_family",
    "master_function",
    "other_structured",
)

PARSE_FAILURE = "PARSE_FAILURE"
OK = "OK"
ABSTAIN = "ABSTAIN"


@dataclass
class Fingerprint:
    functions: list[str] = field(default_factory=list)
    indices: list[str] = field(default_factory=list)
    branch_condition: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MemberMap:
    source_node_id: str
    role: str = ""
    source_fingerprint: Optional[Fingerprint] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_node_id": self.source_node_id,
            "role": self.role,
            "source_fingerprint": (
                self.source_fingerprint.to_dict()
                if isinstance(self.source_fingerprint, Fingerprint)
                else self.source_fingerprint
            ),
        }


@dataclass
class GroundedHypothesis:
    representation_type: str
    latent_object: str
    member_maps: list[MemberMap]
    operators: list[Any] = field(default_factory=list)
    proof_obligations: list[str] = field(default_factory=list)
    required_assumptions: list[str] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 0.0
    generic_member: str = ""
    degenerate_member: str = ""
    limit_variable: str = ""
    parse_status: str = OK
    parse_error: Optional[str] = None

    def member_ids(self) -> list[str]:
        ids = [m.source_node_id for m in self.member_maps]
        if self.generic_member:
            ids.append(self.generic_member)
        if self.degenerate_member:
            ids.append(self.degenerate_member)
        return list(dict.fromkeys(ids))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["member_maps"] = [m.to_dict() if isinstance(m, MemberMap) else m
                            for m in self.member_maps]
        return d
