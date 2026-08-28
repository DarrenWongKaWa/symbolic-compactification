"""Generic Newton/Hermite recurrence checks. False ZERO = 0. No source gold."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.dd import (
    hermite_dd,
    newton_first,
    newton_table,
    repeated_diagonal,
)
from research.multibranch_verification.recurrence import (
    FORMULAS,
    KIND_FXX,
    KIND_FXXX,
    KIND_FXXY,
    KIND_FXYY,
    KIND_HERMITE_STEP,
    KIND_NEWTON_STEP,
    NONZERO,
    REL_DD,
    REL_HERMITE,
    RecurrenceResult,
    UNKNOWN,
    ZERO,
    check_recurrence,
)
import research.multibranch_verification.recurrence.check as check_mod


def _cubic():
    z, x, y, w = sympy.symbols("z x y w")
    return z**3, z, x, y, w


def _quadratic():
    z, x, y = sympy.symbols("z x y")
    return z**2, z, x, y


def _assert_not_zero(result: RecurrenceResult, label: str) -> None:
    assert result.verdict != ZERO, f"{label}: false ZERO {result.to_dict()}"
    assert result.verdict in {NONZERO, UNKNOWN}
    assert "verdict" in result.provenance
    assert "constructor" in result.provenance
    assert "formula" in result.provenance


# --------------------------------------------------------------------------- #
# Positive controls
# --------------------------------------------------------------------------- #


def test_public_api_and_formulas():
    assert FORMULAS[KIND_FXX] == "F[x,x]=F'(x)"
    assert FORMULAS[KIND_FXXY] == "F[x,x,y]=(F[x,x]-F[x,y])/(x-y)"
    assert FORMULAS[KIND_FXYY] == "F[x,y,y]=(F[x,y]-F[y,y])/(x-y)"
    assert FORMULAS[KIND_FXXX] == "F[x,x,x]=F''(x)/2"
    F, z, x, y, _w = _cubic()
    r = check_recurrence(KIND_FXX, F, z, x)
    assert r.relation == REL_HERMITE
    d = r.to_dict()
    assert d["verdict"] == ZERO
    assert d["provenance"]["formula"] == FORMULAS[KIND_FXX]
    assert "constructor" in d["provenance"]
    ob = r.to_obligation()
    assert ob["relation"] == REL_HERMITE
    assert ob["verdict"] == ZERO


def test_Fxx_equals_derivative():
    F, z, x, _y, _w = _cubic()
    r = check_recurrence(KIND_FXX, F, z, x)
    assert r.verdict == ZERO, r.to_dict()
    assert r.formula == "F[x,x]=F'(x)"
    assert r.multiplicities == (2,)
    assert sympy.expand(repeated_diagonal(F, z, x) - 3 * x**2) == 0
    assert sympy.expand(hermite_dd(F, z, [(x, 2)]) - 3 * x**2) == 0
    claimed = check_recurrence("Fxx", F, z, x, claimed=3 * x**2)
    assert claimed.verdict == ZERO, claimed.to_dict()
    deriv = check_recurrence(KIND_FXX, F, z, x, claimed=F.diff(z).xreplace({z: x}))
    assert deriv.verdict == ZERO


def test_Fxxy_recurrence_and_closed_form():
    F, z, x, y, _w = _cubic()
    ident = check_recurrence(KIND_FXXY, F, z, x, y)
    assert ident.verdict == ZERO, ident.to_dict()
    assert ident.formula == "F[x,x,y]=(F[x,x]-F[x,y])/(x-y)"
    assert ident.multiplicities == (2, 1)
    closed = check_recurrence(KIND_FXXY, F, z, x, y, claimed=2 * x + y)
    assert closed.verdict == ZERO, closed.to_dict()
    recon = hermite_dd(F, z, [(x, 2), (y, 1)])
    assert sympy.simplify(recon - (2 * x + y)) == 0
    fxx = repeated_diagonal(F, z, x)
    fxy = newton_first(F, z, x, y)
    mission = (fxx - fxy) / (x - y)
    newton_orient = (fxy - fxx) / (y - x)
    assert check_recurrence(KIND_FXXY, F, z, x, y, rhs=mission).verdict == ZERO
    assert check_recurrence(KIND_FXXY, F, z, x, y, rhs=newton_orient).verdict == ZERO


def test_Fxyy_recurrence_and_closed_form():
    F, z, x, y, _w = _cubic()
    ident = check_recurrence(KIND_FXYY, F, z, x, y)
    assert ident.verdict == ZERO, ident.to_dict()
    assert ident.formula == "F[x,y,y]=(F[x,y]-F[y,y])/(x-y)"
    assert ident.multiplicities == (1, 2)
    closed = check_recurrence("Fxyy", F, z, x, y, claimed=x + 2 * y)
    assert closed.verdict == ZERO, closed.to_dict()
    fxy = newton_first(F, z, x, y)
    fyy = repeated_diagonal(F, z, y)
    mission = (fxy - fyy) / (x - y)
    newton_orient = (fyy - fxy) / (y - x)
    assert check_recurrence(KIND_FXYY, F, z, x, y, rhs=mission).verdict == ZERO
    assert check_recurrence(KIND_FXYY, F, z, x, y, rhs=newton_orient).verdict == ZERO


def test_Fxxx_equals_second_deriv_over_2():
    F, z, x, _y, _w = _cubic()
    ident = check_recurrence(KIND_FXXX, F, z, x)
    assert ident.verdict == ZERO, ident.to_dict()
    assert ident.formula == "F[x,x,x]=F''(x)/2"
    assert ident.multiplicities == (3,)
    closed = check_recurrence("Fxxx", F, z, x, claimed=3 * x)
    assert closed.verdict == ZERO, closed.to_dict()
    fxx_over_2 = F.diff(z, 2).xreplace({z: x}) / sympy.factorial(2)
    assert check_recurrence(KIND_FXXX, F, z, x, claimed=fxx_over_2).verdict == ZERO
    assert sympy.expand(hermite_dd(F, z, [(x, 3)]) - 3 * x) == 0
    probe = hermite_dd(F, z, [(x, 3)]).xreplace({x: sympy.Integer(1)})
    assert probe == sympy.Integer(3)


def test_quadratic_identities():
    F, z, x, y = _quadratic()
    assert check_recurrence(KIND_FXX, F, z, x, claimed=2 * x).verdict == ZERO
    assert check_recurrence(KIND_FXXY, F, z, x, y, claimed=sympy.Integer(1)).verdict == ZERO
    assert check_recurrence(KIND_FXYY, F, z, x, y, claimed=sympy.Integer(1)).verdict == ZERO
    assert check_recurrence(KIND_FXXX, F, z, x, claimed=sympy.Integer(1)).verdict == ZERO


def test_newton_step_cubic_three_nodes():
    F, z, x, y, w = _cubic()
    ident = check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, y, w])
    assert ident.verdict == ZERO, ident.to_dict()
    assert ident.relation == REL_DD
    closed = check_recurrence(
        "dd_recurrence", F, z, nodes=[x, y, w], claimed=x + y + w,
    )
    assert closed.verdict == ZERO, closed.to_dict()
    two = check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, y])
    assert two.verdict == ZERO, two.to_dict()
    assert sympy.expand(newton_table(F, z, [x, y]) - newton_first(F, z, x, y)) == 0


def test_hermite_step_matches_named_kinds():
    F, z, x, y, _w = _cubic()
    xxy = check_recurrence(
        KIND_HERMITE_STEP, F, z, nodes=[(x, 2), (y, 1)], claimed=2 * x + y,
    )
    xyy = check_recurrence(
        "hermite_dd_recurrence", F, z, nodes=[(x, 1), (y, 2)], claimed=x + 2 * y,
    )
    xxx = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 3)], claimed=3 * x)
    xx = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 2)], claimed=3 * x**2)
    assert xxy.verdict == ZERO, xxy.to_dict()
    assert xyy.verdict == ZERO, xyy.to_dict()
    assert xxx.verdict == ZERO, xxx.to_dict()
    assert xx.verdict == ZERO, xx.to_dict()


def test_exp_and_log_probes():
    z, x, y = sympy.symbols("z x y")
    E = sympy.exp(z)
    assert check_recurrence(KIND_FXX, E, z, x, claimed=sympy.exp(x)).verdict == ZERO
    assert check_recurrence(KIND_FXXX, E, z, x, claimed=sympy.exp(x) / 2).verdict == ZERO
    assert check_recurrence(KIND_FXXY, E, z, x, y).verdict == ZERO
    L = sympy.log(z)
    two = sympy.Integer(2)
    assert check_recurrence(KIND_FXX, L, z, two, claimed=sympy.Rational(1, 2)).verdict == ZERO
    assert check_recurrence(KIND_FXXX, L, z, two, claimed=sympy.Rational(-1, 8)).verdict == ZERO


# --------------------------------------------------------------------------- #
# Fail closed: missing data / ill-posed → UNKNOWN, not ZERO
# --------------------------------------------------------------------------- #


def test_missing_F_is_unknown():
    _F, z, x, y, _w = _cubic()
    for r in (
        check_recurrence(KIND_FXX, None, z, x),
        check_recurrence(KIND_FXXY, None, z, x, y),
        check_recurrence(KIND_FXXX, None, z, x),
        check_recurrence(KIND_NEWTON_STEP, None, z, nodes=[x, y]),
    ):
        assert r.verdict == UNKNOWN
        assert r.note == "missing_F"
        assert r.verdict != ZERO


def test_missing_nodes_and_claimed_unknown():
    F, z, x, y, _w = _cubic()
    assert check_recurrence(KIND_FXXY, F, z, x).verdict == UNKNOWN
    assert check_recurrence(KIND_FXX, F, z).note == "missing_x"
    assert check_recurrence(KIND_NEWTON_STEP, F, z).verdict == UNKNOWN
    assert check_recurrence(KIND_HERMITE_STEP, F, z).verdict == UNKNOWN
    bare = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[x, y])
    assert bare.verdict == UNKNOWN
    assert bare.note == "missing_multiplicities"
    assert check_recurrence(KIND_FXX, F, z, x, claimed="not-an-expr").verdict == UNKNOWN
    assert check_recurrence("not_a_kind", F, z, x).verdict == UNKNOWN
    empty = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[])
    assert empty.verdict == UNKNOWN
    bad_m = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 0)])
    assert bad_m.verdict == UNKNOWN
    assert bad_m.verdict != ZERO


def test_mixed_hermite_nodes_unknown_not_guessed():
    F, z, x, y, _w = _cubic()
    r = check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 1), (y, 1), (x, 1)])
    assert r.verdict == UNKNOWN
    assert r.note == "hermite_ill_posed"
    assert r.verdict != ZERO


def test_newton_coincident_nodes_are_not_the_derivative():
    F, z, x, _y, _w = _cubic()
    r = check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, x], claimed=3 * x**2)
    _assert_not_zero(r, "newton_coincident_as_derivative")
    assert r.verdict == NONZERO


def test_fxxy_formula_at_coincident_nodes_is_not_zero():
    F, z, x, _y, _w = _cubic()
    r = check_recurrence(KIND_FXXY, F, z, x, x, claimed=3 * x)
    _assert_not_zero(r, "fxxy_substituted_x_eq_y")
    assert r.provenance.get("coincident_nodes") is True


# --------------------------------------------------------------------------- #
# Adversarial — must not false-ZERO
# --------------------------------------------------------------------------- #


def test_adversarial_wrong_sign():
    F, z, x, y, _w = _cubic()
    cases = [
        check_recurrence(KIND_FXX, F, z, x, claimed=-3 * x**2),
        check_recurrence(KIND_FXXY, F, z, x, y, claimed=-(2 * x + y)),
        check_recurrence(KIND_FXYY, F, z, x, y, claimed=-(x + 2 * y)),
        check_recurrence(KIND_FXXX, F, z, x, claimed=-3 * x),
        check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, y], claimed=-(x**2 + x * y + y**2)),
    ]
    for c, label in zip(cases, ("fxx", "fxxy", "fxyy", "fxxx", "newton")):
        _assert_not_zero(c, f"sign_{label}")
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_adversarial_wrong_factorial():
    F, z, x, _y, _w = _cubic()
    fxx = F.diff(z, 2).xreplace({z: x})
    for bad, label in (
        (fxx / 1, "xxx_div_1"),
        (fxx / 6, "xxx_div_3_fact"),
        (fxx / 3, "xxx_div_3"),
        (sympy.Integer(6), "xxx_unit_probe_wrong"),
        (fxx, "xxx_no_factorial"),
    ):
        c = check_recurrence(KIND_FXXX, F, z, x, claimed=bad)
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())
        rhs = check_recurrence(KIND_FXXX, F, z, x, rhs=bad)
        _assert_not_zero(rhs, f"rhs_{label}")
        assert rhs.verdict == NONZERO, (label, rhs.to_dict())
    true = check_recurrence(KIND_FXXX, F, z, x, claimed=fxx / 2)
    assert true.verdict == ZERO


def test_adversarial_wrong_derivative_order():
    F, z, x, _y, _w = _cubic()
    cases = [
        ("repeated_as_second_deriv", KIND_FXX, F.diff(z, 2).xreplace({z: x})),
        ("repeated_as_third_deriv", KIND_FXX, F.diff(z, 3).xreplace({z: x})),
        ("xxx_as_third_deriv", KIND_FXXX, F.diff(z, 3).xreplace({z: x})),
        ("xxx_as_second_deriv_no_factorial", KIND_FXXX, F.diff(z, 2).xreplace({z: x})),
        ("xxx_as_first_deriv", KIND_FXXX, F.diff(z).xreplace({z: x})),
        ("xxx_as_zeroth", KIND_FXXX, F.xreplace({z: x})),
    ]
    for label, kind, claimed in cases:
        c = check_recurrence(kind, F, z, x, claimed=claimed)
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())
    rhs_order = check_recurrence(
        KIND_FXXX, F, z, x, rhs=F.diff(z, 3).xreplace({z: x}) / 2,
    )
    _assert_not_zero(rhs_order, "xxx_rhs_third_deriv")
    assert rhs_order.verdict == NONZERO


def test_adversarial_wrong_multiplicity():
    F, z, x, y, _w = _cubic()
    r_xx_as_xy = check_recurrence(KIND_FXX, F, z, x, claimed=(x**3 - y**3) / (x - y))
    _assert_not_zero(r_xx_as_xy, "newton_member_as_repeated")
    assert r_xx_as_xy.verdict == NONZERO
    r_xxx_as_xx = check_recurrence(KIND_FXXX, F, z, x, claimed=3 * x**2)
    _assert_not_zero(r_xxx_as_xx, "Fxx_as_Fxxx")
    r_xx_as_xxx = check_recurrence(KIND_FXX, F, z, x, claimed=3 * x)
    _assert_not_zero(r_xx_as_xxx, "Fxxx_as_Fxx")
    r_xxx_as_xxy = check_recurrence(KIND_FXXX, F, z, x, claimed=2 * x + y)
    _assert_not_zero(r_xxx_as_xxy, "xxy_member_as_xxx")
    r_xxy_as_xy = check_recurrence(KIND_FXXY, F, z, x, y, claimed=x**2 + x * y + y**2)
    _assert_not_zero(r_xxy_as_xy, "xy_member_as_xxy")
    r_xx_as_fx = check_recurrence(KIND_FXX, F, z, x, claimed=x**3)
    _assert_not_zero(r_xx_as_fx, "Fxx_as_F_of_x")
    r_h = check_recurrence(
        KIND_HERMITE_STEP, F, z, nodes=[(x, 2)], claimed=3 * x,
    )
    _assert_not_zero(r_h, "hermite_xx_claimed_xxx")
    for c in (
        r_xx_as_xy, r_xxx_as_xx, r_xx_as_xxx, r_xxx_as_xxy,
        r_xxy_as_xy, r_xx_as_fx, r_h,
    ):
        assert c.verdict == NONZERO, c.to_dict()


def test_adversarial_wrong_orientation():
    F, z, x, y, _w = _cubic()
    # F[x,x,y]=2x+y vs F[x,y,y]=x+2y
    c1 = check_recurrence(KIND_FXYY, F, z, x, y, claimed=2 * x + y)
    c2 = check_recurrence(KIND_FXXY, F, z, x, y, claimed=x + 2 * y)
    c3 = check_recurrence(
        KIND_HERMITE_STEP, F, z, nodes=[(y, 2), (x, 1)], claimed=2 * x + y,
    )
    c4 = check_recurrence(
        KIND_HERMITE_STEP, F, z, nodes=[(y, 1), (x, 2)], claimed=x + 2 * y,
    )
    fxx = repeated_diagonal(F, z, x)
    fxy = newton_first(F, z, x, y)
    fyy = repeated_diagonal(F, z, y)
    # one sign flip only (numerator reversed, denom not)
    wrong_xxy = (fxy - fxx) / (x - y)
    wrong_xyy = (fyy - fxy) / (x - y)
    c5 = check_recurrence(KIND_FXXY, F, z, x, y, rhs=wrong_xxy)
    c6 = check_recurrence(KIND_FXYY, F, z, x, y, rhs=wrong_xyy)
    for c, label in (
        (c1, "xxy_member_on_xyy"),
        (c2, "xyy_member_on_xxy"),
        (c3, "blocks_yyx_vs_xxy"),
        (c4, "blocks_yxx_vs_xyy"),
        (c5, "xxy_formula_flipped_num"),
        (c6, "xyy_formula_flipped_num"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_adversarial_wrong_node_value():
    F, z, x, y, _w = _cubic()
    c1 = check_recurrence(KIND_FXX, F, z, x, claimed=3 * y**2)
    c2 = check_recurrence(KIND_FXX, F, z, y, claimed=3 * x**2)
    c3 = check_recurrence(KIND_FXXX, F, z, x, claimed=3 * y)
    c4 = check_recurrence(KIND_FXXY, F, z, x, y, claimed=2 * y + x)
    c5 = check_recurrence(KIND_FXYY, F, z, x, y, claimed=y + 2 * x)
    c6 = check_recurrence(
        KIND_HERMITE_STEP, F, z, nodes=[(y, 3)], claimed=3 * x,
    )
    for c, label in (
        (c1, "Fxx_at_y"),
        (c2, "Fyy_claimed_Fxx"),
        (c3, "Fxxx_at_y"),
        (c4, "xxy_swapped_closed_form"),
        (c5, "xyy_swapped_closed_form"),
        (c6, "yyy_claimed_xxx"),
    ):
        _assert_not_zero(c, label)
        assert c.verdict == NONZERO, (label, c.to_dict())


def test_false_zero_count_is_zero():
    F, z, x, y, w = _cubic()
    fxx = F.diff(z, 2).xreplace({z: x})
    fxy = newton_first(F, z, x, y)
    fxx_d = repeated_diagonal(F, z, x)
    attacks = [
        check_recurrence(KIND_FXX, F, z, x, claimed=-3 * x**2),
        check_recurrence(KIND_FXX, F, z, x, claimed=fxx),
        check_recurrence(KIND_FXX, F, z, x, claimed=(x**3 - y**3) / (x - y)),
        check_recurrence(KIND_FXX, F, z, x, claimed=3 * y**2),
        check_recurrence(KIND_FXX, F, z, y, claimed=3 * x**2),
        check_recurrence(KIND_FXXX, F, z, x, claimed=fxx),
        check_recurrence(KIND_FXXX, F, z, x, claimed=fxx / 6),
        check_recurrence(KIND_FXXX, F, z, x, claimed=F.diff(z, 3).xreplace({z: x})),
        check_recurrence(KIND_FXXX, F, z, x, claimed=3 * x**2),
        check_recurrence(KIND_FXXX, F, z, x, claimed=3 * y),
        check_recurrence(KIND_FXXY, F, z, x, y, claimed=-(2 * x + y)),
        check_recurrence(KIND_FXXY, F, z, x, y, claimed=x + 2 * y),
        check_recurrence(KIND_FXXY, F, z, x, y, claimed=2 * y + x),
        check_recurrence(KIND_FXYY, F, z, x, y, claimed=2 * x + y),
        check_recurrence(KIND_FXXY, F, z, x, y, rhs=(fxy - fxx_d) / (x - y)),
        check_recurrence(KIND_FXYY, F, z, x, y, rhs=(repeated_diagonal(F, z, y) - fxy) / (x - y)),
        check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 1), (y, 1)], claimed=2 * x + y),
        check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 3)], claimed=2 * x + y),
        check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(y, 2), (x, 1)], claimed=2 * x + y),
        check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[x, x, y], claimed=2 * x + y),
        check_recurrence(KIND_HERMITE_STEP, F, z, nodes=[(x, 1), (y, 1), (x, 1)]),
        check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, x], claimed=3 * x**2),
        check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, y, w], claimed=x + y - w),
        check_recurrence(KIND_FXXY, F, z, x, x, claimed=3 * x),
        check_recurrence(KIND_FXX, None, z, x, claimed=3 * x**2),
        check_recurrence("not_a_kind", F, z, x, claimed=3 * x**2),
        check_recurrence(KIND_FXXX, F, z, x, rhs=fxx / 1),
        check_recurrence(KIND_FXXX, F, z, x, rhs=F.diff(z, 1).xreplace({z: x}) / 2),
    ]
    false_zeros = [c for c in attacks if c.verdict == ZERO]
    assert false_zeros == [], [c.to_dict() for c in false_zeros]
    assert check_recurrence(KIND_FXX, F, z, x, claimed=3 * x**2).verdict == ZERO
    assert check_recurrence(KIND_FXXY, F, z, x, y, claimed=2 * x + y).verdict == ZERO
    assert check_recurrence(KIND_FXYY, F, z, x, y, claimed=x + 2 * y).verdict == ZERO
    assert check_recurrence(KIND_FXXX, F, z, x, claimed=3 * x).verdict == ZERO
    assert check_recurrence(KIND_NEWTON_STEP, F, z, nodes=[x, y, w], claimed=x + y + w).verdict == ZERO


def test_no_source_member_hardcode():
    src = inspect.getsource(check_mod)
    assert "G0001" not in src
    assert "G0007" not in src
    assert "G0012" not in src
    assert "representation_invention.guo" not in src
    assert "openai" not in src.lower()
    assert "hermite_dd" in src
    assert "newton_first" in src
    assert "repeated_diagonal" in src
    assert "newton_table" in src
    assert "from research.representation_invention.dd import" in src
