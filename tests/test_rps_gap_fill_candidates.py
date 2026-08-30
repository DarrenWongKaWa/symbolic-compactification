from __future__ import annotations

import hashlib
import json

import pytest

from research.representation_program_search.packages.gap_fill import (
    freshness_audit,
    validate,
)
from research.representation_program_search.packages.gap_fill.build_candidates import (
    build_all,
)


def test_gap_fill_packages_are_strict_m1_exact_zero_candidates() -> None:
    report = validate.validate_all()

    assert report["verdict"] == "VALID"
    assert report["candidate_count"] == 2
    by_id = {row["case_id"]: row for row in report["cases"]}
    assert by_id["gf-cr3bp-2017-eq28"]["compiled_obligations"] == 4
    assert by_id["gf-vdw-2013-eq1"]["compiled_obligations"] == 8
    assert all(not row["schema_deltas"] for row in by_id.values())
    assert all(row["tautological"] is False for row in by_id.values())


def test_r2_candidate_uses_one_shared_latent_and_four_distinct_newton_pairs() -> None:
    row = validate.validate_package(validate.ROOT / "gf-cr3bp-2017-eq28")

    assert row["operator_counts"] == {
        "LINEAR_COMBINATION": 4,
        "NEWTON_DD": 4,
    }
    assert row["candidate_status"] == "CANDIDATE_ONLY_NOT_ADMITTED"


def test_r6_candidate_remains_explicitly_depth_review_gated() -> None:
    row = validate.validate_package(validate.ROOT / "gf-vdw-2013-eq1")

    assert row["candidate_status"] == "CANDIDATE_ONLY_DEPTH_REVIEW_REQUIRED"
    assert set(row["operator_counts"]) == {
        "COMPOSE",
        "DERIVATIVE",
        "LINEAR_COMBINATION",
        "SUBSTITUTE",
        "VALUE",
    }


def test_public_projection_firewall_rejects_target_hint() -> None:
    with pytest.raises(validate.GapFillValidationError, match="forbidden public"):
        validate._walk_public(
            {
                "schema_version": "RPSProposerViewV1",
                "source_catalog": {"members": []},
                "operator_sequence": ["NEWTON_DD"],
            }
        )


def test_freshness_audit_covers_historical_current_and_package_corpora() -> None:
    report = freshness_audit.audit_candidates()

    assert report["verdict"] == "PASS_TO_MANUAL_REVIEW"
    assert report["gold_fields_used"] is False
    assert report["audit_scope"]["historical_documents"] >= 79
    assert report["audit_scope"]["current_mined_cases"] >= 47
    assert report["audit_scope"]["current_packages"] >= 13
    assert all(not row["blocking_findings"] for row in report["cases"])


def test_one_shot_builder_refuses_to_overwrite_committed_evidence() -> None:
    assert all(path.is_dir() for path in validate.package_dirs())
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build_all()


def test_no_candidate_artifact_mentions_test_partition_or_guo() -> None:
    for package in validate.package_dirs():
        for path in package.rglob("*"):
            if not path.is_file() or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").casefold()
            assert "test_manifest" not in text
            assert "reference/program" not in (
                path.read_text(encoding="utf-8", errors="ignore").casefold()
                if path.name == "proposer_view.json"
                else ""
            )
            assert "g0016" not in text
            assert "g0013" not in text


def test_mining_audit_binds_committed_manifests_and_source_dossiers() -> None:
    audit = json.loads((validate.ROOT / "MINING_AUDIT.json").read_text(encoding="utf-8"))
    for row in audit["candidates"]:
        package = validate.ROOT / row["case_id"]
        assert hashlib.sha256((package / "package.json").read_bytes()).hexdigest() == row[
            "package_manifest_sha256"
        ]
        assert hashlib.sha256(
            (package / "sources/source_dossier.json").read_bytes()
        ).hexdigest() == row["source_dossier_sha256"]
