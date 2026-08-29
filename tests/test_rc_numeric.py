"""Numeric remainder / t^{N+1} probes. Never CERTIFIED, never ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.numeric import (  # noqa: E402
    AGREE,
    ALLOWED_STATUSES,
    DISAGREE,
    EXACT_INVESTIGATION,
    FORBIDDEN_VERDICTS,
    UNDECIDED,
    numeric_probe,
    probe_report,
)
import research.remainder_certification.numeric as numeric_pkg  # noqa: E402
import research.remainder_certification.numeric.probe as probe_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "numeric"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")
FORBIDDEN = ("ZERO", "CERTIFIED", "NONANALYTIC", "NONZERO", "LEVEL_C")


def _assert_not_certificate(status: str) -> None:
    assert status in ALLOWED_STATUSES
    assert status not in FORBIDDEN
    assert status != "ZERO"
    assert status != "CERTIFIED"
    assert status != "NONANALYTIC"


def test_public_api_importable():
    assert callable(numeric_probe)
    assert callable(probe_report)
    assert numeric_probe is probe_mod.numeric_probe
    sig = inspect.signature(numeric_probe)
    assert list(sig.parameters)[:4] == ["f", "z0", "c", "n"]
    assert ALLOWED_STATUSES == frozenset({AGREE, DISAGREE, UNDECIDED})
    assert "ZERO" not in ALLOWED_STATUSES
    assert "CERTIFIED" not in ALLOWED_STATUSES
    assert "NONANALYTIC" not in ALLOWED_STATUSES
    assert not hasattr(numeric_pkg, "ZERO")
    assert not hasattr(numeric_pkg, "CERTIFIED")
    for name in FORBIDDEN:
        assert name in FORBIDDEN_VERDICTS


def test_exp_remainder_after_n2_scales_like_t3():
    status = numeric_probe(sympy.exp, 1, 1, 2)
    assert status == "agree"
    _assert_not_certificate(status)
    rec = probe_report(sympy.exp, 1, 1, 2)
    assert rec.status == AGREE
    assert rec.expansion_order == 2
    assert rec.investigation != EXACT_INVESTIGATION
    assert rec.observed_order is not None
    order = float(rec.observed_order)
    assert 2.7 <= order <= 3.3
    assert "not a certificate" in rec.note.lower() or "never" in rec.note.lower()


def test_exp_string_and_shifted_argument_agree():
    assert numeric_probe("exp", 0, 1, 2) == "agree"
    assert numeric_probe("exp", 1, 2, 2) == "agree"
    z = sympy.Dummy("z")
    assert numeric_probe(sympy.exp(z), 2, 1, 2) == "agree"
    _assert_not_certificate(numeric_probe("exp", 1, 1, 2))


def test_agree_is_not_a_certificate():
    rec = probe_report("exp", 1, 1, 2)
    assert rec.status == AGREE
    assert rec.status != "CERTIFIED"
    assert rec.status != "ZERO"
    blob = rec.to_dict()
    assert blob["status"] != "CERTIFIED"
    assert blob["status"] != "ZERO"
    assert blob["investigation"] not in FORBIDDEN
    assert "CERTIFIED" not in blob["status"]
    assert "never" in rec.note.lower()


def test_polygamma_at_numeric_pole_is_not_certified():
    z = sympy.Dummy("z")
    status = numeric_probe(sympy.polygamma(0, z), 0, 1, 2)
    assert status == "disagree"
    _assert_not_certificate(status)
    rec = probe_report(sympy.polygamma(0, z), 0, 1, 2)
    assert rec.status == DISAGREE
    assert rec.status != "CERTIFIED"
    assert rec.status != "NONANALYTIC"
    assert rec.investigation == EXACT_INVESTIGATION
    assert rec.investigation != "NONANALYTIC"
    assert rec.investigation != "CERTIFIED"
    assert "not NONANALYTIC" in rec.note or "investigation" in rec.note.lower()
    assert numeric_probe(sympy.polygamma(0, z), 0, 1, 2) != EXACT_INVESTIGATION


def test_polygamma_negative_integer_pole_is_not_certified():
    z = sympy.Dummy("z")
    for pole in (0, -1, -2):
        status = numeric_probe(sympy.polygamma(0, z), pole, 1, 2)
        assert status in ALLOWED_STATUSES
        assert status != "CERTIFIED"
        rec = probe_report(sympy.polygamma(0, z), pole, 1, 2)
        assert rec.status != "CERTIFIED"
        assert rec.status != "NONANALYTIC"
        assert rec.investigation != "NONANALYTIC"


def test_polygamma_safe_point_agrees_but_does_not_certify():
    z = sympy.Dummy("z")
    status = numeric_probe(sympy.polygamma(0, z), 1, 1, 2)
    assert status == "agree"
    _assert_not_certificate(status)
    rec = probe_report(sympy.polygamma(0, z), 1, 1, 2)
    assert rec.status == AGREE
    assert rec.status != "CERTIFIED"
    assert rec.investigation != EXACT_INVESTIGATION


def test_symbolic_polygamma_without_declared_domain_is_undecided():
    z = sympy.Dummy("z")
    z0 = sympy.Symbol("z0")
    status = numeric_probe(sympy.polygamma(0, z), z0, 1, 2)
    assert status == "undecided"
    _assert_not_certificate(status)
    rec = probe_report(sympy.polygamma(0, z), z0, 1, 2)
    assert rec.status == UNDECIDED
    assert rec.status != "CERTIFIED"
    assert rec.investigation != "NONANALYTIC"


def test_entire_symbolic_parameters_may_agree_without_certifying():
    z0, c = sympy.symbols("z0 c")
    status = numeric_probe(sympy.exp, z0, c, 2)
    assert status == "agree"
    _assert_not_certificate(status)


def test_non_entire_symbolic_argument_is_undecided():
    z = sympy.Dummy("z")
    z0 = sympy.Symbol("z0")
    status = numeric_probe(sympy.exp(1 / z), z0, 1, 2)
    assert status == "undecided"
    _assert_not_certificate(status)


def test_rational_pole_is_not_certified():
    z = sympy.Dummy("z")
    status = numeric_probe(1 / z, 0, 1, 2)
    assert status == "disagree"
    _assert_not_certificate(status)
    rec = probe_report(1 / z, 0, 1, 2)
    assert rec.status != "CERTIFIED"
    assert rec.investigation == EXACT_INVESTIGATION
    assert rec.investigation != "NONANALYTIC"


def test_log_at_zero_disagrees_without_minting_nonanalytic():
    status = numeric_probe("log", 0, 1, 2)
    assert status == "disagree"
    _assert_not_certificate(status)
    rec = probe_report("log", 0, 1, 2)
    assert rec.investigation == EXACT_INVESTIGATION
    assert rec.status != "NONANALYTIC"


def test_log_safe_disk_agrees_without_certifying():
    status = numeric_probe("log", 1, 1, 2)
    assert status == "agree"
    _assert_not_certificate(status)


def test_probe_never_returns_forbidden_verdicts():
    z = sympy.Dummy("z")
    cases = [
        (sympy.exp, 1, 1, 2),
        (sympy.exp, 0, 2, 2),
        ("exp", 1, 1, 2),
        (sympy.polygamma(0, z), 0, 1, 2),
        (sympy.polygamma(0, z), 1, 1, 2),
        (sympy.polygamma(0, z), -1, 1, 2),
        ("log", 0, 1, 2),
        ("log", 1, 1, 2),
        (sympy.sin, 0, 1, 2),
        (None, None, None, None),
        ("???", 1, 1, 2),
    ]
    for args in cases:
        status = numeric_probe(*args)
        _assert_not_certificate(status)
        rec = probe_report(*args)
        _assert_not_certificate(rec.status)
        blob = rec.to_dict()
        assert blob["status"] not in FORBIDDEN
        assert blob["investigation"] not in FORBIDDEN


def test_strong_disagree_is_exact_investigation_not_status():
    rec = probe_report("log", 0, 1, 2)
    assert rec.status == DISAGREE
    assert rec.investigation == EXACT_INVESTIGATION
    assert rec.investigation != "ZERO"
    assert rec.investigation != "NONANALYTIC"
    assert numeric_probe("log", 0, 1, 2) != EXACT_INVESTIGATION
    assert numeric_probe("log", 0, 1, 2) == "disagree"


def test_garbage_and_empty_are_undecided():
    assert numeric_probe(None, None, None, None) == "undecided"
    assert numeric_probe("???", 1, 1, 2) == "undecided"
    assert numeric_probe("", 1, 1, 2) == "undecided"
    assert numeric_probe("exp", 1, 1, -1) == "undecided"
    rec = probe_report("not an expr", 1, 1, 2)
    assert rec.status == UNDECIDED
    assert rec.status != "ZERO"
    assert rec.status != "CERTIFIED"


def test_readme_forbids_certificates():
    text = (PKG / "README.md").read_text(encoding="utf-8").lower()
    assert "not a verifier" in text
    assert "never" in text and "certified" in text
    assert "never" in text and "zero" in text
    assert "exact_investigation" in text
    assert "not" in text and "nonanalytic" in text


def test_source_ban_no_gold_names_and_no_certificate_return():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
    py = inspect.getsource(probe_mod)
    assert 'return "ZERO"' not in py
    assert "return ZERO" not in py
    assert 'return "CERTIFIED"' not in py
    assert "return CERTIFIED" not in py
    assert 'return "NONANALYTIC"' not in py
    assert "return NONANALYTIC" not in py
    assert "FAMILY_ZERO" not in py
    assert "LEVEL_C" not in py or "FORBIDDEN" in py
    assert "openai" not in py.lower()
    assert "llm" not in py.lower() or "No LLM" in py or "no LLM" in py
