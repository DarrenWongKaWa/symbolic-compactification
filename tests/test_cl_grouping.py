"""Algebraic grouping of Laurent coefficient terms. No hop verdict."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.grouping import (  # noqa: E402
    GroupKey,
    group_terms,
    sum_groups,
)
from research.coefficient_laurent.grouping import group as group_mod  # noqa: E402

GROUPING_DIR = ROOT / "research" / "coefficient_laurent" / "grouping"
x, y, z, w = sympy.symbols("x y z w")


def _pg(order: int, arg: sympy.Expr = z) -> sympy.Expr:
    return sympy.polygamma(order, arg)


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.expand(a - b) == 0
    except Exception:
        return False


def test_public_api_importable():
    assert group_terms is group_mod.group_terms
    assert sum_groups is group_mod.sum_groups
    assert GroupKey is group_mod.GroupKey


def test_two_terms_same_polygamma_combine():
    d = x - y
    t = _pg(1) / d
    expr = sympy.Add(t, 2 * t, evaluate=False)
    groups = group_terms(expr)
    assert len(groups) == 1
    terms = next(iter(groups.values()))
    assert len(terms) == 2
    summed = sum_groups(groups)
    assert len(summed) == 1
    combined = next(iter(summed.values()))
    assert _eq(combined, 3 * t)

    # Distinct additive args that SymPy will not auto-collect.
    expr2 = x * t + y * t
    groups2 = group_terms(expr2)
    assert len(groups2) == 1
    key = next(iter(groups2))
    assert key.polygamma_order == 1
    assert key.argument == z
    assert _eq(next(iter(sum_groups(groups2).values())), (x + y) * t)


def test_different_orders_stay_split():
    d = x - y
    expr = _pg(1) / d + _pg(2) / d
    groups = group_terms(expr)
    assert len(groups) == 2
    orders = {key.polygamma_order for key in groups}
    assert orders == {1, 2}
    summed = sum_groups(groups)
    assert len(summed) == 2
    by_order = {key.polygamma_order: val for key, val in summed.items()}
    assert _eq(by_order[1], _pg(1) / d)
    assert _eq(by_order[2], _pg(2) / d)

    # Unsimplified (ψ_1 + ψ_2)/d is one Mul; orders must still stay split.
    bundled = (_pg(1) + _pg(2)) / d
    grouped_bundled = group_terms(bundled)
    assert len(grouped_bundled) == 2
    assert {key.polygamma_order for key in grouped_bundled} == {1, 2}


def test_different_arguments_stay_split():
    d = x - y
    expr = _pg(1, z) / d + _pg(1, w) / d
    groups = group_terms(expr)
    assert len(groups) == 2
    args = {key.argument for key in groups}
    assert args == {z, w}


def test_different_denominator_signatures_stay_split():
    expr = _pg(1) / (x - y) + _pg(1) / (x - w)
    groups = group_terms(expr)
    assert len(groups) == 2
    sigs = {key.denom_signature for key in groups}
    assert len(sigs) == 2


def test_sign_and_content_share_denominator_signature():
    a = _pg(1) / (x - y)
    b = 2 * _pg(1) / (y - x)
    c = _pg(1) / (8 * x - 8 * y)
    groups = group_terms(a + b + c)
    assert len(groups) == 1
    key = next(iter(groups))
    assert key.polygamma_order == 1
    assert key.argument == z


def test_sum_groups_does_not_mix_split_orders():
    d = x - y
    expr = x * _pg(1) / d + y * _pg(1) / d + _pg(3) / d
    grouped = group_terms(expr)
    assert len(grouped) == 2
    summed = sum_groups(grouped)
    rebuilt = sympy.Add(*summed.values())
    assert _eq(rebuilt, expr)


def test_sequence_input_same_as_add():
    t1 = x * _pg(1) / (x - y)
    t2 = y * _pg(1) / (x - y)
    from_seq = group_terms([t1, t2])
    from_add = group_terms(t1 + t2)
    assert list(from_seq) == list(from_add)
    assert len(from_seq) == 1


def test_rational_terms_group_by_denominator_only():
    expr = x / (x - y) + z / (x - y) + w / (x - z)
    groups = group_terms(expr)
    assert len(groups) == 2
    assert all(key.polygamma_order is None for key in groups)


def test_pref_times_add_distributes_then_groups():
    pref = sympy.symbols("beta")
    d = x - y
    inner = x * _pg(1) / d + y * _pg(1) / d + _pg(2) / d
    groups = group_terms(pref * inner)
    assert len(groups) == 2
    assert {key.polygamma_order for key in groups} == {1, 2}
    rebuilt = sympy.Add(*sum_groups(groups).values())
    assert _eq(rebuilt, pref * inner)


def test_reconstruction_of_unevaluated_sum():
    t = _pg(1) / (x - y)
    expr = sympy.Add(t, 2 * t, evaluate=False)
    rebuilt = sympy.Add(*sum_groups(group_terms(expr)).values())
    assert _eq(rebuilt, 3 * t)


def test_source_ban():
    text = ""
    for path in sorted(GROUPING_DIR.glob("*.py")):
        text += path.read_text()
    assert "simplify(" not in text
    assert "Phi_Gamma" not in text
    assert "guo_map" not in text
    assert "openai" not in text.lower()
