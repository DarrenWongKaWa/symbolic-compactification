"""v0.2.2 audit-delta: FINAL CERTIFIED FORM reporting delta.

Deterministic, neutral synthetic fixtures only. Covers the v0.2.2 reporting
increments on top of ``test_reporting.py``:

* finalize/render writes BOTH artifacts: the machine form
  ``final/certified_expression.txt`` (canonical certified text) AND the
  human artifact ``final/FINAL_CERTIFIED_FORM.md``; the report carries
  ``certified_expression_path`` and ``human_render_verified`` (asserted
  True on the verified synthetic case).
* the v0.2.2 forbidden tokens ``"omitted"`` and ``"see JSON"`` in the
  human form or any definition raise ``REPORT_INCOMPLETE`` with the
  offenders listed, alongside the existing ``{...}`` / TODO / "same kernel"
  rejections.
* the CLI ``finalize`` path writes both artifacts as well.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import sympy

from symbolic_compactification import (
    CERTIFIED_EXPRESSION_NAME,
    FINAL_ARTIFACT_NAME,
    ZERO,
    AdapterError,
    ExpressionRecord,
    StepRecord,
    normalize_symbols,
    parse_expression,
    record_step,
    render_final_report,
    set_current,
    sha256_text,
    verify_equivalent,
)
from symbolic_compactification.cli import main as cli_main
from symbolic_compactification.session import init_session, promote


# --------------------------------------------------------------------------- #
# helpers: a synthetic certified run (self-contained)
# --------------------------------------------------------------------------- #

def _record(text: str, symbols=("x",)) -> ExpressionRecord:
    declared = normalize_symbols(list(symbols))
    parsed = parse_expression(text, declared)
    return ExpressionRecord(
        text=text,
        sha256=sha256_text(text),
        source_path=None,
        parsed_expr=parsed,
        symbols=declared,
    )


def _verification_step(session, candidate_rec, result, status: str):
    return StepRecord(
        step=len(session.steps) + 1,
        current_hash=session.current.sha256,
        candidate_hash=candidate_rec.sha256,
        candidate_text=candidate_rec.text,
        residual=result.residual,
        verdict=result.verdict,
        evidence=list(result.evidence),
        status=status,
        telemetry={
            "input_chars": len(session.current.text),
            "output_chars": len(candidate_rec.text),
            "count_ops_before": sympy.count_ops(session.current.parsed_expr),
            "count_ops_after": sympy.count_ops(candidate_rec.parsed_expr),
            "primitive": None,
            "wall_time_seconds": result.seconds,
            "verdict": result.verdict,
            "timeout_status": None,
        },
    )


def _certified_run(workspace_root, current_text="x**2 + 2*x + 1",
                   certified_text="(x+1)**2", symbols=("x",)):
    """Script a real ZERO-gated promotion: ingest -> verify ZERO -> promote.

    Returns ``(session, run_root, certified_record)``.
    """
    session = init_session(workspace_root=str(workspace_root))
    current = _record(current_text, symbols)
    set_current(session, current)

    candidate = _record(certified_text, symbols)
    result = verify_equivalent(current.text, candidate.text, list(symbols))
    assert result.verdict == ZERO, "fixture run must certify via ZERO"
    record_step(session, _verification_step(
        session, candidate, result, status="CERTIFIED"))
    promote(session, candidate)

    run_root = Path(workspace_root) / "runs" / session.run_id
    return session, run_root, candidate


# --------------------------------------------------------------------------- #
# dual artifacts: machine form + human form
# --------------------------------------------------------------------------- #

def test_render_writes_both_machine_and_human_artifacts(tmp_path):
    session, run_root, candidate = _certified_run(tmp_path)

    report = render_final_report(session)

    # machine artifact: the canonical certified expression text, one formula
    machine_path = run_root / "final" / CERTIFIED_EXPRESSION_NAME
    assert machine_path.is_file(), "certified_expression.txt was not written"
    assert machine_path.read_text(encoding="utf-8") == candidate.text + "\n"
    assert report["certified_expression_path"] == str(machine_path)
    assert report["certified_expression_path"].endswith(
        f"final/{CERTIFIED_EXPRESSION_NAME}")

    # human artifact: written alongside, referenced by the report
    human_path = run_root / "final" / FINAL_ARTIFACT_NAME
    assert human_path.is_file(), "FINAL_CERTIFIED_FORM.md was not written"
    assert report["artifact_path"] == str(human_path)
    assert candidate.text in human_path.read_text(encoding="utf-8")


def test_human_render_verified_true_on_verified_synthetic_case(tmp_path):
    """The verified synthetic run: the human form is programmatically
    derivable from the certified AST and the expansion check verifies, so
    human_render_verified is True — never a silent claim."""
    session, run_root, _ = _certified_run(tmp_path)
    report = render_final_report(session)
    assert report["expansion_check"] == "verified"
    assert report["human_render_verified"] is True

    # same holds with fully supplied, consistent definitions
    report = render_final_report(
        session, human_form="K1", definitions={"K1": "(x+1)**2"})
    assert report["expansion_check"] == "verified"
    assert report["human_render_verified"] is True


def test_cli_finalize_writes_both_artifacts(tmp_path, capsys):
    session, run_root, candidate = _certified_run(tmp_path)

    exit_code = cli_main([
        "finalize", "--run", session.run_id, "--workspace", str(tmp_path)])
    assert exit_code == 0
    capsys.readouterr()

    machine_path = run_root / "final" / CERTIFIED_EXPRESSION_NAME
    human_path = run_root / "final" / FINAL_ARTIFACT_NAME
    assert machine_path.is_file()
    assert human_path.is_file()
    assert machine_path.read_text(encoding="utf-8") == candidate.text + "\n"


# --------------------------------------------------------------------------- #
# v0.2.2 forbidden tokens: "omitted" / "see JSON"
# --------------------------------------------------------------------------- #

def test_omitted_token_in_definition_is_report_incomplete(tmp_path):
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session, human_form="K1",
                            definitions={"K1": "lower-order terms omitted"})
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert any("omitted" in v for v in excinfo.value.violators)


def test_see_json_token_in_human_form_is_report_incomplete(tmp_path):
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        # "see JSON" plus undefined identifiers: every offender is listed
        render_final_report(session, human_form="see JSON for the formula")
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert any("see JSON" in v for v in excinfo.value.violators)
    assert excinfo.value.violators, "offenders must be listed"


def test_forbidden_tokens_rejected_alongside_existing_placeholders(tmp_path):
    """'omitted'/'see JSON' join the existing {...}/TODO/'same kernel'
    rejections: all five hand-waving shapes fail closed with offenders."""
    session, run_root, _ = _certified_run(tmp_path)

    cases = [
        ("K1", {"K1": "the rest is omitted"}),          # omitted
        ("K1 + see JSON", {}),                          # see JSON
        ("(x+1)**2 + {rest}", {}),                      # brace placeholder
        ("K1", {"K1": "(x+1)**2  # TODO: finish"}),     # TODO marker
        ("K1", {"K1": "same kernel as before"}),        # same-kernel waving
    ]
    for human_form, definitions in cases:
        with pytest.raises(AdapterError) as excinfo:
            render_final_report(session, human_form=human_form,
                                definitions=definitions)
        assert excinfo.value.code == "REPORT_INCOMPLETE"
        assert any("placeholder" in v for v in excinfo.value.violators), \
            f"no placeholder offender listed for {human_form!r}"


def test_omitted_token_case_insensitive_in_human_form(tmp_path):
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        # "OMITTED" in the human form itself (the certified text is clean)
        render_final_report(session, human_form="K1  # details OMITTED",
                            definitions={"K1": "(x+1)**2"})
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert any("omitted" in v for v in excinfo.value.violators)
