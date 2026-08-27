"""Wrap frozen first-order LGG. Do not rewrite antiunify.py."""
from __future__ import annotations

import sympy

from symbolic_compactification.observations.discovery import probe_backend
from symbolic_compactification.observations.ir import (
    CANDIDATE_RELATION,
    ObservationFamily,
    RelationEdge,
)
from symbolic_compactification.observations.nodes import index_by_srepr

FROZEN_SHA = "efc0924"


def available() -> bool:
    return probe_backend("lgg").startswith("AVAILABLE")


def run(expr: sympy.Expr, nodes, *, symbols=None, functions=None) -> dict:
    if not available():
        return {"unavailable": True, "backend": "lgg"}
    from research.abstraction_invention.prototype.antiunify import lgg_pair
    try:
        from research.abstraction_invention.beyond.score import score_hypothesis
    except Exception:
        score_hypothesis = None

    by = index_by_srepr(nodes)
    terms = list(sympy.Add.make_args(expr))
    rels: list[RelationEdge] = []
    fams: list[ObservationFamily] = []
    n = 0
    for i, a in enumerate(terms):
        for b in terms[i + 1:]:
            if n >= 12:
                break
            if a == b:
                continue
            gen = lgg_pair(a, b)
            if not gen.useful():
                continue
            ia, ib = by.get(sympy.srepr(a)), by.get(sympy.srepr(b))
            ids = [x for x in (ia, ib) if x]
            sc = None
            if score_hypothesis is not None:
                try:
                    sc = score_hypothesis(str(gen.template), [str(a), str(b)])
                except Exception:
                    sc = None
            fams.append(ObservationFamily(
                family_id=f"lgg_{n}",
                member_ids=ids,
                kind="LGG_FAMILY",
                backend="lgg",
                note=str(gen.template),
            ))
            rels.append(RelationEdge(
                source_ids=ids,
                relation_type="LGG_FAMILY",
                backend="lgg",
                exactness_class=CANDIDATE_RELATION,
                evidence=(
                    f"frozen LGG template={gen.template} holes={gen.n_holes} "
                    f"score={sc} sha={FROZEN_SHA}"
                ),
                witness=str(gen.substitutions),
                backend_version=FROZEN_SHA,
            ))
            rels.append(RelationEdge(
                source_ids=ids,
                relation_type="SUBSTITUTION_INSTANCE",
                backend="lgg",
                exactness_class=CANDIDATE_RELATION,
                evidence="instance maps of frozen LGG (not certified promotion)",
                backend_version=FROZEN_SHA,
            ))
            n += 1
    return {
        "families": fams, "relations": rels, "canonical_variants": [],
        "backend": "lgg", "version": FROZEN_SHA,
    }
