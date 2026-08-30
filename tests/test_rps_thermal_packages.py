from __future__ import annotations

import json
import shutil

import pytest

from research.representation_program_search.packages.thermal.validate import (
    PACKAGE_CONFIG,
    PackageValidationError,
    validate_all,
    validate_package,
)


def test_thermal_packages_validate_with_expected_fail_closed_totals():
    assert validate_all() == {
        "package_count": 6,
        "package_statuses": {"PACKAGE_READY": 2, "PROOF_REQUIRED": 4},
        "verdict_totals": {"NONZERO": 0, "UNKNOWN": 4, "ZERO": 8},
    }


def test_ready_gate_and_depth_downgrades_are_explicit():
    assert PACKAGE_CONFIG["thermal-09-digamma-newton-z1"]["audited_depth"].startswith("R0")
    assert PACKAGE_CONFIG["thermal-10-polygamma-order2-recurrence"]["audited_depth"].startswith("R1")
    assert PACKAGE_CONFIG["thermal-11-digamma-duplication"]["audited_depth"].startswith("R1")
    assert {
        name for name, config in PACKAGE_CONFIG.items()
        if config["package_status"] == "PACKAGE_READY"
    } == {"thermal-09-digamma-newton-z1", "thermal-13-alternating-digamma-z1"}


def test_proposer_views_expose_no_evaluator_fields():
    root = __import__(
        "research.representation_program_search.packages.thermal.validate",
        fromlist=["ROOT"],
    ).ROOT
    forbidden = {"audited_depth", "gold", "operator", "package_status", "program", "reference", "role", "source_dossier_id", "target", "verdict"}
    for name in PACKAGE_CONFIG:
        view = json.loads((root / name / "proposer_view.json").read_text())
        keys: set[str] = set()
        stack = [view]
        while stack:
            value = stack.pop()
            if isinstance(value, dict):
                keys.update(key.lower() for key in value)
                stack.extend(value.values())
            elif isinstance(value, list):
                stack.extend(value)
        assert not keys & forbidden


def test_member_hash_tamper_fails_closed(tmp_path):
    root = __import__(
        "research.representation_program_search.packages.thermal.validate",
        fromlist=["ROOT"],
    ).ROOT
    copy = tmp_path / "thermal-09-digamma-newton-z1"
    shutil.copytree(root / copy.name, copy)
    (copy / "members/A001.txt").write_text("0\n", encoding="utf-8")
    with pytest.raises(PackageValidationError, match="artifact manifest mismatch"):
        validate_package(copy)


def test_unknown_packages_are_never_labelled_ready():
    root = __import__(
        "research.representation_program_search.packages.thermal.validate",
        fromlist=["ROOT"],
    ).ROOT
    for name in PACKAGE_CONFIG:
        package = root / name
        manifest = json.loads((package / "package.json").read_text())
        obligations = json.loads((package / "reference/obligations.json").read_text())["obligations"]
        all_required_zero = all(
            not obligation["required"] or obligation["verdict"] == "ZERO"
            for obligation in obligations
        )
        assert (manifest["package_status"] == "PACKAGE_READY") == all_required_zero
