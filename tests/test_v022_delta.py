"""v0.2.2 audit-delta: step telemetry completeness and the split status
taxonomy axes.

Deterministic, neutral synthetic fixtures only. Covers:

* Step telemetry (CLI-driven verification step): every normal step record
  populates each telemetry field when computable, or carries an explicit
  ``<field>_reason`` key instead — populated XOR reason, never a silent
  null. Checked per-field for input_chars, output_chars,
  count_ops_before/count_ops_after, wall_time_seconds, primitive, verdict,
  timeout_status, engine_version and agent_protocol_version.
* Taxonomy combined blockers: ``assumption_status=HUMAN_REQUIRED`` and
  ``proof_status=PROOF_REQUIRED`` can be carried SIMULTANEOUSLY on one
  step (``derive_status_axes`` behavior); the vocabulary constants cover
  HYPOTHESIS/UNKNOWN-verdict/PROOF_REQUIRED/HUMAN_REQUIRED on the
  applicable axes.
"""
from __future__ import annotations

import json
import types

import pytest

from symbolic_compactification import (
    AGENT_PROTOCOL_VERSION,
    ASSUMPTION_STATUS_VALUES,
    ENGINE_VERSION,
    NONZERO,
    PROOF_STATUS_VALUES,
    STEP_STATUSES,
    UNKNOWN,
    ZERO,
    AdapterError,
    StepRecord,
    derive_status_axes,
)
from symbolic_compactification.cli import _step_telemetry
from symbolic_compactification.cli import main as cli_main
from symbolic_compactification.models import PROPOSER_MODES


# --------------------------------------------------------------------------- #
# helpers: a CLI-driven verification step on neutral synthetic content
# --------------------------------------------------------------------------- #

def _cli_verified_step(tmp_path) -> dict:
    """Script a real CLI run: init-session -> one ZERO step. Returns the
    persisted step record dict."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "current.txt").write_text("x**2 + 2*x + 1\n", encoding="utf-8")
    (ws / "candidate.txt").write_text("(x+1)**2\n", encoding="utf-8")
    (ws / "symbols.json").write_text('["x"]\n', encoding="utf-8")

    assert cli_main(["init-session", "--workspace", str(ws),
                     "--current", str(ws / "current.txt"),
                     "--symbols", str(ws / "symbols.json")]) == 0
    run_id = next(p for p in (ws / "runs").iterdir()).name

    exit_code = cli_main([
        "step", "--run", run_id, "--workspace", str(ws),
        # explicit --current: the step re-parses both sides, so both op
        # counts are computable (the rehydrated session current carries no
        # parse — that reason-only branch is covered separately below)
        "--current", str(ws / "current.txt"),
        "--candidate", str(ws / "candidate.txt"),
        "--symbols", str(ws / "symbols.json"),
    ])
    assert exit_code == 0, "the synthetic step must certify ZERO"

    step_path = ws / "runs" / run_id / "steps" / "step_001.json"
    return json.loads(step_path.read_text(encoding="utf-8"))


def _assert_populated_xor_reason(telemetry: dict, field: str) -> None:
    """Per-field contract: the field is populated XOR an explicit
    ``<field>_reason`` code is present — never both, never a silent null."""
    has_field = field in telemetry
    has_reason = f"{field}_reason" in telemetry
    assert has_field != has_reason, (
        f"{field}: populated={has_field}, reason={has_reason} "
        "(expected exactly one)")
    if has_field:
        assert telemetry[field] is not None, f"{field} is a silent null"
    else:
        reason = telemetry[f"{field}_reason"]
        assert isinstance(reason, str) and reason.strip(), \
            f"{field}_reason must be an explicit code"


# --------------------------------------------------------------------------- #
# step telemetry on a normal verification step
# --------------------------------------------------------------------------- #

def test_normal_step_telemetry_populated_xor_reason_per_field(tmp_path):
    step = _cli_verified_step(tmp_path)
    telemetry = step["telemetry"]
    assert telemetry, "a CLI verification step must record telemetry"

    # always-computable fields: populated, correctly typed, never null
    assert isinstance(telemetry["input_chars"], int)
    assert telemetry["input_chars"] > 0
    assert isinstance(telemetry["output_chars"], int)
    assert telemetry["output_chars"] > 0
    assert isinstance(telemetry["wall_time_seconds"], (int, float))
    assert not isinstance(telemetry["wall_time_seconds"], bool)
    assert telemetry["wall_time_seconds"] >= 0.0
    assert telemetry["verdict"] == ZERO
    assert telemetry["timeout_status"] == "ok"
    assert telemetry["engine_version"] == ENGINE_VERSION
    assert telemetry["agent_protocol_version"] == AGENT_PROTOCOL_VERSION

    # populated-XOR-reason contract for the conditionally computable fields
    for field in ("input_chars", "output_chars", "count_ops_before",
                  "count_ops_after", "wall_time_seconds", "primitive",
                  "verdict", "timeout_status"):
        _assert_populated_xor_reason(telemetry, field)

    # the synthetic ZERO step computes both op counts
    assert isinstance(telemetry["count_ops_before"], int)
    assert isinstance(telemetry["count_ops_after"], int)
    assert telemetry["count_ops_before"] > 0
    assert telemetry["count_ops_after"] > 0
    # a CLI step applies no structural primitive: reason-only, explicit
    assert "primitive" not in telemetry
    assert telemetry["primitive_reason"] == "CLI_STEP_NO_STRUCTURAL_PRIMITIVE"

    # no silent nulls anywhere in the record
    assert all(value is not None for value in telemetry.values())

    # the split status axes are recorded on the persisted step too
    assert step["assumption_status"] == "DECLARED"
    assert step["proof_status"] == "PROVEN"


def test_telemetry_reason_branches_are_explicit_not_silent_nulls():
    """Direct exercise of the reason branch: records without a parse carry
    explicit ``*_reason`` codes (never a silent null), and a budget-timeout
    evidence kind flips timeout_status."""
    current = types.SimpleNamespace(text="x + 1", parsed_expr=None)
    candidate = types.SimpleNamespace(text="x + 1", parsed_expr=None)
    result = types.SimpleNamespace(
        seconds=0.25, verdict=UNKNOWN,
        evidence=[{"kind": "TIME_BUDGET_EXCEEDED", "operation": "simplify"}])

    telemetry = _step_telemetry(current, candidate, result)

    assert "count_ops_before" not in telemetry
    assert telemetry["count_ops_before_reason"] == "PARSE_UNAVAILABLE"
    assert "count_ops_after" not in telemetry
    assert telemetry["count_ops_after_reason"] == "PARSE_UNAVAILABLE"
    assert telemetry["timeout_status"] == "TIME_BUDGET_EXCEEDED"
    assert telemetry["verdict"] == UNKNOWN
    assert telemetry["primitive_reason"] == "CLI_STEP_NO_STRUCTURAL_PRIMITIVE"
    assert all(value is not None for value in telemetry.values())


# --------------------------------------------------------------------------- #
# taxonomy axes: vocabularies + combined blockers
# --------------------------------------------------------------------------- #

def test_taxonomy_vocabularies_cover_the_documented_states():
    # assumption axis: NONE / DECLARED / HUMAN_REQUIRED
    assert {"NONE", "DECLARED", "HUMAN_REQUIRED"} <= set(
        ASSUMPTION_STATUS_VALUES)
    # proof axis: NONE / HYPOTHESIS / PROOF_REQUIRED / PROVEN
    assert {"NONE", "HYPOTHESIS", "PROOF_REQUIRED", "PROVEN"} <= set(
        PROOF_STATUS_VALUES)
    # HYPOTHESIS also lives in the lifecycle vocabulary
    assert "HYPOTHESIS" in STEP_STATUSES
    # PROOF_REQUIRED is a proof-gap status, never an assumption status
    assert "PROOF_REQUIRED" not in ASSUMPTION_STATUS_VALUES
    assert "HUMAN_REQUIRED" not in PROOF_STATUS_VALUES
    # UNKNOWN is the verifier VERDICT, not a taxonomy axis value
    assert UNKNOWN not in ASSUMPTION_STATUS_VALUES
    assert UNKNOWN not in PROOF_STATUS_VALUES
    # the proposer-mode vocabulary stays complete (context for UNKNOWN)
    assert "UNKNOWN" in PROPOSER_MODES


def test_derive_status_axes_zero_verdict_is_proven():
    assert derive_status_axes(ZERO) == ("NONE", "PROVEN")
    assert derive_status_axes(ZERO, assumptions_status="DECLARED") == (
        "DECLARED", "PROVEN")


def test_derive_status_axes_unknown_is_proof_gap_never_human_gate():
    """The critical semantic: engine-cannot-prove maps to PROOF_REQUIRED and
    NEVER to HUMAN_REQUIRED (a proof gap is not a human-decision gate)."""
    assumption, proof = derive_status_axes(UNKNOWN)
    assert proof == "PROOF_REQUIRED"
    assert proof != "HUMAN_REQUIRED"
    assert derive_status_axes(NONZERO) == ("NONE", "PROOF_REQUIRED")


def test_derive_status_axes_unadjudicated_is_hypothesis():
    assert derive_status_axes(UNKNOWN, adjudicated=False) == (
        "NONE", "HYPOTHESIS")
    assert derive_status_axes(ZERO, adjudicated=False) == (
        "NONE", "HYPOTHESIS")


def test_combined_blockers_human_required_and_proof_required_simultaneously():
    """A step can depend on genuinely NEW assumptions AND be unproven by the
    deterministic verifier at the same time: the two axes are orthogonal."""
    assumption, proof = derive_status_axes(
        UNKNOWN, assumptions_status="HUMAN_REQUIRED", adjudicated=True)
    assert assumption == "HUMAN_REQUIRED"
    assert proof == "PROOF_REQUIRED"

    # and a StepRecord carries BOTH simultaneously
    step = StepRecord(
        step=1, current_hash="h", candidate_hash="c", candidate_text="x",
        residual="r", verdict=UNKNOWN,
        assumption_status="HUMAN_REQUIRED", proof_status="PROOF_REQUIRED")
    payload = step.to_dict()
    assert payload["assumption_status"] == "HUMAN_REQUIRED"
    assert payload["proof_status"] == "PROOF_REQUIRED"


def test_status_axes_unknown_values_normalize_or_fail_closed():
    # an unknown assumptions_status normalizes to NONE (never crashes)
    assert derive_status_axes(UNKNOWN, assumptions_status="SOMETHING_ELSE") \
        == ("NONE", "PROOF_REQUIRED")
    # ... while StepRecord fields fail closed on vocabulary violations
    with pytest.raises(AdapterError) as excinfo:
        StepRecord(step=1, current_hash="h", candidate_hash="c",
                   candidate_text="x", residual=None, verdict=UNKNOWN,
                   assumption_status="BOGUS")
    assert excinfo.value.code == "ASSUMPTION_STATUS_INVALID"
    with pytest.raises(AdapterError) as excinfo:
        StepRecord(step=1, current_hash="h", candidate_hash="c",
                   candidate_text="x", residual=None, verdict=UNKNOWN,
                   proof_status="BOGUS")
    assert excinfo.value.code == "PROOF_STATUS_INVALID"
