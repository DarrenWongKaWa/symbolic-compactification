"""Exact post-hoc adjudication for search methods without verifier feedback."""
from __future__ import annotations

from pathlib import Path

from research.representation_program_search.search import PublicCase, SearchResult

from .controller import verifier_search
from .model import (
    ASSUMPTION_CLEARANCE_STATUSES,
    EVALUATION_CONDITIONS,
    LEAKAGE_STATUSES,
    FrontierContractError,
    VerifierFrontierNode,
    VerifierSearchResult,
)


def nodes_from_search_result(
    result: SearchResult,
    case: PublicCase,
    *,
    leakage_status: str = "UNKNOWN",
    assumption_clearance: str = "UNKNOWN",
) -> tuple[VerifierFrontierNode, ...]:
    """Preserve the recorded search expansion order as evaluator nodes.

    This function does not infer either scientific clearance.  Both values
    must be supplied from independent, hash-bound audits before a complete
    program is eligible for verifier invocation.
    """
    if result.condition not in EVALUATION_CONDITIONS:
        raise FrontierContractError("EVALUATION_CONDITION_UNKNOWN")
    if result.case_id != case.case_id:
        raise FrontierContractError("SEARCH_RESULT_CASE_MISMATCH")
    if result.grammar_id not in {"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"}:
        raise FrontierContractError("GRAMMAR_ABLATION_UNKNOWN")
    if leakage_status not in LEAKAGE_STATUSES:
        raise FrontierContractError("LEAKAGE_STATUS_INVALID")
    if assumption_clearance not in ASSUMPTION_CLEARANCE_STATUSES:
        raise FrontierContractError("ASSUMPTION_CLEARANCE_INVALID")
    public_hash = result.public_case_manifest.get("proposer_view_sha256")
    if public_hash != case.proposer_view_sha256:
        raise FrontierContractError("SEARCH_RESULT_PUBLIC_CASE_DRIFT")
    states = result.expanded_states
    if len({item.canonical_hash for item in states}) != len(states):
        raise FrontierContractError("SEARCH_RESULT_DUPLICATE_STATE")

    def make_node(state, index: int, parent_hash: str | None):
        return VerifierFrontierNode(
            program=state.to_program(
                source_members=case.source_members,
                assumption_statuses=case.assumption_statuses,
            ),
            context=case.compile_context(result.grammar_id),
            public_state={
                "candidate_pool_hash": result.candidate_pool.canonical_hash,
                "search_state": state.scientific_payload(),
                "search_state_hash": state.canonical_hash,
            },
            complexity=state.complexity,
            depth=state.depth,
            # Every node is inserted initially.  Expansion ordinal therefore
            # fixes the exact search order independently of verifier outcomes.
            public_priority=(index,),
            leakage_status=leakage_status,
            assumption_clearance=assumption_clearance,
            parent_hash=parent_hash,
            action_from_parent=(
                None
                if state.action_from_parent is None
                else state.action_from_parent.to_dict()
            ),
        )

    preliminary = tuple(
        make_node(state, index, None)
        for index, state in enumerate(states, start=1)
    )
    node_hash_by_state = {
        state.canonical_hash: node.canonical_hash
        for state, node in zip(states, preliminary)
    }
    nodes: list[VerifierFrontierNode] = []
    for index, state in enumerate(states, start=1):
        parent_hash = None
        if state.parent_hash is not None:
            parent_hash = node_hash_by_state.get(state.parent_hash)
            if parent_hash is None:
                raise FrontierContractError("SEARCH_PARENT_NOT_EXPANDED")
        nodes.append(make_node(state, index, parent_hash))
    return tuple(nodes)


def verify_search_result_posthoc(
    result: SearchResult,
    case: PublicCase,
    *,
    output_root: str | Path,
    leakage_status: str = "UNKNOWN",
    assumption_clearance: str = "UNKNOWN",
) -> VerifierSearchResult:
    """Adjudicate expanded states without exposing outcomes to the search."""
    nodes = nodes_from_search_result(
        result,
        case,
        leakage_status=leakage_status,
        assumption_clearance=assumption_clearance,
    )
    return verifier_search(
        nodes,
        output_root=output_root,
        budget=result.budget_requested,
        condition=result.condition,
        llm_tokens_used=result.llm_tokens,
        expander=None,
    )
