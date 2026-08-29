"""Exact affine argument normalizer. Residual must be 0; else UNSUPPORTED."""
from research.remainder_certification.affine.normalize import (
    AffineNormalization,
    AffineResult,
    UNSUPPORTED,
    normalize_affine,
)

__all__ = [
    "AffineNormalization",
    "AffineResult",
    "UNSUPPORTED",
    "normalize_affine",
]
