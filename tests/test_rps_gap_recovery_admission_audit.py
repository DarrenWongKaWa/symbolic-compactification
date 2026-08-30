from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.representation_program_search.audits.gap_recovery_admission.audit import (
    AUDITED_COMMIT,
    EXCERPTS,
    PACKAGE_REL,
    PREDECESSOR_REL,
    PREDECESSOR_TREE_SHA256,
    ROOT,
    SOURCE_ARCHIVE_SHA256,
    SOURCE_TEX_SHA256,
    audit,
)


AUDIT_DIR = (
    ROOT
    / "research/representation_program_search/audits/gap_recovery_admission"
)


@pytest.fixture(scope="module")
def report():
    return audit(ROOT)


def test_independent_recovery_decision_is_admission_ready_r2_only(report):
    assert report["status"] == "PASS"
    assert report["decision"] == "ADMISSION_READY"
    assert report["admission_scope"] == "DEV_R2_CALIBRATION_ONLY"
    assert report["audited_commit"] == AUDITED_COMMIT
    assert report["audited_package"] == PACKAGE_REL
    assert all(section["status"] == "PASS" for section in report["sections"].values())
    assert "THIS_R2_CALIBRATION_CASE_DOES_NOT_ADDRESS_THE_PRIMARY_R3_PLUS_FRONTIER" in report["limitations"]


def test_primary_source_was_independently_retrieved_and_all_excerpt_bytes_match(report):
    source = report["sections"]["primary_source"]
    retrieval = source["independent_retrieval"]
    assert retrieval["source_archive_sha256"] == SOURCE_ARCHIVE_SHA256
    assert retrieval["source_file_sha256"] == SOURCE_TEX_SHA256
    assert retrieval["source_file_line_count"] == 1179
    assert retrieval["stored_excerpt_comparison"] == "ALL_SIX_CMP_IDENTICAL"
    assert source["source_excerpt_hashes"] == EXCERPTS
    assert source["errors"] == []
    assert all(source["official_metadata_checks"][key] is True for key in (
        "authors_match", "doi_match", "title_match", "venue_pages_match"
    ))


def test_public_loader_uses_exact_real_namespace_and_no_evaluator_paths(report):
    public = report["sections"]["assumptions_and_public_boundary"]
    assert public["namespace_provenance"] == "EXACT_PROPOSER_REFERENCE"
    assert len(public["symbols"]) == 8
    assert all(symbol["real"] is True for symbol in public["symbols"])
    assert public["assumption_statuses"] == {
        "P9A1": "DECLARED",
        "P9A2": "DECLARED",
        "P9A3": "DECLARED",
        "P9A4": "DERIVED",
    }
    assert public["public_target_terms"] == []
    assert all(
        not ({"reference", "verification", "runs", "steps"} & set(Path(path).parts))
        for path in public["accessed_paths"]
    )
    assert "PUBLIC_EXPRESSIONS_ARE_ALREADY_FACTORIZED" in public["easiness_risks"]


def test_m1_programs_are_canonical_nontautological_and_true_r2(report):
    compilation = report["sections"]["compilation_and_depth"]
    assert compilation["loader_schema_deltas"] == []
    assert compilation["depth"]["assessment"] == "R2_NEWTON_DD"
    assert compilation["depth"]["not_tautological"] is True
    assert compilation["depth"]["not_r3"] == "No repeated node appears."
    assert compilation["named_primitive_required"] is False
    assert compilation["primitive_operator_set"] == ["LINEAR_COMBINATION", "VALUE"]
    assert set(compilation["variants"]) == {"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"}
    for row in compilation["variants"].values():
        assert row["status"] == "COMPILED"
        assert row["tautological"] is False
        assert row["obligation_count"] == 4
        assert len(row["canonical_program_hash"]) == 64


def test_all_session_receipts_are_bound_and_independently_replay_zero(report):
    receipts = report["sections"]["receipts"]
    assert receipts["stored_receipt_count"] == 12
    assert receipts["replayed_zero"] == 12
    assert {
        (row["grammar"], row["obligation_id"])
        for row in receipts["independent_replay"]
    } == {
        (grammar, f"Q9H{number}")
        for grammar in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
        for number in range(1, 5)
    }
    assert all(row["recorded_receipt_valid"] for row in receipts["independent_replay"])
    assert all(row["independent_verdict"] == "ZERO" for row in receipts["independent_replay"])


def test_exact_predecessor_copies_are_versioned_repair_not_second_identity(report):
    duplicate = report["sections"]["duplicate_and_identity_status"]
    assert duplicate["exact_matches"] == [
        f"{PREDECESSOR_REL}/members/G{number:04d}.txt"
        for number in range(1, 5)
    ]
    assert duplicate["renamed_matches"] == []
    assert duplicate["predecessor_tree_sha256"] == PREDECESSOR_TREE_SHA256
    assert duplicate["predecessor_file_count"] == 33
    assert duplicate["repair_of_newly_mined_identity"] is True
    assert duplicate["fresh_identity_claim"] is False
    assert duplicate["method_run_references"] == []
    assert duplicate["manifest_references"] == []
    assert "Count the pair as one scientific identity" in duplicate["admission_interpretation"]


def test_static_audit_is_exact_replay_of_independent_auditor(report):
    stored = json.loads(
        (AUDIT_DIR / "INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json").read_text(
            encoding="utf-8"
        )
    )
    assert stored == report


def test_audit_is_read_only_with_respect_to_candidate_and_predecessor(report):
    assert report["package_mutated_by_audit"] is False
    assert (ROOT / PACKAGE_REL / "package.json").is_file()
    assert (ROOT / PREDECESSOR_REL / "package.json").is_file()
