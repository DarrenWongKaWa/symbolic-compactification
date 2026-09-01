"""Forward demo regressions: accepted ZERO and refused NONZERO."""
from __future__ import annotations

import shutil
from pathlib import Path

from symbolic_compactification import NONZERO, ZERO, load_workspace, verify_hypothesis

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
EXACT = REPOSITORY_ROOT / "examples/forward/exact-step"
REFUSED = REPOSITORY_ROOT / "examples/forward/refused-step"
REQUIRED_WORKSPACE_PATHS = {
    "project.yaml",
    "expressions",
    "notes",
    "assumptions",
    "references",
    "hypotheses/hypothesis.json",
}


def test_forward_demo_workspaces_load():
    for root in (EXACT, REFUSED):
        for relative in REQUIRED_WORKSPACE_PATHS:
            assert (root / relative).exists(), f"{root.name} missing {relative}"
        workspace = load_workspace(root)
        assert workspace.project.project_name
        assert workspace.hypothesis.proof_obligations


def test_exact_step_is_zero_and_refused_step_is_nonzero(tmp_path):
    exact = tmp_path / "exact"
    refused = tmp_path / "refused"
    shutil.copytree(EXACT, exact)
    shutil.copytree(REFUSED, refused)
    assert verify_hypothesis(exact).result == ZERO
    assert verify_hypothesis(refused).result == NONZERO
