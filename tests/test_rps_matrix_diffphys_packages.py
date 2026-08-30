"""Contract tests for fresh fixed matrix/differentiable-physics packages."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from research.representation_program_search.packages.matrix_diffphys.validate import (
    FORBIDDEN_PROPOSER_KEYS,
    FORBIDDEN_PROPOSER_VALUES,
    LOWERING_SCOPE,
    PackageValidationError,
    ROOT,
    _all_keys,
    canonical_json_bytes,
    canonical_program_hash,
    sha256_bytes,
    validate_all,
    validate_package,
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.write_bytes(canonical_json_bytes(value))


def _rehash_artifact(package_dir: Path, relative_path: str) -> None:
    manifest_path = package_dir / "package.json"
    manifest = _load(manifest_path)
    for artifact in manifest["artifacts"]:
        if artifact["path"] == relative_path:
            artifact["sha256"] = sha256_bytes((package_dir / relative_path).read_bytes())
            break
    else:
        raise AssertionError(relative_path)
    _write(manifest_path, manifest)


def test_balanced_fixed_package_set_fails_closed_on_proof_gap() -> None:
    rows = validate_all()
    assert len(rows) == 4
    assert {row["audited_depth"] for row in rows} == {"R2", "R3", "R4", "R6"}
    status_by_depth = {row["audited_depth"]: row["package_status"] for row in rows}
    assert status_by_depth == {
        "R2": "PACKAGE_READY",
        "R3": "PACKAGE_READY",
        "R4": "PROOF_REQUIRED",
        "R6": "PACKAGE_READY",
    }
    assert sum(row["verdict_counts"]["ZERO"] for row in rows) == 10
    assert all(row["verdict_counts"]["NONZERO"] == 0 for row in rows)
    assert sum(row["verdict_counts"]["UNKNOWN"] for row in rows) == 1


def test_proposer_projection_is_exact_and_reference_free() -> None:
    for package_dir in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        proposer = _load(package_dir / "proposer_view.json")
        assert proposer["source_catalog"] == _load(package_dir / "source_catalog.json")
        assert proposer["assumptions"] == _load(package_dir / "assumptions.json")
        assert not (_all_keys(proposer) & FORBIDDEN_PROPOSER_KEYS)
        assert FORBIDDEN_PROPOSER_VALUES.search(json.dumps(proposer, sort_keys=True)) is None
        assert proposer["case_id"].startswith("MDF")


def test_lowerings_deny_symbolic_matrix_dimension_claims() -> None:
    for package_dir in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        package = _load(package_dir / "package.json")
        source = _load(package_dir / "source_manifest.json")
        assert package["lowering_scope"] == LOWERING_SCOPE
        assert source["lowering_provenance"]["symbolic_matrix_dimension_proof"] is False
        assert source["source_dossier"]["case_id"] == package["source_dossier_id"]


def test_required_obligations_are_zero_and_diagnostic_unknown_is_retained() -> None:
    diagnostic_count = 0
    for package_dir in sorted(path for path in ROOT.iterdir() if path.is_dir()):
        obligations = _load(package_dir / "reference" / "obligations.json")
        for obligation in obligations["obligations"]:
            assert obligation["required"] is True
            step = _load(package_dir / obligation["session_path"] / "steps" / "step_001.json")
            assert step["verdict"] == obligation["verdict"]
            if obligation["verdict"] == "ZERO":
                assert step["status"] == "CERTIFIED"
                assert step["proof_status"] == "PROVEN"
            else:
                assert obligation["verdict"] == "UNKNOWN"
                assert step["status"] == "UNVERIFIED"
                assert step["proof_status"] == "PROOF_REQUIRED"
        for attempt in obligations.get("non_success_evidence", []):
            diagnostic_count += 1
            assert attempt["required"] is False
            assert attempt["verdict"] in {"NONZERO", "UNKNOWN"}
            step = _load(package_dir / attempt["session_path"] / "steps" / "step_001.json")
            assert step["verdict"] == attempt["verdict"]
        for attempt in obligations.get("diagnostic_evidence", []):
            diagnostic_count += 1
            assert attempt["eligibility"] == "INELIGIBLE_RESTRICTED_REPLAY"
            assert attempt["verdict"] == "ZERO"
            step = _load(package_dir / attempt["session_path"] / "steps" / "step_001.json")
            assert step["verdict"] == "ZERO"
    assert diagnostic_count == 1


def test_r3_repeated_sites_are_explicit_node_objects() -> None:
    package_dir = ROOT / "mx-sqrt-hermite-fixed-r3"
    program = _load(package_dir / "reference" / "program.json")
    nodes = {row["node_id"]: row["nodes"] for row in program["node_structures"]}
    assert ["x", "x"] in nodes.values()
    for operator in program["operators"]:
        if operator["operator"] == "HERMITE_DD":
            assert operator["arguments"]["nodes"] in nodes


def test_validator_rejects_non_enum_lowering_scope(tmp_path: Path) -> None:
    source = ROOT / "mx-sqrt-newton-fixed-r2"
    package_dir = tmp_path / source.name
    shutil.copytree(source, package_dir)
    manifest = _load(package_dir / "package.json")
    manifest["lowering_scope"] = {"kind": LOWERING_SCOPE}
    _write(package_dir / "package.json", manifest)
    with pytest.raises(PackageValidationError, match="frozen enum"):
        validate_package(package_dir)


def test_validator_rejects_uncovered_nonidentical_reconstruction(tmp_path: Path) -> None:
    source = ROOT / "mx-abba-exp-fixed-r6"
    package_dir = tmp_path / source.name
    shutil.copytree(source, package_dir)
    program_path = package_dir / "reference" / "program.json"
    program = _load(program_path)
    program["member_assignments"]["G0003"].pop("obligation_id")
    program["program_id"] = canonical_program_hash(program)
    _write(program_path, program)
    _rehash_artifact(package_dir, "reference/program.json")
    with pytest.raises(PackageValidationError, match="lacks required obligation"):
        validate_package(package_dir)
