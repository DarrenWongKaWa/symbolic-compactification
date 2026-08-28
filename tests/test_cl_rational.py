"""Rational prefactor Laurent series. No together of a summed kernel."""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.rational import (  # noqa: E402
    convolve,
    expand_rational,
    pole_order,
)
from research.coefficient_laurent.rational import expand as expand_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "rational"


def _xy():
    return sympy.symbols("x y")


def _coeff_eq(got: sympy.Expr, expected: sympy.Expr) -> bool:
    return sympy.expand(got - expected) == 0


def test_public_api():
    assert callable(expand_rational)
    assert callable(pole_order)
    assert callable(convolve)
    assert expand_rational is expand_mod.expand_rational
    assert pole_order is expand_mod.pole_order
    assert convolve is expand_mod.convolve
    sig = inspect.signature(expand_rational)
    assert list(sig.parameters)[:4] == ["expr", "var", "point", "pmax"]
    sig_p = inspect.signature(pole_order)
    assert list(sig_p.parameters)[:3] == ["expr", "var", "point"]


def test_fourth_pole_y_to_x_is_t_minus_4():
    x, y = _xy()
    expr = 1 / (x - y) ** 4
    assert pole_order(expr, y, x) == -4
    series = expand_rational(expr, y, x, 2)
    assert set(series) == {-4}
    assert series[-4] == 1
    assert series[-4] == sympy.Integer(1)


def test_fourth_pole_x_to_y_is_t_minus_4():
    x, y = _xy()
    expr = 1 / (x - y) ** 4
    assert pole_order(expr, x, y) == -4
    series = expand_rational(expr, x, y, 0)
    assert series == {-4: sympy.Integer(1)}


def test_y_minus_x_fourth_pole():
    x, y = _xy()
    expr = 1 / (y - x) ** 4
    assert pole_order(expr, y, x) == -4
    assert expand_rational(expr, y, x, 0)[-4] == 1


def test_simple_pole_sign():
    x, y = _xy()
    series = expand_rational(1 / (x - y), y, x, 1)
    assert pole_order(1 / (x - y), y, x) == -1
    assert series[-1] == -1
    assert 0 not in series


def test_holomorphic_pole_order_is_zero():
    x, y = _xy()
    expr = 1 / (x + y)
    assert pole_order(expr, y, x) == 0
    series = expand_rational(expr, y, x, 2)
    assert set(series) == {0, 1, 2}
    assert _coeff_eq(series[0], 1 / (2 * x))
    assert _coeff_eq(series[1], -1 / (4 * x**2))
    assert _coeff_eq(series[2], 1 / (8 * x**3))


def test_zero_of_order_two_is_not_a_pole():
    x, y = _xy()
    expr = (y - x) ** 2
    assert pole_order(expr, y, x) == 0
    series = expand_rational(expr, y, x, 3)
    assert series == {2: sympy.Integer(1)}


def test_product_of_two_series_matches_convolve():
    x, y = _xy()
    left_expr = 1 / (y - x) ** 2
    right_expr = 1 + (y - x)
    pmax = 2
    left = expand_rational(left_expr, y, x, pmax)
    right = expand_rational(right_expr, y, x, pmax)
    got = convolve(left, right, pmax)
    expected = expand_rational(left_expr * right_expr, y, x, pmax)
    assert left == {-2: sympy.Integer(1)}
    assert set(right) == {0, 1}
    assert set(got) == {-2, -1}
    assert set(got) == set(expected)
    for power in got:
        assert _coeff_eq(got[power], expected[power])


def test_convolve_two_geometric_series():
    x, y = _xy()
    t = y - x
    left_expr = 1 / (1 + t)
    right_expr = 1 / (2 + t)
    pmax = 3
    left = expand_rational(left_expr, y, x, pmax)
    right = expand_rational(right_expr, y, x, pmax)
    got = convolve(left, right, pmax)
    expected = expand_rational(left_expr * right_expr, y, x, pmax)
    assert set(got) == set(expected)
    for power in expected:
        assert _coeff_eq(got[power], expected[power])


def test_pole_times_holomorphic_keeps_subleading():
    x, y = _xy()
    expr = 1 / ((x - y) ** 2 * (x + y))
    assert pole_order(expr, y, x) == -2
    series = expand_rational(expr, y, x, 0)
    assert set(series) == {-2, -1, 0}
    assert _coeff_eq(series[-2], 1 / (2 * x))
    assert _coeff_eq(series[-1], -1 / (4 * x**2))
    assert _coeff_eq(series[0], 1 / (8 * x**3))


def test_pmax_truncates():
    x, y = _xy()
    series = expand_rational(1 / (1 + (y - x)), y, x, 1)
    assert set(series) == {0, 1}
    assert series[0] == 1
    assert series[1] == -1


def test_pmax_below_pole_is_empty():
    x, y = _xy()
    assert expand_rational(1 / (x - y) ** 4, y, x, -5) == {}


def test_convolve_drops_cancelled_power():
    got = convolve({0: 1, 1: 1}, {0: 1, 1: -1}, pmax=1)
    assert set(got) == {0}
    assert got[0] == 1


def test_indexed_linear_fourth_pole():
    epsilon = sympy.Function("epsilon")
    m, n = sympy.symbols("m n")
    expr = 1 / (epsilon(m) - epsilon(n)) ** 4
    assert pole_order(expr, epsilon(m), epsilon(n)) == -4
    series = expand_rational(expr, epsilon(m), epsilon(n), 0)
    assert series == {-4: sympy.Integer(1)}


def test_add_cancels_opposite_poles():
    x, y = _xy()
    expr = 1 / (y - x) + 1 / (x - y)
    assert pole_order(expr, y, x) == 0
    assert expand_rational(expr, y, x, 2) == {}


def test_expand_never_calls_together_series_or_limit(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("together/series/limit on a rational prefactor is forbidden")

    monkeypatch.setattr(sympy, "together", _boom)
    monkeypatch.setattr(sympy, "series", _boom)
    monkeypatch.setattr(sympy, "limit", _boom)
    x, y = _xy()
    expr = 1 / (x - y) ** 4
    assert pole_order(expr, y, x) == -4
    series = expand_rational(expr, y, x, 0)
    assert series[-4] == 1
    mixed = expand_rational(1 / ((x - y) ** 2 * (x + y)), y, x, 0)
    assert -2 in mixed
    conv = convolve({-2: 1}, {0: 1, 1: y}, pmax=0)
    assert conv[-2] == 1
    assert conv[-1] == y


def test_source_ban():
    files = sorted(p for p in PKG.rglob("*.py") if p.is_file())
    assert files
    banned_substrings = (
        "sympy.together",
        ".together(",
        "sympy.series",
        ".series(",
        "sympy.limit",
        ".limit(",
        "sympy.simplify",
        ".simplify(",
        "Phi_Gamma",
        "guo_map",
        "L4",
        "FAMILY_ZERO",
    )
    for path in files:
        src = path.read_text(encoding="utf-8")
        for tok in banned_substrings:
            assert tok not in src, (path.name, tok)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id not in {"together", "series", "limit", "simplify"}
                elif isinstance(func, ast.Attribute):
                    assert func.attr not in {"together", "series", "limit", "simplify"}
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name not in {"together", "series", "limit", "simplify"}
