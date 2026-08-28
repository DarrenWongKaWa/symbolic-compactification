"""Track V / V1 — compositional proof-decomposition planner.

Does not decide ZERO. See PROOF_DECOMPOSITION.md.
"""
from research.scalable_verification.decomposition.decompose import (
    DD_CERTIFICATE,
    DIRECT,
    EQUALITY,
    FACTOR_LOCAL,
    HERMITE_DD,
    LIMIT,
    NEWTON_DD,
    RELATIONS,
    SERIES_LOCAL,
    SPECIAL_FUNCTION_LOCAL,
    Composition,
    DecompositionPlan,
    ObligationStep,
    certify_composition,
    certify_identical_cancel,
    decompose,
)

__all__ = [
    "EQUALITY",
    "LIMIT",
    "NEWTON_DD",
    "HERMITE_DD",
    "RELATIONS",
    "DIRECT",
    "FACTOR_LOCAL",
    "SERIES_LOCAL",
    "DD_CERTIFICATE",
    "SPECIAL_FUNCTION_LOCAL",
    "Composition",
    "DecompositionPlan",
    "ObligationStep",
    "certify_composition",
    "certify_identical_cancel",
    "decompose",
]
