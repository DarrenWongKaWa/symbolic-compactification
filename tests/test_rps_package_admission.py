from __future__ import annotations

import json
from pathlib import Path

from research.representation_program_search.audits.package_admission.audit import (
    audit_repository,
    render_markdown,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = (
    ROOT
    / "research"
    / "representation_program_search"
    / "audits"
    / "package_admission"
)


def _report() -> dict:
    return audit_repository(ROOT)


def _by_id(report: dict) -> dict[str, dict]:
    return {row["package_id"]: row for row in report["packages"]}


def test_generated_artifacts_are_deterministic() -> None:
    report = _report()
    expected_json = json.dumps(
        report, sort_keys=True, indent=2, ensure_ascii=False
    ) + "\n"
    assert (AUDIT_DIR / "PACKAGE_ADMISSION_AUDIT.json").read_text() == expected_json
    assert (AUDIT_DIR / "PACKAGE_ADMISSION_AUDIT.md").read_text() == render_markdown(report)


def test_exact_package_coverage_and_no_partition_selection() -> None:
    report = _report()
    assert report["package_count"] == 13
    assert report["admission_ready_count"] == 0
    assert report["admission_ready_packages"] == []
    assert report["selects_test"] is False
    assert report["frozen_parser_modified"] is False
    assert report["gold_programs_modified"] is False
    assert report["schema_repair_sufficient_for_admission"] is False
    assert report["dev_calibration_recommendation"]["selected_packages"] == []
    assert all(
        detail["status"] == "MISSING"
        for detail in report["dev_calibration_recommendation"]["slots"].values()
    )
    assert report["dev_calibration_recommendation"]["negative_trap"]["status"] == (
        "EVALUATOR_ONLY_SEPARATE"
    )


def test_parser_hash_receipt_and_member_coverage_gates_are_evidence_backed() -> None:
    report = _report()
    for row in report["packages"]:
        assert row["parser"]["all_machine_expressions_parse"] is True
        assert row["manifest"]["hash_integrity"] is True
        assert row["manifest"]["manifest_coverage_complete"] is True
        assert row["obligations"]["member_coverage_complete"] is True
        assert row["obligations"]["receipt_errors"] == []


def test_m1_fails_closed_without_repairing_legacy_links() -> None:
    rows = _by_id(_report())
    thermal = [row for row in rows.values() if row["family"] == "thermal"]
    assert len(thermal) == 6
    for row in thermal:
        assert row["m1"]["loader_status"] == "LOADED"
        assert row["m1"]["compile_status"] == "COMPILE_FAILURE"
        assert row["m1"]["compile_failure_codes"] == ["OPERATOR_OUTPUT_MISSING:OP0"]
        assert row["m1"]["schema_deltas"] == [
            "SOURCE_MEMBERS_INJECTED_FROM_EXACT_CATALOG",
            "ASSUMPTION_STATUSES_INJECTED_FROM_EXACT_CONTRACT",
            "EXECUTABLE_OPERATOR_OUTPUTS_MISSING",
            "EXECUTABLE_ASSIGNMENT_OUTPUTS_MISSING",
            "EXECUTABLE_OBLIGATION_OUTPUT_LINKS_MISSING",
            "LEGACY_PROGRAM_ID_IS_NOT_M1_ALPHA_NORMALIZED_HASH",
        ]
        assert "SCHEMA_GAP" in row["dispositions"]

    nonthermal = [row for row in rows.values() if row["family"] != "thermal"]
    assert len(nonthermal) == 7
    for row in nonthermal:
        assert row["m1"]["loader_status"] == "LOAD_FAILURE"
        assert row["m1"]["loader_error"] == "PACKAGE_ARTIFACT_MANIFEST_INVALID"
        assert row["manifest"]["artifact_field"] == "artifacts"
        assert row["manifest"]["strict_rps_case_package_v1"] is False


def test_proof_and_domain_axes_remain_separate() -> None:
    rows = _by_id(_report())
    oscillator = rows["dp-oscillator-confluent-fixed-r4"]
    assert oscillator["assumptions"]["independent_assumption_status"] == "DECLARED"
    assert oscillator["obligations"]["required_verdict_counts"] == {
        "UNKNOWN": 1,
        "ZERO": 4,
    }
    assert oscillator["obligations"]["restricted_replays"][0]["eligibility"] == (
        "INELIGIBLE_RESTRICTED_REPLAY"
    )
    assert "PROOF_REQUIRED" in oscillator["dispositions"]

    thermal_10 = rows["thermal-10-polygamma-order2-recurrence"]
    assert thermal_10["assumptions"]["independent_assumption_status"] == "HUMAN_REQUIRED"
    assert "HUMAN_REQUIRED" in thermal_10["dispositions"]
    assert "PROOF_REQUIRED" in thermal_10["dispositions"]


def test_depth_is_independent_and_tensor_replays_are_diagnostic_only() -> None:
    rows = _by_id(_report())
    assert rows["mx-abba-exp-fixed-r6"]["depth"]["independent_depth"] == "R2"
    assert rows["rps-r-feshbach-optical-heff"]["depth"]["independent_depth"] == "R0"
    for package_id in ("rps-t-barnes-rivers-dn", "rps-t-stf-son-rank3"):
        row = rows[package_id]
        assert row["depth"]["independent_depth"] == "DIAGNOSTIC_ONLY"
        assert "DIAGNOSTIC_ONLY" in row["dispositions"]
        assert row["fair_comparison_eligible"] is False


def test_projection_and_duplicate_review_are_explicit() -> None:
    rows = _by_id(_report())
    for package_id in (
        "thermal-09-digamma-newton",
        "thermal-09-digamma-newton-z1",
        "thermal-10-polygamma-order2-recurrence",
    ):
        assert "LEAKAGE_REVIEW" in rows[package_id]["dispositions"]
    hermite = rows["mx-sqrt-hermite-fixed-r3"]
    assert hermite["current_pool_duplicates"]["exact_member_overlaps"]
    assert "DUPLICATE_REVIEW" in hermite["dispositions"]
    assert hermite["depth"]["named_primitive_giveaway"].startswith("CRITICAL")
