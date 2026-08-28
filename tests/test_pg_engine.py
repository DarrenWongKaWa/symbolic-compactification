"""Atom-series polygamma confluence. Timeout is UNKNOWN, never ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.polygamma_confluence.engine import atom_series_confluence  # noqa: E402
from research.polygamma_confluence.schema import NONZERO, UNKNOWN, ZERO  # noqa: E402


def test_newton_polygamma0_is_zero():
    x, y = sympy.symbols("x y")
    src = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (y - x)
    tgt = sympy.polygamma(1, x)
    r = atom_series_confluence(src, tgt, y, x)
    assert r.verdict == ZERO, r.to_dict()
    assert r.reconstruction_ok is True
    assert r.n_atoms >= 1


def test_wrong_order_is_nonzero():
    x, y = sympy.symbols("x y")
    src = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (y - x)
    tgt = sympy.polygamma(2, x)
    r = atom_series_confluence(src, tgt, y, x)
    assert r.verdict in (NONZERO, UNKNOWN)
    assert r.verdict != ZERO


def test_cubic_newton_still_zero():
    x, y = sympy.symbols("x y")
    r = atom_series_confluence((x ** 3 - y ** 3) / (x - y), 3 * x ** 2, y, x)
    assert r.verdict == ZERO, r.to_dict()


def test_source_ban():
    src = Path(ROOT, "research/polygamma_confluence/engine.py").read_text()
    assert "Phi_Gamma" not in src
    assert "guo_map" not in src
    assert "L4" not in src
