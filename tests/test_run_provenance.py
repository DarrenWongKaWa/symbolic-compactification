"""Release-focused tests for bounded researcher-run provenance."""
from __future__ import annotations

import hashlib
import json

import pytest

from symbolic_compactification.models import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PACKAGE_VERSION,
)
from symbolic_compactification.provenance import (
    PROVENANCE_SCHEMA_VERSION,
    ProvenanceError,
    build_run_record,
    hash_named_files,
    record_research_run,
    sha256_file,
    write_run_record,
)

FIXED_TIME = "2026-08-31T04:05:06Z"
FIXED_RUN = "20260831T040506Z-test0001"
FIXED_GIT = "a" * 40


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _record(**overrides) -> dict:
    values = {
        "input_hashes": {"notes/research_notes.md": _digest("notes\n")},
        "expression_hashes": {
            "expressions/current.txt": _digest("x + 1\n"),
        },
        "hypothesis_hash": _digest('{"claim":"x + 1"}\n'),
        "assumptions_hash": _digest("symbols: [x]\n"),
        "verifier_route": "python_sympy_exact_v1",
        "result": "ZERO",
        "runtime_seconds": 0.125,
        "warnings": (),
        "run_id": FIXED_RUN,
        "timestamp": FIXED_TIME,
        "git_commit": FIXED_GIT,
        "installed_dependencies": {"sympy": "1.14.0"},
    }
    values.update(overrides)
    return build_run_record(**values)


def test_hashes_are_exact_deterministic_bytes_and_labels_are_sorted(tmp_path):
    first = tmp_path / "first.txt"
    second = tmp_path / "second.txt"
    first.write_bytes(b"x + 1\n")
    second.write_bytes(b"\x00\xff\n")
    before = (first.read_bytes(), first.stat().st_mtime_ns)

    assert sha256_file(first) == hashlib.sha256(b"x + 1\n").hexdigest()
    hashes = hash_named_files({"z/second.bin": second, "a/first.txt": first})
    assert list(hashes) == ["a/first.txt", "z/second.bin"]
    assert hashes["a/first.txt"] == hashlib.sha256(b"x + 1\n").hexdigest()
    assert hashes["z/second.bin"] == hashlib.sha256(b"\x00\xff\n").hexdigest()
    assert (first.read_bytes(), first.stat().st_mtime_ns) == before


def test_record_has_every_required_field_and_only_bounded_metadata():
    record = _record()
    assert set(record) == {
        "schema_version",
        "run_id",
        "timestamp",
        "package_version",
        "engine_version",
        "agent_protocol_version",
        "git_commit",
        "python_version",
        "python_implementation",
        "dependency_versions",
        "input_hashes",
        "expression_hashes",
        "hypothesis_hash",
        "assumptions_hash",
        "verifier_route",
        "result",
        "runtime_seconds",
        "warnings",
    }
    assert record["schema_version"] == PROVENANCE_SCHEMA_VERSION
    assert record["package_version"] == PACKAGE_VERSION
    assert record["engine_version"] == ENGINE_VERSION
    assert record["agent_protocol_version"] == AGENT_PROTOCOL_VERSION
    assert record["git_commit"] == FIXED_GIT
    assert record["dependency_versions"] == {"sympy": "1.14.0"}
    assert record["result"] == "ZERO"
    assert record["verifier_route"] == "python_sympy_exact_v1"


def test_fixed_inputs_produce_byte_identical_json_in_distinct_roots(tmp_path):
    record_a = _record(input_hashes={
        "z.txt": _digest("z"),
        "a.txt": _digest("a"),
    })
    record_b = _record(input_hashes={
        "a.txt": _digest("a"),
        "z.txt": _digest("z"),
    })
    assert record_a == record_b

    path_a = write_run_record(tmp_path / "one" / "runs", record_a)
    path_b = write_run_record(tmp_path / "two" / "runs", record_b)
    assert path_a.read_bytes() == path_b.read_bytes()
    assert path_a.read_text(encoding="utf-8").endswith("\n")


def test_write_is_non_overwriting_and_leaves_no_temporary_file(tmp_path):
    runs = tmp_path / "caller-selected-runs"
    record = _record()
    path = write_run_record(runs, record)
    original = path.read_bytes()

    replacement = _record(result="NONZERO", runtime_seconds=1.5)
    with pytest.raises(ProvenanceError, match="PROVENANCE_RUN_ALREADY_EXISTS"):
        write_run_record(runs, replacement)

    assert path.read_bytes() == original
    assert not list(path.parent.glob(".*.tmp"))


def test_convenience_api_hashes_artifacts_and_writes_under_caller_runs_dir(
        tmp_path):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    hypothesis = tmp_path / "hypothesis.json"
    assumptions = tmp_path / "assumptions.yaml"
    current.write_text("x + 1\n", encoding="utf-8")
    candidate.write_text("1 + x\n", encoding="utf-8")
    hypothesis.write_text('{"hypothesis_type":"identity"}\n',
                          encoding="utf-8")
    assumptions.write_text("symbols: [x]\n", encoding="utf-8")
    source_bytes = {
        path: path.read_bytes()
        for path in (current, candidate, hypothesis, assumptions)
    }

    persisted = record_research_run(
        tmp_path / "custom" / "runs",
        input_files={"hypotheses/hypothesis.json": hypothesis},
        expression_files={
            "expressions/current.txt": current,
            "expressions/candidate.txt": candidate,
        },
        hypothesis_file=hypothesis,
        assumptions_file=assumptions,
        verifier_route="python_sympy_exact_v1",
        result="UNKNOWN",
        runtime_seconds=0.01,
        run_id=FIXED_RUN,
        timestamp=FIXED_TIME,
    )

    assert persisted.path == (tmp_path / "custom" / "runs" / FIXED_RUN
                              / "provenance.json")
    disk = json.loads(persisted.path.read_text(encoding="utf-8"))
    assert disk == persisted.record
    assert disk["hypothesis_hash"] == sha256_file(hypothesis)
    assert disk["assumptions_hash"] == sha256_file(assumptions)
    assert disk["result"] == "UNKNOWN"
    for source, original in source_bytes.items():
        assert source.read_bytes() == original


def test_secrets_and_environment_are_excluded_or_redacted(tmp_path, monkeypatch):
    env_secret = "environment-secret-must-never-appear"
    api_secret = "sk-provenancesecret123456789"
    bearer_secret = "header-token-secret-987654321"
    github_secret = "ghp_abcdefghijklmnopqrstuvwxyz"
    monkeypatch.setenv("UNRELATED_PRIVATE_VALUE", env_secret)
    record = _record(
        warnings=[
            f"DEEPSEEK_API_KEY={api_secret}",
            f"Authorization: Bearer {bearer_secret}",
            f"transport rejected {github_secret}",
        ],
        installed_dependencies={"sympy": f"1.14+{api_secret}"},
    )
    path = write_run_record(tmp_path / "runs", record)
    blob = path.read_text(encoding="utf-8")

    assert "[REDACTED]" in blob
    assert api_secret not in blob
    assert bearer_secret not in blob
    assert github_secret not in blob
    assert env_secret not in blob
    assert "UNRELATED_PRIVATE_VALUE" not in blob
    assert "api_key" not in {key.lower() for key in json.loads(blob)}


def test_arbitrary_or_unsafe_fields_cannot_be_persisted(tmp_path):
    record = _record()
    record["api_key"] = "sk-do-not-write-this-secret"
    with pytest.raises(ProvenanceError, match="PROVENANCE_RECORD_SCHEMA_INVALID"):
        write_run_record(tmp_path / "runs", record)
    assert not (tmp_path / "runs").exists()

    with pytest.raises(ProvenanceError, match="PROVENANCE_VERIFIER_ROUTE_INVALID"):
        _record(verifier_route="https://verify.invalid?api_key=secret")


@pytest.mark.parametrize(
    "result",
    [
        "ZERO",
        "NONZERO",
        "UNKNOWN",
        "PARSE_FAILURE",
        "COMPILE_FAILURE",
        "ASSUMPTION_REQUIRED",
    ],
)
def test_all_public_result_states_are_recordable(result):
    assert _record(result=result)["result"] == result


def test_unknown_result_and_invalid_runtime_fail_closed():
    with pytest.raises(ProvenanceError, match="PROVENANCE_RESULT_INVALID"):
        _record(result="SUCCESS")
    with pytest.raises(ProvenanceError, match="PROVENANCE_RUNTIME_INVALID"):
        _record(runtime_seconds=float("nan"))
