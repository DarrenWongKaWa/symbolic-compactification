"""Track V4 — generic polygamma / repeated-argument local confluence.

No LLM. No Guo identity table. PATH/FAMILY composition reuses Track V3.
"""
from research.polygamma_confluence.schema import (
    ATOM_SERIES,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    NONZERO,
    UNKNOWN,
    ZERO,
    AtomSeriesCertificate,
)
from research.polygamma_confluence.engine import atom_series_confluence

__all__ = [
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "FAMILY_ZERO",
    "FAMILY_NONZERO",
    "FAMILY_UNKNOWN",
    "ATOM_SERIES",
    "AtomSeriesCertificate",
    "atom_series_confluence",
]
