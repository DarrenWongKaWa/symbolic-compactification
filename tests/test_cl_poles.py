"""Negative Laurent coefficients: leftover t^{-1} is NONZERO; t^0 is not a skip."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.poles import (  # noqa: E402
    NONZERO,
    OPS_CAP,
    UNKNOWN,
    ZERO,
    certify_negative,
)
from research.coefficient_laurent.schema import compose_hop_verdict  # noqa: E402
import research.coefficient_laurent.poles.certify as poles_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "poles"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma", "sympy.limit")


def _huge() -> sympy.Expr:
    x = sympy.symbols("x")
    expr: sympy.Expr = sympy.Integer(0)
    i = 1
    while int(sympy.count_ops(expr, visual=False)) <= OPS_CAP:
        expr = expr + (x + i) ** 3
        i += 1
        if i > 5000:
            break
    assert int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    return expr


def _powers(cert) -> list[int]:
    return [rec.power for rec in cert.records]


def test_public_api():
    assert callable(certify_negative)
    assert ZERO == "ZERO"
    assert NONZERO == "NONZERO"
    assert UNKNOWN == "UNKNOWN"
    assert OPS_CAP == 120
    sig = inspect.signature(certify_negative)
    assert list(sig.parameters)[:1] == ["sparse_map"]


def test_all_negative_zero_is_zero():
    x = sympy.symbols("x")
    expand_zero = (x + 1) ** 2 - x**2 - 2 * x - 1
    cancel_zero = (x**2 - 1) / (x - 1) - (x + 1)
    r = certify_negative(
        {
            -3: sympy.Integer(0),
            -2: expand_zero,
            -1: cancel_zero,
            0: x,
            1: x**2,
        }
    )
    assert r.verdict == ZERO
    assert r.verdict != UNKNOWN
    assert set(_powers(r)) == {-3, -2, -1}
    assert 0 not in _powers(r)
    by_p = {rec.power: rec for rec in r.records}
    assert by_p[-3].verdict == ZERO
    assert by_p[-2].verdict == ZERO
    assert by_p[-2].method == "expand"
    assert by_p[-1].verdict == ZERO
    assert by_p[-1].method == "cancel"
    assert all(rec.exact for rec in r.records)


def test_t_minus_1_leftover_is_nonzero():
    r = certify_negative({-1: sympy.Integer(1)})
    assert r.verdict == NONZERO
    assert r.verdict != ZERO
    assert _powers(r) == [-1]
    assert r.records[0].verdict == NONZERO
    assert r.records[0].exact is True


def test_huge_undecided_is_unknown():
    r = certify_negative({-1: _huge()})
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert r.verdict != NONZERO
    assert _powers(r) == [-1]
    assert r.records[0].verdict == UNKNOWN
    assert r.records[0].method == "size_guard"
    assert r.records[0].exact is False


def test_t0_match_must_not_hide_t_minus_1():
    """A matching t^0 coefficient must not skip leftover t^{-1}."""
    K = sympy.symbols("K")
    r = certify_negative({-1: sympy.Integer(1), 0: K, 1: sympy.Integer(0)})
    assert r.verdict == NONZERO
    assert r.verdict != ZERO
    assert -1 in _powers(r)
    assert 0 not in _powers(r)
    rec = next(item for item in r.records if item.power == -1)
    assert rec.verdict == NONZERO
    hop, _lvl = compose_hop_verdict(
        reconstruction_ok=True,
        atoms_expanded=True,
        negative_verdict=r.verdict,
        constant_verdict=ZERO,
        remainder_verdict=ZERO,
    )
    assert hop == NONZERO


def test_no_negative_powers_is_zero():
    r = certify_negative({0: sympy.symbols("K"), 2: sympy.Integer(1)})
    assert r.verdict == ZERO
    assert r.records == ()


def test_empty_sparse_map_is_zero():
    r = certify_negative({})
    assert r.verdict == ZERO
    assert r.records == ()


def test_huge_t0_does_not_undecide_vanished_poles():
    r = certify_negative({-1: sympy.Integer(0), 0: _huge()})
    assert r.verdict == ZERO
    assert _powers(r) == [-1]


def test_string_keys_and_zero_strings():
    r = certify_negative({"-2": "0", "-1": "0", "0": "K"})
    assert r.verdict == ZERO
    assert set(_powers(r)) == {-2, -1}


def test_nonzero_dominates_huge_unknown():
    r = certify_negative({-2: _huge(), -1: sympy.Integer(1)})
    assert r.verdict == NONZERO
    by_p = {rec.power: rec for rec in r.records}
    assert by_p[-2].verdict == UNKNOWN
    assert by_p[-1].verdict == NONZERO


def test_huge_skips_expand_and_cancel(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("expand/cancel must not run on huge C_p")

    monkeypatch.setattr(poles_mod.sympy, "expand", _boom)
    monkeypatch.setattr(poles_mod.sympy, "cancel", _boom)
    r = certify_negative({-1: _huge(), 0: sympy.Integer(1)})
    assert r.verdict == UNKNOWN
    assert r.records[0].method == "size_guard"


def test_source_ban():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix != ".py":
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
