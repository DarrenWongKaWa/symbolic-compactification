"""Typed public boundary for verifier-in-the-loop representation search.

The boundary is deliberately narrower than a search implementation.  S6 may
consume states from enumeration, beam search, or a synthetic control, but it
never receives evaluator targets or hidden reference programs.  The only
scientific feedback returned to an expander is one of the four frozen outcome
classes.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.program_ir import (
    CompileContext,
    RepresentationProgram,
    canonical_json,
    canonical_program_hash,
)
from research.representation_program_search.program_ir.model import (
    freeze_json,
    thaw_json,
)

FEEDBACK_VALUES = frozenset({"ZERO", "NONZERO", "UNKNOWN", "COMPILE_FAILURE"})
FIXED_STATE_BUDGETS = (10, 50, 100, 500, 1000)
LEAKAGE_STATUSES = frozenset({"CLEARED", "FOUND", "UNKNOWN"})
ASSUMPTION_CLEARANCE_STATUSES = frozenset({"CLEARED", "INCOMPLETE", "UNKNOWN"})
POLICY_VERSION = "RPSVerifierSearchPolicyV1"
EVALUATION_CONDITIONS = frozenset({
    "S0", "S1", "S2", "S2_MATCHED_BATCH32", "S3", "S4", "S5", "S6",
    "S6_MATCHED_BATCH32", "S7", "F0",
})

# These keys name evaluator-only information.  Values are intentionally not
# scanned: a scientific expression can legitimately contain words such as
# "target" in an opaque source identifier.  Ordering cannot reference a
# forbidden key at any nesting depth.
_FORBIDDEN_PUBLIC_KEYS = frozenset({
    "answer",
    "evaluator",
    "expected_success",
    "expected_verdict",
    "gold",
    "gold_operator_sequence",
    "gold_program",
    "hidden_member_roles",
    "reference_program",
    "target_representation",
    "target_representation_type",
})


class FrontierContractError(ValueError):
    """Stable fail-closed error at the method-neutral frontier boundary."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _scan_public_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key).lower() in _FORBIDDEN_PUBLIC_KEYS:
                raise FrontierContractError(
                    f"HIDDEN_EVALUATOR_FIELD:{str(key).lower()}"
                )
            _scan_public_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _scan_public_keys(child)


def _priority_item(value: Any) -> bool:
    return (
        isinstance(value, int) and not isinstance(value, bool)
    ) or isinstance(value, str)


@dataclass(frozen=True)
class VerifierFrontierNode:
    """One public search state adapted to an executable M1 program.

    ``public_state`` owns duplicate identity and must contain only proposer-
    visible material.  Ancestry, wall time, evaluator labels, and verifier
    traces do not enter the state hash.  ``public_priority`` is similarly
    syntax-only and cannot contain floats or opaque Python objects.
    """

    program: RepresentationProgram
    context: CompileContext
    public_state: Mapping[str, Any]
    complexity: int
    depth: int
    public_priority: tuple[int | str, ...] = ()
    leakage_status: str = "UNKNOWN"
    assumption_clearance: str = "UNKNOWN"
    label: str | None = None
    parent_hash: str | None = None
    action_from_parent: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.complexity, int) or isinstance(self.complexity, bool):
            raise FrontierContractError("STATE_COMPLEXITY_INVALID")
        if not isinstance(self.depth, int) or isinstance(self.depth, bool):
            raise FrontierContractError("STATE_DEPTH_INVALID")
        if self.complexity < 0 or self.depth < 0:
            raise FrontierContractError("STATE_METRIC_NEGATIVE")
        if self.leakage_status not in LEAKAGE_STATUSES:
            raise FrontierContractError("LEAKAGE_STATUS_INVALID")
        if self.assumption_clearance not in ASSUMPTION_CLEARANCE_STATUSES:
            raise FrontierContractError("ASSUMPTION_CLEARANCE_INVALID")
        if not all(_priority_item(item) for item in self.public_priority):
            raise FrontierContractError("PUBLIC_PRIORITY_INVALID")
        try:
            frozen = freeze_json(self.public_state)
        except TypeError as exc:
            raise FrontierContractError("PUBLIC_STATE_NOT_JSON") from exc
        if not isinstance(frozen, Mapping):
            raise FrontierContractError("PUBLIC_STATE_NOT_OBJECT")
        _scan_public_keys(frozen)
        object.__setattr__(self, "public_state", frozen)
        if self.action_from_parent is not None:
            try:
                frozen_action = freeze_json(self.action_from_parent)
            except TypeError as exc:
                raise FrontierContractError("ACTION_NOT_JSON") from exc
            if not isinstance(frozen_action, Mapping):
                raise FrontierContractError("ACTION_NOT_OBJECT")
            _scan_public_keys(frozen_action)
            object.__setattr__(self, "action_from_parent", frozen_action)

    @classmethod
    def from_program(
        cls,
        program: RepresentationProgram,
        context: CompileContext,
        *,
        complexity: int,
        depth: int,
        public_priority: tuple[int | str, ...] = (),
        leakage_status: str = "UNKNOWN",
        assumption_clearance: str = "UNKNOWN",
        label: str | None = None,
        parent_hash: str | None = None,
        action_from_parent: Mapping[str, Any] | None = None,
    ) -> "VerifierFrontierNode":
        """Create a minimal public node without search-engine coupling."""
        return cls(
            program=program,
            context=context,
            public_state={
                "grammar_id": context.grammar_id,
                "program_id": canonical_program_hash(program),
            },
            complexity=complexity,
            depth=depth,
            public_priority=public_priority,
            leakage_status=leakage_status,
            assumption_clearance=assumption_clearance,
            label=label,
            parent_hash=parent_hash,
            action_from_parent=action_from_parent,
        )

    @property
    def canonical_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(thaw_json(self.public_state)).encode("utf-8")
        ).hexdigest()

    @property
    def program_id(self) -> str:
        return canonical_program_hash(self.program)

    @property
    def complete(self) -> bool:
        source_ids = {item.member_id for item in self.program.source_members}
        assigned_ids = {item.member_id for item in self.program.member_assignments}
        return not self.program.unexplained_members and assigned_ids == source_ids

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "action_from_parent": (
                None
                if self.action_from_parent is None
                else thaw_json(self.action_from_parent)
            ),
            "canonical_hash": self.canonical_hash,
            "assumption_clearance": self.assumption_clearance,
            "complexity": self.complexity,
            "depth": self.depth,
            "grammar_id": self.context.grammar_id,
            "leakage_status": self.leakage_status,
            "parent_hash": self.parent_hash,
            "program_id": self.program_id,
            "public_priority": list(self.public_priority),
            "public_state": thaw_json(self.public_state),
        }


@dataclass(frozen=True)
class VerifierSearchPolicy:
    """Frozen S6 state ordering and retention semantics."""

    version: str = POLICY_VERSION
    initial_priority_band: int = 1
    zero_successor_band: int = 0
    nonzero_successor_band: int = 1
    compile_failure_successor_band: int = 1
    unknown_successor_band: int = 2
    continue_after_success: bool = True

    def __post_init__(self) -> None:
        if self.version != POLICY_VERSION:
            raise FrontierContractError("VERIFIER_SEARCH_POLICY_UNKNOWN")
        bands = (
            self.initial_priority_band,
            self.zero_successor_band,
            self.nonzero_successor_band,
            self.compile_failure_successor_band,
            self.unknown_successor_band,
        )
        if any(not isinstance(item, int) or isinstance(item, bool) or item < 0 for item in bands):
            raise FrontierContractError("VERIFIER_SEARCH_POLICY_INVALID")
        if self.unknown_successor_band <= self.initial_priority_band:
            raise FrontierContractError("UNKNOWN_PRIORITY_NOT_LOWER")

    def band_for_feedback(self, feedback: str) -> int:
        if feedback not in FEEDBACK_VALUES:
            raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")
        return {
            "ZERO": self.zero_successor_band,
            "NONZERO": self.nonzero_successor_band,
            "UNKNOWN": self.unknown_successor_band,
            "COMPILE_FAILURE": self.compile_failure_successor_band,
        }[feedback]

    def to_dict(self) -> dict[str, Any]:
        return {
            "compile_failure_successor_band": self.compile_failure_successor_band,
            "continue_after_success": self.continue_after_success,
            "initial_priority_band": self.initial_priority_band,
            "nonzero_successor_band": self.nonzero_successor_band,
            "unknown_successor_band": self.unknown_successor_band,
            "version": self.version,
            "zero_successor_band": self.zero_successor_band,
        }


@dataclass(frozen=True)
class VerifierSearchResult:
    """Immutable summary of one fixed-state-budget exact-evaluation run."""

    condition: str
    budget_requested: int
    states_expanded: int
    frontier_exhausted: bool
    first_success_index: int | None
    successful_state_hashes: tuple[str, ...]
    retained_unknown_state_hashes: tuple[str, ...]
    duplicate_states_pruned: int
    disposition_counts: Mapping[str, int]
    feedback_counts: Mapping[str, int]
    obligation_verdict_counts: Mapping[str, int]
    success_at: Mapping[str, bool | None]
    decision_hashes: tuple[str, ...]
    trace_hash: str
    semantic_decision_hashes: tuple[str, ...]
    semantic_trace_hash: str
    wall_time_seconds: float
    time_to_first_success_seconds: float | None
    llm_tokens_used: int
    output_root: str
    policy: VerifierSearchPolicy = field(default_factory=VerifierSearchPolicy)

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget_requested": self.budget_requested,
            "condition": self.condition,
            "decision_hashes": list(self.decision_hashes),
            "disposition_counts": dict(self.disposition_counts),
            "duplicate_states_pruned": self.duplicate_states_pruned,
            "feedback_counts": dict(self.feedback_counts),
            "first_success_index": self.first_success_index,
            "frontier_exhausted": self.frontier_exhausted,
            "llm_tokens_used": self.llm_tokens_used,
            "obligation_verdict_counts": dict(self.obligation_verdict_counts),
            "output_root": self.output_root,
            "policy": self.policy.to_dict(),
            "retained_unknown_state_hashes": list(
                self.retained_unknown_state_hashes
            ),
            "semantic_decision_hashes": list(self.semantic_decision_hashes),
            "semantic_trace_hash": self.semantic_trace_hash,
            "states_expanded": self.states_expanded,
            "success_at": dict(self.success_at),
            "successful_state_hashes": list(self.successful_state_hashes),
            "trace_hash": self.trace_hash,
            "time_to_first_success_seconds": self.time_to_first_success_seconds,
            "wall_time_seconds": self.wall_time_seconds,
        }
