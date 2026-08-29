"""Typed O(t^k)/o(t^k) algebra. Vanishing remainder is not hop ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.order_algebra import (  # noqa: E402
    KEEP_THROUGH,
    UNKNOWN,
    AnalyticExpansion,
    ExactPower,
    ExactZero,
    O,
    Order,
    add,
    compose,
    compose_remainder,
    div,
    exact_power,
    is_unknown,
    mul,
    o,
    prod_orders,
    remainder_times_prefactor,
    sufficient_expansion_order,
    sum_orders,
    taylor_expansion,
    times_prefactor,
    vanishes_through_constant,
    zero,
)
import research.remainder_certification.order_algebra as pkg  # noqa: E402
import research.remainder_certification.order_algebra.order as order_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "order_algebra"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "PhiGamma")
HOP_ZERO = "ZERO"


def test_public_api():
    assert pkg.O is order_mod.O
    assert pkg.add is order_mod.add
    assert pkg.mul is order_mod.mul
    assert pkg.div is order_mod.div
    assert pkg.sum_orders is order_mod.sum_orders
    assert pkg.compose is order_mod.compose
    assert KEEP_THROUGH == 0
    assert UNKNOWN == "UNKNOWN"
    assert UNKNOWN != HOP_ZERO
    sig = inspect.signature(remainder_times_prefactor)
    assert "N" in sig.parameters
    assert "m" in sig.parameters


def test_o_t2_plus_o_t3_is_o_t2():
    got = add(O(2), O(3))
    assert got == O(2)
    assert got == Order("O", 2, "t")
    assert str(got) == "O(t^2)"


def test_t_inv3_times_o_t4_is_o_t():
    got = mul(exact_power(-3), O(4))
    assert got == O(1)
    assert str(got) == "O(t)"
    assert times_prefactor(O(4), 3) == O(1)
    assert remainder_times_prefactor(3, 3) == O(1)
    assert remainder_times_prefactor(N=3, m=3) == O(1)


def test_t_inv3_times_o_t3_is_o_1_does_not_vanish():
    got = mul(exact_power(-3), O(3))
    assert got == O(0)
    assert str(got) == "O(1)"
    assert vanishes_through_constant(got) is False
    assert vanishes_through_constant(got) != HOP_ZERO
    assert sufficient_expansion_order(2, 3) is False


def test_insufficient_n_relative_to_pole_order():
    # N = m-1 leaves O(t^0) = O(1), not certified vanishing.
    rem = remainder_times_prefactor(N=2, m=3)
    assert rem == O(0)
    assert vanishes_through_constant(rem) is False
    assert sufficient_expansion_order(2, 3) is False
    # N = m-2 leaves a polar remainder O(t^{-1}).
    polar = remainder_times_prefactor(N=1, m=3)
    assert polar == O(-1)
    assert str(polar) == "O(t^{-1})"
    assert vanishes_through_constant(polar) is False
    assert sufficient_expansion_order(1, 3) is False
    # Threshold: N >= m  <=>  N+1-m >= 1.
    assert remainder_times_prefactor(N=3, m=3) == O(1)
    assert sufficient_expansion_order(3, 3) is True
    assert vanishes_through_constant(O(1)) is True
    assert remainder_times_prefactor(4, 3) == O(2)
    assert sufficient_expansion_order(4, 3) is True


def test_no_heuristic_truncation_same_order_stays_big_o():
    assert add(O(2), O(2)) == O(2)
    assert add(O(2), O(2)) != o(2)
    both_exact = add(exact_power(2), exact_power(2))
    assert both_exact == O(2)
    assert not isinstance(both_exact, ExactPower)


def test_little_o_and_mixed_addition():
    assert add(o(2), o(3)) == o(2)
    assert add(O(2), o(2)) == O(2)
    assert add(O(2), o(3)) == O(2)
    assert add(o(2), O(3)) == o(2)
    assert add(exact_power(2), o(2)) == exact_power(2)
    assert add(exact_power(2), O(2)) == O(2)


def test_finite_sums():
    assert sum_orders(O(5), O(2), O(4)) == O(2)
    assert sum_orders(o(3), o(1), o(4)) == o(1)
    assert sum_orders() == ExactZero()
    assert add(zero(), O(4)) == O(4)
    assert add(O(4), zero()) == O(4)


def test_multiplication():
    assert mul(O(2), O(3)) == O(5)
    assert mul(o(2), O(3)) == o(5)
    assert mul(o(2), o(3)) == o(5)
    assert mul(exact_power(-3), o(4)) == o(1)
    assert mul(zero(), O(5)) == zero()
    assert prod_orders(O(1), O(2), O(3)) == O(6)
    assert mul(exact_power(2), exact_power(-5)) == exact_power(-3)


def test_division_requires_certified_nonzero_leading():
    assert div(O(4), exact_power(3)) == O(1)
    assert div(o(4), exact_power(3)) == o(1)
    assert div(exact_power(5), exact_power(3)) == exact_power(2)
    assert div(O(4), exact_power(3, leading_certified_nonzero=False)) == UNKNOWN
    assert div(O(4), O(3)) == UNKNOWN
    assert div(O(4), o(3)) == UNKNOWN
    assert div(O(4), zero()) == UNKNOWN
    assert is_unknown(div(O(4), O(3)))
    assert div(O(2), exact_power(0)) == O(2)


def test_compose_analytic_expansion_with_certified_linear_inner():
    expn = taylor_expansion(3)
    inner = exact_power(1)
    rem = compose_remainder(expn, inner)
    assert rem == O(4)
    scaled = times_prefactor(rem, 3)
    assert scaled == O(1)
    assert vanishes_through_constant(scaled) is True
    short = taylor_expansion(2)
    rem_short = compose_remainder(short, inner)
    assert rem_short == O(3)
    assert times_prefactor(rem_short, 3) == O(0)
    assert vanishes_through_constant(times_prefactor(rem_short, 3)) is False


def test_compose_requires_inner_to_zero_and_exact_for_negative_powers():
    expn = taylor_expansion(2)
    assert compose_remainder(expn, O(0)) == UNKNOWN
    assert compose_remainder(expn, exact_power(0)) == UNKNOWN
    assert compose_remainder(expn, O(1)) == O(3)
    assert compose_remainder(expn, o(1)) == o(3)
    neg = AnalyticExpansion(remainder=O(-1, variable="w"), variable="w")
    assert compose_remainder(neg, O(1)) == UNKNOWN
    assert compose_remainder(neg, exact_power(1)) == O(-1)
    assert compose_remainder(neg, exact_power(2)) == O(-2)


def test_compose_keeps_uncertified_present_terms():
    expn = AnalyticExpansion(
        remainder=O(3, variable="w"),
        terms=((1, False),),
        variable="w",
    )
    got = compose(expn, exact_power(1))
    assert got == O(1)
    certified = AnalyticExpansion(
        remainder=O(3, variable="w"),
        terms=((1, True),),
        variable="w",
    )
    got_ex = compose(certified, exact_power(1))
    assert got_ex == exact_power(1)


def test_vanishes_through_constant_kinds():
    assert vanishes_through_constant(O(1)) is True
    assert vanishes_through_constant(O(0)) is False
    assert vanishes_through_constant(O(-2)) is False
    assert vanishes_through_constant(o(0)) is True
    assert vanishes_through_constant(o(-1)) is False
    assert vanishes_through_constant(zero()) is True
    assert vanishes_through_constant(exact_power(2)) is True
    assert vanishes_through_constant(exact_power(0)) is False
    assert vanishes_through_constant(UNKNOWN) == UNKNOWN
    assert vanishes_through_constant(O(1)) is not HOP_ZERO


def test_fail_closed_unknown_and_variable_mismatch():
    assert add("nope", O(1)) == UNKNOWN
    assert mul(O(1), None) == UNKNOWN
    assert add(O(1, "t"), O(2, "s")) == UNKNOWN
    assert mul(O(1, "t"), exact_power(2, variable="s")) == UNKNOWN
    assert remainder_times_prefactor("N", 3) == UNKNOWN
    assert remainder_times_prefactor(True, 3) == UNKNOWN
    assert sufficient_expansion_order(3, None) == UNKNOWN


def test_vanishing_is_not_hop_zero():
    rem = remainder_times_prefactor(3, 3)
    assert rem == O(1)
    assert vanishes_through_constant(rem) is True
    assert vanishes_through_constant(rem) != HOP_ZERO
    assert UNKNOWN != HOP_ZERO
    assert sufficient_expansion_order(3, 3) is True
    assert sufficient_expansion_order(3, 3) != HOP_ZERO


def test_documents_prefactor_rule():
    readme = (PKG / "README.md").read_text(encoding="utf-8")
    doc = (order_mod.__doc__ or "")
    blob = readme + "\n" + doc
    for tok in (
        "t^{-m}",
        "N+1-m",
        "UNKNOWN",
        "t → 0",
        "hop ZERO",
        "leading",
    ):
        assert tok in blob, tok
    assert "O(t^2) + O(t^3)" in readme or "O(t^2)+O(t^3)" in readme.replace(" ", "")


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
