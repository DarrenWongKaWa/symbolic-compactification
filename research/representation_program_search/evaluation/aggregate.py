"""Transparent task- and cluster-weighted summaries of RPS run records."""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Any, Iterable

from .model import FIXED_BUDGETS, EvaluationContractError, EvaluationRun


def _wilson(successes: int, total: int, z: float = 1.959963984540054) -> list[float] | None:
    if total == 0:
        return None
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def _method_key(run: EvaluationRun) -> tuple[Any, ...]:
    return (
        run.partition,
        run.condition,
        run.grammar_id,
        run.latent_creation_allowed,
        run.model,
    )


def _method_key_dict(key: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "partition": key[0],
        "condition": key[1],
        "grammar_id": key[2],
        "latent_creation_allowed": key[3],
        "model": key[4],
    }


def _median(values: list[int | float]) -> int | float | None:
    return None if not values else statistics.median(values)


def aggregate_runs(runs: Iterable[EvaluationRun]) -> dict[str, Any]:
    """Aggregate frozen-budget curves without treating unavailable as failure.

    Task-weighted probability gives every available seed/run equal weight.
    Cluster-weighted probability first averages all available runs inside a
    structural cluster and then gives every represented cluster equal weight.
    Both are reported because neither is silently substituted for the other.
    """
    records = tuple(runs)
    if len({run.run_id for run in records}) != len(records):
        raise EvaluationContractError("DUPLICATE_RUN_ID")

    grouped: dict[tuple[Any, ...], list[EvaluationRun]] = defaultdict(list)
    for run in records:
        grouped[_method_key(run)].append(run)

    summaries: list[dict[str, Any]] = []
    for key in sorted(grouped, key=lambda item: tuple("" if x is None else str(x) for x in item)):
        group = grouped[key]
        available = [run for run in group if run.availability == "AVAILABLE"]
        unavailable = [run for run in group if run.availability == "UNAVAILABLE"]
        curve: dict[str, Any] = {}
        for budget in FIXED_BUDGETS:
            eligible = [run for run in available if run.budget_requested >= budget]
            successes = [run for run in eligible if run.success_at(budget)]
            by_cluster: dict[str, list[bool]] = defaultdict(list)
            for run in eligible:
                by_cluster[run.cluster_id].append(bool(run.success_at(budget)))
            cluster_rates = [
                sum(values) / len(values) for values in by_cluster.values()
            ]
            certified_depths = [
                run.representation_depth for run in successes
            ]
            curve[f"SUCCESS@{budget}"] = {
                "available_runs": len(eligible),
                "best_certified_depth": max(certified_depths, default=None),
                "cluster_weighted_probability": (
                    sum(cluster_rates) / len(cluster_rates) if cluster_rates else None
                ),
                "represented_clusters": len(by_cluster),
                "successes": len(successes),
                "task_weighted_probability": (
                    len(successes) / len(eligible) if eligible else None
                ),
                "task_weighted_wilson_95": _wilson(len(successes), len(eligible)),
            }

        successful = [run for run in available if run.program_success]
        seed_outcomes: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for run in available:
            seed_outcomes[run.case_id].append({
                "first_success_index": run.first_success_index,
                "program_success": run.program_success,
                "seed": run.seed,
            })
        summaries.append({
            **_method_key_dict(key),
            "available_runs": len(available),
            "budget_curve": curve,
            "failed_or_censored_runs": len(available) - len(successful),
            "median_states_to_first_success_conditional": _median([
                run.first_success_index for run in successful
                if run.first_success_index is not None
            ]),
            "median_time_to_first_success_seconds_conditional": _median([
                run.time_to_first_success_seconds for run in successful
                if run.time_to_first_success_seconds is not None
            ]),
            "median_tokens_to_first_success_conditional": _median([
                run.tokens_to_first_success for run in successful
                if run.tokens_to_first_success is not None
            ]),
            "seed_sensitivity": dict(sorted(seed_outcomes.items())),
            "successful_runs": len(successful),
            "unavailable_reasons": dict(sorted(
                (reason, sum(1 for run in unavailable if run.exclusion_reason == reason))
                for reason in {run.exclusion_reason for run in unavailable}
                if reason is not None
            )),
            "unavailable_runs": len(unavailable),
        })

    return {
        "aggregation_version": "RPSEvaluationAggregationV1",
        "fixed_state_budgets": list(FIXED_BUDGETS),
        "n_input_records": len(records),
        "notes": {
            "cluster_weighting": "mean within cluster, then equal weight per represented cluster",
            "median_success_metrics": "conditional on PROGRAM_SUCCESS; failures/censoring reported separately",
            "unavailable_policy": "excluded from success denominators and reported separately",
            "wilson_interval": "two-sided 95% Wilson score interval on task-weighted Bernoulli runs",
        },
        "summaries": summaries,
    }
