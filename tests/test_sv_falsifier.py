"""Track-V adversarial claims must not certify as ZERO."""
from __future__ import annotations

import re
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CONTROL_CASES,
    CONTROL_IDS,
)
from research.scalable_verification.falsifier.checkers import (  # noqa: E402
    check_all,
    check_attack,
    check_controls,
    false_zero_count,
    report,
)
from research.scalable_verification.falsifier.engines import (  # noqa: E402
    discover_engines,
)

FALSIFIER_DIR = ROOT / "research" / "scalable_verification" / "falsifier"

MISSION_KINDS = (
    "wrong_limit_target",
    "false_removable_singularity",
    "pole_sensitive",
    "wrong_branch",
    "nonuniform_limit_sketch",
    "coefficient_corruption",
    "hidden_assumption",
    "fake_dd_structure",
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
    assert case["primary_engine"] in {"confluence", "dd_cert", "factor"}
    assert case["math"]["kind"]
    assert case["symbols"]


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_verdict_is_not_zero(case):
    result = check_attack(case)
    assert result.should_be_zero is False
    assert result.verdict != ZERO, result.to_dict()
    assert result.false_zero is False, result.to_dict()
    assert result.local_verdict != ZERO, result.to_dict()
    assert result.local_verdict == NONZERO, result.to_dict()
    assert all(r.get("verdict") != ZERO for r in result.engine_verdicts), result.to_dict()


def test_false_zero_count_is_zero():
    results = check_all()
    assert len(results) == 8
    n = false_zero_count(results)
    assert n == 0, [r.to_dict() for r in results if r.false_zero]
    assert all(r.verdict != ZERO for r in results)
    assert all(r.verdict == NONZERO for r in results)


@pytest.mark.parametrize("case", CONTROL_CASES, ids=lambda c: c["id"])
def test_true_controls_still_zero(case):
    result = check_attack(case)
    assert result.should_be_zero is True
    assert result.local_verdict == ZERO, result.to_dict()
    assert result.verdict == ZERO, result.to_dict()
    assert result.false_zero is False


def test_control_ids_match():
    assert [c["id"] for c in CONTROL_CASES] == list(CONTROL_IDS)
    assert check_controls()[0].case_id == "V7_TRUE_LIMIT_CONTROL"


def test_empty_or_unusable_engines_are_not_zero():
    info = discover_engines()
    for name, rec in info["engines"].items():
        assert rec["importable"] is True, name
        # Empty stubs in this worktree have no verify/certify API.
        if not rec["usable"]:
            assert rec["names"] == []
    results = check_all()
    assert false_zero_count(results) == 0
    for r in results:
        assert r.verdict != ZERO


def test_injected_engine_zero_is_false_zero():
    fake = types.SimpleNamespace(verify_claim=lambda *a, **k: ZERO)
    case = ATTACK_CASES[0]
    result = check_attack(case, extra_engines={"injected": fake})
    assert result.false_zero is True, result.to_dict()
    assert result.verdict == ZERO
    assert any(r.get("verdict") == ZERO for r in result.engine_verdicts)
    # The rest of the suite must not inherit the injection.
    assert false_zero_count(check_all()) == 0


def test_check_limit_signature_is_probed_with_sympy_args():
    seen: list = []

    def check_limit(F, y, x, G):
        seen.append((F, y, x, G))
        return NONZERO

    fake = types.SimpleNamespace(check_limit=check_limit)
    case = next(c for c in ATTACK_CASES if c["kind"] == "wrong_limit_target")
    result = check_attack(case, extra_engines={"injected": fake})
    assert result.false_zero is False
    assert result.verdict == NONZERO
    assert seen, result.to_dict()
    F, y, x, G = seen[0]
    assert str(y) == "y" and str(x) == "x"
    assert "sin" in str(F) and "sin" in str(G)


def test_check_limit_zero_on_wrong_target_is_false_zero():
    fake = types.SimpleNamespace(check_limit=lambda F, y, x, G: ZERO)
    case = next(c for c in ATTACK_CASES if c["kind"] == "wrong_limit_target")
    result = check_attack(case, extra_engines={"injected": fake})
    assert result.false_zero is True, result.to_dict()
    assert result.verdict == ZERO


def test_injected_engine_nonzero_is_not_false_zero():
    fake = types.SimpleNamespace(verify_claim=lambda *a, **k: NONZERO)
    result = check_attack(ATTACK_CASES[0], extra_engines={"injected": fake})
    assert result.false_zero is False
    assert result.verdict == NONZERO


def test_report_matches_checks():
    blob = report()
    assert blob["n"] == 8
    assert blob["n_false_zero"] == 0
    assert blob["false_zero_ids"] == []
    assert blob["control_verdicts"][CONTROL_IDS[0]] == ZERO
    assert blob["control_verdicts"][CONTROL_IDS[1]] == ZERO


def test_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = ""
    for path in FALSIFIER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    blob += (ROOT / "tests" / "test_sv_falsifier.py").read_text(encoding="utf-8")
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


def test_timeout_token_never_becomes_zero():
    # Fail-closed contract from PROTOCOL: timeout / size-guard is UNKNOWN.
    assert UNKNOWN != ZERO
    fake = types.SimpleNamespace(verify_claim=lambda *a, **k: UNKNOWN)
    result = check_attack(ATTACK_CASES[2], extra_engines={"injected": fake})
    assert result.verdict != ZERO
    assert result.false_zero is False
