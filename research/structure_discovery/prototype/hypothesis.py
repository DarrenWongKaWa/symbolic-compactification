"""Machine-readable structural hypothesis schema.

A hypothesis is NOT a proof and is NOT a complete expression. Construction
and verification are separate stages. Free-text is allowed only as commentary
beside required typed fields.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

HYPOTHESIS_TYPES = (
    "repeated_kernel",
    "identical_kernel_merge",  # aggressive: treat similar denoms as one kernel
    "permutation_orbit",
    "master_function",
    "symmetry_invariant",
    "basis_reduction",
    "generating_function",
    "divided_difference",
    "confluent_representation",
    "low_rank_structure",
    "tensor_generator",
    "derivative_family",
    "spectral_family",
    "structural_regrouping",
)

HYPOTHESIS_TYPE_TO_DLEVEL = {
    "structural_regrouping": "D1",
    "repeated_kernel": "D2",
    "identical_kernel_merge": "D2",
    "permutation_orbit": "D5",
    "master_function": "D3",
    "symmetry_invariant": "D5",
    "basis_reduction": "D5",
    "generating_function": "D4",
    "divided_difference": "D4",
    "confluent_representation": "D4",
    "low_rank_structure": "D5",
    "tensor_generator": "D5",
    "derivative_family": "D3",
    "spectral_family": "D3",
}


@dataclass
class Auxiliary:
    name: str
    definition: str
    role: str = "kernel"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class StructureHypothesis:
    hypothesis_type: str
    target_subexpressions: list[str]
    claimed_structure: str
    proposed_auxiliaries: list[Auxiliary] = field(default_factory=list)
    expected_benefit: str = ""
    construction_plan: str = ""
    required_assumptions: list[str] = field(default_factory=list)
    verification_obligations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    swap_pair: Optional[list[str]] = None
    source: str = "deterministic_discoverer"
    observation_support: list[str] = field(default_factory=list)
    aggressive: bool = False

    def __post_init__(self) -> None:
        if self.hypothesis_type not in HYPOTHESIS_TYPES:
            raise ValueError(f"unknown hypothesis_type: {self.hypothesis_type}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not self.target_subexpressions and self.hypothesis_type != "structural_regrouping":
            raise ValueError("target_subexpressions required")

    @property
    def d_level(self) -> str:
        return HYPOTHESIS_TYPE_TO_DLEVEL[self.hypothesis_type]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["d_level"] = self.d_level
        return d

    @classmethod
    def from_dict(cls, raw: dict) -> "StructureHypothesis":
        aux = [Auxiliary(**a) if not isinstance(a, Auxiliary) else a
               for a in raw.get("proposed_auxiliaries") or []]
        payload = dict(raw)
        payload.pop("d_level", None)
        payload["proposed_auxiliaries"] = aux
        known = {f.name for f in cls.__dataclass_fields__.values()}
        payload = {k: v for k, v in payload.items() if k in known}
        return cls(**payload)
