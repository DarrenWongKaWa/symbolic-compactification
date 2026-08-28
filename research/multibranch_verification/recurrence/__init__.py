"""V2-C — generic Newton / Hermite recurrence checks.

False ZERO = 0. Constructors imported, not copied. No source-member binding.
"""
from research.multibranch_verification.recurrence.check import (
    BACKEND_HERMITE,
    BACKEND_NEWTON_FIRST,
    BACKEND_NEWTON_TABLE,
    BACKEND_REPEATED,
    FORMULAS,
    KIND_FXX,
    KIND_FXXX,
    KIND_FXXY,
    KIND_FXYY,
    KIND_HERMITE_STEP,
    KIND_NEWTON_STEP,
    NONZERO,
    REL_DD,
    REL_HERMITE,
    RecurrenceResult,
    UNKNOWN,
    ZERO,
    check_recurrence,
)

__all__ = [
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "KIND_FXX",
    "KIND_FXXY",
    "KIND_FXYY",
    "KIND_FXXX",
    "KIND_NEWTON_STEP",
    "KIND_HERMITE_STEP",
    "REL_DD",
    "REL_HERMITE",
    "FORMULAS",
    "BACKEND_HERMITE",
    "BACKEND_REPEATED",
    "BACKEND_NEWTON_FIRST",
    "BACKEND_NEWTON_TABLE",
    "RecurrenceResult",
    "check_recurrence",
]
