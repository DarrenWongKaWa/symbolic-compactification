"""Numeric remainder-scaling probes.

High-precision samples of remainder / t^{N+1} as t -> 0. Not a verifier.
Returns agree / disagree / undecided. Never ZERO, never CERTIFIED.
Disagreement is EXACT_INVESTIGATION only; it does not mint NONANALYTIC.
No LLM.
"""
from research.remainder_certification.numeric.probe import (
    AGREE,
    ALLOWED_STATUSES,
    DISAGREE,
    EXACT_INVESTIGATION,
    FORBIDDEN_VERDICTS,
    UNDECIDED,
    NumericProbeResult,
    numeric_probe,
    probe_report,
)

__all__ = [
    "AGREE",
    "DISAGREE",
    "UNDECIDED",
    "EXACT_INVESTIGATION",
    "ALLOWED_STATUSES",
    "FORBIDDEN_VERDICTS",
    "NumericProbeResult",
    "numeric_probe",
    "probe_report",
]
