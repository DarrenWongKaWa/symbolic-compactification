"""S3 deterministic search over the exact M2 legal frontier."""
from __future__ import annotations

import heapq
import time
from collections import Counter
from pathlib import Path

from research.representation_program_search.grammar_v1 import BUDGET_STATES
from research.representation_program_search.search import (
    CandidatePool,
    ExpansionRecord,
    PublicCase,
    SearchContractError,
    SearchPolicy,
    SearchResult,
    SearchState,
    expand_state,
    extract_candidate_pool,
    initial_state,
)
from research.representation_program_search.search.results import public_manifest

from .heuristic import SOLPriorityPolicy, route_legal_child
from .model import SOLRoutingDecision, SOLSearchResult
from .projection import load_sol_projection


def sol_conditioned_search(
    case: PublicCase,
    *,
    budget: int,
    artifact_path: str | Path,
    artifact_sha256: str,
    grammar_id: str = "G_FULL",
    candidate_pool: CandidatePool | None = None,
    policy: SearchPolicy | None = None,
    priority_policy: SOLPriorityPolicy | None = None,
) -> SOLSearchResult:
    """Run S3, or return an explicit no-run unavailable SOL record."""
    if budget not in BUDGET_STATES:
        raise SearchContractError(f"STATE_BUDGET_NOT_FROZEN:{budget}")
    pool = candidate_pool or extract_candidate_pool(case)
    frozen_policy = policy or SearchPolicy()
    sol_policy = priority_policy or SOLPriorityPolicy()
    projection = load_sol_projection(
        case,
        artifact_path,
        expected_sha256=artifact_sha256,
    )
    if projection.status != "AVAILABLE":
        return SOLSearchResult(
            projection=projection,
            budget_requested=budget,
            grammar_id=grammar_id,
            candidate_pool_hash=pool.canonical_hash,
            search_result=None,
            priority_policy_version=sol_policy.version,
        )

    started = time.perf_counter()
    root = initial_state(case, grammar_id=grammar_id)
    # key = (-cumulative SOL units, frozen complexity, depth, canonical hash)
    root_key = (0, root.complexity, root.depth, root.canonical_hash)
    frontier: list[tuple[tuple[int, int, int, str], int, SearchState]] = [
        (root_key, 0, root)
    ]
    queued: dict[str, tuple[int, int, int, str]] = {root.canonical_hash: root_key}
    priority_by_hash = {root.canonical_hash: 0}
    expanded: list[SearchState] = []
    expanded_hashes: set[str] = set()
    trace: list[ExpansionRecord] = []
    routing: list[SOLRoutingDecision] = []
    rejection_counts: Counter[str] = Counter()
    duplicates = 0
    serial = 1

    while frontier and len(expanded) < budget:
        key, _serial, state = heapq.heappop(frontier)
        state_hash = state.canonical_hash
        if queued.get(state_hash) != key:
            duplicates += 1
            continue
        queued.pop(state_hash, None)
        if state_hash in expanded_hashes:
            duplicates += 1
            continue
        state_priority = priority_by_hash[state_hash]
        expansion = expand_state(state, case, pool, frozen_policy)
        expanded.append(state)
        expanded_hashes.add(state_hash)
        trace.append(ExpansionRecord(
            expansion_index=len(expanded),
            state_hash=state_hash,
            complexity=state.complexity,
            depth=state.depth,
            legal_child_hashes=tuple(item.canonical_hash for item in expansion.children),
        ))
        rejection_counts.update(expansion.rejected)
        for child, action in zip(expansion.children, expansion.actions):
            decision = route_legal_child(
                projection,
                parent=state,
                action=action,
                child=child,
                candidate_pool=pool,
                parent_priority=state_priority,
            )
            routing.append(decision)
            child_hash = child.canonical_hash
            if child_hash in expanded_hashes:
                duplicates += 1
                continue
            child_key = (
                -decision.child_priority,
                child.complexity,
                child.depth,
                child_hash,
            )
            previous = queued.get(child_hash)
            if previous is not None and previous <= child_key:
                duplicates += 1
                continue
            if previous is not None:
                duplicates += 1
            queued[child_hash] = child_key
            priority_by_hash[child_hash] = decision.child_priority
            heapq.heappush(frontier, (child_key, serial, child))
            serial += 1

    result = SearchResult(
        condition="S3",
        case_id=case.case_id,
        grammar_id=grammar_id,
        budget_requested=budget,
        states_expanded=len(expanded),
        frontier_exhausted=not queued,
        seed=None,
        wall_time_seconds=time.perf_counter() - started,
        expanded_states=tuple(expanded),
        expansion_trace=tuple(trace),
        duplicate_states_pruned=duplicates,
        rejection_counts=dict(sorted(rejection_counts.items())),
        candidate_pool=pool,
        policy=frozen_policy,
        public_case_manifest=public_manifest(case),
        ordering_uses_verifier_outcomes=False,
        llm_tokens=0,
    )
    return SOLSearchResult(
        projection=projection,
        budget_requested=budget,
        grammar_id=grammar_id,
        candidate_pool_hash=pool.canonical_hash,
        search_result=result,
        routing_decisions=tuple(routing),
        priority_policy_version=sol_policy.version,
    )
