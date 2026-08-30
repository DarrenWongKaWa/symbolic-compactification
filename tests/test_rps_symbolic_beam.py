from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

import research.representation_program_search.program_ir as program_ir
import research.representation_program_search.search.symbolic_heuristic as heuristic
import symbolic_compactification
from research.representation_program_search.search import (
    BATCHED_BEAM_MERGE_POLICY_VERSION,
    CROSS_PARENT_PRIORITY_FIELDS,
    LLM_BATCH_SIZE,
    LLM_BEAM_WIDTH,
    LLM_PRIMARY_MODEL,
    SYMBOLIC_MATCHED_BATCH_CONDITION,
    DeepSeekSearchConfig,
    LatentCandidate,
    llm_state_ranking_search,
    SYMBOLIC_BEAM_WIDTH,
    ObligationEvidence,
    SearchContractError,
    SearchPolicy,
    apply_action,
    expand_state,
    extract_candidate_pool,
    extract_symbolic_observations,
    initial_state,
    legal_actions,
    load_public_case,
    symbolic_beam_search,
    symbolic_matched_batch32_search,
    symbolic_priority,
)
from research.representation_program_search.program_ir import NodeStructure, Operator


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(tmp_path: Path) -> Path:
    expressions = (
        "f(x)/(x + a)**2",
        "f(y)/(y + a)**3",
        "f(x)/(x + a)**2",
    )
    members = []
    for index, expression in enumerate(expressions, 1):
        member_id = f"A{index:03d}"
        relative = f"members/{member_id}.txt"
        members.append({
            "member_id": member_id,
            "path": relative,
            "sha256": _text(tmp_path / relative, expression),
        })
    symbols_sha256 = _json(
        tmp_path / "symbols.json", {"symbols": ["a", "x", "y"]}
    )
    _json(tmp_path / "reference" / "program.json", {"gold": "forbidden"})
    _json(tmp_path / "verification" / "receipt.json", {"verdict": "ZERO"})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "SYNTHETIC_SYMBOLIC_BEAM",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha256,
        },
    })
    return tmp_path / "proposer_view.json"


def _created_shared_state(case, pool):
    root = initial_state(case, grammar_id="G_FULL")
    shared_ids = {
        item.candidate_id
        for item in pool.latents
        if item.extraction == "PAIRWISE_ANTI_UNIFICATION"
        and len(item.public_origins) >= 2
    }
    action = next(
        item for item in legal_actions(root, case, pool, SearchPolicy())
        if item.action == "CREATE_LATENT"
        and item.payload["candidate_id"] in shared_ids
    )
    return apply_action(root, action, case)


def _widened_pool(case):
    original = extract_candidate_pool(case)
    latents = tuple(
        LatentCandidate(
            candidate_id=f"LC_MATCHED_{index:02d}",
            form="FUNCTION_1",
            parameters=("rps_p0",),
            expression=f"rps_p0 + {index}",
            public_origins=("A001", "A002"),
            instance_maps=(
                ("A001", (("rps_p0", "x"),)),
                ("A002", (("rps_p0", "y"),)),
            ),
            extraction="PAIRWISE_ANTI_UNIFICATION",
        )
        for index in range(24)
    )
    return replace(original, latents=latents)


class _MatchedSymbolicRankingTransport:
    """Mock S4 ranking that replays the diagnostic's local symbolic ranks."""

    def __init__(self, parent_batches):
        self._rankings = {
            item.parent_state_hash: item.locally_ranked_child_hashes
            for item in parent_batches
        }
        self.requests = []

    def complete(self, request):
        self.requests.append(request)
        user = json.loads(request["messages"][1]["content"])
        parent_hash = user["current_search_state"]["state_hash"]
        by_hash = {
            item["state"]["state_hash"]: item["opaque_id"]
            for item in user["candidates"]
        }
        ranking = [by_hash[item] for item in self._rankings[parent_hash]]
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({"ranking": ranking})},
            }],
            "id": f"matched-{len(self.requests)}",
            "model": LLM_PRIMARY_MODEL,
            "usage": {
                "completion_tokens": 5,
                "completion_tokens_details": {"reasoning_tokens": 2},
                "prompt_cache_hit_tokens": 1,
                "prompt_cache_miss_tokens": 9,
                "prompt_tokens": 10,
                "total_tokens": 15,
            },
        }


def test_s2_replays_deterministically_and_matches_root_legal_frontier(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    root = initial_state(case, grammar_id="G_FULL")
    expected = tuple(
        item.canonical_hash for item in expand_state(root, case, pool, policy).children
    )
    first = symbolic_beam_search(
        case, budget=50, candidate_pool=pool, policy=policy
    )
    replay = symbolic_beam_search(
        case, budget=50, candidate_pool=pool, policy=policy
    )
    assert first.expansion_trace[0].legal_child_hashes == expected
    assert [item.canonical_hash for item in first.expanded_states] == [
        item.canonical_hash for item in replay.expanded_states
    ]
    assert [item.to_dict() for item in first.priority_records] == [
        item.to_dict() for item in replay.priority_records
    ]
    assert [item.to_dict() for item in first.beam_layers] == [
        item.to_dict() for item in replay.beam_layers
    ]
    assert first.beam_width == SYMBOLIC_BEAM_WIDTH == 32
    assert first.ordering_uses_verifier_outcomes is False
    assert first.llm_tokens == 0


def test_s2_budget_is_exact_when_frontier_remains_and_invalid_budget_fails(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    for budget in (10, 50):
        result = symbolic_beam_search(case, budget=budget)
        assert result.states_expanded == budget
        assert [item.expansion_index for item in result.expansion_trace] == list(
            range(1, budget + 1)
        )
        assert result.wall_time_seconds >= 0
        assert result.llm_tokens == 0
    with pytest.raises(SearchContractError, match="STATE_BUDGET_NOT_FROZEN"):
        symbolic_beam_search(case, budget=11)


def test_symbolic_observations_and_priority_rank_structure_not_target_labels(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    observations = extract_symbolic_observations(case, pool)
    assert ("A001", "A002") in observations.argument_family_edges
    assert ("A001", "A002") in observations.denominator_family_edges
    assert ("A001", "A002") in observations.derivative_edges
    assert ("A001", "A003") in observations.symmetry_edges
    assert "x" in observations.repeated_node_values

    root = initial_state(case, grammar_id="G_FULL")
    shared = _created_shared_state(case, pool)
    literal_action = next(
        item for item in legal_actions(root, case, pool, SearchPolicy())
        if item.action == "CREATE_LATENT"
        and next(
            candidate for candidate in pool.latents
            if candidate.candidate_id == item.payload["candidate_id"]
        ).role == "TAUTOLOGY_CONTROL"
    )
    literal = apply_action(root, literal_action, case)
    shared_priority = symbolic_priority(shared, case, pool, observations)
    literal_priority = symbolic_priority(literal, case, pool, observations)
    assert shared_priority.features["relation_support"] >= 1
    assert literal_priority.features["tautology_control_latent"] == 1
    assert shared_priority.total > literal_priority.total
    assert not ({"target", "gold", "verdict", "audited_depth"} & set(
        shared_priority.features
    ))

    supported_node = replace(
        shared,
        node_structures=(NodeStructure("N_SUPPORTED", ("x", "x")),),
    )
    distractor_node = replace(
        shared,
        node_structures=(NodeStructure("N_DISTRACTOR", ("z", "z")),),
    )
    assert symbolic_priority(
        supported_node, case, pool, observations
    ).total > symbolic_priority(
        distractor_node, case, pool, observations
    ).total

    latent_id = shared.latent_objects[0].latent_id
    derivative = replace(shared, operators=(Operator(
        "OP_D", "DERIVATIVE", "out_d", latent_id, (),
        {"order": 1, "variable": shared.latent_objects[0].parameters[0]},
    ),), complexity=5)
    neutral = replace(shared, operators=(Operator(
        "OP_S", "SHIFT", "out_s", latent_id, (), {"offset": "1"},
    ),), complexity=5)
    assert symbolic_priority(
        derivative, case, pool, observations
    ).features["derivative_edge_match"] == 1
    assert symbolic_priority(
        derivative, case, pool, observations
    ).total > symbolic_priority(neutral, case, pool, observations).total


def test_relation_extractors_do_not_mutate_shared_trees_or_depend_on_order(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    public_expressions = tuple(member.expression for member in case.members)
    tree = heuristic._tree(public_expressions[0])
    assert tree is not None
    original = ast.dump(tree, include_attributes=True)

    denominator_first = heuristic._denominator_families(tree)
    assert ast.dump(tree, include_attributes=True) == original
    power_second = heuristic._power_profile(tree)
    assert ast.dump(tree, include_attributes=True) == original

    replay_tree = heuristic._tree(public_expressions[0])
    assert replay_tree is not None
    power_first = heuristic._power_profile(replay_tree)
    denominator_second = heuristic._denominator_families(replay_tree)
    assert ast.dump(replay_tree, include_attributes=True) == original
    assert denominator_first == denominator_second
    assert power_first == power_second

    first = extract_symbolic_observations(case, pool)
    second = extract_symbolic_observations(case, pool)
    assert first == second
    assert tuple(member.expression for member in case.members) == public_expressions


def test_s2_never_calls_evaluator_loader_or_verifier(tmp_path, monkeypatch):
    case = load_public_case(_fixture(tmp_path))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("evaluator/verifier boundary crossed")

    monkeypatch.setattr(program_ir, "load_case_package", forbidden)
    monkeypatch.setattr(symbolic_compactification, "verify_equivalent", forbidden)
    result = symbolic_beam_search(case, budget=10)
    matched = symbolic_matched_batch32_search(case, budget=10)
    assert result.states_expanded == 10
    assert matched.states_expanded == 10
    for search_result in (result, matched):
        assert all(
            "reference" not in item and "verification" not in item
            for item in search_result.public_case_manifest["accessed_paths"]
        )


def test_unknown_and_nonzero_evidence_cannot_change_symbolic_order(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    observations = extract_symbolic_observations(case, pool)
    state = _created_shared_state(case, pool)
    unknown = replace(state, verified_obligations=(
        ObligationEvidence("OBL_SYNTH", "UNKNOWN"),
    ))
    nonzero = replace(state, verified_obligations=(
        ObligationEvidence("OBL_SYNTH", "NONZERO"),
    ))
    assert symbolic_priority(state, case, pool, observations) == symbolic_priority(
        unknown, case, pool, observations
    )
    assert symbolic_priority(state, case, pool, observations) == symbolic_priority(
        nonzero, case, pool, observations
    )
    assert state.canonical_hash == unknown.canonical_hash == nonzero.canonical_hash


@pytest.mark.parametrize("grammar_id", ["G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"])
def test_s2_uses_frozen_grammar_ablations_and_latent_ablation(tmp_path, grammar_id):
    case = load_public_case(_fixture(tmp_path))
    result = symbolic_beam_search(case, budget=10, grammar_id=grammar_id)
    assert result.grammar_id == grammar_id
    assert all(item.grammar_id == grammar_id for item in result.expanded_states)
    disabled = symbolic_beam_search(
        case,
        budget=10,
        grammar_id=grammar_id,
        policy=SearchPolicy(latent_creation_enabled=False),
    )
    assert disabled.states_expanded == 1
    assert disabled.frontier_exhausted is True


def test_primitive_frontier_and_priority_preserve_cross_latent_compose(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    pool = extract_candidate_pool(case)
    policy = SearchPolicy()
    candidates = [
        item for item in pool.latents
        if item.role == "SEARCH_CANDIDATE"
        and len(item.parameters) == 1
        and item.instance_maps
    ]
    assert len(candidates) >= 2
    state = initial_state(case, grammar_id="G_PRIMITIVE")
    for candidate in candidates[:2]:
        create = next(
            item for item in legal_actions(state, case, pool, policy)
            if item.action == "CREATE_LATENT"
            and item.payload["candidate_id"] == candidate.candidate_id
        )
        state = apply_action(state, create, case)
        member_id = next(
            member_id for member_id, _values in candidate.instance_maps
            if member_id in state.unexplained_members
        )
        assign = next(
            item for item in legal_actions(state, case, pool, policy)
            if item.action == "ADD_MEMBER"
            and item.payload.get("member_id") == member_id
            and item.payload.get("latent_id") == f"F_{candidate.candidate_id}"
        )
        state = apply_action(state, assign, case)

    first_output = state.member_assignments[0].output
    second_latent = state.latent_objects[1].latent_id
    compose = next(
        item for item in legal_actions(state, case, pool, policy)
        if item.action == "ADD_COMPOSE"
        and item.payload["latent_id"] == second_latent
        and tuple(item.payload["inputs"]) == (first_output,)
    )
    composed = apply_action(state, compose, case)
    assert composed.operators[-1].operator == "COMPOSE"
    assert symbolic_priority(
        composed, case, pool
    ).features["cross_latent_compose"] == 1


def test_s2_reports_candidate_pool_and_beam_incompleteness(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    result = symbolic_beam_search(case, budget=50)
    payload = result.to_dict()
    assert payload["branching_incomplete"] is True
    assert payload["beam_search_complete"] is False
    assert payload["global_expression_enumeration_claimed"] is False
    assert payload["generated_frontier_exhaustive"] is True
    assert payload["observations_hash"] == result.observations.canonical_hash
    assert payload["beam_states_pruned"] > 0
    assert any(item["pruned_state_count"] > 0 for item in payload["beam_layers"])


def test_s2_matched_batch32_exactly_matches_s4_presented_frontier_and_merge(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))
    pool = _widened_pool(case)
    matched = symbolic_matched_batch32_search(
        case,
        budget=50,
        candidate_pool=pool,
    )
    transport = _MatchedSymbolicRankingTransport(matched.parent_batches)
    llm = llm_state_ranking_search(
        case,
        budget=50,
        candidate_pool=pool,
        transport=transport,
        decision_directory=tmp_path / "s4",
        config=DeepSeekSearchConfig(seed_label="seed-0"),
    )

    assert [item.canonical_hash for item in matched.expanded_states] == [
        item.canonical_hash for item in llm.expanded_states
    ]
    assert len(matched.parent_batches) == len(llm.decision_records)
    for batch, frozen_record in zip(matched.parent_batches, llm.decision_records):
        record = dict(frozen_record)
        assert batch.parent_state_hash == record["current_state_hash"]
        llm_presented = tuple(
            item["state"]["state_hash"]
            for item in record["candidate_batch"]["candidate_records"]
        )
        assert batch.presented_child_hashes == llm_presented
        opaque_to_hash = {
            item["opaque_id"]: item["state"]["state_hash"]
            for item in record["candidate_batch"]["candidate_records"]
        }
        assert batch.locally_ranked_child_hashes == tuple(
            opaque_to_hash[item] for item in record["ranking_used"]
        )
        assert batch.all_legal_child_count == record["candidate_batch"][
            "all_legal_child_count"
        ]
        assert batch.batch_pruned_state_count == record["candidate_batch"][
            "batch_pruned_count"
        ]

    assert len(matched.beam_layers) == len(llm.llm_layer_records)
    for symbolic_layer, llm_layer in zip(
        matched.beam_layers, llm.llm_layer_records
    ):
        assert symbolic_layer.candidate_state_hashes == (
            llm_layer.candidate_state_hashes
        )
        assert symbolic_layer.selected_state_hashes == llm_layer.selected_state_hashes
        assert symbolic_layer.pruned_state_count == llm_layer.beam_pruned_state_count

    payload = matched.to_dict()
    assert payload["condition"] == SYMBOLIC_MATCHED_BATCH_CONDITION
    assert payload["batch_size"] == LLM_BATCH_SIZE == 32
    assert payload["beam_width"] == LLM_BEAM_WIDTH == 32
    assert payload["merge_policy_version"] == BATCHED_BEAM_MERGE_POLICY_VERSION
    assert payload["cross_parent_priority"] == list(CROSS_PARENT_PRIORITY_FIELDS)
    assert payload["frontier_matched_to_s4_s5"] is True
    assert payload["symbolic_comparison_status"] == (
        "MATCHED_BATCH32_DIAGNOSTIC_CONTROL"
    )


def test_s2_matched_is_deterministic_incomplete_and_does_not_replace_full_s2(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))
    pool = _widened_pool(case)
    first = symbolic_matched_batch32_search(case, budget=50, candidate_pool=pool)
    replay = symbolic_matched_batch32_search(case, budget=50, candidate_pool=pool)
    full = symbolic_beam_search(case, budget=50, candidate_pool=pool)

    assert [item.canonical_hash for item in first.expanded_states] == [
        item.canonical_hash for item in replay.expanded_states
    ]
    assert [item.to_dict() for item in first.parent_batches] == [
        item.to_dict() for item in replay.parent_batches
    ]
    assert [item.to_dict() for item in first.beam_layers] == [
        item.to_dict() for item in replay.beam_layers
    ]
    assert first.parent_batches[0].all_legal_child_count > LLM_BATCH_SIZE
    assert len(first.parent_batches[0].presented_child_hashes) == LLM_BATCH_SIZE
    assert first.batch_states_pruned > 0
    assert first.beam_search_complete is False
    assert first.global_expression_enumeration_claimed is False
    assert first.strongest_symbolic_baseline is False
    assert first.replaces_full_frontier_s2 is False
    assert full.condition == "S2"
    assert len(full.expansion_trace[0].legal_child_hashes) == (
        first.parent_batches[0].all_legal_child_count
    )
    assert set(full.beam_layers[0].candidate_state_hashes) > set(
        first.parent_batches[0].presented_child_hashes
    )


@pytest.mark.parametrize("grammar_id", ["G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"])
def test_s2_matched_uses_frozen_budgets_grammar_and_latent_ablation(
    tmp_path, grammar_id
):
    case = load_public_case(_fixture(tmp_path / grammar_id))
    result = symbolic_matched_batch32_search(
        case,
        budget=10,
        grammar_id=grammar_id,
    )
    assert result.states_expanded == 10
    assert result.grammar_id == grammar_id
    assert result.llm_tokens == 0
    disabled = symbolic_matched_batch32_search(
        case,
        budget=10,
        grammar_id=grammar_id,
        policy=SearchPolicy(latent_creation_enabled=False),
    )
    assert disabled.states_expanded == 1
    assert disabled.frontier_exhausted is True

    with pytest.raises(SearchContractError, match="STATE_BUDGET_NOT_FROZEN"):
        symbolic_matched_batch32_search(case, budget=11, grammar_id=grammar_id)
    with pytest.raises(
        SearchContractError, match="SYMBOLIC_MATCHED_SEARCH_POLICY_NOT_FROZEN"
    ):
        symbolic_matched_batch32_search(
            case,
            budget=10,
            grammar_id=grammar_id,
            policy=SearchPolicy(max_complexity=23),
        )
