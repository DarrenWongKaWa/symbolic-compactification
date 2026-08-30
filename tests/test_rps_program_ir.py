from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from symbolic_compactification import ZERO, verify_equivalent

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
    canonical_program_hash,
    compile_program,
    is_tautological,
    load_case_package,
)


def _source(tmp_path: Path, member_id: str, text: str) -> SourceMember:
    path = tmp_path / "members" / f"{member_id}.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text + "\n", encoding="utf-8")
    return SourceMember(
        member_id=member_id,
        path=path.relative_to(tmp_path).as_posix(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _dd_program(
    source: SourceMember,
    *,
    parameter: str = "u",
    kind: str = "NEWTON_DD",
    nodes: tuple[str, ...] = ("x", "y"),
    arguments: dict | None = None,
) -> RepresentationProgram:
    return RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_1", (parameter,), f"sqrt({parameter})"),),
        node_structures=(NodeStructure("N0", nodes),),
        operators=(Operator(
            operator_id="OP0",
            operator=kind,
            output="t0",
            latent_id="F0",
            arguments=arguments or {"nodes": "N0"},
        ),),
        member_assignments=(MemberAssignment("A001", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O000", "A001", "t0"),),
        instance_maps={"A001": {parameter: list(nodes)}},
    )


def _context(tmp_path: Path, grammar_id: str = "G_FULL") -> CompileContext:
    return CompileContext(tmp_path, ("x", "y"), grammar_id=grammar_id)


def test_alpha_equivalent_programs_hash_identically_but_source_ids_stay_exact(tmp_path):
    source = _source(tmp_path, "u_member", "(sqrt(y)-sqrt(x))/(y-x)")
    first = _dd_program(source, parameter="u")
    second = _dd_program(source, parameter="q")
    assert canonical_program_hash(first) == canonical_program_hash(second)
    payload = second.to_dict()
    assert payload["source_members"][0]["member_id"] == "u_member"
    assert payload["source_members"][0]["path"] == "members/u_member.txt"


def test_alpha_normalization_is_scoped_across_multiple_latents(tmp_path):
    source = _source(tmp_path, "A001", "x")
    base = _dd_program(source)
    first = replace(
        base,
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("u",), "u"),
            LatentObject("F1", "FUNCTION_1", ("u",), "u + 1"),
        ),
        instance_maps={"A001": {"F0": {"u": "x"}, "F1": {"u": "y"}}},
    )
    second = replace(
        first,
        latent_objects=(
            LatentObject("F0", "FUNCTION_1", ("p",), "p"),
            LatentObject("F1", "FUNCTION_1", ("q",), "q + 1"),
        ),
        instance_maps={"A001": {"F0": {"p": "x"}, "F1": {"q": "y"}}},
    )
    assert canonical_program_hash(first) == canonical_program_hash(second)


def test_canonical_json_is_order_independent_and_rejects_nan():
    assert canonical_json({"b": 2, "a": 1}) == '{"a":1,"b":2}'
    with pytest.raises(ValueError):
        canonical_json({"not_exact": float("nan")})


def test_non_tautological_r2_newton_program_compiles_to_exact_zero_candidate(tmp_path):
    source = _source(tmp_path, "A001", "(sqrt(y)-sqrt(x))/(y-x)")
    result = compile_program(_dd_program(source), _context(tmp_path))
    assert result.status == "COMPILED"
    assert result.failure_codes == ()
    assert result.tautological is False
    assert len(result.obligations) == 1
    obligation = result.obligations[0]
    assert obligation.status == "COMPILED"
    assert "verdict" not in obligation.to_dict()
    assert verify_equivalent(
        obligation.current_expression,
        obligation.candidate_expression,
        ["x", "y"],
    ).verdict == ZERO


def test_non_tautological_r3_hermite_program_preserves_repeated_node_multiplicity(tmp_path):
    source = _source(
        tmp_path,
        "A001",
        "((sqrt(y)-sqrt(x))/(y-x)-1/(2*sqrt(x)))/(y-x)",
    )
    program = _dd_program(
        source,
        kind="HERMITE_DD",
        nodes=("x", "x", "y"),
    )
    assert program.node_structures[0].nodes == ("x", "x", "y")
    result = compile_program(program, _context(tmp_path))
    assert result.status == "COMPILED"
    assert verify_equivalent(
        result.obligations[0].current_expression,
        result.obligations[0].candidate_expression,
        ["x", "y"],
    ).verdict == ZERO


@pytest.mark.parametrize(
    ("kind", "nodes", "code"),
    [
        ("NEWTON_DD", ("x", "x"), "NEWTON_REPEATED_NODE:N0"),
        ("HERMITE_DD", ("x", "y"), "HERMITE_REPEATED_NODE_REQUIRED:N0"),
        ("HERMITE_DD", ("x", "y", "x"), "HERMITE_NODES_NOT_GROUPED:N0"),
    ],
)
def test_newton_and_hermite_node_types_are_not_interchangeable(tmp_path, kind, nodes, code):
    source = _source(tmp_path, "A001", "x")
    result = compile_program(
        _dd_program(source, kind=kind, nodes=nodes),
        _context(tmp_path),
    )
    assert result.status == "COMPILE_FAILURE"
    assert result.failure_codes == (code,)


def test_unknown_operator_and_argument_aliases_fail_closed(tmp_path):
    source = _source(tmp_path, "A001", "x")
    unknown = _dd_program(source, kind="NEWTON")
    result = compile_program(unknown, _context(tmp_path))
    assert result.failure_codes == ("OPERATOR_UNKNOWN:NEWTON",)

    alias = _dd_program(source, arguments={"node_structure": "N0"})
    result = compile_program(alias, _context(tmp_path))
    assert result.failure_codes == ("OPERATOR_ARGUMENT_UNKNOWN:OP0",)


def test_missing_output_fails_instead_of_inferring_last_operator(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = _dd_program(source)
    program = replace(
        program,
        operators=(replace(program.operators[0], output=None),),
        member_assignments=(replace(program.member_assignments[0], output=None),),
    )
    result = compile_program(program, _context(tmp_path))
    assert result.failure_codes == ("OPERATOR_OUTPUT_MISSING:OP0",)


def test_exact_source_hash_is_a_hard_gate(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = _dd_program(replace(source, sha256="0" * 64))
    result = compile_program(program, _context(tmp_path))
    assert result.failure_codes == ("SOURCE_HASH_MISMATCH:A001",)


def test_missing_source_and_path_escape_fail_closed(tmp_path):
    missing = SourceMember("A001", "members/missing.txt", "0" * 64)
    assert compile_program(_dd_program(missing), _context(tmp_path)).failure_codes == (
        "SOURCE_MEMBER_MISSING:A001",
    )
    outside = SourceMember("A001", "../outside.txt", "0" * 64)
    assert compile_program(_dd_program(outside), _context(tmp_path)).failure_codes == (
        "SOURCE_PATH_NOT_MEMBER_ARTIFACT:../outside.txt",
    )


def test_grammar_ablations_enforce_frozen_operator_sets(tmp_path):
    source = _source(tmp_path, "A001", "x")
    hermite = _dd_program(source, kind="HERMITE_DD", nodes=("x", "x"))
    assert compile_program(hermite, _context(tmp_path, "G_NO_HERMITE")).failure_codes == (
        "OPERATOR_FORBIDDEN_BY_ABLATION:OP0",
    )
    newton = _dd_program(source)
    assert compile_program(newton, _context(tmp_path, "G_PRIMITIVE")).failure_codes == (
        "OPERATOR_FORBIDDEN_BY_ABLATION:OP0",
    )


def test_declared_or_derived_assumptions_only(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = replace(
        _dd_program(source),
        assumptions_used=("P1",),
        assumption_statuses={"P1": "NOT_DECLARED"},
    )
    assert compile_program(program, _context(tmp_path)).failure_codes == (
        "ASSUMPTION_NOT_DECLARED:P1",
    )


def test_independent_value_self_wrappers_are_tautological(tmp_path):
    first = _source(tmp_path, "A001", "x + 1")
    second = _source(tmp_path, "A002", "y + 1")
    program = RepresentationProgram(
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
    context = CompileContext(tmp_path, ("x", "y"))
    assert is_tautological(program, context) is True
    assert compile_program(program, context).tautological is True


def test_thermal_legacy_program_is_loaded_but_not_repaired_or_executed():
    package = Path(
        "research/representation_program_search/packages/thermal/"
        "thermal-09-digamma-newton"
    )
    loaded = load_case_package(package)
    assert loaded.package_id == package.name
    assert "SOURCE_MEMBERS_INJECTED_FROM_EXACT_CATALOG" in loaded.schema_deltas
    assert "EXECUTABLE_OPERATOR_OUTPUTS_MISSING" in loaded.schema_deltas
    assert "EXECUTABLE_OBLIGATION_OUTPUT_LINKS_MISSING" in loaded.schema_deltas
    result = compile_program(loaded.program, loaded.context)
    assert result.status == "COMPILE_FAILURE"
    assert result.failure_codes == ("OPERATOR_OUTPUT_MISSING:OP0",)


def test_program_serialization_is_deterministic(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = _dd_program(source)
    assert canonical_json(program.to_dict()) == canonical_json(program.to_dict())
    assert program.to_dict()["program_id"] == canonical_program_hash(program)


def test_all_non_dd_operators_have_deterministic_executable_semantics(tmp_path):
    source = _source(tmp_path, "A001", "x**4")
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_1", ("u",), "u**2"),),
        node_structures=(),
        operators=(
            Operator("OP0", "VALUE", "t0", "F0", arguments={"node": "x"}),
            Operator("OP1", "DERIVATIVE", "t1", "F0", arguments={"variable": "u"}),
            Operator("OP2", "SUBSTITUTE", "t2", "F0", ("t1",), {"parameter": "u", "value": "x"}),
            Operator("OP3", "SHIFT", "t3", "F0", arguments={"variable": "u", "delta": "1"}),
            Operator("OP4", "SUBSTITUTE", "t4", "F0", ("t3",), {"parameter": "u", "value": "x"}),
            Operator("OP5", "PERMUTE", "t5", "F0", ("t0",), {"mapping": {"x": "y"}}),
            Operator("OP6", "RECURRENCE", "t6", "F0", arguments={"parameter": "u", "base": "x", "step": "1", "form": "FORWARD_DIFFERENCE"}),
            Operator("OP7", "LINEAR_COMBINATION", "t7", "F0", ("t0", "t2"), {"coefficients": ["1", "-1"], "constant": "1"}),
            Operator("OP8", "BASIS_PROJECT", "t8", "F0", ("t0",), {"basis": "y", "coefficient": "2"}),
            Operator("OP9", "BASIS_RECONSTRUCT", "t9", "F0", ("t0", "t2"), {"coefficients": ["1", "1"]}),
            Operator("OP10", "COMPOSE", "t10", "F0", ("t0",), {}),
        ),
        member_assignments=(MemberAssignment("A001", "t10", ("OP0", "OP10")),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A001", "t10"),),
    )
    result = compile_program(program, _context(tmp_path))
    assert result.status == "COMPILED"
    assert verify_equivalent(
        result.obligations[0].current_expression,
        result.obligations[0].candidate_expression,
        ["x", "y"],
    ).verdict == ZERO


def test_function_2_value_requires_complete_parameter_map(tmp_path):
    source = _source(tmp_path, "A001", "x + y")
    base = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(source,),
        latent_objects=(LatentObject("F0", "FUNCTION_2", ("u", "v"), "u + v"),),
        node_structures=(),
        operators=(Operator("OP0", "VALUE", "t0", "F0", arguments={"values": {"u": "x", "v": "y"}}),),
        member_assignments=(MemberAssignment("A001", "t0", ("OP0",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("O0", "A001", "t0"),),
    )
    assert compile_program(base, _context(tmp_path)).status == "COMPILED"
    incomplete = replace(
        base,
        operators=(replace(base.operators[0], arguments={"values": {"u": "x"}}),),
    )
    assert compile_program(incomplete, _context(tmp_path)).failure_codes == (
        "VALUE_ARGUMENT_INVALID:OP0",
    )


def test_declared_program_id_and_dependency_links_are_hard_gates(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = _dd_program(source)
    bad_id = replace(program, declared_program_id="0" * 64)
    assert compile_program(bad_id, _context(tmp_path)).failure_codes == (
        "PROGRAM_ID_MISMATCH",
    )
    bad_input_operator = replace(
        program.operators[0],
        inputs=("missing",),
    )
    bad_input = replace(program, operators=(bad_input_operator,))
    assert compile_program(bad_input, _context(tmp_path)).failure_codes == (
        "OPERATOR_INPUT_UNAVAILABLE:missing",
    )


def test_member_reconstruction_must_match_dependency_closure(tmp_path):
    source = _source(tmp_path, "A001", "x")
    program = _dd_program(source)
    mismatched = replace(
        program,
        member_assignments=(MemberAssignment("A001", "t0", ()),),
    )
    assert compile_program(mismatched, _context(tmp_path)).failure_codes == (
        "MEMBER_RECONSTRUCTION_MISMATCH:A001",
    )
