"""Regression tests for fail-closed real-domain package recovery."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path

import pytest

from research.representation_program_search.packages.real_domain_recovery.validate import (
    CANDIDATE,
    FORBIDDEN_PROPOSER_TERMS,
    PACKAGE_IDS,
    _manifest,
    _receipts,
    _source_and_firewall,
    validate,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "research/representation_program_search/packages/real_domain_recovery"


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report():
    return validate(ROOT)


def test_collection_is_candidate_only_and_keeps_missing_slots(report):
    assert report["status"] == "VALID_CANDIDATE_SET"
    assert report["admission_decision"] == "NO_ADMISSION_PERFORMED"
    assert {row["package_id"] for row in report["packages"]} == set(PACKAGE_IDS)
    assert all(row["status"] == CANDIDATE for row in report["packages"])
    assert report["gaps"]["admission_action"] == "NONE"
    assert report["gaps"]["missing_slots"]["R2"]["status"] == "MISSING"
    assert report["gaps"]["missing_slots"]["R6"]["status"] == "MISSING"
    assert "ADMISSION_READY" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in COLLECTION.rglob("*.json")
    )


@pytest.mark.parametrize("package_id", PACKAGE_IDS)
def test_strict_manifest_real_domain_and_proposer_firewall(package_id):
    package = COLLECTION / package_id
    assert _manifest(package)["status"] == "VALID"
    source = _source_and_firewall(package)
    assert source["all_symbols_explicitly_real"] is True
    assert source["assumption_contract_complete"] is True
    assert source["assumptions_hash_bound"] is True
    assert source["catalog_hash_bound"] is True
    assert source["dossier_hash_bound"] is True
    assert source["expected_retrieval_hashes_present"] is True
    assert source["local_source_artifacts_hash_bound"] is True
    assert source["primary_locator_complete"] is True
    assert source["proposer_leaks"] == []
    visible = _json(package / "proposer_view.json")
    visible_blob = json.dumps(visible, sort_keys=True).casefold()
    assert not any(term in visible_blob for term in FORBIDDEN_PROPOSER_TERMS)


@pytest.mark.parametrize("package_id", PACKAGE_IDS)
def test_m1_program_and_both_ablations_compile_non_tautologically(package_id):
    package = COLLECTION / package_id
    loaded = load_case_package(package)
    assert loaded.schema_deltas == ()
    for grammar_id in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"):
        if grammar_id == "G_FULL":
            program = loaded.program
        else:
            program = program_from_dict(
                _json(package / "reference/ablations" / f"{grammar_id}.program.json")
            )
        result = compile_program(
            program,
            CompileContext(
                package.resolve(),
                loaded.context.symbols,
                loaded.context.functions,
                grammar_id=grammar_id,
            ),
        )
        assert result.status == "COMPILED"
        assert result.tautological is False
        assert len(result.obligations) == 3
        assert all(obligation.required for obligation in result.obligations)


@pytest.mark.parametrize("package_id", PACKAGE_IDS)
def test_every_variant_obligation_has_main_proposal_then_exact_zero(package_id):
    package = COLLECTION / package_id
    receipts = _receipts(package)
    assert receipts["errors"] == []
    assert receipts["attempt_count"] == 9
    assert receipts["all_zero"] is True
    assert all(all(row["checks"].values()) for row in receipts["rows"])
    obligations = _json(package / "reference/obligations.json")
    assert obligations["summary"] == {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 3}
    for row in obligations["obligations"]:
        assert row["verdict"] == "ZERO"
        assert row["proof_status"] == "PROVEN"
        assert (
            hashlib.sha256((package / row["current_path"]).read_bytes()).hexdigest()
            == row["current_sha256"]
        )
        assert (
            hashlib.sha256((package / row["candidate_path"]).read_bytes()).hexdigest()
            == row["candidate_sha256"]
        )
        assert (package / row["step_path"]).is_file()


def test_r3_repeated_nodes_are_not_required_as_named_primitives():
    package = COLLECTION / "rps-real-c3j9"
    full = _json(package / "reference/program.json")
    primitive = _json(package / "reference/ablations/G_PRIMITIVE.program.json")
    assert [row["nodes"] for row in full["node_structures"]] == [
        ["x", "y"],
        ["x", "x", "y"],
        ["x", "y", "y"],
    ]
    assert {row["operator"] for row in primitive["operators"]} <= {
        "VALUE",
        "DERIVATIVE",
        "SUBSTITUTE",
        "LINEAR_COMBINATION",
        "COMPOSE",
    }
    assert "HERMITE_DD" not in {row["operator"] for row in primitive["operators"]}


def test_r5_package_keeps_depth_downgrade_risk_explicit():
    review = _json(COLLECTION / "rps-real-c8q2/reference/review.json")
    assert review["candidate_status"] == CANDIDATE
    assert "depth_downgrade_risk" in review
    assert review["grammar_assessment"]["named_primitive_required"] is False
