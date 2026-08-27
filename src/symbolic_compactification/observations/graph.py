"""Merge backend observations into a Scientific Relation Graph.

Duplicate backends for one relation are preserved, not OR-collapsed.
"""
from __future__ import annotations

from symbolic_compactification.observations.ir import ObservationBundle, RelationEdge


def merge_relations(*groups: list[RelationEdge]) -> list[RelationEdge]:
    out: list[RelationEdge] = []
    seen = set()
    for g in groups:
        for r in g:
            key = (
                r.relation_type, r.backend, tuple(r.source_ids),
                r.exactness_class, r.evidence,
            )
            if key in seen:
                continue
            seen.add(key)
            out.append(r)
    return out
