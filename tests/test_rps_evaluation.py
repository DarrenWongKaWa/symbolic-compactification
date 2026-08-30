from __future__ import annotations

from dataclasses import replace

import pytest

from research.representation_program_search.evaluation import (
    EvaluationContractError,
    EvaluationRun,
    aggregate_runs,
    load_evaluation_run,
)

HASH = "a" * 64


def _run(**changes) -> EvaluationRun:
    base = EvaluationRun(
        run_id="run-1",
        condition="S1",
        case_id="case-1",
        cluster_id="cluster-a",
        partition="DEV",
        representation_depth=3,
        grammar_id="G_FULL",
        latent_creation_allowed=True,
        seed=0,
        model=None,
        budget_requested=1000,
        availability="AVAILABLE",
        exclusion_reason=None,
        admission_status="ADMISSION_READY",
        leakage_status="CLEARED",
        states_expanded=1000,
        first_success_index=42,
        time_to_first_success_seconds=1.25,
        tokens_to_first_success=None,
        wall_time_seconds=4.0,
        source_result_sha256=HASH,
        search_trace_hash="b" * 64,
        evidence_trace_hash="c" * 64,
    )
    return replace(base, **changes)


def test_success_curves_and_conditional_efficiency_are_explicit():
    first = _run()
    second = _run(
        run_id="run-2",
        case_id="case-2",
        cluster_id="cluster-b",
        seed=1,
        first_success_index=None,
        time_to_first_success_seconds=None,
    )
    out = aggregate_runs([first, second])
    summary = out["summaries"][0]
    assert summary["budget_curve"]["SUCCESS@10"]["successes"] == 0
    at_50 = summary["budget_curve"]["SUCCESS@50"]
    assert at_50["task_weighted_probability"] == 0.5
    assert at_50["cluster_weighted_probability"] == 0.5
    assert at_50["best_certified_depth"] == 3
    assert summary["median_states_to_first_success_conditional"] == 42
    assert summary["failed_or_censored_runs"] == 1


def test_cluster_weighting_does_not_let_large_cluster_dominate():
    runs = [
        _run(run_id="a1", case_id="a1", cluster_id="large", seed=0),
        _run(run_id="a2", case_id="a2", cluster_id="large", seed=1),
        _run(run_id="a3", case_id="a3", cluster_id="large", seed=2),
        _run(
            run_id="b1", case_id="b1", cluster_id="small", seed=0,
            first_success_index=None, time_to_first_success_seconds=None,
        ),
    ]
    point = aggregate_runs(runs)["summaries"][0]["budget_curve"]["SUCCESS@50"]
    assert point["task_weighted_probability"] == 0.75
    assert point["cluster_weighted_probability"] == 0.5


def test_unavailable_is_reported_not_counted_as_failure():
    unavailable = _run(
        run_id="missing", availability="UNAVAILABLE",
        exclusion_reason="SOL_REPLAY_UNAVAILABLE", admission_status="NOT_APPLICABLE",
        leakage_status="UNKNOWN", states_expanded=None, first_success_index=None,
        time_to_first_success_seconds=None, wall_time_seconds=None,
        search_trace_hash=None, evidence_trace_hash=None,
    )
    summary = aggregate_runs([_run(), unavailable])["summaries"][0]
    assert summary["available_runs"] == 1
    assert summary["unavailable_runs"] == 1
    assert summary["budget_curve"]["SUCCESS@50"]["task_weighted_probability"] == 1.0


def test_available_requires_admission_and_leakage_clearance():
    with pytest.raises(EvaluationContractError, match="CASE_NOT_ADMISSION_READY"):
        _run(admission_status="CANDIDATE_FOR_INDEPENDENT_REVIEW")
    with pytest.raises(EvaluationContractError, match="LEAKAGE_NOT_CLEARED"):
        _run(leakage_status="UNKNOWN")


def test_llm_and_non_llm_model_binding_is_fail_closed():
    with pytest.raises(EvaluationContractError, match="LLM_MODEL_MISSING"):
        _run(condition="S4")
    with pytest.raises(EvaluationContractError, match="NON_LLM_MODEL_SET"):
        _run(model="deepseek-v4-pro")
    llm = _run(condition="S4", model="deepseek-v4-pro")
    assert llm.condition == "S4"


def test_schema_is_exact_and_hashes_are_validated():
    payload = _run().to_dict()
    assert load_evaluation_run(payload) == _run()
    payload["extra"] = True
    with pytest.raises(EvaluationContractError, match="RUN_SCHEMA_MISMATCH"):
        load_evaluation_run(payload)
    with pytest.raises(EvaluationContractError, match="SOURCE_RESULT_SHA256_INVALID"):
        _run(source_result_sha256="bad")


def test_no_success_metrics_on_failure_and_one_indexed_success():
    with pytest.raises(EvaluationContractError, match="FAILURE_HAS_SUCCESS_METRIC"):
        _run(first_success_index=None)
    with pytest.raises(EvaluationContractError, match="FIRST_SUCCESS_NOT_ONE_INDEXED"):
        _run(first_success_index=0)
