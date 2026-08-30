"""Method-neutral search execution records."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .actions import SearchPolicy
from .candidates import CandidatePool
from .model import SearchState
from .public_case import PublicCase


@dataclass(frozen=True)
class ExpansionRecord:
    expansion_index: int
    state_hash: str
    complexity: int
    depth: int
    legal_child_hashes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "complexity": self.complexity,
            "depth": self.depth,
            "expansion_index": self.expansion_index,
            "legal_child_hashes": list(self.legal_child_hashes),
            "state_hash": self.state_hash,
        }


@dataclass(frozen=True)
class SearchResult:
    condition: str
    case_id: str
    grammar_id: str
    budget_requested: int
    states_expanded: int
    frontier_exhausted: bool
    seed: int | None
    wall_time_seconds: float
    expanded_states: tuple[SearchState, ...]
    expansion_trace: tuple[ExpansionRecord, ...]
    duplicate_states_pruned: int
    rejection_counts: Mapping[str, int]
    candidate_pool: CandidatePool
    policy: SearchPolicy
    public_case_manifest: Mapping[str, Any]
    ordering_uses_verifier_outcomes: bool = False
    generated_frontier_exhaustive: bool = True
    global_expression_enumeration_claimed: bool = False
    llm_tokens: int = 0

    def __post_init__(self) -> None:
        if self.states_expanded != len(self.expanded_states):
            raise ValueError("SEARCH_RESULT_EXPANSION_COUNT_MISMATCH")
        if self.states_expanded != len(self.expansion_trace):
            raise ValueError("SEARCH_RESULT_TRACE_COUNT_MISMATCH")

    def to_dict(self, *, include_states: bool = False) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "branching_incomplete": self.candidate_pool.branching_incomplete,
            "budget_requested": self.budget_requested,
            "candidate_pool_hash": self.candidate_pool.canonical_hash,
            "case_id": self.case_id,
            "condition": self.condition,
            "duplicate_states_pruned": self.duplicate_states_pruned,
            "expansion_trace": [item.to_dict() for item in self.expansion_trace],
            "frontier_exhausted": self.frontier_exhausted,
            "generated_frontier_exhaustive": self.generated_frontier_exhaustive,
            "global_expression_enumeration_claimed": self.global_expression_enumeration_claimed,
            "grammar_id": self.grammar_id,
            "llm_tokens": self.llm_tokens,
            "ordering_uses_verifier_outcomes": self.ordering_uses_verifier_outcomes,
            "policy": self.policy.to_dict(),
            "public_case_manifest": dict(self.public_case_manifest),
            "rejection_counts": dict(self.rejection_counts),
            "seed": self.seed,
            "states_expanded": self.states_expanded,
            "wall_time_seconds": self.wall_time_seconds,
        }
        if include_states:
            payload["expanded_states"] = [item.to_dict() for item in self.expanded_states]
        return payload


def public_manifest(case: PublicCase) -> Mapping[str, Any]:
    return case.public_manifest()
