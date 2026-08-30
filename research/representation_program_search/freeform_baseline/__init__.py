"""Frozen F0/P0 RAW compatibility boundary."""

from .authority import F0_AUTHORITY_COMMIT, validate_f0_authority
from .evaluator import (
    F0_EVALUATION_POLICY_VERSION,
    F0_TYPED_TRANSLATOR_VERSION,
    F0EvaluationContractError,
    evaluate_f0,
)
from .prompt import F0Prompt, build_f0_prompt
from .runner import (
    F0_RUN_POLICY_VERSION,
    F0RunContractError,
    F0RunResult,
    run_f0,
)

__all__ = [
    "F0_AUTHORITY_COMMIT",
    "F0_EVALUATION_POLICY_VERSION",
    "F0_TYPED_TRANSLATOR_VERSION",
    "F0EvaluationContractError",
    "F0Prompt",
    "F0RunContractError",
    "F0RunResult",
    "build_f0_prompt",
    "evaluate_f0",
    "F0_RUN_POLICY_VERSION",
    "run_f0",
    "validate_f0_authority",
]
