"""Synthetic, no-live-call controls for S7 and S6_MATCHED_BATCH32."""
from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from research.representation_program_search.program_ir import (
    CompileContext,
    LatentObject,
    MemberAssignment,
    NodeStructure,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
    canonical_json,
)
from research.representation_program_search.search import (
    CANDIDATE_POLICY_VERSION,
    CandidatePool,
    LLM_CAUSAL_REASON_FALLBACK,
    LLM_CAUSAL_REASON_INCOMPLETE_USAGE,
    LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    LLM_CAUSAL_STATUS_INVALID,
    LLM_CAUSAL_STATUS_VALID,
    DeepSeekSearchConfig,
    LatentCandidate,
    SearchContractError,
    SearchPolicy,
    extract_candidate_pool,
    load_public_case,
)
from research.representation_program_search.verifier_search import (
    S6_MATCHED_BATCH32_CONDITION,
    S7_CONDITION,
    BatchedVerifierSearchResult,
    FrontierContractError,
    M2VerifierFrontierAdapter,
    S7VerifierSearchResult,
    VerifierFrontierNode,
    llm_verifier_search,
    verifier_matched_batch32_search,
)

PRIVATE_REASONING_SENTINEL = "S7_PRIVATE_REASONING_MUST_NOT_PERSIST"


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(tmp_path: Path, members: tuple[tuple[str, str], ...], symbols):
    rows = []
    for member_id, expression in members:
        relative = f"members/{member_id}.txt"
        rows.append({
            "member_id": member_id,
            "path": relative,
            "sha256": _text(tmp_path / relative, expression),
        })
    symbols_sha256 = _json(tmp_path / "symbols.json", {"symbols": symbols})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {"predicates": []},
        "case_id": "SYNTHETIC_S7",
        "source_catalog": {
            "members": rows,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha256,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def _source(case, member_id: str) -> SourceMember:
    return next(item for item in case.source_members if item.member_id == member_id)


def _value_program(
    source: SourceMember,
    *,
    expression: str,
    parameter: str,
    node: str,
) -> RepresentationProgram:
    return RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_1", (parameter,), expression),),
        node_structures=(),
        operators=(
            Operator("OP0", "VALUE", "t0", "F0", arguments={"node": node}),
        ),
        member_assignments=(MemberAssignment(source.member_id, "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", source.member_id, "t0"),),
    )


def _partial_program(source: SourceMember) -> RepresentationProgram:
    return RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(),
        node_structures=(),
        operators=(),
        member_assignments=(),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(),
        unexplained_members=(source.member_id,),
    )


def _node(
    program: RepresentationProgram,
    context: CompileContext,
    label: str,
    *,
    complexity: int,
    depth: int,
    parent_hash: str | None = None,
    public_state: dict | None = None,
) -> VerifierFrontierNode:
    return VerifierFrontierNode(
        program=program,
        context=context,
        public_state=(
            public_state
            or {
                "search_state": {"synthetic_label": label},
                "search_state_hash": hashlib.sha256(label.encode()).hexdigest(),
            }
        ),
        complexity=complexity,
        depth=depth,
        public_priority=(complexity, label),
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
        label=label,
        parent_hash=parent_hash,
        action_from_parent=(
            None
            if parent_hash is None
            else {"action": "ADD_MEMBER", "payload": {"label": label}}
        ),
    )


class MockRankingTransport:
    def __init__(self, mode: str = "identity") -> None:
        self.mode = mode
        self.requests: list[dict] = []

    def complete(self, request):
        required_header = getattr(self, "required_header", None)
        if required_header is not None:
            assert Path(required_header).is_file()
        self.requests.append(dict(request))
        user = json.loads(request["messages"][1]["content"])
        identifiers = [item["opaque_id"] for item in user["candidates"]]
        if self.mode == "identity":
            content = json.dumps({"ranking": identifiers})
        elif self.mode == "reverse":
            content = json.dumps({"ranking": list(reversed(identifiers))})
        elif self.mode == "bad_json":
            content = "not-json"
        elif self.mode == "unknown_id":
            content = json.dumps({"ranking": identifiers[:-1] + ["UNKNOWN"]})
        elif self.mode == "raise":
            raise RuntimeError("synthetic API failure")
        else:
            raise AssertionError(self.mode)
        usage = {
            "completion_tokens": 5,
            "completion_tokens_details": {"reasoning_tokens": 2},
            "prompt_cache_hit_tokens": 1,
            "prompt_cache_miss_tokens": 9,
            "prompt_tokens": 10,
            "total_tokens": 15,
        }
        if self.mode == "incomplete_usage":
            usage.pop("prompt_cache_hit_tokens")
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {
                    "content": content,
                    "reasoning_content": PRIVATE_REASONING_SENTINEL,
                },
            }],
            "id": f"mock-s7-{len(self.requests)}",
            "model": request["model"],
            "usage": usage,
        }


class IncompleteUsageTransport(MockRankingTransport):
    def complete(self, request):
        self.requests.append(dict(request))
        user = json.loads(request["messages"][1]["content"])
        identifiers = [item["opaque_id"] for item in user["candidates"]]
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": json.dumps({"ranking": identifiers})},
            }],
            "id": f"mock-incomplete-{len(self.requests)}",
            "model": request["model"],
            "usage": {
                "completion_tokens": 5,
                "completion_tokens_details": {"reasoning_tokens": 2},
                "prompt_cache_miss_tokens": 9,
                "prompt_tokens": 10,
                "total_tokens": 15,
            },
        }


class ScriptedM2Adapter(M2VerifierFrontierAdapter):
    """Synthetic controller fixture; production paths still require M2 type."""

    def __init__(self, case, root, edges):
        super().__init__(
            case,
            candidate_pool=CandidatePool(
                policy_version=CANDIDATE_POLICY_VERSION,
                latents=(),
                node_values=(),
                coefficients=("-1", "0", "1", "2", "Rational(1, 2)"),
                branching_incomplete=True,
                incompleteness_reasons=("SYNTHETIC_CONTROLLER_FIXTURE",),
                source_member_count=len(case.members),
            ),
            leakage_status="CLEARED",
        )
        self.scripted_root = root
        self.edges = edges
        self.feedback_seen: list[tuple[str, str | None]] = []

    def initial_node(self):
        return self.scripted_root

    def expand(self, node, feedback):
        self.feedback_seen.append((node.label, feedback))
        return self.edges.get(node.canonical_hash, ())

    def public_contract(self):
        payload = super().public_contract()
        payload["synthetic_test_control"] = True
        return payload


def _feedback_graph(tmp_path: Path):
    case = _case(
        tmp_path,
        (
            ("A001", "x + 2"),
            ("A002", "1/z"),
            ("A003", "x**2"),
        ),
        ["x", "y", {"name": "z", "real": False}],
    )
    context = CompileContext(case.package_root, ("x", "y", {"name": "z", "real": False}))
    root = _node(
        _partial_program(_source(case, "A001")), context, "root", complexity=0, depth=0
    )
    zero = _node(
        _value_program(
            _source(case, "A001"), expression="u + 2", parameter="u", node="x"
        ),
        context,
        "zero",
        complexity=2,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    nonzero = _node(
        _value_program(
            _source(case, "A001"), expression="u + 1", parameter="u", node="x"
        ),
        context,
        "nonzero",
        complexity=3,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    unknown_program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(_source(case, "A002"),),
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("u",), "polygamma(0, u)"),
        ),
        node_structures=(NodeStructure("N0", ("z", "z + 1")),),
        operators=(
            Operator("OP0", "NEWTON_DD", "t0", "F0", arguments={"nodes": "N0"}),
        ),
        member_assignments=(MemberAssignment("A002", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A002", "t0"),),
    )
    unknown = _node(
        unknown_program,
        context,
        "unknown",
        complexity=4,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    compile_program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(_source(case, "A003"),),
        latent_objects=(LatentObject("F0", "FUNCTION_1", ("u",), "u**3"),),
        node_structures=(NodeStructure("N0", ("x", "y")),),
        operators=(
            Operator("OP0", "HERMITE_DD", "t0", "F0", arguments={"nodes": "N0"}),
        ),
        member_assignments=(MemberAssignment("A003", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A003", "t0"),),
    )
    compile_failure = _node(
        compile_program,
        context,
        "compile",
        complexity=5,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    parents = (zero, nonzero, unknown, compile_failure)
    leaves = tuple(
        _node(
            _partial_program(_source(case, "A001")),
            context,
            f"leaf-{parent.label}",
            complexity=6,
            depth=2,
            parent_hash=parent.canonical_hash,
        )
        for parent in parents
    )
    edges = {root.canonical_hash: parents}
    edges.update({parent.canonical_hash: (leaf,) for parent, leaf in zip(parents, leaves)})
    return case, root, edges


def _partial_graph(tmp_path: Path, *, child_count: int = 4):
    case = _case(tmp_path, (("A001", "x"),), ["x"])
    context = CompileContext(case.package_root, ("x",))
    program = _partial_program(_source(case, "A001"))
    root = _node(program, context, "root", complexity=0, depth=0)
    children = tuple(
        _node(
            program,
            context,
            f"child-{index}",
            complexity=1,
            depth=1,
            parent_hash=root.canonical_hash,
        )
        for index in range(child_count)
    )
    leaves = tuple(
        _node(
            program,
            context,
            f"leaf-{index}",
            complexity=2,
            depth=2,
            parent_hash=child.canonical_hash,
        )
        for index, child in enumerate(children)
    )
    edges = {root.canonical_hash: children}
    edges.update({child.canonical_hash: (leaf,) for child, leaf in zip(children, leaves)})
    return case, root, edges


def _decision_rows(output: Path):
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((output / "decisions").glob("decision_*.json"))
    ]


def test_s7_exact_feedback_receipts_real_tokens_and_private_reasoning_firewall(tmp_path):
    case, root, edges = _feedback_graph(tmp_path / "case")
    transport = MockRankingTransport()
    output = tmp_path / "s7"
    transport.required_header = output / "controller.json"
    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=output,
        budget=10,
        transport=transport,
        config=DeepSeekSearchConfig(seed_label="seed-3"),
    )

    assert isinstance(result, S7VerifierSearchResult)
    assert result.condition == S7_CONDITION
    assert result.states_expanded == 9
    assert result.feedback_counts == {
        "COMPILE_FAILURE": 1,
        "NONZERO": 1,
        "UNKNOWN": 1,
        "ZERO": 1,
    }
    assert result.first_success_index is not None
    assert result.success_at["SUCCESS@10"] is True
    assert result.llm_decision_count == 5
    assert result.accepted_llm_decisions == 5
    assert result.llm_tokens_used == 75
    assert result.llm_tokens_used == result.prompt_tokens + result.completion_tokens
    assert result.tokens_to_first_success is not None
    assert result.tokens_to_first_success < result.llm_tokens_used
    assert result.reasoning_tokens == 10
    assert result.seed == 3 and result.seed_label == "seed-3"
    assert result.llm_causal_valid is True
    assert result.llm_causal_validity_status == LLM_CAUSAL_STATUS_VALID
    assert result.llm_guided_scientific_run_eligible is True
    assert result.verifier_comparison_requires_matched_batch_control is True
    assert result.required_verifier_control_condition == S6_MATCHED_BATCH32_CONDITION
    bands = {
        item.feedback_class: item.feedback_priority_band
        for item in result.parent_batches
        if item.feedback_class is not None
    }
    assert bands == {
        "ZERO": result.policy.zero_successor_band,
        "NONZERO": result.policy.nonzero_successor_band,
        "UNKNOWN": result.policy.unknown_successor_band,
        "COMPILE_FAILURE": result.policy.compile_failure_successor_band,
    }

    request_feedback = {
        json.loads(item["messages"][1]["content"])["aggregate_feedback_class"]
        for item in transport.requests
    }
    assert request_feedback == {None, "ZERO", "NONZERO", "UNKNOWN", "COMPILE_FAILURE"}
    request_blob = canonical_json(transport.requests)
    assert "residual" not in request_blob
    assert "counterexample" not in request_blob
    assert "obligations" not in request_blob

    rows = _decision_rows(output)
    assert {item["feedback_class"] for item in rows} == {
        None, "ZERO", "NONZERO", "UNKNOWN", "COMPILE_FAILURE"
    }
    label_order = [
        item["current_search_state"]["search_state"].get("synthetic_label")
        for item in rows
    ]
    assert label_order.index("leaf-zero") < label_order.index("leaf-unknown")
    output_blob = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(output.rglob("*.json"))
        if "/verification/runs/" not in path.as_posix()
    )
    assert PRIVATE_REASONING_SENTINEL not in output_blob
    for row in rows:
        declared = row["decision_hash"]
        unhashed = dict(row)
        unhashed.pop("decision_hash")
        assert declared == hashlib.sha256(
            canonical_json(unhashed).encode("utf-8")
        ).hexdigest()
        evaluation = output / row["state_evaluation_artifact"]
        assert hashlib.sha256(evaluation.read_bytes()).hexdigest() == row[
            "state_evaluation_sha256"
        ]
    tampered = dict(rows[0])
    tampered["feedback_class"] = "ZERO"
    tampered.pop("decision_hash")
    assert hashlib.sha256(canonical_json(tampered).encode("utf-8")).hexdigest() != (
        rows[0]["decision_hash"]
    )

    evaluated = [item for item in rows if item["feedback_class"] is not None]
    receipt_verdicts = set()
    for row in evaluated:
        evaluation = json.loads(
            (output / row["state_evaluation_artifact"]).read_text(encoding="utf-8")
        )
        for obligation in evaluation["obligations"]:
            receipt_verdicts.add(obligation["verdict"])
            evidence = output / obligation["artifact_path"] / "evidence.json"
            assert evidence.is_file()
    assert receipt_verdicts == {"ZERO", "NONZERO", "UNKNOWN"}
    compile_row = next(item for item in rows if item["feedback_class"] == "COMPILE_FAILURE")
    compile_evaluation = json.loads(
        (output / compile_row["state_evaluation_artifact"]).read_text(encoding="utf-8")
    )
    assert compile_evaluation["evaluation"]["compilation"]["failure_codes"] == [
        "HERMITE_REPEATED_NODE_REQUIRED:N0"
    ]


def test_s6_matched_replays_s7_identity_frontier_without_replacing_s6(tmp_path):
    case, root, edges = _partial_graph(tmp_path / "case")
    s7_output = tmp_path / "s7"
    matched_output = tmp_path / "matched"
    s7 = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=s7_output,
        budget=10,
        transport=MockRankingTransport(),
    )
    matched = verifier_matched_batch32_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=matched_output,
        budget=10,
    )

    assert isinstance(matched, BatchedVerifierSearchResult)
    assert matched.condition == S6_MATCHED_BATCH32_CONDITION
    assert matched.llm_tokens_used == 0
    assert matched.strongest_full_frontier_s6 is False
    assert matched.replaces_full_frontier_s6 is False
    assert matched.frontier_matched_to_s7 is True
    assert matched.batched_search_complete is False
    assert matched.verifier_comparison_status == "MATCHED_BATCH32_DIAGNOSTIC_CONTROL"
    assert [item["current_state_hash"] for item in _decision_rows(s7_output)] == [
        item["current_state_hash"] for item in _decision_rows(matched_output)
    ]
    assert [item.to_dict() for item in s7.parent_batches] == [
        item.to_dict() for item in matched.parent_batches
    ]
    assert [item.to_dict() for item in s7.beam_layers] == [
        item.to_dict() for item in matched.beam_layers
    ]
    assert s7.feedback_counts == matched.feedback_counts
    assert s7.success_at == matched.success_at


def test_s7_accepted_state_ranking_controls_only_the_legal_local_order(tmp_path):
    case, root, edges = _partial_graph(tmp_path / "case", child_count=3)
    output = tmp_path / "output"
    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=output,
        budget=10,
        transport=MockRankingTransport("reverse"),
    )
    root_batch = result.parent_batches[0]
    assert root_batch.ordered_child_hashes == tuple(
        reversed(root_batch.presented_child_hashes)
    )
    root_decision = _decision_rows(output)[0]
    assert root_decision["chosen_next_state_hash"] == (
        root_batch.presented_child_hashes[-1]
    )
    assert set(root_batch.ordered_child_hashes) == set(
        root_batch.presented_child_hashes
    )
    assert result.accepted_llm_decisions > 0
    assert result.llm_guided_scientific_run_eligible is True


@pytest.mark.parametrize(
    ("transport", "expected_reasons"),
    [
        (
            MockRankingTransport("bad_json"),
            (LLM_CAUSAL_REASON_FALLBACK, LLM_CAUSAL_REASON_ZERO_ACCEPTED),
        ),
        (
            IncompleteUsageTransport(),
            (
                LLM_CAUSAL_REASON_FALLBACK,
                LLM_CAUSAL_REASON_INCOMPLETE_USAGE,
                LLM_CAUSAL_REASON_ZERO_ACCEPTED,
            ),
        ),
        (
            MockRankingTransport("raise"),
            (
                LLM_CAUSAL_REASON_FALLBACK,
                LLM_CAUSAL_REASON_INCOMPLETE_USAGE,
                LLM_CAUSAL_REASON_ZERO_ACCEPTED,
            ),
        ),
    ],
)
def test_s7_any_fallback_or_incomplete_usage_is_diagnostic_only(
    tmp_path, transport, expected_reasons
):
    case, root, edges = _partial_graph(tmp_path / "case", child_count=1)
    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=tmp_path / "output",
        budget=10,
        transport=transport,
    )
    assert result.fallback_decisions == result.llm_decision_count
    assert result.accepted_llm_decisions == 0
    assert result.llm_causal_invalid_reasons == expected_reasons
    assert result.llm_causal_valid is False
    assert result.llm_causal_validity_status == LLM_CAUSAL_STATUS_INVALID
    assert result.llm_guided_scientific_run_eligible is False
    stored = json.loads((tmp_path / "output/result.json").read_text(encoding="utf-8"))
    assert stored["llm_guided_scientific_run_eligible"] is False


def test_s7_zero_success_without_llm_decision_is_not_ai_evidence(tmp_path):
    case = _case(tmp_path / "case", (("A001", "x + 2"),), ["x"])
    context = CompileContext(case.package_root, ("x",))
    root = _node(
        _value_program(
            _source(case, "A001"), expression="u + 2", parameter="u", node="x"
        ),
        context,
        "root-zero",
        complexity=2,
        depth=0,
    )
    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, {}),
        output_root=tmp_path / "output",
        budget=10,
        transport=MockRankingTransport(),
    )
    assert result.first_success_index == 1
    assert result.feedback_counts["ZERO"] == 1
    assert result.llm_decision_count == 0
    assert result.llm_tokens_used == 0
    assert result.tokens_to_first_success == 0
    assert result.llm_causal_invalid_reasons == (
        LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    )
    assert result.llm_guided_scientific_run_eligible is False


def test_s7_one_late_fallback_invalidates_prior_accepted_guidance(tmp_path):
    case, root, edges = _partial_graph(tmp_path / "case", child_count=1)

    class AcceptedThenInvalid(MockRankingTransport):
        def complete(self, request):
            self.mode = "identity" if not self.requests else "bad_json"
            return super().complete(request)

    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=tmp_path / "output",
        budget=10,
        transport=AcceptedThenInvalid(),
    )
    assert result.accepted_llm_decisions == 1
    assert result.fallback_decisions == 1
    assert result.usage_complete_for_all_decisions is True
    assert result.llm_causal_invalid_reasons == (LLM_CAUSAL_REASON_FALLBACK,)
    assert result.llm_guided_scientific_run_eligible is False


def test_s7_preserves_assumption_leakage_and_tautology_success_gates(tmp_path):
    case = _case(tmp_path / "case", (("A001", "x + 2"),), ["x"])
    context = CompileContext(case.package_root, ("x",))
    source = _source(case, "A001")
    partial = _partial_program(source)
    root = _node(partial, context, "root", complexity=0, depth=0)
    exact = _value_program(source, expression="u + 2", parameter="u", node="x")
    missing_assumption = _node(
        replace(
            exact,
            assumptions_used=("P_UNDECLARED",),
            assumption_statuses={},
        ),
        context,
        "assumption",
        complexity=2,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    leakage_uncleared = replace(
        _node(
            exact,
            context,
            "leakage",
            complexity=3,
            depth=1,
            parent_hash=root.canonical_hash,
        ),
        leakage_status="UNKNOWN",
    )
    tautology = _node(
        _value_program(source, expression="x + 2", parameter="u", node="x"),
        context,
        "tautology",
        complexity=4,
        depth=1,
        parent_hash=root.canonical_hash,
    )
    edges = {root.canonical_hash: (missing_assumption, leakage_uncleared, tautology)}
    output = tmp_path / "output"
    result = llm_verifier_search(
        ScriptedM2Adapter(case, root, edges),
        output_root=output,
        budget=10,
        transport=MockRankingTransport(),
    )
    assert result.first_success_index is None
    rows = _decision_rows(output)
    evaluations = {
        row["current_search_state"]["search_state"]["synthetic_label"]: json.loads(
            (output / row["state_evaluation_artifact"]).read_text(encoding="utf-8")
        )
        for row in rows
        if row["current_search_state"]["search_state"].get("synthetic_label")
        != "root"
    }
    assert evaluations["assumption"]["evaluation"]["compilation"]["failure_codes"] == [
        "ASSUMPTION_NOT_DECLARED:P_UNDECLARED"
    ]
    assert evaluations["leakage"]["evaluation"]["reason"] == (
        "TARGET_LEAKAGE_NOT_CLEARED"
    )
    assert evaluations["tautology"]["evaluation"]["reason"] == (
        "TAUTOLOGICAL_PROGRAM"
    )
    assert not list(output.rglob("verification"))


def _widened_pool(case):
    original = extract_candidate_pool(case)
    latents = tuple(
        LatentCandidate(
            candidate_id=f"LC_S7_{index:02d}",
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


def test_s7_and_s6_matched_use_identical_first32_exact_m2_frontier(tmp_path):
    case = _case(
        tmp_path / "case",
        (("A001", "exp(x)"), ("A002", "exp(y)")),
        ["x", "y"],
    )
    pool = _widened_pool(case)
    transport = MockRankingTransport()
    s7 = llm_verifier_search(
        M2VerifierFrontierAdapter(
            case, candidate_pool=pool, leakage_status="CLEARED"
        ),
        output_root=tmp_path / "s7",
        budget=10,
        transport=transport,
    )
    matched = verifier_matched_batch32_search(
        M2VerifierFrontierAdapter(
            case, candidate_pool=pool, leakage_status="CLEARED"
        ),
        output_root=tmp_path / "matched",
        budget=10,
    )
    assert s7.parent_batches[0].all_legal_child_count > 32
    assert len(s7.parent_batches[0].presented_child_hashes) == 32
    assert s7.parent_batches[0].presented_child_hashes == (
        matched.parent_batches[0].presented_child_hashes
    )
    first_request = json.loads(transport.requests[0]["messages"][1]["content"])
    assert tuple(
        item["state"]["state_hash"] for item in first_request["candidates"]
    ) == s7.parent_batches[0].presented_child_hashes
    assert [item["current_state_hash"] for item in _decision_rows(tmp_path / "s7")] == [
        item["current_state_hash"]
        for item in _decision_rows(tmp_path / "matched")
    ]


def test_s7_public_firewall_rejects_residual_before_model_call(tmp_path):
    case = _case(tmp_path / "case", (("A001", "x"),), ["x"])
    context = CompileContext(case.package_root, ("x",))
    root = _node(
        _partial_program(_source(case, "A001")), context, "root", complexity=0, depth=0
    )
    forged = _node(
        _partial_program(_source(case, "A001")),
        context,
        "forged",
        complexity=1,
        depth=1,
        parent_hash=root.canonical_hash,
        public_state={"residual": "SECRET_COUNTEREXAMPLE"},
    )
    transport = MockRankingTransport()
    with pytest.raises(SearchContractError, match="LLM_PUBLIC_FIELD_FORBIDDEN"):
        llm_verifier_search(
            ScriptedM2Adapter(case, root, {root.canonical_hash: (forged,)}),
            output_root=tmp_path / "output",
            budget=10,
            transport=transport,
        )
    assert transport.requests == []
    assert not list((tmp_path / "output/decisions").glob("*.json"))


def test_s7_frozen_budget_adapter_and_atomic_output_contracts(tmp_path):
    case = _case(tmp_path / "case", (("A001", "x"),), ["x"])
    adapter = M2VerifierFrontierAdapter(case)
    with pytest.raises(FrontierContractError, match="STATE_BUDGET_NOT_FROZEN"):
        llm_verifier_search(
            adapter,
            output_root=tmp_path / "bad-budget",
            budget=11,
            transport=MockRankingTransport(),
        )
    with pytest.raises(FrontierContractError, match="BATCHED_VERIFIER_M2_ADAPTER_REQUIRED"):
        llm_verifier_search(
            object(),
            output_root=tmp_path / "bad-adapter",
            budget=10,
            transport=MockRankingTransport(),
        )
    with pytest.raises(
        FrontierContractError, match="BATCHED_VERIFIER_SEARCH_POLICY_NOT_FROZEN"
    ):
        llm_verifier_search(
            M2VerifierFrontierAdapter(
                case,
                leakage_status="CLEARED",
                search_policy=SearchPolicy(max_complexity=23),
            ),
            output_root=tmp_path / "tuned-policy",
            budget=10,
            transport=MockRankingTransport(),
        )
    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "prior.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FrontierContractError, match="OUTPUT_ROOT_NOT_EMPTY"):
        llm_verifier_search(
            adapter,
            output_root=occupied,
            budget=10,
            transport=MockRankingTransport(),
        )
