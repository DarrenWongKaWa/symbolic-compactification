from __future__ import annotations

import json
from pathlib import Path

from research.representation_program_search.audits.r4_r5_candidate_recovery.audit import (
    HERE,
    REPORT_JSON,
    run_audit,
)


def test_negative_boundary_report_is_current_and_fail_closed() -> None:
    report = run_audit()
    assert report == json.loads(REPORT_JSON.read_text(encoding="utf-8"))
    assert report["status"] == "VALID_NEGATIVE_BOUNDARY"
    assert report["candidate_count"] == 0
    assert report["honest_case_remaining"] is False
    assert report["slot_disposition"]["R4_R5"] == "MISSING"
    assert report["package_status"] == "NO_PACKAGE_CREATED"
    assert report["public_loader"] == {
        "reason": "NO_RETAINED_CANDIDATE",
        "status": "NOT_APPLICABLE",
    }
    assert report["m1_compile"] == report["public_loader"]


def test_source_bytes_locators_and_formula_hashes_are_frozen() -> None:
    report = run_audit()
    sources = {
        row["source_id"]: row
        for row in report["source_provenance"]["sources"]
    }
    assert (sources["SRC-A"]["artifact_bytes"], sources["SRC-A"]["artifact_sha256"]) == (
        307489,
        "210afa1d3b8548b805c754a9757e790175405d55114fc8fd87631845b5c2b0ff",
    )
    assert (sources["SRC-B"]["artifact_bytes"], sources["SRC-B"]["artifact_sha256"]) == (
        301757,
        "6f690b01de0ce95ad450a5233ffc470ba6ca1b2b84c744a8f7fe98fd1f3f31f1",
    )
    assert all(
        equation["locator"] and len(equation["formula_sha256"]) == 64
        for source in sources.values()
        for equation in source["equations"]
    )


def test_old_test_variants_are_rejected_not_relabelled() -> None:
    report = run_audit()
    by_id = {row["candidate_id"]: row for row in report["screened_leads"]}
    assert "OLD_TEST_VARIANT:test-a-newton-first" in by_id["SCREEN-A"]["reasons"]
    assert "OLD_TEST_VARIANT:test-b-piecewise-dd" in by_id["SCREEN-A"]["reasons"]
    assert "OLD_TEST_VARIANT:test-a-hermite-two" in by_id["SCREEN-B"]["reasons"]
    assert all(row["disposition"] == "REJECTED" for row in by_id.values())
    assert report["historical_duplicate_audit"]["status"] == "VALID"


def test_diagnostic_receipts_preserve_zero_nonzero_unknown() -> None:
    report = run_audit()
    receipts = {
        row["diagnostic_id"]: row
        for row in report["diagnostic_receipts"]["receipts"]
    }
    assert {key: row["verdict"] for key, row in receipts.items()} == {
        "D001": "ZERO",
        "D002": "NONZERO",
        "D003": "UNKNOWN",
        "D004": "ZERO",
    }
    assert receipts["D002"]["checks"]["exact_counterexample"] is True
    assert receipts["D003"]["checks"]["unknown_fail_closed"] is True
    assert all(all(row["checks"].values()) for row in receipts.values())


def test_no_candidate_package_or_public_view_was_created() -> None:
    assert not (HERE / "package.json").exists()
    assert not (HERE / "proposer_view.json").exists()
    assert not (
        Path(__file__).resolve().parents[1]
        / "research/representation_program_search/packages/r4_r5_candidate_recovery"
    ).exists()
