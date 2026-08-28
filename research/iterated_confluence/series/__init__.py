"""Multivariate series CONTROL for iterated-limit toys.

This package is a control, not a verifier. It never certifies a family.
"""
from research.iterated_confluence.series.control import (
    COMPARED,
    OPS_CAP,
    UNKNOWN,
    iterated_limits,
    multivariate_control,
)

__all__ = [
    "OPS_CAP",
    "UNKNOWN",
    "COMPARED",
    "iterated_limits",
    "multivariate_control",
]
