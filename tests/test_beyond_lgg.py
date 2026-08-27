"""Beyond-LGG controls. Does not modify frozen antiunify.py or B9."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.abstraction_invention.beyond.canonicalize import canon_expand
from research.abstraction_invention.beyond.invent_beyond import b3_canon_equal, b5_operator_graph
from research.abstraction_invention.beyond.score import rank_records, score_hypothesis
from symbolic_compactification import parse_expression


def _s(*n):
    return [{"name": x, "real": True} for x in n]


def test_score_ranks_polygamma_above_shallow_without_gold():
    recs = [
        {"template": "I*mu*theta0", "family": ["-I*mu", "I*beta*mu"]},
        {"template": (
            "theta0*theta1*(polygamma(theta2, z) + polygamma(theta2, z))"
        ), "family": [
            "-3*pi*(polygamma(2, z) + polygamma(2, z))",
            "beta*gamma*(polygamma(3, z) + polygamma(3, z))",
        ]},
    ]
    ranked = rank_records(recs, symbols=_s("mu", "beta", "gamma", "z"))
    assert ranked[0]["template"].startswith("theta0") or "polygamma" in ranked[0]["template"]
    assert ranked[0]["score"]["S"] > ranked[-1]["score"]["S"]
    assert "I*mu*theta0" in ranked[-1]["template"] or ranked[-1]["score"]["S"] < ranked[0]["score"]["S"]


def test_canon_expand_solves_distrib():
    syms = _s("x", "y", "z")
    a = parse_expression("x*(y + z)", syms, functions=None)
    b = parse_expression("x*y + x*z", syms, functions=None)
    assert canon_expand(a) == canon_expand(b)
    hits = b3_canon_equal(
        "F(x*(y + z)) + F(x*y + x*z)", syms, ["F"],
    )
    assert hits and hits[0]["operator"] == "algebraic_equivalence"


def test_canon_does_not_equate_wrong_distrib():
    hits = b3_canon_equal(
        "F(x*(y + z)) + F(x*y + w*z)",
        _s("x", "y", "z", "w"), ["F"],
    )
    assert hits == []


def test_permutation_edge_on_swap():
    g = b5_operator_graph("T(i, j) + T(j, i)", _s("i", "j"), ["T"])
    assert g["n_permutation"] >= 1
