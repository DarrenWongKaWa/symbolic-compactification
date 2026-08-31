"""Reviewer tables are generated from machine records, not authored markdown."""
from __future__ import annotations

import json

import pytest

from symbolic_compactification.audit.evidence import AuditRun
from symbolic_compactification.audit.report import generate_audit_report
from symbolic_compactification.audit.schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    ASYMPTOTIC_CLAIM,
    CERTIFIED_BY_CHILDREN,
    DEFINITION,
    NONZERO,
    NONZERO_REVIEWER_TEXT,
    SPLIT_PARENT,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    UNKNOWN,
    ZERO,
    AuditRecord,
    public_status_label,
)
from symbolic_compactification.audit.tables import generate_tables
from symbolic_compactification.audit.workspace import initialize_audit_workspace

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64

_VERIFIED_HEADER = (
    "| Edge ID | Manuscript equation reference(s) | "
    "Claim / transformation | Executable residual | Derivation type | "
    "Declared assumptions | Verifier | Result | Artifact link |"
)

_REPORT_SECTIONS = (
    "## Scope",
    "## Declared semantics",
    "## Source snapshot",
    "## Verification summary",
    "## Machine-verified identities",
    "## Structural steps",
    "## Nonzero residuals",
    "## Uncertified / asymptotic / integral",
    "## Assumptions",
    "## Reproduction",
    "## Limitations",
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
        engine_version="0.3.0",
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


def _definition() -> AuditRecord:
    return _record(
        edge_id="D001",
        source_refs=("eq:def",),
        edge_type="DEFINITION_INSERTION",
        status=DEFINITION,
        result=DEFINITION,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
        lhs_hash=None,
        rhs_hash=None,
        claim="define K",
        residual_text=None,
    )


def _asymptotic_unknown() -> AuditRecord:
    return _record(
        edge_id="A001",
        source_refs=("eq:asym",),
        edge_type=ASYMPTOTIC_CLAIM,
        status=UNKNOWN,
        result=UNKNOWN,
        executable=True,
        claim="remainder claim",
        residual_text="F - A",
    )


def _nonzero() -> AuditRecord:
    return _record(
        edge_id="N001",
        source_refs=("eq:nz",),
        status=NONZERO,
        result=NONZERO,
        claim="lhs - rhs",
        residual_text="1",
    )


def _hand_built(tmp_path, extra=()):
    workspace = initialize_audit_workspace(tmp_path / "paper-audit")
    records = (
        _record(),
        _definition(),
        _asymptotic_unknown(),
        _nonzero(),
        *extra,
    )
    run = AuditRun(
        run_id="run1",
        audit_id="audit1",
        directory=workspace.root / "runs" / "run1",
        records=records,
    )
    return workspace, run


def _section_body(text: str, heading: str) -> str:
    start = text.index(heading)
    rest = text[start + len(heading):]
    nxt = rest.find("\n## ")
    return rest if nxt < 0 else rest[:nxt]


def _json_rows(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {row["edge_id"]: row for row in payload["rows"]}


def test_verified_markdown_contains_only_the_zero_edge(tmp_path):
    workspace, run = _hand_built(tmp_path)
    artifacts = generate_tables(workspace, run)
    verified = artifacts.verified_md.read_text(encoding="utf-8")
    assert artifacts.verified_md.name == "TABLE_VERIFIED.md"
    assert _VERIFIED_HEADER in verified
    assert "integrity PASS" in verified
    assert "E001" in verified
    assert "D001" not in verified
    assert "A001" not in verified
    assert "N001" not in verified
    rows = _json_rows(artifacts.table_json)
    assert rows["E001"]["table"] == TABLE_VERIFIED
    assert rows["E001"]["integrity"] == "PASS"
    assert rows["E001"]["may_appear_in_verified_table"] is True
    assert rows["D001"]["table"] == TABLE_STRUCTURAL
    assert rows["A001"]["table"] == TABLE_UNCERTIFIED
    assert rows["N001"]["table"] == TABLE_NONZERO


def test_forged_markdown_zero_is_ignored_on_regeneration(tmp_path):
    workspace, run = _hand_built(tmp_path)
    artifacts = generate_tables(workspace, run)
    path = artifacts.verified_md
    path.write_text(
        path.read_text(encoding="utf-8")
        + "\n| FORGED_ZERO | eq:fake | forged identity | 0 | "
        "ALGEBRAIC_EQUIVALENCE | | python_sympy_exact_v1 | ZERO | |\n",
        encoding="utf-8",
    )
    assert "FORGED_ZERO" in path.read_text(encoding="utf-8")
    generate_tables(workspace, run)
    restored = path.read_text(encoding="utf-8")
    assert "FORGED_ZERO" not in restored
    assert "E001" in restored
    assert "D001" not in restored
    assert "A001" not in restored
    assert "N001" not in restored


def test_nonzero_reappears_if_deleted_then_regenerated(tmp_path):
    workspace, run = _hand_built(tmp_path)
    artifacts = generate_tables(workspace, run)
    path = artifacts.nonzero_md
    assert path.exists()
    path.unlink()
    assert not path.exists()
    generate_tables(workspace, run)
    text = path.read_text(encoding="utf-8")
    assert "N001" in text
    assert "POTENTIAL DERIVATION MISMATCHES" in text
    assert NONZERO_REVIEWER_TEXT in text
    assert "the paper is wrong" not in text.lower()
    assert "E001" not in text


def test_asymptotic_unknown_is_not_in_verified_table(tmp_path):
    workspace, run = _hand_built(tmp_path)
    artifacts = generate_tables(workspace, run)
    verified = artifacts.verified_md.read_text(encoding="utf-8")
    uncertified = artifacts.uncertified_md.read_text(encoding="utf-8")
    assert "A001" not in verified
    assert "A001" in uncertified
    rows = _json_rows(artifacts.table_json)
    assert rows["A001"]["table"] == TABLE_UNCERTIFIED
    assert rows["A001"]["may_appear_in_verified_table"] is False
    csv_text = artifacts.table_csv.read_text(encoding="utf-8")
    assert "A001" in csv_text
    assert TABLE_UNCERTIFIED in csv_text


def test_certified_by_children_is_never_displayed_as_zero(tmp_path):
    parent = _record(
        edge_id="E008",
        source_refs=("eq:split",),
        edge_type=SPLIT_PARENT,
        status=CERTIFIED_BY_CHILDREN,
        result=CERTIFIED_BY_CHILDREN,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
        children=("C12", "C13"),
        claim="delegated split",
        residual_text=None,
    )
    workspace, run = _hand_built(tmp_path, extra=(parent,))
    artifacts = generate_tables(workspace, run)
    structural = artifacts.structural_md.read_text(encoding="utf-8")
    verified = artifacts.verified_md.read_text(encoding="utf-8")
    label = public_status_label(CERTIFIED_BY_CHILDREN)
    assert "E008" not in verified
    assert "E008" in structural
    assert label in structural
    assert "ZERO" not in label
    for line in structural.splitlines():
        if "| E008 |" in line or line.startswith("| E008 "):
            assert ZERO not in line
            assert label in line
            break
    else:
        pytest.fail("missing E008 row in TABLE_STRUCTURAL.md")
    rows = _json_rows(artifacts.table_json)
    assert rows["E008"]["table"] == TABLE_STRUCTURAL
    assert rows["E008"]["public_status"] == label
    assert rows["E008"]["may_appear_in_verified_table"] is False


def test_audit_report_uses_records_and_approved_claims(tmp_path):
    workspace, run = _hand_built(tmp_path)
    path = generate_audit_report(workspace, run)
    assert path.name == "REPORT.md"
    text = path.read_text(encoding="utf-8")
    for heading in _REPORT_SECTIONS:
        assert heading in text
    assert APPROVED_MACHINE_CLAIM in text
    assert APPROVED_CAVEAT in text
    assert NONZERO_REVIEWER_TEXT in text
    assert "POTENTIAL DERIVATION MISMATCHES" in text
    assert "the paper is wrong" not in text.lower()
    assert workspace.manuscript_sha256 in text
    assert workspace.assumptions_sha256 in text
    verified_body = _section_body(text, "## Machine-verified identities")
    assert "E001" in verified_body
    assert "D001" not in verified_body
    assert "A001" not in verified_body
    assert "N001" not in verified_body
    uncertified_body = _section_body(
        text, "## Uncertified / asymptotic / integral")
    assert "A001" in uncertified_body
    nonzero_body = _section_body(text, "## Nonzero residuals")
    assert "N001" in nonzero_body
    structural_body = _section_body(text, "## Structural steps")
    assert "D001" in structural_body
