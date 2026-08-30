from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import research.llm_abstraction.client as old_llm_client
import research.representation_program_search.program_ir as program_ir
import symbolic_compactification
from research.representation_program_search.search import (
    BATCHED_BEAM_MERGE_POLICY_VERSION,
    CROSS_PARENT_PRIORITY_FIELDS,
    LLM_ALLOWED_MODELS,
    LLM_BATCH_SIZE,
    LLM_BEAM_WIDTH,
    LLM_PRIMARY_MODEL,
    LLM_REASONING_EFFORT,
    LLM_ROBUSTNESS_MODEL,
    LLM_SEED_LABELS,
    LLM_THINKING_TYPE,
    LLM_CAUSAL_REASON_FALLBACK,
    LLM_CAUSAL_REASON_INCOMPLETE_USAGE,
    LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    LLM_CAUSAL_STATUS_INVALID,
    LLM_CAUSAL_STATUS_VALID,
    DeepSeekSearchConfig,
    LatentCandidate,
    OpenAIChatCompletionsTransport,
    SearchContractError,
    SearchPolicy,
    build_ranking_request,
    call_and_validate_ranking,
    candidate_state_items,
    decision_record_hash,
    expand_state,
    extract_candidate_pool,
    initial_state,
    legal_action_items,
    llm_action_proposal_search,
    llm_state_ranking_search,
    load_public_case,
    public_state_payload,
)

PRIVATE_REASONING_SENTINEL = "PRIVATE_CHAIN_OF_THOUGHT_MUST_NOT_PERSIST"


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
    expressions = ("f(x) + 1", "f(y) + 1", "f(x + y) + 2")
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
        tmp_path / "symbols.json", {"symbols": ["x", "y"]}
    )
    _json(tmp_path / "reference" / "program.json", {"gold": "forbidden"})
    _json(tmp_path / "verification" / "receipt.json", {"verdict": "ZERO"})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "SYNTHETIC_LLM_SEARCH",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha256,
        },
    })
    return tmp_path / "proposer_view.json"


class MockRankingTransport:
    def __init__(self, *, mode: str = "reverse") -> None:
        self.mode = mode
        self.requests: list[dict] = []

    def complete(self, request):
        required_header = getattr(self, "required_header", None)
        if required_header is not None:
            assert Path(required_header).is_file()
        self.requests.append(dict(request))
        user = json.loads(request["messages"][1]["content"])
        identifiers = [item["opaque_id"] for item in user["candidates"]]
        if self.mode == "reverse":
            ranking: object = list(reversed(identifiers))
            body: object = {"ranking": ranking}
        elif self.mode == "unknown":
            body = {"ranking": identifiers[:-1] + ["UNKNOWN_ID"]}
        elif self.mode == "duplicate":
            body = {"ranking": identifiers[:-1] + [identifiers[0]]}
        elif self.mode == "missing":
            body = {"ranking": identifiers[:-1]}
        elif self.mode == "extra_field":
            body = {"ranking": identifiers, "explanation": "forbidden"}
        elif self.mode == "freeform":
            body = {"ranking": "I prefer the first candidate"}
        elif self.mode == "private_reasoning_field":
            body = {
                "ranking": identifiers,
                "reasoning_content": PRIVATE_REASONING_SENTINEL,
            }
        elif self.mode == "bad_json":
            body = None
        else:
            raise RuntimeError("synthetic transport failure")
        content = "not-json" if body is None else json.dumps(body)
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {
                    "content": content,
                    "reasoning_content": PRIVATE_REASONING_SENTINEL,
                    "reasoning_tail": PRIVATE_REASONING_SENTINEL,
                },
            }],
            "id": f"mock-request-{len(self.requests)}",
            "model": request["model"],
            "usage": {
                "completion_tokens": 5,
                "completion_tokens_details": {"reasoning_tokens": 2},
                "prompt_cache_hit_tokens": 1,
                "prompt_cache_miss_tokens": 9,
                "prompt_tokens": 10,
                "total_tokens": 15,
            },
        }


def _widened_pool(case):
    original = extract_candidate_pool(case)
    latents = tuple(
        LatentCandidate(
            candidate_id=f"LC_SYNTH_{index:02d}",
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


def _root_material(case, pool=None, grammar_id="G_FULL"):
    pool = pool or extract_candidate_pool(case)
    policy = SearchPolicy()
    root = initial_state(case, grammar_id=grammar_id)
    expansion = expand_state(root, case, pool, policy)
    return pool, policy, root, expansion


def test_deepseek_chat_completions_request_is_exactly_frozen(tmp_path):
    case = load_public_case(_fixture(tmp_path))
    _pool, _policy, root, expansion = _root_material(case)
    items = candidate_state_items(expansion.children[:2])
    for model in LLM_ALLOWED_MODELS:
        config = DeepSeekSearchConfig(model=model, seed_label="seed-3")
        assert config.seed == 3
        request = build_ranking_request(
            condition="S4",
            config=config,
            case=case,
            current_state=root,
            candidate_items=items,
        )
        assert request["model"] == model
        assert request["reasoning_effort"] == LLM_REASONING_EFFORT == "high"
        assert request["extra_body"] == {"thinking": {"type": "enabled"}}
        assert LLM_THINKING_TYPE == "enabled"
        assert request["response_format"] == {"type": "json_object"}
        assert request["stream"] is False
        assert "temperature" not in request and "top_p" not in request
        assert "JSON" in request["messages"][0]["content"]
    assert LLM_PRIMARY_MODEL == "deepseek-v4-pro"
    assert LLM_ROBUSTNESS_MODEL == "deepseek-v4-flash"
    assert len(LLM_SEED_LABELS) == 5
    assert [DeepSeekSearchConfig(seed_label=label).seed for label in LLM_SEED_LABELS] == [
        0, 1, 2, 3, 4,
    ]
    with pytest.raises(SearchContractError, match="LLM_MODEL_NOT_FROZEN"):
        DeepSeekSearchConfig(model="deepseek-chat")
    with pytest.raises(SearchContractError, match="LLM_SEED_LABEL_NOT_FROZEN"):
        DeepSeekSearchConfig(seed_label="best-seed")
    with pytest.raises(SearchContractError, match="LLM_REASONING_EFFORT_NOT_FROZEN"):
        DeepSeekSearchConfig(reasoning_effort="max")


def test_openai_compatible_transport_dispatches_chat_completions_without_live_call(monkeypatch):
    import openai

    captured = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured["request"] = kwargs
            return {"ok": True}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    secret = "sk-synthetic-secret-never-record"
    transport = OpenAIChatCompletionsTransport(api_key=secret)
    request = {
        "extra_body": {"thinking": {"type": "enabled"}},
        "messages": [{"role": "user", "content": "JSON"}],
        "model": LLM_PRIMARY_MODEL,
        "reasoning_effort": "high",
        "response_format": {"type": "json_object"},
    }
    assert transport.complete(request) == {"ok": True}
    assert captured["client"]["api_key"] == secret
    assert captured["client"]["base_url"] == "https://api.deepseek.com"
    assert captured["request"] == request
    assert secret not in json.dumps(captured["request"])


def test_response_projection_never_reads_or_persists_private_reasoning():
    transport = MockRankingTransport()
    expected = ("O_A", "O_B")
    request = {
        "messages": [{"role": "user", "content": "json"}],
        "model": LLM_PRIMARY_MODEL,
    }
    # Direct transport uses candidates from the user JSON.
    request["messages"][0]["content"] = json.dumps({
        "candidates": [{"opaque_id": item} for item in expected]
    })
    request["messages"].append(request["messages"].pop(0))
    # Mock expects the second message; retain a harmless system record.
    request["messages"].insert(0, {"role": "system", "content": "JSON"})
    response = call_and_validate_ranking(
        transport,
        request,
        expected_ids=expected,
        requested_model=LLM_PRIMARY_MODEL,
    )
    assert response.valid is True
    assert response.ranking == tuple(reversed(expected))
    assert response.usage.reasoning_tokens == 2
    blob = json.dumps(response.to_dict(), sort_keys=True)
    assert PRIVATE_REASONING_SENTINEL not in blob
    assert "reasoning_content" not in blob
    assert "reasoning_tail" not in blob


@pytest.mark.parametrize(
    ("mode", "error"),
    [
        ("unknown", "RANKING_UNKNOWN_ID"),
        ("duplicate", "RANKING_DUPLICATE_ID"),
        ("missing", "RANKING_MISSING_ID"),
        ("extra_field", "RANKING_FIELDS_INVALID"),
        ("freeform", "RANKING_NOT_STRING_LIST"),
        ("bad_json", "RESPONSE_JSON_INVALID"),
        ("private_reasoning_field", "RESPONSE_PRIVATE_REASONING_FIELD_FORBIDDEN"),
    ],
)
def test_invalid_rankings_are_rejected_without_repair(mode, error):
    transport = MockRankingTransport(mode=mode)
    expected = ("O_A", "O_B", "O_C")
    request = {
        "messages": [
            {"role": "system", "content": "JSON"},
            {"role": "user", "content": json.dumps({
                "candidates": [{"opaque_id": item} for item in expected]
            })},
        ],
        "model": LLM_PRIMARY_MODEL,
    }
    response = call_and_validate_ranking(
        transport,
        request,
        expected_ids=expected,
        requested_model=LLM_PRIMARY_MODEL,
    )
    assert response.valid is False
    assert response.ranking == ()
    assert response.error_code == error


@pytest.mark.parametrize("condition", ["S4", "S5"])
def test_s4_s5_audit_every_decision_and_share_frontier_policy(tmp_path, condition):
    case = load_public_case(_fixture(tmp_path / condition))
    pool = _widened_pool(case)
    transport = MockRankingTransport()
    run = tmp_path / f"run-{condition}"
    transport.required_header = run / "run_header.json"
    search = (
        llm_state_ranking_search if condition == "S4"
        else llm_action_proposal_search
    )
    result = search(
        case,
        budget=10,
        transport=transport,
        decision_directory=run,
        candidate_pool=pool,
        config=DeepSeekSearchConfig(seed_label="seed-2"),
    )
    _pool, policy, root, expansion = _root_material(case, pool)
    assert result.states_expanded == 10
    assert result.expansion_trace[0].legal_child_hashes == tuple(
        item.canonical_hash for item in expansion.children
    )
    assert result.batch_size == LLM_BATCH_SIZE == 32
    assert result.beam_width == LLM_BEAM_WIDTH == 32
    assert result.policy == policy
    assert result.llm_batch_states_pruned > 0
    assert result.ordering_uses_verifier_outcomes is False
    assert result.self_certifies_success is False
    assert result.success_evaluation == "EXTERNAL_EVALUATOR_REQUIRED"
    assert result.states_to_first_success is None
    assert result.time_to_first_success_seconds is None
    assert result.tokens_to_first_success is None
    assert result.model == LLM_PRIMARY_MODEL
    assert result.seed == 2
    assert result.seed_label == "seed-2"
    assert result.fallback_decisions == 0
    assert result.invalid_response_decisions == 0
    assert result.usage_complete_for_all_decisions is True
    assert result.accepted_llm_decisions == len(result.decision_records)
    assert result.llm_causal_valid is True
    assert result.llm_causal_validity_status == LLM_CAUSAL_STATUS_VALID
    assert result.llm_causal_invalid_reasons == ()
    assert result.llm_guided_scientific_run_eligible is True
    assert result.prompt_tokens == 10 * len(result.decision_records)
    assert result.completion_tokens == 5 * len(result.decision_records)
    assert result.llm_tokens == 15 * len(result.decision_records)
    assert result.reasoning_tokens == 2 * len(result.decision_records)
    assert result.wall_time_seconds >= 0
    assert result.symbolic_comparison_requires_matched_batch_control is True
    assert result.symbolic_comparison_status == (
        "UNMATCHED_FRONTIER_DO_NOT_CLAIM_AI_ADVANTAGE"
    )

    first_request = json.loads(transport.requests[0]["messages"][1]["content"])
    assert first_request["current_search_state"] == public_state_payload(root)
    assert len(first_request["candidates"]) == LLM_BATCH_SIZE
    if condition == "S4":
        assert first_request["candidate_kind"] == "CHILD_STATE"
        assert all(set(item) == {"opaque_id", "state"} for item in first_request["candidates"])
        expected = candidate_state_items(expansion.children[:LLM_BATCH_SIZE])
    else:
        assert first_request["candidate_kind"] == "LEGAL_ACTION"
        assert all(set(item) == {"action", "opaque_id"} for item in first_request["candidates"])
        expected = legal_action_items(expansion.actions[:LLM_BATCH_SIZE])
    assert first_request["candidates"] == list(expected)

    assert len(result.decision_artifacts) == len(result.decision_records)
    header = json.loads((run / "run_header.json").read_text(encoding="utf-8"))
    header_without_hash = dict(header)
    header_digest = header_without_hash.pop("run_header_sha256")
    from research.representation_program_search.program_ir import canonical_json
    assert header_digest == hashlib.sha256(
        canonical_json(header_without_hash).encode("utf-8")
    ).hexdigest()
    assert header_digest == result.run_header_sha256
    assert header["condition"] == condition
    assert header["proposer_view_sha256"] == case.proposer_view_sha256
    assert header["candidate_pool"]["candidate_pool_sha256"] == pool.canonical_hash
    assert header["search_policy"] == SearchPolicy().to_dict()
    assert header["batch_policy"] == {
        "batch_size": 32,
        "beam_width": 32,
        "cross_parent_priority": list(CROSS_PARENT_PRIORITY_FIELDS),
        "fallback_policy": "PRESENTED_CANONICAL_ORDER_V1",
        "merge_policy_version": BATCHED_BEAM_MERGE_POLICY_VERSION,
        "policy_version": "RPSLLMBeamBatchPolicyV1",
        "presented_subset": "FIRST_32_M2_ORDERED_LEGAL_CHILDREN",
    }
    assert header["symbolic_comparison_requires_matched_batch_control"] is True
    assert header["symbolic_comparison_status"] == (
        "UNMATCHED_FRONTIER_DO_NOT_CLAIM_AI_ADVANTAGE"
    )
    assert header["llm_causal_validity_policy"] == {
        "fallback_is_diagnostic_only": True,
        "policy_version": "RPSLLMCausalValidityV1",
        "pre_call_status": "PENDING_FAIL_CLOSED",
        "valid_requires": [
            "AT_LEAST_ONE_ACCEPTED_LLM_DECISION",
            "ZERO_FALLBACK_DECISIONS",
            "COMPLETE_USAGE_FOR_EVERY_DECISION",
        ],
    }
    assert (run / "search_result.json").is_file()
    terminal = json.loads((run / "search_result.json").read_text(encoding="utf-8"))
    assert terminal == result.to_dict()
    assert terminal["seed"] == 2
    assert terminal["seed_label"] == "seed-2"
    assert terminal["llm_causal_valid"] is True
    assert terminal["llm_guided_scientific_run_eligible"] is True
    serialized_records = result.to_dict()["decision_records"]
    for filename, serialized_record in zip(
        result.decision_artifacts, serialized_records
    ):
        path = run / filename
        assert path.is_file()
        record = json.loads(path.read_text(encoding="utf-8"))
        assert record == serialized_record
        assert record["decision_record_sha256"] == decision_record_hash(record)
        assert record["run_header_sha256"] == result.run_header_sha256
        assert record["current_state_hash"] == record["current_search_state"]["state_hash"]
        assert record["chosen_next_state_hash"]
        assert record["private_reasoning_persisted"] is False
        assert record["provider_response"]["raw_structured_final_response"] is not None
        assert record["provider_response"]["usage"]["complete"] is True
    artifact_blob = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(run.glob("*.json"))
    )
    assert PRIVATE_REASONING_SENTINEL not in artifact_blob
    assert "reasoning_content" not in artifact_blob
    assert "reasoning_tail" not in artifact_blob
    for forbidden in ('"gold"', '"reference"', '"verification"', '"verdict"'):
        assert forbidden not in artifact_blob


def test_invalid_or_failed_api_uses_separate_canonical_fallback(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))
    pool = extract_candidate_pool(case)
    invalid = llm_state_ranking_search(
        case,
        budget=10,
        transport=MockRankingTransport(mode="unknown"),
        decision_directory=tmp_path / "invalid",
        candidate_pool=pool,
    )
    failed = llm_state_ranking_search(
        case,
        budget=10,
        transport=MockRankingTransport(mode="raise"),
        decision_directory=tmp_path / "failed",
        candidate_pool=pool,
    )
    assert invalid.fallback_decisions == len(invalid.decision_records)
    assert failed.fallback_decisions == len(failed.decision_records)
    for result in (invalid, failed):
        assert result.accepted_llm_decisions == 0
        assert result.llm_causal_valid is False
        assert result.llm_causal_validity_status == LLM_CAUSAL_STATUS_INVALID
        assert result.llm_guided_scientific_run_eligible is False
        assert LLM_CAUSAL_REASON_FALLBACK in result.llm_causal_invalid_reasons
        assert LLM_CAUSAL_REASON_ZERO_ACCEPTED in result.llm_causal_invalid_reasons
    assert LLM_CAUSAL_REASON_INCOMPLETE_USAGE not in invalid.llm_causal_invalid_reasons
    assert LLM_CAUSAL_REASON_INCOMPLETE_USAGE in failed.llm_causal_invalid_reasons
    assert [item.canonical_hash for item in invalid.expanded_states] == [
        item.canonical_hash for item in failed.expanded_states
    ]
    invalid_first = json.loads(
        (tmp_path / "invalid" / invalid.decision_artifacts[0]).read_text()
    )
    failed_first = json.loads(
        (tmp_path / "failed" / failed.decision_artifacts[0]).read_text()
    )
    assert invalid_first["fallback"] == {
        "policy": "PRESENTED_CANONICAL_ORDER_V1",
        "reason": "RANKING_UNKNOWN_ID",
        "used": True,
    }
    assert invalid_first["response_ranking_accepted"] is False
    assert invalid_first["provider_response"]["raw_structured_final_response"] is not None
    assert failed_first["fallback"]["reason"] == "API_FAILURE:RuntimeError"
    assert failed_first["provider_response"]["raw_structured_final_response"] is None
    for run_name in ("invalid", "failed"):
        terminal = json.loads(
            (tmp_path / run_name / "search_result.json").read_text(encoding="utf-8")
        )
        assert terminal["llm_causal_valid"] is False
        assert terminal["llm_guided_scientific_run_eligible"] is False
        assert terminal["llm_causal_validity_status"] == LLM_CAUSAL_STATUS_INVALID


def test_incomplete_usage_invalidates_response_and_is_recorded(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))

    class IncompleteUsage(MockRankingTransport):
        def complete(self, request):
            response = super().complete(request)
            del response["usage"]["prompt_cache_hit_tokens"]
            return response

    result = llm_action_proposal_search(
        case,
        budget=10,
        transport=IncompleteUsage(),
        decision_directory=tmp_path / "run",
    )
    assert result.fallback_decisions == len(result.decision_records)
    assert result.usage_complete_for_all_decisions is False
    assert result.llm_causal_valid is False
    assert result.llm_guided_scientific_run_eligible is False
    assert result.llm_causal_invalid_reasons == (
        LLM_CAUSAL_REASON_FALLBACK,
        LLM_CAUSAL_REASON_INCOMPLETE_USAGE,
        LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    )
    first = json.loads((tmp_path / "run" / result.decision_artifacts[0]).read_text())
    assert first["fallback"]["reason"] == "RESPONSE_USAGE_INCOMPLETE"
    assert first["provider_response"]["usage"]["complete"] is False


def test_any_fallback_invalidates_run_even_after_an_accepted_llm_decision(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))

    class AcceptedThenFallback(MockRankingTransport):
        def complete(self, request):
            self.mode = "reverse" if not self.requests else "bad_json"
            return super().complete(request)

    result = llm_state_ranking_search(
        case,
        budget=10,
        transport=AcceptedThenFallback(),
        decision_directory=tmp_path / "run",
    )
    assert result.accepted_llm_decisions == 1
    assert result.fallback_decisions > 0
    assert result.usage_complete_for_all_decisions is True
    assert result.llm_causal_invalid_reasons == (LLM_CAUSAL_REASON_FALLBACK,)
    assert result.llm_causal_valid is False
    assert result.llm_causal_validity_status == LLM_CAUSAL_STATUS_INVALID
    assert result.llm_guided_scientific_run_eligible is False


def test_no_evaluator_verifier_sol_or_old_reasoning_client_is_called(tmp_path, monkeypatch):
    case = load_public_case(_fixture(tmp_path / "case"))

    def forbidden(*_args, **_kwargs):
        raise AssertionError("forbidden evaluator or old LLM boundary")

    monkeypatch.setattr(program_ir, "load_case_package", forbidden)
    monkeypatch.setattr(symbolic_compactification, "verify_equivalent", forbidden)
    monkeypatch.setattr(old_llm_client, "chat_complete", forbidden)
    result = llm_state_ranking_search(
        case,
        budget=10,
        transport=MockRankingTransport(),
        decision_directory=tmp_path / "run",
        grammar_id="G_PRIMITIVE",
        config=DeepSeekSearchConfig(
            model=LLM_ROBUSTNESS_MODEL,
            seed_label="seed-4",
        ),
    )
    assert result.states_expanded == 10
    assert result.grammar_id == "G_PRIMITIVE"
    assert result.model == LLM_ROBUSTNESS_MODEL
    assert result.seed_label == "seed-4"
    assert result.seed == 4
    assert all(
        "reference" not in item and "verification" not in item
        for item in result.public_case_manifest["accessed_paths"]
    )


def test_budget_latent_ablation_and_atomic_directory_fail_closed(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))
    with pytest.raises(SearchContractError, match="STATE_BUDGET_NOT_FROZEN"):
        llm_state_ranking_search(
            case,
            budget=11,
            transport=MockRankingTransport(),
            decision_directory=tmp_path / "bad-budget",
        )
    disabled = llm_action_proposal_search(
        case,
        budget=10,
        transport=MockRankingTransport(),
        decision_directory=tmp_path / "disabled",
        policy=SearchPolicy(latent_creation_enabled=False),
    )
    assert disabled.states_expanded == 1
    assert not disabled.decision_records
    assert disabled.frontier_exhausted is True
    assert disabled.llm_causal_valid is False
    assert disabled.llm_causal_validity_status == LLM_CAUSAL_STATUS_INVALID
    assert disabled.llm_causal_invalid_reasons == (
        LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    )
    assert disabled.llm_guided_scientific_run_eligible is False

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "prior.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(SearchContractError, match="LLM_DECISION_DIRECTORY_NOT_EMPTY"):
        llm_state_ranking_search(
            case,
            budget=10,
            transport=MockRankingTransport(),
            decision_directory=occupied,
        )

    with pytest.raises(SearchContractError, match="LLM_SEARCH_POLICY_NOT_FROZEN"):
        llm_state_ranking_search(
            case,
            budget=10,
            transport=MockRankingTransport(),
            decision_directory=tmp_path / "tuned-policy",
            policy=SearchPolicy(max_complexity=23),
        )


def test_manually_forged_evaluator_context_is_rejected_before_artifact_creation(tmp_path):
    case = load_public_case(_fixture(tmp_path / "case"))
    forged = replace(case, assumptions={"gold_program": {"operator": "HERMITE_DD"}})
    output = tmp_path / "forged"
    with pytest.raises(SearchContractError, match="LLM_PUBLIC_FIELD_FORBIDDEN"):
        llm_state_ranking_search(
            forged,
            budget=10,
            transport=MockRankingTransport(),
            decision_directory=output,
        )
    assert not output.exists()
