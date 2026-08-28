"""Newton/Hermite compositional certificates. False ZERO = 0. No Guo pairing."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.dd import hermite_dd, newton_first, repeated_diagonal
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.dd_cert import (
    Certificate,
    hermite_ok,
    hermite_xxx_ok,
    hermite_xxy_ok,
    hermite_xyy_ok,
    newton_first_ok,
    repeated_ok,
)
import research.scalable_verification.dd_cert.certificates as cert_mod


def _cubic():
    z, x, y = sympy.symbols("z x y")
    return z**3, z, x, y


def _quadratic():
    z, x, y = sympy.symbols("z x y")
    return z**2, z, x, y


def _assert_not_zero(cert: Certificate, label: str) -> None:
    assert cert.verdict != ZERO, f"{label}: false ZERO {cert.to_dict()}"
    assert cert.verdict in {NONZERO, UNKNOWN}
    assert "verdict" in cert.provenance
    assert "constructor" in cert.provenance


# --------------------------------------------------------------------------- #
# Positive controls
# --------------------------------------------------------------------------- #


def test_newton_first_ok_cubic_closed_form():
    F, z, x, y = _cubic()
    cert = newton_first_ok(F, z, x, y, x**2 + x * y + y**2)
    assert cert.verdict == ZERO, cert.to_dict()
    assert cert.kind == "NEWTON_FIRST"
    assert cert.backend.endswith("newton_first")
    assert cert.provenance["explicit_F"] is True
    assert cert.multiplicities == (1, 1)
    recon = newton_first(F, z, x, y)
    assert sympy.simplify(recon - (x**2 + x * y + y**2)) == 0


def test_newton_first_ok_quadratic_difference_form():
    F, z, x, y = _quadratic()
    cert = newton_first_ok(F, z, x, y, (x**2 - y**2) / (x - y))
    assert cert.verdict == ZERO, cert.to_dict()
    assert cert.residual == "0"


def test_repeated_ok_matches_derivative_and_hermite_mult2():
    F, z, x, _y = _cubic()
    cert = repeated_ok(F, z, x, 3 * x**2)
    assert cert.verdict == ZERO, cert.to_dict()
    assert cert.kind == "REPEATED"
    assert cert.multiplicities == (2,)
    assert cert.provenance["explicit_multiplicities"] is True
    assert sympy.expand(repeated_diagonal(F, z, x) - 3 * x**2) == 0
    assert sympy.expand(hermite_dd(F, z, [(x, 2)]) - 3 * x**2) == 0
    via_h = hermite_ok(F, z, [(x, 2)], 3 * x**2)
    assert via_h.verdict == ZERO, via_h.to_dict()


def test_repeated_ok_quadratic():
    F, z, x, _y = _quadratic()
    cert = repeated_ok(F, z, x, 2 * x)
    assert cert.verdict == ZERO, cert.to_dict()


def test_hermite_xxy_xyy_xxx_cubic():
    F, z, x, y = _cubic()
    xxy = hermite_xxy_ok(F, z, x, y, 2 * x + y)
    xyy = hermite_xyy_ok(F, z, x, y, x + 2 * y)
    xxx = hermite_xxx_ok(F, z, x, 3 * x)
    assert xxy.verdict == ZERO, xxy.to_dict()
    assert xyy.verdict == ZERO, xyy.to_dict()
    assert xxx.verdict == ZERO, xxx.to_dict()
    assert xxy.provenance["claimed"] == "F[x,x,y]"
    assert xyy.provenance["claimed"] == "F[x,y,y]"
    assert xxx.provenance["claimed"] == "F[x,x,x]"
    assert xxy.multiplicities == (2, 1)
    assert xyy.multiplicities == (1, 2)
    assert xxx.multiplicities == (3,)
    assert hermite_ok(F, z, [(x, 2), (y, 1)], 2 * x + y).verdict == ZERO
    assert hermite_ok(F, z, [(x, 1), (y, 2)], x + 2 * y).verdict == ZERO
    assert hermite_ok(F, z, [(x, 3)], F.diff(z, 2).xreplace({z: x}) / 2).verdict == ZERO


def test_exp_repeated_and_xxx():
    z, x = sympy.symbols("z x")
    F = sympy.exp(z)
    assert repeated_ok(F, z, x, sympy.exp(x)).verdict == ZERO
    assert hermite_xxx_ok(F, z, x, sympy.exp(x) / 2).verdict == ZERO
    assert hermite_ok(F, z, [(x, 2)], sympy.exp(x)).verdict == ZERO


def test_log_repeated_numeric_probe():
    z = sympy.symbols("z")
    F = sympy.log(z)
    two = sympy.Integer(2)
    assert repeated_ok(F, z, two, sympy.Rational(1, 2)).verdict == ZERO
    assert hermite_xxx_ok(F, z, two, sympy.Rational(-1, 8)).verdict == ZERO


def test_certificate_to_dict_has_provenance():
    F, z, x, y = _cubic()
    cert = newton_first_ok(F, z, x, y, x**2 + x * y + y**2)
    d = cert.to_dict()
    assert d["verdict"] == ZERO
    assert d["provenance"]["formula"].startswith("F[x,y]")
    assert d["provenance"]["explicit_F"] is True
    assert d["nodes"] == ["x", "y"]


# --------------------------------------------------------------------------- #
# Fail closed: missing F / multiplicities / ill-posed → UNKNOWN, not ZERO
# --------------------------------------------------------------------------- #


def test_missing_F_is_unknown():
    _F, z, x, y = _cubic()
    cert = newton_first_ok(None, z, x, y, x + y)
    assert cert.verdict == UNKNOWN
    assert cert.note == "missing_F"
    r = repeated_ok(None, z, x, 2 * x)
    assert r.verdict == UNKNOWN
    h = hermite_xxx_ok(None, z, x, 3 * x)
    assert h.verdict == UNKNOWN


def test_missing_member_is_unknown():
    F, z, x, y = _cubic()
    assert newton_first_ok(F, z, x, y, None).verdict == UNKNOWN
    assert repeated_ok(F, z, x, None).verdict == UNKNOWN
    assert hermite_xxy_ok(F, z, x, y, None).verdict == UNKNOWN


def test_hermite_requires_explicit_multiplicities():
    F, z, x, y = _cubic()
    # bare node list without (value, multiplicity) pairs
    cert = hermite_ok(F, z, [x, y], x**2 + x * y + y**2)
    assert cert.verdict == UNKNOWN
    assert cert.note == "missing_multiplicities"
    assert cert.provenance["explicit_multiplicities"] is False
    empty = hermite_ok(F, z, [], 0)
    assert empty.verdict == UNKNOWN
    none = hermite_ok(F, z, None, 0)
    assert none.verdict == UNKNOWN
    bad_m = hermite_ok(F, z, [(x, 0)], 3 * x**2)
    assert bad_m.verdict == UNKNOWN
    assert bad_m.verdict != ZERO


def test_mixed_hermite_nodes_unknown_not_guessed():
    F, z, x, y = _cubic()
    cert = hermite_ok(F, z, [(x, 1), (y, 1), (x, 1)], 2 * x + y)
    assert cert.verdict == UNKNOWN
    assert cert.note == "hermite_ill_posed"
    assert cert.verdict != ZERO


def test_newton_coincident_nodes_are_not_the_derivative():
    F, z, x, _y = _cubic()
    cert = newton_first_ok(F, z, x, x, 3 * x**2)
    _assert_not_zero(cert, "newton_coincident_as_derivative")
    assert cert.verdict == NONZERO
    assert cert.provenance.get("coincident_nodes") is True
    assert cert.provenance.get("not_a_derivative") is True


# --------------------------------------------------------------------------- #
# Adversarial — must not false-ZERO
# --------------------------------------------------------------------------- #


def test_adversarial_wrong_sign():
    F, z, x, y = _cubic()
    good = newton_first_ok(F, z, x, y, x**2 + x * y + y**2)
    assert good.verdict == ZERO
    flipped = newton_first_ok(F, z, x, y, -(x**2 + x * y + y**2))
    swapped = newton_first_ok(F, z, x, y, (y**3 - x**3) / (x - y))
    hsign = hermite_xxy_ok(F, z, x, y, -(2 * x + y))
    rsign = repeated_ok(F, z, x, -3 * x**2)
    for c, label in (
        (flipped, "newton_sign"),
        (swapped, "newton_swapped_numerator"),
        (hsign, "hermite_sign"),
        (rsign, "repeated_sign"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_adversarial_wrong_denom():
    F, z, x, y = _cubic()
    cert = newton_first_ok(F, z, x, y, (x**3 - y**3) / (x + y))
    _assert_not_zero(cert, "newton_wrong_denom")
    assert cert.verdict == NONZERO
    plus = newton_first_ok(F, z, x, y, (x**3 - y**3) / (y - x))
    _assert_not_zero(plus, "newton_reversed_denom")
    assert plus.verdict == NONZERO


def test_adversarial_wrong_derivative_order():
    F, z, x, _y = _cubic()
    # F[x,x] is F', not F''
    c_xx = repeated_ok(F, z, x, F.diff(z, 2).xreplace({z: x}))
    # F[x,x,x] is F''/2, not F''' and not F''
    c_xxx_d3 = hermite_xxx_ok(F, z, x, F.diff(z, 3).xreplace({z: x}))
    c_xxx_d2 = hermite_xxx_ok(F, z, x, F.diff(z, 2).xreplace({z: x}))
    c_xxx_d1 = hermite_xxx_ok(F, z, x, F.diff(z).xreplace({z: x}))
    for c, label in (
        (c_xx, "repeated_as_second_deriv"),
        (c_xxx_d3, "xxx_as_third_deriv"),
        (c_xxx_d2, "xxx_as_second_deriv_no_factorial"),
        (c_xxx_d1, "xxx_as_first_deriv"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_adversarial_wrong_factorial():
    F, z, x, _y = _cubic()
    fxx = F.diff(z, 2).xreplace({z: x})
    # true is /2!; /1, /3!, /3 are wrong
    for bad, label in (
        (fxx / 1, "xxx_div_1"),
        (fxx / 6, "xxx_div_3_fact"),
        (fxx / 3, "xxx_div_3"),
        (sympy.Integer(6), "xxx_unit_probe_wrong"),
    ):
        c = hermite_xxx_ok(F, z, x, bad)
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())
    true = hermite_xxx_ok(F, z, x, fxx / 2)
    assert true.verdict == ZERO


def test_adversarial_wrong_multiplicity():
    F, z, x, y = _cubic()
    # two-node Newton member claimed as F[x,x]
    c1 = repeated_ok(F, z, x, (x**3 - y**3) / (x - y))
    # F[x,x] claimed as F[x,x,x]
    c2 = hermite_xxx_ok(F, z, x, 3 * x**2)
    # F[x,x,y] claimed with multiplicity (3,) / (1,1)
    c3 = hermite_ok(F, z, [(x, 3)], 2 * x + y)
    c4 = hermite_ok(F, z, [(x, 1), (y, 1)], 2 * x + y)
    # F[x,x] via hermite multiplicity 1 (just F(x))
    c5 = hermite_ok(F, z, [(x, 1)], 3 * x**2)
    for c, label in (
        (c1, "newton_member_as_repeated"),
        (c2, "Fxx_as_Fxxx"),
        (c3, "xxy_member_as_xxx"),
        (c4, "xxy_member_as_xy"),
        (c5, "Fxx_as_F_of_x"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_adversarial_wrong_order_of_nodes():
    F, z, x, y = _cubic()
    # F[x,x,y]=2x+y vs F[x,y,y]=x+2y
    c1 = hermite_xyy_ok(F, z, x, y, 2 * x + y)
    c2 = hermite_xxy_ok(F, z, x, y, x + 2 * y)
    c3 = hermite_ok(F, z, [(y, 2), (x, 1)], 2 * x + y)
    c4 = hermite_ok(F, z, [(y, 1), (x, 2)], x + 2 * y)
    for c, label in (
        (c1, "xxy_member_on_xyy"),
        (c2, "xyy_member_on_xxy"),
        (c3, "blocks_yyx_vs_xxy"),
        (c4, "blocks_yxx_vs_xyy"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_false_zero_count_is_zero():
    F, z, x, y = _cubic()
    fxx = F.diff(z, 2).xreplace({z: x})
    attacks = [
        newton_first_ok(F, z, x, y, -(x**2 + x * y + y**2)),
        newton_first_ok(F, z, x, y, (x**3 - y**3) / (x + y)),
        newton_first_ok(F, z, x, y, (y**3 - x**3) / (x - y)),
        newton_first_ok(F, z, x, x, 3 * x**2),
        repeated_ok(F, z, x, -3 * x**2),
        repeated_ok(F, z, x, fxx),
        repeated_ok(F, z, x, (x**3 - y**3) / (x - y)),
        hermite_xxx_ok(F, z, x, fxx),
        hermite_xxx_ok(F, z, x, fxx / 6),
        hermite_xxx_ok(F, z, x, F.diff(z, 3).xreplace({z: x})),
        hermite_xxx_ok(F, z, x, 3 * x**2),
        hermite_xxy_ok(F, z, x, y, -(2 * x + y)),
        hermite_xxy_ok(F, z, x, y, x + 2 * y),
        hermite_xyy_ok(F, z, x, y, 2 * x + y),
        hermite_ok(F, z, [(x, 1), (y, 1)], 2 * x + y),
        hermite_ok(F, z, [(x, 3)], 2 * x + y),
        hermite_ok(F, z, [(y, 2), (x, 1)], 2 * x + y),
        hermite_ok(F, z, [x, x, y], 2 * x + y),  # missing explicit multiplicities
        hermite_ok(F, z, [(x, 1), (y, 1), (x, 1)], 2 * x + y),
        newton_first_ok(None, z, x, y, x**2 + x * y + y**2),
    ]
    false_zeros = [c for c in attacks if c.verdict == ZERO]
    assert false_zeros == [], [c.to_dict() for c in false_zeros]
    # true controls still ZERO (not a vacuous always-NONZERO checker)
    assert newton_first_ok(F, z, x, y, x**2 + x * y + y**2).verdict == ZERO
    assert repeated_ok(F, z, x, 3 * x**2).verdict == ZERO
    assert hermite_xxy_ok(F, z, x, y, 2 * x + y).verdict == ZERO
    assert hermite_xyy_ok(F, z, x, y, x + 2 * y).verdict == ZERO
    assert hermite_xxx_ok(F, z, x, 3 * x).verdict == ZERO


def test_no_catalog_member_hardcode():
    src = inspect.getsource(cert_mod)
    assert "G0001" not in src
    assert "G0007" not in src
    assert "representation_invention.guo" not in src
    assert "catalog" not in inspect.getsource(newton_first_ok).lower()
