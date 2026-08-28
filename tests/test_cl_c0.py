"""Constant-term matcher. No full-kernel together. Size-guard is UNKNOWN."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.c0 import (  # noqa: E402
    OPS_CAP,
    match_constant,
)
from research.coefficient_laurent.c0 import match as match_mod  # noqa: E402
from research.coefficient_laurent.schema import NONZERO, UNKNOWN, ZERO  # noqa: E402

C0_DIR = ROOT / "research" / "coefficient_laurent" / "c0"
BANNED = ("Phi_Gamma", "openai", "anthropic", "llm_abstraction")


def _huge_dummy(n_terms: int) -> sympy.Expr:
    d = sympy.Dummy("d")
    return sympy.Add(*[d**i for i in range(1, n_terms + 1)], evaluate=False)


def test_public_api_importable():
    assert match_constant is match_mod.match_constant
    assert OPS_CAP == 800
    sig = inspect.signature(match_constant)
    assert list(sig.parameters)[:2] == ["c0", "target"]


def test_identical_is_zero():
    x = sympy.symbols("x")
    r = match_constant(3 * x**2, 3 * x**2)
    assert r.verdict == ZERO
    assert r.verdict != UNKNOWN
    assert r.used_full_together is False
    assert r.ops <= OPS_CAP


def test_3x2_vs_4x2_is_nonzero():
    x = sympy.symbols("x")
    r = match_constant(3 * x**2, 4 * x**2)
    assert r.verdict == NONZERO
    assert r.verdict != ZERO
    assert r.used_full_together is False


def test_huge_dummy_is_unknown():
    huge = _huge_dummy(OPS_CAP + 50)
    ops = int(sympy.count_ops(huge, visual=False))
    assert ops + ops > OPS_CAP
    r = match_constant(huge, huge)
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert r.provenance == "size_guard"
    assert r.used_full_together is False


def test_does_not_call_together(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("full-kernel together is forbidden")

    monkeypatch.setattr(sympy, "together", _boom)
    x = sympy.symbols("x")
    assert match_constant(3 * x**2, 3 * x**2).verdict == ZERO
    assert match_constant(3 * x**2, 4 * x**2).verdict == NONZERO
    huge = _huge_dummy(OPS_CAP + 50)
    assert match_constant(huge, huge).verdict == UNKNOWN


def test_polygamma_rational_coeffs_match_without_together(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("full-kernel together is forbidden")

    monkeypatch.setattr(sympy, "together", _boom)
    x, z = sympy.symbols("x z")
    pg = sympy.polygamma(1, z)
    c0 = ((x**2 - 1) / (x - 1)) * pg
    tgt = (x + 1) * pg
    r = match_constant(c0, tgt)
    assert r.verdict == ZERO
    assert r.used_full_together is False
    monkeypatch.setattr(match_mod, "CANCEL_OPS_CAP", 0)
    grouped = match_constant(c0, tgt)
    assert grouped.verdict == ZERO
    assert grouped.provenance == "pg_atoms"


def test_polygamma_coeff_mismatch_is_nonzero(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("full-kernel together is forbidden")

    monkeypatch.setattr(sympy, "together", _boom)
    z = sympy.symbols("z")
    r = match_constant(2 * sympy.polygamma(1, z), 3 * sympy.polygamma(1, z))
    assert r.verdict == NONZERO
    assert r.verdict != ZERO


def test_source_ban_no_together_no_llm():
    for path in sorted(C0_DIR.rglob("*")):
        if not path.is_file() or path.suffix != ".py":
            continue
        src = path.read_text(encoding="utf-8")
        assert "sympy.together" not in src, path.name
        assert "simplify(" not in src, path.name
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
