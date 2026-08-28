"""Adversarial Laurent families must not certify as hop ZERO."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_A,
    LEVEL_B,
    LEVEL_C,
    NONZERO,
    UNKNOWN,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.falsifier import run_cases  # noqa: E402
from research.coefficient_laurent.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CONTROL_CASES,
    CONTROL_IDS,
)
from research.coefficient_laurent.falsifier.checkers import (  # noqa: E402
    check_all,
    check_case,
    check_controls,
    false_zero_count,
    forbidden_ignore_remainder,
    forbidden_level_a_is_zero,
    forbidden_t0_is_zero,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402

FALSIFIER_DIR = ROOT / "research" / "coefficient_laurent" / "falsifier"
SCHEMA = ROOT / "research" / "coefficient_laurent" / "schema.py"

MISSION_KINDS = (
    "t0_match_surviving_pole",
    "wrong_polygamma_order",
    "missing_atom",
    "sign_flip",
    "insufficient_order",
)


def test_five_named_attacks_present():
    ids = [c["id"] for c in ATTACK_CASES]
    kinds = [c["kind"] for c in ATTACK_CASES]
    assert ids == list(ATTACK_IDS)
    assert kinds == list(ATTACK_KINDS)
    assert tuple(kinds) == MISSION_KINDS
    assert len(ids) == 5
    assert len(set(ids)) == 5


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_payload_shape(case):
    assert case["should_be_zero"] is False
    assert case["expect"] in {NONZERO, UNKNOWN}
    assert case["expect"] != ZERO
    assert case["kind"] in MISSION_KINDS
    assert case["description"]
    assert case["atoms"]
    assert case["target"]
    assert case["symbols"]
    assert case["degeneration_variable"] == "t"


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_is_not_zero(case):
    result = check_case(case)
    assert result.expect != ZERO
    assert result.got != ZERO, result.extra
    assert result.false_zero is False
    composed, level = compose_hop_verdict(**result.compose_kwargs)
    assert composed == result.got
    assert composed != ZERO
    assert level in {LEVEL_A, LEVEL_B, LEVEL_C}
    assert result.certificate is not None
    assert result.certificate.final_verdict != ZERO
    assert result.certificate.used_full_together is False


def test_run_cases_false_zero_is_zero():
    blob = run_cases()
    assert blob["n"] == len(ATTACK_CASES) + len(CONTROL_CASES)
    assert blob["n_false_zero"] == 0
    assert all(set(row) == {"id", "expect", "got"} for row in blob["rows"])
    for row in blob["rows"]:
        if row["expect"] != ZERO:
            assert row["got"] != ZERO, row
    assert false_zero_count() == 0
    assert all(r.got != ZERO for r in check_all())


def test_t0_match_surviving_pole_is_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "t0_match_surviving_pole")
    result = check_case(case)
    assert result.constant_verdict == ZERO
    assert result.negative_verdict == NONZERO
    assert result.got == NONZERO
    assert result.proof_level == LEVEL_B
    assert result.trap_t0 == ZERO
    assert forbidden_t0_is_zero(result.constant_verdict) == ZERO
    assert compose_hop_verdict(**result.compose_kwargs)[0] == NONZERO


def test_wrong_polygamma_order_is_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "wrong_polygamma_order")
    result = check_case(case)
    assert result.reconstruction_ok is True
    assert result.atoms_expanded is True
    assert result.negative_verdict == ZERO
    assert result.constant_verdict == NONZERO
    assert result.got == NONZERO
    assert result.got != ZERO
    extra = result.extra
    assert extra.get("true_order") == 1
    assert extra.get("claimed_order") == 2


def test_missing_atom_is_not_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "missing_atom")
    result = check_case(case)
    assert result.reconstruction_ok is False
    assert result.atoms_expanded is True
    assert result.constant_verdict == ZERO
    assert result.negative_verdict == NONZERO
    assert result.got == UNKNOWN
    assert result.got != ZERO
    assert result.proof_level == LEVEL_A
    assert result.trap_t0 == ZERO
    lied, _ = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=result.negative_verdict,
        constant_verdict=result.constant_verdict,
        remainder_verdict=result.remainder_verdict,
    )
    assert lied == NONZERO
    assert forbidden_t0_is_zero(result.constant_verdict) == ZERO


def test_sign_flip_is_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "sign_flip")
    result = check_case(case)
    assert result.reconstruction_ok is True
    assert result.constant_verdict == ZERO
    assert result.negative_verdict == NONZERO
    assert result.got == NONZERO
    assert result.trap_t0 == ZERO


def test_insufficient_order_is_unknown_not_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "insufficient_order")
    result = check_case(case)
    assert result.reconstruction_ok is True
    assert result.atoms_expanded is True
    assert result.negative_verdict == ZERO
    assert result.constant_verdict != ZERO
    assert result.remainder_verdict != ZERO
    assert result.got == UNKNOWN
    assert result.got != ZERO
    assert result.proof_level == LEVEL_B
    assert result.trap_ignore_remainder == ZERO
    assert result.trap_level_a == ZERO
    assert (
        forbidden_ignore_remainder(
            negative_verdict=result.negative_verdict,
            constant_verdict=result.constant_verdict,
        )
        == ZERO
    )
    naive, _ = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=UNKNOWN,
    )
    assert naive == UNKNOWN
    assert naive != ZERO


@pytest.mark.parametrize("case", CONTROL_CASES, ids=lambda c: c["id"])
def test_positive_controls_are_zero(case):
    result = check_case(case)
    assert result.expect == ZERO
    assert result.got == ZERO, result.extra
    assert result.false_zero is False
    assert result.proof_level == LEVEL_C
    assert result.reconstruction_ok is True
    assert result.atoms_expanded is True
    assert result.negative_verdict == ZERO
    assert result.constant_verdict == ZERO
    assert result.remainder_verdict == ZERO
    assert compose_hop_verdict(**result.compose_kwargs) == (ZERO, LEVEL_C)


def test_control_ids_match():
    assert [c["id"] for c in CONTROL_CASES] == list(CONTROL_IDS)
    assert check_controls()[0].case_id == "V5L_POS_rational_pole_cancel"


def test_compose_schema_is_the_hop_rule():
    import research.coefficient_laurent.falsifier.checkers as ch
    import research.coefficient_laurent.schema as schema_mod

    src = inspect.getsource(ch.check_case)
    assert "compose_hop_verdict" in src
    assert inspect.getmodule(ch.compose_hop_verdict) is schema_mod
    assert not hasattr(schema_mod.compose_hop_verdict, "__wrapped__")


def test_schema_file_not_rewritten():
    text = SCHEMA.read_text(encoding="utf-8")
    assert "LEVEL A is not hop ZERO" in text
    assert "Majority is forbidden" in text
    assert "def compose_hop_verdict" in text
    assert "Only LEVEL C may be ZERO" in text


def test_t0_match_with_surviving_pole_schema_contract():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=NONZERO,
        constant_verdict=ZERO,
        remainder_verdict=ZERO,
    )
    assert v == NONZERO
    assert v != ZERO
    assert lvl == LEVEL_B


def test_insufficient_remainder_never_becomes_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=UNKNOWN,
    )
    assert v == UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


def test_level_a_atom_series_is_not_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=UNKNOWN,
        constant_verdict=UNKNOWN,
        remainder_verdict=UNKNOWN,
    )
    assert v == UNKNOWN
    assert lvl == LEVEL_A
    assert forbidden_level_a_is_zero(reconstruction_ok=True, atoms_expanded=True) == ZERO


def test_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = ""
    for path in FALSIFIER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    blob += (ROOT / "tests" / "test_cl_falsifier.py").read_text(encoding="utf-8")
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
