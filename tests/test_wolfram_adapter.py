"""Generic regression tests for the Wolfram-text ingestion adapter (v0.2).

Synthetic content only: generic symbol/function names (x, y, n, N, K, f, h).
Covers comment stripping (incl. nesting), decimal -> Rational conversion,
constants (Pi/I), square-bracket calls, structural Sum/Piecewise/indexed
preservation, PolyGamma mapping, configuration assumption lists, and the
fail-closed error ladder for malformed input.
"""
import pytest
import sympy

from symbolic_compactification import (ZERO, AdapterError,
                                       translate_wolfram_text,
                                       verify_equivalent)
from symbolic_compactification.adapters.wolfram_text import (
    WolframStructureError, WolframSyntaxError, WolframTokenError,
    strip_wolfram_comments)


# --------------------------------------------------------------------------- #
# comments
# --------------------------------------------------------------------------- #

def test_simple_comment_stripped():
    assert strip_wolfram_comments("x (* note *) + 1") == "x  + 1"


def test_nested_comments_stripped():
    text = "x + (* outer (* inner *) still comment *) 1"
    assert strip_wolfram_comments(text) == "x +  1"


def test_deeply_nested_comment_round_trip():
    text = "(* a (* b (* c *) b *) a *) y + 2"
    result = translate_wolfram_text(text)
    assert result.expr == sympy.Symbol("y", real=True) + 2


def test_comment_only_input_is_empty():
    with pytest.raises(AdapterError) as excinfo:
        translate_wolfram_text("(* nothing but a comment *)")
    assert excinfo.value.code == "EMPTY_EXPRESSION"


# --------------------------------------------------------------------------- #
# numbers, constants, calls
# --------------------------------------------------------------------------- #

def test_decimal_becomes_exact_rational():
    result = translate_wolfram_text("0.5*x")
    assert result.expr == sympy.Rational(1, 2) * sympy.Symbol("x", real=True)
    # no floats anywhere in the translated tree
    assert not result.expr.atoms(sympy.Float)


def test_multi_digit_decimal_is_rational():
    result = translate_wolfram_text("2.25")
    assert result.expr == sympy.Rational(9, 4)


def test_integer_stays_integer():
    result = translate_wolfram_text("42")
    assert result.expr == sympy.Integer(42)


def test_pi_and_imaginary_unit_constants():
    assert translate_wolfram_text("Pi").expr == sympy.pi
    result = translate_wolfram_text("I*y", complex_symbols=("y",))
    assert result.expr == sympy.I * sympy.Symbol("y", real=False)


def test_square_bracket_calls_map_to_sympy():
    result = translate_wolfram_text("Sin[x]")
    assert result.expr == sympy.sin(sympy.Symbol("x", real=True))
    nested = translate_wolfram_text("Exp[Sin[x]]")
    assert nested.expr == sympy.exp(sympy.sin(sympy.Symbol("x", real=True)))


def test_power_and_unary_minus():
    result = translate_wolfram_text("-x^2 + (x + 1)^2")
    x = sympy.Symbol("x", real=True)
    assert sympy.expand(result.expr) == sympy.expand(-x**2 + (x + 1)**2)


# --------------------------------------------------------------------------- #
# assumption configuration (real_symbols / complex_symbols / nonzero_symbols)
# --------------------------------------------------------------------------- #

def test_assumption_lists_drive_symbol_declarations():
    result = translate_wolfram_text("a + b + c",
                                    real_symbols=("a",),
                                    complex_symbols=("b",),
                                    nonzero_symbols=("c",))
    by_name = {s["name"]: s for s in result.symbols}
    assert by_name["a"]["real"] is True
    assert by_name["b"]["real"] is False
    assert by_name["c"]["nonzero"] is True


def test_real_declaration_wins_over_complex():
    result = translate_wolfram_text("a",
                                    real_symbols=("a",),
                                    complex_symbols=("a",))
    assert result.symbols == [{"name": "a", "real": True, "nonzero": False}]


# --------------------------------------------------------------------------- #
# structural Sum: symbolic bounds, never expanded
# --------------------------------------------------------------------------- #

def test_symbolic_sum_not_expanded():
    result = translate_wolfram_text("Sum[K*f[n], {n, 1, N}]")
    expr = result.expr
    assert isinstance(expr, sympy.Sum)
    body, (var, lo, hi) = expr.args[0], expr.limits[0]
    assert lo == sympy.Integer(1)
    assert hi == sympy.Symbol("N", real=True)          # symbolic upper bound
    assert var.name == "n"
    assert body == sympy.Symbol("K", real=True) * sympy.Function("f")(var)
    # iterator variable is BOUND: not a free symbol, but reported separately
    assert "n" not in {s["name"] for s in result.symbols}
    assert result.bound_symbols == ["n"]
    assert result.functions == ["f"]


def test_two_element_iterator_defaults_lower_bound_to_one():
    result = translate_wolfram_text("Sum[f[n], {n, N}]")
    (var, lo, hi) = result.expr.limits[0]
    assert lo == sympy.Integer(1)
    assert hi.name == "N"


def test_sum_malformed_iterator_fails_closed():
    with pytest.raises(WolframStructureError):
        translate_wolfram_text("Sum[f[n], n]")
    with pytest.raises(WolframStructureError):
        translate_wolfram_text("Sum[f[n], {n, 1, N, 2}]")


# --------------------------------------------------------------------------- #
# structural Piecewise: branches + conditions preserved
# --------------------------------------------------------------------------- #

def test_piecewise_branches_and_conditions_preserved():
    result = translate_wolfram_text("Piecewise[{{x, x > 0}, {-x, x < 0}}]")
    expr = result.expr
    assert isinstance(expr, sympy.Piecewise)
    x = sympy.Symbol("x", real=True)
    assert expr.args == ((x, x > 0), (-x, x < 0))


def test_piecewise_default_value_becomes_true_branch():
    result = translate_wolfram_text("Piecewise[{{1, x > 0}}, 0]")
    expr = result.expr
    assert expr.args[-1] == (sympy.Integer(0), sympy.S.true)


def test_piecewise_malformed_branch_fails_closed():
    with pytest.raises(WolframStructureError):
        translate_wolfram_text("Piecewise[{x}]")
    with pytest.raises(WolframStructureError):
        translate_wolfram_text("Piecewise[x > 0]")


# --------------------------------------------------------------------------- #
# indexed functions: structural round-trip through the strict parser
# --------------------------------------------------------------------------- #

def test_indexed_functions_survive_translation_round_trip():
    result = translate_wolfram_text("f[n] + h[a, n, m]")
    assert result.functions == ["f", "h"]
    assert isinstance(result.expr, sympy.Add)
    applied = list(result.expr.atoms(sympy.core.function.AppliedUndef))
    assert {type(a).__name__ for a in applied} == {"f", "h"}
    # round-trip: translated text re-parsed by the strict whitelist parser
    # with declared functions verifies against itself -> ZERO
    symbols = [s["name"] for s in result.symbols]
    verdict = verify_equivalent(result.text, result.text, symbols,
                                functions=result.functions)
    assert verdict.verdict == ZERO


# --------------------------------------------------------------------------- #
# PolyGamma: admitted by policy, translates and verifies a trivial identity
# --------------------------------------------------------------------------- #

def test_polygamma_translation_and_trivial_identity():
    result = translate_wolfram_text("PolyGamma[0, x]")
    assert result.expr == sympy.polygamma(0, sympy.Symbol("x", real=True))
    # trivial identity through the full strict pipeline -> ZERO
    verdict = verify_equivalent(result.text, result.text, ["x"])
    assert verdict.verdict == ZERO


def test_polygamma_benign_rewrite_verifies_zero():
    verdict = verify_equivalent("polygamma(0, x) + x", "x + polygamma(0, x)",
                                ["x"])
    assert verdict.verdict == ZERO


# --------------------------------------------------------------------------- #
# fail-closed ladder for malformed input
# --------------------------------------------------------------------------- #

def test_blank_input_empty_expression():
    with pytest.raises(AdapterError) as excinfo:
        translate_wolfram_text("   ")
    assert excinfo.value.code == "EMPTY_EXPRESSION"


def test_non_string_input_empty_expression():
    with pytest.raises(AdapterError) as excinfo:
        translate_wolfram_text(None)
    assert excinfo.value.code == "EMPTY_EXPRESSION"


def test_bad_character_is_token_error():
    with pytest.raises(WolframTokenError) as excinfo:
        translate_wolfram_text("x @@ y")
    assert excinfo.value.code == "WOLFRAM_TOKEN_ERROR"


@pytest.mark.parametrize("bad", [
    "x +",            # dangling operator
    "(x + 1",         # unbalanced parenthesis
    "x y",            # trailing input after a complete expression
    "[x]",            # bare leading bracket
    "f[x,",           # unterminated call
])
def test_grammar_violations_are_syntax_errors(bad):
    with pytest.raises(WolframSyntaxError) as excinfo:
        translate_wolfram_text(bad)
    assert excinfo.value.code == "WOLFRAM_SYNTAX_ERROR"


def test_bare_list_outside_structure_fails_closed():
    with pytest.raises(WolframStructureError) as excinfo:
        translate_wolfram_text("{1, 2, 3}")
    assert excinfo.value.code == "WOLFRAM_STRUCTURE_ERROR"


def test_unknown_mapped_function_fails_closed():
    with pytest.raises(AdapterError) as excinfo:
        translate_wolfram_text("NoSuchFn[x]",
                               func_map={"NoSuchFn": "definitely_not_sympy"})
    assert excinfo.value.code == "WOLFRAM_FUNC_UNKNOWN"


def test_expression_size_policy_enforced():
    with pytest.raises(AdapterError) as excinfo:
        translate_wolfram_text("x + 1", policy={"max_expr_chars": 3})
    assert excinfo.value.code == "EXPRESSION_TOO_LARGE"
