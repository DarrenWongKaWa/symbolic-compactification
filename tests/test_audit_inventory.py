"""Targeted tests for derivation-audit equation inventory."""
from __future__ import annotations

import hashlib
from pathlib import Path

import yaml

from symbolic_compactification.audit.inventory import (
    inventory_equations,
    load_equation_manifest,
)
from symbolic_compactification.audit.workspace import (
    initialize_audit_workspace,
    load_audit_workspace,
)

TINY_ARTICLE = """\\documentclass{article}
\\begin{document}
\\begin{equation}
\\label{eq:add}
a + b = c
\\end{equation}
\\end{document}
"""

DUPLICATE_ARTICLE = """\\documentclass{article}
\\begin{document}
\\begin{equation}
\\label{eq:dup}
1 = 1
\\end{equation}
\\begin{equation}
\\label{eq:dup}
2 = 2
\\end{equation}
\\end{document}
"""


def _workspace_with_manuscript(tmp_path: Path, text: str):
    root = tmp_path / "paper-audit"
    initialize_audit_workspace(root)
    manuscript = root / "manuscript" / "source.tex"
    manuscript.write_text(text, encoding="utf-8")
    return load_audit_workspace(root), manuscript


def test_extract_labeled_equation_from_tiny_article(tmp_path):
    workspace, manuscript = _workspace_with_manuscript(tmp_path, TINY_ARTICLE)
    sidecar = workspace.root / "reports" / "inventory.json"
    assert not sidecar.is_file()

    preview = inventory_equations(workspace, write=False)
    assert not sidecar.is_file()
    assert len(preview.equations) == 1
    equation = preview.equations[0]
    assert equation.label == "eq:add"
    assert equation.equation_id == "eq:add"
    assert equation.environment == "equation"
    assert equation.source_file == "manuscript/source.tex"
    assert equation.start_line == 3
    assert equation.end_line == 6
    assert "a + b = c" in equation.body
    assert "\\label{eq:add}" in equation.body
    assert equation.source_hash == hashlib.sha256(
        equation.body.encode("utf-8")).hexdigest()
    assert equation.curated is False
    assert preview.source_hash == hashlib.sha256(TINY_ARTICLE.encode("utf-8")).hexdigest()
    assert preview.duplicate_labels == ()

    written = inventory_equations(workspace, write=True)
    assert sidecar.is_file()
    loaded = load_equation_manifest(workspace)
    assert [item.equation_id for item in loaded.equations] == ["eq:add"]
    assert written.equations[0].body == loaded.equations[0].body
    assert manuscript.read_text(encoding="utf-8") == TINY_ARTICLE


def test_duplicate_labels_reported(tmp_path):
    workspace, _manuscript = _workspace_with_manuscript(tmp_path, DUPLICATE_ARTICLE)
    inventory = inventory_equations(workspace, write=True)
    assert len(inventory.equations) == 2
    assert inventory.duplicate_labels == ("eq:dup",)
    assert inventory.equations[0].label == "eq:dup"
    assert inventory.equations[1].label == "eq:dup"
    assert inventory.equations[0].body != inventory.equations[1].body
    assert any("not scientific evidence" in warning for warning in inventory.warnings)
    assert "eq:dup" in " ".join(inventory.warnings)
    loaded = load_equation_manifest(workspace)
    assert loaded.duplicate_labels == ("eq:dup",)


def test_curated_mapping_preserved_on_rewrite(tmp_path):
    workspace, _manuscript = _workspace_with_manuscript(tmp_path, TINY_ARTICLE)
    first = inventory_equations(workspace, write=True)
    assert first.equations[0].equation_id == "eq:add"
    assert first.equations[0].curated is False

    manifest = workspace.root / "equations" / "equations.yaml"
    document = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    matching = None
    for row in document["equations"]:
        if row.get("label") == "eq:add":
            row["id"] = "E001"
            row["curated"] = True
            row["notes"] = "manual-id"
            matching = row
    assert matching is not None
    manifest.write_text(
        yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    rewritten = inventory_equations(workspace, write=True)
    assert len(rewritten.equations) == 1
    equation = rewritten.equations[0]
    assert equation.equation_id == "E001"
    assert equation.label == "eq:add"
    assert equation.curated is True
    assert "a + b = c" in equation.body

    persisted = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    row = persisted["equations"][0]
    assert row["id"] == "E001"
    assert row["label"] == "eq:add"
    assert row["curated"] is True
    assert row["notes"] == "manual-id"
    loaded = load_equation_manifest(workspace)
    assert loaded.equations[0].equation_id == "E001"
    assert loaded.equations[0].curated is True


def test_manuscript_bytes_unchanged(tmp_path):
    workspace, manuscript = _workspace_with_manuscript(tmp_path, TINY_ARTICLE)
    before = manuscript.read_bytes()
    mode_before = manuscript.stat().st_mode
    inventory_equations(workspace, write=False)
    inventory_equations(workspace, write=True)
    inventory_equations(workspace, write=True)
    assert manuscript.read_bytes() == before
    assert manuscript.stat().st_mode == mode_before
    assert not manuscript.is_symlink()
    tree = {
        path.relative_to(workspace.root / "manuscript").as_posix(): path.read_bytes()
        for path in (workspace.root / "manuscript").rglob("*")
        if path.is_file()
    }
    inventory_equations(workspace, write=True)
    after = {
        path.relative_to(workspace.root / "manuscript").as_posix(): path.read_bytes()
        for path in (workspace.root / "manuscript").rglob("*")
        if path.is_file()
    }
    assert after == tree


def test_markdown_display_math_labels(tmp_path):
    text = (
        "Notes\n"
        "\n"
        "$$\n"
        "\\label{eq:dollar}\n"
        "x = 1\n"
        "$$\n"
        "\n"
        "\\[\n"
        "\\label{eq:bracket}\n"
        "y = 2\n"
        "\\]\n"
    )
    workspace, _manuscript = _workspace_with_manuscript(tmp_path, text)
    inventory = inventory_equations(workspace, write=False)
    by_label = {item.label: item for item in inventory.equations}
    assert set(by_label) == {"eq:dollar", "eq:bracket"}
    assert by_label["eq:dollar"].environment == "$$"
    assert "x = 1" in by_label["eq:dollar"].body
    assert by_label["eq:bracket"].environment == "\\["
    assert "y = 2" in by_label["eq:bracket"].body
