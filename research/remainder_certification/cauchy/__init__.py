"""Cauchy remainder order bound from a certified pole-free disk.

Does not certify a disk. Remainder CERTIFIED is not hop ZERO.
"""
from research.remainder_certification.cauchy.bound import (
    CAUCHY_BOUND_FORM,
    M_FINITE_LEMMA,
    Q_FORM,
    cauchy_remainder_bound,
)
from research.remainder_certification.schema import (
    ASSUMPTION_REQUIRED,
    CERTIFIED,
    NEIGHBORHOOD_CERTIFIED,
    NONANALYTIC,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)

__all__ = [
    "CAUCHY_BOUND_FORM",
    "M_FINITE_LEMMA",
    "Q_FORM",
    "cauchy_remainder_bound",
    "ASSUMPTION_REQUIRED",
    "CERTIFIED",
    "NEIGHBORHOOD_CERTIFIED",
    "NONANALYTIC",
    "UNKNOWN",
    "remainder_cannot_be_hop_zero",
    "validate_certificate",
]
