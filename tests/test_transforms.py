"""Generic regression tests for bounded structural primitives (v0.2).

Synthetic content only. Covers:
* ``combine_identical_sums`` certifying Sum(K*A) + Sum(K*B) == Sum(K*(A+B))
  via the exact verifier -> ZERO WITHOUT any concrete-index expansion;
* general symbolic factoring identities certified with no finite expansion;
* the remaining targeted primitives (factor/collect/together/cancel,
  argument canonicalization under explicit symmetry declarations);
* op-count caps and the ``TARGETED_PRIMITIVES`` roster.
"""
import sympy

from symbolic_compactification import (ZERO, TransformResult,
                                       canonicalize_equivalent_arguments,
                                       cancel, collect_common_factor,
                                       combine_identical_sums,
                                       factor_common_kernel, factor_terms,
                                       residual_of, together,
                                       verify_equivalent)
from symbolic_compactification.transforms import TARGETED_PRIMITIVES

K = sympy.Symbol("K", real=True)
N = sympy.Symbol("N", real=True)
n = sympy.Symbol("n", real=True)
x = sympy.Symbol("x", real=True)
y = sympy.Symbol("y", real=True)
f = sympy.Function("f")
g = sympy.Function("g")


# --------------------------------------------------------------------------- #
# combine_identical_sums: structural factoring of repeated kernels
# --------------------------------------------------------------------------- #

def test_combine_identical_sums_applies_and_keeps_structure_symbolic():
    expr = sympy.Sum(K * f(n), (n, 1, N)) + sympy.Sum(K * g(n), (n, 1, N))
    result = combine_identical_sums(expr)
    assert isinstance(result, TransformResult)
    assert result.applied
    assert result.primitive == "combine_identical_sums"
    # the result is STILL a symbolic Sum: no concrete-index expansion
    sums = result.after.atoms(sympy.Sum)
    assert len(sums) == 1
    assert N in result.after.free_symbols   # symbolic bound survived
    # local checkability: residual before - after expands to 0
    assert residual_of(result) == 0


def test_combine_identical_sums_certified_zero_without_expansion():
    """Sum(K*f) + Sum(K*g) == Sum(K*f + K*g) is certified by the exact
    verifier (ZERO) purely on the symbolic structure: no expand_finite, no
    concrete bound substitution anywhere in this test."""
    expr = sympy.Sum(K * f(n), (n, 1, N)) + sympy.Sum(K * g(n), (n, 1, N))
    result = combine_identical_sums(expr)
    assert result.applied
    verdict = verify_equivalent(str(result.before), str(result.after),
                                ["K", "N", "n"], functions=["f", "g"])
    assert verdict.verdict == ZERO


def test_combine_identical_sums_no_op_on_single_sum():
    expr = sympy.Sum(K * f(n), (n, 1, N)) + x
    result = combine_identical_sums(expr)
    assert not result.applied
    assert result.note == "no_identical_sum_limits"


def test_combine_identical_sums_no_op_on_non_add():
    result = combine_identical_sums(sympy.Sum(K * f(n), (n, 1, N)))
    assert not result.applied
    assert result.note == "not_an_Add"


def test_distinct_limits_are_not_combined():
    expr = (sympy.Sum(f(n), (n, 1, N))
            + sympy.Sum(g(n), (n, 1, N + 1)))
    result = combine_identical_sums(expr)
    assert not result.applied


# --------------------------------------------------------------------------- #
# general symbolic factoring WITHOUT any concrete-index expansion
# --------------------------------------------------------------------------- #

def test_symbolic_factoring_identity_certified_without_expansion():
    """K*f(n) + K*g(n) == K*(f(n) + g(n)): a general factoring identity on
    structural (indexed) content, certified ZERO with symbolic bounds only;
    expand_finite is never invoked."""
    expr = K * f(n) + K * g(n)
    result = factor_common_kernel(expr)
    assert result.applied
    assert result.after == K * (f(n) + g(n))
    verdict = verify_equivalent(str(result.before), str(result.after),
                                ["K", "n"], functions=["f", "g"])
    assert verdict.verdict == ZERO


def test_factoring_outside_a_symbolic_sum_certified_zero():
    """K*Sum(f) + K*Sum(g) == K*(Sum(f) + Sum(g)): common-kernel collection
    over STRUCTURAL sums, again certified with no concrete-index expansion."""
    expr = (K * sympy.Sum(f(n), (n, 1, N))
            + K * sympy.Sum(g(n), (n, 1, N)))
    result = collect_common_factor(expr)
    assert result.applied
    verdict = verify_equivalent(str(result.before), str(result.after),
                                ["K", "N", "n"], functions=["f", "g"])
    assert verdict.verdict == ZERO
    # the structural Sum nodes survived the transform
    assert len(result.after.atoms(sympy.Sum)) == 2


def test_factor_terms_primitive_round_trip_zero():
    expr = 2 * x + 2 * y
    result = factor_terms(expr)
    assert result.applied
    assert residual_of(result) == 0
    verdict = verify_equivalent(str(result.before), str(result.after),
                                ["x", "y"])
    assert verdict.verdict == ZERO


# --------------------------------------------------------------------------- #
# together / cancel / factor round-trips
# --------------------------------------------------------------------------- #

def test_together_common_denominator_round_trip():
    expr = x / y + 1 / y
    result = together(expr)
    assert result.applied
    verdict = verify_equivalent(str(result.before), str(result.after),
                                [{"name": "x", "real": True, "nonzero": False},
                                 {"name": "y", "real": True, "nonzero": True}])
    assert verdict.verdict == ZERO


def test_cancel_common_factor_round_trip():
    expr = (x**2 - 1) / (x - 1)
    result = cancel(expr)
    assert result.applied
    assert result.after == x + 1
    verdict = verify_equivalent(str(result.before), str(result.after),
                                [{"name": "x", "real": True, "nonzero": False}])
    assert verdict.verdict == ZERO


# --------------------------------------------------------------------------- #
# argument canonicalization: only declared-symmetric functions
# --------------------------------------------------------------------------- #

def test_canonicalize_only_for_declared_symmetric_functions():
    s = sympy.Function("s")
    expr = s(y, x)
    result = canonicalize_equivalent_arguments(
        expr, symmetric_functions=frozenset({"s"}))
    assert result.applied
    assert result.after == s(x, y)


def test_canonicalize_refuses_without_symmetry_declaration():
    expr = f(y, x)
    result = canonicalize_equivalent_arguments(expr)
    assert not result.applied
    assert result.note == "no_symmetric_functions_declared"
    assert result.after == expr


def test_canonicalize_leaves_undeclared_functions_untouched():
    s = sympy.Function("s")
    expr = f(y, x) + s(y, x)
    result = canonicalize_equivalent_arguments(
        expr, symmetric_functions=frozenset({"s"}))
    assert result.applied
    # f is NOT declared symmetric: its argument order is untouched
    assert result.after == f(y, x) + s(x, y)


# --------------------------------------------------------------------------- #
# policy: op-count caps and the targeted-primitive roster
# --------------------------------------------------------------------------- #

def test_ops_cap_discards_over_cap_candidates():
    result = factor_common_kernel(x**2 + 2 * x + 1, ops_cap=1)
    assert not result.applied
    assert result.note == "ops_cap_exceeded"


def test_transform_result_to_dict_is_json_native():
    result = factor_common_kernel(x**2 + 2 * x + 1)
    payload = result.to_dict()
    assert payload["primitive"] == "factor_common_kernel"
    assert payload["applied"] is True
    assert isinstance(payload["before"], str)
    assert isinstance(payload["after"], str)


def test_targeted_primitives_roster():
    names = [p.__name__ for p in TARGETED_PRIMITIVES]
    assert names == ["combine_identical_sums", "collect_common_factor",
                     "together", "cancel"]
