"""Experimental representation obligation compiler and verifier.

COMPILE_FAILURE ≠ UNKNOWN ≠ ZERO. Historical ``research.obligation_ir``
semantics are not modified.
"""

from research.representation_invention.obligations.compile import compile_hypothesis
from research.representation_invention.obligations.schema import (
    BASIS_RECONSTRUCTION,
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    DERIVATIVE,
    EQUALITY,
    HERMITE_DD,
    KINDS,
    LIMIT,
    MASTER_INSTANCE,
    NEWTON_DD,
    NONZERO,
    PERMUTATION,
    RECURRENCE,
    SUBSTITUTION,
    UNKNOWN,
    ZERO,
    CompileResult,
    Obligation,
    VerifyResult,
)
from research.representation_invention.obligations.verify import verify_obligation

__all__ = [
    "BASIS_RECONSTRUCTION",
    "COMPILE_FAILURE",
    "COMPILE_OK",
    "CONFLUENCE",
    "DERIVATIVE",
    "EQUALITY",
    "HERMITE_DD",
    "KINDS",
    "LIMIT",
    "MASTER_INSTANCE",
    "NEWTON_DD",
    "NONZERO",
    "PERMUTATION",
    "RECURRENCE",
    "SUBSTITUTION",
    "UNKNOWN",
    "ZERO",
    "CompileResult",
    "Obligation",
    "VerifyResult",
    "compile_hypothesis",
    "verify_obligation",
]
