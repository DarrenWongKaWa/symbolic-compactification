"""One-parameter edge verifier (Track V3-D).

Split spectators first, then run the Track V cascade on local kernels.
Timeout and size-guard are UNKNOWN, never ZERO. No Guo identities. No LLM.
"""
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.iterated_confluence.edges.certify import (
    FULL_OPS_CAP,
    LIMIT_OPS_CAP,
    OneParameterCertificate,
    certify_one_parameter,
)

__all__ = [
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "FULL_OPS_CAP",
    "LIMIT_OPS_CAP",
    "OneParameterCertificate",
    "certify_one_parameter",
]
