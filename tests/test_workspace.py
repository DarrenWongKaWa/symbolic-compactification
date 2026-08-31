"""Focused tests for the external researcher workspace contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from symbolic_compactification import (
    WorkspaceError,
    initialize_workspace,
    load_workspace,
)


def _snapshot(root: Path) -> dict[str, tuple[bytes, int, int]]:
    return {
        path.relative_to(root).as_posix(): (
            path.read_bytes(), path.stat().st_mtime_ns, path.stat().st_mode)
        for path in root.rglob("*")
        if path.is_file()
    }


def _expect(code: str, call):
    with pytest.raises(WorkspaceError) as excinfo:
        call()
    assert excinfo.value.code == code
    assert code in str(excinfo.value)
    return excinfo.value


def test_initialize_workspace_creates_minimal_valid_layout(tmp_path):
    root = tmp_path / "research-project"
    workspace = initialize_workspace(root)

    expected = {
        "project.yaml",
        "expressions/current.txt",
        "expressions/candidate.txt",
        "notes/research_notes.md",
        "assumptions/assumptions.yaml",
        "references/README.md",
        "hypotheses/hypothesis.json",
    }
    assert expected == {
        path.relative_to(root).as_posix()
        for path in root.rglob("*") if path.is_file()
    }
    assert (root / "runs").is_dir()
    assert workspace.project.project_name == "research-project"
    assert workspace.current_expression.text == "x**2 + 2*x + 1"
    assert workspace.hypothesis.proof_obligations[0].relation == "equivalent"
    assert workspace.hypothesis.normalized_simple_form is False


def test_initialize_never_overwrites_even_empty_existing_directory(tmp_path):
    root = tmp_path / "existing"
    root.mkdir()
    _expect("WORKSPACE_ALREADY_EXISTS", lambda: initialize_workspace(root))
    assert list(root.iterdir()) == []


def test_load_is_read_only_for_all_source_files(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    before = _snapshot(root)

    loaded = load_workspace(root)

    assert _snapshot(root) == before
    assert loaded.project_source.sha256 == hashlib.sha256(
        (root / "project.yaml").read_bytes()).hexdigest()
    assert loaded.hypothesis_source.sha256 == hashlib.sha256(
        (root / "hypotheses/hypothesis.json").read_bytes()).hexdigest()


@pytest.mark.parametrize(
    ("relative_path", "replacement", "source_attribute", "semantic_check"),
    [
        (
            "project.yaml",
            b"project_name: replaced\nobjective: replaced\n"
            b"expression_entrypoint: expressions/current.txt\n"
            b"assumptions_file: assumptions/assumptions.yaml\n",
            "project_source",
            lambda workspace: workspace.project.objective.startswith("Test an exact"),
        ),
        (
            "assumptions/assumptions.yaml",
            b"symbols:\n  - name: y\n    real: true\n"
            b"    nonzero: false\nfunctions: []\n",
            "assumptions_source",
            lambda workspace: [item["name"] for item in workspace.symbols] == ["x"],
        ),
        (
            "hypotheses/hypothesis.json",
            b'{"hypothesis_type":"unsupported","members":['
            b'"expressions/current.txt","expressions/candidate.txt"],'
            b'"assumptions_used":["x"]}',
            "hypothesis_source",
            lambda workspace: workspace.hypothesis.hypothesis_type == "equivalence",
        ),
    ],
)
def test_critical_metadata_parse_and_hash_share_one_immutable_byte_snapshot(
        tmp_path, monkeypatch, relative_path, replacement, source_attribute,
        semantic_check):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    target = root / relative_path
    original = target.read_bytes()
    expected_digest = hashlib.sha256(original).hexdigest()
    original_read_bytes = Path.read_bytes
    target_resolved = target.resolve()
    target_reads = 0

    def mutate_after_snapshot(path):
        nonlocal target_reads
        raw = original_read_bytes(path)
        if path.resolve() == target_resolved:
            target_reads += 1
            if target_reads == 1:
                path.write_bytes(replacement)
        return raw

    monkeypatch.setattr(Path, "read_bytes", mutate_after_snapshot)

    loaded = load_workspace(root)

    source = getattr(loaded, source_attribute)
    assert target_reads == 1
    assert source.sha256 == expected_digest
    assert source.text == original.decode("utf-8")
    assert semantic_check(loaded)
    assert target.read_bytes() == replacement


def test_simple_equivalence_form_is_normalized_predictably(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    simple = {
        "hypothesis_type": "equivalence",
        "members": ["expressions/current.txt", "expressions/candidate.txt"],
        "assumptions_used": ["x"],
    }
    (root / "hypotheses/hypothesis.json").write_text(
        json.dumps(simple), encoding="utf-8")

    hypothesis = load_workspace(root).hypothesis

    assert hypothesis.normalized_simple_form is True
    assert hypothesis.schema_version == 1
    assert [item.to_dict() for item in hypothesis.proof_obligations] == [{
        "obligation_id": "equivalence-1",
        "relation": "equivalent",
        "left": "expressions/current.txt",
        "right": "expressions/candidate.txt",
    }]


def test_project_rejects_unknown_fields(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    project = root / "project.yaml"
    project.write_text(project.read_text(encoding="utf-8") + "surprise: true\n",
                       encoding="utf-8")
    error = _expect("PROJECT_SCHEMA_INVALID", lambda: load_workspace(root))
    assert "unknown fields: surprise" in error.detail


def test_yaml_aliases_are_rejected(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "assumptions/assumptions.yaml").write_text(
        "symbols: &items\n  - name: x\nfunctions: *items\n", encoding="utf-8")
    error = _expect("ASSUMPTIONS_PARSE_FAILURE", lambda: load_workspace(root))
    assert "anchors and aliases" in error.detail


def test_workspace_rejects_real_false_fail_closed(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "assumptions/assumptions.yaml").write_text(
        "symbols:\n  - name: x\n    real: false\n    nonzero: false\n"
        "functions: []\n",
        encoding="utf-8",
    )

    error = _expect(
        "UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS",
        lambda: load_workspace(root),
    )

    assert "rejects real:false" in error.detail


def test_hypothesis_rejects_duplicate_json_keys(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "hypotheses/hypothesis.json").write_text(
        '{"hypothesis_type":"equivalence","hypothesis_type":"other",'
        '"members":[],"assumptions_used":[]}', encoding="utf-8")
    error = _expect("HYPOTHESIS_PARSE_FAILURE", lambda: load_workspace(root))
    assert "duplicate key" in error.detail


def test_expression_parse_failure_preserves_underlying_code(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    (root / "expressions/candidate.txt").write_text(
        "x + undeclared", encoding="utf-8")
    error = _expect("EXPRESSION_PARSE_FAILURE", lambda: load_workspace(root))
    assert error.detail == "UNDECLARED_OR_DISALLOWED_NAME"
    assert error.path.endswith("expressions/candidate.txt")


def test_traversal_in_project_path_is_rejected(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    project = root / "project.yaml"
    project.write_text(project.read_text(encoding="utf-8").replace(
        "expressions/current.txt", "expressions/../project.yaml"), encoding="utf-8")
    _expect("PATH_OUTSIDE_WORKSPACE", lambda: load_workspace(root))


def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")
    candidate = root / "expressions/candidate.txt"
    candidate.unlink()
    candidate.symlink_to(outside)

    _expect("PATH_OUTSIDE_WORKSPACE", lambda: load_workspace(root))


def test_hypothesis_references_only_declared_members_and_assumptions(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(path.read_text(encoding="utf-8"))
    hypothesis["assumptions_used"] = ["y"]
    path.write_text(json.dumps(hypothesis), encoding="utf-8")
    error = _expect("HYPOTHESIS_SCHEMA_INVALID", lambda: load_workspace(root))
    assert "undeclared: y" in error.detail


def test_hypothesis_cannot_hide_a_declared_assumption(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    path = root / "hypotheses/hypothesis.json"
    hypothesis = json.loads(path.read_text(encoding="utf-8"))
    hypothesis["assumptions_used"] = []
    path.write_text(json.dumps(hypothesis), encoding="utf-8")
    error = _expect("DECLARED_ASSUMPTIONS_OMITTED", lambda: load_workspace(root))
    assert "omitted: x" in error.detail


def test_fixed_project_metadata_symlink_cannot_escape(tmp_path):
    root = tmp_path / "workspace"
    initialize_workspace(root)
    outside = tmp_path / "project.yaml"
    outside.write_text((root / "project.yaml").read_text(encoding="utf-8"),
                       encoding="utf-8")
    (root / "project.yaml").unlink()
    (root / "project.yaml").symlink_to(outside)

    _expect("PATH_OUTSIDE_WORKSPACE", lambda: load_workspace(root))
