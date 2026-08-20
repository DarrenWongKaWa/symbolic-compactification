"""Stable verification-to-state-transition pipeline.

This module is the one authoritative path from an ingested candidate to a
recorded verdict and, only for a deterministically proven ZERO, promotion.
The CLI is an adapter over this API; it contains no certification policy.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import sympy

from .budgets import get_budget_policy
from .models import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PACKAGE_VERSION,
    ZERO,
    AdapterError,
    ExpressionRecord,
    SessionState,
    StepRecord,
    VerificationResult,
    derive_status_axes,
)
from .parser import get_parse_policy
from .session import promote, proposal_assumption_status, record_step
from .transforms import get_transform_policy
from .verifier import get_verify_policy, verify_equivalent

__all__ = ["StepOutcome", "adjudicate_candidate"]


@dataclass(frozen=True)
class StepOutcome:
    """The complete result of one candidate adjudication."""

    result: VerificationResult
    step: StepRecord
    step_path: Path
    promoted_path: Optional[Path]

    @property
    def promoted(self) -> bool:
        return self.promoted_path is not None


def _count_ops(record: ExpressionRecord) -> Optional[int]:
    if record.parsed_expr is None:
        return None
    try:
        return int(sympy.count_ops(record.parsed_expr, visual=False))
    except Exception:
        return None


def _policy_snapshot() -> dict:
    return {
        "parse": get_parse_policy(),
        "verify": get_verify_policy(),
        "transform": get_transform_policy(),
        "budget": get_budget_policy(),
    }


def _telemetry(current: ExpressionRecord, candidate: ExpressionRecord,
               result: VerificationResult) -> dict:
    timed_out = any(
        isinstance(item, dict)
        and item.get("kind") == "TIME_BUDGET_EXCEEDED"
        for item in result.evidence)
    payload = {
        "input_chars": len(current.text),
        "output_chars": len(candidate.text),
        "wall_time_seconds": result.seconds,
        "verdict": result.verdict,
        "timeout_status": (
            "TIME_BUDGET_EXCEEDED" if timed_out else "ok"),
        "primitive_reason": "CANDIDATE_EQUIVALENCE_VERIFICATION",
        "repository_version": PACKAGE_VERSION,
        "engine_version": ENGINE_VERSION,
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "policies": _policy_snapshot(),
    }
    before = _count_ops(current)
    after = _count_ops(candidate)
    if before is None:
        payload["count_ops_before_reason"] = "PARSE_UNAVAILABLE"
    else:
        payload["count_ops_before"] = before
    if after is None:
        payload["count_ops_after_reason"] = "PARSE_UNAVAILABLE"
    else:
        payload["count_ops_after"] = after
    return payload


def adjudicate_candidate(session: SessionState,
                         candidate: ExpressionRecord, *,
                         meta: Optional[dict] = None) -> StepOutcome:
    """Verify, record, and conditionally promote one candidate.

    The candidate must use the exact persisted symbol/function namespace of
    the current state. This prevents a step from silently changing scientific
    assumptions. Promotion is delegated to ``session.promote``, which binds
    the ZERO evidence to these exact current/candidate hashes and texts.
    """
    current = session.current
    if current is None:
        raise AdapterError("NO_CURRENT_EXPRESSION")
    if candidate.symbols != current.symbols:
        raise AdapterError("DECLARED_ASSUMPTIONS_CHANGED")
    if candidate.functions != current.functions:
        raise AdapterError("DECLARED_FUNCTIONS_CHANGED")
    if proposal_assumption_status(
            session, candidate.text) == "HUMAN_REQUIRED":
        raise AdapterError("HUMAN_AUTHORIZATION_REQUIRED")

    result = verify_equivalent(
        current.text,
        candidate.text,
        current.symbols,
        functions=current.functions or None,
    )
    assumption_status, proof_status = derive_status_axes(
        result.verdict, assumptions_status="DECLARED", adjudicated=True)
    step = StepRecord(
        step=len(session.steps) + 1,
        current_hash=current.sha256,
        candidate_hash=candidate.sha256,
        candidate_text=candidate.text,
        residual=result.simplified_residual or result.residual,
        verdict=result.verdict,
        evidence=list(result.evidence),
        status="CERTIFIED" if result.verdict == ZERO else "UNVERIFIED",
        telemetry=_telemetry(current, candidate, result),
        assumption_status=assumption_status,
        proof_status=proof_status,
    )
    step_path = record_step(session, step, meta=meta)
    promoted_path = (
        promote(session, candidate, meta=meta)
        if result.verdict == ZERO else None)
    return StepOutcome(
        result=result,
        step=step,
        step_path=step_path,
        promoted_path=promoted_path,
    )
