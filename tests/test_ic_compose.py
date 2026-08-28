"""Path composition: PATH_ZERO is not FAMILY_ZERO."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.compose import (  # noqa: E402
    PATH_NONZERO,
    PATH_UNKNOWN,
    PATH_ZERO,
    PathCertificate,
    PathStep,
    compose_path,
    compose_paths,
)
from research.iterated_confluence.compose import path as path_mod  # noqa: E402
from research.iterated_confluence.schema import (  # noqa: E402
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    compose_family_verdict,
    compose_path_verdict,
)

COMPOSE_DIR = ROOT / "research" / "iterated_confluence" / "compose"


def test_public_api_importable():
    assert compose_path is not None
    assert compose_paths is not None
    assert PathCertificate is not None
    assert PathStep is not None


def test_all_zero_is_path_zero():
    cert = compose_path(["ZERO", "ZERO"], path_id="p", start="A", end="C")
    assert cert.path_verdict == PATH_ZERO
    assert cert.path_id == "p"
    assert cert.start_member == "A"
    assert cert.end_member == "C"


def test_any_nonzero_is_path_nonzero():
    cert = compose_path(["ZERO", "NONZERO"], path_id="p")
    assert cert.path_verdict == PATH_NONZERO


def test_unknown_blocks_path_zero():
    cert = compose_path(["ZERO", "UNKNOWN"], path_id="p")
    assert cert.path_verdict == PATH_UNKNOWN
    assert cert.path_verdict != PATH_ZERO


def test_empty_path_is_unknown_not_zero():
    cert = compose_path([], path_id="empty")
    assert cert.path_verdict == PATH_UNKNOWN
    assert cert.path_verdict != PATH_ZERO
    assert compose_path(None).path_verdict == PATH_UNKNOWN


def test_path_zero_is_not_family_zero():
    cert = compose_path(["ZERO", "ZERO"], path_id="only", start="A", end="B")
    assert cert.path_verdict == PATH_ZERO
    assert PATH_ZERO != FAMILY_ZERO
    family = compose_family_verdict(
        path_verdicts=[cert.path_verdict],
        consistency_verdicts=[],
        reconstruction_verdicts=["ZERO"],
        require_path_independence=True,
    )
    assert family == FAMILY_UNKNOWN
    assert family != FAMILY_ZERO


def test_path_steps_compose_like_verdict_strings():
    steps = [
        PathStep(source="A", target="B", verdict="ZERO"),
        PathStep(source="B", target="C", verdict="ZERO"),
    ]
    cert = compose_path(steps, path_id="chain")
    assert cert.path_verdict == PATH_ZERO
    assert cert.start_member == "A"
    assert cert.end_member == "C"
    assert cert.steps[0] is steps[0]
    assert cert.steps[1] is steps[1]


def test_compose_paths_fills_path_verdict():
    p = PathCertificate(
        path_id="p",
        start_member="A",
        end_member="C",
        steps=[
            PathStep(source="A", target="B", verdict="ZERO"),
            PathStep(source="B", target="C", verdict="ZERO"),
        ],
        path_verdict=PATH_UNKNOWN,
    )
    out = compose_paths([p])
    assert out[0] is p
    assert p.path_verdict == PATH_ZERO


def test_compose_paths_mixed_verdicts():
    paths = [
        PathCertificate(
            path_id="z",
            start_member="A",
            end_member="B",
            steps=[PathStep(source="A", target="B", verdict="ZERO")],
        ),
        PathCertificate(
            path_id="n",
            start_member="A",
            end_member="C",
            steps=[
                PathStep(source="A", target="B", verdict="ZERO"),
                PathStep(source="B", target="C", verdict="NONZERO"),
            ],
        ),
        PathCertificate(
            path_id="u",
            start_member="A",
            end_member="D",
            steps=[
                PathStep(source="A", target="B", verdict="ZERO"),
                PathStep(source="B", target="D", verdict="UNKNOWN"),
            ],
        ),
        PathCertificate(path_id="empty", start_member="A", end_member="A", steps=[]),
    ]
    filled = compose_paths(paths)
    assert [c.path_verdict for c in filled] == [
        PATH_ZERO,
        PATH_NONZERO,
        PATH_UNKNOWN,
        PATH_UNKNOWN,
    ]


def test_nonzero_wins_over_unknown():
    cert = compose_path(["UNKNOWN", "NONZERO"])
    assert cert.path_verdict == PATH_NONZERO


def test_majority_zero_plus_unknown_is_not_path_zero():
    cert = compose_path(["ZERO", "ZERO", "UNKNOWN"])
    assert cert.path_verdict == PATH_UNKNOWN
    assert cert.path_verdict != PATH_ZERO


def test_compose_path_delegates_to_schema():
    assert path_mod.compose_path_verdict is compose_path_verdict


def test_compose_path_calls_schema(monkeypatch):
    called = {}

    def fake(verdicts):
        called["verdicts"] = list(verdicts)
        return PATH_ZERO

    monkeypatch.setattr(path_mod, "compose_path_verdict", fake)
    cert = compose_path(["ZERO", "ZERO"], path_id="p")
    assert called["verdicts"] == ["ZERO", "ZERO"]
    assert cert.path_verdict == PATH_ZERO


def test_compose_path_does_not_call_family_rule(monkeypatch):
    def boom(**kwargs):
        raise AssertionError("family rule must not run during path composition")

    monkeypatch.setattr(
        "research.iterated_confluence.schema.compose_family_verdict",
        boom,
    )
    cert = compose_path(["ZERO", "ZERO"])
    assert cert.path_verdict == PATH_ZERO
    filled = compose_paths([cert])
    assert filled[0].path_verdict == PATH_ZERO


def test_source_ban_compose_does_not_decide_family_zero():
    py_files = sorted(p for p in COMPOSE_DIR.rglob("*.py") if p.is_file())
    assert py_files
    blob = "\n".join(p.read_text(encoding="utf-8") for p in py_files)
    assert "FAMILY_ZERO" not in blob
    assert "compose_family_verdict" not in blob
    import research.iterated_confluence.compose as compose_pkg

    assert "compose_family_verdict" not in getattr(compose_pkg, "__all__", ())
    assert not hasattr(compose_pkg, "compose_family_verdict")
    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id != "FAMILY_ZERO"
                assert node.id != "compose_family_verdict"
            elif isinstance(node, ast.Attribute):
                assert node.attr != "FAMILY_ZERO"
                assert node.attr != "compose_family_verdict"
            elif isinstance(node, ast.alias):
                assert node.name != "FAMILY_ZERO"
                assert (node.asname or "") != "FAMILY_ZERO"
                assert node.name != "compose_family_verdict"
