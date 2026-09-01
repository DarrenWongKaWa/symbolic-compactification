"""Static inventory of the synthetic derivation-audit public demos.

These checks do not call verify_audit. Expected statuses are declared
in demo.yaml (and mirrored as comments in edges.yaml); they are not
machine evidence.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from symbolic_compactification.audit.schema import (
    AUDIT_SCHEMA_VERSION,
    AUDIT_STATUSES,
    DEFAULT_VERIFIER_ROUTE,
    EDGE_TYPES,
)
from symbolic_compactification.audit.workspace import load_audit_workspace

REPO = Path(__file__).resolve().parents[1]
DEMO_ROOT = REPO / "tests/fixtures/audit_demos"
PUBLIC_DEMOS = REPO / "docs/paper-audit.md"

DEMO_IDS = ("A", "B", "C")
REQUIRED_RELATIVE_PATHS = (
    "audit.yaml",
    "demo.yaml",
    "manuscript/source.tex",
    "equations/equations.yaml",
    "edges/edges.yaml",
    "assumptions/assumptions.yaml",
)
# Demos must not ship unpublished-validation paths or local denylists.
PRIVATE_SUBSTRINGS = (
    ".private_validation/",
    "private_denylist.txt",
)
COMMENT_STATUS_RE = re.compile(
    r"#\s*expected_status:\s*([A-Z_]+)",
)


def _demo_dir(demo_id: str) -> Path:
    return DEMO_ROOT / demo_id


def _load_yaml(path: Path) -> dict:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict), f"{path} must be a mapping"
    return raw


def _iter_demo_text_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "runs" in path.relative_to(root).parts and path.name != ".gitkeep":
            continue
        if path.suffix.lower() in {".png", ".pdf", ".pyc"}:
            continue
        yield path


def test_public_demo_trees_exist_and_load():
    assert PUBLIC_DEMOS.is_file()
    public_text = PUBLIC_DEMOS.read_text(encoding="utf-8").lower()
    assert "synthetic" in public_text
    assert "unpublished" in public_text
    assert DEMO_ROOT.is_dir()
    assert tuple(
        sorted(path.name for path in DEMO_ROOT.iterdir() if path.is_dir())
    ) == DEMO_IDS

    for demo_id in DEMO_IDS:
        root = _demo_dir(demo_id)
        for relative in REQUIRED_RELATIVE_PATHS:
            assert (root / relative).is_file(), f"{demo_id} missing {relative}"
        expressions = list((root / "expressions").glob("*.txt"))
        assert expressions, f"{demo_id} has no expression files"
        run_files = sorted(
            path.name for path in (root / "runs").iterdir() if path.is_file()
        )
        assert run_files in ([], [".gitkeep"])
        workspace = load_audit_workspace(root)
        assert workspace.config.schema_version == AUDIT_SCHEMA_VERSION
        assert workspace.config.verifier_profile == DEFAULT_VERIFIER_ROUTE
        assert workspace.config.manuscript_source == "manuscript/source.tex"


def test_expected_statuses_are_declared_for_every_edge():
    for demo_id in DEMO_IDS:
        root = _demo_dir(demo_id)
        edges_path = root / "edges" / "edges.yaml"
        edges_text = edges_path.read_text(encoding="utf-8")
        edges_doc = _load_yaml(edges_path)
        demo_doc = _load_yaml(root / "demo.yaml")
        assert demo_doc.get("synthetic") is True
        assert demo_doc.get("demo_id") == demo_id
        declared = edges_doc.get("edges")
        expected_rows = demo_doc.get("expected_edges")
        assert isinstance(declared, list) and declared, f"{demo_id} has no edges"
        assert isinstance(expected_rows, list) and expected_rows
        expected_by_id = {}
        for row in expected_rows:
            assert row["edge_id"] not in expected_by_id
            assert row["edge_type"] in EDGE_TYPES
            assert row["expected_status"] in AUDIT_STATUSES
            expected_by_id[row["edge_id"]] = row
        comment_statuses = COMMENT_STATUS_RE.findall(edges_text)
        assert len(comment_statuses) == len(declared), (
            f"{demo_id} edges.yaml must comment expected_status on each edge"
        )
        for edge, comment_status in zip(declared, comment_statuses):
            edge_id = edge["edge_id"]
            row = expected_by_id[edge_id]
            assert edge["edge_type"] == row["edge_type"]
            assert comment_status == row["expected_status"]
            assert comment_status in AUDIT_STATUSES
        assert set(expected_by_id) == {edge["edge_id"] for edge in declared}


def test_demo_a_declares_multiple_algebraic_zero_edges():
    rows = _load_yaml(_demo_dir("A") / "demo.yaml")["expected_edges"]
    zero_algebra = [
        row for row in rows
        if row["edge_type"] == "ALGEBRAIC_EQUIVALENCE"
        and row["expected_status"] == "ZERO"
    ]
    assert len(zero_algebra) >= 2


def test_demo_b_declares_typed_linear_algebra_steps():
    rows = _load_yaml(_demo_dir("B") / "demo.yaml")["expected_edges"]
    by_type = {row["edge_type"]: row["expected_status"] for row in rows}
    assert by_type["INDEX_RELABELING"] == "ZERO"
    assert by_type["PROJECTOR_IDENTITY"] == "ZERO"
    assert by_type["PAIRWISE_REDUCTION"] == "ZERO"
    assert by_type["DEFINITION_INSERTION"] == "DEFINITION"
    assert by_type["BOOKKEEPING"] == "RECORDED"


def test_demo_c_asymptotic_claim_is_unknown_without_remainder_certificate():
    edges_path = _demo_dir("C") / "edges" / "edges.yaml"
    edges_text = edges_path.read_text(encoding="utf-8")
    assert "ASYMPTOTIC_CLAIM" in edges_text
    declared = _load_yaml(edges_path)["edges"]
    expected = {
        row["edge_id"]: row
        for row in _load_yaml(_demo_dir("C") / "demo.yaml")["expected_edges"]
    }
    asymptotic = [edge for edge in declared if edge["edge_type"] == "ASYMPTOTIC_CLAIM"]
    assert len(asymptotic) == 1
    edge = asymptotic[0]
    assert "remainder_certificate" not in edge
    assert "remainder_certificate_hash" not in edge
    assert expected[edge["edge_id"]]["expected_status"] == "UNKNOWN"
    # Must not encode the remainder claim as an exact identity F - a/g = 0.
    assert edge.get("residual") in (None, "")
    coeff_zero = [
        row for row in expected.values()
        if row["edge_type"] in {"LAURENT_COEFFICIENT", "COEFFICIENT_IDENTITY"}
        and row["expected_status"] == "ZERO"
    ]
    assert len(coeff_zero) >= 2


def test_public_demo_texts_are_synthetic_and_avoid_private_sources():
    scanned = 0
    for demo_id in DEMO_IDS:
        for path in _iter_demo_text_files(_demo_dir(demo_id)):
            text = path.read_text(encoding="utf-8")
            lowered = text.lower()
            scanned += 1
            for token in PRIVATE_SUBSTRINGS:
                assert token not in lowered, f"{path} contains {token!r}"
    assert scanned > 0
