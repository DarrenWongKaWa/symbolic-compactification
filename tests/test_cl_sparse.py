"""Sparse Laurent maps: powerwise add/convolve/scale. No together of the kernel."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.sparse import (  # noqa: E402
    EXPAND_OPS_CAP,
    add_maps,
    convolve,
    count_ops_map,
    scale,
)
from research.coefficient_laurent.sparse import algebra as algebra_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "sparse"


def _symbols():
    return sympy.symbols("a b t0 x")


def test_public_api():
    assert add_maps is algebra_mod.add_maps
    assert convolve is algebra_mod.convolve
    assert scale is algebra_mod.scale
    assert count_ops_map is algebra_mod.count_ops_map
    assert EXPAND_OPS_CAP > 0


def test_add_two_maps():
    a, b, _t0, _x = _symbols()
    left = {-1: 1, 0: a}
    right = {-1: 2, 0: b, 2: a}
    got = add_maps(left, right)
    assert set(got) == {-1, 0, 2}
    assert got[-1] == sympy.Integer(3)
    assert sympy.expand(got[0] - (a + b)) == 0
    assert got[2] == a
    assert left == {-1: 1, 0: a}
    assert right == {-1: 2, 0: b, 2: a}


def test_add_maps_drops_cancelled_power():
    a, _b, _t0, _x = _symbols()
    got = add_maps({-1: 1, 0: a}, {-1: -1, 0: -a})
    assert got == {}


def test_convolve_pole_with_t0():
    a, _b, t0, _x = _symbols()
    got = convolve({-1: 1, 0: a}, {1: t0})
    assert set(got) == {0, 1}
    assert got[0] == t0
    assert sympy.expand(got[1] - a * t0) == 0


def test_scale_and_count_ops_map():
    a, _b, _t0, _x = _symbols()
    m = {-1: 1, 0: a + 1}
    got = scale(m, 2)
    assert got[-1] == sympy.Integer(2)
    assert sympy.expand(got[0] - 2 * (a + 1)) == 0
    assert scale(m, 0) == {}
    assert count_ops_map(got) == int(sympy.count_ops(got[-1], visual=False)) + int(
        sympy.count_ops(got[0], visual=False)
    )
    assert count_ops_map({}) == 0


def test_over_cap_leaves_unsimplified():
    _a, _b, _t0, x = _symbols()
    term = (x + 1) ** 2
    kept = add_maps({0: term}, {}, ops_cap=0)
    assert kept[0] == term
    expanded = add_maps({0: term}, {}, ops_cap=EXPAND_OPS_CAP)
    assert expanded[0] == sympy.expand(term)
    assert expanded[0] != term


def test_add_convolve_scale_never_call_together(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("together of summed kernel is forbidden")

    monkeypatch.setattr(sympy, "together", _boom)
    a, _b, t0, _x = _symbols()
    added = add_maps({-1: 1, 0: a}, {-1: -1, 1: a})
    conv = convolve({-1: 1, 0: a}, {1: t0})
    scaled = scale({-1: 1, 0: a}, t0)
    assert added[1] == a
    assert 0 in conv
    assert scaled[-1] == t0


def test_source_ban_no_together_of_summed_kernel():
    files = sorted(p for p in PKG.rglob("*.py") if p.is_file())
    assert files
    for path in files:
        src = path.read_text(encoding="utf-8")
        assert "sympy.together" not in src, path.name
        assert ".together(" not in src, path.name
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    assert func.id != "together", path.name
                elif isinstance(func, ast.Attribute):
                    assert func.attr != "together", path.name
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name != "together", path.name
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "together", path.name
