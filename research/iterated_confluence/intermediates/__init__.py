"""Exact source-derived intermediates. No heuristic interpolation. No LLM."""
from research.iterated_confluence.intermediates.build import (
    EQ_IMPOSITION,
    SUBSTITUTION,
    IntermediateBuild,
    build_intermediate,
)
from research.iterated_confluence.intermediates.lattice import (
    FROZEN_PATH,
    frozen_source_lattice_coverage,
    intermediates_required_for_frozen_families,
)

__all__ = [
    "EQ_IMPOSITION",
    "SUBSTITUTION",
    "IntermediateBuild",
    "build_intermediate",
    "FROZEN_PATH",
    "frozen_source_lattice_coverage",
    "intermediates_required_for_frozen_families",
]
