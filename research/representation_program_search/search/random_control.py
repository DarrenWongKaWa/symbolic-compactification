"""S0 seeded random control over the exact S1-generated state frontier."""
from __future__ import annotations

import random
import time
from collections import Counter

from research.representation_program_search.grammar_v1 import BUDGET_STATES

from .actions import SearchPolicy, expand_state, initial_state
from .candidates import CandidatePool, extract_candidate_pool
from .model import SearchContractError, SearchState
from .public_case import PublicCase
from .results import ExpansionRecord, SearchResult, public_manifest


def random_search(
    case: PublicCase,
    *,
    budget: int,
    seed: int,
    grammar_id: str = "G_FULL",
    candidate_pool: CandidatePool | None = None,
    policy: SearchPolicy | None = None,
) -> SearchResult:
    """Uniformly sample the next state from the same legal frontier as S1."""
    if budget not in BUDGET_STATES:
        raise SearchContractError(f"STATE_BUDGET_NOT_FROZEN:{budget}")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise SearchContractError("RANDOM_SEED_INVALID")
    started = time.perf_counter()
    pool = candidate_pool or extract_candidate_pool(case)
    frozen_policy = policy or SearchPolicy()
    root = initial_state(case, grammar_id=grammar_id)
    frontier: list[SearchState] = [root]
    queued = {root.canonical_hash}
    expanded: list[SearchState] = []
    expanded_hashes: set[str] = set()
    trace: list[ExpansionRecord] = []
    rejection_counts: Counter[str] = Counter()
    duplicates = 0
    rng = random.Random(seed)

    while frontier and len(expanded) < budget:
        index = rng.randrange(len(frontier))
        state = frontier.pop(index)
        state_hash = state.canonical_hash
        queued.discard(state_hash)
        if state_hash in expanded_hashes:
            duplicates += 1
            continue
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
        for child in expansion.children:
            child_hash = child.canonical_hash
            if child_hash in expanded_hashes or child_hash in queued:
                duplicates += 1
                continue
            frontier.append(child)
            queued.add(child_hash)

    return SearchResult(
        condition="S0",
        case_id=case.case_id,
        grammar_id=grammar_id,
        budget_requested=budget,
        states_expanded=len(expanded),
        frontier_exhausted=not frontier,
        seed=seed,
        wall_time_seconds=time.perf_counter() - started,
        expanded_states=tuple(expanded),
        expansion_trace=tuple(trace),
        duplicate_states_pruned=duplicates,
        rejection_counts=dict(sorted(rejection_counts.items())),
        candidate_pool=pool,
        policy=frozen_policy,
        public_case_manifest=public_manifest(case),
    )
