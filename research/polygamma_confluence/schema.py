"""Atom-series confluence certificate. Timeout/size-guard is UNKNOWN, never ZERO."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"
ATOM_SERIES = "atom_series"

FAMILY_ZERO = "FAMILY_ZERO"
FAMILY_NONZERO = "FAMILY_NONZERO"
FAMILY_UNKNOWN = "FAMILY_UNKNOWN"


@dataclass
class AtomSeriesCertificate:
    """One-parameter confluence via per-atom series + Laurent t^0."""

    verdict: str = UNKNOWN
    provenance: str = ""
    n_atoms: int = 0
    reconstruction_ok: bool = False
    poles_ok: Optional[bool] = None
    full_ops: Optional[int] = None
    local_ops: Optional[int] = None
    together_ops: Optional[int] = None
    c0_ops: Optional[int] = None
    steps: tuple[str, ...] = ()
    source: str = ""
    target: str = ""
    variable: str = ""
    target_value: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
