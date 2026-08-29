"""Assumption-leak auditor. Hidden hypotheses cannot CERTIFY or mint hop ZERO."""
from research.remainder_certification.assumption_audit.scan import (
    RULE_IDS,
    AssumptionLeak,
    apply_assumption_gate,
    audit_certificate,
    blocks_certified,
    blocks_hop_zero_promotion,
    certificate_silent_leaks,
    engine_path,
    has_hidden_hypotheses,
    iter_remainder_python,
    scan_all,
    scan_engine,
    scan_remainder_python,
    scan_text,
)

__all__ = [
    "RULE_IDS",
    "AssumptionLeak",
    "apply_assumption_gate",
    "audit_certificate",
    "blocks_certified",
    "blocks_hop_zero_promotion",
    "certificate_silent_leaks",
    "engine_path",
    "has_hidden_hypotheses",
    "iter_remainder_python",
    "scan_all",
    "scan_engine",
    "scan_remainder_python",
    "scan_text",
]
