"""Laurent series of a rational prefactor in ``t = var - point``.

Sparse maps only. No combined-kernel together.
"""
from research.coefficient_laurent.rational.expand import (
    convolve,
    expand_rational,
    pole_order,
)

__all__ = [
    "convolve",
    "expand_rational",
    "pole_order",
]
