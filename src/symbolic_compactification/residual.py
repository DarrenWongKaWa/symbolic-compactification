"""Residual construction and session-recording helpers.

Kept deliberately small: the residual of (current, candidate) is just the
symbolic difference, and ``residual_record`` packages residual strings +
content hashes for the session layer.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy

from .models import ExpressionRecord, VerificationResult, sha256_text


def make_residual(current: sympy.Expr, candidate: sympy.Expr) -> sympy.Expr:
    """R := current - candidate (already-parsed sympy expressions)."""
    return current - candidate


def residual_record(current_rec: ExpressionRecord,
                    candidate_rec: ExpressionRecord,
                    result: Optional[VerificationResult]) -> dict:
    """Session-recording payload for one residual evaluation.

    Captures both input hashes, the residual strings and (when available) the
    verification verdict; everything is JSON-serializable.
    """
    record: dict[str, Any] = {
        "construction": "difference_current_minus_candidate",
        "current_sha256": current_rec.sha256,
        "candidate_sha256": candidate_rec.sha256,
        "residual": result.residual if result is not None else None,
        "simplified_residual": (result.simplified_residual
                                if result is not None else None),
        "verdict": result.verdict if result is not None else None,
    }
    if record["residual"] is not None:
        record["residual_sha256"] = sha256_text(record["residual"])
    else:
        record["residual_sha256"] = None
    return record
