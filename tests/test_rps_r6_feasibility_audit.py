from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.representation_program_search.audits.r6_feasibility.audit import (
    EXPECTED_REGISTRIES,
    HISTORICAL_R6,
    PINNED_INPUTS,
    R6_RELEVANT_PACKAGES,
    build_audit,
    validate_audit,
)
from research.representation_program_search.grammar_v1 import OPERATORS, OPTIONAL_LATER
from research.representation_program_search.program_ir import (
    CompileContext,
    LatentObject,
    MemberAssignment,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
    compile_program,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = (
    ROOT
    / "research"
    / "representation_program_search"
    / "audits"
    / "r6_feasibility"
)


def _report() -> dict:
    report = build_audit(ROOT)
    validate_audit(ROOT, report)
    return report


def test_full_registry_is_hash_bound_and_decision_fails_closed() -> None:
    report = _report()

    assert report["decision"] == "R6_MISSING"
    assert report["failure_class"] == "PACKAGING_GAP"
    assert report["candidate_count"] == 0
    assert report["qualifying_candidate_ids"] == []
    assert report["package_created"] is False
    assert report["pinned_inputs"] == PINNED_INPUTS
    assert report["registries"] == EXPECTED_REGISTRIES


def test_every_current_science_dossier_is_accounted_for() -> None:
    report = _report()
    admission = json.loads((
        ROOT
        / "research/representation_program_search/audits/admission/ADMISSION_AUDIT.json"
    ).read_text(encoding="utf-8"))
    expected_ids = {item["case_id"] for item in admission["cases"]}
    audited_ids = {item["case_id"] for item in report["current_cases"]}

    assert audited_ids == expected_ids
    assert len(audited_ids) == 39
    r6 = [item for item in report["current_cases"] if item["audited_depth"] == "R6"]
    assert len(r6) == 14
    assert {item["primary_status"] for item in r6} == {
        "PACKAGING_GAP",
        "DUPLICATE_REVIEW",
        "PROBLEM_UNDERSPECIFIED",
    }
    assert all(item["frozen_source_artifact_count"] == 0 for item in r6)
    assert all(item["machine_package_status"] == "ABSENT" for item in r6)
    assert all(not item["qualifies"] for item in report["current_cases"])


def test_every_historical_r6_dossier_fails_the_freshness_gate() -> None:
    report = _report()
    rows = report["historical_r6"]

    assert len(rows) == len(HISTORICAL_R6) == 14
    assert len({row["case_id"] for row in rows}) == 14
    assert all("HISTORICAL_IDENTITY" in row["failure_codes"] for row in rows)
    assert all(row["declared_ladder"] == "R6_master_object" for row in rows)
    assert all(not row["qualifies"] for row in rows)


def test_frozen_parser_and_ir_do_not_supply_missing_scientific_semantics() -> None:
    language = _report()["frozen_language"]
    probes = language["parser_probes"]

    assert probes["exp(a)"] == "PARSED"
    assert probes["polygamma(1,a)"] == "PARSED"
    assert probes["Sum(a,(n,0,3))"] == "PARSED"
    for expression in (
        "Integral(exp(-t),(t,0,oo))",
        "Matrix(a)",
        "Trace(a)",
        "Determinant(a)",
        "Commutator(a,b)",
        "zeta(2,a)",
        "factorial(n)",
    ):
        assert probes[expression] == "UNDECLARED_OR_DISALLOWED_NAME"
    assert language["matrix_function_form_has_matrix_semantics"] is False
    assert not set(OPTIONAL_LATER) & set(OPERATORS)


def test_matrix_function_latent_label_executes_as_a_scalar(tmp_path: Path) -> None:
    members = tmp_path / "members"
    members.mkdir()
    source = members / "M1.txt"
    source.write_text("exp(x)\n", encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    program = RepresentationProgram(
        grammar_version="RepresentationGrammarV1",
        source_members=(SourceMember("M1", "members/M1.txt", digest),),
        latent_objects=(LatentObject("F1", "MATRIX_FUNCTION", ("z",), "exp(z)"),),
        node_structures=(),
        operators=(Operator("O1", "VALUE", "out", "F1", (), {"node": "x"}),),
        member_assignments=(MemberAssignment("M1", "out", ("O1",)),),
        assumptions_used=(),
        assumption_statuses={},
        obligations=(Obligation("Q1", "M1", "out"),),
    )
    context = CompileContext(
        package_root=tmp_path,
        symbols=({"name": "x", "real": False, "nonzero": False},),
    )

    result = compile_program(program, context)

    assert result.status == "COMPILED"
    assert len(result.obligations) == 1
    assert result.obligations[0].candidate_expression == "exp(x)"

    invalid = RepresentationProgram(
        grammar_version=program.grammar_version,
        source_members=program.source_members,
        latent_objects=(LatentObject("F1", "MATRIX_FUNCTION", ("z",), "Matrix(z)"),),
        node_structures=(),
        operators=program.operators,
        member_assignments=program.member_assignments,
        assumptions_used=(),
        assumption_statuses={},
        obligations=program.obligations,
    )
    failed = compile_program(invalid, context)
    assert failed.status == "COMPILE_FAILURE"
    assert failed.failure_codes == ("LATENT_PARSE_UNDECLARED_OR_DISALLOWED_NAME:F1",)


def test_r6_named_or_source_derived_packages_reproduce_recorded_failures() -> None:
    rows = {item["package_id"]: item for item in _report()["r6_relevant_packages"]}

    assert rows["mx-abba-exp-fixed-r6"]["loader_status"] == "PACKAGE_ARTIFACT_MANIFEST_INVALID"
    assert rows["mx-abba-exp-fixed-r6"]["independent_depth"] == "R2"
    assert rows["rps-r-feshbach-optical-heff"]["loader_status"] == "PACKAGE_ARTIFACT_MANIFEST_INVALID"
    assert rows["rps-r-feshbach-optical-heff"]["independent_depth"] == "R0"
    for package_id in ("gf-vdw-2013-eq1", "rps-candidate-j2-001"):
        assert rows[package_id]["loader_status"] == "COMPILED_NO_SCHEMA_DELTAS"
        assert rows[package_id]["compile_status"] == "COMPILED"
        assert rows[package_id]["schema_deltas"] == []
    assert rows["gf-vdw-2013-eq1"]["independent_depth"] == "R1_DERIVATIVE_RESPONSE_GRAPH"
    assert rows["rps-candidate-j2-001"]["independent_depth"] == "R3_REPEATED_NODE_INELIGIBLE"
    assert all(not row["qualifies"] for row in rows.values())


def test_public_source_members_expose_the_only_packaged_master_candidates() -> None:
    mx = json.loads((
        ROOT
        / R6_RELEVANT_PACKAGES["mx-abba-exp-fixed-r6"]["path"]
        / "reference/program.json"
    ).read_text(encoding="utf-8"))
    mx_ops = {item["operator_id"]: item for item in mx["operators"]}
    assert mx["member_assignments"]["G0005"]["operator_id"] == "O0003"
    assert mx_ops["O0003"]["operator"] == "NEWTON_DD"

    vdw = json.loads((
        ROOT
        / R6_RELEVANT_PACKAGES["gf-vdw-2013-eq1"]["path"]
        / "reference/program.json"
    ).read_text(encoding="utf-8"))
    vdw_ops = {item["operator_id"]: item for item in vdw["operators"]}
    g1 = next(item for item in vdw["member_assignments"] if item["member_id"] == "G0001")
    assert g1["operator_ids"] == ["O0001"]
    assert vdw_ops["O0001"]["operator"] == "VALUE"

    feshbach = json.loads((
        ROOT
        / R6_RELEVANT_PACKAGES["rps-r-feshbach-optical-heff"]["path"]
        / "reference/program.json"
    ).read_text(encoding="utf-8"))
    assert {item["operator"] for item in feshbach["operators"]} == {
        "VALUE",
        "LINEAR_COMBINATION",
    }


def test_no_r6_relevant_package_contains_hash_bound_primary_source_bytes() -> None:
    report = _report()
    for row in report["r6_relevant_packages"]:
        package = ROOT / row["path"]
        source_bytes = [
            path
            for path in package.rglob("*")
            if path.is_file()
            and (
                "upstream" in path.parts
                or path.suffix.casefold() in {".pdf", ".tex", ".html", ".xml"}
            )
        ]
        assert row["stored_source_bytes"] is False
        assert source_bytes == []


def test_static_audit_summary_matches_recomputation() -> None:
    report = _report()
    static = json.loads((
        AUDIT_DIR / "INDEPENDENT_R6_FEASIBILITY_AUDIT.json"
    ).read_text(encoding="utf-8"))

    for key in (
        "schema_version",
        "audited_tree",
        "decision",
        "failure_class",
        "candidate_count",
        "package_created",
        "claim_boundary",
        "qualification_gates",
        "registries",
        "current_case_summary",
        "requested_family_conclusions",
        "qualifying_candidate_ids",
    ):
        assert static[key] == report[key]

    projected = [
        {
            "failure_codes": row["failure_codes"],
            "independent_depth": row["independent_depth"],
            "loader_status": row["loader_status"],
            "package_id": row["package_id"],
            "qualifies": row["qualifies"],
            "source_member_master_exposed": row["source_member_master_exposed"],
        }
        for row in report["r6_relevant_packages"]
    ]
    assert static["r6_relevant_packages"] == projected
