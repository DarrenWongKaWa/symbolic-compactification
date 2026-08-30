from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from research.representation_program_search.packages.fresh_r3.validate import (
    FreshR3ValidationError,
    PACKAGE,
    PUBLIC_PATHS,
    SOURCE_EXCERPT_SHA256,
    _sha,
    validate,
)
from research.representation_program_search.program_ir import (
    compile_program,
    load_case_package,
)
from research.representation_program_search.search import (
    SearchContractError,
    load_public_case,
)


def _read(relative: str):
    return json.loads((PACKAGE / relative).read_text(encoding="utf-8"))


def test_fresh_r3_candidate_clears_all_fail_closed_gates():
    result = validate()
    assert result["status"] == "VALID_CANDIDATE"
    assert result["admission_status"] == "CANDIDATE_FOR_INDEPENDENT_REVIEW"
    assert result["receipt_count"] == 9
    assert result["public_accessed_paths"] == sorted(PUBLIC_PATHS)
    assert all(
        item == {"obligations": 3, "status": "COMPILED", "tautological": False}
        for item in result["compiled_variants"].values()
    )


def test_public_loader_succeeds_without_evaluator_paths_or_target_terms():
    case = load_public_case(PACKAGE / "proposer_view.json")
    assert case.case_id == "Q7V3"
    assert set(case.accessed_paths) == PUBLIC_PATHS
    assert all(
        not any(part in {"reference", "verification", "source"} for part in Path(path).parts)
        for path in case.accessed_paths
    )
    assert tuple(member.member_id for member in case.members) == ("M01", "M02", "M03")
    visible = "\n".join(
        (PACKAGE / relative).read_text(encoding="utf-8")
        for relative in sorted(PUBLIC_PATHS)
    ).casefold()
    for forbidden in (
        "hermite",
        "divided difference",
        "frechet",
        "fréchet",
        "multiplicity",
        "repeated node",
        "operator sequence",
        "target representation",
    ):
        assert forbidden not in visible


def test_public_member_tamper_fails_at_hash_boundary(tmp_path):
    package = tmp_path / PACKAGE.name
    shutil.copytree(PACKAGE, package)
    (package / "members/M02.txt").write_text("0\n", encoding="utf-8")
    with pytest.raises(SearchContractError, match="PUBLIC_HASH_MISMATCH"):
        load_public_case(package / "proposer_view.json")


def test_m1_loader_has_no_schema_delta_and_compile_is_non_tautological():
    loaded = load_case_package(PACKAGE)
    assert loaded.schema_deltas == ()
    compiled = compile_program(loaded.program, loaded.context)
    assert compiled.status == "COMPILED"
    assert compiled.failure_codes == ()
    assert compiled.tautological is False
    assert len(compiled.obligations) == 3


def test_multiplicity_is_evaluator_only_and_is_genuinely_arity_four():
    program = _read("reference/program.json")
    assert {
        row["node_id"]: row["nodes"] for row in program["node_structures"]
    } == {
        "N01": ["a", "a", "b", "b"],
        "N02": ["a", "a", "b", "c"],
        "N03": ["a", "b", "c", "c"],
    }
    public = "\n".join(
        (PACKAGE / relative).read_text(encoding="utf-8")
        for relative in sorted(PUBLIC_PATHS)
    )
    assert '"nodes"' not in public
    assert '"node_structures"' not in public
    assert '"representation_depth"' not in public


def test_named_hermite_is_not_required_by_the_reference_ablations():
    allowed = {"VALUE", "DERIVATIVE", "SUBSTITUTE", "LINEAR_COMBINATION", "COMPOSE"}
    for grammar in ("G_NO_HERMITE", "G_PRIMITIVE"):
        program = _read(f"reference/ablations/{grammar}.program.json")
        operators = {row["operator"] for row in program["operators"]}
        assert operators <= allowed
        assert "HERMITE_DD" not in operators
        assert program["node_structures"] == []
    review = _read("reference/review.json")
    assert review["grammar_assessment"]["named_primitive_required"] is False
    assert "expressibility only" in review["grammar_assessment"]["scope_note"]


def test_all_variant_obligations_have_hash_bound_zero_session_receipts():
    index = _read("verification/index.json")
    assert len(index["attempts"]) == 9
    assert {
        (row["program_variant"], row["obligation_id"])
        for row in index["attempts"]
    } == {
        (grammar, obligation)
        for grammar in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
        for obligation in ("O01", "O02", "O03")
    }
    for row in index["attempts"]:
        run = PACKAGE / "verification/workspace/runs" / row["run_id"]
        proposal = json.loads((run / "steps/step_001.json").read_text(encoding="utf-8"))
        receipt = json.loads((run / "steps/step_002.json").read_text(encoding="utf-8"))
        assert proposal["status"] == "HYPOTHESIS"
        assert receipt["verdict"] == "ZERO"
        assert receipt["status"] == "CERTIFIED"
        assert receipt["proof_status"] == "PROVEN"
        assert receipt["current_hash"] == _sha(PACKAGE / f"members/{row['member_id']}.txt")
        assert receipt["candidate_hash"] == _sha(PACKAGE / row["candidate_path"])


def test_primary_equation_bytes_and_domain_artifacts_are_hash_bound():
    source = _read("source_manifest.json")
    row = source["sources"][0]
    assert row["doi"] == "10.1016/j.laa.2022.10.005"
    assert row["arxiv_version"] == "2203.03930v2"
    assert "Theorem 2, equations (8)--(9)" in row["journal_locator"]
    assert row["stored_artifact"]["sha256"] == SOURCE_EXCERPT_SHA256
    assert _sha(PACKAGE / row["stored_artifact"]["path"]) == SOURCE_EXCERPT_SHA256
    for binding in ("assumption_contract", "assumption_locators", "symbol_namespace"):
        artifact = source[binding]
        assert _sha(PACKAGE / artifact["path"]) == artifact["sha256"]


def test_duplicate_audit_explicitly_covers_old_test_c3j9_and_phi_family():
    audit = _read("source/duplicate_audit.json")
    assert audit["exact_byte_audit"]["candidate_vs_current_member_overlap"] == []
    assert audit["exact_byte_audit"]["candidate_vs_historical_expression_overlap"] == []
    assert audit["explicit_json_node_signature_matches"] == []
    assert {row["identity"] for row in audit["manual_structural_anchors"]} == {
        "C3J9",
        "test-a-hermite-two",
        "sciml-phi-hermite-01",
    }
    assert audit["candidate_signatures"]["M01"] == {
        "arity": 4,
        "multiplicity_partition": [2, 2],
    }


def test_validator_rejects_any_hash_tamper(tmp_path):
    package = tmp_path / PACKAGE.name
    shutil.copytree(PACKAGE, package)
    (package / "source/lowering.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(FreshR3ValidationError, match="ARTIFACT_HASH"):
        validate(package)
