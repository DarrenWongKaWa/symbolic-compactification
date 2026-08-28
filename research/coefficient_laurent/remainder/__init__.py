"""Remainder sufficiency for rational × polygamma Laurent atoms.

Series through t^0 is enough when the affine argument at t=0 is not a
nonpositive-integer polygamma pole. Otherwise remainder_ok is False and
the remainder verdict is UNKNOWN.
"""
from research.coefficient_laurent.remainder.sufficiency import (
    REQUIRED_PMAX,
    SUFFICIENCY_REASON,
    UNKNOWN,
    remainder_ok,
    remainder_verdict,
    required_pmin,
)

__all__ = [
    "remainder_ok",
    "required_pmin",
    "remainder_verdict",
    "REQUIRED_PMAX",
    "UNKNOWN",
    "SUFFICIENCY_REASON",
]
