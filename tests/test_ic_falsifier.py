"""Adversarial iterated-path families must not certify as FAMILY_ZERO."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.schema import (  # noqa: E402
    CONSISTENT_ZERO,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_UNKNOWN,
    PATH_ZERO,
    compose_family_verdict,
    compose_path_verdict,
)
from research.iterated_confluence.falsifier import run_cases  # noqa: E402
from research.iterated_confluence.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CONTROL_CASES,
    CONTROL_IDS,
)
from research.iterated_confluence.falsifier.checkers import (  # noqa: E402
    check_all,
    check_case,
    check_controls,
    false_family_zero_count,
    forbidden_majority_paths,
    forbidden_pairwise_leap,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402

FALSIFIER_DIR = ROOT / "research" / "iterated_confluence" / "falsifier"
SCHEMA = ROOT / "research" / "iterated_confluence" / "schema.py"

MISSION_KINDS = (
    "one_path_zero_other_nonzero",
    "noncommuting_limits",
    "hidden_pole",
    "corrupted_intermediate",
    "wrong_equality_surface",
    "path_dependent_repeated_node",
    "spectator_mismatch",
    "majority_path_unknown",
)


def test_eight_named_attacks_present():
    ids = [c["id"] for c in ATTACK_CASES]
    kinds = [c["kind"] for c in ATTACK_CASES]
    assert ids == list(ATTACK_IDS)
    assert kinds == list(ATTACK_KINDS)
    assert tuple(kinds) == MISSION_KINDS
    assert len(ids) == 8
    assert len(set(ids)) == 8


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_payload_shape(case):
    assert case["should_be_zero"] is False
    assert case["expect"] in {FAMILY_NONZERO, FAMILY_UNKNOWN}
    assert case["expect"] != FAMILY_ZERO
    assert case["kind"] in MISSION_KINDS
    assert case["description"]
    assert case["members"]
    assert case["paths"]
    assert case["symbols"]


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_is_not_family_zero(case):
    result = check_case(case)
    assert result.expect != FAMILY_ZERO
    assert result.got != FAMILY_ZERO, result.extra
    assert result.false_family_zero is False
    composed = compose_family_verdict(**result.compose_kwargs)
    assert composed == result.got
    assert composed != FAMILY_ZERO
    assert result.certificate is not None
    assert result.certificate.family_verdict != FAMILY_ZERO


def test_run_cases_false_family_zero_is_zero():
    blob = run_cases()
    assert blob["n"] == len(ATTACK_CASES) + len(CONTROL_CASES)
    assert blob["n_false_family_zero"] == 0
    assert all(set(row) == {"id", "expect", "got"} for row in blob["rows"])
    for row in blob["rows"]:
        if row["expect"] != FAMILY_ZERO:
            assert row["got"] != FAMILY_ZERO, row
    assert false_family_zero_count() == 0
    assert all(r.got != FAMILY_ZERO for r in check_all())


def test_order_dependent_case_is_not_family_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "noncommuting_limits")
    result = check_case(case)
    assert INCONSISTENT_NONZERO in result.consistency_verdicts
    assert result.got == FAMILY_NONZERO
    assert result.got != FAMILY_ZERO
    assert PATH_ZERO in result.path_verdicts
    assert forbidden_pairwise_leap(result.path_verdicts) == FAMILY_ZERO
    naive = compose_family_verdict(
        path_verdicts=result.path_verdicts,
        consistency_verdicts=[CONSISTENT_ZERO],
        reconstruction_verdicts=result.reconstruction_verdicts,
        required_edge_verdicts=[v for v in result.required_edge_verdicts if v != "NONZERO"]
        or result.required_edge_verdicts,
        require_path_independence=True,
    )
    # Lying that orders commute is the attack, not a pass.
    if all(v == PATH_ZERO for v in result.path_verdicts) and all(
        v == "ZERO" for v in result.reconstruction_verdicts
    ):
        assert naive == FAMILY_ZERO


def test_majority_unknown_case_is_not_family_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "majority_path_unknown")
    result = check_case(case)
    assert result.path_verdicts.count(PATH_ZERO) >= 2
    assert PATH_UNKNOWN in result.path_verdicts
    assert PATH_NONZERO not in result.path_verdicts
    assert result.got == FAMILY_UNKNOWN
    assert result.got != FAMILY_ZERO
    assert forbidden_majority_paths(result.path_verdicts) == FAMILY_ZERO


def test_one_nonzero_path_is_family_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "one_path_zero_other_nonzero")
    result = check_case(case)
    assert PATH_ZERO in result.path_verdicts
    assert PATH_NONZERO in result.path_verdicts
    assert result.got == FAMILY_NONZERO
    assert compose_path_verdict(["ZERO"]) == PATH_ZERO
    assert compose_path_verdict(["ZERO", "NONZERO"]) == PATH_NONZERO


def test_hidden_pole_is_not_finite_confluence():
    case = next(c for c in ATTACK_CASES if c["kind"] == "hidden_pole")
    result = check_case(case)
    pole = next(p for p in result.extra["paths"] if p["path_id"] == "p_pole")
    assert pole["path_verdict"] == PATH_NONZERO
    step = pole["steps"][0]
    assert step["verdict"] == "NONZERO"
    assert step["note"] in {"no_finite_two_sided_limit", "infinite_limit"}
    assert step.get("directional_disagree") or is_infinite_note(step)
    assert result.got == FAMILY_NONZERO


def is_infinite_note(step: dict) -> bool:
    limit = str(step.get("limit") or "")
    return "oo" in limit or step["note"] == "infinite_limit"


def test_corrupted_intermediate_is_family_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "corrupted_intermediate")
    result = check_case(case)
    assert "NONZERO" in result.reconstruction_verdicts
    assert PATH_NONZERO in result.path_verdicts
    assert result.got == FAMILY_NONZERO


def test_wrong_equality_surface_identity_is_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "wrong_equality_surface")
    result = check_case(case)
    ident = next(p for p in result.extra["paths"] if p["path_id"] == "false_identity")
    truep = next(p for p in result.extra["paths"] if p["path_id"] == "true_confluence")
    assert ident["path_verdict"] == PATH_NONZERO
    assert truep["path_verdict"] == PATH_ZERO
    assert result.extra.get("surface_restricted_verdict") == "ZERO"
    assert result.got == FAMILY_NONZERO


def test_spectator_mismatch_local_kernel_is_not_family_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "spectator_mismatch")
    result = check_case(case)
    assert PATH_ZERO in result.path_verdicts
    assert "NONZERO" in result.reconstruction_verdicts
    assert "ZERO" in result.reconstruction_verdicts
    assert result.got == FAMILY_NONZERO


def test_path_dependent_repeated_node_is_family_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "path_dependent_repeated_node")
    result = check_case(case)
    assert PATH_ZERO in result.path_verdicts
    assert PATH_NONZERO in result.path_verdicts
    assert result.got == FAMILY_NONZERO


@pytest.mark.parametrize("case", CONTROL_CASES, ids=lambda c: c["id"])
def test_positive_commuting_family_is_family_zero(case):
    result = check_case(case)
    assert result.expect == FAMILY_ZERO
    assert result.got == FAMILY_ZERO, result.extra
    assert result.false_family_zero is False
    assert CONSISTENT_ZERO in result.consistency_verdicts
    assert all(v == PATH_ZERO for v in result.path_verdicts)
    assert all(v == "ZERO" for v in result.reconstruction_verdicts)
    assert all(v == "ZERO" for v in result.required_edge_verdicts)
    assert compose_family_verdict(**result.compose_kwargs) == FAMILY_ZERO


def test_control_ids_match():
    assert [c["id"] for c in CONTROL_CASES] == list(CONTROL_IDS)
    assert check_controls()[0].case_id == "V3J_POS_commuting_iterated_linear"


def test_compose_schema_is_the_family_rule():
    import research.iterated_confluence.falsifier.checkers as ch
    import research.iterated_confluence.schema as schema_mod

    src = inspect.getsource(ch.check_case)
    assert "compose_family_verdict" in src
    assert "compose_path_verdict" in src
    assert inspect.getmodule(ch.compose_family_verdict) is schema_mod
    assert inspect.getmodule(ch.compose_path_verdict) is schema_mod
    assert not hasattr(schema_mod.compose_family_verdict, "__wrapped__")


def test_schema_file_not_rewritten():
    text = SCHEMA.read_text(encoding="utf-8")
    assert "PATH_ZERO of one or more paths is never FAMILY_ZERO" in text
    assert "Majority vote is forbidden" in text or "Majority is forbidden" in text
    assert "def compose_family_verdict" in text
    assert "def compose_path_verdict" in text


def test_timeout_unknown_never_becomes_family_zero():
    assert (
        compose_family_verdict(
            path_verdicts=[PATH_ZERO, PATH_ZERO, PATH_UNKNOWN],
            consistency_verdicts=[CONSISTENT_ZERO],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=["ZERO", "ZERO", "UNKNOWN"],
            require_path_independence=True,
        )
        == FAMILY_UNKNOWN
    )
    assert FAMILY_UNKNOWN != FAMILY_ZERO


def test_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = ""
    for path in FALSIFIER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    blob += (ROOT / "tests" / "test_ic_falsifier.py").read_text(encoding="utf-8")
    for pat in patterns:
        assert pat.search(blob) is None, pat.pattern


def test_no_llm_imports_or_calls():
    banned = (
        "openai",
        "anthropic",
        "groq",
        "litellm",
        "requests.get",
        "httpx",
        "research.representation_invention.llm",
        "research.llm_abstraction",
    )
    blob = ""
    for path in FALSIFIER_DIR.glob("*.py"):
        blob += path.read_text(encoding="utf-8")
    low = blob.lower()
    assert "llm" not in low
    for token in banned:
        assert token not in blob
