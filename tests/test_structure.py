"""Generic regression tests for structure-first preservation (v0.2).

Synthetic content only. Covers:
* ``expand_finite`` — the explicitly DIAGNOSTIC finite-N replay;
* ``structure_summary`` — cheap structural inspection;
* the scoping rule that a finite-N check is NEVER a proof for symbolic
  bounds: a generalization that holds at a concrete N but is false
  symbolically must not be certified ZERO.
"""
import pytest
import sympy

from symbolic_compactification import (AdapterError, expand_finite,
                                       structure_summary, verify_equivalent)

N = sympy.Symbol("N", real=True)
n = sympy.Symbol("n", real=True)
x = sympy.Symbol("x", real=True)
f = sympy.Function("f")
g = sympy.Function("g")


# --------------------------------------------------------------------------- #
# expand_finite: diagnostic finite-N replay
# --------------------------------------------------------------------------- #

def test_expand_finite_expands_concrete_sum():
    expr = sympy.Sum(f(n), (n, 1, N))
    lowered = expand_finite(expr, {"N": 3})
    assert sympy.expand(lowered - (f(1) + f(2) + f(3))) == 0


def test_expand_finite_substitutes_bounds_in_plain_expressions():
    lowered = expand_finite(N * x + 1, {"N": 2})
    assert lowered == 2 * x + 1


def test_expand_finite_rejects_non_mapping_bounds():
    with pytest.raises(AdapterError) as excinfo:
        expand_finite(x, [("N", 2)])
    assert excinfo.value.code == "BOUNDS_MALFORMED"


def test_expand_finite_rejects_non_integer_values():
    with pytest.raises(AdapterError) as excinfo:
        expand_finite(x, {"N": 2.0})
    assert excinfo.value.code == "BOUNDS_MALFORMED"
    with pytest.raises(AdapterError) as excinfo:
        expand_finite(x, {"N": True})
    assert excinfo.value.code == "BOUNDS_MALFORMED"


# --------------------------------------------------------------------------- #
# structure_summary
# --------------------------------------------------------------------------- #

def test_structure_summary_reports_structural_content():
    expr = (sympy.Sum(f(n), (n, 1, N))
            + sympy.Piecewise((x, x > 0), (-x, x < 0))
            + g(x, n))
    summary = structure_summary(expr)
    assert summary["sums"] == 1
    assert summary["piecewise"] == 1
    assert summary["piecewise_branches"] == 2
    assert summary["indexed_calls"] == 2           # f(n) and g(x, n)
    assert summary["indexed_names"] == ["f", "g"]
    assert set(summary["free_symbols"]) == {"N", "n", "x"}
    assert summary["count_ops"] > 0


def test_structure_summary_of_flat_expression_is_empty_structurally():
    summary = structure_summary(x + 1)
    assert summary["sums"] == 0
    assert summary["products"] == 0
    assert summary["piecewise"] == 0
    assert summary["indexed_calls"] == 0
    assert summary["indexed_names"] == []


# --------------------------------------------------------------------------- #
# diagnostic scope: finite agreement is NEVER symbolic certification
# --------------------------------------------------------------------------- #

def test_finite_true_but_symbolically_false_claim_is_not_certified():
    """Claim: Sum(n, (n, 1, N)) == N + 1.

    TRUE at the concrete value N = 2 (both sides are 3) yet FALSE for
    symbolic N. The finite-N diagnostic agrees at N = 2; the symbolic
    verifier must still refuse to certify (verdict NONZERO or UNKNOWN,
    never ZERO).
    """
    lhs = sympy.Sum(n, (n, 1, N))
    rhs = N + 1

    # the finite diagnostic (legitimately) shows agreement at N = 2 ...
    assert expand_finite(lhs, {"N": 2}) == expand_finite(rhs, {"N": 2})

    # ... but symbolic adjudication must NOT certify the generalization.
    result = verify_equivalent(str(lhs), str(rhs), ["N", "n"])
    assert result.verdict != "ZERO"
    assert result.verdict in ("NONZERO", "UNKNOWN")


def test_finite_diagnostic_agreement_never_substitutes_for_proof():
    """A second, independently false generalization: agreement at N = 1
    only. Verdict must again stay out of ZERO."""
    lhs = sympy.Sum(n**2, (n, 1, N))      # 1 at N = 1
    rhs = sympy.Integer(1)                # constant 1: equal only at N = 1
    assert expand_finite(lhs, {"N": 1}) == expand_finite(rhs, {})

    result = verify_equivalent(str(lhs), str(rhs), ["N", "n"])
    assert result.verdict != "ZERO"


def test_symbolically_true_identity_still_certifies_with_expansion_unused():
    """Control: a genuinely symbolic identity still reaches ZERO without
    relying on the finite diagnostic at all (expand_finite never called)."""
    lhs = sympy.Sum(f(n) + g(n), (n, 1, N))
    rhs = sympy.Sum(f(n), (n, 1, N)) + sympy.Sum(g(n), (n, 1, N))
    result = verify_equivalent(str(lhs), str(rhs), ["N", "n"],
                               functions=["f", "g"])
    assert result.verdict == "ZERO"
