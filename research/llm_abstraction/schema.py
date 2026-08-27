"""Experimental LLM hypothesis schema.

Frozen StructureHypothesis / AbstractionHypothesis are not mutated.
This schema is the DeepSeek proposer contract. Missing fields are
PARSE_FAILURE, never silently filled with scientific content.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

HYPOTHESIS_TYPES = (
    "repeated_kernel",
    "parameterized_family",
    "master_function",
    "derivative_family",
    "recurrence_family",
    "confluent_representation",
    "divided_difference",
    "symmetry_invariant",
    "basis_reduction",
    "tensor_generator",
    "generating_function",
    "other_structured",
)

TYPE_TO_DLEVEL = {
    "repeated_kernel": "D2",
    "parameterized_family": "D3",
    "master_function": "D3",
    "derivative_family": "D3",
    "recurrence_family": "D3",
    "confluent_representation": "D4",
    "divided_difference": "D4",
    "generating_function": "D4",
    "symmetry_invariant": "D5",
    "basis_reduction": "D5",
    "tensor_generator": "D5",
    "other_structured": "D1",
}

# Representation-changing types (T5–T7 / F5–F7).
REPRESENTATION_TYPES = frozenset({
    "confluent_representation",
    "divided_difference",
    "symmetry_invariant",
    "basis_reduction",
    "tensor_generator",
    "generating_function",
    "master_function",
})

REQUIRED_FIELDS = (
    "hypothesis_type",
    "target_members",
    "latent_object",
    "parameters",
    "operators",
    "instance_maps",
    "construction_plan",
    "required_assumptions",
    "proof_obligations",
    "rationale",
    "confidence",
)

PARSE_FAILURE = "PARSE_FAILURE"
OK = "OK"
ABSTAIN = "ABSTAIN"
BLOCKED = "BLOCKED"
UNNECESSARY_STRUCTURE = "UNNECESSARY_STRUCTURE"

QUALITY_CLASSES = (
    "useful",
    "shallow",
    "tautological",
    "unnecessary_structure",
    "incorrect",
    "unverifiable",
    "gold-like-but-unsupported",
    "abstain",
    "parse_failure",
)


@dataclass
class LLMStructureHypothesis:
    hypothesis_type: str
    target_members: list[str]
    latent_object: str
    parameters: list[str]
    operators: list[Any]
    instance_maps: list[Any]
    construction_plan: str
    required_assumptions: list[str]
    proof_obligations: list[str]
    rationale: str
    confidence: float
    parse_status: str = OK
    parse_error: Optional[str] = None
    quality_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.parse_status == PARSE_FAILURE:
            return
        if self.hypothesis_type not in HYPOTHESIS_TYPES:
            raise ValueError(f"unknown hypothesis_type: {self.hypothesis_type}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence must be in [0, 1]")

    @property
    def d_level(self) -> str:
        return TYPE_TO_DLEVEL.get(self.hypothesis_type, "D1")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["d_level"] = self.d_level
        return d

    @classmethod
    def parse_failure(cls, reason: str, raw: Optional[dict] = None) -> "LLMStructureHypothesis":
        raw = raw or {}
        return cls(
            hypothesis_type="other_structured",
            target_members=list(raw.get("target_members") or []),
            latent_object=str(raw.get("latent_object") or ""),
            parameters=list(raw.get("parameters") or []),
            operators=list(raw.get("operators") or []),
            instance_maps=list(raw.get("instance_maps") or []),
            construction_plan=str(raw.get("construction_plan") or ""),
            required_assumptions=list(raw.get("required_assumptions") or []),
            proof_obligations=list(raw.get("proof_obligations") or []),
            rationale=str(raw.get("rationale") or ""),
            confidence=0.0,
            parse_status=PARSE_FAILURE,
            parse_error=reason,
        )


@dataclass
class ProposeResult:
    hypotheses: list[LLMStructureHypothesis]
    parse_status: str
    parse_error: Optional[str] = None
    abstain: bool = False
    abstain_reason: str = ""
    raw_content: str = ""
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypotheses": [h.to_dict() for h in self.hypotheses],
            "parse_status": self.parse_status,
            "parse_error": self.parse_error,
            "abstain": self.abstain,
            "abstain_reason": self.abstain_reason,
            "raw_content": self.raw_content,
            "meta": self.meta,
            "n_hypotheses": len([
                h for h in self.hypotheses if h.parse_status == OK
            ]),
            "n_parse_failure": len([
                h for h in self.hypotheses if h.parse_status == PARSE_FAILURE
            ]),
        }
