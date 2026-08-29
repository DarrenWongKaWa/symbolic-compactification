"""Adversarial remainder attacks must not validate as CERTIFIED."""
from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.schema import (  # noqa: E402
    LEVEL_B,
    LEVEL_C,
    ZERO,
    compose_hop_verdict,
)
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN  # noqa: E402
from research.remainder_certification.schema import (  # noqa: E402
    ASSUMPTION_REQUIRED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    NONANALYTIC,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)
from research.remainder_certification.falsifier import run_cases  # noqa: E402
from research.remainder_certification.falsifier.cases import (  # noqa: E402
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CONTROL_CASES,
    CONTROL_IDS,
    is_class_c_or_d,
    load_class_c_attacks,
)
from research.remainder_certification.falsifier.checkers import (  # noqa: E402
    check_all,
    check_case,
    check_controls,
    claimed_certificate,
    discover_compile_remainder,
    false_certified_count,
    forbidden_ignore_remainder,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402

FALSIFIER_DIR = ROOT / "research" / "remainder_certification" / "falsifier"
SCHEMA = ROOT / "research" / "remainder_certification" / "schema.py"

MISSION_KINDS = (
    "expansion_point_at_pole",
    "symbolic_point_may_be_pole",
    "affine_path_cross_pole",
    "insufficient_taylor_order",
    "divergent_prefactor",
    "hidden_denominator_zero",
    "complex_path_real_only",
    "incorrect_boundedness",
    "symbolic_M_unproved",
    "ignore_remainder",
)


def test_ten_named_attacks_present():
    ids = [c["id"] for c in ATTACK_CASES]
    kinds = [c["kind"] for c in ATTACK_CASES]
    assert ids == list(ATTACK_IDS)
    assert kinds == list(ATTACK_KINDS)
    assert tuple(kinds) == MISSION_KINDS
    assert len(ids) == 10
    assert len(set(ids)) == 10
    assert "ignore_remainder" in kinds


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_payload_shape(case):
    assert case["should_be_certified"] is False
    assert case["expect"] in {NONANALYTIC, ASSUMPTION_REQUIRED, UNKNOWN}
    assert case["expect"] != CERTIFIED
    assert case["kind"] in MISSION_KINDS
    assert case["description"]
    assert case["function_family"]
    assert case["argument"]
    assert case["expansion_point"]
    assert case["domain_conditions"]
    assert case["degeneration_variable"] == "t"


@pytest.mark.parametrize("case", ATTACK_CASES, ids=lambda c: c["id"])
def test_attack_is_not_certified(case):
    result = check_case(case)
    assert result.expect != CERTIFIED
    assert result.got != CERTIFIED, result.extra
    assert result.false_certified is False, result.extra
    assert result.local_verdict != CERTIFIED
    assert result.certificate is not None
    assert result.certificate.verdict != CERTIFIED
    assert validate_certificate(result.certificate) != CERTIFIED
    assert remainder_cannot_be_hop_zero(result.got)


def test_run_cases_false_certified_is_zero():
    blob = run_cases()
    assert blob["n"] == len(ATTACK_CASES) + len(CONTROL_CASES)
    assert blob["n_false_certified"] == 0
    assert all(set(row) == {"id", "expect", "got"} for row in blob["rows"])
    for row in blob["rows"]:
        if row["expect"] != CERTIFIED:
            assert row["got"] != CERTIFIED, row
    assert false_certified_count() == 0
    assert all(r.got != CERTIFIED for r in check_all())


@pytest.mark.parametrize("case", load_class_c_attacks(), ids=lambda c: c["id"])
def test_class_c_validate_certificate_never_certified(case):
    assert is_class_c_or_d(case)
    cert = claimed_certificate(case)
    assert cert.verdict == CERTIFIED
    classes = {
        item.get("class")
        for item in cert.assumptions_used
        if isinstance(item, dict)
    }
    assert classes & {C_GENERICITY, D_HUMAN_REQUIRED}
    got = validate_certificate(cert)
    assert got != CERTIFIED
    assert got == ASSUMPTION_REQUIRED


def test_compile_remainder_if_present_rejects_attacks():
    fn = discover_compile_remainder()
    results = check_all()
    for result in results:
        if result.compiler_verdict is not None:
            assert result.compiler_verdict != CERTIFIED, result.extra
        if fn is not None:
            assert result.false_certified is False, result.extra


def test_expansion_point_at_pole_is_nonanalytic():
    case = next(c for c in ATTACK_CASES if c["kind"] == "expansion_point_at_pole")
    result = check_case(case)
    assert case["expansion_point"] == "0"
    assert case["distance_to_singularity"] == "0"
    assert result.got == NONANALYTIC
    assert result.extra.get("pole_kind") == "pole"
    assert validate_certificate(result.certificate) == NONANALYTIC


def test_symbolic_point_is_assumption_required():
    case = next(c for c in ATTACK_CASES if c["kind"] == "symbolic_point_may_be_pole")
    result = check_case(case)
    assert result.got == ASSUMPTION_REQUIRED
    assert result.class_c is True
    assert result.schema_verdict == ASSUMPTION_REQUIRED
    assert "z0_may_be_pole" in result.extra.get("reasons", [])


def test_affine_path_cross_pole_not_certified():
    case = next(c for c in ATTACK_CASES if c["kind"] == "affine_path_cross_pole")
    result = check_case(case)
    assert "b" in case["argument"]
    assert case["expansion_point"] == "1/2"
    assert result.got != CERTIFIED
    assert result.got == ASSUMPTION_REQUIRED
    assert "path_cross_pole" in result.extra.get("reasons", [])


def test_insufficient_taylor_order_unknown():
    case = next(c for c in ATTACK_CASES if c["kind"] == "insufficient_taylor_order")
    result = check_case(case)
    n = int(case["expansion_order"])
    needed = int(case["needed_vanish_power"])
    assert n + 1 < needed
    assert result.got == UNKNOWN
    assert result.extra.get("vanish_power") == n + 1
    assert "insufficient_order" in result.extra.get("reasons", [])


def test_divergent_prefactor_order_algebra():
    case = next(c for c in ATTACK_CASES if c["kind"] == "divergent_prefactor")
    n = int(case["expansion_order"])
    m_power = int(case["prefactor_power"])
    assert m_power < 0
    assert n + 1 + m_power <= 0
    result = check_case(case)
    assert result.got == UNKNOWN
    assert result.got != CERTIFIED
    assert "divergent_prefactor" in result.extra.get("reasons", [])


def test_hidden_denominator_zero_nonanalytic():
    case = next(c for c in ATTACK_CASES if c["kind"] == "hidden_denominator_zero")
    result = check_case(case)
    assert case["denominator"]
    assert case["numerator"]
    assert result.got == NONANALYTIC
    assert "hidden_denominator_zero" in result.extra.get("reasons", [])


def test_complex_path_real_only_assumption_required():
    case = next(c for c in ATTACK_CASES if c["kind"] == "complex_path_real_only")
    result = check_case(case)
    assert case["perturbation_complex"] is True
    assert case["real_only_assumption"] is True
    assert result.got == ASSUMPTION_REQUIRED
    assert result.schema_verdict == ASSUMPTION_REQUIRED
    assert "real_only_on_complex" in result.extra.get("reasons", [])


def test_incorrect_boundedness_unknown():
    case = next(c for c in ATTACK_CASES if c["kind"] == "incorrect_boundedness")
    result = check_case(case)
    assert float(case["bound_radius"]) > float(case["extra"]["true_distance"])
    assert result.got == UNKNOWN
    assert "bound_contains_pole" in result.extra.get("reasons", [])


def test_symbolic_M_unproved_assumption_required():
    case = next(c for c in ATTACK_CASES if c["kind"] == "symbolic_M_unproved")
    result = check_case(case)
    assert case["M_symbol"] == "M"
    assert case["M_finiteness_proved"] is False
    assert result.got == ASSUMPTION_REQUIRED
    assert result.schema_verdict == ASSUMPTION_REQUIRED
    assert "M_unproved" in result.extra.get("reasons", [])


def test_ignore_remainder_hop_not_zero():
    case = next(c for c in ATTACK_CASES if c["kind"] == "ignore_remainder")
    assert case["kind"] == "ignore_remainder"
    assert case["id"].endswith("ignore_remainder")
    result = check_case(case)
    assert result.got == UNKNOWN
    assert result.got != CERTIFIED
    assert result.hop_verdict == HOP_UNKNOWN
    assert result.hop_verdict != ZERO
    assert result.hop_level == LEVEL_B
    assert result.hop_level != LEVEL_C
    assert result.trap_ignore_remainder == ZERO
    hop, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=HOP_UNKNOWN,
    )
    assert hop == HOP_UNKNOWN
    assert hop != ZERO
    assert lvl == LEVEL_B
    assert (
        forbidden_ignore_remainder(
            negative_verdict=ZERO,
            constant_verdict=ZERO,
            remainder_verdict=HOP_UNKNOWN,
        )
        == ZERO
    )


def test_v5_negatives_c0_unknown_remainder_not_hop_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=ZERO,
        constant_verdict=ZERO,
        remainder_verdict=HOP_UNKNOWN,
    )
    assert v == HOP_UNKNOWN
    assert v != ZERO
    assert lvl == LEVEL_B


@pytest.mark.parametrize("case", CONTROL_CASES, ids=lambda c: c["id"])
def test_positive_controls_are_certified(case):
    result = check_case(case)
    assert result.expect == CERTIFIED
    assert result.got == CERTIFIED, result.extra
    assert result.false_certified is False
    assert validate_certificate(result.certificate) == CERTIFIED
    assert remainder_cannot_be_hop_zero(CERTIFIED)
    assert CERTIFIED != ZERO


def test_control_ids_match():
    assert [c["id"] for c in CONTROL_CASES] == list(CONTROL_IDS)
    assert check_controls()[0].case_id == "RC9_POS_entire_exp"


def test_prefactor_control_order_algebra():
    case = next(c for c in CONTROL_CASES if c["kind"] == "prefactor_ok")
    n = int(case["expansion_order"])
    m_power = int(case["prefactor_power"])
    assert n + 1 + m_power > 0
    result = check_case(case)
    assert result.got == CERTIFIED


def test_certified_remainder_is_not_hop_zero():
    v, lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=HOP_UNKNOWN,
        constant_verdict=HOP_UNKNOWN,
        remainder_verdict=ZERO,
    )
    assert v != ZERO
    assert remainder_cannot_be_hop_zero(CERTIFIED)


def test_compose_schema_is_the_hop_rule():
    import research.coefficient_laurent.schema as hop_schema
    import research.remainder_certification.falsifier.checkers as ch

    src = inspect.getsource(ch.check_case)
    assert "compose_hop_verdict" in src
    assert inspect.getmodule(ch.compose_hop_verdict) is hop_schema


def test_schema_file_not_rewritten():
    text = SCHEMA.read_text(encoding="utf-8")
    assert "Class-C/D assumptions forbid CERTIFIED" in text
    assert "def validate_certificate" in text
    assert "Remainder CERTIFIED is never hop ZERO" in text


def test_no_guo_gold_strings():
    patterns = [re.compile(p) for p in FORBIDDEN_GOLD_PATTERNS]
    blob = ""
    for path in FALSIFIER_DIR.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    blob += (ROOT / "tests" / "test_rc_falsifier.py").read_text(encoding="utf-8")
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
