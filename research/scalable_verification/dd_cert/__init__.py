"""V4 — Newton / Hermite compositional certificates.

False ZERO = 0. No Guo pairing. Constructors imported, not copied.
"""
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.dd_cert.certificates import (
    HERMITE,
    NEWTON_FIRST,
    REPEATED,
    Certificate,
    hermite_ok,
    hermite_xxx_ok,
    hermite_xxy_ok,
    hermite_xyy_ok,
    newton_first_ok,
    repeated_ok,
)

__all__ = [
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "NEWTON_FIRST",
    "REPEATED",
    "HERMITE",
    "Certificate",
    "newton_first_ok",
    "repeated_ok",
    "hermite_ok",
    "hermite_xxy_ok",
    "hermite_xyy_ok",
    "hermite_xxx_ok",
]
