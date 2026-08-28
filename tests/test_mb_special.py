"""Local polygamma prover for Track V2. No invented masters. No Guo ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.special import classify_identity
from research.multibranch_verification.special import (
    DERIVATIVE,
    NEWTON_FIRST,
    SERIES,
    LocalProof,
    prove_local,
)


def _pg():
    return sympy.polygamma


def test_public_api_verdicts_and_classify_reuse():
    assert ZERO == "ZERO"
    assert NONZERO == "NONZERO"
    assert UNKNOWN == "UNKNOWN"
    assert prove_local is not None
    src = (ROOT / "research" / "multibranch_verification" / "special" / "prove.py").read_text()
    assert "classify_identity" in src
    assert "research.scalable_verification.special" in src
    assert "sympy.limit(" not in src
    assert "expand_func" not in src


def test_derivative_identity_zero():
    n, z = sympy.symbols("n z")
    pg = _pg()
    left = sympy.Derivative(pg(n, z), z)
    right = pg(n + 1, z)
    for claim in (
        (left, right),
        sympy.Eq(left, right),
        "diff(polygamma(n, z), z) = polygamma(n + 1, z)",
        {"left": left, "right": right},
        left - right,
    ):
        r = prove_local(claim)
        assert r.verdict == ZERO, (claim, r.to_dict())
        assert r.verdict != UNKNOWN
        assert r.identity == DERIVATIVE
    ev = sympy.diff(pg(n, z), z)
    assert prove_local((ev, pg(n + 1, z))).verdict == ZERO


def test_derivative_after_spectators_zero():
    n, z = sympy.symbols("n z")
    pg = _pg()
    h1 = sympy.Function("h1")
    left = sympy.Derivative(pg(n, z), z)
    right = pg(n + 1, z)
    r_mul = prove_local((h1(z) * left, h1(z) * right))
    assert r_mul.verdict == ZERO, r_mul.to_dict()
    assert any("spectator_mul" in s for s in r_mul.steps)
    r_c = prove_local((3 * left, 3 * right))
    assert r_c.verdict == ZERO, r_c.to_dict()
    r_add = prove_local((left + z, right + z))
    assert r_add.verdict == ZERO, r_add.to_dict()
    assert any("spectator_add" in s for s in r_add.steps)


def test_newton_first_vs_psi_zero():
    x, y = sympy.symbols("x y")
    pg = _pg()
    newt = (pg(0, x) - pg(0, y)) / (x - y)
    r = prove_local((newt, "(psi(x) - psi(y))/(x - y)"))
    assert r.verdict == ZERO, r.to_dict()
    assert r.identity == NEWTON_FIRST
    assert classify_identity((newt, "(psi(x) - psi(y))/(x - y)")) == "supported"
    swapped = (pg(0, y) - pg(0, x)) / (y - x)
    assert prove_local((newt, swapped)).verdict == ZERO


def test_series_newton_to_trigamma_zero():
    x, y = sympy.symbols("x y")
    pg = _pg()
    newt = (pg(0, x) - pg(0, y)) / (x - y)
    r = prove_local(
        (newt, pg(1, x)),
        relation="series",
        variable=y,
        target=x,
    )
    assert r.verdict == ZERO, r.to_dict()
    assert r.identity == SERIES
    r2 = prove_local({"left": newt, "right": pg(1, x), "relation": "series"})
    assert r2.verdict == ZERO, r2.to_dict()
    n = sympy.symbols("n")
    newt_n = (pg(n, x) - pg(n, y)) / (x - y)
    r3 = prove_local((newt_n, pg(n + 1, x)), relation="series", variable=y, target=x)
    assert r3.verdict == ZERO, r3.to_dict()


def test_newton_vs_trigamma_without_series_relation_is_not_zero():
    x, y = sympy.symbols("x y")
    pg = _pg()
    newt = (pg(0, x) - pg(0, y)) / (x - y)
    r = prove_local((newt, pg(1, x)))
    assert r.verdict != ZERO, r.to_dict()
    assert classify_identity((newt, pg(1, x))) == "unsupported"


def test_wrong_derivative_order_nonzero():
    n, z = sympy.symbols("n z")
    pg = _pg()
    left = sympy.Derivative(pg(n, z), z)
    r = prove_local((left, pg(n + 2, z)))
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO
    assert prove_local((pg(0, z), pg(1, z))).verdict == NONZERO


def test_flipped_newton_nonzero():
    x, y = sympy.symbols("x y")
    pg = _pg()
    newt = (pg(0, x) - pg(0, y)) / (x - y)
    flipped = (pg(0, y) - pg(0, x)) / (x - y)
    r = prove_local((flipped, "(psi(x) - psi(y))/(x - y)"))
    assert r.verdict == NONZERO, r.to_dict()
    r2 = prove_local(
        (flipped, pg(1, x)),
        relation="series",
        variable=y,
        target=x,
    )
    assert r2.verdict == NONZERO, r2.to_dict()


def test_series_wrong_target_nonzero():
    x, y = sympy.symbols("x y")
    pg = _pg()
    newt = (pg(0, x) - pg(0, y)) / (x - y)
    r = prove_local((newt, pg(2, x)), relation="series", variable=y, target=x)
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_recurrence_not_zero():
    z = sympy.symbols("z")
    pg = _pg()
    rec = pg(0, z + 1) - pg(0, z)
    r = prove_local((rec, 1 / z))
    assert r.verdict != ZERO, r.to_dict()
    assert r.verdict == UNKNOWN
    assert sympy.expand_func(rec - 1 / z) == 0


def test_higher_order_derivative_not_zero():
    n, z = sympy.symbols("n z")
    pg = _pg()
    left = sympy.Derivative(pg(n, z), (z, 2))
    r = prove_local((left, pg(n + 2, z)))
    assert r.verdict != ZERO, r.to_dict()


def test_chain_rule_not_zero():
    n, z = sympy.symbols("n z")
    pg = _pg()
    left = sympy.Derivative(pg(n, 2 * z), z)
    r = prove_local((left, 2 * pg(n + 1, 2 * z)))
    assert r.verdict != ZERO, r.to_dict()


def test_phi_gamma_and_l4_l7_unknown():
    for text in (
        "Phi_Gamma(z) = polygamma(0, z)",
        "L4 = polygamma(0, zP) + polygamma(0, zM)",
        "L5 H1 = polygamma(1, z)",
        "L7 master = polygamma(2, z)",
    ):
        r = prove_local(text)
        assert r.verdict != ZERO, (text, r.to_dict())
        assert r.verdict == UNKNOWN


def test_algebra_and_garbage_unknown():
    x, y = sympy.symbols("x y")
    assert prove_local((x + y, y + x)).verdict == UNKNOWN
    assert prove_local("???").verdict == UNKNOWN
    assert prove_local(None).verdict == UNKNOWN
    r = prove_local((x, y, x))
    assert isinstance(r, LocalProof)
    assert r.verdict == UNKNOWN


def test_guo_source_unknown():
    text = (ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt").read_text()
    assert len(text) > 4096
    r = prove_local(text)
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert prove_local((text, "polygamma(1, z)")).verdict == UNKNOWN


def test_no_master_constructors_in_package():
    pkg = ROOT / "research" / "multibranch_verification" / "special"
    for path in sorted(pkg.glob("*.py")):
        src = path.read_text()
        assert "def Phi_Gamma" not in src
        assert "def L4" not in src
        assert "def L5" not in src
        assert "def L6" not in src
        assert "def L7" not in src
