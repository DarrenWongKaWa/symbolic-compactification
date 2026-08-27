"""Machine-readable invented abstraction: H = (T, θ, O, F).

LLM (or algorithm) must emit this, not a pretty formula.
Verifier adjudicates each proof obligation A_i - O_i[F] = 0.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

OPERATORS = (
    "antiunification",
    "master_derivative",
    "master_shift",
    "confluence",
    "basis",
    "parameterized_orbit",
)


@dataclass
class InstanceMap:
    member: str
    theta: dict[str, str]
    operator_on_template: str = "identity"  # identity | d/dtheta | specialize

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AbstractionHypothesis:
    operator: str
    family: list[str]
    latent_variables: list[str]
    template: str
    instance_maps: list[InstanceMap]
    reason: str
    proof_obligations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    source: str = "lgg"

    def __post_init__(self) -> None:
        if self.operator not in OPERATORS:
            raise ValueError(self.operator)
        if len(self.family) < 2:
            raise ValueError("family needs ≥2 members")
        if not self.template:
            raise ValueError("template required")

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["instance_maps"] = [m.to_dict() if isinstance(m, InstanceMap) else m
                              for m in self.instance_maps]
        return d
