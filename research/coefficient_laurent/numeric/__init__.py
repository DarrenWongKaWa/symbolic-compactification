"""Numeric falsifier for coefficient-space Laurent hops.

High-precision samples of lim t->0 E_gen vs E_diag. Not a verifier.
Returns agree / disagree / undecided. Never ZERO. Strong mismatch is
SUSPECT_NONZERO for investigation only; exact path still required.
No LLM.
"""
from research.coefficient_laurent.numeric.probe import (
    AGREE,
    ALLOWED_STATUSES,
    DISAGREE,
    SUSPECT_NONZERO,
    UNDECIDED,
    NumericProbeResult,
    numeric_probe,
    probe_report,
)

__all__ = [
    "AGREE",
    "DISAGREE",
    "UNDECIDED",
    "SUSPECT_NONZERO",
    "ALLOWED_STATUSES",
    "NumericProbeResult",
    "numeric_probe",
    "probe_report",
]
