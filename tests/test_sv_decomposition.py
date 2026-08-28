"""Track V / V1 proof-decomposition planner. Small polynomials only.

False composition acceptance must stay 0. The planner never assigns ZERO.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.api import STRATEGIES
from research.scalable_verification.decomposition import (
    DD_CERTIFICATE,
    EQUALITY,
    FACTOR_LOCAL,
    HERMITE_DD,
    LIMIT,
    NEWTON_DD,
    SERIES_LOCAL,
    certify_composition,
    certify_identical_cancel,
    decompose,
)

x, y, z = sympy.symbols("x y z")
FALSE_COMPOSITION = []


def _plan_blob(plan) -> str:
    return json.dumps(plan.to_dict(), sort_keys=True)


def _assert_open(plan, label: str) -> None:
    d = plan.to_dict()
    assert "verdict" not in d, (label, d)
    for step in d["steps"]:
        assert "verdict" not in step, (label, step)
        assert step["suggested_strategy"] in STRATEGIES, (label, step)
    for s in d["suggested_strategies"]:
        assert s in STRATEGIES, (label, s)
    blob = _plan_blob(plan)
    assert '"ZERO"' not in blob, (label, blob)
    assert '"NONZERO"' not in blob, (label, blob)


def _record_false(label: str, cond: bool) -> None:
    if cond:
        FALSE_COMPOSITION.append(label)
    assert not cond, label


# --------------------------------------------------------------------------- #
# Contract
# --------------------------------------------------------------------------- #


def test_plan_has_no_verdict_and_uses_strategies():
    plan = decompose(x * (x + 1), y * (x + 1), EQUALITY, assumptions=[sympy.Ne(x + 1, 0)])
    assert plan.steps
    _assert_open(plan, "contract")
    assert plan.relation == EQUALITY
    assert all(s.suggested_strategy in STRATEGIES for s in plan.steps)


def test_unknown_relation_is_unknown_strategy():
    plan = decompose(x, y, "NOT_A_RELATION")
    _assert_open(plan, "unknown_rel")
    assert "UNKNOWN" in plan.suggested_strategies
    assert plan.notes == ("unknown_relation",)


# --------------------------------------------------------------------------- #
# Spectator composition
# --------------------------------------------------------------------------- #


def test_equality_spectator_with_nonzero_assumption():
    s = x + 1
    a = x * s
    b = y * s
    plan = decompose(a, b, EQUALITY, assumptions=[sympy.Ne(s, 0)])
    _assert_open(plan, "spectator_assumed")
    assert plan.composition is not None
    assert plan.composition.exact is True
    assert plan.composition.equivalent is True
    assert sympy.expand(plan.composition.a_loc - x) == 0
    assert sympy.expand(plan.composition.b_loc - y) == 0
    assert sympy.expand(plan.composition.residual - (x - y)) == 0
    assert FACTOR_LOCAL in plan.suggested_strategies
    assert any(s.provenance == "residual_equality" for s in plan.steps)


def test_equality_constant_spectator():
    a = 2 * (x + 1)
    b = 2 * (y + 1)
    plan = decompose(a, b, EQUALITY)
    _assert_open(plan, "constant_spectator")
    assert plan.composition is not None
    assert plan.composition.exact is True
    assert plan.composition.equivalent is True
    assert plan.composition.status == "constant_nonzero"
    assert sympy.expand(plan.composition.residual - ((x + 1) - (y + 1))) == 0


def test_composition_residual_is_loc_difference():
    s = x + y
    a = (x - y) * s
    b = (2 * y) * s
    comp = certify_composition(a, b, s, assumptions=[sympy.Ne(s, 0)])
    assert comp is not None
    assert sympy.expand(comp.residual - (comp.a_loc - comp.b_loc)) == 0
    assert sympy.expand(comp.a_loc - (x - y)) == 0
    assert sympy.expand(comp.b_loc - 2 * y) == 0


def test_uncertified_spectator_does_not_swap_claim():
    s = x + 1
    a = x * s
    b = y * s
    plan = decompose(a, b, EQUALITY)
    _assert_open(plan, "uncertified")
    assert plan.composition is not None
    assert plan.composition.exact is True
    assert plan.composition.equivalent is False
    assert any("uncertified" in s.provenance or "uncertified" in "".join(s.notes) for s in plan.steps)


# --------------------------------------------------------------------------- #
# False composition (must be 0)
# --------------------------------------------------------------------------- #


def test_false_composition_wrong_spectator_rejected():
    a = x * (x + 1)
    b = y * (x + 2)
    got = certify_composition(a, b, x + 1)
    _record_false("wrong_spectator_x+1", got is not None)


def test_false_composition_no_invented_gcd():
    a = x * (x + 1)
    b = y * (x + 2)
    plan = decompose(a, b, EQUALITY)
    _assert_open(plan, "no_invented_gcd")
    _record_false("invented_spectator", plan.composition is not None and plan.composition.exact)


def test_false_composition_tautological_div_rejected():
    a = x * (x + 1)
    b = y * (x + 1)
    got = certify_composition(a, b, x + 2)
    _record_false("tautological_x+2", got is not None)


def test_false_identical_cancel_factor_absent_from_den():
    a = (x**2 - y**2) / (x - y)
    got = certify_identical_cancel(a, x + y)
    _record_false("cancel_x+y_from_den", got is not None)


def test_false_identical_cancel_factor_absent_from_num():
    a = (x - y) / (x**2 - y**2)
    got = certify_identical_cancel(a, x + y)
    # x+y divides den, not num — not a removable factor of the whole fraction
    _record_false("cancel_x+y_from_num_only", got is not None)


def test_false_composition_zero_spectator_rejected():
    got = certify_composition(x, y, 0)
    _record_false("zero_spectator", got is not None)


def test_false_composition_aggregate_is_zero():
    cases = [
        ("wrong_spectator_x+1", certify_composition(x * (x + 1), y * (x + 2), x + 1)),
        ("tautological_x+2", certify_composition(x * (x + 1), y * (x + 1), x + 2)),
        ("cancel_x+y_from_den", certify_identical_cancel((x**2 - y**2) / (x - y), x + y)),
        ("cancel_x+y_from_num_only", certify_identical_cancel((x - y) / (x**2 - y**2), x + y)),
        ("zero_spectator", certify_composition(x, y, 0)),
        (
            "invented_spectator",
            decompose(x * (x + 1), y * (x + 2), EQUALITY).composition,
        ),
    ]
    bad = [name for name, got in cases if got is not None]
    assert bad == [], bad
    assert FALSE_COMPOSITION == [], FALSE_COMPOSITION


# --------------------------------------------------------------------------- #
# LIMIT: identical cancel, no sympy.limit
# --------------------------------------------------------------------------- #


def test_limit_identical_cancel_without_sympy_limit(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("sympy.limit must not be called")

    monkeypatch.setattr(sympy, "limit", boom)
    a = (x**2 - y**2) / (x - y)
    b = 2 * y
    plan = decompose(a, b, LIMIT, var=x, to=y)
    _assert_open(plan, "limit_cancel")
    assert FACTOR_LOCAL in plan.suggested_strategies
    assert plan.composition is not None
    assert plan.composition.status == "identically_cancelled"
    local = [s for s in plan.steps if s.provenance == "limit_after_cancel"]
    assert local
    assert local[0].kind == EQUALITY
    assert sympy.expand(local[0].left - 2 * y) == 0


def test_limit_wrong_target_still_open():
    a = (x**2 - y**2) / (x - y)
    b = x + y
    plan = decompose(a, b, LIMIT, var=x, to=y)
    _assert_open(plan, "limit_wrong_b")
    local = [s for s in plan.steps if s.provenance == "limit_after_cancel"]
    assert local
    # local claim is 2y vs x+y; planner must not treat that as proven
    assert sympy.expand(local[0].left - 2 * y) == 0
    assert sympy.expand(local[0].right - (x + y)) == 0


def test_limit_remaining_indeterminate_suggests_series():
    a = (x - y) / (x - y) ** 2
    b = sympy.Integer(1)
    plan = decompose(a, b, LIMIT, var=x, to=y)
    _assert_open(plan, "limit_series")
    assert SERIES_LOCAL in plan.suggested_strategies
    assert any(s.kind == LIMIT and s.provenance == "limit_after_cancel" for s in plan.steps)


def test_limit_false_cancel_rejected():
    a = (x**2 - y**2) / (x - y)
    got = certify_identical_cancel(a, x + y)
    _record_false("limit_false_cancel", got is not None)


# --------------------------------------------------------------------------- #
# Newton / Hermite — suggest DD, do not ZERO
# --------------------------------------------------------------------------- #


def test_newton_dd_suggests_certificate_and_does_not_zero():
    a = (x**3 - y**3) / (x - y)
    b = x**2 + x * y + y**2
    plan = decompose(
        a, b, NEWTON_DD, latent=z**3, latent_var=z, nodes=[x, y]
    )
    _assert_open(plan, "newton")
    assert DD_CERTIFICATE in plan.suggested_strategies
    assert any(s.provenance == "newton_definition" for s in plan.steps)
    assert any(s.kind == NEWTON_DD for s in plan.steps)


def test_newton_wrong_sign_not_a_verdict():
    a = -(x**3 - y**3) / (x - y)
    b = x**2 + x * y + y**2
    plan = decompose(a, b, NEWTON_DD, latent=z**3, latent_var=z, nodes=[x, y])
    _assert_open(plan, "newton_sign")
    resid_steps = [s for s in plan.steps if s.residual is not None]
    assert resid_steps
    # residual of cancelled / original pair is not the zero polynomial
    assert any(not (s.residual == 0) for s in resid_steps if s.provenance in {"residual_dd", "residual_equality"})


def test_hermite_dd_suggests_certificate():
    a = 3 * x
    b = 3 * x
    plan = decompose(
        a,
        b,
        HERMITE_DD,
        latent=z**3,
        latent_var=z,
        nodes=[x],
        multiplicities=[3],
    )
    _assert_open(plan, "hermite")
    assert DD_CERTIFICATE in plan.suggested_strategies
    assert any(s.provenance == "hermite_definition" for s in plan.steps)


def test_identical_polynomials_still_no_verdict():
    a = x**2 + 2 * x * y + y**2
    b = (x + y) ** 2
    plan = decompose(a, b, EQUALITY)
    _assert_open(plan, "identical_polys")


def test_certify_composition_true_split_small_poly():
    comp = certify_composition(x * (x + 1), y * (x + 1), x + 1, assumptions=["nonzero:x+1"])
    assert comp is not None
    assert comp.exact is True
    assert comp.equivalent is True
    assert sympy.expand(comp.residual - (x - y)) == 0
