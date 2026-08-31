"""Reviewer-package export: layout, replay script, and privacy firewall."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path

from symbolic_compactification.audit.evidence import AuditRun
from symbolic_compactification.audit.package import (
    PACKAGE_DIRNAME,
    build_reviewer_package,
)
from symbolic_compactification.audit.schema import (
    FORBIDDEN_PUBLIC_CLAIMS,
    NONZERO,
    TABLE_FILENAMES,
    UNKNOWN,
    ZERO,
    AuditRecord,
)
from symbolic_compactification.audit.tables import TableArtifacts
from symbolic_compactification.audit.workspace import initialize_audit_workspace
from symbolic_compactification.models import ENGINE_VERSION
from symbolic_compactification.security import REDACTED

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64

REQUIRED_FILES = (
    "README.md",
    "TABLE_VERIFIED.md",
    "TABLE_STRUCTURAL.md",
    "TABLE_UNCERTIFIED.md",
    "TABLE_NONZERO.md",
    "MANIFEST.json",
    "assumptions.yaml",
    "reproduce.sh",
)


def _record(**overrides) -> AuditRecord:
    base = dict(
        audit_id="audit1",
        edge_id="E001",
        source_refs=("eq:a", "eq:b"),
        edge_type="ALGEBRAIC_EQUIVALENCE",
        status=ZERO,
        result=ZERO,
        source_snapshot_hash=_HASH_A,
        engine_version=ENGINE_VERSION,
        runtime_seconds=0.01,
        lhs_hash=_HASH_B,
        rhs_hash=_HASH_C,
        residual_hash=_HASH_D,
        assumptions_hash=_HASH_E,
        obligation_hash=_HASH_A,
        verifier_route="python_sympy_exact_v1",
        executable=True,
        claim="a - b",
        residual_text="a - b",
    )
    base.update(overrides)
    return AuditRecord(**base)


def _fake_run(workspace, records=None) -> AuditRun:
    run_id = "run001"
    directory = workspace.root / "runs" / run_id
    directory.mkdir(parents=True, exist_ok=True)
    if records is None:
        records = (
            _record(),
            _record(
                edge_id="E002",
                status=NONZERO,
                result=NONZERO,
                residual_text="x - 2*x",
                claim="x - 2*x",
            ),
            _record(
                edge_id="E003",
                status=UNKNOWN,
                result=UNKNOWN,
                residual_text="f(x) - g(x)",
                claim="unresolved",
            ),
        )
    return AuditRun(
        run_id=run_id,
        audit_id="audit1",
        directory=directory,
        records=tuple(records),
    )


def _seed_tables(workspace, *, verified="verified-row\n"):
    reports = workspace.root / workspace.config.output_dir
    reports.mkdir(parents=True, exist_ok=True)
    contents = {
        "TABLE_VERIFIED.md": verified,
        "TABLE_STRUCTURAL.md": "structural-row\n",
        "TABLE_UNCERTIFIED.md": "uncertified-row\n",
        "TABLE_NONZERO.md": "nonzero-row\n",
    }
    for name, text in contents.items():
        (reports / name).write_text(text, encoding="utf-8")
    return contents


def _workspace(tmp_path: Path, name: str = "paper-audit"):
    return initialize_audit_workspace(tmp_path / name)


def test_build_reviewer_package_writes_required_files(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    run = _fake_run(workspace)

    dest = build_reviewer_package(workspace, run)

    assert dest == (workspace.root / PACKAGE_DIRNAME).resolve()
    for name in REQUIRED_FILES:
        assert (dest / name).is_file(), name
        assert not (dest / name).is_symlink()
    assert (dest / "obligations").is_dir()
    assert (dest / "machine_results").is_dir()
    assert (dest / "machine_results" / "machine_records.json").is_file()
    assert (dest / "machine_results" / "provenance.json").is_file()
    assert (dest / "obligations" / "E001.json").is_file()
    assert (dest / "obligations" / "E001.residual.txt").is_file()
    assert (dest / "replay" / "audit.yaml").is_file()
    assert (dest / "replay" / "assumptions" / "assumptions.yaml").is_file()
    assert (dest / "replay" / "equations" / "equations.yaml").is_file()
    assert (dest / "replay" / "edges" / "edges.yaml").is_file()
    verified = (dest / "TABLE_VERIFIED.md").read_text(encoding="utf-8")
    assert "E001" in verified
    assert "ZERO" in verified
    assert "verified-row" not in verified


def test_reproduce_sh_is_executable_and_replays_verify_then_table(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    dest = build_reviewer_package(workspace, _fake_run(workspace))

    script = dest / "reproduce.sh"
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR
    assert os.access(script, os.X_OK)
    text = script.read_text(encoding="utf-8")
    assert text.startswith("#!/bin/sh")
    assert "audit verify" in text
    assert "audit table" in text
    assert "http://" not in text
    assert "https://" not in text
    assert "curl" not in text
    assert "pip install" not in text


def test_private_validation_is_not_copied_even_if_present(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    private = workspace.root / ".private_validation"
    private.mkdir()
    (private / "secret.txt").write_text(
        "UNPUBLISHED_MANUSCRIPT_PAYLOAD", encoding="utf-8")
    (private / "private_denylist.txt").write_text("secret-kernel\n")
    (workspace.root / "expressions" / "ok.txt").write_text("x - x\n")
    outside = tmp_path / "outside-secret.txt"
    outside.write_text("OUTSIDE_SECRET_PAYLOAD\n")
    (workspace.root / "expressions" / "leak.txt").symlink_to(outside)
    (workspace.root / "expressions" / "private-link").symlink_to(private)

    dest = build_reviewer_package(workspace, _fake_run(workspace))

    packaged = [
        path for path in dest.rglob("*")
        if path.is_file() or path.is_dir()
    ]
    assert not any(
        ".private_validation" in path.relative_to(dest).parts
        for path in packaged
    )
    assert not (dest / "replay" / "expressions" / "leak.txt").exists()
    assert not (dest / "replay" / "expressions" / "private-link").exists()
    assert (dest / "replay" / "expressions" / "ok.txt").is_file()
    for path in dest.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "UNPUBLISHED_MANUSCRIPT_PAYLOAD" not in text
        assert "OUTSIDE_SECRET_PAYLOAD" not in text
        assert "secret-kernel" not in text


def test_generate_tables_is_always_called_even_if_reports_exist(
        tmp_path, monkeypatch):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace, verified="LLM_FORGED ZERO\n")
    run = _fake_run(workspace)
    called = {"count": 0}

    def fake_generate(ws, recorded):
        called["count"] += 1
        reports = ws.root / ws.config.output_dir
        reports.mkdir(parents=True, exist_ok=True)
        paths = {}
        for name in TABLE_FILENAMES.values():
            path = reports / name
            path.write_text(f"generated-{name}\n", encoding="utf-8")
            paths[name] = path
        json_path = reports / "verification_table.json"
        json_path.write_text("{}\n", encoding="utf-8")
        csv_path = reports / "verification_table.csv"
        csv_path.write_text("edge_id\n", encoding="utf-8")
        return TableArtifacts(
            verified_md=paths["TABLE_VERIFIED.md"],
            structural_md=paths["TABLE_STRUCTURAL.md"],
            uncertified_md=paths["TABLE_UNCERTIFIED.md"],
            nonzero_md=paths["TABLE_NONZERO.md"],
            table_json=json_path,
            table_csv=csv_path,
        )

    monkeypatch.setattr(
        "symbolic_compactification.audit.package.generate_tables",
        fake_generate,
    )
    dest = build_reviewer_package(workspace, run)
    assert called["count"] == 1
    assert (dest / "TABLE_VERIFIED.md").read_text(encoding="utf-8") == (
        "generated-TABLE_VERIFIED.md\n"
    )
    assert "LLM_FORGED" not in (dest / "TABLE_VERIFIED.md").read_text(
        encoding="utf-8")
    assert (dest / "machine_results" / "verification_table.json").is_file()

    called["count"] = 0
    dest_again = build_reviewer_package(
        workspace, run, dest=tmp_path / "second-export")
    assert called["count"] == 1
    assert (dest_again / "TABLE_VERIFIED.md").read_text(encoding="utf-8") == (
        "generated-TABLE_VERIFIED.md\n"
    )


def test_manifest_records_sha256_run_id_engine_version_and_schema(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    run = _fake_run(workspace)
    dest = build_reviewer_package(workspace, run)
    manifest = json.loads((dest / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["run_id"] == run.run_id
    assert manifest["engine_version"] == ENGINE_VERSION
    assert manifest["schema"] == "DerivationAuditV1"
    files = manifest["files"]
    assert isinstance(files, dict)
    for name in REQUIRED_FILES:
        if name == "MANIFEST.json":
            continue
        assert name in files
        assert len(files[name]) == 64
    readme = (dest / "README.md").read_bytes()
    assert files["README.md"] == hashlib.sha256(readme).hexdigest()


def test_readme_has_no_forbidden_public_claims(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    dest = build_reviewer_package(workspace, _fake_run(workspace))
    text = (dest / "README.md").read_text(encoding="utf-8").lower()
    for phrase in FORBIDDEN_PUBLIC_CLAIMS:
        assert phrase.lower() not in text
    assert "how to reproduce" in text or "reproduce" in text
    assert "audit verify" in text


def test_free_form_strings_are_redacted(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    secret = "sk-proj-synthetic0123456789"
    run = _fake_run(workspace, records=(
        _record(residual_text=f"token={secret}", claim=f"api_key={secret}"),
    ))
    dest = build_reviewer_package(workspace, run)
    residual = (dest / "obligations" / "E001.residual.txt").read_text(
        encoding="utf-8")
    payload = json.loads(
        (dest / "obligations" / "E001.json").read_text(encoding="utf-8"))
    records = json.loads(
        (dest / "machine_results" / "machine_records.json").read_text(
            encoding="utf-8"))
    assert secret not in residual
    assert REDACTED in residual
    assert secret not in json.dumps(payload)
    assert secret not in json.dumps(records)


def test_custom_dest_and_source_immutability(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    before = {
        path.relative_to(workspace.root).as_posix(): path.read_bytes()
        for path in workspace.root.rglob("*")
        if path.is_file()
        and "runs" not in path.relative_to(workspace.root).parts
        and "reports" not in path.relative_to(workspace.root).parts
    }
    dest = tmp_path / "export-dir"
    built = build_reviewer_package(
        workspace, _fake_run(workspace), dest=dest)
    assert built == dest.resolve()
    assert (dest / "README.md").is_file()
    after = {
        path.relative_to(workspace.root).as_posix(): path.read_bytes()
        for path in workspace.root.rglob("*")
        if path.is_file()
        and "runs" not in path.relative_to(workspace.root).parts
        and "reports" not in path.relative_to(workspace.root).parts
        and PACKAGE_DIRNAME not in path.relative_to(workspace.root).parts
    }
    assert after == before


def test_existing_run_machine_records_are_copied(tmp_path):
    workspace = _workspace(tmp_path)
    _seed_tables(workspace)
    run = _fake_run(workspace)
    sidecar = {
        "run_id": run.run_id,
        "records": [{"edge_id": "E001", "result": "ZERO"}],
    }
    (run.directory / "machine_records.json").write_text(
        json.dumps(sidecar), encoding="utf-8")
    (run.directory / "provenance.json").write_text(
        json.dumps({"run_id": run.run_id, "git_commit": "abc"}),
        encoding="utf-8")
    dest = build_reviewer_package(workspace, run)
    copied = json.loads(
        (dest / "machine_results" / "machine_records.json").read_text(
            encoding="utf-8"))
    assert copied["run_id"] == run.run_id
    assert copied["records"][0]["edge_id"] == "E001"
