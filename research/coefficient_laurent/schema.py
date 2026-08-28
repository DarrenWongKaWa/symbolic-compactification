"""Laurent coefficient IR. LEVEL A is not hop ZERO. Majority is forbidden."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

LEVEL_A = "LEVEL_A"  # atom series only
LEVEL_B = "LEVEL_B"  # negative coefficients cancel
LEVEL_C = "LEVEL_C"  # limit certificate

ATOM_CLASSES = ("POLYGAMMA", "RATIONAL", "POWER", "LOG", "OTHER_UNSUPPORTED")

METHOD_VERSION = "v5-coeff-laurent-1"


@dataclass
class LaurentAtom:
    atom_id: str
    source_member: str
    coefficient: str = ""
    function_head: str = ""
    function_order: str = ""
    argument: str = ""
    degeneration_variable: str = ""
    target_value: str = ""
    spectator: str = ""
    source_text_hash: str = ""
    canonical_atom_hash: str = ""
    atom_class: str = "OTHER_UNSUPPORTED"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LaurentCoefficientRecord:
    atom_id: str
    power: int
    coefficient_expr: str
    exact: bool = False
    method: str = ""
    provenance: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LaurentCertificate:
    source_member: str
    target_member: str
    degeneration_variable: str = ""
    target_value: str = ""
    required_power_min: Optional[int] = None
    required_power_max: Optional[int] = None
    atom_records: list[dict[str, Any]] = field(default_factory=list)
    summed_coefficients: dict[str, str] = field(default_factory=dict)
    negative_coefficients_verdict: str = UNKNOWN
    constant_term_verdict: str = UNKNOWN
    remainder_verdict: str = UNKNOWN
    final_verdict: str = UNKNOWN
    proof_level: str = LEVEL_A
    method_version: str = METHOD_VERSION
    source_text_hash: str = ""
    target_text_hash: str = ""
    atom_decomposition_hash: str = ""
    assumptions_hash: str = ""
    max_intermediate_ops: Optional[int] = None
    used_full_together: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compose_hop_verdict(
    *,
    reconstruction_ok: bool,
    atoms_expanded: bool,
    negative_verdict: str,
    constant_verdict: str,
    remainder_verdict: str,
) -> tuple[str, str]:
    """Return (final_verdict, proof_level).

    Only LEVEL C may be ZERO. Atom-series success is not hop ZERO.
    A nonzero negative coefficient or mismatched t^0 is NONZERO.
    """
    if not reconstruction_ok:
        return UNKNOWN, LEVEL_A
    if any(v == NONZERO for v in (negative_verdict, constant_verdict)):
        return NONZERO, LEVEL_B if negative_verdict == NONZERO else LEVEL_C
    if not atoms_expanded:
        return UNKNOWN, LEVEL_A
    if negative_verdict != ZERO:
        return UNKNOWN, LEVEL_A
    if constant_verdict != ZERO or remainder_verdict != ZERO:
        return UNKNOWN, LEVEL_B
    return ZERO, LEVEL_C
