"""Polygamma-local identities already in SymPy. No invented masters."""

from research.scalable_verification.special.classify import (
    UNKNOWN,
    UNSUPPORTED,
    SUPPORTED,
    classify_identity,
)

__all__ = [
    "classify_identity",
    "SUPPORTED",
    "UNSUPPORTED",
    "UNKNOWN",
]
