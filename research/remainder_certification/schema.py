"""RemainderCertificate IR. CERTIFIED remainder is not hop ZERO."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

CERTIFIED = "CERTIFIED"
ASSUMPTION_REQUIRED = "ASSUMPTION_REQUIRED"
NONANALYTIC = "NONANALYTIC"
UNKNOWN = "UNKNOWN"

REMAINDER_VERDICTS = (CERTIFIED, ASSUMPTION_REQUIRED, NONANALYTIC, UNKNOWN)

A_DECLARED = "A_DECLARED"
B_DERIVED = "B_DERIVED"
C_GENERICITY = "C_GENERICITY"
D_HUMAN_REQUIRED = "D_HUMAN_REQUIRED"

ASSUMPTION_CLASSES = (A_DECLARED, B_DERIVED, C_GENERICITY, D_HUMAN_REQUIRED)

METHOD_VERSION = "rc-remainder-cert-1"

NEIGHBORHOOD_CERTIFIED = "CERTIFIED_NEIGHBORHOOD"
NEIGHBORHOOD_ASSUMPTION = "ASSUMPTION_REQUIRED"
NEIGHBORHOOD_UNKNOWN = "UNKNOWN"
UNSUPPORTED = "UNSUPPORTED"

# Hop labels live in Track V5 schema. Remainder CERTIFIED is never hop ZERO.
HOP_ZERO = "ZERO"


@dataclass
class RemainderCertificate:
    """Atom-local remainder certificate. Not a hop certificate."""

    function_family: str = ""
    function_order: str = ""
    argument: str = ""
    expansion_point: str = ""
    perturbation: str = ""
    expansion_order: Optional[int] = None
    domain_conditions: list[str] = field(default_factory=list)
    analyticity_certificate: dict[str, Any] = field(default_factory=dict)
    distance_to_singularity: str = ""
    remainder_form: str = ""
    bound: str = ""
    required_small_t_condition: str = ""
    assumptions_used: list[dict[str, Any]] = field(default_factory=list)
    proof_dependencies: list[str] = field(default_factory=list)
    verdict: str = UNKNOWN
    neighborhood_verdict: str = UNKNOWN
    assumptions_hash: str = ""
    argument_text_hash: str = ""
    method_version: str = METHOD_VERSION
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_certificate(cert: RemainderCertificate) -> str:
    """Return UNKNOWN if the IR is ill-formed. Never upgrade a verdict.

    Empty domain_conditions is an error: the caller must write an
    explicit justified condition, including 'entire' when true.
    Class-C/D assumptions forbid CERTIFIED.
    """
    if cert.verdict not in REMAINDER_VERDICTS:
        return UNKNOWN
    if cert.verdict == HOP_ZERO:
        return UNKNOWN
    if not cert.domain_conditions:
        return UNKNOWN
    if cert.verdict == CERTIFIED and _uses_undeclared_genericity(cert):
        return ASSUMPTION_REQUIRED
    return cert.verdict


def _uses_undeclared_genericity(cert: RemainderCertificate) -> bool:
    for item in cert.assumptions_used:
        klass = item.get("class") if isinstance(item, dict) else None
        if klass in (C_GENERICITY, D_HUMAN_REQUIRED):
            return True
    return False


def remainder_cannot_be_hop_zero(verdict: str) -> bool:
    """Remainder CERTIFIED is never hop ZERO."""
    return verdict != HOP_ZERO
