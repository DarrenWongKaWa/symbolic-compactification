from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.search import (
    CandidatePool,
    SearchPolicy,
    expand_state,
    extract_candidate_pool,
    initial_state,
    load_public_case,
)
from research.representation_program_search.verifier_search import (
    FrontierContractError,
    M2VerifierFrontierAdapter,
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
    symbols_sha = _json(tmp_path / "symbols.json", {"symbols": ["x", "y"]})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "M2_S6_SYNTHETIC",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def test_adapter_exposes_exact_m2_children_and_actions(tmp_path):
    case = _case(tmp_path)
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    state = initial_state(case, grammar_id="G_FULL")
    expected = expand_state(state, case, pool, policy)
    adapter = M2VerifierFrontierAdapter(
        case,
        candidate_pool=pool,
        search_policy=policy,
        leakage_status="CLEARED",
    )
    root = adapter.initial_node()
    children = adapter.expand(root, None)

    assert [item.public_state["search_state_hash"] for item in children] == [
        item.canonical_hash for item in expected.children
    ]
    assert [item.to_public_dict()["action_from_parent"] for item in children] == [
        item.to_dict() for item in expected.actions
    ]
    assert all(item.parent_hash == root.canonical_hash for item in children)
    assert adapter.public_contract()["successor_generation"] == (
        "M2_EXPAND_STATE_UNCHANGED"
    )


def test_feedback_does_not_mutate_the_legal_frontier(tmp_path):
    case = _case(tmp_path)
    adapter = M2VerifierFrontierAdapter(case, leakage_status="CLEARED")
    root = adapter.initial_node()
    baseline = [item.canonical_hash for item in adapter.expand(root, None)]
    for feedback in ("ZERO", "NONZERO", "UNKNOWN", "COMPILE_FAILURE"):
        assert [
            item.canonical_hash for item in adapter.expand(root, feedback)
        ] == baseline
    with pytest.raises(FrontierContractError, match="FEEDBACK_UNKNOWN"):
        adapter.expand(root, "APPROXIMATE")


def test_leakage_clearance_is_never_inferred(tmp_path):
    case = _case(tmp_path)
    assert M2VerifierFrontierAdapter(case).initial_node().leakage_status == "UNKNOWN"
    assert M2VerifierFrontierAdapter(
        case, leakage_status="CLEARED"
    ).initial_node().leakage_status == "CLEARED"


def test_adapter_rejects_candidate_pool_from_another_case(tmp_path):
    case = _case(tmp_path / "left")
    other = _case(tmp_path / "right")
    base = extract_candidate_pool(other)
    bad = CandidatePool(
        policy_version=base.policy_version,
        latents=base.latents,
        node_values=base.node_values,
        coefficients=base.coefficients,
        branching_incomplete=base.branching_incomplete,
        incompleteness_reasons=base.incompleteness_reasons,
        source_member_count=1,
    )
    with pytest.raises(FrontierContractError, match="CANDIDATE_POOL_CASE_MISMATCH"):
        M2VerifierFrontierAdapter(case, candidate_pool=bad)
