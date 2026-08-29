"""Polygamma derivative chain. Coefficients only; not remainder CERTIFIED."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.derivatives import (  # noqa: E402
    DIFF_IDENTITY,
    DOMAIN_OWNER,
    METHOD,
    R_MAX_CAP,
    TAYLOR_IDENTITY,
    polygamma_diff,
    polygamma_taylor_coefficient,
    polygamma_taylor_coefficients,
)
from research.remainder_certification.schema import (  # noqa: E402
    CERTIFIED,
    HOP_ZERO,
)
import research.remainder_certification.derivatives as deriv_pkg  # noqa: E402
import research.remainder_certification.derivatives.chain as chain_mod  # noqa: E402

PKG = ROOT / "research" / "remainder_certification" / "derivatives"
BANNED = (
    "Phi_Gamma",
    "PhiGamma",
    "phi_gamma",
    "Guo",
    "GUO",
    "G0016",
    "G0013",
    "compose_hop_verdict",
    "FAMILY_ZERO",
    "fb3b929",
)


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.expand(a - b) == 0
    except Exception:
        return False


def _series_coeff(k: int, z0: sympy.Expr, c: sympy.Expr, t: sympy.Expr, r: int):
    raw = sympy.polygamma(k, z0 + c * t).series(t, 0, r + 1)
    return raw.removeO().coeff(t, r)


def test_public_api():
    assert callable(polygamma_diff)
    assert callable(polygamma_taylor_coefficient)
    assert callable(polygamma_taylor_coefficients)
    assert polygamma_diff is chain_mod.polygamma_diff
    assert polygamma_taylor_coefficient is chain_mod.polygamma_taylor_coefficient
    assert polygamma_taylor_coefficients is chain_mod.polygamma_taylor_coefficients
    sig = inspect.signature(polygamma_taylor_coefficients)
    assert list(sig.parameters)[:4] == ["k", "z0", "c", "r_max"]
    assert sig.parameters["r_max"].default == 2
    assert R_MAX_CAP == 16
    assert DOMAIN_OWNER == "R2/R3"
    assert DIFF_IDENTITY == "d/dz polygamma(k,z) = polygamma(k+1,z)"
    assert "polygamma(k+r, z0) * c^r / r!" in TAYLOR_IDENTITY
    assert METHOD == "rc-pg-derivative-chain-1"
    assert not hasattr(deriv_pkg, "compose_hop_verdict")
    assert not hasattr(deriv_pkg, "RemainderCertificate")


def test_diff_identity_k012():
    z = sympy.symbols("z")
    for k in (0, 1, 2):
        lhs = sympy.diff(sympy.polygamma(k, z), z)
        rhs = sympy.polygamma(k + 1, z)
        assert lhs == rhs
        got = polygamma_diff(k, z)
        assert got == lhs
        assert got == rhs
        assert got == sympy.polygamma(k + 1, z)


def test_iterated_diff_is_polygamma_shift():
    z = sympy.symbols("z")
    for k in (0, 1, 2):
        for r in (0, 1, 2):
            d = sympy.diff(sympy.polygamma(k, z), z, r)
            assert d == sympy.polygamma(k + r, z)


def test_taylor_coeffs_match_series_k012_r012():
    z0, c, t = sympy.symbols("z0 c t")
    report = polygamma_taylor_coefficients(0, z0, c, r_max=2)
    assert report.domain_owner == DOMAIN_OWNER
    assert report.identity == DIFF_IDENTITY
    assert len(report.coefficients) == 3
    for k in (0, 1, 2):
        got = polygamma_taylor_coefficients(k, z0, c, r_max=2)
        assert got.domain_owner == "R2/R3"
        assert got.r_max == 2
        for r in (0, 1, 2):
            chain = got.coeff(r)
            formula = sympy.polygamma(k + r, z0) * c ** r / sympy.factorial(r)
            series = _series_coeff(k, z0, c, t, r)
            assert chain is not None
            assert _eq(chain, formula)
            assert _eq(chain, series)
            assert _eq(formula, series)
            one = polygamma_taylor_coefficient(k, z0, c, r)
            assert one is not None
            assert _eq(one, chain)


def test_holomorphic_numeric_point_matches_series():
    t = sympy.symbols("t")
    z0 = sympy.Integer(1)
    c = sympy.Integer(2)
    for k in (0, 1, 2):
        got = polygamma_taylor_coefficients(k, z0, c, r_max=2)
        for r in (0, 1, 2):
            chain = got.coeff(r)
            series = _series_coeff(k, z0, c, t, r)
            formula = sympy.polygamma(k + r, z0) * c ** r / sympy.factorial(r)
            assert _eq(chain, series)
            assert _eq(chain, formula)


def test_wrong_order_or_factorial_does_not_match_series():
    z0, c, t = sympy.symbols("z0 c t")
    got = polygamma_taylor_coefficients(0, z0, c, r_max=2)
    for r in (0, 1, 2):
        series = _series_coeff(0, z0, c, t, r)
        wrong_order = sympy.polygamma(r + 1, z0) * c ** r / sympy.factorial(r)
        assert _eq(got.coeff(r), series)
        assert not _eq(got.coeff(r), wrong_order)
        assert sympy.expand(got.coeff(r) - wrong_order) != 0
    # r=0 has 0! = 1! so a factorial off-by-one is not a test; use r=1,2.
    for r in (1, 2):
        wrong_fact = sympy.polygamma(r, z0) * c ** r / sympy.factorial(r + 1)
        assert not _eq(got.coeff(r), wrong_fact)


def test_construction_does_not_require_cas_series(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("derivative-chain coeffs must not use CAS series")

    monkeypatch.setattr(sympy.Expr, "series", _boom)
    z0, c = sympy.symbols("z0 c")
    got = polygamma_taylor_coefficients(1, z0, c, r_max=2)
    assert len(got.coefficients) == 3
    assert _eq(got.coeff(0), sympy.polygamma(1, z0))
    assert _eq(got.coeff(1), sympy.polygamma(2, z0) * c)
    assert _eq(got.coeff(2), sympy.polygamma(3, z0) * c ** 2 / 2)


def test_never_emits_remainder_certified_or_hop_zero():
    z0, c = sympy.symbols("z0 c")
    report = polygamma_taylor_coefficients(0, z0, c, r_max=2)
    blob = report.to_dict()
    assert "remainder_verdict" not in blob
    assert "verdict" not in blob
    assert "proof_level" not in blob
    assert CERTIFIED not in blob.values()
    assert HOP_ZERO not in blob.values()
    assert blob.get("domain_owner") == "R2/R3"
    assert report.coeff(0) is not None
    bad = polygamma_taylor_coefficients(0, z0, c, r_max=-1)
    assert bad.coefficients == ()
    bad_blob = bad.to_dict()
    assert CERTIFIED not in bad_blob.values()
    assert "remainder_verdict" not in bad_blob
    assert polygamma_taylor_coefficient(0, z0, c, -1) is None
    assert polygamma_diff(-1, z0) is None


def test_source_ban_and_identity_documented():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        assert "compose_hop_verdict" not in src
    py = Path(chain_mod.__file__).read_text(encoding="utf-8")
    assert "d/dz polygamma(k, z) = polygamma(k+1, z)" in py
    assert "R2/R3" in py
    assert "sympy.diff" in py
    assert ".series" not in py.replace("not CAS ``series``", "")
    assert "Expr.series" not in py
    init_src = (PKG / "__init__.py").read_text(encoding="utf-8")
    assert "no remainder CERTIFIED" in init_src
