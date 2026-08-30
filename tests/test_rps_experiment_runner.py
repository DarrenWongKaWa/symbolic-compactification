from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.evaluation import (
    CLEARANCE_SCHEMA,
    ExperimentJobError,
    ExperimentJobSpec,
    run_experiment_job,
)
from research.representation_program_search.search import load_public_case


class _ValidTransport:
    def complete(self, request):
        user_content = request["messages"][1]["content"]
        try:
            public = json.loads(user_content)
        except json.JSONDecodeError:
            public = None
        if isinstance(public, dict) and isinstance(public.get("candidates"), list):
            content = json.dumps({
                "ranking": [item["opaque_id"] for item in public["candidates"]]
            })
        else:
            content = json.dumps({"abstain": True, "hypotheses": []})
        return {
            "choices": [{
                "finish_reason": "stop",
                "message": {"content": content},
            }],
            "id": "runner-mock-request",
            "model": request["model"],
            "usage": {
                "completion_tokens": 5,
                "completion_tokens_details": {"reasoning_tokens": 2},
                "prompt_cache_hit_tokens": 1,
                "prompt_cache_miss_tokens": 9,
                "prompt_tokens": 10,
                "total_tokens": 15,
            },
        }


def _json(path: Path, payload: object) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _text(path: Path, value: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(root: Path):
    member_sha = _text(root / "members" / "M001.txt", "exp(x)")
    symbols_sha = _json(root / "symbols.json", {"symbols": ["x"]})
    proposer_path = root / "proposer_view.json"
    _json(proposer_path, {
        "assumptions": {"predicates": []},
        "case_id": "RUNNER_SYNTHETIC",
        "source_catalog": {
            "members": [{
                "member_id": "M001",
                "path": "members/M001.txt",
                "sha256": member_sha,
            }],
            "symbols_path": "symbols.json",
            "symbols_sha256": symbols_sha,
        },
    })
    case = load_public_case(proposer_path)
    receipt_path = root / "clearance.json"
    receipt_sha = _json(receipt_path, {
        "admission_audit_sha256": "a" * 64,
        "admission_status": "ADMISSION_READY",
        "assumption_audit_sha256": "b" * 64,
        "assumption_clearance": "CLEARED",
        "case_id": case.case_id,
        "leakage_audit_sha256": "c" * 64,
        "leakage_status": "CLEARED",
        "proposer_view_sha256": case.proposer_view_sha256,
        "schema_version": CLEARANCE_SCHEMA,
    })
    return case, proposer_path, receipt_path, receipt_sha


def _spec(case, receipt_sha: str, condition: str) -> ExperimentJobSpec:
    return ExperimentJobSpec(
        job_id=f"job-{condition.lower()}",
        condition=condition,
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
        clearance_receipt_sha256=receipt_sha,
        budget=10,
    )


def test_runner_publishes_s1_and_exact_posthoc_artifacts_atomically(tmp_path):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    output = tmp_path / "jobs" / "s1"
    result = run_experiment_job(
        _spec(case, receipt_sha, "S1"),
        proposer_view_path=proposer,
        clearance_receipt_path=receipt,
        output_directory=output,
    )
    assert result["runner_status"] == "COMPLETE"
    assert result["method"]["search_states_expanded"] == 10
    assert (output / "JOB_MANIFEST.json").is_file()
    assert (output / "JOB_RESULT.json").is_file()
    assert (output / "search" / "result.json").is_file()
    assert (output / "verification" / "controller.json").is_file()
    assert not list((tmp_path / "jobs").glob(".s1.*"))
    with pytest.raises(ExperimentJobError, match="JOB_OUTPUT_ALREADY_EXISTS"):
        run_experiment_job(
            _spec(case, receipt_sha, "S1"),
            proposer_view_path=proposer,
            clearance_receipt_path=receipt,
            output_directory=output,
        )


def test_matched_symbolic_control_reaches_posthoc_evaluator(tmp_path):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    result = run_experiment_job(
        _spec(case, receipt_sha, "S2_MATCHED_BATCH32"),
        proposer_view_path=proposer,
        clearance_receipt_path=receipt,
        output_directory=tmp_path / "job",
    )
    assert result["runner_status"] == "COMPLETE"
    controller = json.loads(
        (tmp_path / "job" / "verification" / "controller.json").read_text()
    )
    assert controller["condition"] == "S2_MATCHED_BATCH32"
    assert controller["feedback_guides_successors"] is False


def test_s6_job_uses_exact_feedback_controller(tmp_path):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    result = run_experiment_job(
        _spec(case, receipt_sha, "S6"),
        proposer_view_path=proposer,
        clearance_receipt_path=receipt,
        output_directory=tmp_path / "job",
    )
    assert result["runner_status"] == "COMPLETE"
    controller = json.loads(
        (tmp_path / "job" / "verification" / "controller.json").read_text()
    )
    assert controller["condition"] == "S6"
    assert controller["feedback_guides_successors"] is True


def test_clearance_and_llm_inputs_fail_closed_before_output(tmp_path):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    invalid = ExperimentJobSpec(
        job_id="job-s4",
        condition="S4",
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
        clearance_receipt_sha256=receipt_sha,
        budget=10,
        model="deepseek-v4-pro",
        seed_label="seed-0",
    )
    output = tmp_path / "job"
    with pytest.raises(ExperimentJobError, match="LLM_TRANSPORT_REQUIRED"):
        run_experiment_job(
            invalid,
            proposer_view_path=proposer,
            clearance_receipt_path=receipt,
            output_directory=output,
        )
    assert not output.exists()

    receipt.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ExperimentJobError, match="CLEARANCE_RECEIPT_HASH_MISMATCH"):
        run_experiment_job(
            _spec(case, receipt_sha, "S1"),
            proposer_view_path=proposer,
            clearance_receipt_path=receipt,
            output_directory=output,
        )
    assert not output.exists()


def test_f0_has_no_fake_state_budget(tmp_path):
    case, _proposer, _receipt, receipt_sha = _case(tmp_path / "case")
    with pytest.raises(ExperimentJobError, match="F0_STATE_BUDGET_FORBIDDEN"):
        ExperimentJobSpec(
            job_id="job-f0",
            condition="F0",
            case_id=case.case_id,
            proposer_view_sha256=case.proposer_view_sha256,
            clearance_receipt_sha256=receipt_sha,
            budget=10,
            model="deepseek-v4-pro",
            seed_label="seed-0",
            f0_hidden_sha256="d" * 64,
        )


@pytest.mark.parametrize("condition", ["S4", "S5", "S7"])
def test_llm_condition_jobs_accept_only_recorded_legal_rankings(tmp_path, condition):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    spec = ExperimentJobSpec(
        job_id=f"job-{condition.lower()}",
        condition=condition,
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
        clearance_receipt_sha256=receipt_sha,
        budget=10,
        model="deepseek-v4-pro",
        seed_label="seed-0",
    )
    output = tmp_path / "job"
    result = run_experiment_job(
        spec,
        proposer_view_path=proposer,
        clearance_receipt_path=receipt,
        output_directory=output,
        transport=_ValidTransport(),
    )
    assert result["runner_status"] == "COMPLETE"
    assert result["method"]["llm_guided_scientific_run_eligible"] is True
    assert result["method"]["llm_tokens_used"] > 0
    assert (output / "JOB_RESULT.json").is_file()


def test_f0_job_is_evaluated_without_a_search_budget(tmp_path):
    case, proposer, receipt, receipt_sha = _case(tmp_path / "case")
    hidden_path = tmp_path / "hidden.json"
    hidden_sha = _json(hidden_path, {
        "nontrivial": True,
        "representation_family": [],
    })
    spec = ExperimentJobSpec(
        job_id="job-f0",
        condition="F0",
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
        clearance_receipt_sha256=receipt_sha,
        budget=None,
        model="deepseek-v4-pro",
        seed_label="seed-0",
        f0_hidden_sha256=hidden_sha,
    )
    output = tmp_path / "job"
    result = run_experiment_job(
        spec,
        proposer_view_path=proposer,
        clearance_receipt_path=receipt,
        output_directory=output,
        transport=_ValidTransport(),
        f0_hidden_path=hidden_path,
    )
    assert result["runner_status"] == "COMPLETE"
    assert result["method"]["search_states_expanded"] is None
    assert result["method"]["program_success"] is False
    assert (output / "freeform" / "result.json").is_file()
    assert (output / "verification" / "evaluation.json").is_file()
