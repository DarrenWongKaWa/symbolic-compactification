"""One-parameter edge verifier. Timeout/size is UNKNOWN, never ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.edges import (  # noqa: E402
    FULL_OPS_CAP,
    LIMIT_OPS_CAP,
    NONZERO,
    UNKNOWN,
    ZERO,
    OneParameterCertificate,
    certify_one_parameter,
)
from research.scalable_verification.api import (  # noqa: E402
    NONZERO as SV_NONZERO,
    UNKNOWN as SV_UNKNOWN,
    ZERO as SV_ZERO,
)
from research.scalable_verification.confluence import engine as confluence_engine  # noqa: E402
from symbolic_compactification.budgets import BudgetExceeded  # noqa: E402
import research.iterated_confluence.edges.certify as cert_mod  # noqa: E402


def _xy():
    return sympy.symbols("x y")


def _edge(source, target, variable, target_value, symbols=None, functions=None):
    return certify_one_parameter(
        source, target, variable, target_value, symbols, functions,
    )


def _package_py() -> str:
    here = Path(cert_mod.__file__).resolve().parent
    parts = []
    for path in sorted(here.glob("*.py")):
        parts.append(path.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_public_api_and_verdict_constants():
    assert ZERO == SV_ZERO == "ZERO"
    assert NONZERO == SV_NONZERO == "NONZERO"
    assert UNKNOWN == SV_UNKNOWN == "UNKNOWN"
    assert callable(certify_one_parameter)
    sig = inspect.signature(certify_one_parameter)
    assert list(sig.parameters) == [
        "source",
        "target",
        "variable",
        "target_value",
        "symbols",
        "functions",
    ]
    assert FULL_OPS_CAP == 250
    assert LIMIT_OPS_CAP == 80
    assert FULL_OPS_CAP != 0
    assert LIMIT_OPS_CAP != 0


def test_source_ban_no_guo_pairing():
    src = _package_py()
    assert "guo_map" not in src
    assert "Phi_Gamma" not in src
    assert "if family_id == guo" not in src
    assert 'family_id == "guo"' not in src
    assert "family_id == 'guo'" not in src
    assert "split_multiplicative" in src
    assert "check_limit" in src
    assert "certify_edge" in src
    assert "sympy.limit(" not in src


def test_cubic_newton_confluence_is_zero():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), 3 * x**2, y, x, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.verdict != UNKNOWN
    assert isinstance(r, OneParameterCertificate)
    assert isinstance(r.provenance, str) and r.provenance
    assert isinstance(r.steps, tuple) and r.steps
    assert r.full_ops >= r.local_ops >= 0
    assert r.reduction_ratio == pytest.approx(r.local_ops / r.full_ops if r.full_ops else 1.0)


def test_corrupted_cubic_newton_is_nonzero():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), 4 * x**2, y, x, ["x", "y"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_spectator_h1_split_then_limit_is_zero():
    x, y = _xy()
    h1 = sympy.Function("h1")
    source = h1(x) * ((x**3 - y**3) / (x - y))
    target = h1(x) * 3 * x**2
    r = _edge(source, target, y, x, ["x", "y"], ["h1"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.verdict != UNKNOWN
    assert r.split_certified is True
    assert any("certified" in s and "split" in s for s in r.steps)
    assert r.local_ops < r.full_ops
    assert r.reduction_ratio < 1.0
    assert "check_limit" in r.provenance or any("check_limit" in s for s in r.steps)


def test_split_first_even_when_full_ops_exceeds_250():
    x, y = _xy()
    h1 = sympy.Function("h1")
    spectator = h1(sum(x**i for i in range(1, 140)))
    source = spectator * ((x**3 - y**3) / (x - y))
    target = spectator * 3 * x**2
    assert max(int(sympy.count_ops(source, visual=False)), int(sympy.count_ops(target, visual=False))) > 250
    r = _edge(source, target, y, x, ["x", "y"], ["h1"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.verdict != UNKNOWN
    assert r.full_ops > 250
    assert r.local_ops < 80
    assert r.split_certified is True
    assert any("certified" in s and "split" in s for s in r.steps)


def test_timeout_is_unknown_never_zero(monkeypatch):
    def _boom(*_a, **_k):
        raise BudgetExceeded("confluence_limit", 8.0)

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    r = _edge(sympy.exp(1 / (y - x)), sympy.Integer(0), y, x, ["x", "y"])
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO
    assert "timeout" in r.provenance or any("timeout" in s for s in r.steps)


def test_size_guard_monkeypatch_is_unknown_never_zero(monkeypatch):
    monkeypatch.setattr(cert_mod, "_ops_too_large_local", lambda *_e: True)
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), 3 * x**2, y, x, ["x", "y"])
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO
    assert r.provenance == "size_guard"


def test_huge_unsplit_expr_is_unknown_never_zero():
    x = sympy.symbols("x")
    fat = sum(sympy.symbols(f"a0:{FULL_OPS_CAP + 40}"))
    r = _edge(fat, 3 * x**2, x, x, None)
    assert r.full_ops > FULL_OPS_CAP
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO
    assert r.provenance == "size_guard"
    assert r.split_certified is False


def test_no_unbudgeted_sympy_limit_on_large_ops(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("sympy.limit must not run without budget when count_ops > 80")

    monkeypatch.setattr(sympy, "limit", _boom)
    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    fat = sum(x**i for i in range(1, 50))
    F = sympy.exp(1 / (y - x)) * fat
    assert int(sympy.count_ops(F, visual=False)) > 80
    r = _edge(F, sympy.Integer(0), y, x, ["x", "y"])
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO


def test_parse_failure_is_unknown():
    r = _edge("not a formula ???", "0", "y", "x", ["x", "y"])
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert r.provenance == "parse"


def test_result_carries_ops_and_steps():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), 3 * x**2, y, x, ["x", "y"])
    payload = r.to_dict()
    assert payload["verdict"] == ZERO
    assert "full_ops" in payload and "local_ops" in payload
    assert "reduction_ratio" in payload
    assert payload["steps"] == list(r.steps) or tuple(payload["steps"]) == r.steps
