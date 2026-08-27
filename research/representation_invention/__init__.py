"""Verified Representation Invention v1 — experimental line.

Frozen historical artifacts are read-only. New code lives under this tree.
"""

from research.representation_invention.schema import (
    PARSE_FAILURE,
    OK,
    ABSTAIN,
    REPRESENTATION_TYPES,
    RepresentationHypothesisV2,
    parse_hypothesis_v2,
)

__all__ = [
    "PARSE_FAILURE",
    "OK",
    "ABSTAIN",
    "REPRESENTATION_TYPES",
    "RepresentationHypothesisV2",
    "parse_hypothesis_v2",
]
