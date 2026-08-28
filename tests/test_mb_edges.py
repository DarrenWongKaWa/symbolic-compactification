"""Local edge certifier cascade. Timeout/size is UNKNOWN, never ZERO."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

import pytest
import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.edges import (  # noqa: E402
    NONZERO,
    UNKNOWN,
    ZERO,
    EdgeCertificate,
    certify_edge,
)
from research.multibranch_verification.schema import EDGE_RELATIONS  # noqa: E402
from research.representation_invention.dd import newton_first  # noqa: E402
from research.scalable_verification.api import (  # noqa: E402
    NONZERO as SV_NONZERO,
    UNKNOWN as SV_UNKNOWN,
    ZERO as SV_ZERO,
)
from research.scalable_verification.confluence import engine as confluence_engine  # noqa: E402
from symbolic_compactification.budgets import BudgetExceeded  # noqa: E402
import research.multibranch_verification.edges.certify as cert_mod  # noqa: E402


def _xy():
    return sympy.symbols("x y")


def _cubic():
    z, x, y = sympy.symbols("z x y")
    return z**3, z, x, y


def _edge(source, target, relation, variable, target_value, symbols=None, functions=None):
    return certify_edge(
        source, target, relation, variable, target_value, symbols, functions,
    )


def test_public_api_and_verdict_constants():
    assert ZERO == SV_ZERO == "ZERO"
    assert NONZERO == SV_NONZERO == "NONZERO"
    assert UNKNOWN == SV_UNKNOWN == "UNKNOWN"
    assert callable(certify_edge)
    sig = inspect.signature(certify_edge)
    assert list(sig.parameters)[:7] == [
        "source_expr",
        "target_expr",
        "relation",
        "variable",
        "target_value",
        "symbols",
        "functions",
    ]
    for name in (
        "limit",
        "substitution",
        "derivative",
        "dd_recurrence",
        "hermite_dd_recurrence",
        "one_parameter_confluence",
        "repeated_node_confluence",
    ):
        assert name in EDGE_RELATIONS


def test_no_guo_pairing():
    src = inspect.getsource(cert_mod)
    assert "guo_map" not in src
    assert "GUO" not in src
    assert "Phi_Gamma" not in src
    assert "split_multiplicative" in src
    assert "check_limit" in src
    assert "hermite_xxx_ok" in src


# --------------------------------------------------------------------------- #
# Positives: cubic Newton / confluence toys
# --------------------------------------------------------------------------- #


def test_substitution_continuous_is_zero():
    x, y = _xy()
    r = _edge(x + y, 2 * x, "substitution", y, x, ["x", "y"])
    assert r.verdict == ZERO
    assert r.provenance == "substitution"
    assert r.verdict != UNKNOWN


def test_confluence_difference_of_squares_to_2x():
    x, y = _xy()
    r = _edge((x**2 - y**2) / (x - y), 2 * x, "limit", y, x, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.verdict != UNKNOWN
    assert r.provenance in {"cancel", "together", "check_limit:together_cancel"}


def test_one_parameter_confluence_alias():
    x, y = _xy()
    r = _edge((x**2 - y**2) / (x - y), 2 * x, "one_parameter_confluence", y, x, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()


def test_cubic_newton_closed_form_cancel():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), x**2 + x * y + y**2, "substitution", None, None, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.provenance == "cancel"


def test_cubic_newton_confluence_to_3x2():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), 3 * x**2, "repeated_node_confluence", y, x, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.provenance in {"cancel", "together", "check_limit:together_cancel"}


def test_cubic_derivative_repeated_node():
    F, z, x, _y = _cubic()
    r = _edge(F, 3 * x**2, "derivative", z, x, ["z", "x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.provenance == "derivative"


def test_cubic_hermite_xxx_via_dd_cert():
    F, z, x, _y = _cubic()
    r = _edge(F, 3 * x, "hermite_dd_recurrence", z, x, ["z", "x"])
    assert r.verdict == ZERO, r.to_dict()
    assert r.provenance.startswith("dd_cert") or r.provenance == "derivative"


def test_cubic_newton_first_via_dd_cert():
    F, z, x, y = _cubic()
    r = _edge(F, (x**3 - y**3) / (x - y), "dd_recurrence", z, None, ["z", "x", "y"])
    assert r.verdict == ZERO, r.to_dict()
    assert "dd_cert" in r.provenance


def test_cubic_repeated_via_dd_cert():
    F, z, x, _y = _cubic()
    r = _edge(F, 3 * x**2, "dd_recurrence", z, x, ["z", "x"])
    assert r.verdict == ZERO, r.to_dict()


def test_string_cubic_hermite_parses():
    r = _edge("z**3", "3*x", "hermite_dd_recurrence", "z", "x", ["z", "x"], None)
    assert r.verdict == ZERO, r.to_dict()


def test_split_multiplicative_then_limit():
    x, y = _xy()
    source = (x + 1) * (x**2 - y**2) / (x - y)
    target = (x + 1) * 2 * x
    r = _edge(source, target, "limit", y, x, ["x", "y"])
    assert r.verdict == ZERO, r.to_dict()


def test_exp_first_dd_via_check_limit(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("sympy.limit must not be required on this toy")

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    z = sympy.symbols("z")
    F = newton_first(sympy.exp(z), z, x, y)
    r = _edge(F, sympy.exp(x), "limit", y, x, ["x", "y", "z"])
    assert r.verdict == ZERO, r.to_dict()
    assert "check_limit" in r.provenance or r.provenance in {"cancel", "together", "substitution"}


def test_result_carries_provenance_and_local_edge():
    x, y = _xy()
    r = _edge((x**2 - y**2) / (x - y), 2 * x, "limit", y, x, ["x", "y"])
    assert isinstance(r, EdgeCertificate)
    assert isinstance(r.provenance, str) and r.provenance
    assert isinstance(r.steps, tuple) and r.steps
    payload = r.to_dict()
    assert payload["verdict"] == ZERO
    edge = r.to_local_edge()
    assert edge.verdict == ZERO
    assert edge.relation == "limit"
    assert edge.variable == "y"


# --------------------------------------------------------------------------- #
# Negatives: wrong target, pole — never ZERO
# --------------------------------------------------------------------------- #


def test_wrong_confluence_target_is_nonzero():
    x, y = _xy()
    r = _edge((x**2 - y**2) / (x - y), 3 * x, "limit", y, x, ["x", "y"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_non_removable_pole_is_nonzero():
    x, y = _xy()
    r = _edge(1 / (x - y), sympy.Integer(0), "limit", y, x, ["x", "y"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_wrong_newton_closed_form_is_nonzero():
    x, y = _xy()
    r = _edge((x**3 - y**3) / (x - y), x**2 + y**2, "substitution", None, None, ["x", "y"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_wrong_hermite_target_is_nonzero():
    F, z, x, _y = _cubic()
    r = _edge(F, 6 * x, "hermite_dd_recurrence", z, x, ["z", "x"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_wrong_derivative_is_nonzero():
    F, z, x, _y = _cubic()
    r = _edge(F, 6 * x, "derivative", z, x, ["z", "x"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


def test_wrong_sign_newton_dd_is_nonzero():
    F, z, x, y = _cubic()
    r = _edge(F, -(x**3 - y**3) / (x - y), "dd_recurrence", z, None, ["z", "x", "y"])
    assert r.verdict == NONZERO, r.to_dict()
    assert r.verdict != ZERO


# --------------------------------------------------------------------------- #
# Fail closed: timeout / size / parse → UNKNOWN, never ZERO
# --------------------------------------------------------------------------- #


def test_timeout_is_unknown_never_zero(monkeypatch):
    def _boom(*_a, **_k):
        raise BudgetExceeded("confluence_limit", 8.0)

    monkeypatch.setattr(confluence_engine, "_budgeted_sympy_limit", _boom)
    x, y = _xy()
    r = _edge(sympy.exp(1 / (y - x)), sympy.Integer(0), "limit", y, x, ["x", "y"])
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO
    assert "timeout" in r.provenance or any("timeout" in s for s in r.steps)


def test_size_guard_is_unknown_never_zero(monkeypatch):
    monkeypatch.setattr(cert_mod, "_ops_too_large", lambda *_e: True)
    x, y = _xy()
    r = _edge((x**2 - y**2) / (x - y), 2 * x, "limit", y, x, ["x", "y"])
    assert r.verdict == UNKNOWN, r.to_dict()
    assert r.verdict != ZERO
    assert r.provenance == "size_guard"


def test_parse_failure_is_unknown():
    r = _edge("not a formula ???", "0", "limit", "y", "x", ["x", "y"])
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
    assert r.provenance == "parse"


def test_missing_sides_unknown():
    x = sympy.symbols("x")
    r = _edge(None, x, "substitution", None, None, ["x"])
    assert r.verdict == UNKNOWN
    assert r.verdict != ZERO
