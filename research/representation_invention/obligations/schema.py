"""Experimental representation obligation IR.

Independent of ``research.obligation_ir.schema``. COMPILE_FAILURE is not
UNKNOWN and is not ZERO. The compiler never assigns a verification verdict.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from research.representation_invention.schema import OBLIGATION_KINDS

EQUALITY = "EQUALITY"
SUBSTITUTION = "SUBSTITUTION"
PERMUTATION = "PERMUTATION"
DERIVATIVE = "DERIVATIVE"
LIMIT = "LIMIT"
NEWTON_DD = "NEWTON_DD"
HERMITE_DD = "HERMITE_DD"
CONFLUENCE = "CONFLUENCE"
RECURRENCE = "RECURRENCE"
MASTER_INSTANCE = "MASTER_INSTANCE"
BASIS_RECONSTRUCTION = "BASIS_RECONSTRUCTION"

KINDS = (
    EQUALITY,
    SUBSTITUTION,
    PERMUTATION,
    DERIVATIVE,
    LIMIT,
    NEWTON_DD,
    HERMITE_DD,
    CONFLUENCE,
    RECURRENCE,
    MASTER_INSTANCE,
    BASIS_RECONSTRUCTION,
)

if KINDS != OBLIGATION_KINDS:
    raise RuntimeError("experimental kinds must match RepresentationHypothesisV2")

COMPILE_OK = "COMPILE_OK"
COMPILE_FAILURE = "COMPILE_FAILURE"

# Verifier outcomes for a compiled obligation. COMPILE_FAILURE is not one of these.
ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"


@dataclass
class Obligation:
    """Checkable reconstruction. Failure to build it is COMPILE_FAILURE."""

    kind: str
    member_ids: list[str] = field(default_factory=list)
    left: str = ""
    right: str = ""
    exact_expressions: dict[str, str] = field(default_factory=dict)
    variables: dict[str, str] = field(default_factory=dict)
    assumptions: list[str] = field(default_factory=list)
    operator: str = "identity"
    expected_relation: str = "equal"
    provenance: str = "compiler"
    compile_status: str = COMPILE_OK
    compile_error: Optional[str] = None
    latent: str = ""
    theta: dict[str, str] = field(default_factory=dict)
    nodes: list[str] = field(default_factory=list)
    node_multiplicities: list[int] = field(default_factory=list)
    order: int = 1
    var: str = ""
    to: str = ""
    coefficients: dict[str, str] = field(default_factory=dict)
    basis: list[str] = field(default_factory=list)
    recurrence_rhs: str = ""
    shift_var: str = ""
    shift_step: str = "1"
    reconstruction: str = ""

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            if self.compile_status == COMPILE_OK:
                self.compile_status = COMPILE_FAILURE
                self.compile_error = self.compile_error or f"unknown_kind:{self.kind}"

    @property
    def source_member_ids(self) -> list[str]:
        return list(self.member_ids)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["source_member_ids"] = list(self.member_ids)
        return d


@dataclass
class CompileResult:
    """Hypothesis-layer compilation. No ZERO / NONZERO / UNKNOWN here."""

    obligations: list[Obligation]
    n_ok: int
    n_fail: int
    representation_type: str = ""
    hypothesis_type: str = ""
    latent_core: str = ""
    notes: list[str] = field(default_factory=list)

    @property
    def compile_status(self) -> str:
        if self.n_ok == 0:
            return COMPILE_FAILURE
        return COMPILE_OK

    def to_dict(self) -> dict[str, Any]:
        return {
            "representation_type": self.representation_type,
            "hypothesis_type": self.hypothesis_type or self.representation_type,
            "latent_core": self.latent_core,
            "n_ok": self.n_ok,
            "n_fail": self.n_fail,
            "compile_status": self.compile_status,
            "notes": list(self.notes),
            "obligations": [o.to_dict() for o in self.obligations],
        }


@dataclass
class VerifyResult:
    """Verification of one compiled obligation.

    ``verdict`` is ZERO | NONZERO | UNKNOWN only when ``compile_status`` is
    COMPILE_OK. Compile failures leave ``verdict`` unset (None).
    """

    kind: str
    verdict: Optional[str]
    backend: str
    note: str = ""
    compile_status: str = COMPILE_OK
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
