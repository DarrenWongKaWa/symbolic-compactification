"""Certified local-kernel complexity reduction. Uncertified rewrites fail closed."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.complexity import (  # noqa: E402
    count_ops,
    reduce_kernel,
)
from research.iterated_confluence.complexity import reduce as reduce_mod  # noqa: E402

KEYS = {"original_ops", "reduced_ops", "expr_reduced", "trace", "equivalent"}
COMPLEXITY_PY = ROOT / "research" / "iterated_confluence" / "complexity"


def _uncancelled_ratio() -> tuple[sympy.Symbol, sympy.Symbol, sympy.Expr]:
    x, y = sympy.symbols("x y")
    expr = sympy.Mul(x - y, x + y, sympy.Pow(x - y, -1), evaluate=False)
    return x, y, expr


def _assert_shape(out: dict) -> None:
    assert set(out) == KEYS
    assert isinstance(out["original_ops"], int)
    assert isinstance(out["reduced_ops"], int)
    assert isinstance(out["trace"], list)
    assert all(isinstance(item, str) for item in out["trace"])
    assert isinstance(out["equivalent"], bool)


def test_public_api_importable():
    assert reduce_kernel is reduce_mod.reduce_kernel
    assert count_ops is reduce_mod.count_ops


def test_count_ops_matches_sympy():
    x, y = sympy.symbols("x y")
    expr = x + y
    assert count_ops(expr) == int(sympy.count_ops(expr, visual=False))
    _, _, ratio = _uncancelled_ratio()
    assert count_ops(ratio) == int(sympy.count_ops(ratio, visual=False))
    assert count_ops(ratio) > count_ops(x + y)


def test_cancel_common_linear_factor():
    x, y, expr = _uncancelled_ratio()
    assert expr != x + y
    assert count_ops(expr) > count_ops(x + y)
    out = reduce_kernel(expr)
    _assert_shape(out)
    assert out["equivalent"] is True
    assert out["expr_reduced"] == x + y
    assert out["original_ops"] == count_ops(expr)
    assert out["reduced_ops"] == count_ops(x + y)
    assert out["reduced_ops"] < out["original_ops"]
    assert sympy.cancel(expr - out["expr_reduced"]) == 0
    assert any(item.startswith("cancel:") for item in out["trace"])


def test_uncertified_rewrite_rejected(monkeypatch):
    x = sympy.symbols("x")
    original = sympy.sin(x) ** 2 + sympy.cos(x) ** 2
    assert sympy.cancel(original - 1) != 0

    def fake_propose(expr):
        return sympy.Integer(1), ["bad: uncertified trig collapse"]

    monkeypatch.setattr(reduce_mod, "_propose_reduced", fake_propose)
    out = reduce_kernel(original)
    _assert_shape(out)
    assert out["equivalent"] is False
    assert out["expr_reduced"] == original
    assert out["reduced_ops"] == out["original_ops"] == count_ops(original)
    assert any("rejected" in item for item in out["trace"])


def test_uncertified_bad_transform_rejected(monkeypatch):
    x, y = sympy.symbols("x y")
    original = x + y

    def fake_cancel(expr):
        return sympy.Integer(0)

    monkeypatch.setattr(reduce_mod, "_transform_cancel", fake_cancel)
    out = reduce_kernel(original)
    _assert_shape(out)
    assert out["equivalent"] is False
    assert out["expr_reduced"] == original
    assert out["expr_reduced"] != sympy.Integer(0)


def test_piecewise_is_not_collapsed():
    x, y, ratio = _uncancelled_ratio()
    m, n = sympy.symbols("m n")
    expr = sympy.Piecewise(
        (ratio, sympy.Eq(m, n)),
        (x + y, True),
        evaluate=False,
    )
    assert isinstance(expr, sympy.Piecewise)
    assert len(expr.args) == 2
    out = reduce_kernel(expr)
    _assert_shape(out)
    reduced = out["expr_reduced"]
    assert out["equivalent"] is True
    assert isinstance(reduced, sympy.Piecewise)
    assert len(reduced.args) == 2
    assert reduced.args[0][1] == expr.args[0][1]
    assert reduced.args[1][1] == expr.args[1][1]
    assert reduced != x + y
    assert out["reduced_ops"] <= out["original_ops"]
    assert sympy.cancel(reduced.args[0][0] - (x + y)) == 0
    assert any("preserved 2 branches" in item for item in out["trace"])


def test_piecewise_three_branches_not_merged():
    x, y, ratio = _uncancelled_ratio()
    m, n, p = sympy.symbols("m n p")
    expr = sympy.Piecewise(
        (ratio, sympy.Eq(m, n)),
        (x - y, sympy.Eq(m, p)),
        (x + y, True),
        evaluate=False,
    )
    assert isinstance(expr, sympy.Piecewise)
    assert len(expr.args) == 3
    out = reduce_kernel(expr)
    _assert_shape(out)
    reduced = out["expr_reduced"]
    assert out["equivalent"] is True
    assert isinstance(reduced, sympy.Piecewise)
    assert len(reduced.args) == 3
    assert [cond for _, cond in reduced.args] == [cond for _, cond in expr.args]
    assert reduced != x + y
    assert any("preserved 3 branches" in item for item in out["trace"])


def test_never_returns_different_expr_without_equivalent_true():
    x, y = sympy.symbols("x y")
    _, _, ratio = _uncancelled_ratio()
    m, n = sympy.symbols("m n")
    cases = [
        ratio,
        x + y,
        sympy.sin(x) ** 2 + sympy.cos(x) ** 2,
        x * y + x * n + y,
        sympy.Piecewise((ratio, sympy.Eq(m, n)), (x + y, True), evaluate=False),
        sympy.Integer(3),
    ]
    for expr in cases:
        out = reduce_kernel(expr)
        _assert_shape(out)
        if out["expr_reduced"] != expr:
            assert out["equivalent"] is True
            assert _protected_same(expr, out["expr_reduced"])
            assert sympy.cancel(expr - out["expr_reduced"]) == 0 or isinstance(
                expr, sympy.Piecewise
            )


def test_trig_identity_not_secretly_applied():
    x = sympy.symbols("x")
    expr = sympy.sin(x) ** 2 + sympy.cos(x) ** 2
    out = reduce_kernel(expr)
    _assert_shape(out)
    assert out["expr_reduced"] == expr
    assert out["equivalent"] is True
    assert out["expr_reduced"] != sympy.Integer(1)


def test_together_common_denominator():
    x, y = sympy.symbols("x y")
    expr = x / (x - y) + y / (x - y)
    out = reduce_kernel(expr)
    _assert_shape(out)
    assert out["equivalent"] is True
    assert out["reduced_ops"] < out["original_ops"]
    assert sympy.cancel(expr - out["expr_reduced"]) == 0


def test_collect_lowers_ops():
    x, y, z = sympy.symbols("x y z")
    expr = x * y + x * z + y
    out = reduce_kernel(expr)
    _assert_shape(out)
    assert out["equivalent"] is True
    assert out["reduced_ops"] <= out["original_ops"]
    if out["expr_reduced"] != expr:
        assert sympy.cancel(expr - out["expr_reduced"]) == 0


def test_source_ban_no_phi_gamma_no_guo_table():
    files = sorted(
        p for p in COMPLEXITY_PY.rglob("*")
        if p.is_file() and p.suffix in {".py", ".md"}
    )
    assert files
    banned = (
        "Phi_Gamma",
        "guo_map",
        "GUO_OBLIGATION",
        "identity_table",
        "sympy.simplify",
        ".simplify(",
        "sympy.series",
        ".series(",
    )
    for path in files:
        src = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in src, (path.name, token)


def _protected_same(a: sympy.Basic, b: sympy.Basic) -> bool:
    return reduce_mod._protected_signature(a) == reduce_mod._protected_signature(b)
