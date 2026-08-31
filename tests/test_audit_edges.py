"""Edge-manifest load and source-grounding tests (derivation-audit E3)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from symbolic_compactification.audit.edges import ground_edge, load_edges
from symbolic_compactification.audit.schema import GROUNDING_FAILURE, AuditError
from symbolic_compactification.audit.workspace import (
    initialize_audit_workspace,
    load_audit_workspace,
)

_OPTIONAL_LHS_YAML = """\
schema_version: DerivationAuditV1
edges:
  - id: E001
    from: eq:a
    to: eq:b
    type: ALGEBRAIC_EQUIVALENCE
    assumptions_used: [x]
    claim: "optional"
"""

_UNKNOWN_TYPE_YAML = """\
schema_version: DerivationAuditV1
edges:
  - id: E001
    from: eq:a
    to: eq:b
    type: TELEPORTATION
"""

_MISSING_RESIDUAL_YAML = """\
schema_version: DerivationAuditV1
edges:
  - id: E001
    from: eq:a
    to: eq:b
    type: ALGEBRAIC_EQUIVALENCE
    residual: expressions/res.txt
"""

_BOUND_LHS_YAML = """\
schema_version: DerivationAuditV1
edges:
  - id: E001
    from: eq:a
    to: eq:b
    type: ALGEBRAIC_EQUIVALENCE
    lhs: expressions/left.txt
    rhs: expressions/right.txt
"""


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _write_edges(root: Path, text: str) -> None:
    (root / "edges" / "edges.yaml").write_text(text, encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_snapshot_hash(root: Path, bound_relpaths: tuple[str, ...]) -> str:
    files = {
        "audit.yaml": _file_sha256(root / "audit.yaml"),
        "assumptions/assumptions.yaml": _file_sha256(
            root / "assumptions" / "assumptions.yaml"),
        "edges/edges.yaml": _file_sha256(root / "edges" / "edges.yaml"),
        "equations/equations.yaml": _file_sha256(
            root / "equations" / "equations.yaml"),
    }
    for rel in bound_relpaths:
        files[rel] = _file_sha256(root / rel)
    payload = json.dumps(
        files, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_load_optional_lhs_edge(tmp_path):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    _write_edges(root, _OPTIONAL_LHS_YAML)
    workspace = load_audit_workspace(root)
    before = _snapshot(root)

    edges = load_edges(workspace)
    grounded = ground_edge(edges[0], workspace)

    assert _snapshot(root) == before
    assert len(edges) == 1
    edge = edges[0]
    assert edge.edge_id == "E001"
    assert edge.source_from == "eq:a"
    assert edge.source_to == "eq:b"
    assert edge.edge_type == "ALGEBRAIC_EQUIVALENCE"
    assert edge.lhs is None
    assert edge.rhs is None
    assert edge.residual is None
    assert edge.assumptions_used == ("x",)
    assert edge.claim == "optional"
    assert grounded.ok
    assert grounded.status == ""
    assert grounded.issues == ()
    assert grounded.source_refs == ("eq:a", "eq:b")
    assert grounded.source_snapshot_hash == _expected_snapshot_hash(root, ())


def test_unknown_edge_type_fails(tmp_path):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    _write_edges(root, _UNKNOWN_TYPE_YAML)
    workspace = load_audit_workspace(root)
    before = _snapshot(root)

    with pytest.raises(AuditError) as excinfo:
        load_edges(workspace)

    assert _snapshot(root) == before
    assert excinfo.value.code == "UNKNOWN_EDGE_TYPE"
    assert "TELEPORTATION" in excinfo.value.detail


def test_missing_residual_file_grounds_as_grounding_failure(tmp_path):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    _write_edges(root, _MISSING_RESIDUAL_YAML)
    workspace = load_audit_workspace(root)
    before = _snapshot(root)

    edges = load_edges(workspace)
    grounded = ground_edge(edges[0], workspace)

    assert _snapshot(root) == before
    assert edges[0].residual == "expressions/res.txt"
    assert edges[0].lhs is None
    assert not grounded.ok
    assert grounded.status == GROUNDING_FAILURE
    assert "SOURCE_FILE_MISSING" in grounded.issues
    assert "expressions/res.txt" in grounded.source_refs
    assert grounded.source_snapshot_hash == _expected_snapshot_hash(root, ())


def test_snapshot_hash_changes_when_bound_expression_file_changes(tmp_path):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    _write_edges(root, _BOUND_LHS_YAML)
    left = root / "expressions" / "left.txt"
    right = root / "expressions" / "right.txt"
    left.write_text("x\n", encoding="utf-8")
    right.write_text("y\n", encoding="utf-8")
    workspace = load_audit_workspace(root)
    edge = load_edges(workspace)[0]
    before = _snapshot(root)

    first = ground_edge(edge, workspace)
    assert _snapshot(root) == before
    assert first.ok
    bound = ("expressions/left.txt", "expressions/right.txt")
    assert first.source_snapshot_hash == _expected_snapshot_hash(root, bound)

    left.write_text("x + 1\n", encoding="utf-8")
    after_edit = _snapshot(root)
    second = ground_edge(edge, workspace)
    assert _snapshot(root) == after_edit
    assert second.ok
    assert second.source_snapshot_hash == _expected_snapshot_hash(root, bound)
    assert first.source_snapshot_hash != second.source_snapshot_hash
    assert len(first.source_snapshot_hash) == 64
    assert len(second.source_snapshot_hash) == 64


def test_load_dataclass_field_name_aliases(tmp_path):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    _write_edges(root, """\
schema_version: DerivationAuditV1
edges:
  - edge_id: A.binomial-expand
    source_from: eq.binomial-left
    source_to: eq.binomial-right
    edge_type: ALGEBRAIC_EQUIVALENCE
    lhs: expressions/left.txt
    rhs: expressions/right.txt
""")
    workspace = load_audit_workspace(root)
    edges = load_edges(workspace)
    assert edges[0].edge_id == "A.binomial-expand"
    assert edges[0].source_from == "eq.binomial-left"
    assert edges[0].edge_type == "ALGEBRAIC_EQUIVALENCE"
