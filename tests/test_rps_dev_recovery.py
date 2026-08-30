from __future__ import annotations

import json
from pathlib import Path

from research.representation_program_search.packages.dev_recovery.validate import validate


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = (
    ROOT
    / "research"
    / "representation_program_search"
    / "packages"
    / "dev_recovery"
    / "rps-candidate-j2-001"
)


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_recovery_validator_accepts_only_fail_closed_gap_evidence():
    report = validate(ROOT)
    assert report["status"] == "VALID_PACKAGING_GAP_EVIDENCE"
    assert report["admission_decision"] == "PACKAGING_GAP"
    assert all(report["hard_checks"].values())
    assert report["receipts"]["domain_eligibility"] == (
        "INELIGIBLE_REAL_FALSE_CONTRACT_DEFECT"
    )


def test_m1_native_programs_compile_without_schema_repair_but_cannot_admit():
    report = validate(ROOT)
    programs = report["compiled_programs"]
    assert programs["loader_schema_deltas"] == []
    assert programs["full"]["status"] == "COMPILED"
    assert programs["full"]["tautological"] is False
    assert ["x", "x", "y"] in programs["full_repeated_node_shapes"]
    assert ["x", "y", "y"] in programs["full_repeated_node_shapes"]
    assert programs["primitive"]["status"] == "COMPILED"
    assert programs["no_hermite_compositional"]["status"] == "COMPILED"
    assert _json(PACKAGE / "package.json")["package_status"] == "PACKAGING_GAP"
    assert _json(PACKAGE / "package.json")["eligibility"] == "INELIGIBLE"


def test_all_recorded_zero_receipts_are_hash_bound_and_explicitly_ineligible():
    receipts = validate(ROOT)["receipts"]
    assert receipts["attempt_count"] == 8
    assert receipts["all_zero"] is True
    assert all(all(row["checks"].values()) for row in receipts["rows"])
    assert receipts["domain_eligibility"].startswith("INELIGIBLE_")


def test_source_and_proposer_firewall_are_hash_bound_and_opaque():
    source = validate(ROOT)["source_and_firewall"]
    assert source["assumptions_hash_bound"] is True
    assert source["catalog_hash_bound"] is True
    assert source["dossier_exact_copy"] is True
    assert source["opaque_case_id"] is True
    assert source["opaque_member_ids"] is True
    assert source["primary_locator_complete"] is True
    assert source["proposer_leaks"] == []


def test_recovery_leaves_every_requested_depth_slot_missing():
    gaps = _json(
        ROOT
        / "research"
        / "representation_program_search"
        / "packages"
        / "dev_recovery"
        / "RECOVERY_GAPS.json"
    )["slots"]
    assert set(gaps) == {"R2", "R3", "R4_R5", "R6"}
    assert gaps["R2"]["disposition"] == "MISSING"
    assert gaps["R3"]["disposition"] == "PACKAGING_GAP"
    assert gaps["R4_R5"]["disposition"] == "PACKAGING_GAP"
    assert gaps["R6"]["disposition"] == "MISSING"
    assert "without human authorization" in gaps["R4_R5"]["reason"]


def test_recovery_audit_has_no_admission_path():
    report = _json(
        ROOT
        / "research"
        / "representation_program_search"
        / "audits"
        / "dev_recovery"
        / "RECOVERY_AUDIT.json"
    )
    assert report["admission_decision"] == "PACKAGING_GAP"
    assert report["status"] == "VALID_PACKAGING_GAP_EVIDENCE"
    assert report["hard_checks"]["zero_receipts_ineligible"] is True
