from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.freeform_baseline import (
    F0_AUTHORITY_COMMIT,
    build_f0_prompt,
    validate_f0_authority,
)
from research.representation_program_search.freeform_baseline.prompt import F0ContractError
from research.representation_program_search.search import load_public_case


def _json(path: Path, value: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(tmp_path: Path):
    members = []
    for index, expression in enumerate(("x + 1\n", "x**2 + 1\n"), 1):
        path = tmp_path / "members" / f"M{index}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(expression, encoding="utf-8")
        members.append({
            "member_id": f"OPAQUE_{index}",
            "path": path.relative_to(tmp_path).as_posix(),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    symbols_sha = _json(tmp_path / "symbols.json", {"symbols": ["x"]})
    assumptions_sha = _json(tmp_path / "assumptions.json", {
        "predicates": [{
            "predicate_id": "P1", "statement": "x is real", "status": "DECLARED",
        }],
        "status": "COMPLETE",
    })
    _json(tmp_path / "proposer_view.json", {
        "assumptions": {"path": "assumptions.json", "sha256": assumptions_sha},
        "case_id": "F0_PUBLIC_CASE",
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": members,
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha,
        },
    })
    return load_public_case(tmp_path / "proposer_view.json")


def test_authority_matches_closed_experiment():
    root = Path(__file__).resolve().parents[1]
    assert F0_AUTHORITY_COMMIT == "0cdde49"
    assert validate_f0_authority(root) == ()


def test_prompt_uses_frozen_p0_and_deterministic_grounded_ids(tmp_path):
    prompt = build_f0_prompt(_case(tmp_path))
    payload = prompt.to_dict()
    assert prompt.condition == "P0" and prompt.result_condition == "F0"
    assert prompt.source_id_map == {"OPAQUE_1": "G0001", "OPAQUE_2": "G0002"}
    user = prompt.messages[1]["content"]
    assert "CONDITION: P0_RAW" in user
    assert "G0001" in user and "G0002" in user
    assert "x + 1" in user and "x**2 + 1" in user
    assert "STRUCTURAL OBSERVATION PACKETS" not in user
    assert payload["private_reasoning_requested"] is False


def test_prompt_never_reads_reference_or_verification(tmp_path, monkeypatch):
    case = _case(tmp_path)
    (tmp_path / "reference").mkdir()
    (tmp_path / "reference" / "program.json").write_text("gold", encoding="utf-8")
    original = Path.read_bytes

    def guarded(path, *args, **kwargs):
        if tmp_path in path.parents:
            assert "reference" not in path.parts
            assert "verification" not in path.parts
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_bytes", guarded)
    build_f0_prompt(case)


def test_authority_drift_fails_closed(tmp_path, monkeypatch):
    case = _case(tmp_path / "case")
    monkeypatch.setattr(
        "research.representation_program_search.freeform_baseline.prompt.validate_f0_authority",
        lambda _root: ("F0_AUTHORITY_DRIFT:x",),
    )
    with pytest.raises(F0ContractError, match="F0_AUTHORITY_DRIFT"):
        build_f0_prompt(case)
