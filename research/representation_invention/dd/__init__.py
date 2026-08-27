"""Generic Newton / Hermite divided-difference constructors.

Public API is generic mathematics. Source instantiation of catalog
members onto ``F[nodes]`` is G/C, not this package.

Layers (do not mix):
- definition: ``newton_first``, ``repeated_diagonal``
- recurrence: ``newton_table``, ``hermite_dd``
- confluence identity: ``limit_generic_to_degenerate``
- source instantiation: not here
"""
from research.representation_invention.dd.confluence import (
    ConfluenceLimitError,
    limit_generic_to_degenerate,
)
from research.representation_invention.dd.hermite import (
    HermiteDDError,
    hermite_dd,
    repeated_diagonal,
)
from research.representation_invention.dd.newton import newton_first, newton_table

__all__ = [
    "newton_first",
    "newton_table",
    "repeated_diagonal",
    "hermite_dd",
    "HermiteDDError",
    "limit_generic_to_degenerate",
    "ConfluenceLimitError",
]
