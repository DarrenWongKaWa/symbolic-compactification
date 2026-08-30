from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

from research.representation_program_search.search import load_public_case
from research.representation_program_search.sol_search import (
    SOL_AUTHORITY_MANIFEST_SHA256,
    SOL_REPLAY_BACKENDS,
    SOL_REPLAY_BACKEND_PRESET,
    SOL_REPLAY_POLICY_VERSION,
    SOL_REPLAY_TIMEOUT_SECONDS,
    SOLProjection,
    SOLReplayError,
    SOLReplayPolicy,
    build_sol_replay_artifact,
    load_sol_projection,
    structural_container_metadata,
    structural_container_text,
)


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(tmp_path: Path):
    expressions = {
        "A001": "polygamma(0, x)\n",
        "A002": "polygamma(1, x)\n",
        "A003": "x + 1\n",
    }
    members = []
    for member_id, expression in expressions.items():
        relative = f"members/{member_id}.txt"
        members.append({
            "member_id": member_id,
            "path": relative,
            "sha256": _text(tmp_path / relative, expression),
        })
    symbols_sha256 = _json(
        tmp_path / "symbols.json",
        {"symbols": ["x"]},
    )
    _json(tmp_path / "reference" / "program.json", {"never": "read"})
    _json(tmp_path / "verification" / "receipt.json", {"never": "read"})
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {
            "predicates": [{"predicate_id": "P_REAL", "status": "DECLARED"}],
        },
        "case_id": "SYNTHETIC_SOL_REPLAY",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha256,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def test_structural_container_embeds_exact_member_bytes_without_normalizing(tmp_path):
    case = _case(tmp_path / "case")
    text = structural_container_text(case)
    metadata = structural_container_metadata(case)
    for member in case.members:
        assert member.expression in text
        assert hashlib.sha256(member.expression.encode("utf-8")).hexdigest() == member.sha256
    assert metadata["member_bytes_embedded"] is True
    assert metadata["member_order"] == ["A001", "A002", "A003"]
    assert metadata["expression_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()
    assert all(
        wrapper.startswith("RPS_SOL_MEMBER_")
        for wrapper in metadata["wrapper_functions"].values()
    )


def test_actual_synthetic_replay_is_atomic_deterministic_and_self_validating(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path / "case")
    original_read_text = Path.read_text
    original_read_bytes = Path.read_bytes

    def guarded_text(path, *args, **kwargs):
        if case.package_root in path.parents:
            assert not ({"reference", "verification"} & set(path.parts))
        return original_read_text(path, *args, **kwargs)

    def guarded_bytes(path, *args, **kwargs):
        if case.package_root in path.parents:
            assert not ({"reference", "verification"} & set(path.parts))
        return original_read_bytes(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", guarded_text)
    monkeypatch.setattr(Path, "read_bytes", guarded_bytes)
    monkeypatch.setattr(
        "symbolic_compactification.verify_equivalent",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("verifier called")),
    )
    replay_module = importlib.import_module(
        "research.representation_program_search.sol_search.replay"
    )
    original_fsync_directory = replay_module._fsync_directory
    fsynced: list[Path] = []

    def tracked_fsync(path):
        fsynced.append(path)
        original_fsync_directory(path)

    monkeypatch.setattr(replay_module, "_fsync_directory", tracked_fsync)
    first_path = tmp_path / "artifacts" / "first.json"
    second_path = tmp_path / "artifacts" / "second.json"
    first = build_sol_replay_artifact(case, first_path)
    second = build_sol_replay_artifact(case, second_path)
    assert first_path.is_file() and second_path.is_file()
    assert first.artifact_sha256 == second.artifact_sha256
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first.projection.status == "AVAILABLE"
    assert first.projection.relations
    assert first.projection.source_artifact_sha256 == first.artifact_sha256
    assert first.replay_policy.to_dict() == {
        "backend_preset": SOL_REPLAY_BACKEND_PRESET,
        "requested_backends": list(SOL_REPLAY_BACKENDS),
        "timeout_seconds": SOL_REPLAY_TIMEOUT_SECONDS,
        "version": SOL_REPLAY_POLICY_VERSION,
    }
    raw = json.loads(first_path.read_text(encoding="utf-8"))
    attestation = raw["replay_attestation"]
    assert attestation["authority_manifest_sha256"] == SOL_AUTHORITY_MANIFEST_SHA256
    assert attestation["backend_provenance"]["backends_run"]
    assert set(attestation["backend_provenance"]["backend_versions"]) == set(
        SOL_REPLAY_BACKENDS
    )
    assert attestation["environment_versions"]["python_version"]
    replayed = load_sol_projection(
        case, first_path, expected_sha256=first.artifact_sha256
    )
    assert replayed == first.projection
    assert first.to_dict()["audit_semantics"] == "HASH_AND_REPLAY_NOT_PROOF_OF_EXECUTION"
    assert fsynced == [first_path.parent, first_path.parent, second_path.parent, second_path.parent]


def test_authority_drift_refuses_before_sol_execution_or_output(tmp_path, monkeypatch):
    case = _case(tmp_path / "case")
    output = tmp_path / "artifact.json"
    monkeypatch.setattr(
        "research.representation_program_search.sol_search.replay.validate_local_authority",
        lambda _root: (
            "SOL_AUTHORITY_SOURCE_DRIFT:src/symbolic_compactification/observations/api.py",
        ),
    )
    monkeypatch.setattr(
        "symbolic_compactification.observations.api.observe",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("SOL called")),
    )
    with pytest.raises(SOLReplayError, match="SOL_AUTHORITY_SOURCE_DRIFT"):
        build_sol_replay_artifact(case, output)
    assert not output.exists()


def test_public_boundary_member_hash_parser_and_output_firewalls(tmp_path):
    case = _case(tmp_path / "case")
    contaminated = replace(
        case,
        accessed_paths=case.accessed_paths + ("reference/program.json",),
    )
    with pytest.raises(SOLReplayError, match="PUBLIC_BOUNDARY_VIOLATION"):
        build_sol_replay_artifact(contaminated, tmp_path / "contaminated.json")

    bad_member = replace(case.members[0], expression="polygamma(0, x) + 1\n")
    drifted = replace(case, members=(bad_member, *case.members[1:]))
    with pytest.raises(SOLReplayError, match="MEMBER_HASH_MISMATCH"):
        build_sol_replay_artifact(drifted, tmp_path / "drifted.json")

    invalid_path = case.package_root / "reference" / "sol.json"
    with pytest.raises(SOLReplayError, match="OUTPUT_PATH_FORBIDDEN"):
        build_sol_replay_artifact(case, invalid_path)
    assert not invalid_path.exists()

    invalid_case_root = tmp_path / "invalid"
    invalid = _case(invalid_case_root)
    bad_expression = "x @ x\n"
    bad_path = invalid.package_root / "members" / "A001.txt"
    bad_hash = _text(bad_path, bad_expression)
    bad = replace(
        invalid,
        members=(
            replace(invalid.members[0], expression=bad_expression, sha256=bad_hash),
            *invalid.members[1:],
        ),
    )
    with pytest.raises(SOLReplayError, match="MEMBER_PARSE_FAILURE"):
        build_sol_replay_artifact(bad, tmp_path / "invalid.json")


def test_output_is_not_published_when_immediate_projection_fails(tmp_path, monkeypatch):
    case = _case(tmp_path / "case")
    output = tmp_path / "artifact.json"
    unavailable = SOLProjection(
        status="UNAVAILABLE",
        reason_codes=("SYNTHETIC_SELF_VALIDATION_FAILURE",),
        source_artifact_sha256=None,
        expected_artifact_sha256=None,
        public_case_sha256=case.proposer_view_sha256,
    )
    monkeypatch.setattr(
        "research.representation_program_search.sol_search.replay.load_sol_projection",
        lambda *_args, **_kwargs: unavailable,
    )
    with pytest.raises(SOLReplayError, match="SOL_REPLAY_SELF_VALIDATION_FAILED"):
        build_sol_replay_artifact(case, output)
    assert not output.exists()
    assert not list(tmp_path.glob(".artifact.json.*.tmp"))


def test_replay_policy_is_not_task_tunable_and_existing_output_is_preserved(tmp_path):
    with pytest.raises(SOLReplayError, match="SOL_REPLAY_POLICY_UNKNOWN"):
        SOLReplayPolicy(version="retuned")
    case = _case(tmp_path / "case")
    output = tmp_path / "artifact.json"
    output.write_text("user evidence\n", encoding="utf-8")
    with pytest.raises(SOLReplayError, match="SOL_REPLAY_OUTPUT_EXISTS"):
        build_sol_replay_artifact(case, output)
    assert output.read_text(encoding="utf-8") == "user evidence\n"
