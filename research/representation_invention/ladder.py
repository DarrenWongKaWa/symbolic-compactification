"""Frozen evaluation ladder R0–R8.

R-level of a hypothesis is determined by verified structure, not by the
string `representation_type`. Type→R is only a proposer hint.
"""
from __future__ import annotations

from typing import Optional

from research.representation_invention.schema import RepresentationHypothesisV2

R_LEVELS = ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8")

R_DEFINITIONS = {
    "R0": "Local confluence: one generic expression tends exactly to one degenerate branch.",
    "R1": "First Newton divided difference F[x,y] with explicit generic formula.",
    "R2": "Repeated-node divided difference F[x,x] or F[x,x,y].",
    "R3": "Higher-order Hermite divided difference (multiple repeated nodes / higher degeneracy).",
    "R4": "Piecewise-to-DD unification: several explicit branches reconstructed as one DD family.",
    "R5": "Special-function DD: same structure when F contains special functions (e.g. polygamma).",
    "R6": "Master analytic object: several distinct kernels from one latent F by operators.",
    "R7": "Representation-level scientific compactification of a sector by a small master set.",
    "R8": "Generator / invariant basis: geometric or symmetry-adapted representation.",
}

TYPE_TO_R_HINT = {
    "local_confluence": "R0",
    "divided_difference": "R1",
    "hermite_divided_difference": "R2",
    "derivative_family": "R6",
    "recurrence_family": "R6",
    "master_function": "R6",
    "generating_function": "R7",
    "invariant_basis": "R8",
    "tensor_generator": "R8",
    "other_explicit": None,
}

# Guo DEV success boundaries (evaluation labels, not proposer hints).
G_LEVELS = ("G0", "G1", "G2", "G3", "G4", "G5", "G6")

G_DEFINITIONS = {
    "G0": "grounded local relation",
    "G1": "multiple local confluence relations",
    "G2": "explicit Newton DD",
    "G3": "explicit Hermite / repeated-node DD",
    "G4": "one grounded master analytic object explains multiple branch families",
    "G5": "multiple sectors reconstructed using a small master library",
    "G6": "geometric / invariant generators",
}


def type_r_hint(representation_type: str) -> Optional[str]:
    return TYPE_TO_R_HINT.get(representation_type)


def r_rank(level: Optional[str]) -> int:
    if level not in R_LEVELS:
        return -1
    return R_LEVELS.index(level)


def max_r(levels: list[str]) -> Optional[str]:
    ranked = [lv for lv in levels if lv in R_LEVELS]
    if not ranked:
        return None
    return max(ranked, key=r_rank)


def hint_from_hypothesis(h: RepresentationHypothesisV2) -> Optional[str]:
    return type_r_hint(h.representation_type)
