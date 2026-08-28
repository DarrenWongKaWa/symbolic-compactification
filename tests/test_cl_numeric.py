"""Numeric probes of lim t->0 E_gen vs E_diag. Never certify ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.numeric import (  # noqa: E402
    AGREE,
    ALLOWED_STATUSES,
    DISAGREE,
    SUSPECT_NONZERO,
    UNDECIDED,
    numeric_probe,
    probe_report,
)
import research.coefficient_laurent.numeric as numeric_pkg  # noqa: E402
import research.coefficient_laurent.numeric.probe as probe_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "numeric"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma")


def _xy():
    return sympy.symbols("x y")


def _cubic_gen():
    x, y = _xy()
    return (y**3 - x**3) / (y - x), x, y


def test_public_api_importable():
    assert callable(numeric_probe)
    assert callable(probe_report)
    assert numeric_probe is probe_mod.numeric_probe
    sig = inspect.signature(numeric_probe)
    assert list(sig.parameters)[:2] == ["e_gen", "e_diag"]
    assert ALLOWED_STATUSES == frozenset({AGREE, DISAGREE, UNDECIDED})
    assert "ZERO" not in ALLOWED_STATUSES
    assert not hasattr(numeric_pkg, "ZERO")


def test_cubic_agrees_with_3x2():
    gen, x, _y = _cubic_gen()
    status = numeric_probe(gen, 3 * x**2)
    assert status == "agree"
    assert status != "ZERO"


def test_cubic_disagrees_with_4x2():
    gen, x, _y = _cubic_gen()
    status = numeric_probe(gen, 4 * x**2)
    assert status == "disagree"
    assert status != "ZERO"


def test_probe_never_returns_zero():
    gen, x, y = _cubic_gen()
    for diag in (3 * x**2, 4 * x**2, x**2 + x * y + y**2, sympy.Integer(0)):
        status = numeric_probe(gen, diag)
        assert status in ALLOWED_STATUSES
        assert status != "ZERO"
        assert status != "NONZERO"
        rec = probe_report(gen, diag)
        assert rec.status in ALLOWED_STATUSES
        assert rec.status != "ZERO"
        blob = rec.to_dict()
        assert blob["status"] != "ZERO"
        assert "ZERO" not in {blob["status"], blob["investigation"]}


def test_strong_disagree_is_suspect_nonzero_investigation():
    gen, x, _y = _cubic_gen()
    rec = probe_report(gen, 4 * x**2)
    assert rec.status == DISAGREE
    assert rec.investigation == SUSPECT_NONZERO
    assert rec.investigation != "ZERO"
    assert numeric_probe(gen, 4 * x**2) != SUSPECT_NONZERO


def test_agree_is_not_a_certificate():
    gen, x, _y = _cubic_gen()
    rec = probe_report(gen, 3 * x**2)
    assert rec.status == AGREE
    assert rec.investigation != SUSPECT_NONZERO
    assert "never" in rec.note.lower() or "not a certificate" in rec.note.lower()
    assert rec.status != "ZERO"


def test_string_forms_match_sympy():
    x, y = _xy()
    gen = (y**3 - x**3) / (y - x)
    assert numeric_probe("(y**3-x**3)/(y-x)", "3*x**2") == "agree"
    assert numeric_probe("(y**3-x**3)/(y-x)", "4*x**2") == "disagree"
    assert numeric_probe(gen, "3*x**2") == numeric_probe(gen, 3 * x**2)


def test_explicit_degeneration_y_to_x():
    gen, x, y = _cubic_gen()
    assert numeric_probe(gen, 3 * x**2, y, x) == "agree"
    assert numeric_probe(gen, 4 * x**2, degeneration_variable=y, target_value=x) == (
        "disagree"
    )


def test_parameter_t_to_zero_agrees_with_derivative():
    x, t = sympy.symbols("x t")
    gen = ((x + t) ** 3 - x**3) / t
    assert numeric_probe(gen, 3 * x**2) == "agree"
    assert numeric_probe(gen, 4 * x**2) == "disagree"
    assert numeric_probe(gen, 3 * x**2) != "ZERO"


def test_pole_is_disagree_not_zero():
    x, y = _xy()
    status = numeric_probe(1 / (y - x), 3 * x**2)
    assert status == "disagree"
    rec = probe_report(1 / (y - x), 3 * x**2)
    assert rec.investigation == SUSPECT_NONZERO
    assert rec.status != "ZERO"


def test_garbage_and_empty_are_undecided():
    assert numeric_probe(None, None) == "undecided"
    assert numeric_probe("???", "1") == "undecided"
    assert numeric_probe("", "0") == "undecided"
    rec = probe_report("not an expr", 1)
    assert rec.status == UNDECIDED
    assert rec.status != "ZERO"


def test_readme_forbids_zero_certificate():
    text = (PKG / "README.md").read_text(encoding="utf-8").lower()
    assert "not a verifier" in text
    assert "never" in text and "zero" in text
    assert "suspect_nonzero" in text


def test_source_ban_no_gold_names_and_no_zero_return():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
    py = inspect.getsource(probe_mod)
    assert 'return "ZERO"' not in py
    assert "return ZERO" not in py
    assert "FAMILY_ZERO" not in py
    assert "openai" not in py.lower()
    assert "llm" not in py.lower() or "No LLM" in py or "no LLM" in py
