"""Infrastructure-only controls for S6 verifier-in-the-loop search."""
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
from research.representation_program_search.verifier_search import (
    FIXED_STATE_BUDGETS,
    FrontierContractError,
    VerifierFrontierNode,
    VerifierSearchController,
    verifier_search,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _source(root: Path, member_id: str, text: str) -> SourceMember:
    path = root / "members" / f"{member_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    return SourceMember(
        member_id=member_id,
        path=path.relative_to(root).as_posix(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _value_program(
    source: SourceMember,
    *,
    expression: str,
    parameters: tuple[str, ...],
    values: dict[str, str],
    grammar_id: str = "G_FULL",
) -> tuple[RepresentationProgram, CompileContext]:
    arguments = (
        {"node": values[parameters[0]]}
        if len(parameters) == 1
        else {"values": values}
    )
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(
            LatentObject(
                "F0",
                "FUNCTION_1" if len(parameters) == 1 else "FUNCTION_2",
                parameters,
                expression,
            ),
        ),
        node_structures=(),
        operators=(Operator("OP0", "VALUE", "t0", "F0", arguments=arguments),),
        member_assignments=(MemberAssignment(source.member_id, "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", source.member_id, "t0"),),
    )
    symbols = tuple(sorted(set(values.values())))
    return program, CompileContext(Path(source.path).parent.parent, symbols, grammar_id=grammar_id)


def _node(
    program: RepresentationProgram,
    context: CompileContext,
    *,
    complexity: int = 3,
    depth: int = 1,
    priority: tuple[int | str, ...] = (0,),
    label: str | None = None,
) -> VerifierFrontierNode:
    return VerifierFrontierNode.from_program(
        program,
        context,
        complexity=complexity,
        depth=depth,
        public_priority=priority,
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
        label=label,
    )


def _single_decision(output: Path) -> dict:
    paths = sorted((output / "decisions").glob("decision_*.json"))
    assert len(paths) == 1
    return _load(paths[0])


def _step_for_obligation(output: Path, obligation: dict) -> dict:
    artifact = output / obligation["artifact_path"]
    evidence = _load(artifact / "evidence.json")
    return _load(artifact / evidence["evidence"]["step_path"])


def test_zero_is_program_success_and_every_equality_has_atomic_session_evidence(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x**2 + 2*x*y + y**2")
    program, _bad_context = _value_program(
        source,
        expression="(u + v)**2",
        parameters=("u", "v"),
        values={"u": "x", "v": "y"},
    )
    context = CompileContext(case, ("x", "y"))
    output = tmp_path / "output"
    result = verifier_search(
        [_node(program, context)], output_root=output, budget=10
    )

    assert result.states_expanded == 1
    assert result.condition == "S6"
    assert result.first_success_index == 1
    assert result.feedback_counts["ZERO"] == 1
    assert result.obligation_verdict_counts["ZERO"] == 1
    assert result.llm_tokens_used == 0
    assert result.time_to_first_success_seconds is not None
    assert result.success_at["SUCCESS@10"] is True
    decision = _single_decision(output)
    assert decision["disposition"] == "PROGRAM_SUCCESS"
    assert decision["feedback_exposed_to_expander"] == "ZERO"
    assert decision["private_reasoning_recorded"] is False
    assert decision["semantic_decision_hash_inputs"]["condition"] == "S6"
    assert decision["semantic_decision_hash_inputs"][
        "feedback_guides_successors"
    ] is False
    assert "residual" not in canonical_json(decision)
    assert "counterexample" not in canonical_json(decision)
    obligation = decision["obligations"][0]
    artifact = output / obligation["artifact_path"]
    assert not any(path.name.startswith(".") for path in artifact.parent.iterdir())
    evidence = _load(artifact / "evidence.json")
    assert evidence["verdict"] == "ZERO"
    step = _step_for_obligation(output, obligation)
    assert step["verdict"] == "ZERO"
    assert step["status"] == "CERTIFIED"
    assert step["proof_status"] == "PROVEN"
    run_root = artifact / evidence["evidence"]["run_path"]
    assert (run_root / "final/current.json").is_file()
    assert hashlib.sha256((run_root / "manifest.json").read_bytes()).hexdigest() == (
        evidence["evidence"]["manifest_sha256"]
    )


def test_assumption_clearance_is_a_fail_closed_pre_verifier_gate(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x + 1")
    program, _ = _value_program(
        source,
        expression="u + 1",
        parameters=("u",),
        values={"u": "x"},
    )
    context = CompileContext(case, ("x",))
    node = VerifierFrontierNode.from_program(
        program,
        context,
        complexity=3,
        depth=1,
        leakage_status="CLEARED",
    )
    output = tmp_path / "output"
    result = verifier_search([node], output_root=output, budget=10)

    assert result.first_success_index is None
    assert result.disposition_counts == {"PRE_VERIFICATION_INELIGIBLE": 1}
    decision = _single_decision(output)
    assert decision["evaluation"]["reason"] == (
        "ASSUMPTION_CLEARANCE_NOT_ESTABLISHED"
    )
    assert not list((output / "states").glob("*/obligations/*"))


def test_nonzero_prunes_only_exact_state_and_retains_exact_counterexample_in_step(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x + 2")
    program, _ = _value_program(
        source,
        expression="u + 1",
        parameters=("u",),
        values={"u": "x"},
    )
    repair, _ = _value_program(
        source,
        expression="u + 2",
        parameters=("u",),
        values={"u": "x"},
    )
    context = CompileContext(case, ("x",))
    repair_node = _node(repair, context, complexity=3, depth=2)
    feedback_seen: list[str | None] = []

    def expander(node, feedback):
        feedback_seen.append(feedback)
        return (repair_node,) if node.program_id != repair_node.program_id else ()

    output = tmp_path / "output"
    result = verifier_search(
        [_node(program, context)],
        output_root=output,
        budget=10,
        expander=expander,
    )
    assert feedback_seen == ["NONZERO", "ZERO"]
    assert result.feedback_counts["NONZERO"] == 1
    assert result.feedback_counts["ZERO"] == 1
    assert result.first_success_index == 2
    decisions = [_load(path) for path in sorted((output / "decisions").glob("*.json"))]
    decision = decisions[0]
    assert decision["disposition"] == "PRUNED"
    step = _step_for_obligation(output, decision["obligations"][0])
    assert step["residual"] not in (None, "", "0")
    counterexamples = [
        row for row in step["evidence"] if row.get("kind") == "exact_counterexample"
    ]
    assert len(counterexamples) == 1
    assert counterexamples[0]["exact_value"] != "0"
    assert decisions[1]["disposition"] == "PROGRAM_SUCCESS"


def test_unknown_is_never_success_and_is_retained_at_frozen_lower_priority(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "1/z")
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("u",), "polygamma(0, u)"),
        ),
        node_structures=(NodeStructure("N0", ("z", "z + 1")),),
        operators=(
            Operator(
                "OP0",
                "NEWTON_DD",
                "t0",
                "F0",
                arguments={"nodes": "N0"},
            ),
        ),
        member_assignments=(MemberAssignment("A001", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A001", "t0"),),
    )
    context = CompileContext(
        case,
        ({"name": "z", "real": False, "nonzero": False},),
    )
    output = tmp_path / "output"
    result = verifier_search(
        [_node(program, context)], output_root=output, budget=10
    )
    assert result.first_success_index is None
    assert result.feedback_counts["UNKNOWN"] == 1
    assert result.retained_unknown_state_hashes
    assert result.policy.unknown_successor_band > result.policy.initial_priority_band
    decision = _single_decision(output)
    assert decision["disposition"] == "RETAINED_LOWER_PRIORITY"
    step = _step_for_obligation(output, decision["obligations"][0])
    assert step["verdict"] == "UNKNOWN"
    assert step["proof_status"] == "PROOF_REQUIRED"
    obligation = decision["obligations"][0]
    artifact = output / obligation["artifact_path"]
    evidence = _load(artifact / "evidence.json")
    run_root = artifact / evidence["evidence"]["run_path"]
    assert not (run_root / "final/current.json").exists()


def test_actual_m1_wrong_hermite_prefix_is_compile_failure_without_verifier(tmp_path):
    case = Path(
        "research/representation_program_search/falsifier/traps/"
        "wrong-hermite-multiplicity"
    ).resolve()
    member = case / "members/m001.txt"
    source = SourceMember(
        "m001",
        "members/m001.txt",
        hashlib.sha256(member.read_bytes()).hexdigest(),
    )
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_1", ("u",), "u**3"),),
        node_structures=(NodeStructure("N0", ("x", "y")),),
        operators=(
            Operator(
                "OP0", "HERMITE_DD", "t0", "F0", arguments={"nodes": "N0"}
            ),
        ),
        member_assignments=(MemberAssignment("m001", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "m001", "t0"),),
    )
    context = CompileContext(case, ("x", "y", "z"))
    output = tmp_path / "output"
    result = verifier_search(
        [_node(program, context)], output_root=output, budget=10
    )
    assert result.feedback_counts["COMPILE_FAILURE"] == 1
    decision = _single_decision(output)
    assert decision["evaluation"]["compilation"]["failure_codes"] == [
        "HERMITE_REPEATED_NODE_REQUIRED:N0"
    ]
    assert not list((output / "states").rglob("verification"))


def test_tautological_and_strictly_dominated_states_never_reach_verifier(tmp_path):
    # Exact self wrappers are rejected before any session is initialized.
    taut_case = tmp_path / "taut"
    first = _source(taut_case, "A001", "x + 1")
    second = _source(taut_case, "A002", "y + 1")
    taut = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(first, second),
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("u",), "x + 1"),
            LatentObject("F1", "FUNCTION_1", ("v",), "y + 1"),
        ),
        node_structures=(),
        operators=(
            Operator("OP0", "VALUE", "t0", "F0", arguments={"node": "x"}),
            Operator("OP1", "VALUE", "t1", "F1", arguments={"node": "y"}),
        ),
        member_assignments=(
            MemberAssignment("A001", "t0", ("OP0",)),
            MemberAssignment("A002", "t1", ("OP1",)),
        ),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(
            Obligation("O0", "A001", "t0"),
            Obligation("O1", "A002", "t1"),
        ),
    )
    taut_output = tmp_path / "taut-output"
    verifier_search(
        [_node(taut, CompileContext(taut_case, ("x", "y")))],
        output_root=taut_output,
        budget=10,
    )
    taut_decision = _single_decision(taut_output)
    assert taut_decision["evaluation"]["reason"] == "TAUTOLOGICAL_PROGRAM"
    assert taut_decision["feedback_exposed_to_expander"] is None
    assert not list((taut_output / "states").rglob("verification"))

    # An unused extra operator changes the program but not any exact compiled
    # equality.  The lower-complexity state is a conservative witness.
    dom_case = tmp_path / "dominance"
    source = _source(dom_case, "A001", "x")
    simple, _ = _value_program(
        source, expression="u", parameters=("u",), values={"u": "x"}
    )
    complex_program = replace(
        simple,
        operators=simple.operators
        + (
            Operator(
                "OP1",
                "DERIVATIVE",
                "unused",
                "F0",
                arguments={"variable": "u"},
            ),
        ),
    )
    context = CompileContext(dom_case, ("x",))
    output = tmp_path / "dominance-output"
    result = verifier_search(
        [
            _node(simple, context, complexity=2, label="simple"),
            _node(complex_program, context, complexity=5, label="complex"),
        ],
        output_root=output,
        budget=10,
    )
    assert result.states_expanded == 2
    decisions = [_load(path) for path in sorted((output / "decisions").glob("*.json"))]
    assert decisions[0]["disposition"] == "PROGRAM_SUCCESS"
    assert decisions[1]["evaluation"]["reason"] == "DOMINATED_EXACT_OBLIGATIONS"
    assert decisions[1]["evaluation"]["dominated_by"] == decisions[0]["node"]["canonical_hash"]
    assert len(list((output / "states").rglob("verification"))) == 1


def test_g_primitive_compose_is_a_legal_executable_controller_state(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x**2")
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("u",), "u"),
            LatentObject("F1", "FUNCTION_1", ("v",), "v**2"),
        ),
        node_structures=(),
        operators=(
            Operator("OP0", "VALUE", "t0", "F0", arguments={"node": "x"}),
            Operator("OP1", "COMPOSE", "t1", "F1", inputs=("t0",)),
        ),
        member_assignments=(MemberAssignment("A001", "t1", ("OP0", "OP1")),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A001", "t1"),),
    )
    context = CompileContext(case, ("x",), grammar_id="G_PRIMITIVE")
    result = verifier_search(
        [_node(program, context)], output_root=tmp_path / "output", budget=10
    )
    assert result.feedback_counts["ZERO"] == 1
    assert result.first_success_index == 1


def test_method_neutral_partial_state_expands_without_verifier_feedback(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x")
    complete, _ = _value_program(
        source, expression="u", parameters=("u",), values={"u": "x"}
    )
    partial = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(),
        node_structures=(),
        operators=(),
        member_assignments=(),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(),
        unexplained_members=("A001",),
    )
    context = CompileContext(case, ("x",))
    partial_node = _node(partial, context, complexity=0, depth=0)
    complete_node = _node(complete, context, complexity=2, depth=1)
    feedback_seen: list[str | None] = []

    def expander(node, feedback):
        feedback_seen.append(feedback)
        return (complete_node,) if node.canonical_hash == partial_node.canonical_hash else ()

    output = tmp_path / "output"
    result = verifier_search(
        [partial_node], output_root=output, budget=10, expander=expander
    )
    assert result.states_expanded == 2
    assert feedback_seen == [None, "ZERO"]
    decisions = [_load(path) for path in sorted((output / "decisions").glob("*.json"))]
    assert decisions[0]["disposition"] == "PARTIAL_EXPANDED"
    assert decisions[0]["feedback_exposed_to_expander"] is None
    assert not list((output / "states/state_00001").rglob("verification"))
    assert decisions[1]["disposition"] == "PROGRAM_SUCCESS"


def test_public_frontier_firewall_frozen_budget_and_hash_integrity(tmp_path):
    case = tmp_path / "case"
    source = _source(case, "A001", "x")
    program, _ = _value_program(
        source, expression="u", parameters=("u",), values={"u": "x"}
    )
    context = CompileContext(case, ("x",))
    with pytest.raises(FrontierContractError, match="HIDDEN_EVALUATOR_FIELD"):
        VerifierFrontierNode(
            program,
            context,
            {"gold_program": "forbidden"},
            complexity=1,
            depth=1,
            leakage_status="CLEARED",
        )
    with pytest.raises(
        FrontierContractError, match="STATE_BUDGET_NOT_FROZEN_CHECKPOINT"
    ):
        VerifierSearchController(output_root=tmp_path / "bad", budget=11)
    assert FIXED_STATE_BUDGETS == (10, 50, 100, 500, 1000)

    output = tmp_path / "output"
    result = verifier_search(
        [_node(program, context)], output_root=output, budget=10
    )
    decision = _single_decision(output)
    declared_hash = decision.pop("decision_hash")
    actual_hash = hashlib.sha256(canonical_json(decision).encode("utf-8")).hexdigest()
    assert declared_hash == actual_hash
    stored_result = _load(output / "result.json")
    assert stored_result["trace_hash"] == result.trace_hash
    assert stored_result["decision_hashes"] == list(result.decision_hashes)

    second_output = tmp_path / "second-output"
    second = verifier_search(
        [_node(program, context)], output_root=second_output, budget=10
    )
    assert second.semantic_decision_hashes == result.semantic_decision_hashes
    assert second.semantic_trace_hash == result.semantic_trace_hash
    assert result.decision_hashes != second.decision_hashes
