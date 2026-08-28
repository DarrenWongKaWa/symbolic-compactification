"""Exact spectator-factor split. False decomposition acceptance = 0."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.factor import (  # noqa: E402
    split_additive,
    split_multiplicative,
)
from research.scalable_verification.factor.split import (  # noqa: E402
    split_additive as split_add_mod,
    split_multiplicative as split_mul_mod,
)

KEYS = {"S", "A_local", "B_local", "certified", "note"}
x, y, z, u, v, t = sympy.symbols("x y z u v t")


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.cancel(a - b) == 0
    except Exception:
        return False


def _assert_shape(out: dict) -> None:
    assert set(out) == KEYS
    assert isinstance(out["certified"], bool)
    assert isinstance(out["note"], str)
    assert out["note"]
    assert isinstance(out["S"], sympy.Expr)
    assert isinstance(out["A_local"], sympy.Expr)
    assert isinstance(out["B_local"], sympy.Expr)


def _assert_certified_mul(A: sympy.Expr, B: sympy.Expr) -> dict:
    out = split_multiplicative(A, B)
    _assert_shape(out)
    assert out["certified"] is True, out
    assert _eq(out["S"] * out["A_local"], A)
    assert _eq(out["S"] * out["B_local"], B)
    n_s, d_s = sympy.fraction(sympy.together(out["S"]))
    n_a, d_a = sympy.fraction(sympy.together(A))
    n_b, d_b = sympy.fraction(sympy.together(B))
    assert sympy.fraction(sympy.cancel(n_a / n_s))[1] in (1, sympy.Integer(1), -1, sympy.Integer(-1))
    assert sympy.fraction(sympy.cancel(n_b / n_s))[1] in (1, sympy.Integer(1), -1, sympy.Integer(-1))
    assert sympy.fraction(sympy.cancel(d_a / d_s))[1] in (1, sympy.Integer(1), -1, sympy.Integer(-1))
    assert sympy.fraction(sympy.cancel(d_b / d_s))[1] in (1, sympy.Integer(1), -1, sympy.Integer(-1))
    return out


def _assert_certified_add(A: sympy.Expr, B: sympy.Expr) -> dict:
    out = split_additive(A, B)
    _assert_shape(out)
    assert out["certified"] is True, out
    assert _eq(out["S"] + out["A_local"], A)
    assert _eq(out["S"] + out["B_local"], B)
    assert out["S"] != 0
    return out


def test_public_api_importable():
    assert split_multiplicative is split_mul_mod
    assert split_additive is split_add_mod


# --------------------------------------------------------------------------- #
# Multiplicative positives
# --------------------------------------------------------------------------- #


def test_mul_shared_linear_factor():
    A = (x + 1) * y
    B = (x + 1) * z
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], x + 1)
    assert _eq(out["A_local"], y)
    assert _eq(out["B_local"], z)


def test_mul_shared_power_takes_min_exponent():
    A = (x + 1) ** 3 * y
    B = (x + 1) ** 2 * z
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], (x + 1) ** 2)
    assert _eq(out["A_local"], (x + 1) * y)
    assert _eq(out["B_local"], z)


def test_mul_unfactored_polynomial_gcd():
    A = (x ** 2 - 1) * y
    B = (x - 1) * z
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], x - 1)
    assert not _eq(out["S"], x ** 2 - 1)


def test_mul_numeric_content():
    out = _assert_certified_mul(sympy.Integer(6) * x, sympy.Integer(9) * x)
    assert _eq(out["S"], 3 * x)
    assert _eq(out["A_local"], sympy.Integer(2))
    assert _eq(out["B_local"], sympy.Integer(3))


def test_mul_shared_denominator():
    A = y / (t - 1)
    B = z / (t - 1)
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], 1 / (t - 1))
    assert _eq(out["A_local"], y)
    assert _eq(out["B_local"], z)


def test_mul_shared_pole_uses_min_order_not_invented_higher_pole():
    A = y / (t - 1) ** 2
    B = z / (t - 1)
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], 1 / (t - 1))
    assert not _eq(out["S"], 1 / (t - 1) ** 2)


def test_mul_shared_partial_pole_and_not_the_mismatch():
    A = 1 / ((t - 1) * (t + 1))
    B = 1 / ((t - 1) * (t + 2))
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], 1 / (t - 1))
    assert sympy.fraction(sympy.together(out["S"]))[1] != (t + 1) * (t - 1)


def test_mul_shared_numerator_not_mismatched_poles():
    A = (x + 1) / (t - 1)
    B = (x + 1) / (t + 2)
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], x + 1)
    n_s, d_s = sympy.fraction(sympy.together(out["S"]))
    assert d_s in (1, sympy.Integer(1))


def test_mul_function_kernel():
    A = sympy.sin(x) * y
    B = sympy.sin(x) * z
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], sympy.sin(x))


def test_mul_identical_expressions():
    A = (x + y) * z
    out = _assert_certified_mul(A, A)
    assert _eq(out["S"], A)
    assert _eq(out["A_local"], sympy.Integer(1))
    assert _eq(out["B_local"], sympy.Integer(1))


# --------------------------------------------------------------------------- #
# Multiplicative negatives — must not certify a false spectator
# --------------------------------------------------------------------------- #


def test_mul_wrong_sign_near_factor_not_certified():
    A = x + 1
    B = x - 1
    out = split_multiplicative(A, B)
    _assert_shape(out)
    assert out["certified"] is False
    assert out["S"] == 1


def test_mul_wrong_sign_near_factor_does_not_enter_S_when_other_gcd_exists():
    A = (x + 1) * y
    B = (x - 1) * y
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], y)
    assert not _eq(out["S"], x + 1)
    assert not _eq(out["S"], x - 1)


def test_mul_factor_missing_from_one_side_not_certified():
    out = split_multiplicative(x * y, z)
    _assert_shape(out)
    assert out["certified"] is False


def test_mul_factor_missing_from_one_side_is_not_in_S():
    A = x * y * z
    B = x * y
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], x * y)
    assert sympy.gcd(out["S"], z) == 1
    assert not _eq(out["S"], A)


def test_mul_coefficient_mismatch_coprime_not_certified():
    A = 2 * (x + 1)
    B = 3 * (x - 1)
    out = split_multiplicative(A, B)
    _assert_shape(out)
    assert out["certified"] is False


def test_mul_coefficient_mismatch_does_not_overclaim():
    A = 2 * x * y
    B = 3 * x * z
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], x)
    assert not _eq(out["S"], 2 * x)
    assert not _eq(out["S"], 3 * x)


def test_mul_pole_mismatch_not_certified():
    A = 1 / (x - 1)
    B = 1 / (x + 1)
    out = split_multiplicative(A, B)
    _assert_shape(out)
    assert out["certified"] is False
    assert out["S"] == 1


def test_mul_pole_mismatch_does_not_invent_common_den():
    A = y / (x - 1)
    B = y / (x + 1)
    out = _assert_certified_mul(A, B)
    assert _eq(out["S"], y)
    _n, d = sympy.fraction(sympy.together(out["S"]))
    assert d in (1, sympy.Integer(1))


def test_mul_units_are_not_certified():
    out = split_multiplicative(x + 1, y + 1)
    _assert_shape(out)
    assert out["certified"] is False


def test_mul_zero_pair_not_certified():
    out = split_multiplicative(sympy.Integer(0), sympy.Integer(0))
    _assert_shape(out)
    assert out["certified"] is False


def test_mul_bad_input_not_certified():
    out = split_multiplicative("not-an-expr", x)
    _assert_shape(out)
    assert out["certified"] is False


# --------------------------------------------------------------------------- #
# Additive positives
# --------------------------------------------------------------------------- #


def test_add_shared_term():
    A = x + y
    B = x + z
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], x)
    assert _eq(out["A_local"], y)
    assert _eq(out["B_local"], z)


def test_add_min_coefficient_of_like_terms():
    A = 5 * x + y
    B = 3 * x + y
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], 3 * x + y)
    assert _eq(out["A_local"], 2 * x)
    assert _eq(out["B_local"], sympy.Integer(0))


def test_add_shared_constant():
    A = x + 3
    B = y + 3
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], sympy.Integer(3))


def test_add_shared_rational_term():
    A = 1 / (t - 1) + y
    B = 1 / (t - 1) + z
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], 1 / (t - 1))


def test_add_identical_expressions():
    A = x + 2 * y + z
    out = _assert_certified_add(A, A)
    assert _eq(out["S"], A)
    assert _eq(out["A_local"], sympy.Integer(0))
    assert _eq(out["B_local"], sympy.Integer(0))


# --------------------------------------------------------------------------- #
# Additive negatives
# --------------------------------------------------------------------------- #


def test_add_wrong_sign_not_certified_as_common():
    A = x
    B = -x
    out = split_additive(A, B)
    _assert_shape(out)
    assert out["certified"] is False
    assert out["S"] == 0


def test_add_wrong_sign_term_omitted_from_S():
    A = x + y
    B = -x + y
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], y)
    assert not _eq(out["S"], x)


def test_add_wrong_sign_near_offset_omitted_from_S():
    A = y + 1
    B = y - 1
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], y)
    assert not _eq(out["S"], sympy.Integer(1))


def test_add_factor_missing_from_one_side_not_in_S():
    A = x + y + z
    B = x + y
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], x + y)
    assert not _eq(out["S"], x + y + z)


def test_add_disjoint_not_certified():
    out = split_additive(x, y)
    _assert_shape(out)
    assert out["certified"] is False


def test_add_coefficient_mismatch_does_not_overclaim():
    A = 2 * x + y
    B = 3 * x + y
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], 2 * x + y)
    assert not _eq(out["S"], 3 * x + y)


def test_add_coefficient_mismatch_coprime_not_certified():
    A = 2 * x
    B = 3 * y
    out = split_additive(A, B)
    _assert_shape(out)
    assert out["certified"] is False


def test_add_pole_mismatch_not_treated_as_common():
    A = 1 / (x - 1) + y
    B = 1 / (x + 1) + y
    out = _assert_certified_add(A, B)
    assert _eq(out["S"], y)
    assert not _eq(out["S"], 1 / (x - 1))
    assert not _eq(out["S"], 1 / (x + 1))


def test_add_pole_only_mismatch_not_certified():
    A = 1 / (x - 1)
    B = 1 / (x + 1)
    out = split_additive(A, B)
    _assert_shape(out)
    assert out["certified"] is False


def test_add_bad_input_not_certified():
    out = split_additive(object(), x)
    _assert_shape(out)
    assert out["certified"] is False


# --------------------------------------------------------------------------- #
# False-decomposition invariant: certified ⇒ reconstruction, else no claim
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "A,B",
    [
        ((x + 1) * y, (x + 1) * z),
        ((x + 1), (x - 1)),
        (x * y, z),
        (2 * (x + 1), 3 * (x - 1)),
        (1 / (x - 1), 1 / (x + 1)),
        (2 * x * y, 3 * x * z),
        ((x ** 2 - 1) * y, (x - 1) * z),
        (y / (t - 1), z / (t + 1)),
        (1 / ((t - 1) * (t + 1)), 1 / ((t - 1) * (t + 2))),
        (sympy.Integer(0), x),
    ],
)
def test_mul_certified_iff_exact_reconstruction(A, B):
    out = split_multiplicative(A, B)
    _assert_shape(out)
    if out["certified"]:
        assert _eq(out["S"] * out["A_local"], A)
        assert _eq(out["S"] * out["B_local"], B)
        assert out["S"] not in (1, -1, sympy.Integer(1), sympy.Integer(-1))
        assert out["S"] != 0
    else:
        assert out["S"] == 1
        assert out["A_local"] == A
        assert out["B_local"] == B


@pytest.mark.parametrize(
    "A,B",
    [
        (x + y, x + z),
        (x, -x),
        (2 * x, 3 * y),
        (5 * x + y, 3 * x + y),
        (1 / (x - 1) + y, 1 / (x + 1) + y),
        (1 / (x - 1), 1 / (x + 1)),
        (x + y + z, x + y),
        (2 * x, 3 * x),
    ],
)
def test_add_certified_iff_exact_reconstruction(A, B):
    out = split_additive(A, B)
    _assert_shape(out)
    if out["certified"]:
        assert _eq(out["S"] + out["A_local"], A)
        assert _eq(out["S"] + out["B_local"], B)
        assert out["S"] != 0
    else:
        assert out["S"] == 0
        assert out["A_local"] == A
        assert out["B_local"] == B
