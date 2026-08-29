"""Exact affine argument normalizer. Residual must be 0 or UNSUPPORTED."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.affine import (  # noqa: E402
    AffineNormalization,
    UNSUPPORTED,
    normalize_affine,
)
from research.remainder_certification.affine import (  # noqa: E402
    normalize as affine_mod,
)
from research.remainder_certification.schema import (  # noqa: E402
    CERTIFIED,
    HOP_ZERO,
    UNSUPPORTED as SCHEMA_UNSUPPORTED,
)

PKG = ROOT / "research" / "remainder_certification" / "affine"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")

t, z0, c, d, a = sympy.symbols("t z0 c d a")
beta, gamma, mu, epsilon = sympy.symbols("beta gamma mu epsilon")
I, pi = sympy.I, sympy.pi


def _eq(u: sympy.Expr, v: sympy.Expr) -> bool:
    try:
        return sympy.expand(u - v) == 0
    except Exception:
        return False


def _expect(z: sympy.Expr, t_sym: sympy.Symbol, expect_z0: sympy.Expr, expect_c: sympy.Expr):
    got = normalize_affine(z, t_sym)
    assert got is not UNSUPPORTED
    assert isinstance(got, AffineNormalization)
    assert got.residual == 0
    assert got.residual is sympy.Integer(0) or got.residual == sympy.Integer(0)
    assert not got.z0.has(t_sym)
    assert not got.c.has(t_sym)
    assert sympy.expand(z - (got.z0 + got.c * t_sym)) == 0
    assert sympy.expand(z - (got.z0 + got.c * t_sym)) == got.residual
    assert _eq(got.z0, expect_z0)
    assert _eq(got.c, expect_c)
    return got


def test_public_api():
    assert callable(normalize_affine)
    assert UNSUPPORTED == "UNSUPPORTED"
    assert UNSUPPORTED == SCHEMA_UNSUPPORTED
    assert UNSUPPORTED != CERTIFIED
    assert UNSUPPORTED != HOP_ZERO
    assert affine_mod.normalize_affine is normalize_affine
    sig = inspect.signature(normalize_affine)
    assert list(sig.parameters)[:2] == ["z", "t"]


def test_plain_affine():
    _expect(z0 + c * t, t, z0, c)
    _expect(z0 + t * c, t, z0, c)
    _expect(c * t + z0, t, z0, c)
    _expect(t * c + z0, t, z0, c)


def test_add_rearrangements():
    _expect(sympy.Add(z0, c * t, evaluate=False), t, z0, c)
    _expect(sympy.Add(c * t, z0, evaluate=False), t, z0, c)
    _expect(sympy.Add(t * c, z0, evaluate=False), t, z0, c)
    _expect(sympy.Add(z0, t * c, evaluate=False), t, z0, c)
    split = sympy.Add(z0, c * t / 2, c * t / 2, evaluate=False)
    _expect(split, t, z0, c)


def test_algebraically_equivalent_half():
    half = sympy.Mul(
        sympy.Add(
            sympy.Mul(2, z0, evaluate=False),
            sympy.Mul(2, sympy.Mul(c, t, evaluate=False), evaluate=False),
            evaluate=False,
        ),
        sympy.Pow(sympy.Integer(2), sympy.Integer(-1), evaluate=False),
        evaluate=False,
    )
    _expect(half, t, z0, c)
    _expect(
        sympy.Mul(
            sympy.Add(2 * z0, 2 * c * t, evaluate=False),
            sympy.Rational(1, 2),
            evaluate=False,
        ),
        t,
        z0,
        c,
    )
    _expect(2 * (z0 + c * t) / 2, t, z0, c)
    _expect((4 * (z0 + c * t)) / 4, t, z0, c)


def test_constant_is_affine_with_c_zero():
    _expect(z0, t, z0, sympy.Integer(0))
    _expect(sympy.Integer(5), t, sympy.Integer(5), sympy.Integer(0))
    _expect(7, t, sympy.Integer(7), sympy.Integer(0))


def test_rational_and_imaginary_slopes():
    _expect(z0 + t / 2, t, z0, sympy.Rational(1, 2))
    _expect(z0 + 3 * t, t, z0, sympy.Integer(3))
    _expect(z0 - c * t, t, z0, -c)
    _expect(z0 + I * t, t, z0, I)


def test_motivating_shaped_z0():
    z0_plus = sympy.Rational(1, 2) + beta * (gamma + I * (mu - epsilon)) / (2 * pi)
    z0_minus = sympy.Rational(1, 2) + beta * (gamma - I * (mu - epsilon)) / (2 * pi)
    _expect(z0_plus + c * t, t, z0_plus, c)
    _expect(z0_minus + c * t, t, z0_minus, c)
    _expect(z0_plus + t, t, z0_plus, sympy.Integer(1))
    rearranged = (
        sympy.Rational(1, 2)
        + beta * gamma / (2 * pi)
        + I * beta * (mu - epsilon) / (2 * pi)
        + c * t
    )
    _expect(rearranged, t, z0_plus, c)


def test_quadratic_is_unsupported():
    assert normalize_affine(z0 + c * t + d * t**2, t) is UNSUPPORTED
    assert normalize_affine(z0 + t**2, t) is UNSUPPORTED
    assert normalize_affine(d * t**2, t) is UNSUPPORTED
    uneval = sympy.Add(z0, c * t, d * sympy.Pow(t, 2, evaluate=False), evaluate=False)
    assert normalize_affine(uneval, t) is UNSUPPORTED


def test_non_affine_rational_is_unsupported():
    assert normalize_affine(1 / (a + t), t) is UNSUPPORTED
    assert normalize_affine(1 / (z0 + c * t), t) is UNSUPPORTED
    assert normalize_affine(z0 / (1 + t), t) is UNSUPPORTED
    assert normalize_affine((2 + 2 * t) / (1 + t), t) is UNSUPPORTED


def test_transcendental_is_unsupported():
    assert normalize_affine(sympy.exp(t), t) is UNSUPPORTED
    assert normalize_affine(sympy.exp(z0 + c * t), t) is UNSUPPORTED
    assert normalize_affine(sympy.sin(t), t) is UNSUPPORTED
    assert normalize_affine(z0 + c * sympy.sin(t), t) is UNSUPPORTED


def test_t_by_name_and_inexact_rejected():
    got = normalize_affine(z0 + c * t, "t")
    assert isinstance(got, AffineNormalization)
    assert _eq(got.z0, z0) and _eq(got.c, c)
    assert normalize_affine(z0 + sympy.Float(1.0) * t, t) is UNSUPPORTED
    assert normalize_affine(1.5, t) is UNSUPPORTED
    assert normalize_affine(True, t) is UNSUPPORTED
    assert normalize_affine(z0 + c * t, 0) is UNSUPPORTED


def test_never_returns_nonzero_residual():
    samples = [
        z0 + c * t,
        z0 + t * c,
        (2 * z0 + 2 * c * t) / 2,
        z0 + c * t / 2 + c * t / 2,
        sympy.Add(c * t, z0, evaluate=False),
        z0,
        z0 + c * t + d * t**2,
        1 / (a + t),
        sympy.exp(t),
        sympy.Rational(1, 2)
        + beta * (gamma + I * (mu - epsilon)) / (2 * pi)
        + c * t,
    ]
    for z in samples:
        got = normalize_affine(z, t)
        if got is UNSUPPORTED:
            continue
        assert got.residual == 0
        assert sympy.expand(z - (got.z0 + got.c * t)) == 0


def test_not_a_remainder_or_hop_verdict():
    got = normalize_affine(z0 + c * t, t)
    assert got is not CERTIFIED
    assert got is not HOP_ZERO
    src = (PKG / "normalize.py").read_text(encoding="utf-8")
    assert "CERTIFIED" not in src
    assert "simplify(" not in src


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        text = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in text, (path.name, tok)


def test_readme_states_exact_residual_contract():
    readme = (PKG / "README.md").read_text(encoding="utf-8").lower()
    for tok in (
        "z0",
        "unsupported",
        "residual",
        "expand",
        "quadratic",
        "affine",
        "hop",
    ):
        assert tok in readme, tok
    assert "not v6" in readme or "not track v6" in readme
