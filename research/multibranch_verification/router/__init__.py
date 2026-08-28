"""Track V2 obligation router.

Chooses a strategy; does not decide truth. Thresholds are frozen in
``THRESHOLDS.json``.
"""
from research.multibranch_verification.router.complexity import (
    MEASURE_KEYS,
    STRATEGIES,
    THRESHOLDS,
    THRESHOLDS_PATH,
    VERDICTS,
    load_thresholds,
    measure,
    route,
    route_name,
)

__all__ = [
    "MEASURE_KEYS",
    "STRATEGIES",
    "THRESHOLDS",
    "THRESHOLDS_PATH",
    "VERDICTS",
    "load_thresholds",
    "measure",
    "route",
    "route_name",
]
