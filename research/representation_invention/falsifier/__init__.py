"""Adversarial falsifier for representation claims. Attack only."""
from __future__ import annotations

from research.representation_invention.falsifier.cases import (
    ATTACK_CASES,
    ATTACK_IDS,
    CASES_BY_ID,
    MATH_NONZERO_IDS,
    TAUTOLOGY_RESIDUAL_IDS,
    export_fixtures,
    load_attack_cases,
)
from research.representation_invention.falsifier.checkers import (
    AttackResult,
    check_all,
    check_attack,
    false_zero_count,
    true_newton_dd_control,
)
from research.representation_invention.falsifier.obligations_probe import (
    discover_obligations_api,
    probe_all,
    probe_case,
)

__all__ = [
    "ATTACK_CASES",
    "ATTACK_IDS",
    "CASES_BY_ID",
    "MATH_NONZERO_IDS",
    "TAUTOLOGY_RESIDUAL_IDS",
    "AttackResult",
    "check_all",
    "check_attack",
    "discover_obligations_api",
    "export_fixtures",
    "false_zero_count",
    "load_attack_cases",
    "probe_all",
    "probe_case",
    "true_newton_dd_control",
]
