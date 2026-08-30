"""Strict, result-hash-bound input records for RPS statistical reporting."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

FIXED_BUDGETS = (10, 50, 100, 500, 1000)
CONDITIONS = frozenset({"S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "F0"})
PARTITIONS = frozenset({"DEV", "TEST", "CHALLENGE", "HISTORICAL_DIAGNOSTIC"})
GRAMMARS = frozenset({"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"})
AVAILABILITY = frozenset({"AVAILABLE", "UNAVAILABLE"})


class EvaluationContractError(ValueError):
    """A run cannot enter a scientific denominator."""


def _sha256(value: str, field: str) -> str:
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise EvaluationContractError(f"{field.upper()}_INVALID")
    return value


def _optional_nonnegative(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvaluationContractError(f"{field.upper()}_INVALID")
    return value


@dataclass(frozen=True)
class EvaluationRun:
    """One independently admissible case/condition/seed/budget observation.

    An unavailable method is represented explicitly and is never converted to
    a failure.  Scientific admission and leakage clearance are mandatory for
    AVAILABLE records, preventing infrastructure diagnostics from entering a
    headline denominator.
    """

    run_id: str
    condition: str
    case_id: str
    cluster_id: str
    partition: str
    representation_depth: int
    grammar_id: str
    latent_creation_allowed: bool
    seed: int | None
    model: str | None
    budget_requested: int
    availability: str
    exclusion_reason: str | None
    admission_status: str
    leakage_status: str
    states_expanded: int | None
    first_success_index: int | None
    time_to_first_success_seconds: float | None
    tokens_to_first_success: int | None
    wall_time_seconds: float | None
    source_result_sha256: str
    search_trace_hash: str | None
    evidence_trace_hash: str | None

    def __post_init__(self) -> None:
        if not self.run_id or not self.case_id or not self.cluster_id:
            raise EvaluationContractError("RUN_IDENTITY_EMPTY")
        if self.condition not in CONDITIONS:
            raise EvaluationContractError("CONDITION_UNKNOWN")
        if self.partition not in PARTITIONS:
            raise EvaluationContractError("PARTITION_UNKNOWN")
        if self.grammar_id not in GRAMMARS:
            raise EvaluationContractError("GRAMMAR_UNKNOWN")
        if self.availability not in AVAILABILITY:
            raise EvaluationContractError("AVAILABILITY_UNKNOWN")
        if not isinstance(self.representation_depth, int) or isinstance(
            self.representation_depth, bool
        ) or not 0 <= self.representation_depth <= 8:
            raise EvaluationContractError("REPRESENTATION_DEPTH_INVALID")
        if not isinstance(self.budget_requested, int) or isinstance(
            self.budget_requested, bool
        ) or self.budget_requested not in FIXED_BUDGETS:
            raise EvaluationContractError("BUDGET_NOT_FROZEN")
        if self.seed is not None and (
            not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0
        ):
            raise EvaluationContractError("SEED_INVALID")
        _sha256(self.source_result_sha256, "source_result_sha256")
        if self.search_trace_hash is not None:
            _sha256(self.search_trace_hash, "search_trace_hash")
        if self.evidence_trace_hash is not None:
            _sha256(self.evidence_trace_hash, "evidence_trace_hash")
        for value, field in (
            (self.states_expanded, "states_expanded"),
            (self.first_success_index, "first_success_index"),
            (self.tokens_to_first_success, "tokens_to_first_success"),
        ):
            _optional_nonnegative(value, field)
        for value, field in (
            (self.time_to_first_success_seconds, "time_to_first_success_seconds"),
            (self.wall_time_seconds, "wall_time_seconds"),
        ):
            if value is not None and (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or value < 0
            ):
                raise EvaluationContractError(f"{field.upper()}_INVALID")

        if self.availability == "UNAVAILABLE":
            if not self.exclusion_reason:
                raise EvaluationContractError("UNAVAILABLE_REASON_REQUIRED")
            if any(
                value is not None
                for value in (
                    self.states_expanded,
                    self.first_success_index,
                    self.time_to_first_success_seconds,
                    self.tokens_to_first_success,
                    self.wall_time_seconds,
                )
            ):
                raise EvaluationContractError("UNAVAILABLE_HAS_RESULT")
            return

        if self.exclusion_reason is not None:
            raise EvaluationContractError("AVAILABLE_HAS_EXCLUSION_REASON")
        if self.admission_status != "ADMISSION_READY":
            raise EvaluationContractError("CASE_NOT_ADMISSION_READY")
        if self.leakage_status != "CLEARED":
            raise EvaluationContractError("LEAKAGE_NOT_CLEARED")
        if self.states_expanded is None or self.wall_time_seconds is None:
            raise EvaluationContractError("AVAILABLE_RESULT_INCOMPLETE")
        if self.states_expanded > self.budget_requested:
            raise EvaluationContractError("EXPANSIONS_EXCEED_BUDGET")
        if self.first_success_index is not None:
            if self.first_success_index < 1:
                raise EvaluationContractError("FIRST_SUCCESS_NOT_ONE_INDEXED")
            if self.first_success_index > self.states_expanded:
                raise EvaluationContractError("FIRST_SUCCESS_AFTER_TRACE")
            if self.time_to_first_success_seconds is None:
                raise EvaluationContractError("SUCCESS_TIME_MISSING")
        elif any(
            value is not None
            for value in (
                self.time_to_first_success_seconds,
                self.tokens_to_first_success,
            )
        ):
            raise EvaluationContractError("FAILURE_HAS_SUCCESS_METRIC")
        if self.condition in {"S4", "S5", "S7", "F0"} and self.model is None:
            raise EvaluationContractError("LLM_MODEL_MISSING")
        if self.condition in {"S0", "S1", "S2", "S3", "S6"} and self.model is not None:
            raise EvaluationContractError("NON_LLM_MODEL_SET")

    @property
    def program_success(self) -> bool:
        return self.availability == "AVAILABLE" and self.first_success_index is not None

    def success_at(self, budget: int) -> bool | None:
        if budget not in FIXED_BUDGETS:
            raise EvaluationContractError("BUDGET_NOT_FROZEN")
        if self.availability != "AVAILABLE" or budget > self.budget_requested:
            return None
        return self.first_success_index is not None and self.first_success_index <= budget

    def to_dict(self) -> dict[str, Any]:
        return {
            "admission_status": self.admission_status,
            "availability": self.availability,
            "budget_requested": self.budget_requested,
            "case_id": self.case_id,
            "cluster_id": self.cluster_id,
            "condition": self.condition,
            "evidence_trace_hash": self.evidence_trace_hash,
            "exclusion_reason": self.exclusion_reason,
            "first_success_index": self.first_success_index,
            "grammar_id": self.grammar_id,
            "latent_creation_allowed": self.latent_creation_allowed,
            "leakage_status": self.leakage_status,
            "model": self.model,
            "partition": self.partition,
            "representation_depth": self.representation_depth,
            "run_id": self.run_id,
            "search_trace_hash": self.search_trace_hash,
            "seed": self.seed,
            "source_result_sha256": self.source_result_sha256,
            "states_expanded": self.states_expanded,
            "time_to_first_success_seconds": self.time_to_first_success_seconds,
            "tokens_to_first_success": self.tokens_to_first_success,
            "wall_time_seconds": self.wall_time_seconds,
        }


def load_evaluation_run(value: Mapping[str, Any] | str | Path) -> EvaluationRun:
    if isinstance(value, (str, Path)):
        payload = json.loads(Path(value).read_text(encoding="utf-8"))
    else:
        payload = dict(value)
    if set(payload) != set(EvaluationRun.__dataclass_fields__):
        missing = sorted(set(EvaluationRun.__dataclass_fields__) - set(payload))
        extra = sorted(set(payload) - set(EvaluationRun.__dataclass_fields__))
        raise EvaluationContractError(f"RUN_SCHEMA_MISMATCH:missing={missing}:extra={extra}")
    return EvaluationRun(**payload)
