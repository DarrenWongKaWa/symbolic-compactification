"""Method-neutral reporting for frozen representation-search runs."""

from .aggregate import aggregate_runs
from .model import (
    FIXED_BUDGETS,
    EvaluationContractError,
    EvaluationRun,
    load_evaluation_run,
)

__all__ = [
    "FIXED_BUDGETS",
    "EvaluationContractError",
    "EvaluationRun",
    "aggregate_runs",
    "load_evaluation_run",
]
