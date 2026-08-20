"""v0.3 consolidation contracts over neutral synthetic expressions."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import sympy

from symbolic_compactification import (
    ZERO,
    AdapterError,
    ExpressionRecord,
    StepRecord,
    adjudicate_candidate,
    build_conjecture_packet,
    init_session,
    load_expression,
    load_session,
    normalize_symbols,
    owned_children_snapshot,
    parse_expression,
    promote,
    record_step,
    render_final_report,
    run_with_budget,
    set_current,
    sha256_text,
    translate_wolfram_text,
    verify_equivalent,
)
from symbolic_compactification.adapters.wolfram_text import (
    WolframSyntaxError,
    extract_expression_text,
    strip_wolfram_comments,
)
from symbolic_compactification.cli import main as cli_main


def _record(text: str, symbols=("x",), functions=()) -> ExpressionRecord:
    declared = normalize_symbols(list(symbols))
    function_names = list(functions)
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        parsed_expr=parse_expression(
            text, declared, functions=function_names or None),
        symbols=declared,
        functions=function_names,
    )


def _nested_budget_call() -> int:
    return run_with_budget(sum, ((1, 2, 3),), seconds=5,
                           operation="nested-sum")


def test_promotion_binds_exact_zero_to_the_exact_candidate(tmp_path):
    session = init_session(str(tmp_path))
    current = _record("x")
    set_current(session, current)
    result = verify_equivalent("x", "x", ["x"])
    step = StepRecord(
        step=1, current_hash=current.sha256,
        candidate_hash=current.sha256, candidate_text=current.text,
        residual="0", verdict=ZERO, evidence=result.evidence,
        status="CERTIFIED", proof_status="PROVEN")
    record_step(session, step)

    with pytest.raises(AdapterError) as excinfo:
        promote(session, _record("x + 1"))
    assert excinfo.value.code == "CANDIDATE_STATE_MISMATCH"
    assert session.current.text == "x"


def test_report_rejects_alias_free_formula_that_differs_from_machine_state(
        tmp_path):
    session = init_session(str(tmp_path))
    set_current(session, _record("x**2 + 2*x + 1"))
    adjudicate_candidate(session, _record("(x+1)**2"))

    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session, human_form="x + 2")
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert any("contradicts" in item for item in excinfo.value.violators)


def test_declared_function_namespace_survives_session_reload(tmp_path):
    expression = tmp_path / "function.txt"
    expression.write_text("f(x)", encoding="utf-8")
    current = load_expression(expression, ["x"], functions=["f"])
    session = init_session(str(tmp_path))
    set_current(session, current)

    reloaded = load_session(str(tmp_path), session.run_id)
    assert reloaded.current.functions == ["f"]
    packet = build_conjecture_packet(reloaded)
    assert packet["structural_form"] == "f(x)"
    assert packet["declared_functions"] == ["f"]
    report = render_final_report(reloaded)
    assert report["human_render_verified"] is True


def test_symbol_assumptions_are_strict_and_order_is_canonical():
    with pytest.raises(AdapterError) as excinfo:
        normalize_symbols([{"name": "x", "real": "false"}])
    assert excinfo.value.code == "CLAIM_SYMBOLS_MALFORMED"

    left = normalize_symbols(["y", "x"])
    right = normalize_symbols(["x", "y"])
    assert left == right
    first = verify_equivalent("x + y", "x + y + 1", left)
    second = verify_equivalent("x + y", "x + y + 1", right)
    assert (first.verdict, first.residual, first.counterexample) == (
        second.verdict, second.residual, second.counterexample)


def test_parser_rejects_preconstruction_resource_bombs():
    with pytest.raises(AdapterError) as excinfo:
        parse_expression("2**10001", ["x"])
    assert excinfo.value.code == "EXPRESSION_TOO_LARGE"

    deeply_nested = "(" * 257 + "x" + ")" * 257
    with pytest.raises(AdapterError) as excinfo:
        parse_expression(deeply_nested, ["x"])
    assert excinfo.value.code == "EXPRESSION_TOO_LARGE"


def test_wolfram_multiline_product_and_comment_fail_closed():
    source = extract_expression_text(
        "out =\n Product[f[n], {n, 1, N}]\n + 1;")
    result = translate_wolfram_text(source)
    products = result.expr.atoms(sympy.Product)
    assert len(products) == 1
    assert result.bound_symbols == ["n"]
    assert result.functions == ["f"]

    with pytest.raises(WolframSyntaxError):
        strip_wolfram_comments("x + (* unfinished")
    with pytest.raises(WolframSyntaxError):
        strip_wolfram_comments("x *) + 1")


def test_packet_records_do_not_overwrite_without_intervening_steps(tmp_path):
    session = init_session(str(tmp_path))
    set_current(session, _record("x"))
    build_conjecture_packet(session, goal="first")
    build_conjecture_packet(session, goal="second")
    packets = Path(session.run_root) / "packets"
    first = json.loads((packets / "packet_001.json").read_text("utf-8"))
    second = json.loads((packets / "packet_002.json").read_text("utf-8"))
    assert first["goal"] == "first"
    assert second["goal"] == "second"


def test_pipeline_rejects_namespace_changes_and_current_replacement(tmp_path):
    session = init_session(str(tmp_path))
    current = _record("x")
    set_current(session, current)
    with pytest.raises(AdapterError) as excinfo:
        set_current(session, _record("x + 1"))
    assert excinfo.value.code == "CURRENT_ALREADY_SET"

    candidate = _record("x", symbols=("x",))
    candidate.symbols = normalize_symbols(
        [{"name": "x", "real": False, "nonzero": False}])
    with pytest.raises(AdapterError) as excinfo:
        adjudicate_candidate(session, candidate)
    assert excinfo.value.code == "DECLARED_ASSUMPTIONS_CHANGED"


def test_nested_process_budget_leaves_no_owned_workers():
    assert run_with_budget(
        _nested_budget_call, seconds=10, operation="outer") == 6
    assert owned_children_snapshot() == []


def test_cli_json_mode_is_single_machine_readable_object(tmp_path, capsys):
    current = tmp_path / "current.txt"
    candidate = tmp_path / "candidate.txt"
    symbols = tmp_path / "symbols.json"
    current.write_text("x + 1", encoding="utf-8")
    candidate.write_text("1 + x", encoding="utf-8")
    symbols.write_text('{"symbols": ["x"]}', encoding="utf-8")

    code = cli_main([
        "verify", "--current", str(current), "--candidate", str(candidate),
        "--symbols", str(symbols), "--json"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["result"]["verdict"] == ZERO


def test_run_id_path_traversal_is_rejected(tmp_path):
    with pytest.raises(AdapterError) as excinfo:
        load_session(str(tmp_path), "../../outside")
    assert excinfo.value.code == "RUN_ID_INVALID"
