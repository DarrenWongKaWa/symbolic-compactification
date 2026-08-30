"""S2 deterministic symbolic-heuristic beam search."""
from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.grammar_v1 import BUDGET_STATES

from .actions import SearchPolicy, expand_state, initial_state
from .beam_policy import (
    BATCHED_BEAM_MERGE_POLICY_VERSION,
    CROSS_PARENT_PRIORITY_FIELDS,
    MATCHED_LAYER_BEAM_WIDTH,
    MATCHED_PER_PARENT_BATCH_SIZE,
    cross_parent_rank_key,
)
from .candidates import CandidatePool, extract_candidate_pool
from .model import SearchContractError, SearchState
from .public_case import PublicCase
from .results import ExpansionRecord, SearchResult, public_manifest
from .symbolic_heuristic import (
    SYMBOLIC_HEURISTIC_VERSION,
    SymbolicObservations,
    SymbolicPriority,
    extract_symbolic_observations,
    symbolic_priority,
    symbolic_priority_key,
)

SYMBOLIC_BEAM_POLICY_VERSION = "RPSSymbolicBeamPolicyV1"
SYMBOLIC_BEAM_WIDTH = 32
SYMBOLIC_MATCHED_BATCH_POLICY_VERSION = "RPSSymbolicMatchedBatch32PolicyV1"
SYMBOLIC_MATCHED_BATCH_CONDITION = "S2_MATCHED_BATCH32"


@dataclass(frozen=True)
class BeamLayerRecord:
    depth: int
    candidate_state_hashes: tuple[str, ...]
    selected_state_hashes: tuple[str, ...]
    pruned_state_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_state_hashes": list(self.candidate_state_hashes),
            "depth": self.depth,
            "pruned_state_count": self.pruned_state_count,
            "selected_state_hashes": list(self.selected_state_hashes),
        }


@dataclass(frozen=True)
class PriorityRecord:
    state_hash: str
    priority: SymbolicPriority

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority.to_dict(),
            "state_hash": self.state_hash,
        }


@dataclass(frozen=True)
class MatchedParentBatchRecord:
    parent_state_hash: str
    parent_depth: int
    all_legal_child_count: int
    presented_child_hashes: tuple[str, ...]
    locally_ranked_child_hashes: tuple[str, ...]
    batch_pruned_state_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_legal_child_count": self.all_legal_child_count,
            "batch_pruned_state_count": self.batch_pruned_state_count,
            "locally_ranked_child_hashes": list(self.locally_ranked_child_hashes),
            "parent_depth": self.parent_depth,
            "parent_state_hash": self.parent_state_hash,
            "presented_child_hashes": list(self.presented_child_hashes),
        }


@dataclass(frozen=True)
class SymbolicBeamResult(SearchResult):
    heuristic_version: str = SYMBOLIC_HEURISTIC_VERSION
    beam_policy_version: str = SYMBOLIC_BEAM_POLICY_VERSION
    beam_width: int = SYMBOLIC_BEAM_WIDTH
    beam_states_pruned: int = 0
    observations: SymbolicObservations | None = None
    priority_records: tuple[PriorityRecord, ...] = ()
    beam_layers: tuple[BeamLayerRecord, ...] = ()
    beam_search_complete: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.condition != "S2":
            raise ValueError("SYMBOLIC_BEAM_CONDITION_INVALID")
        if self.beam_width != SYMBOLIC_BEAM_WIDTH:
            raise ValueError("SYMBOLIC_BEAM_WIDTH_NOT_FROZEN")
        if self.ordering_uses_verifier_outcomes:
            raise ValueError("SYMBOLIC_BEAM_VERIFIER_ORDERING_FORBIDDEN")

    def to_dict(self, *, include_states: bool = False) -> dict[str, Any]:
        payload = super().to_dict(include_states=include_states)
        payload.update({
            "beam_layers": [item.to_dict() for item in self.beam_layers],
            "beam_policy_version": self.beam_policy_version,
            "beam_search_complete": self.beam_search_complete,
            "beam_states_pruned": self.beam_states_pruned,
            "beam_width": self.beam_width,
            "heuristic_version": self.heuristic_version,
            "observations": (
                None if self.observations is None else self.observations.to_dict()
            ),
            "observations_hash": (
                None if self.observations is None else self.observations.canonical_hash
            ),
            "priority_records": [item.to_dict() for item in self.priority_records],
        })
        return payload


@dataclass(frozen=True)
class MatchedSymbolicBeamResult(SearchResult):
    """Diagnostic S2 over the exact S4/S5 batched search frontier."""

    heuristic_version: str = SYMBOLIC_HEURISTIC_VERSION
    matched_batch_policy_version: str = SYMBOLIC_MATCHED_BATCH_POLICY_VERSION
    merge_policy_version: str = BATCHED_BEAM_MERGE_POLICY_VERSION
    batch_size: int = MATCHED_PER_PARENT_BATCH_SIZE
    beam_width: int = MATCHED_LAYER_BEAM_WIDTH
    batch_states_pruned: int = 0
    beam_states_pruned: int = 0
    observations: SymbolicObservations | None = None
    priority_records: tuple[PriorityRecord, ...] = ()
    parent_batches: tuple[MatchedParentBatchRecord, ...] = ()
    beam_layers: tuple[BeamLayerRecord, ...] = ()
    beam_search_complete: bool = False
    frontier_matched_to_s4_s5: bool = True
    strongest_symbolic_baseline: bool = False
    replaces_full_frontier_s2: bool = False
    symbolic_comparison_status: str = "MATCHED_BATCH32_DIAGNOSTIC_CONTROL"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.condition != SYMBOLIC_MATCHED_BATCH_CONDITION:
            raise ValueError("SYMBOLIC_MATCHED_BATCH_CONDITION_INVALID")
        if (
            self.batch_size != MATCHED_PER_PARENT_BATCH_SIZE
            or self.beam_width != MATCHED_LAYER_BEAM_WIDTH
        ):
            raise ValueError("SYMBOLIC_MATCHED_BATCH_POLICY_NOT_FROZEN")
        if self.merge_policy_version != BATCHED_BEAM_MERGE_POLICY_VERSION:
            raise ValueError("SYMBOLIC_MATCHED_MERGE_POLICY_NOT_FROZEN")
        if self.ordering_uses_verifier_outcomes or self.llm_tokens:
            raise ValueError("SYMBOLIC_MATCHED_CAUSAL_BOUNDARY_INVALID")
        if not self.frontier_matched_to_s4_s5:
            raise ValueError("SYMBOLIC_MATCHED_FRONTIER_FLAG_INVALID")
        if self.strongest_symbolic_baseline or self.replaces_full_frontier_s2:
            raise ValueError("SYMBOLIC_MATCHED_CANNOT_REPLACE_FULL_S2")

    def to_dict(self, *, include_states: bool = False) -> dict[str, Any]:
        payload = super().to_dict(include_states=include_states)
        payload.update({
            "batch_size": self.batch_size,
            "batch_states_pruned": self.batch_states_pruned,
            "beam_layers": [item.to_dict() for item in self.beam_layers],
            "beam_search_complete": self.beam_search_complete,
            "beam_states_pruned": self.beam_states_pruned,
            "beam_width": self.beam_width,
            "cross_parent_priority": list(CROSS_PARENT_PRIORITY_FIELDS),
            "frontier_matched_to_s4_s5": self.frontier_matched_to_s4_s5,
            "heuristic_version": self.heuristic_version,
            "matched_batch_policy_version": self.matched_batch_policy_version,
            "merge_policy_version": self.merge_policy_version,
            "observations": (
                None if self.observations is None else self.observations.to_dict()
            ),
            "observations_hash": (
                None if self.observations is None else self.observations.canonical_hash
            ),
            "parent_batches": [item.to_dict() for item in self.parent_batches],
            "priority_records": [item.to_dict() for item in self.priority_records],
            "replaces_full_frontier_s2": self.replaces_full_frontier_s2,
            "strongest_symbolic_baseline": self.strongest_symbolic_baseline,
            "symbolic_comparison_status": self.symbolic_comparison_status,
        })
        return payload


def symbolic_beam_search(
    case: PublicCase,
    *,
    budget: int,
    grammar_id: str = "G_FULL",
    candidate_pool: CandidatePool | None = None,
    policy: SearchPolicy | None = None,
) -> SymbolicBeamResult:
    """Run the frozen layer-wise beam over the shared legal child frontier."""
    if budget not in BUDGET_STATES:
        raise SearchContractError(f"STATE_BUDGET_NOT_FROZEN:{budget}")
    started = time.perf_counter()
    pool = candidate_pool or extract_candidate_pool(case)
    frozen_policy = policy or SearchPolicy()
    observations = extract_symbolic_observations(case, pool)
    root = initial_state(case, grammar_id=grammar_id)
    layer: tuple[SearchState, ...] = (root,)
    expanded: list[SearchState] = []
    expanded_hashes: set[str] = set()
    trace: list[ExpansionRecord] = []
    priority_records: list[PriorityRecord] = []
    beam_layers: list[BeamLayerRecord] = []
    rejection_counts: Counter[str] = Counter()
    duplicates = 0
    beam_pruned = 0
    stopped_for_budget = False

    while layer and len(expanded) < budget:
        ranked_layer = tuple(sorted(
            layer,
            key=lambda state: symbolic_priority_key(
                state, case, pool, observations
            ),
        ))
        next_candidates: dict[str, SearchState] = {}
        for state in ranked_layer:
            if len(expanded) >= budget:
                stopped_for_budget = True
                break
            state_hash = state.canonical_hash
            if state_hash in expanded_hashes:
                duplicates += 1
                continue
            priority_records.append(PriorityRecord(
                state_hash=state_hash,
                priority=symbolic_priority(state, case, pool, observations),
            ))
            expansion = expand_state(state, case, pool, frozen_policy)
            expanded.append(state)
            expanded_hashes.add(state_hash)
            trace.append(ExpansionRecord(
                expansion_index=len(expanded),
                state_hash=state_hash,
                complexity=state.complexity,
                depth=state.depth,
                legal_child_hashes=tuple(
                    item.canonical_hash for item in expansion.children
                ),
            ))
            rejection_counts.update(expansion.rejected)
            for child in expansion.children:
                child_hash = child.canonical_hash
                if child_hash in expanded_hashes:
                    duplicates += 1
                    continue
                if child_hash in next_candidates:
                    duplicates += 1
                    continue
                next_candidates[child_hash] = child

        if stopped_for_budget:
            break
        ranked_candidates = tuple(sorted(
            next_candidates.values(),
            key=lambda state: symbolic_priority_key(
                state, case, pool, observations
            ),
        ))
        selected = ranked_candidates[:SYMBOLIC_BEAM_WIDTH]
        pruned = max(0, len(ranked_candidates) - len(selected))
        beam_pruned += pruned
        beam_layers.append(BeamLayerRecord(
            depth=(selected[0].depth if selected else ranked_layer[0].depth + 1),
            candidate_state_hashes=tuple(
                item.canonical_hash for item in ranked_candidates
            ),
            selected_state_hashes=tuple(item.canonical_hash for item in selected),
            pruned_state_count=pruned,
        ))
        layer = selected

    # Exhaustion is relative to the frozen beam policy.  It is never a claim
    # that the finite candidate pool, let alone the expression grammar, was
    # exhaustively searched.
    beam_exhausted = not layer and not stopped_for_budget
    return SymbolicBeamResult(
        condition="S2",
        case_id=case.case_id,
        grammar_id=grammar_id,
        budget_requested=budget,
        states_expanded=len(expanded),
        frontier_exhausted=beam_exhausted,
        seed=None,
        wall_time_seconds=time.perf_counter() - started,
        expanded_states=tuple(expanded),
        expansion_trace=tuple(trace),
        duplicate_states_pruned=duplicates,
        rejection_counts=MappingProxyType(dict(sorted(rejection_counts.items()))),
        candidate_pool=pool,
        policy=frozen_policy,
        public_case_manifest=public_manifest(case),
        ordering_uses_verifier_outcomes=False,
        generated_frontier_exhaustive=True,
        global_expression_enumeration_claimed=False,
        llm_tokens=0,
        beam_states_pruned=beam_pruned,
        observations=observations,
        priority_records=tuple(priority_records),
        beam_layers=tuple(beam_layers),
        beam_search_complete=False,
    )


def symbolic_matched_batch32_search(
    case: PublicCase,
    *,
    budget: int,
    grammar_id: str = "G_FULL",
    candidate_pool: CandidatePool | None = None,
    policy: SearchPolicy | None = None,
) -> MatchedSymbolicBeamResult:
    """Run symbolic ranking on S4/S5's first-32-per-parent frontier.

    This is a causal diagnostic only.  ``symbolic_beam_search`` remains the
    stronger full-generated-frontier S2 baseline.
    """
    if budget not in BUDGET_STATES:
        raise SearchContractError(f"STATE_BUDGET_NOT_FROZEN:{budget}")
    started = time.perf_counter()
    pool = candidate_pool or extract_candidate_pool(case)
    frozen_policy = policy or SearchPolicy()
    if frozen_policy != SearchPolicy(
        latent_creation_enabled=frozen_policy.latent_creation_enabled
    ):
        raise SearchContractError("SYMBOLIC_MATCHED_SEARCH_POLICY_NOT_FROZEN")
    observations = extract_symbolic_observations(case, pool)
    root = initial_state(case, grammar_id=grammar_id)
    layer: tuple[SearchState, ...] = (root,)
    expanded: list[SearchState] = []
    expanded_hashes: set[str] = set()
    trace: list[ExpansionRecord] = []
    priority_records: list[PriorityRecord] = []
    parent_batches: list[MatchedParentBatchRecord] = []
    beam_layers: list[BeamLayerRecord] = []
    rejection_counts: Counter[str] = Counter()
    duplicates = 0
    batch_pruned = 0
    beam_pruned = 0
    stopped_for_budget = False

    while layer and len(expanded) < budget:
        next_candidates: dict[str, tuple[tuple[int, str, str], SearchState]] = {}
        for state in layer:
            if len(expanded) >= budget:
                stopped_for_budget = True
                break
            state_hash = state.canonical_hash
            if state_hash in expanded_hashes:
                duplicates += 1
                continue
            priority_records.append(PriorityRecord(
                state_hash=state_hash,
                priority=symbolic_priority(state, case, pool, observations),
            ))
            expansion = expand_state(state, case, pool, frozen_policy)
            expanded.append(state)
            expanded_hashes.add(state_hash)
            trace.append(ExpansionRecord(
                expansion_index=len(expanded),
                state_hash=state_hash,
                complexity=state.complexity,
                depth=state.depth,
                legal_child_hashes=tuple(
                    item.canonical_hash for item in expansion.children
                ),
            ))
            rejection_counts.update(expansion.rejected)
            if not expansion.children:
                continue
            presented = expansion.children[:MATCHED_PER_PARENT_BATCH_SIZE]
            locally_ranked = tuple(sorted(
                presented,
                key=lambda child: symbolic_priority_key(
                    child, case, pool, observations
                ),
            ))
            pruned = len(expansion.children) - len(presented)
            batch_pruned += pruned
            parent_batches.append(MatchedParentBatchRecord(
                parent_state_hash=state_hash,
                parent_depth=state.depth,
                all_legal_child_count=len(expansion.children),
                presented_child_hashes=tuple(
                    child.canonical_hash for child in presented
                ),
                locally_ranked_child_hashes=tuple(
                    child.canonical_hash for child in locally_ranked
                ),
                batch_pruned_state_count=pruned,
            ))
            for local_rank, child in enumerate(locally_ranked):
                child_hash = child.canonical_hash
                if child_hash in expanded_hashes:
                    duplicates += 1
                    continue
                key = cross_parent_rank_key(local_rank, state_hash, child_hash)
                prior = next_candidates.get(child_hash)
                if prior is None or key < prior[0]:
                    if prior is not None:
                        duplicates += 1
                    next_candidates[child_hash] = (key, child)
                else:
                    duplicates += 1

        if stopped_for_budget:
            break
        ranked_candidates = tuple(
            item[1]
            for item in sorted(next_candidates.values(), key=lambda item: item[0])
        )
        selected = ranked_candidates[:MATCHED_LAYER_BEAM_WIDTH]
        pruned = max(0, len(ranked_candidates) - len(selected))
        beam_pruned += pruned
        beam_layers.append(BeamLayerRecord(
            depth=(selected[0].depth if selected else layer[0].depth + 1),
            candidate_state_hashes=tuple(
                item.canonical_hash for item in ranked_candidates
            ),
            selected_state_hashes=tuple(item.canonical_hash for item in selected),
            pruned_state_count=pruned,
        ))
        layer = selected

    beam_exhausted = not layer and not stopped_for_budget
    return MatchedSymbolicBeamResult(
        condition=SYMBOLIC_MATCHED_BATCH_CONDITION,
        case_id=case.case_id,
        grammar_id=grammar_id,
        budget_requested=budget,
        states_expanded=len(expanded),
        frontier_exhausted=beam_exhausted,
        seed=None,
        wall_time_seconds=time.perf_counter() - started,
        expanded_states=tuple(expanded),
        expansion_trace=tuple(trace),
        duplicate_states_pruned=duplicates,
        rejection_counts=MappingProxyType(dict(sorted(rejection_counts.items()))),
        candidate_pool=pool,
        policy=frozen_policy,
        public_case_manifest=public_manifest(case),
        ordering_uses_verifier_outcomes=False,
        generated_frontier_exhaustive=True,
        global_expression_enumeration_claimed=False,
        llm_tokens=0,
        batch_states_pruned=batch_pruned,
        beam_states_pruned=beam_pruned,
        observations=observations,
        priority_records=tuple(priority_records),
        parent_batches=tuple(parent_batches),
        beam_layers=tuple(beam_layers),
        beam_search_complete=False,
    )
