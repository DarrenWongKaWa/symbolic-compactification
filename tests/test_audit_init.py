"""Freeze tests for audit init/inspect source immutability."""
from __future__ import annotations

import json

import pytest

import symbolic_compactification.cli as cli
from symbolic_compactification.audit.schema import AuditError
from symbolic_compactification.audit.workspace import (
    initialize_audit_workspace,
    load_audit_workspace,
)


def _snapshot(root):
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file() and "runs" not in path.relative_to(root).parts
        and "reports" not in path.relative_to(root).parts
    }


def test_audit_init_and_inspect_do_not_rewrite_sources(tmp_path, capsys):
    root = tmp_path / "paper-audit"
    assert cli.main(["audit", "init", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "AUDIT_INITIALIZED"
    before = _snapshot(root)

    loaded = load_audit_workspace(root)
    assert loaded.config.schema_version == "DerivationAuditV1"
    assert cli.main(["audit", "inspect", str(root), "--json"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["audit_name"] == "paper-audit"
    assert inspected["verifier_profile"] == "python_sympy_exact_v1"
    assert "not scientific evidence" in inspected["note"]
    assert _snapshot(root) == before


def test_audit_init_never_overwrites(tmp_path):
    root = tmp_path / "existing"
    initialize_audit_workspace(root)
    with pytest.raises(AuditError) as exc:
        initialize_audit_workspace(root)
    assert exc.value.code == "WORKSPACE_ALREADY_EXISTS"
    assert cli.main(["audit", "init", str(root)]) == 4


def test_v0_1_init_still_works(tmp_path, capsys):
    root = tmp_path / "legacy"
    assert cli.main(["init", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "WORKSPACE_INITIALIZED"
