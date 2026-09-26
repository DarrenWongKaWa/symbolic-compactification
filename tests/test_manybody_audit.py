"""Many-body edges through the derivation audit: demo M end to end."""
from __future__ import annotations

import copy
import shutil
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from symbolic_compactification.audit.edges import load_edges
from symbolic_compactification.audit.evidence import load_audit_run, verify_audit
from symbolic_compactification.audit.schema import (
    ASYMPTOTIC_REMAINDER_LIMIT,
    CERTIFIED_BY_RULE,
    MATSUBARA_RESIDUE_THEOREM,
    TABLE_STRUCTURAL,
    AuditError,
    integrity_issues,
    may_appear_in_verified_table,
    table_bucket,
)
from symbolic_compactification.audit.workspace import load_audit_workspace

pytestmark = pytest.mark.derivation_audit_release_critical

DEMO = Path(__file__).resolve().parents[1] / "tests/fixtures/audit_demos/M"


def _copy(tmp_path: Path) -> Path:
    destination = tmp_path / "demo-M"
    shutil.copytree(DEMO, destination)
    return destination


def _run(root: Path, run_id: str = "mb-run"):
    return verify_audit(load_audit_workspace(root), run_id=run_id)


def _expected() -> dict[str, str]:
    doc = yaml.safe_load((DEMO / "demo.yaml").read_text(encoding="utf-8"))
    return {row["edge_id"]: row["expected_status"] for row in doc["expected_edges"]}


def test_demo_m_statuses_match_declared_expectations(tmp_path):
    run = _run(_copy(tmp_path))
    assert {r.edge_id: r.status for r in run.records} == _expected()


def test_rule_certified_records_are_structural_and_carry_certificates(tmp_path):
    root = _copy(tmp_path)
    run = _run(root)
    by_id = {r.edge_id: r for r in run.records}
    bubble, tail = by_id["M.fermion-bubble"], by_id["M.tail"]
    for record in (bubble, tail):
        assert record.status == CERTIFIED_BY_RULE and not record.executable
        assert not integrity_issues(record)
        assert not may_appear_in_verified_table(record)
        assert table_bucket(record) == TABLE_STRUCTURAL
    assert bubble.rule_certificate.rule_id == MATSUBARA_RESIDUE_THEOREM
    assert "exp(" in bubble.rule_certificate.conclusion
    assert tail.rule_certificate.rule_id == ASYMPTOTIC_REMAINDER_LIMIT
    assert len(tail.remainder_certificate_hash) == 64
    reloaded = {r.edge_id: r for r in load_audit_run(load_audit_workspace(root), run.run_id).records}
    assert reloaded["M.tail"].remainder_certificate_hash == tail.remainder_certificate_hash
    assert reloaded["M.fermion-bubble"].status == CERTIFIED_BY_RULE


def test_declared_poles_off_axis_rule_certifies_bosonic_sum(tmp_path):
    root = _copy(tmp_path)
    path = root / "assumptions/assumptions.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    doc["rules"] = ["MATSUBARA_POLES_OFF_AXIS"]
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    statuses = {r.edge_id: r.status for r in _run(root).records}
    assert statuses["M.boson-bubble"] == CERTIFIED_BY_RULE
    assert statuses["M.fermion-bubble-wrong-sign"] == "NONZERO"


def test_integrity_rejects_rule_status_without_certificates(tmp_path):
    by_id = {r.edge_id: r for r in _run(_copy(tmp_path)).records}
    forged_sum = replace(by_id["M.fermion-bubble"], rule_certificate=None)
    assert "RULE_CERTIFICATE_REQUIRED" in integrity_issues(forged_sum)
    forged_tail = replace(by_id["M.tail"], remainder_certificate_hash=None)
    assert "REMAINDER_CERTIFICATE_REQUIRED" in integrity_issues(forged_tail)
    wrong_rule = replace(by_id["M.tail"], rule_certificate=replace(
        by_id["M.tail"].rule_certificate, rule_id=MATSUBARA_RESIDUE_THEOREM))
    assert "RULE_CERTIFICATE_REQUIRED" in integrity_issues(wrong_rule)
    other_type = replace(by_id["M.fermion-bubble"], edge_type="ALGEBRAIC_EQUIVALENCE")
    assert "CERTIFIED_BY_RULE_REQUIRES_BZ_IBP" in integrity_issues(other_type)


@pytest.mark.parametrize("mutate, message", [
    (lambda e: e[3].__setitem__("matsubara", copy.deepcopy(e[0]["matsubara"])),
     "only valid on MATSUBARA_SUM"),
    (lambda e: e[3]["asymptotic"].__setitem__("order", "-3"), "order must be an integer"),
    (lambda e: e[0]["matsubara"].pop("beta"), "beta"),
])
def test_spec_schema_is_strict(tmp_path, mutate, message):
    root = _copy(tmp_path)
    path = root / "edges/edges.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(doc["edges"])
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    with pytest.raises(AuditError) as info:
        load_edges(load_audit_workspace(root))
    assert info.value.code == "EDGE_SCHEMA_INVALID"
    assert message in str(info.value)
