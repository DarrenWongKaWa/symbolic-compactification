"""Track V2-G — local polygamma prover. No invented masters. No LLM."""
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.multibranch_verification.special.prove import (
    DERIVATIVE,
    IDENTICAL,
    NEWTON_FIRST,
    SERIES,
    LocalProof,
    prove_local,
)

__all__ = [
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "DERIVATIVE",
    "NEWTON_FIRST",
    "SERIES",
    "IDENTICAL",
    "LocalProof",
    "prove_local",
]
