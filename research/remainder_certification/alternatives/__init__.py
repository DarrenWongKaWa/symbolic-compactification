"""Alternative remainder backends. Not CASE R-E; continue custom certificate."""
from __future__ import annotations

from typing import Any

CASE_R_E = "CASE_R_E"
CONTINUE_CUSTOM = "CONTINUE_CUSTOM"
RECOMMENDATION = CONTINUE_CUSTOM

__all__ = [
    "CASE_R_E",
    "CONTINUE_CUSTOM",
    "RECOMMENDATION",
    "run_probe",
]


def run_probe() -> dict[str, Any]:
    from research.remainder_certification.alternatives.probe import run_probe as _run

    return _run()
