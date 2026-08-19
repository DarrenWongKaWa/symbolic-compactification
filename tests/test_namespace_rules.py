"""Generic regression tests for namespace policy, rewrite rules and
telemetry sanity (v0.2).

Synthetic content only. Covers:
* the three-namespace policy: declared symbols vs declared functions vs
  built-ins — explicit declaration beats built-in (allow_reserved opt-in),
  hard-reserved names stay rejected everywhere (FUNCTION_NAME_RESERVED);
* assumption-aware rewrite rules (rules.py): gating on declared
  assumptions, fail-closed non-application on gaps;
* step-record telemetry / engine-version sanity through the session API.
"""
import pytest
import sympy

from symbolic_compactification import (ENGINE_VERSION, NONZERO, ZERO,
                                       AdapterError, BUILTIN_RULES,
                                       ExpressionRecord, RewriteRule,
                                       StepRecord, apply_rule,
                                       init_session, load_session,
                                       normalize_symbols, parse_expression,
                                       record_step, verify_equivalent)


# --------------------------------------------------------------------------- #
# namespace policy: symbols vs functions vs built-ins
# --------------------------------------------------------------------------- #

def test_declared_symbol_shadowing_function_builtin_with_opt_in():
    # "sin" declared as a SYMBOL with the explicit allow_reserved opt-in:
    # explicit declaration beats built-in, and it verifies as a symbol.
    expr = parse_expression("sin + 1", ["sin"], allow_reserved=True)
    assert expr == sympy.Symbol("sin", real=True) + 1
    result = verify_equivalent("sin + x", "x + sin", ["sin", "x"],
                               allow_reserved=True)
    assert result.verdict == ZERO


def test_declared_symbol_shadowing_builtin_without_opt_in_rejected():
    with pytest.raises(AdapterError) as excinfo:
        normalize_symbols(["sin"])
    assert excinfo.value.code == "SYMBOL_NAME_RESERVED"
    # verifier path: fail-closed UNKNOWN carrying the same code
    result = verify_equivalent("sin + 1", "1 + sin", ["sin"])
    assert result.verdict == "UNKNOWN"
    codes = {e.get("code") for e in result.evidence}
    assert "SYMBOL_NAME_RESERVED" in codes


def test_hard_reserved_symbol_rejected_even_with_opt_in():
    for name in ("pi", "E", "I", "Sum", "Piecewise", "Rational"):
        with pytest.raises(AdapterError) as excinfo:
            normalize_symbols([name], allow_reserved=True)
        assert excinfo.value.code == "SYMBOL_NAME_RESERVED"


def test_declared_function_shadowing_function_builtin():
    # "log" declared as an undefined FUNCTION shadows the log builtin:
    # explicit declaration beats built-in along the function axis.
    expr = parse_expression("log(x)", [{"name": "x", "real": True,
                                        "nonzero": False}],
                            functions=["log"])
    assert isinstance(expr, sympy.core.function.AppliedUndef)
    assert type(expr).__name__ == "log"
    result = verify_equivalent("log(x) + 1", "1 + log(x)", ["x"],
                               functions=["log"])
    assert result.verdict == ZERO


def test_declared_function_cannot_shadow_hard_reserved():
    for name in ("Sum", "Piecewise", "pi", "Rational"):
        with pytest.raises(AdapterError) as excinfo:
            parse_expression("x", ["x"], functions=[name])
        assert excinfo.value.code == "FUNCTION_NAME_RESERVED"


def test_declared_function_colliding_with_declared_symbol_rejected():
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("f(x)", ["f", "x"], functions=["f"])
    assert excinfo.value.code == "FUNCTION_NAME_COLLIDES_WITH_SYMBOL"


def test_malformed_function_declarations_rejected():
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("x", ["x"], functions="f")
    assert excinfo.value.code == "CLAIM_FUNCTIONS_MALFORMED"
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("x", ["x"], functions=["f", "f"])
    assert excinfo.value.code == "CLAIM_FUNCTIONS_MALFORMED"
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("x", ["x"], functions=["not an ident"])
    assert excinfo.value.code == "CLAIM_FUNCTIONS_MALFORMED"


# --------------------------------------------------------------------------- #
# rules.py: assumption gating
# --------------------------------------------------------------------------- #

def _rule_by_name(name):
    return next(r for r in BUILTIN_RULES if r.name == name)


def test_conjugate_rule_applies_only_for_declared_real():
    rule = _rule_by_name("conjugate_real_identity")
    x = sympy.Symbol("x")
    applied = apply_rule(rule, sympy.conjugate(x),
                         [{"name": "x", "real": True}])
    assert applied.applied
    assert applied.after == x

    skipped = apply_rule(rule, sympy.conjugate(x),
                         [{"name": "x", "real": False}])
    assert not skipped.applied
    assert skipped.after == sympy.conjugate(x)


def test_re_rule_applies_only_for_declared_real():
    rule = _rule_by_name("re_real_identity")
    x = sympy.Symbol("x")
    applied = apply_rule(rule, sympy.re(x), [{"name": "x", "real": True}])
    assert applied.applied
    assert applied.after == x


def test_sqrt_square_abs_rule_is_generic():
    rule = _rule_by_name("sqrt_square_abs")
    x = sympy.Symbol("x")
    applied = apply_rule(rule, sympy.sqrt(x**2), ["y"])
    assert applied.applied
    assert applied.after == sympy.Abs(x)


def test_fixed_requirement_gap_is_never_bridged():
    rule = RewriteRule(name="needs_nonzero_x",
                       transform=lambda expr, syms: expr + 1,
                       required_assumptions={"x": "nonzero"})
    x = sympy.Symbol("x")

    gap = apply_rule(rule, x, [{"name": "x", "real": True}])
    assert not gap.applied
    assert gap.reason == "assumptions_insufficient"
    assert gap.missing_assumptions == ("x:nonzero",)
    assert gap.after == x

    ok = apply_rule(rule, x, [{"name": "x", "real": True,
                               "nonzero": True}])
    assert ok.applied
    assert ok.after == x + 1


def test_failing_rule_transform_is_a_non_match_never_an_exception():
    def _explode(expr, syms):
        raise RuntimeError("rule bug")

    rule = RewriteRule(name="buggy", transform=_explode)
    outcome = apply_rule(rule, sympy.Symbol("x"), ["x"])
    assert not outcome.applied
    assert outcome.reason == "no_change"


def test_verifier_level_assumption_gating_conjugate():
    # with x declared real the rewrite is valid -> ZERO
    real = verify_equivalent("conjugate(x)", "x",
                             [{"name": "x", "real": True}])
    assert real.verdict == ZERO
    # with x declared complex the same claim is refutable -> never ZERO
    complex_verdict = verify_equivalent("conjugate(x)", "x",
                                        [{"name": "x", "real": False}])
    assert complex_verdict.verdict != ZERO
    assert complex_verdict.verdict in (NONZERO, "UNKNOWN")


# --------------------------------------------------------------------------- #
# telemetry / engine-version sanity via the session API
# --------------------------------------------------------------------------- #

def test_step_records_carry_engine_version_and_telemetry(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    record = ExpressionRecord(text="x", sha256="0" * 64,
                              symbols=[{"name": "x", "real": True,
                                        "nonzero": False}])
    telemetry = {
        "input_chars": 1, "output_chars": 1,
        "count_ops_before": 0, "count_ops_after": 0,
        "primitive": None, "wall_time_seconds": 0.001,
        "verdict": ZERO, "timeout_status": None,
        "engine_version": ENGINE_VERSION,
    }
    step = StepRecord(step=1, current_hash="a" * 64,
                      candidate_hash="b" * 64, candidate_text="x",
                      residual="0", verdict=ZERO, status="CERTIFIED",
                      telemetry=telemetry)
    record_step(session, step)

    loaded = load_session(str(tmp_path), session.run_id)
    assert len(loaded.steps) == 1
    got = loaded.steps[0]
    assert got.engine_version == "0.2.0"
    assert ENGINE_VERSION == "0.2.0"
    assert got.status == "CERTIFIED"
    assert got.telemetry == telemetry
    for key in ("input_chars", "output_chars", "count_ops_before",
                "count_ops_after", "primitive", "wall_time_seconds",
                "verdict", "timeout_status", "engine_version"):
        assert key in got.telemetry
    # provenance field is always present (git sha or the documented fallback)
    assert isinstance(got.engine_git_sha, str) and got.engine_git_sha


def test_invalid_step_status_rejected():
    with pytest.raises(AdapterError) as excinfo:
        StepRecord(step=1, current_hash="a", candidate_hash="b",
                   candidate_text="x", residual="0", verdict=ZERO,
                   status="PROVEN")
    assert excinfo.value.code == "STEP_STATUS_INVALID"
