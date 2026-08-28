"""Track V3 — iterated one-parameter confluence for multi-branch kernels.

No new LLM calls. Frozen V2 Guo families only. Track D2 remains locked
until a frozen family is FAMILY_ZERO or FAMILY_NONZERO.
"""
from research.iterated_confluence.schema import (
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_UNKNOWN,
    PATH_ZERO,
    IntermediateExpression,
    IteratedConfluenceCertificate,
    PathCertificate,
    PathConsistencyObligation,
    PathStep,
    compose_family_verdict,
    compose_path_verdict,
)

__all__ = [
    "PATH_ZERO",
    "PATH_NONZERO",
    "PATH_UNKNOWN",
    "FAMILY_ZERO",
    "FAMILY_NONZERO",
    "FAMILY_UNKNOWN",
    "CONSISTENT_ZERO",
    "INCONSISTENT_NONZERO",
    "CONSISTENCY_UNKNOWN",
    "PathStep",
    "PathCertificate",
    "PathConsistencyObligation",
    "IntermediateExpression",
    "IteratedConfluenceCertificate",
    "compose_path_verdict",
    "compose_family_verdict",
]
