"""Polygamma derivative chain. Taylor coefficients only; no remainder CERTIFIED."""
from research.remainder_certification.derivatives.chain import (
    DIFF_IDENTITY,
    DOMAIN_OWNER,
    METHOD,
    R_MAX_CAP,
    TAYLOR_IDENTITY,
    DerivativeChainCoeffs,
    polygamma_diff,
    polygamma_taylor_coefficient,
    polygamma_taylor_coefficients,
)

__all__ = [
    "DIFF_IDENTITY",
    "DOMAIN_OWNER",
    "METHOD",
    "R_MAX_CAP",
    "TAYLOR_IDENTITY",
    "DerivativeChainCoeffs",
    "polygamma_diff",
    "polygamma_taylor_coefficient",
    "polygamma_taylor_coefficients",
]
