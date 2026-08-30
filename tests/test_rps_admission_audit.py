"""Focused contracts for the fail-closed RPS admission audit."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.representation_program_search.audits.admission.audit import (
    AUDIT_VERSION,
    AuditError,
    JSON_OUTPUT,
    MARKDOWN_OUTPUT,
    REVIEWS_PATH,
    _machine_package,
    build_audit,
    check_outputs,
    discover_dossiers,
)


EXPECTED_STATUS_COUNTS = {
    "ADMISSION_CANDIDATE": 0,
    "PACKAGING_GAP": 27,
    "PROBLEM_UNDERSPECIFIED": 1,
    "DUPLICATE_REVIEW": 8,
    "REJECT": 3,
}


def test_all_non_skeptic_dossiers_are_covered_once():
    dossiers = discover_dossiers()
    assert len(dossiers) == 39
    assert {cluster for cluster, _, _ in dossiers} == {
        "matrix", "thermal", "response", "tensor", "diffphys"
    }
    ids = [dossier["case_id"] for _, _, dossier in dossiers]
    assert len(ids) == len(set(ids))
    reviews = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))["cases"]
    assert set(reviews) == set(ids)


def test_fail_closed_status_counts_and_no_silent_admission():
    audit = build_audit()
    assert audit["audit_version"] == AUDIT_VERSION
    assert audit["summary"]["total"] == 39
    assert audit["summary"]["by_status"] == EXPECTED_STATUS_COUNTS
    assert audit["summary"]["machine_packages_parseable"] == 0
    assert audit["summary"]["frozen_source_artifact_references"] == 0
    assert all(row["primary_status"] != "ADMISSION_CANDIDATE" for row in audit["cases"])


def test_sketch_is_never_mistaken_for_a_machine_package():
    audit = build_audit()
    assert audit["policy"]["expression_sketch_is_verifier_input"] is False
    for row in audit["cases"]:
        assert row["machine_package"]["status"] == "ABSENT"
        assert row["machine_package"]["member_count"] == 0
        assert "expression_sketch is context" in row["machine_package"]["reason"]


def test_primary_status_keeps_scientific_failures_visible_over_packaging():
    audit = build_audit()
    by_id = {row["case_id"]: row for row in audit["cases"]}
    assert by_id["rps-r-birman-schwinger-kernel"]["primary_status"] == (
        "PROBLEM_UNDERSPECIFIED"
    )
    assert {case_id for case_id, row in by_id.items() if row["primary_status"] == "REJECT"} == {
        "rps-r-fano-beutler-profile",
        "rps-r-lorentz-causal-poles",
        "rps-r-schrieffer-wolff-denom",
    }
    assert all(by_id[case_id]["machine_package"]["status"] == "ABSENT" for case_id in (
        "rps-r-birman-schwinger-kernel",
        "rps-r-fano-beutler-profile",
        "rps-r-lorentz-causal-poles",
        "rps-r-schrieffer-wolff-denom",
    ))


def test_duplicate_review_is_explicit_and_not_partition_selection():
    audit = build_audit()
    duplicates = {
        row["case_id"]: row["duplicate_with"]
        for row in audit["cases"]
        if row["primary_status"] == "DUPLICATE_REVIEW"
    }
    assert len(duplicates) == 8
    assert duplicates["mx-rodrigues-so3-01"] == ["rps-dp-rodrigues-so3-dexp"]
    assert duplicates["rps-dp-rodrigues-so3-dexp"] == ["mx-rodrigues-so3-01"]
    assert "ac-t-pauli-completeness" in duplicates["rps-t-dirac-gamma-completeness"]
    assert "sciml-phi-hermite-01" in duplicates["rps-dp-skaflestad-wright-phisq"]


def test_depth_and_parser_axes_are_complete():
    audit = build_audit()
    assert audit["summary"]["by_depth_assessment"] == {
        "PLAUSIBLE": 34,
        "NEEDS_DOWNGRADE": 3,
        "NOT_OPERATIONAL_AT_PROPOSED_DEPTH": 2,
    }
    assert audit["summary"]["by_parser_fit"] == {
        "REPRESENTABLE_AFTER_PACKAGING": 4,
        "REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING": 15,
        "NOT_REPRESENTABLE_UNDER_FROZEN_PARSER": 20,
    }
    assert all(row["parser_blockers"] for row in audit["cases"])


def test_citations_are_not_overclaimed_as_frozen_source_evidence():
    audit = build_audit()
    assert all(row["source_citation_count"] > 0 for row in audit["cases"])
    assert all(
        row["provenance_status"] == "CITATIONS_PRESENT_SOURCE_NOT_FROZEN"
        for row in audit["cases"]
    )
    assert all(
        row["nonfabricated_status"]
        == "NO_FABRICATION_SIGNAL_CITATIONS_NOT_SOURCE_AUTHENTICATED"
        for row in audit["cases"]
    )


def test_explicit_package_is_parsed_from_files_not_sketch(tmp_path: Path):
    (tmp_path / "m1.txt").write_text("x + 1\n", encoding="utf-8")
    (tmp_path / "m2.txt").write_text("1 + x\n", encoding="utf-8")
    (tmp_path / "o1.txt").write_text("x + 1\n", encoding="utf-8")
    (tmp_path / "symbols.json").write_text(
        json.dumps({"symbols": ["x"]}) + "\n", encoding="utf-8"
    )
    dossier_path = tmp_path / "case.json"
    dossier_path.write_text("{}\n", encoding="utf-8")
    dossier = {
        "expression_sketch": "this is deliberately not parseable prose",
        "admission_package": {
            "member_files": ["m1.txt", "m2.txt"],
            "obligation_files": ["o1.txt"],
            "symbols_file": "symbols.json",
        },
    }
    result = _machine_package(dossier, dossier_path)
    assert result["status"] == "PARSEABLE"
    assert result["member_count"] == 2
    assert result["obligation_count"] == 1


def test_package_paths_cannot_escape_case_directory(tmp_path: Path):
    outside = tmp_path.parent / "outside-symbols.json"
    outside.write_text(json.dumps({"symbols": ["x"]}), encoding="utf-8")
    dossier_path = tmp_path / "case.json"
    dossier_path.write_text("{}\n", encoding="utf-8")
    result = _machine_package({
        "admission_package": {
            "member_files": ["m1.txt", "m2.txt"],
            "obligation_files": ["o1.txt"],
            "symbols_file": "../outside-symbols.json",
        }
    }, dossier_path)
    assert result["status"] == "UNPARSEABLE"
    assert result["reason"] == "SYMBOL_NAMESPACE_UNREADABLE"


def test_committed_artifacts_are_deterministic_and_current():
    assert JSON_OUTPUT.is_file()
    assert MARKDOWN_OUTPUT.is_file()
    check_outputs(build_audit())


def test_index_count_mismatch_fails_closed(tmp_path: Path):
    for cluster in ("matrix", "thermal", "response", "tensor", "diffphys"):
        directory = tmp_path / cluster
        directory.mkdir(parents=True)
        (directory / "index.json").write_text(
            json.dumps({"count": 1, "dossiers": []}), encoding="utf-8"
        )
    with pytest.raises(AuditError, match="INDEX_COUNT_MISMATCH"):
        discover_dossiers(tmp_path)
