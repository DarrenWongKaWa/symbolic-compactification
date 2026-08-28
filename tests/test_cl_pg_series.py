"""Per-atom polygamma Laurent series. Failure is empty/exact=False, never ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.pg_series import (  # noqa: E402
    SERIES_OPS_CAP,
    expand_polygamma_atom,
)
import research.coefficient_laurent.pg_series.expand as expand_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "pg_series"
BANNED = (
    "Phi_Gamma",
    "phi_gamma",
    "guo_map",
    "Guo",
    "GUO",
    "L4",
    "L5",
    "L6",
    "L7",
    "identity_table",
)


def test_public_api():
    assert callable(expand_polygamma_atom)
    assert expand_polygamma_atom is expand_mod.expand_polygamma_atom
    assert SERIES_OPS_CAP == 80
    sig = inspect.signature(expand_polygamma_atom)
    assert list(sig.parameters)[:5] == ["term", "var", "point", "pmin", "pmax"]


def test_newton_psi_constant_term_is_polygamma1():
    """(psi(x+t)-psi(x))/t series t^0 is polygamma(1, x)."""
    x, t = sympy.symbols("x t")
    term = (sympy.polygamma(0, x + t) - sympy.polygamma(0, x)) / t
    got = expand_polygamma_atom(term, t, 0, -2, 2)
    assert got.exact is True
    assert 0 in got
    c0 = got[0]
    assert sympy.expand(c0 - sympy.polygamma(1, x)) == 0
    assert c0 == sympy.polygamma(1, x)

    y = sympy.symbols("y")
    newt = (sympy.polygamma(0, y) - sympy.polygamma(0, x)) / (y - x)
    got_y = expand_polygamma_atom(newt, y, x, -1, 2)
    assert got_y.exact is True
    assert sympy.expand(got_y[0] - sympy.polygamma(1, x)) == 0


def test_wrong_order_not_equal():
    x, t = sympy.symbols("x t")
    term = (sympy.polygamma(0, x + t) - sympy.polygamma(0, x)) / t
    got = expand_polygamma_atom(term, t, 0, -1, 2)
    assert got.exact is True
    c0 = got[0]
    assert sympy.expand(c0 - sympy.polygamma(1, x)) == 0
    assert sympy.expand(c0 - sympy.polygamma(2, x)) != 0
    assert c0 != sympy.polygamma(2, x)


def test_per_atom_sum_constant_is_polygamma1():
    x, t = sympy.symbols("x t")
    left = expand_polygamma_atom(sympy.polygamma(0, x + t) / t, t, 0, -2, 1)
    right = expand_polygamma_atom(-sympy.polygamma(0, x) / t, t, 0, -2, 1)
    assert left.exact is True
    assert right.exact is True
    c0 = sympy.expand(left[0] + right[0])
    c_m1 = sympy.expand(left[-1] + right[-1])
    assert c0 == sympy.polygamma(1, x)
    assert c_m1 == 0
    assert sympy.expand(c0 - sympy.polygamma(2, x)) != 0


def test_singular_argument_empty_not_exact():
    t = sympy.Dummy("t")
    got = expand_polygamma_atom(sympy.polygamma(0, 1 / t), t, 0, -2, 2)
    assert got.exact is False
    assert dict(got) == {}
    assert list(got) == []


def test_source_ban():
    files = sorted(
        p for p in PKG.rglob("*") if p.is_file() and p.suffix in {".py", ".md"}
    )
    assert files
    for path in files:
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        if path.suffix == ".py":
            assert "sympy.limit" not in src
            assert ".limit(" not in src
