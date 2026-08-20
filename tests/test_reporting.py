"""Regression tests for the FINAL CERTIFIED FORM reporting contract
(agent protocol v0.2.2).

Covers ``render_final_report`` / ``cmd_finalize``:
* the deliverable shows the EXPLICIT certified expression (never an
  abstraction-only pointer) with a complete provenance header;
* abbreviation discipline: every alias must be defined; ``{...}`` / TODO /
  "same kernel" placeholders are rejected with REPORT_INCOMPLETE listing
  the offenders;
* the abbreviation-expansion check is VERIFIED (not skipped) on small
  generic polynomial/Sum examples — substituting the kernel definitions
  into the human form reproduces the certified machine representation;
* the large-result artifact ``final/FINAL_CERTIFIED_FORM.md`` carries every
  supplied definition plus the provenance header;
* the CLI ``finalize --run <id>`` prints the FINAL CERTIFIED FORM section
  and the artifact path with exit 0.
"""
from __future__ import annotations

import json

import pytest
import sympy

from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
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
# helpers: a synthetic certified run
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
            "engine_version": ENGINE_VERSION,
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

    from pathlib import Path
    run_root = Path(workspace_root) / "runs" / session.run_id
    return session, run_root, candidate


# --------------------------------------------------------------------------- #
# explicit expression + provenance header
# --------------------------------------------------------------------------- #

def test_render_final_report_shows_explicit_expression_and_header(tmp_path):
    session, run_root, candidate = _certified_run(tmp_path)

    report = render_final_report(session)

    # the deliverable is the EXPLICIT expression, not an abstraction-only
    # pointer: human form defaults to the certified machine text itself
    assert report["certified_text"] == "(x+1)**2"
    assert report["human_form"] == "(x+1)**2"
    assert report["certified_state_sha256"] == candidate.sha256
    assert report["run_id"] == session.run_id
    assert report["expansion_check"] == "verified"

    # summary counts are real (one ZERO promotion, no NONZERO/UNKNOWN)
    assert report["summary"]["zero_promotions"] == 1
    assert report["summary"]["nonzero_count"] == 0
    assert report["summary"]["unknown_count"] == 0

    artifact = run_root / "final" / FINAL_ARTIFACT_NAME
    assert report["artifact_path"] == str(artifact)
    md = artifact.read_text(encoding="utf-8")
    assert "# FINAL CERTIFIED FORM" in md
    # provenance header carries every required field
    assert f"run_id: {session.run_id}" in md
    assert f"engine_version: {ENGINE_VERSION}" in md
    assert f"agent_protocol_version: {AGENT_PROTOCOL_VERSION}" in md
    assert AGENT_PROTOCOL_VERSION == "0.3.0"
    assert f"certified_state_sha256: {candidate.sha256}" in md
    assert "zero_promotions: 1" in md
    assert "nonzero_attempts: 0" in md
    assert "unknown_attempts: 0" in md
    # the explicit certified expression appears in the artifact body
    assert "(x+1)**2" in md


def test_render_final_report_accepts_a_run_dir_path(tmp_path):
    session, run_root, candidate = _certified_run(tmp_path)
    report = render_final_report(run_root)  # Path source, not SessionState
    assert report["certified_text"] == candidate.text
    assert report["run_id"] == session.run_id


def test_render_final_report_no_current_expression(tmp_path):
    session = init_session(workspace_root=str(tmp_path))
    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session)
    assert excinfo.value.code == "NO_CURRENT_EXPRESSION"


# --------------------------------------------------------------------------- #
# abbreviation discipline + expansion check
# --------------------------------------------------------------------------- #

def test_fully_defined_abbreviations_render_and_verify(tmp_path):
    """definitions {K1: ...} fully supplied: renders, and the expansion
    check VERIFIES that substitution reproduces the certified form."""
    session, run_root, candidate = _certified_run(tmp_path)

    report = render_final_report(
        session, human_form="K1", definitions={"K1": "(x+1)**2"})

    assert report["human_form"] == "K1"
    assert report["definitions"] == {"K1": "(x+1)**2"}
    assert report["expansion_check"] == "verified"
    md = (run_root / "final" / FINAL_ARTIFACT_NAME).read_text(encoding="utf-8")
    assert "`K1` := `(x+1)**2`" in md
    assert "- status: verified" in md


def test_nested_kernel_expansion_is_verified_not_skipped(tmp_path):
    """An introduced kernel substituted into the TOP-LEVEL form must
    reproduce the certified machine representation: human 'K1**2' with
    K1 := x + 1 expands to (x + 1)**2 — verified by the exact verifier."""
    session, run_root, _ = _certified_run(tmp_path)
    report = render_final_report(
        session, human_form="K1**2", definitions={"K1": "x + 1"})
    assert report["expansion_check"] == "verified"


def test_sum_kernel_expansion_is_verified(tmp_path):
    """Small generic Sum example: the expansion check is verified, not
    skipped, for structural builtins too."""
    session, run_root, _ = _certified_run(
        tmp_path, current_text="Sum(k, (k, 1, n)) + 0",
        certified_text="Sum(k, (k, 1, n))", symbols=("n", "k"))
    report = render_final_report(
        session, human_form="K1", definitions={"K1": "Sum(k, (k, 1, n))"})
    assert report["expansion_check"] == "verified"


def test_undefined_alias_raises_report_incomplete_listing_offender(tmp_path):
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session, human_form="K1 + Zz9",
                            definitions={"K1": "(x+1)**2"})
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert "Zz9" in excinfo.value.violators


def test_placeholder_fixtures_are_rejected(tmp_path):
    """``{...}``, TODO and 'same kernel' hand-waving are incomplete reports."""
    session, run_root, _ = _certified_run(tmp_path)

    cases = [
        ("(x+1)**2 + {rest}", {}),                    # brace placeholder
        ("K1", {"K1": "(x+1)**2  # TODO: finish"}),   # TODO marker
        ("K1", {"K1": "same kernel as before"}),      # same-kernel waving
    ]
    for human_form, definitions in cases:
        with pytest.raises(AdapterError) as excinfo:
            render_final_report(session, human_form=human_form,
                                definitions=definitions)
        assert excinfo.value.code == "REPORT_INCOMPLETE"
        assert excinfo.value.violators, "offenders must be listed"
        assert any("placeholder" in v for v in excinfo.value.violators)


def test_contradictory_definition_raises_report_incomplete(tmp_path):
    """A defined abbreviation whose expansion is PROVABLY wrong (NONZERO
    residual against the certified form) is an incomplete report."""
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session, human_form="K1",
                            definitions={"K1": "x**2 + 5"})
    assert excinfo.value.code == "REPORT_INCOMPLETE"
    assert any("contradicts" in v for v in excinfo.value.violators)


def test_empty_human_form_is_rejected(tmp_path):
    session, run_root, _ = _certified_run(tmp_path)
    with pytest.raises(AdapterError) as excinfo:
        render_final_report(session, human_form="   ")
    assert excinfo.value.code == "REPORT_INCOMPLETE"


# --------------------------------------------------------------------------- #
# large-result artifact path
# --------------------------------------------------------------------------- #

def test_artifact_contains_every_definition_and_provenance(tmp_path):
    """The FINAL_CERTIFIED_FORM.md artifact is the complete deliverable:
    every supplied kernel/branch definition plus the provenance header."""
    session, run_root, candidate = _certified_run(tmp_path)

    definitions = {
        "K1": "(x+1)**2",
        "B1": "x + 1",
    }
    report = render_final_report(session, human_form="K1",
                                 definitions=definitions)

    md = (run_root / "final" / FINAL_ARTIFACT_NAME).read_text(encoding="utf-8")
    for name, body in definitions.items():
        assert f"`{name}` := `{body}`" in md
    # provenance header present in the same artifact
    assert f"run_id: {session.run_id}" in md
    assert f"engine_version: {ENGINE_VERSION}" in md
    assert f"agent_protocol_version: {AGENT_PROTOCOL_VERSION}" in md
    assert f"certified_state_sha256: {candidate.sha256}" in md
    # machine representation section carries the canonical certified text
    assert "## Machine representation" in md
    assert report["artifact_path"].endswith(
        f"final/{FINAL_ARTIFACT_NAME}")


# --------------------------------------------------------------------------- #
# CLI: finalize --run <id>
# --------------------------------------------------------------------------- #

def test_cli_finalize_prints_final_form_and_artifact_path(tmp_path, capsys):
    session, run_root, candidate = _certified_run(tmp_path)

    exit_code = cli_main([
        "finalize", "--run", session.run_id, "--workspace", str(tmp_path)])
    out = capsys.readouterr().out

    assert exit_code == 0
    assert "FINAL CERTIFIED FORM" in out
    # the explicit certified expression is printed (not a pointer only)
    assert "(x+1)**2" in out
    expected_artifact = run_root / "final" / FINAL_ARTIFACT_NAME
    assert str(expected_artifact) in out
    assert expected_artifact.is_file()
    # run id + certified hash are part of the printed section
    assert session.run_id in out
    assert candidate.sha256 in out
