"""Derivative-basis Taylor CONTROL for polygamma. Not a hop certificate."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.basis import (  # noqa: E402
    CONTROL,
    DERIVATIVE_IDENTITY,
    NTERMS_CAP,
    UNKNOWN,
    polygamma_taylor_basis,
)
import research.coefficient_laurent.basis as basis_pkg  # noqa: E402
import research.coefficient_laurent.basis.taylor as taylor_mod  # noqa: E402

PKG = ROOT / "research" / "coefficient_laurent" / "basis"
BANNED = ("Phi_Gamma", "PhiGamma", "phi_gamma", "FAMILY_ZERO")


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.expand(a - b) == 0
    except Exception:
        return False


def _z0bt():
    return sympy.symbols("z0 b t")


def test_public_api():
    assert callable(polygamma_taylor_basis)
    assert polygamma_taylor_basis is taylor_mod.polygamma_taylor_basis
    sig = inspect.signature(polygamma_taylor_basis)
    assert list(sig.parameters)[:4] == ["k", "z0", "b", "t"]
    assert sig.parameters["nterms"].default == 2
    assert NTERMS_CAP == 16
    assert CONTROL == "CONTROL"
    assert UNKNOWN == "UNKNOWN"
    assert DERIVATIVE_IDENTITY == "d^n/dz^n polygamma(k, z) = polygamma(k+n, z)"
    assert not hasattr(basis_pkg, "FAMILY_ZERO")
    assert not hasattr(basis_pkg, "compose_hop_verdict")


def test_n0_first_two_terms_match_sympy_series():
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    assert r.status == CONTROL
    assert r.polynomial is not None
    assert len(r.terms) == 2
    raw = sympy.polygamma(0, z0 + b * t).series(t, 0, 2)
    core = raw.removeO()
    assert _eq(r.polynomial, core)
    assert _eq(r.terms[0], sympy.polygamma(0, z0))
    assert _eq(r.terms[1], sympy.polygamma(1, z0) * b * t)


def test_wrong_factorial_is_not_equal():
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    raw = sympy.polygamma(0, z0 + b * t).series(t, 0, 2).removeO()
    wrong = sympy.Add(
        *[
            sympy.polygamma(n, z0) * (b * t) ** n / sympy.factorial(n + 1)
            for n in range(2)
        ]
    )
    assert _eq(r.polynomial, raw)
    assert not _eq(r.polynomial, wrong)
    assert not _eq(wrong, raw)
    assert sympy.expand(r.polynomial - wrong) != 0


def test_ops_vs_raw_series():
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    raw = sympy.polygamma(0, z0 + b * t).series(t, 0, 2)
    assert isinstance(r.basis_ops, int)
    assert isinstance(r.raw_ops, int)
    assert r.raw_ops == int(sympy.count_ops(raw, visual=False))
    assert r.basis_ops == int(sympy.count_ops(r.polynomial, visual=False))
    assert r.basis_ops <= r.raw_ops
    assert r.raw_core_ops == int(sympy.count_ops(raw.removeO(), visual=False))


def test_nested_argument_basis_keeps_fewer_ops_than_raw_series():
    beta, gamma, mu, b, t = sympy.symbols("beta gamma mu b t")
    z0 = (beta * (gamma + sympy.I * mu) + sympy.pi) / (2 * sympy.pi)
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    raw = sympy.polygamma(0, z0 + b * t).series(t, 0, 2)
    assert r.status == CONTROL
    assert _eq(r.polynomial, raw.removeO())
    assert r.basis_ops < r.raw_ops
    assert r.basis_ops < int(sympy.count_ops(raw.removeO(), visual=False))


def test_documented_derivative_identity():
    k, z = sympy.symbols("k z")
    assert sympy.diff(sympy.polygamma(k, z), z) == sympy.polygamma(k + 1, z)
    assert sympy.diff(sympy.polygamma(k, z), z, 2) == sympy.polygamma(k + 2, z)
    src = Path(taylor_mod.__file__).read_text(encoding="utf-8")
    assert "d/dz polygamma(k, z) = polygamma(k + 1, z)" in src
    assert DERIVATIVE_IDENTITY in src
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(1, z0, b, t, nterms=3)
    assert r.identity == DERIVATIVE_IDENTITY
    assert _eq(r.terms[0], sympy.polygamma(1, z0))
    assert _eq(r.terms[1], sympy.polygamma(2, z0) * b * t)
    assert _eq(r.terms[2], sympy.polygamma(3, z0) * (b * t) ** 2 / 2)


def test_construction_does_not_require_cas_series(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("basis rewrite must not use CAS series")

    monkeypatch.setattr(sympy.Expr, "series", _boom)
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    assert r.status == CONTROL
    assert r.polynomial is not None
    assert _eq(r.polynomial, sympy.polygamma(0, z0) + sympy.polygamma(1, z0) * b * t)
    assert r.raw_ops is None
    assert r.raw_series is None


def test_never_emits_hop_zero():
    z0, b, t = _z0bt()
    r = polygamma_taylor_basis(0, z0, b, t, nterms=2)
    blob = r.to_dict()
    assert r.status != "ZERO"
    assert blob.get("status") != "ZERO"
    assert blob.get("verdict") is None
    assert "FAMILY_ZERO" not in str(blob)
    assert "ZERO" not in r.note
    bad = polygamma_taylor_basis(0, z0, b, t, nterms=0)
    assert bad.status == UNKNOWN
    assert bad.polynomial is None
    assert bad.status != "ZERO"


def test_source_ban_and_not_a_proposer():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix != ".py":
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        assert "Phi_Gamma" not in src
        assert "grounded_proposer" not in src
        assert "STRUCTURAL_PROPOSER" not in src
        assert "compose_hop_verdict" not in src
        assert "FAMILY_ZERO" not in src
    src = Path(taylor_mod.__file__).read_text(encoding="utf-8")
    assert "Not a proposer" in src
    assert "not a hop certificate" in src.lower()
    init_src = (PKG / "__init__.py").read_text(encoding="utf-8")
    assert "Not a proposer" in init_src
