"""Laurent remainder sufficiency. remainder_ok False is UNKNOWN, not NONZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.remainder import (  # noqa: E402
    REQUIRED_PMAX,
    SUFFICIENCY_REASON,
    UNKNOWN,
    remainder_ok,
    remainder_verdict,
    required_pmin,
)
from research.coefficient_laurent.schema import (  # noqa: E402
    ZERO,
    LaurentAtom,
)
import research.coefficient_laurent.remainder as remainder_pkg  # noqa: E402
import research.coefficient_laurent.remainder.sufficiency as sufficiency  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "remainder"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")


def test_public_api():
    assert callable(remainder_ok)
    assert callable(required_pmin)
    sig = inspect.signature(remainder_ok)
    assert "argument" in sig.parameters
    sig_p = inspect.signature(required_pmin)
    assert "pmin" in sig_p.parameters
    assert REQUIRED_PMAX == 0
    assert UNKNOWN == "UNKNOWN"
    assert remainder_pkg.remainder_ok is remainder_ok


def test_z_one_plus_t_remainder_ok():
    t = sympy.symbols("t")
    assert remainder_ok(1 + t, t) is True
    assert remainder_ok("1+t", t) is True
    assert remainder_ok("1+t", "t") is True
    assert remainder_verdict(1 + t, t) == ZERO


def test_z_t_remainder_not_ok_pole_at_zero():
    t = sympy.symbols("t")
    assert remainder_ok(t, t) is False
    assert remainder_ok("t", t) is False
    assert remainder_verdict(t, t) == UNKNOWN
    assert remainder_verdict(t, t) != ZERO
    assert remainder_verdict(t, t) != "NONZERO"


def test_nonpositive_integer_arguments_not_ok():
    t = sympy.symbols("t")
    assert remainder_ok(-t, t) is False
    assert remainder_ok(-1 + t, t) is False
    assert remainder_ok(-2 + t, t) is False
    assert remainder_ok(sympy.Integer(0), t) is False
    assert remainder_ok(0, t) is False


def test_regular_arguments_ok():
    t = sympy.symbols("t")
    assert remainder_ok(2 + t, t) is True
    assert remainder_ok(sympy.Rational(1, 2) + t, t) is True
    assert remainder_ok(1 - t, t) is True
    assert remainder_ok(1, t) is True
    assert remainder_ok(sympy.pi + t, t) is True
    assert remainder_ok(sympy.I + t, t) is True


def test_symbolic_alpha_is_unknown():
    t, a = sympy.symbols("t a")
    assert remainder_ok(a + t, t) is False
    assert remainder_verdict(a + t, t) == UNKNOWN


def test_non_affine_is_unknown():
    t = sympy.symbols("t")
    assert remainder_ok(1 / t, t) is False
    assert remainder_ok(1 + t**2, t) is False
    assert remainder_ok(sympy.exp(t), t) is False


def test_required_pmin_uses_given_pole_order_when_ok():
    t = sympy.symbols("t")
    assert required_pmin(-3) == -3
    assert required_pmin(-3, 1 + t, t) == -3
    assert required_pmin(0, 1 + t, t) == 0
    assert required_pmin(sympy.Integer(-2), "1+t", t) == -2
    assert REQUIRED_PMAX == 0


def test_required_pmin_none_when_possible_pole():
    t = sympy.symbols("t")
    assert required_pmin(-3, t, t) is None
    assert required_pmin(-1, "t", "t") is None
    assert required_pmin("not-an-int", 1 + t, t) is None


def test_full_atom_extracts_polygamma_argument():
    t = sympy.symbols("t")
    regular = sympy.polygamma(0, 1 + t) / t
    polar = sympy.polygamma(2, t) / t
    assert remainder_ok(regular, t) is True
    assert remainder_ok(polar, t) is False
    assert required_pmin(-1, regular, t) == -1
    assert required_pmin(-1, polar, t) is None


def test_laurent_atom_argument_field():
    ok_atom = LaurentAtom(
        atom_id="a1",
        source_member="src",
        argument="1+t",
        degeneration_variable="t",
        function_head="polygamma",
        function_order="0",
    )
    pole_atom = LaurentAtom(
        atom_id="a2",
        source_member="src",
        argument="t",
        degeneration_variable="t",
        function_head="polygamma",
        function_order="1",
    )
    assert remainder_ok(ok_atom) is True
    assert remainder_ok(pole_atom) is False
    assert required_pmin(-4, ok_atom) == -4
    assert required_pmin(-4, pole_atom) is None


def test_entire_negative_order_even_at_zero():
    t = sympy.symbols("t")
    assert remainder_ok(t, t, order=-2) is True
    assert remainder_ok(sympy.polygamma(-2, t), t) is True
    assert remainder_ok(sympy.polygamma(0, t), t) is False


def test_documents_why_t0_is_enough():
    readme = (PKG / "README.md").read_text(encoding="utf-8").lower()
    doc = (sufficiency.__doc__ or "").lower()
    blob = readme + "\n" + doc + "\n" + SUFFICIENCY_REASON.lower()
    for tok in (
        "t^0",
        "holomorphic",
        "nonpositive",
        "o(t)",
        "unknown",
        "pmin",
        "affine",
    ):
        assert tok in blob, tok
    assert "remainder_ok" in readme


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)


def test_remainder_false_is_unknown_not_nonzero():
    t = sympy.symbols("t")
    ok = remainder_ok(t, t)
    assert ok is False
    verdict = ZERO if ok else UNKNOWN
    assert verdict == UNKNOWN
