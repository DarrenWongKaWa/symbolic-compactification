"""Typed confluence / limit engine (Track V3).

Cascade; timeout and size-guard are UNKNOWN, never ZERO.
"""
from research.scalable_verification.confluence.engine import (
    LIMIT_MODE,
    LIMIT_OPS_CAP,
    LIMIT_SECONDS,
    ConfluenceResult,
    check_limit,
)

__all__ = [
    "ConfluenceResult",
    "check_limit",
    "LIMIT_MODE",
    "LIMIT_OPS_CAP",
    "LIMIT_SECONDS",
]
