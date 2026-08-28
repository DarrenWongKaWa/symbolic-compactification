"""Local polygamma identity classification. No invented masters. No Guo ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.special import (
    UNKNOWN,
    UNSUPPORTED,
    SUPPORTED,
    classify_identity,
)


def test_public_api_labels():
    assert SUPPORTED == "supported"
    assert UNSUPPORTED == "unsupported"
    assert UNKNOWN == "UNKNOWN"
    assert classify_identity is not None


def test_sympy_has_polygamma_derivative_identity():
    n, z = sympy.symbols("n z")
    assert sympy.diff(sympy.polygamma(n, z), z) == sympy.polygamma(n + 1, z)
    uneval = sympy.Derivative(sympy.polygamma(n, z), z)
    assert uneval.doit() == sympy.polygamma(n + 1, z)


def test_derivative_identity_supported_unevaluated_and_string():
    n, z = sympy.symbols("n z")
    left = sympy.Derivative(sympy.polygamma(n, z), z)
    right = sympy.polygamma(n + 1, z)
    assert classify_identity((left, right)) == SUPPORTED
    assert classify_identity(sympy.Eq(left, right)) == SUPPORTED
    assert classify_identity(
        "diff(polygamma(n, z), z) = polygamma(n + 1, z)"
    ) == SUPPORTED
    assert classify_identity(
        {"left": left, "right": right}
    ) == SUPPORTED
    residual = left - right
    assert classify_identity(residual) == SUPPORTED


def test_derivative_identity_supported_integer_order_and_evaluated_diff():
    z = sympy.symbols("z")
    left = sympy.Derivative(sympy.polygamma(0, z), z)
    assert classify_identity((left, sympy.polygamma(1, z))) == SUPPORTED
    n = sympy.symbols("n")
    ev = sympy.diff(sympy.polygamma(n, z), z)
    assert classify_identity((ev, sympy.polygamma(n + 1, z))) == SUPPORTED


def test_newton_first_vs_psi_quotient_supported():
    x, y = sympy.symbols("x y")
    pg = (sympy.polygamma(0, x) - sympy.polygamma(0, y)) / (x - y)
    # SymPy 1.14 stores digamma as polygamma(0, ·); psi is a parse alias.
    assert classify_identity((
        pg,
        "(psi(x) - psi(y))/(x - y)",
    )) == SUPPORTED
    assert classify_identity((
        "(polygamma(0, x) - polygamma(0, y))/(x - y)",
        "(psi(x) - psi(y))/(x - y)",
    )) == SUPPORTED
    swapped = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (y - x)
    assert classify_identity((pg, swapped)) == SUPPORTED


def test_wrong_polygamma_order_unsupported():
    z = sympy.symbols("z")
    assert classify_identity((
        sympy.polygamma(0, z),
        sympy.polygamma(1, z),
    )) == UNSUPPORTED
    n = sympy.symbols("n")
    assert classify_identity((
        sympy.Derivative(sympy.polygamma(n, z), z),
        sympy.polygamma(n + 2, z),
    )) == UNSUPPORTED


def test_recurrence_and_confluence_slogan_unsupported():
    z, x, y = sympy.symbols("z x y")
    rec = sympy.polygamma(0, z + 1) - sympy.polygamma(0, z)
    assert classify_identity((rec, 1 / z)) == UNSUPPORTED
    newton = (sympy.polygamma(0, x) - sympy.polygamma(0, y)) / (x - y)
    # Confluence / diagonal is not a listed local identity (V3/V4, not V5).
    assert classify_identity((newton, sympy.polygamma(1, x))) == UNSUPPORTED
    flipped = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (x - y)
    assert classify_identity((
        flipped,
        "(psi(x) - psi(y))/(x - y)",
    )) == UNSUPPORTED


def test_phi_gamma_and_l4_l7_unsupported():
    assert classify_identity("Phi_Gamma(z) = polygamma(0, z)") == UNSUPPORTED
    assert classify_identity("L4 = polygamma(0, zP) + polygamma(0, zM)") == UNSUPPORTED
    assert classify_identity("L5 H1 = polygamma(1, z)") == UNSUPPORTED
    assert classify_identity(("L6", "polygamma(0, z)")) == UNSUPPORTED
    assert classify_identity("L7 master = polygamma(2, z)") == UNSUPPORTED


def test_higher_order_derivative_not_widened():
    n, z = sympy.symbols("n z")
    left = sympy.Derivative(sympy.polygamma(n, z), (z, 2))
    right = sympy.polygamma(n + 2, z)
    assert classify_identity((left, right)) == UNSUPPORTED


def test_algebra_and_garbage_unknown():
    x, y = sympy.symbols("x y")
    assert classify_identity((x + y, y + x)) == UNKNOWN
    assert classify_identity("???") == UNKNOWN
    assert classify_identity(None) == UNKNOWN
    assert classify_identity((x, y, x)) == UNKNOWN


def test_guo_source_unknown_reduction_not_demonstrated():
    text = (ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt").read_text()
    assert len(text) > 4096
    assert classify_identity(text) == UNKNOWN
    assert classify_identity((text, "polygamma(1, z)")) == UNKNOWN
    assert classify_identity(text) != SUPPORTED


def test_no_master_constructors_in_package():
    pkg = ROOT / "research" / "scalable_verification" / "special"
    for path in sorted(pkg.glob("*.py")):
        src = path.read_text()
        assert "def Phi_Gamma" not in src
        assert "def L4" not in src
        assert "def L5" not in src
        assert "def L6" not in src
        assert "def L7" not in src
