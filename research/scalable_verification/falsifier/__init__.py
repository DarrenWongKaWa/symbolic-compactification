"""Adversarial falsifier for Track-V compositional verification. Attack only."""
from __future__ import annotations

from research.scalable_verification.falsifier.cases import (
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CASES_BY_ID,
    CONTROL_CASES,
    CONTROL_IDS,
    load_attack_cases,
)
from research.scalable_verification.falsifier.checkers import (
    AttackResult,
    check_all,
    check_attack,
    check_controls,
    false_zero_count,
    local_check,
    report,
)
from research.scalable_verification.falsifier.engines import (
    discover_engines,
    probe_engines,
)

__all__ = [
    "ATTACK_CASES",
    "ATTACK_IDS",
    "ATTACK_KINDS",
    "AttackResult",
    "CASES_BY_ID",
    "CONTROL_CASES",
    "CONTROL_IDS",
    "check_all",
    "check_attack",
    "check_controls",
    "discover_engines",
    "false_zero_count",
    "load_attack_cases",
    "local_check",
    "probe_engines",
    "report",
]
