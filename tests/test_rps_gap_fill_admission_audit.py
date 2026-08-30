from __future__ import annotations

import json

from research.representation_program_search.audits.gap_fill_admission import audit


def test_gap_fill_admission_audit_is_fail_closed_and_reproducible() -> None:
    report = audit.audit()
    committed = json.loads(audit.OUTPUT_JSON.read_text(encoding="utf-8"))

    assert report == committed
    assert audit.render_markdown(report) == audit.OUTPUT_MD.read_text(encoding="utf-8")
    assert report["verdict"] == "ZERO_ADMISSIONS"
    assert report["admission_ready_count"] == 0
    assert report["scientific_packages_modified"] is False


def test_cr3bp_is_exact_r2_but_not_admission_ready() -> None:
    report = audit.audit()
    row = {item["case_id"]: item for item in report["cases"]}["gf-cr3bp-2017-eq28"]

    assert row["depth"]["independent"] == "R2"
    assert row["receipts"]["summary"] == {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 4}
    assert row["ablations"]["G_FULL"]["status"] == "COMPILED"
    assert row["ablations"]["G_NO_HERMITE"]["status"] == "COMPILED"
    assert row["ablations"]["G_PRIMITIVE"]["status"] == "COMPILE_FAILURE"
    assert "PUBLIC_NAMESPACE_MISMATCH" in row["blocking_findings"]
    assert "SOURCE_BYTES_UNBOUND" in row["blocking_findings"]
    assert row["admission_ready"] is False


def test_vdw_is_exact_but_depth_downgraded_from_r6() -> None:
    report = audit.audit()
    row = {item["case_id"]: item for item in report["cases"]}["gf-vdw-2013-eq1"]

    assert row["depth"]["independent"] == "R1_DERIVATIVE_RESPONSE_GRAPH"
    assert row["receipts"]["summary"] == {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 8}
    assert row["ablations"]["G_PRIMITIVE"]["status"] == "COMPILED"
    assert row["program_shape"]["source_member_exposes_master"] is True
    assert row["program_shape"]["single_use_reciprocal_wrapper"] is True
    assert "DEPTH_DOWNGRADED" in row["blocking_findings"]
    assert row["admission_ready"] is False


def test_actual_public_loader_exposes_namespace_drift_for_both_packages() -> None:
    for row in audit.audit()["cases"]:
        public = row["public_boundary"]
        assert public["namespace_provenance"] == "INFERRED_PUBLIC_EXPRESSION_INSPECTION"
        assert public["symbols_json_accessed"] is False
        assert public["namespace_matches_exact_symbols"] is False
        assert all(symbol["real"] is False for symbol in public["public_symbols"])


def test_independent_source_retrievals_are_exactly_recorded() -> None:
    report = audit.audit()

    assert len(report["source_retrievals"]) == 4
    assert all(len(row["sha256"]) == 64 for row in report["source_retrievals"])
    assert all(row["bytes"] > 0 for row in report["source_retrievals"])
    assert all(row["locator_verified"] for row in report["source_retrievals"])
    assert all(
        row["source"]["retrieved_source_artifact_hash_count"] == 0
        and row["source"]["strict_retrieved_source_binding"] is False
        for row in report["cases"]
    )
