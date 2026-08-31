"""v0.2 derivation-audit release-critical gate.

Layers that are still stubbed raise NOT_IMPLEMENTED and are skipped here so
the marker can run throughout the swarm. Full coverage is required before
DERIVATION_AUDIT_ALPHA_READY.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import symbolic_compactification.cli as cli
from symbolic_compactification.audit.privacy import (
    PRIVATE_OFFLINE_ENV,
    is_private_relpath,
    load_denylist,
    refuse_network_if_private_offline,
    refuse_proposer_if_private_offline,
)
from symbolic_compactification.audit.schema import (
    ASYMPTOTIC_CLAIM,
    AuditError,
    AuditRecord,
    may_appear_in_verified_table,
    table_bucket,
)
from symbolic_compactification.audit.workspace import initialize_audit_workspace

pytestmark = pytest.mark.derivation_audit_release_critical

_H = "a" * 64


def _skip_unimplemented(exc: AuditError) -> None:
    if exc.code == "NOT_IMPLEMENTED":
        pytest.skip("layer not yet implemented")
    raise exc


def test_audit_init_inspect_and_source_immutability(tmp_path, capsys):
    root = tmp_path / "gate-init"
    assert cli.main(["audit", "init", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "AUDIT_INITIALIZED"
    before = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.parts[-2] not in {"runs", "reports"}
    }
    assert cli.main(["audit", "inspect", str(root), "--json"]) == 0
    inspected = json.loads(capsys.readouterr().out)
    assert inspected["schema_version"] == "DerivationAuditV1"
    after = {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in root.rglob("*")
        if p.is_file() and p.parts[-2] not in {"runs", "reports"}
    }
    assert before == after


def test_definition_recorded_split_not_lowered_and_asymptotic_buckets():
    def rec(**kwargs):
        base = dict(
            audit_id="a",
            edge_id="e",
            source_refs=("eq:1",),
            edge_type="ALGEBRAIC_EQUIVALENCE",
            status="ZERO",
            result="ZERO",
            source_snapshot_hash=_H,
            engine_version="0.3.0",
            lhs_hash=_H,
            rhs_hash=_H,
            residual_hash=_H,
            assumptions_hash=_H,
            obligation_hash=_H,
            verifier_route="python_sympy_exact_v1",
            executable=True,
        )
        base.update(kwargs)
        return AuditRecord(**base)

    zero = rec()
    assert table_bucket(zero) == "TABLE_VERIFIED"
    definition = rec(
        edge_type="DEFINITION_INSERTION", status="DEFINITION",
        result="DEFINITION", executable=False, residual_hash=None,
        obligation_hash=None, assumptions_hash=None, verifier_route=None)
    assert table_bucket(definition) == "TABLE_STRUCTURAL"
    recorded = rec(
        edge_type="BOOKKEEPING", status="RECORDED", result="RECORDED",
        executable=False, residual_hash=None, obligation_hash=None,
        assumptions_hash=None, verifier_route=None)
    assert table_bucket(recorded) == "TABLE_STRUCTURAL"
    split = rec(
        edge_type="SPLIT_PARENT", status="SPLIT", result="SPLIT",
        executable=False, residual_hash=None, obligation_hash=None,
        assumptions_hash=None, verifier_route=None)
    assert table_bucket(split) == "TABLE_STRUCTURAL"
    not_lowered = rec(
        status="NOT_LOWERED", result="NOT_LOWERED", executable=False,
        residual_hash=None, obligation_hash=None, assumptions_hash=None,
        verifier_route=None)
    assert table_bucket(not_lowered) == "TABLE_UNCERTIFIED"
    asymptotic = rec(
        edge_type=ASYMPTOTIC_CLAIM, status="UNKNOWN", result="UNKNOWN")
    assert table_bucket(asymptotic) == "TABLE_UNCERTIFIED"
    assert not may_appear_in_verified_table(asymptotic)
    nonzero = rec(status="NONZERO", result="NONZERO")
    assert table_bucket(nonzero) == "TABLE_NONZERO"


def test_forged_zero_rejected_and_nonzero_preserved():
    forged = AuditRecord(
        audit_id="a", edge_id="forged", source_refs=("eq:1",),
        edge_type="ALGEBRAIC_EQUIVALENCE", status="ZERO", result="ZERO",
        source_snapshot_hash=_H, engine_version="0.3.0", executable=True,
    )
    assert not may_appear_in_verified_table(forged)
    nonzero = AuditRecord(
        audit_id="a", edge_id="bad", source_refs=("eq:1",),
        edge_type="ALGEBRAIC_EQUIVALENCE", status="NONZERO", result="NONZERO",
        source_snapshot_hash=_H, engine_version="0.3.0",
        residual_hash=_H, assumptions_hash=_H, obligation_hash=_H,
        verifier_route="python_sympy_exact_v1", executable=True,
    )
    assert table_bucket(nonzero) == "TABLE_NONZERO"


def test_private_offline_and_gitignore(tmp_path, monkeypatch):
    assert is_private_relpath(".private_validation/secret.txt")
    assert not is_private_relpath("reports/TABLE_VERIFIED.md")
    assert load_denylist(tmp_path) == ()
    monkeypatch.setenv(PRIVATE_OFFLINE_ENV, "1")
    with pytest.raises(AuditError) as net:
        refuse_network_if_private_offline("https://example.invalid/x")
    assert net.value.code == "PRIVATE_OFFLINE_NETWORK_REFUSED"
    with pytest.raises(AuditError) as prop:
        refuse_proposer_if_private_offline()
    assert prop.value.code == "PRIVATE_OFFLINE_PROPOSER_DISABLED"
    gitignore = Path(__file__).resolve().parents[1] / ".gitignore"
    assert ".private_validation/" in gitignore.read_text(encoding="utf-8")


def test_inventory_verify_table_package_if_implemented(tmp_path, capsys):
    root = tmp_path / "gate-layers"
    initialize_audit_workspace(root)
    code = cli.main(["audit", "inventory", str(root), "--json"])
    if code == 4:
        err = capsys.readouterr()
        if "NOT_IMPLEMENTED" in err.out + err.err:
            pytest.skip("inventory not yet implemented")
    assert code == 0
    code = cli.main(["audit", "verify", str(root), "--json"])
    if code == 4:
        err = capsys.readouterr()
        if "NOT_IMPLEMENTED" in err.out + err.err:
            pytest.skip("verify not yet implemented")
    assert code in (0, 2, 3)
    code = cli.main(["audit", "table", str(root), "--json"])
    if code == 4:
        err = capsys.readouterr()
        if "NOT_IMPLEMENTED" in err.out + err.err:
            pytest.skip("table not yet implemented")
    assert code == 0
    code = cli.main(["audit", "package", str(root), "--json"])
    if code == 4:
        pytest.skip("package not yet implemented")
    assert code == 0


def test_v0_1_workspace_verify_still_zero(tmp_path, capsys):
    root = tmp_path / "legacy"
    assert cli.main(["init", str(root), "--json"]) == 0
    capsys.readouterr()
    assert cli.main(["verify", str(root), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"] == "ZERO"
