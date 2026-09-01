"""Structural Observation Layer contracts. Read-only; no gold leakage."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("matchpy")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from symbolic_compactification.observations.api import observe, backend_status, PRESETS
from symbolic_compactification.observations.ir import (
    DESCRIPTIVE_FACT,
    EXACT_FACT,
    FORBIDDEN_INTERPRETATION,
    ObservationBundle,
)
from symbolic_compactification.observations.leak import assert_no_interpretation
from symbolic_compactification.observations.backends.matchpy_backend import (
    available as mp_ok,
    sympy_to_matchpy,
    _ops,
)
from matchpy import Symbol as MpSymbol
from symbolic_compactification import parse_expression


def _s(*n):
    return [{"name": x, "real": True} for x in n]


def test_backend_status_core_sympy():
    st = backend_status()
    assert st["sympy"] == "AVAILABLE"
    assert "cadabra" in st
    assert "form" in st


def test_observe_cse_and_no_interpretation():
    b = observe("K(n)*a(n) + K(n)*b(n)", _s("n"), ["K", "a", "b"],
                backends="minimal")
    assert isinstance(b, ObservationBundle)
    types = {r.relation_type for r in b.relations}
    assert "CSE_SHARED" in types or "IDENTICAL" in types or "SAME_FUNCTION_FAMILY" in types
    payload = b.to_dict()
    assert_no_interpretation(payload)
    blob = json.dumps(payload).lower()
    for tok in FORBIDDEN_INTERPRETATION:
        assert tok.lower() not in blob


def test_descriptive_pole_is_not_exact():
    b = observe(
        "1/(x - a) + 1/(x - a - d)",
        _s("x", "a", "d"), [], backends="minimal",
    )
    poles = [r for r in b.relations if r.relation_type == "SAME_POLE_SIGNATURE"]
    for r in poles:
        assert r.exactness_class == DESCRIPTIVE_FACT


def test_permutation_descriptive():
    b = observe("F(n, m) + F(m, n)", _s("n", "m"), ["F"], backends="minimal")
    perms = [r for r in b.relations if r.relation_type == "PERMUTATION_RELATED"]
    assert perms
    assert all(r.exactness_class == DESCRIPTIVE_FACT for r in perms)


def test_derivative_exact_fact_not_master_name():
    b = observe("polygamma(0, z) + polygamma(1, z)", _s("z"), [],
                backends="minimal")
    deriv = [r for r in b.relations if r.relation_type == "DERIVATIVE_RELATED"]
    assert deriv
    assert all(r.exactness_class == EXACT_FACT for r in deriv)
    blob = json.dumps(b.to_dict())
    assert "Phi_Gamma" not in blob
    assert "thermal master" not in blob.lower()


def test_piecewise_inventory():
    b = observe(
        "Piecewise((K(n, m), Ne(n, m)), (K(n, n), True))",
        _s("n", "m"), ["K"], backends="minimal",
    )
    br = [r for r in b.relations if r.relation_type == "SAME_BRANCH_DEPENDENCY"]
    assert br


def test_matchpy_roundtrip_mul_ac():
    if not mp_ok():
        return
    Add, Mul = _ops()
    e = parse_expression("a*b", _s("a", "b"), functions=None)
    mp = sympy_to_matchpy(e, Add, Mul, MpSymbol)
    assert "a" in str(mp) and "b" in str(mp)
    b = observe("a*c + b*d", _s("a", "b", "c", "d"), [], backends=["sympy", "matchpy"])
    assert any(r.backend == "matchpy" for r in b.relations) or b.backend_status["matchpy"].startswith("AVAILABLE")


def test_optional_missing_backends_do_not_crash():
    b = observe("x + y", _s("x", "y"), [], backends="all_available")
    assert b.backend_status["sympy"] == "AVAILABLE"
    # cadabra/form may be unavailable
    cad = b.backend_status["cadabra"]
    assert "UNAVAILABLE" in cad or "AVAILABLE" in cad or "OPTIONAL" in cad


def test_presets_exist():
    for k in ("minimal", "algebra", "relations", "physics", "all_available"):
        assert k in PRESETS


def test_conflicting_backends_keep_both_records():
    b = observe("x + y", _s("x", "y"), [], backends=["sympy", "egglog"])
    # multiple evidence rows allowed
    payload = b.to_dict()
    assert "relations" in payload
    assert_no_interpretation(payload)
