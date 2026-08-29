"""Adversarial falsifier for remainder certificates. Attack only."""
from __future__ import annotations

from research.remainder_certification.falsifier.cases import (
    ATTACK_CASES,
    ATTACK_IDS,
    ATTACK_KINDS,
    CASES_BY_ID,
    CONTROL_CASES,
    CONTROL_IDS,
    is_class_c_or_d,
    load_all_cases,
    load_attack_cases,
    load_class_c_attacks,
    load_control_cases,
)
from research.remainder_certification.falsifier.checkers import (
    CaseResult,
    check_all,
    check_case,
    check_controls,
    claimed_certificate,
    discover_compile_remainder,
    false_certified_count,
    forbidden_ignore_remainder,
    local_remainder_verdict,
    run_cases,
)

__all__ = [
    "ATTACK_CASES",
    "ATTACK_IDS",
    "ATTACK_KINDS",
    "CASES_BY_ID",
    "CONTROL_CASES",
    "CONTROL_IDS",
    "CaseResult",
    "check_all",
    "check_case",
    "check_controls",
    "claimed_certificate",
    "discover_compile_remainder",
    "false_certified_count",
    "forbidden_ignore_remainder",
    "is_class_c_or_d",
    "load_all_cases",
    "load_attack_cases",
    "load_class_c_attacks",
    "load_control_cases",
    "local_remainder_verdict",
    "run_cases",
]
