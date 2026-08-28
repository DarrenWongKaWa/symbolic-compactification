"""Piecewise family normalizer (Track V2-F).

Roles from conditions only. Does not collapse branches or infer confluence.
"""
from research.multibranch_verification.piecewise.normalize import (
    DIAGONAL,
    GENERIC,
    HIGHER_DEGENERACY,
    ROLES,
    UNKNOWN_ROLE,
    classify_condition,
    normalize_piecewise_family,
)

__all__ = [
    "GENERIC",
    "DIAGONAL",
    "HIGHER_DEGENERACY",
    "UNKNOWN_ROLE",
    "ROLES",
    "classify_condition",
    "normalize_piecewise_family",
]
