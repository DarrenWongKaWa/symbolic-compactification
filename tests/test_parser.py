"""Strict-parser safety regression tests (fail-closed whitelist ingestion).

Scientifically neutral: only generic symbols (x, y, a, b, t) and standard
operations. Every rejection path must surface as an AdapterError carrying a
stable machine-readable ``.code``; the parser must never evaluate code.
"""
from __future__ import annotations

import hashlib

import pytest
import sympy

from symbolic_compactification import (
    AdapterError,
    get_parse_policy,
    load_expression,
    normalize_symbols,
    parse_expression,
    set_parse_policy,
)

# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #


@pytest.fixture()
def restore_policy():
    """Snapshot the module-level parse policy and restore it after the test."""
    snapshot = get_parse_policy()
    yield
    set_parse_policy(
        max_expr_chars=snapshot["max_expr_chars"],
        max_nodes=snapshot["max_nodes"],
        max_symbols=snapshot["max_symbols"],
        allowed_functions=snapshot["allowed_functions"],
    )


def expect_error(code: str, fn):
    """Run ``fn`` and assert it raises AdapterError with exactly ``code``."""
    with pytest.raises(AdapterError) as excinfo:
        fn()
    assert excinfo.value.code == code
    return excinfo.value


# --------------------------------------------------------------------------- #
# happy path
# --------------------------------------------------------------------------- #

def test_parses_generic_polynomial():
    expr = parse_expression("x**2 + 2*x + 1", ["x"])
    x = sympy.Symbol("x", real=True)
    assert expr == x**2 + 2 * x + 1
    assert {str(s) for s in expr.free_symbols} == {"x"}


def test_declared_assumptions_respected():
    real_expr = parse_expression("x", [{"name": "x", "real": True}])
    complex_expr = parse_expression("x", [{"name": "x", "real": False}])
    assert list(real_expr.free_symbols)[0].is_real is True
    assert list(complex_expr.free_symbols)[0].is_real is False


def test_caret_is_converted_to_power():
    assert parse_expression("x^2", ["x"]) == parse_expression("x**2", ["x"])


def test_whitelisted_functions_and_constants():
    expr = parse_expression("sin(x) + exp(x) + pi + E + I", ["x"])
    assert expr.has(sympy.sin) and expr.has(sympy.exp)


# --------------------------------------------------------------------------- #
# symbol declaration safety
# --------------------------------------------------------------------------- #

def test_undeclared_symbol_rejected():
    expect_error("UNDECLARED_OR_DISALLOWED_NAME",
                 lambda: parse_expression("x + y", ["x"]))


def test_undeclared_function_like_name_rejected():
    expect_error("UNDECLARED_OR_DISALLOWED_NAME",
                 lambda: parse_expression("foo(x)", ["x"]))


@pytest.mark.parametrize("reserved", ["sin", "E", "pi", "Rational"])
def test_reserved_name_as_symbol_rejected(reserved):
    expect_error("SYMBOL_NAME_RESERVED",
                 lambda: parse_expression("x", [reserved]))


@pytest.mark.parametrize("bad_symbols", [
    "x",                       # not a list
    [1],                       # non-string, non-dict entry
    [],                        # empty declaration
    ["x", "x"],                # duplicate names
    [""],                      # blank name
    [{"real": True}],          # dict without a name
])
def test_malformed_symbol_declaration_rejected(bad_symbols):
    expect_error("CLAIM_SYMBOLS_MALFORMED",
                 lambda: parse_expression("x", bad_symbols))


def test_too_many_symbols_rejected():
    names = [f"s{i}" for i in range(41)]
    expect_error("CLAIM_SYMBOLS_TOO_MANY",
                 lambda: parse_expression("s0", names))


# --------------------------------------------------------------------------- #
# injection / character-gate safety
# --------------------------------------------------------------------------- #

def test_semicolon_injection_rejected():
    # ";" is outside the character gate; nothing after it is ever parsed
    expect_error("DISALLOWED_CHARACTERS",
                 lambda: parse_expression("x; import os", ["x"]))


def test_dunder_call_injection_rejected():
    expect_error("DISALLOWED_CHARACTERS",
                 lambda: parse_expression("__import__('os')", ["x"]))


def test_attribute_access_rejected():
    # "." passes the character gate (decimal literals), but the dunder
    # identifier is never declared, so the name gate must reject it
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("x.__class__", ["x"])
    assert excinfo.value.code in {"DISALLOWED_CHARACTERS",
                                  "UNDECLARED_OR_DISALLOWED_NAME",
                                  "SYMBOLIC_PARSE_FAILED"}


@pytest.mark.parametrize("text", ["x @ y", "x = 1", "x[0]", "x & y"])
def test_disallowed_characters_rejected(text):
    expect_error("DISALLOWED_CHARACTERS",
                 lambda: parse_expression(text, ["x"]))


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_empty_expression_rejected(text):
    expect_error("EMPTY_EXPRESSION",
                 lambda: parse_expression(text, ["x"]))


def test_non_string_expression_rejected():
    expect_error("EMPTY_EXPRESSION", lambda: parse_expression(None, ["x"]))
    expect_error("EMPTY_EXPRESSION", lambda: parse_expression(3, ["x"]))


# --------------------------------------------------------------------------- #
# size gates (policy overrides)
# --------------------------------------------------------------------------- #

def test_oversized_input_rejected_via_policy_override(restore_policy):
    set_parse_policy(max_expr_chars=6)
    expect_error("EXPRESSION_TOO_LARGE",
                 lambda: parse_expression("x + x + x", ["x"]))


def test_oversized_input_rejected_via_per_call_policy():
    expect_error("EXPRESSION_TOO_LARGE",
                 lambda: parse_expression("x + x + x", ["x"],
                                          policy={"max_expr_chars": 4}))


def test_oversized_node_count_rejected(restore_policy):
    set_parse_policy(max_nodes=1)
    # distinct symbols so the sum does not auto-collapse to a single term
    expect_error("EXPRESSION_TOO_LARGE",
                 lambda: parse_expression("x + y + t", ["x", "y", "t"]))


def test_policy_unknown_key_rejected():
    expect_error("PARSE_POLICY_KEY_UNKNOWN",
                 lambda: set_parse_policy(bogus_key=1))
    expect_error("PARSE_POLICY_KEY_UNKNOWN",
                 lambda: parse_expression("x", ["x"], policy={"bogus_key": 1}))


# --------------------------------------------------------------------------- #
# normalize_symbols canonical form
# --------------------------------------------------------------------------- #

def test_normalize_symbols_string_shorthand_defaults():
    assert normalize_symbols(["x"]) == [{"name": "x", "real": True,
                                         "nonzero": False}]


def test_normalize_symbols_keeps_explicit_assumptions():
    out = normalize_symbols([{"name": "a", "real": False, "nonzero": True}])
    assert out == [{"name": "a", "real": False, "nonzero": True}]


def test_implicit_multiplication_is_not_silently_accepted():
    # "2x" passes the identifier gate as a single identifier "2x" (which is
    # not a declared symbol). Fail-closed requires a rejection here; silently
    # evaluating it as 2*x would accept input the user never validated.
    with pytest.raises(AdapterError):
        parse_expression("2x", ["x"])


# --------------------------------------------------------------------------- #
# file ingestion (read-only, raw-byte hashing)
# --------------------------------------------------------------------------- #

def test_load_expression_hashes_raw_bytes_and_reads_only(tmp_path):
    src = tmp_path / "expr.txt"
    src.write_text("x + 1\n", encoding="utf-8")
    rec = load_expression(str(src), ["x"])
    assert rec.text == "x + 1"
    assert rec.sha256 == hashlib.sha256(b"x + 1\n").hexdigest()
    assert rec.parsed_expr is not None
    # the source file must never be modified by ingestion
    assert src.read_text(encoding="utf-8") == "x + 1\n"


def test_load_expression_missing_file_rejected(tmp_path):
    expect_error("EXPRESSION_SOURCE_UNREADABLE",
                 lambda: load_expression(str(tmp_path / "nope.txt"), ["x"]))
