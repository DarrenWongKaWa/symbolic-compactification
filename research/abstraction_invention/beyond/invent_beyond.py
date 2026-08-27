"""B2–B5 inventors. Frozen LGG is a callee, not edited."""
from __future__ import annotations

from research.abstraction_invention.beyond.ac_lgg import lgg_after_canon
from research.abstraction_invention.beyond.canonicalize import canon_expand
from research.abstraction_invention.beyond.relations import build_graph
from research.abstraction_invention.beyond.score import rank_records, score_hypothesis
from research.abstraction_invention.prototype.inventor import invent_from_expression
from research.abstraction_invention.prototype.schema import (
    AbstractionHypothesis,
    InstanceMap,
)
from symbolic_compactification import parse_expression

import sympy


def b2_filtered_lgg(text, symbols, functions) -> list[AbstractionHypothesis]:
    hyps = invent_from_expression(text, symbols, functions)
    kept = []
    for h in hyps:
        sc = score_hypothesis(h.template, h.family, symbols=symbols, functions=functions)
        if sc["keep"] or h.operator == "master_derivative":
            kept.append(h)
    return kept


def b3_canon_equal(text, symbols, functions) -> list[dict]:
    """Algebraic equivalence of top-level terms after expand/AC. Not invention."""
    expr = parse_expression(text, symbols, functions=functions or None)
    terms = list(sympy.Add.make_args(expr))
    out = []
    for i, a in enumerate(terms):
        for b in terms[i + 1:]:
            if a == b:
                continue
            if canon_expand(a) == canon_expand(b):
                out.append({
                    "operator": "algebraic_equivalence",
                    "family": [str(a), str(b)],
                    "note": "equal_after_expand",
                    "invention": False,
                })
    return out


def b4_ac_lgg(text, symbols, functions) -> list[dict]:
    expr = parse_expression(text, symbols, functions=functions or None)
    terms = list(sympy.Add.make_args(expr))
    out = []
    for i, a in enumerate(terms):
        for b in terms[i + 1:]:
            g = lgg_after_canon(a, b, expand=True)
            rec = {
                "operator": "ac_lgg",
                "family": [str(a), str(b)],
                "template": str(getattr(g, "template", "")),
                "exact_after_canon": bool(getattr(g, "exact_after_canon", False)
                                          or getattr(g, "n_holes", 1) == 0),
                "useful_lgg": bool(getattr(g, "useful", lambda: False)()),
            }
            out.append(rec)
    return out


def b5_operator_graph(text, symbols, functions) -> dict:
    expr = parse_expression(text, symbols, functions=functions or None)
    graph = build_graph(expr)
    deriv = [e for e in graph.edges if e.kind == "derivative"]
    alg = [e for e in graph.edges if e.kind == "algebraic"]
    perm = [e for e in graph.edges if e.kind == "permutation"]
    hyps = []
    for e in deriv:
        hyps.append(AbstractionHypothesis(
            operator="master_derivative",
            family=[e.src, e.dst],
            latent_variables=[e.note],
            template=e.src,
            instance_maps=[
                InstanceMap(e.src, {}, "identity"),
                InstanceMap(e.dst, {e.note: e.note}, "d/dtheta"),
            ],
            reason=f"relation-graph derivative wrt {e.note}",
            source="operator_graph",
        ))
    return {
        "graph": graph.to_dict(),
        "n_derivative": len(deriv),
        "n_algebraic": len(alg),
        "n_permutation": len(perm),
        "hypotheses": [h.to_dict() for h in hyps],
    }
