"""Scientific Proof Obligation IR (Track B / L4).

LLM prose is not an obligation. Fail-closed: uncompiled is COMPILE_FAILURE,
not UNKNOWN, and UNKNOWN is not ZERO.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

EQUALITY = "EQUALITY"
SUBSTITUTION = "SUBSTITUTION"
PERMUTATION = "PERMUTATION"
DERIVATIVE = "DERIVATIVE"
LIMIT = "LIMIT"
DIVIDED_DIFFERENCE = "DIVIDED_DIFFERENCE"
CONFLUENCE = "CONFLUENCE"
BASIS = "BASIS"

KINDS = (
    EQUALITY, SUBSTITUTION, PERMUTATION, DERIVATIVE,
    LIMIT, DIVIDED_DIFFERENCE, CONFLUENCE, BASIS,
)

COMPILE_OK = "COMPILE_OK"
COMPILE_FAILURE = "COMPILE_FAILURE"

# Layer labels
D = "D"  # discovery
C = "C"  # construction / compilation
V = "V"  # verification


@dataclass
class Obligation:
    kind: str
    left: str
    right: str = ""
    member: str = ""
    latent: str = ""
    operator: str = "identity"
    theta: dict[str, str] = field(default_factory=dict)
    nodes: list[str] = field(default_factory=list)
    order: int = 1
    var: str = ""
    to: str = ""
    coefficients: dict[str, str] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    compile_status: str = COMPILE_OK
    compile_error: Optional[str] = None
    source: str = "llm_hypothesis"

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(self.kind)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CompileResult:
    obligations: list[Obligation]
    n_ok: int
    n_fail: int
    hypothesis_type: str = ""
    latent_core: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_type": self.hypothesis_type,
            "latent_core": self.latent_core,
            "n_ok": self.n_ok,
            "n_fail": self.n_fail,
            "obligations": [o.to_dict() for o in self.obligations],
        }


@dataclass
class VerifyResult:
    kind: str
    verdict: str  # ZERO | NONZERO | UNKNOWN
    backend: str
    note: str = ""
    compile_status: str = COMPILE_OK
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
