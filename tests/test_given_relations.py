"""A step checked under relations the paper states (Guo-style 'X -> Y using R')."""
from __future__ import annotations

import pytest
import sympy

from symbolic_compactification.manybody.given import verify_identity_given

pytestmark = pytest.mark.release_critical

VEL = ["v12a", "v21a", "v12b", "v21b", "v12c", "v21c", "v1b", "v1c", "e12", "gab", "gac"]


def test_step_that_needs_no_relation_is_exact():
    out = verify_identity_given("a*(b + c)", "a*b + a*c", [("a", "b")], symbols=["a", "b", "c"])
    assert out["verdict"] == "ZERO" and out["given_used"] == []


def test_metric_velocity_step_holds_under_the_stated_relation():
    # K_1A = v_1^c (v21a v12b + v12a v21b) + v_1^b (...) = 2 e12^2 (v_1^c g_ab + v_1^b g_ac)
    lhs = "v1c*(v21a*v12b + v12a*v21b) + v1b*(v21a*v12c + v12a*v21c)"
    rhs = "2*e12**2*(v1c*gab + v1b*gac)"
    relations = [("v12a*v21b + v12b*v21a", "2*e12**2*gab"),
                 ("v12a*v21c + v12c*v21a", "2*e12**2*gac")]
    out = verify_identity_given(lhs, rhs, relations, symbols=VEL)
    assert out["verdict"] == "ZERO"
    assert out["given_used"] == [0, 1]
    cert = out["certificate"]
    # the certificate is checkable by hand: residual = sum(cofactor_i * relation_i)
    residual = sympy.sympify(f"({lhs}) - ({rhs})")
    combo = sum(sympy.sympify(q) * (sympy.sympify(l) - sympy.sympify(r))
                for q, (l, r) in zip(cert["cofactors"], relations))
    assert sympy.expand(residual - combo) == 0


def test_without_the_relation_the_same_step_is_not_exact():
    lhs = "v1c*(v21a*v12b + v12a*v21b)"
    out = verify_identity_given(lhs, "2*e12**2*v1c*gab", [], symbols=VEL)
    assert out["verdict"] != "ZERO"


def test_rational_step_records_the_denominator():
    out = verify_identity_given("x*a/(b*c)", "x/d", [("b*c", "a*d")], symbols=["a", "b", "c", "d", "x"])
    assert out["verdict"] == "ZERO"
    assert out["certificate"]["nonzero"]          # b*c*d != 0 is part of the claim


def test_step_that_fails_under_the_relation_has_a_counterexample_satisfying_it():
    out = verify_identity_given("x + y", "2*x", [("y", "x**2")], symbols=["x", "y"])
    assert out["verdict"] == "NONZERO"
    point = {sympy.Symbol(k): sympy.Rational(v) for k, v in out["counterexample"].items()}
    x, y = sympy.symbols("x y")
    assert point[y] == point[x] ** 2                # the stated relation holds there
    assert (point[x] + point[y]) != 2 * point[x]     # and the step does not


def test_a_relation_that_restates_the_step_is_refused():
    out = verify_identity_given("a*b + c", "d*e", [("d*e", "a*b + c")], symbols=["a", "b", "c", "d", "e"])
    assert out["verdict"] == "UNKNOWN"
    assert "GIVEN_RESTATES_THE_STEP" in out["reasons"]


def test_substituting_a_stated_definition_is_a_step():
    # -(A12a A21b - A12b A21a) = -(-i Omega) using Omega = i (A12a A21b - A12b A21a)
    out = verify_identity_given("-(A12a*A21b - A12b*A21a)", "-(-I*Omega)",
                                [("Omega", "I*(A12a*A21b - A12b*A21a)")],
                                symbols=["A12a", "A21b", "A12b", "A21a", "Omega"])
    assert out["verdict"] == "ZERO" and out["given_used"] == [0]


def test_relation_that_does_not_reach_the_step_is_unknown_not_invalid():
    # nothing can be solved linearly: no counterexample is constructed
    out = verify_identity_given("x**2 + y**2", "1", [("x**2*y**2", "1")], symbols=["x", "y"])
    assert out["verdict"] == "UNKNOWN"


def test_contradictory_relations_are_not_used():
    # eps21 = -eps12 and eps21 = eps12 together force eps12 = 0: everything would 'hold'
    out = verify_identity_given("e12*x", "0", [("e21", "-e12"), ("e21", "e12")], symbols=["e12", "e21", "x"])
    assert out["verdict"] == "UNKNOWN"
    assert any(r.startswith(("GIVEN_FORCES_ZERO", "GIVEN_INCONSISTENT")) for r in out["reasons"])


def test_inconsistent_relations_are_not_used():
    out = verify_identity_given("x", "y", [("a", "1"), ("a", "2")], symbols=["a", "x", "y"])
    assert out["verdict"] == "UNKNOWN" and out["reasons"] == ["GIVEN_INCONSISTENT"]


def test_a_stated_zero_is_a_condition_not_a_contradiction():
    out = verify_identity_given("x + mu*y", "x", [("mu", "0")], symbols=["x", "y", "mu"])
    assert out["verdict"] == "ZERO"


def test_relations_that_make_a_denominator_vanish_prove_nothing():
    # with ea = eb every denominator (ea - eb) is zero: the 'identity' is vacuous
    out = verify_identity_given("1/(ea - eb)", "ea/((ea - eb)*eb)", [("ea", "eb")],
                                symbols=["ea", "eb"])
    assert out["verdict"] == "UNKNOWN"
    assert "GIVEN_MAKES_A_DENOMINATOR_VANISH" in out["reasons"]


def test_counterexample_respects_declared_positivity():
    # y = -x has no solution with x, y > 0: no counterexample may be reported
    out = verify_identity_given("x + y", "2*x", [("y", "-x")], symbols=["x", "y"], positive=("x", "y"))
    assert out["verdict"] != "NONZERO"


def test_trivial_and_contradictory_constant_relations_do_not_crash():
    assert verify_identity_given("x", "y", [("a", "a")], symbols=["a", "x", "y"])["verdict"] != "ZERO"
    out = verify_identity_given("x", "y", [("1", "2")], symbols=["x", "y"])
    assert out["verdict"] == "UNKNOWN" and out["reasons"] == ["GIVEN_INCONSISTENT"]


def test_huge_constants_do_not_crash():
    out = verify_identity_given("10**400*x", "10**400*y", [("x", "z")], symbols=["x", "y", "z"])
    assert out["verdict"] in ("NONZERO", "UNKNOWN")


def test_counterexample_keeps_real_symbols_real():
    # x = i y has no real solution but x = y = 0: no counterexample for real x, y
    out = verify_identity_given("x", "y", [("x", "I*y")], symbols=["x", "y"])
    assert out["verdict"] != "NONZERO"


def test_counterexample_assigns_symbols_that_cancelled():
    # mu eliminated through the relation; A cancels from the residual but stays in the relation
    out = verify_identity_given("w + mu*A", "w + 2", [("mu*A", "3")], symbols=["w", "mu", "A"])
    assert out["verdict"] == "NONZERO"
    point = {k: sympy.Rational(v) for k, v in out["counterexample"].items()}
    assert point["mu"] * point["A"] == 3


def test_unused_declared_functions_do_not_block_a_counterexample():
    # Eq. (28) of math-ph/0303052: 64 printed where 69 follows, with lambda^2 = 3 A^2 mu / 4
    lhs = ("omega**2 + 3*A**2*mu/4 - 3*A**4*mu**2/(128*(omega**2 + lamda**2))"
           " + 3*A**4*mu**2*(3*A**2*mu - 4*lamda**2)/(512*(lamda**2 + omega**2)**2)")
    rhs = "(64*A**4*mu**2 + 192*A**2*mu*omega**2 + 128*omega**4)/(96*A**2*mu + 128*omega**2)"
    out = verify_identity_given(lhs, rhs, [("lamda**2", "3*A**2*mu/4")], symbols=["A", "mu", "omega", "lamda"],
                                functions=["s_3"])
    assert out["verdict"] == "NONZERO"
    fixed = rhs.replace("64*A**4", "69*A**4")
    assert verify_identity_given(lhs, fixed, [("lamda**2", "3*A**2*mu/4")], symbols=["A", "mu", "omega", "lamda"],
                                 functions=["s_3"])["verdict"] == "ZERO"


def test_definitions_with_denominators_are_substituted():
    # alpha_0..alpha_3 of math-ph/0303052, Eq. (31): the sum of the stated alphas
    rels = [("alpha_0", "omega**2 + lamda**2"), ("alpha_1", "3*A**2*mu/4 - lamda**2"),
            ("alpha_2", "-3*A**4*mu**2/(128*(omega**2 + lamda**2))"),
            ("alpha_3", "3*A**4*mu**2*(3*A**2*mu - 4*lamda**2)/(512*(lamda**2 + omega**2)**2)")]
    rhs = ("omega**2 + 3*A**2*mu/4 - 3*A**4*mu**2/(128*(omega**2 + lamda**2))"
           " + 3*A**4*mu**2*(3*A**2*mu - 4*lamda**2)/(512*(lamda**2 + omega**2)**2)")
    out = verify_identity_given("alpha_0 + alpha_1 + alpha_2 + alpha_3", rhs, rels,
                                symbols=["A", "mu", "omega", "lamda", "alpha_0", "alpha_1", "alpha_2", "alpha_3"])
    assert out["verdict"] == "ZERO" and sorted(out["given_used"]) == [0, 1, 2, 3]
