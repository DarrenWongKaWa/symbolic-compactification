"""Adversarial representation claims must not certify as ZERO."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    FIXTURES_DIR,
    MATH_NONZERO_IDS,
    TAUTOLOGY_RESIDUAL_IDS,
    load_attack_cases,
    load_fixture,
)
from research.representation_invention.falsifier.checkers import (  # noqa: E402
    check_all,
    check_attack,
    false_zero_count,
    true_newton_dd_control,
)
from research.representation_invention.falsifier.obligations_probe import (  # noqa: E402
    discover_obligations_api,
    probe_all,
    probe_case,
)
from research.representation_invention.labels import (  # noqa: E402
    AUDIT_CLASSES,
    COMPILE_FAILURE,
    FORBIDDEN_GOLD_PATTERNS,
    VERDICT_NONZERO,
    VERDICT_UNKNOWN,
    VERDICT_ZERO,
)
from research.representation_invention.schema import (  # noqa: E402
    PARSE_FAILURE,
    parse_hypothesis_v2,
)

NON_SUCCESS = {VERDICT_ZERO}


def test_ten_named_attacks_present():
    ids = [c["id"] for c in ATTACK_CASES]
    assert ids == list(ATTACK_IDS)
    assert len(ids) == 10
    assert len(set(ids)) == 10


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_case_payload_shape(case):
    assert case["should_be_zero"] is False
    assert case["expected_audit_class"] in AUDIT_CLASSES
    assert case["expected_audit_class"] != "TRUE_STRUCTURAL_DISCOVERY"
    assert "hypothesis" in case
    assert "description" in case and case["description"]
    assert case["attack_kind"]
    hyp = case["hypothesis"]
    assert "representation_type" in hyp
    assert "latent_object" in hyp
    assert isinstance(hyp.get("member_ids"), list)


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_verdict_is_not_zero(case):
    result = check_attack(case)
    assert result.should_be_zero is False
    assert result.verdict != VERDICT_ZERO, result.to_dict()
    assert result.false_zero is False, result.to_dict()
    assert result.audit_class == case["expected_audit_class"], result.to_dict()


def test_false_zero_count_is_zero():
    results = check_all()
    assert len(results) == 10
    n = false_zero_count(results)
    assert n == 0, [r.to_dict() for r in results if r.false_zero]
    assert all(r.verdict != VERDICT_ZERO for r in results)


def test_true_newton_identity_still_zero():
    # Residual machinery is not a trivial always-NONZERO gate.
    control = true_newton_dd_control()
    assert control.should_be_zero is True
    assert control.verdict == VERDICT_ZERO, control.to_dict()
    assert control.false_zero is False


def test_math_cases_parse_as_v2():
    math_ids = [c["id"] for c in ATTACK_CASES if c["id"] != "F10_ambiguous_member_maps"]
    for case in ATTACK_CASES:
        if case["id"] not in math_ids:
            continue
        cat = set(case["catalog"])
        h = parse_hypothesis_v2(case["hypothesis"], cat)
        assert h.parse_status != PARSE_FAILURE, (case["id"], h.parse_error)


def test_alias_ids_are_parse_failure():
    case = next(c for c in ATTACK_CASES if c["id"] == "F10_ambiguous_member_maps")
    h = parse_hypothesis_v2(case["hypothesis"], set(case["catalog"]))
    assert h.parse_status == PARSE_FAILURE
    assert "alias" in (h.parse_error or "")
    result = check_attack(case)
    assert result.verdict == PARSE_FAILURE
    assert result.audit_class == "UNGROUNDABLE"
    assert "S1_True" in result.extra["aliases"]
    assert "generic_branch" in result.extra["aliases"]
    assert "G0001" in result.extra["incompatible_roles"]


def test_tautology_not_certified_even_if_residual_zero():
    case = next(c for c in ATTACK_CASES if c["id"] == "F08_tautological_master")
    result = check_attack(case)
    assert result.verdict != VERDICT_ZERO
    assert result.audit_class == "TAUTOLOGICAL_MASTER"
    assert result.residual_verdict in {VERDICT_ZERO, None} or result.note == "F_eq_A_used_once"
    assert result.verdict == COMPILE_FAILURE


def test_overgeneral_identity_latent_rejected():
    case = next(c for c in ATTACK_CASES if c["id"] == "F09_overgeneralized_latent")
    result = check_attack(case)
    assert result.verdict != VERDICT_ZERO
    assert result.audit_class == "SHALLOW_REPACKAGING"
    assert result.extra.get("identity_template") is True


def test_json_fixtures_match_cases():
    from research.representation_invention.falsifier.cases import export_fixtures

    export_fixtures(FIXTURES_DIR)
    index_path = FIXTURES_DIR / "index.json"
    assert index_path.is_file()
    index = json.loads(index_path.read_text(encoding="utf-8"))
    assert [row["id"] for row in index] == list(ATTACK_IDS)
    for case in load_attack_cases():
        loaded = load_fixture(case["id"])
        assert loaded["id"] == case["id"]
        assert loaded["should_be_zero"] is False
        assert loaded["expected_audit_class"] == case["expected_audit_class"]
        assert loaded["hypothesis"] == case["hypothesis"]
        assert loaded["catalog"] == case["catalog"]


def test_fixtures_have_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = json.dumps(ATTACK_CASES)
    for path in FIXTURES_DIR.glob("*.json"):
        blob += path.read_text(encoding="utf-8")
    for pat in patterns:
        assert pat.search(blob) is None, pat.pattern


def test_obligations_math_attacks_not_zero():
    """False identities must not verify ZERO if compile/verify exist."""
    api = discover_obligations_api()
    report = probe_all()
    assert report["n"] == 10
    if not api["available"]:
        assert report["available"] is False
        return
    math_rows = [r for r in report["rows"] if r["case_id"] in MATH_NONZERO_IDS]
    leaks = [r for r in math_rows if r.get("verdict") == VERDICT_ZERO]
    assert leaks == [], leaks
    for case in ATTACK_CASES:
        if case["id"] not in MATH_NONZERO_IDS:
            continue
        probed = probe_case(case)
        assert probed["verdict"] != VERDICT_ZERO, probed
        assert probed["verdict"] in {
            VERDICT_NONZERO,
            VERDICT_UNKNOWN,
            COMPILE_FAILURE,
            PARSE_FAILURE,
        }, probed


def test_tautology_residual_zero_is_not_a_certified_claim():
    """F:=A used once can residual-ZERO; local audit still rejects the claim."""
    for cid in TAUTOLOGY_RESIDUAL_IDS:
        case = next(c for c in ATTACK_CASES if c["id"] == cid)
        local = check_attack(case)
        assert local.verdict != VERDICT_ZERO, local.to_dict()
        assert local.false_zero is False
        assert local.audit_class in {"TAUTOLOGICAL_MASTER", "SHALLOW_REPACKAGING"}


@pytest.mark.parametrize(
    "case_id,audit",
    [
        ("F01_fake_confluence", "WRONG_CONFLUENCE"),
        ("F02_wrong_repeated_node", "WRONG_DD_NODE_STRUCTURE"),
        ("F03_pole_sensitive_recurrence", "NONZERO"),
        ("F04_special_function_order", "WRONG_OPERATOR"),
        ("F05_invalid_limit", "WRONG_CONFLUENCE"),
        ("F06_sign_flipped_dd", "WRONG_OPERATOR"),
        ("F07_broken_symmetry_coefficient", "WRONG_OPERATOR"),
        ("F08_tautological_master", "TAUTOLOGICAL_MASTER"),
        ("F09_overgeneralized_latent", "SHALLOW_REPACKAGING"),
        ("F10_ambiguous_member_maps", "UNGROUNDABLE"),
    ],
)
def test_audit_class_mapping(case_id, audit):
    case = next(c for c in ATTACK_CASES if c["id"] == case_id)
    result = check_attack(case)
    assert result.audit_class == audit
    assert result.verdict not in NON_SUCCESS or result.verdict != VERDICT_ZERO
    assert result.verdict != VERDICT_ZERO
