"""Adversarial multi-branch families must not certify as FAMILY_ZERO."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.schema import (  # noqa: E402
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    compose_family_verdict,
)
from research.multibranch_verification.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CONTROL_CASES,
    CONTROL_IDS,
)
from research.multibranch_verification.falsifier.checkers import (  # noqa: E402
    check_all,
    check_controls,
    check_family,
    false_zero_count,
    majority_branch_vote,
    report,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402

FALSIFIER_DIR = ROOT / "research" / "multibranch_verification" / "falsifier"

MISSION_KINDS = (
    "corrupted_branch_coefficient",
    "wrong_factorial",
    "broken_branch",
    "mixed_latent_F",
    "path_inconsistent_recurrence",
    "wrong_derivative_order",
    "wrong_degeneracy_variable",
    "pole_sensitive_false_confluence",
)

MAJORITY_TRAP_IDS = (
    "V2H_01_corrupted_branch_coefficient",
    "V2H_02_wrong_factorial",
    "V2H_03_broken_branch",
    "V2H_04_mixed_latent_F",
    "V2H_05_path_inconsistent_recurrence",
    "V2H_06_wrong_derivative_order",
    "V2H_07_wrong_degeneracy_variable",
    "V2H_08_pole_sensitive_false_confluence",
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
    assert case["kind"] in MISSION_KINDS
    assert case["description"]
    assert case["members"]
    assert case["reconstructions"]
    assert len(case["members"]) >= 4
    assert case["symbols"]


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_is_not_family_zero(case):
    result = check_family(case)
    assert result.should_be_zero is False
    assert result.family_verdict != FAMILY_ZERO, result.to_dict()
    assert result.false_zero is False, result.to_dict()
    composed = compose_family_verdict(**result.compose_kwargs)
    assert composed == result.family_verdict
    assert composed != FAMILY_ZERO
    assert result.certificate is not None
    assert result.certificate.family_verdict != FAMILY_ZERO


def test_false_zero_count_is_zero():
    results = check_all()
    assert len(results) == 8
    n = false_zero_count(results)
    assert n == 0, [r.to_dict() for r in results if r.false_zero]
    assert all(r.family_verdict != FAMILY_ZERO for r in results)


@pytest.mark.parametrize("case", CONTROL_CASES, ids=lambda c: c["id"])
def test_true_hermite_family_is_family_zero(case):
    result = check_family(case)
    assert result.should_be_zero is True
    assert result.family_verdict == FAMILY_ZERO, result.to_dict()
    assert result.false_zero is False
    assert result.connected is True
    assert result.latent_compatible is True
    assert result.multiplicities_consistent is True
    assert all(v == "ZERO" for v in result.required_edge_verdicts), result.to_dict()
    assert all(v == "ZERO" for v in result.recurrence_verdicts), result.to_dict()
    assert all(v == "ZERO" for v in result.path_verdicts), result.to_dict()
    assert compose_family_verdict(**result.compose_kwargs) == FAMILY_ZERO


def test_control_ids_match():
    assert [c["id"] for c in CONTROL_CASES] == list(CONTROL_IDS)
    assert check_controls()[0].case_id == "V2H_TRUE_HERMITE_FAMILY"


@pytest.mark.parametrize("cid", MAJORITY_TRAP_IDS)
def test_majority_branch_vote_is_the_trap(cid):
    case = next(c for c in ATTACK_CASES if c["id"] == cid)
    result = check_family(case)
    assert result.majority_verdict == FAMILY_ZERO, result.to_dict()
    assert result.family_verdict != FAMILY_ZERO, result.to_dict()
    assert majority_branch_vote(result.reconstruction_verdicts) == FAMILY_ZERO


def test_mixed_latent_needs_latent_and_connected_flags():
    case = next(c for c in ATTACK_CASES if c["kind"] == "mixed_latent_F")
    result = check_family(case)
    assert result.latent_compatible is False
    assert result.connected is False
    assert all(v == "ZERO" for v in result.required_edge_verdicts), result.to_dict()
    assert result.family_verdict == FAMILY_UNKNOWN
    naive = compose_family_verdict(
        required_edge_verdicts=result.required_edge_verdicts,
        recurrence_verdicts=result.recurrence_verdicts,
        path_verdicts=result.path_verdicts,
        connected=True,
        multiplicities_consistent=True,
        latent_compatible=True,
    )
    assert naive == FAMILY_ZERO
    assert compose_family_verdict(**result.compose_kwargs) != FAMILY_ZERO


def test_path_inconsistent_is_family_nonzero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "path_inconsistent_recurrence")
    result = check_family(case)
    assert all(v == "ZERO" for v in result.reconstruction_verdicts), result.to_dict()
    assert any(v == "NONZERO" for v in result.recurrence_verdicts + result.path_verdicts)
    assert result.family_verdict == FAMILY_NONZERO


def test_pole_sensitive_limit_is_not_finite():
    case = next(c for c in ATTACK_CASES if c["kind"] == "pole_sensitive_false_confluence")
    result = check_family(case)
    conf = result.extra["confluence"]
    generic_edge = next(r for r in conf if r["source"] == "M_xy")
    assert generic_edge["verdict"] == "NONZERO"
    note = generic_edge["note"]
    assert note in {"no_finite_two_sided_limit", "infinite_limit"}
    extra = generic_edge["extra"]
    assert extra.get("directional_disagree") or extra.get("limit") in {"oo", "-oo", "zoo"}
    assert result.family_verdict == FAMILY_NONZERO


def test_compose_family_verdict_is_the_family_rule():
    src = inspect.getsource(check_family)
    assert "compose_family_verdict" in src
    assert "majority_branch_vote" in inspect.getsource(
        sys.modules["research.multibranch_verification.falsifier.checkers"]
    )


def test_timeout_unknown_never_becomes_family_zero():
    assert compose_family_verdict(
        required_edge_verdicts=["UNKNOWN"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=True,
        multiplicities_consistent=True,
        latent_compatible=True,
    ) == FAMILY_UNKNOWN
    assert FAMILY_UNKNOWN != FAMILY_ZERO
    four_zero_one_unknown = compose_family_verdict(
        required_edge_verdicts=["ZERO", "ZERO", "ZERO", "ZERO", "UNKNOWN"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=True,
        multiplicities_consistent=True,
        latent_compatible=True,
    )
    assert four_zero_one_unknown != FAMILY_ZERO
    assert four_zero_one_unknown == FAMILY_UNKNOWN


def test_report_matches_checks():
    blob = report()
    assert blob["n"] == 8
    assert blob["n_false_zero"] == 0
    assert blob["false_zero_ids"] == []
    assert blob["control_verdicts"][CONTROL_IDS[0]] == FAMILY_ZERO
    for cid in ATTACK_IDS:
        assert blob["family_verdicts"][cid] != FAMILY_ZERO


def test_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = ""
    for path in FALSIFIER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    blob += (ROOT / "tests" / "test_mb_falsifier.py").read_text(encoding="utf-8")
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
