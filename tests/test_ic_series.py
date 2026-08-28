"""Multivariate series CONTROL for iterated-limit toys. Not a verifier."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.series import (  # noqa: E402
    COMPARED,
    OPS_CAP,
    UNKNOWN,
    iterated_limits,
    multivariate_control,
)
import research.iterated_confluence.series as series_pkg  # noqa: E402
import research.iterated_confluence.series.control as control_mod  # noqa: E402

PKG = ROOT / "research" / "iterated_confluence" / "series"
BANNED = ("Guo", "GUO", "Phi_Gamma", "phi_gamma")


def _xy():
    return sympy.symbols("x y")


def test_public_api():
    assert callable(iterated_limits)
    assert callable(multivariate_control)
    assert OPS_CAP == 40
    assert UNKNOWN == "UNKNOWN"
    assert not hasattr(series_pkg, "FAMILY_ZERO")
    sig = inspect.signature(iterated_limits)
    assert list(sig.parameters)[:2] == ["expr", "steps"]
    sig_c = inspect.signature(multivariate_control)
    assert list(sig_c.parameters)[:2] == ["expr", "vars_and_points"]


def test_readme_is_control_not_verifier():
    text = (PKG / "README.md").read_text(encoding="utf-8").lower()
    assert "control" in text
    assert "not a verifier" in text
    assert "family certificate" in text


def test_source_ban_no_gold_names():
    for path in sorted(PKG.rglob("*")):
        if not path.is_file() or path.suffix not in {".py", ".md"}:
            continue
        src = path.read_text(encoding="utf-8")
        for tok in BANNED:
            assert tok not in src, (path.name, tok)
        if path.suffix == ".py":
            assert "sympy.limit" not in src


def test_removable_cubic_at_y_eq_x_is_3x2():
    x, y = _xy()
    expr = (x**3 - y**3) / (x - y)
    got = iterated_limits(expr, [(y, x)])
    assert got is not None
    assert sympy.expand(got - 3 * x**2) == 0


def test_removable_does_not_call_cas_limit(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("explicit series/cancel only")

    monkeypatch.setattr(sympy, "limit", _boom)
    x, y = _xy()
    got = iterated_limits((x**3 - y**3) / (x - y), [(y, x)])
    assert got is not None
    assert sympy.expand(got - 3 * x**2) == 0


def test_noncommuting_x_over_x_plus_y():
    x, y = _xy()
    r = multivariate_control(x / (x + y), [(x, 0), (y, 0)])
    assert set(r) >= {"commuting", "order_a", "order_b", "note"}
    assert r["commuting"] is False
    assert r["order_a"] == 0
    assert r["order_b"] == 1
    assert r["order_a"] != r["order_b"]
    assert r["status"] == COMPARED
    assert "order" in r["note"].lower()
    assert "FAMILY_ZERO" not in r["note"]
    assert r["cross_terms_agree"] is False


def test_commuting_polynomial_both_orders_zero():
    x, y = _xy()
    r = multivariate_control(x + y, [(x, 0), (y, 0)])
    assert r["commuting"] is True
    assert r["order_a"] == 0
    assert r["order_b"] == 0
    assert r["status"] == COMPARED
    assert "not a verifier" in r["note"].lower()
    assert "FAMILY_ZERO" not in str(r)
    assert r["mixed_derivatives_agree"] is True
    assert r["cross_terms_agree"] is True


def test_large_expr_unknown_never_zero():
    x, y = _xy()
    expr = sum((x + y) ** i for i in range(1, 20))
    assert sympy.count_ops(expr, visual=False) > OPS_CAP
    r = multivariate_control(expr, [(x, 0), (y, 0)])
    assert r["commuting"] is None
    assert r["order_a"] is None
    assert r["order_b"] is None
    assert r["status"] == UNKNOWN
    assert "UNKNOWN" in r["note"]
    assert iterated_limits(expr, [(x, 0), (y, 0)]) is None
    assert r.get("verdict") not in {"ZERO", "FAMILY_ZERO"}


def test_iterated_agreement_is_not_joint_certificate():
    x, y = _xy()
    r = multivariate_control(x * y / (x**2 + y**2), [(x, 0), (y, 0)])
    assert r["commuting"] is True
    assert r["order_a"] == 0
    assert r["order_b"] == 0
    note = r["note"].lower()
    assert "not a verifier" in note
    assert "joint" in note
    assert "FAMILY_ZERO" not in r["note"]


def test_mixed_derivatives_polynomial():
    x, y = _xy()
    r = multivariate_control(x**2 * y + y**3, [(x, 0), (y, 0)])
    assert r["mixed_derivatives_agree"] is True
    assert r["commuting"] is True
    assert r["order_a"] == 0
    assert r["order_b"] == 0


def test_mixed_partials_of_formula_can_commute_when_limits_do_not():
    x, y = _xy()
    r = multivariate_control(x / (x + y), [(x, 0), (y, 0)])
    assert r["commuting"] is False
    assert r["mixed_derivatives_agree"] is True


def test_control_never_emits_family_zero():
    x, y = _xy()
    for expr, steps in (
        (x + y, [(x, 0), (y, 0)]),
        (x / (x + y), [(x, 0), (y, 0)]),
        ((x**3 - y**3) / (x - y), [(y, x)]),
    ):
        r = multivariate_control(expr, steps)
        blob = repr(r)
        assert "FAMILY_ZERO" not in blob
        assert r.get("verdict") != "ZERO"
        assert r.get("family_verdict") is None


def test_garbage_and_empty_are_unknown():
    x, y = _xy()
    assert iterated_limits(x + y, []) is None
    assert iterated_limits("???", [(x, 0)]) is None
    r = multivariate_control(None, [(x, 0), (y, 0)])
    assert r["commuting"] is None
    assert r["status"] == UNKNOWN


def test_source_has_no_family_composer():
    src = inspect.getsource(control_mod)
    assert "compose_family_verdict" not in src
    assert "check_limit" not in src
    assert "FAMILY_ZERO" not in src
