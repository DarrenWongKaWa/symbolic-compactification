"""Generic Newton/Hermite divided differences. No live API. No source gold."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.constructor import _equal
from research.representation_invention.dd import (
    ConfluenceLimitError,
    HermiteDDError,
    hermite_dd,
    limit_generic_to_degenerate,
    newton_first,
    newton_table,
    repeated_diagonal,
)
from research.representation_invention.dd.confluence import limit_generic_to_degenerate as lim_mod
from research.representation_invention.dd.hermite import hermite_dd as hermite_mod
from research.representation_invention.dd.newton import newton_first as newton_mod


def _cubic():
    z, x, y, w = sympy.symbols("z x y w")
    return z**3, z, x, y, w


def test_public_api_importable():
    assert newton_first is newton_mod
    assert hermite_dd is hermite_mod
    assert limit_generic_to_degenerate is lim_mod


def test_newton_first_cubic_closed_form():
    F, z, x, y, _ = _cubic()
    got = newton_first(F, z, x, y)
    assert _equal(got, x**2 + x * y + y**2)


def test_newton_table_matches_definition_and_higher_cubic():
    F, z, x, y, w = _cubic()
    assert _equal(newton_table(F, z, [x]), x**3)
    assert _equal(newton_table(F, z, [x, y]), newton_first(F, z, x, y))
    assert _equal(newton_table(F, z, [x, y, w]), x + y + w)


def test_hermite_diagonal_cubic_Fxx_and_Fxxx():
    F, z, x, _, _ = _cubic()
    fxx = hermite_dd(F, z, [(x, 2)])
    fxxx = hermite_dd(F, z, [(x, 3)])
    assert _equal(fxx, 3 * x**2)
    assert _equal(fxx, repeated_diagonal(F, z, x))
    assert _equal(fxx - F.diff(z).xreplace({z: x}), 0)
    assert _equal(fxxx, F.diff(z, 2).xreplace({z: x}) / 2)
    assert _equal(fxxx, 3 * x)
    # unit probe of F[x,x,x] for z**3 is 3
    assert _equal(fxxx.xreplace({x: sympy.Integer(1)}), sympy.Integer(3))


def test_hermite_F_xxy_and_F_xyy_cubic():
    F, z, x, y, _ = _cubic()
    xxy = hermite_dd(F, z, [(x, 2), (y, 1)])
    xyy = hermite_dd(F, z, [(x, 1), (y, 2)])
    xy = hermite_dd(F, z, [(x, 1), (y, 1)])
    assert _equal(xy, newton_first(F, z, x, y))
    assert _equal(xxy, 2 * x + y)
    assert _equal(xyy, x + 2 * y)
    # recurrence identity: F[x,x,y] = (F[x,y] - F[x,x]) / (y - x)
    assert _equal(xxy, (newton_first(F, z, x, y) - repeated_diagonal(F, z, x)) / (y - x))


def test_exp_diagonal_identity_and_numeric_probe():
    z, x, y = sympy.symbols("z x y")
    F = sympy.exp(z)
    assert _equal(repeated_diagonal(F, z, x), sympy.exp(x))
    assert _equal(hermite_dd(F, z, [(x, 2)]), sympy.exp(x))
    assert _equal(hermite_dd(F, z, [(x, 3)]), sympy.exp(x) / 2)
    probe = newton_first(F, z, sympy.Integer(0), sympy.Integer(1))
    # definition: (e^0 - e^1)/(0-1) = e-1
    assert _equal(probe, sympy.exp(1) - 1)
    lim = limit_generic_to_degenerate(newton_first(F, z, x, y), y, x)
    assert _equal(lim, sympy.exp(x))


def test_log_numeric_probe():
    z = sympy.symbols("z")
    F = sympy.log(z)
    two = sympy.Integer(2)
    assert _equal(repeated_diagonal(F, z, two), sympy.Rational(1, 2))
    assert _equal(hermite_dd(F, z, [(two, 2)]), sympy.Rational(1, 2))
    assert _equal(hermite_dd(F, z, [(two, 3)]), sympy.Rational(-1, 8))


def test_negative_wrong_sign():
    F, z, x, y, _ = _cubic()
    got = newton_first(F, z, x, y)
    wrong = -(F.xreplace({z: x}) - F.xreplace({z: y})) / (x - y)
    assert not _equal(got, wrong)


def test_negative_wrong_denominator():
    F, z, x, y, _ = _cubic()
    got = newton_first(F, z, x, y)
    wrong = (F.xreplace({z: x}) - F.xreplace({z: y})) / (x + y)
    assert not _equal(got, wrong)


def test_negative_wrong_multiplicity_is_not_derivative():
    F, z, x, _, _ = _cubic()
    naive = newton_first(F, z, x, x)
    table = newton_table(F, z, [x, x])
    diag = repeated_diagonal(F, z, x)
    assert naive.has(sympy.nan) or naive == sympy.nan
    assert table.has(sympy.nan) or table == sympy.nan
    assert not _equal(naive, diag)
    assert not _equal(table, 3 * x**2)
    assert not _equal(naive, 3 * x**2)


def test_negative_wrong_derivative_order():
    F, z, x, _, _ = _cubic()
    fxx = hermite_dd(F, z, [(x, 2)])
    fxxx = hermite_dd(F, z, [(x, 3)])
    assert not _equal(fxx, F.diff(z, 2).xreplace({z: x}))
    assert not _equal(fxxx, F.diff(z, 2).xreplace({z: x}))
    assert not _equal(fxxx, F.diff(z, 3).xreplace({z: x}))
    assert not _equal(fxxx, sympy.Integer(6))


def test_confluence_generic_first_dd_to_diagonal():
    F, z, x, y, _ = _cubic()
    generic = newton_first(F, z, x, y)
    lim = limit_generic_to_degenerate(generic, y, x)
    assert _equal(lim, repeated_diagonal(F, z, x))
    assert _equal(lim, hermite_dd(F, z, [(x, 2)]))


def test_confluence_F_xxy_to_F_xxx():
    F, z, x, y, _ = _cubic()
    generic = hermite_dd(F, z, [(x, 2), (y, 1)])
    lim = limit_generic_to_degenerate(generic, y, x)
    assert _equal(lim, hermite_dd(F, z, [(x, 3)]))
    assert _equal(lim, 3 * x)


def test_confluence_limit_failure_is_typed_error():
    z = sympy.symbols("z")
    with pytest.raises(ConfluenceLimitError):
        limit_generic_to_degenerate(z, z, object())


def test_hermite_mixed_equal_endpoints_do_not_guess():
    F, z, x, y, _ = _cubic()
    with pytest.raises(HermiteDDError):
        hermite_dd(F, z, [(x, 1), (y, 1), (x, 1)])
