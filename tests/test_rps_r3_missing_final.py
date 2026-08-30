from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.representation_program_search.audits.r3_missing_final import validate as audit_module
from research.representation_program_search.audits.r3_missing_final.validate import (
    AUDIT,
    R3MissingAuditError,
    validate,
)


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_final_bounded_pass_fails_closed_without_a_candidate():
    result = validate()
    assert result == {
        "admission_ready_count": 0,
        "authority_head": "bcb43e25c0b529fcf172d545e852577848d2135c",
        "corpus_file_count": 117,
        "screened_source_count": 3,
        "status": "VALID_R3_MISSING_AUDIT",
        "verdict": "R3_MISSING",
    }


def test_each_screen_has_version_pinned_primary_bytes_and_exact_locators():
    audit = _read(AUDIT)
    assert {row["primary_source"]["arxiv_id_version"] for row in audit["screened_families"]} == {
        "1509.05030v2",
        "2306.15814v1",
        "1504.00960v2",
    }
    for row in audit["screened_families"]:
        source = row["primary_source"]
        assert source["archive_url"].endswith(source["arxiv_id_version"])
        assert len(source["archive_sha256"]) == 64
        assert len(source["tex_sha256"]) == 64
        assert source["tex_byte_count"] > 70_000
        assert row["locators"]
        assert row["freshness_assessment"] == "FAIL"
        assert row["disposition"] == "REJECT_NO_PACKAGE"


def test_complete_historical_and_current_baseline_inventory_is_hash_bound():
    audit = _read(AUDIT)
    duplicate = audit["duplicate_audit"]
    assert duplicate["file_counts"] == {
        "historical_case_json": 47,
        "old_dev_tasks": 18,
        "old_test_tasks": 14,
        "current_package_manifests": 19,
        "current_source_manifests": 19,
        "total": 117,
    }
    controls = {row["identity"]: row for row in duplicate["key_controls"]}
    assert controls["mp-opitz-dd-01"]["partition"] == "previous TEST CHALLENGE"
    assert controls["mp-opitz-dd-01"]["relation"] == "DIRECT_GENERIC_SUPERFAMILY"
    assert controls["rps-case-q7v3"]["relation"] == "CURRENT_ARITY_FOUR_MATRIX_FUNCTION_CONTROL"
    assert controls["rps-real-c3j9"]["relation"] == "CURRENT_R3_MATRIX_FUNCTION_CONTROL"


def test_no_strict_package_evidence_is_fabricated_after_source_rejection():
    audit = _read(AUDIT)
    assert audit["assumption_audit"]["result"] == "NO_PACKAGE_TO_CONTRACT"
    assert audit["mechanical_evidence"] == {
        "public_case_loader": "NOT_RUN_NO_SURVIVOR",
        "m1_compilation": "NOT_RUN_NO_SURVIVOR",
        "session_receipts": "NOT_CREATED_NO_SURVIVOR",
        "opaque_ids": "NOT_ALLOCATED_NO_SURVIVOR",
        "scientific_result": "NONE",
        "package_result": "NONE",
    }


def test_tampered_source_disposition_is_rejected(monkeypatch, tmp_path):
    tampered = _read(AUDIT)
    tampered["screened_families"][0]["disposition"] = "ADMIT_DEV"
    path = tmp_path / "R3_MISSING.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    monkeypatch.setattr(audit_module, "AUDIT", path)
    with pytest.raises(R3MissingAuditError, match="DISPOSITION:1509.05030v2"):
        audit_module.validate()


def test_tampered_generic_control_hash_is_rejected(monkeypatch, tmp_path):
    tampered = _read(AUDIT)
    tampered["duplicate_audit"]["key_controls"][0]["sha256"] = "0" * 64
    path = tmp_path / "R3_MISSING.json"
    path.write_text(json.dumps(tampered), encoding="utf-8")
    monkeypatch.setattr(audit_module, "AUDIT", path)
    with pytest.raises(R3MissingAuditError, match="KEY_CONTROL_HASH:mp-opitz-dd-01"):
        audit_module.validate()

