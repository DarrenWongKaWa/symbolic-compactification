from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

from research.representation_program_search.search import (
    ExpansionRecord,
    SearchPolicy,
    SearchResult,
    apply_action,
    extract_candidate_pool,
    initial_state,
    legal_actions,
    load_public_case,
)
from research.representation_program_search.search.results import public_manifest
from research.representation_program_search.verifier_search import (
    FrontierContractError,
    nodes_from_search_result,
    verify_search_result_posthoc,
)


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(tmp_path: Path):
    members = []
    for member_id, expression in (("A001", "exp(x)"), ("A002", "exp(y)")):
        relative = f"members/{member_id}.txt"
        members.append({
            "member_id": member_id,
            "path": relative,
            "sha256": _text(tmp_path / relative, expression),
        })
    symbols_hash = _json(tmp_path / "symbols.json", {"symbols": ["x", "y"]})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "POSTHOC_SYNTHETIC",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_hash,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def _search_result(tmp_path: Path, *, condition: str = "S1", llm_tokens: int = 0):
    case = _case(tmp_path)
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    root = initial_state(case, grammar_id="G_FULL")
    create = next(
        action
        for action in legal_actions(root, case, pool, policy)
        if action.action == "CREATE_LATENT"
        and action.payload["candidate_id"]
        == next(
            item.candidate_id
            for item in pool.latents
            if item.extraction == "PAIRWISE_ANTI_UNIFICATION"
        )
    )
    latent = apply_action(root, create, case)
    add_first = next(
        action
        for action in legal_actions(latent, case, pool, policy)
        if action.action == "ADD_MEMBER" and action.payload.get("member_id") == "A001"
        and "latent_id" in action.payload
    )
    one = apply_action(latent, add_first, case)
    add_second = next(
        action
        for action in legal_actions(one, case, pool, policy)
        if action.action == "ADD_MEMBER" and action.payload.get("member_id") == "A002"
        and "latent_id" in action.payload
    )
    complete = apply_action(one, add_second, case)
    states = (root, latent, one, complete)
    trace = tuple(
        ExpansionRecord(index, state.canonical_hash, state.complexity, state.depth, ())
        for index, state in enumerate(states, start=1)
    )
    result = SearchResult(
        condition=condition,
        case_id=case.case_id,
        grammar_id="G_FULL",
        budget_requested=10,
        states_expanded=len(states),
        frontier_exhausted=True,
        seed=None,
        wall_time_seconds=0.0,
        expanded_states=states,
        expansion_trace=trace,
        duplicate_states_pruned=0,
        rejection_counts={},
        candidate_pool=pool,
        policy=policy,
        public_case_manifest=public_manifest(case),
        llm_tokens=llm_tokens,
    )
    return case, result


def test_posthoc_exactly_preserves_search_order_and_certifies_complete_state(tmp_path):
    case, result = _search_result(tmp_path / "case")
    nodes = nodes_from_search_result(
        result,
        case,
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    assert [node.public_priority for node in nodes] == [(1,), (2,), (3,), (4,)]
    assert [node.public_state["search_state_hash"] for node in nodes] == [
        state.canonical_hash for state in result.expanded_states
    ]

    output = tmp_path / "evaluation"
    evaluated = verify_search_result_posthoc(
        result,
        case,
        output_root=output,
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    assert evaluated.condition == "S1"
    assert evaluated.states_expanded == 4
    assert evaluated.first_success_index == 4
    assert evaluated.obligation_verdict_counts["ZERO"] == 2
    controller = json.loads((output / "controller.json").read_text())
    assert controller["condition"] == "S1"
    assert controller["feedback_guides_successors"] is False
    decisions = [
        json.loads(path.read_text())
        for path in sorted((output / "decisions").glob("*.json"))
    ]
    assert [
        row["node"]["public_state"]["search_state_hash"] for row in decisions
    ] == [state.canonical_hash for state in result.expanded_states]


def test_posthoc_clearances_default_unknown_and_prevent_false_success(tmp_path):
    case, result = _search_result(tmp_path / "case")
    output = tmp_path / "evaluation"
    evaluated = verify_search_result_posthoc(result, case, output_root=output)
    assert evaluated.first_success_index is None
    final = json.loads(sorted((output / "decisions").glob("*.json"))[-1].read_text())
    assert final["evaluation"]["reason"] == (
        "ASSUMPTION_CLEARANCE_NOT_ESTABLISHED"
    )
    assert not list((output / "states").glob("*/obligations/*"))


def test_posthoc_retains_llm_token_accounting_without_feedback(tmp_path):
    case, result = _search_result(tmp_path / "case", condition="S4", llm_tokens=37)
    evaluated = verify_search_result_posthoc(
        result,
        case,
        output_root=tmp_path / "evaluation",
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    assert evaluated.condition == "S4"
    assert evaluated.llm_tokens_used == 37
    assert evaluated.first_success_index == 4


def test_posthoc_rejects_public_case_drift(tmp_path):
    case, result = _search_result(tmp_path / "case")
    drifted = replace(result, case_id="OTHER")
    import pytest

    with pytest.raises(FrontierContractError, match="SEARCH_RESULT_CASE_MISMATCH"):
        nodes_from_search_result(drifted, case)
