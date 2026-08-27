"""Relation graph: facts only for safe deterministic edges."""
from __future__ import annotations

from dataclasses import dataclass, field

import sympy
from sympy.core.function import AppliedUndef

from research.abstraction_invention.beyond.canonicalize import canon_ac, canon_expand
from research.abstraction_invention.prototype.antiunify import lgg_pair


@dataclass
class Edge:
    src: str
    dst: str
    kind: str  # identical, substitution, permutation, derivative, algebraic
    note: str = ""


@dataclass
class RelationGraph:
    nodes: list[str] = field(default_factory=list)
    edges: list[Edge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": self.nodes,
            "edges": [e.__dict__ for e in self.edges],
        }


def _terms(expr: sympy.Expr) -> list[sympy.Expr]:
    return list(sympy.Add.make_args(expr))


def build_graph(expr: sympy.Expr) -> RelationGraph:
    terms = _terms(expr)
    g = RelationGraph(nodes=[str(t) for t in terms])
    for i, a in enumerate(terms):
        for b in terms[i + 1:]:
            if a == b:
                g.edges.append(Edge(str(a), str(b), "identical"))
                continue
            if canon_ac(a) == canon_ac(b) or canon_expand(a) == canon_expand(b):
                g.edges.append(Edge(str(a), str(b), "algebraic", "canon"))
                continue
            for x in list(a.free_symbols)[:4]:
                try:
                    da = sympy.diff(a, x)
                    if da == b or sympy.expand(da - b) == 0:
                        g.edges.append(Edge(str(a), str(b), "derivative", str(x)))
                except Exception:
                    pass
            # permutation of two symbols
            syms = list(a.free_symbols)
            if len(syms) >= 2:
                x, y = syms[0], syms[1]
                swapped = a.xreplace({x: y, y: x})
                if swapped == b:
                    g.edges.append(Edge(str(a), str(b), "permutation", f"{x},{y}"))
            gen = lgg_pair(a, b)
            if gen.useful():
                g.edges.append(Edge(str(a), str(b), "substitution", str(gen.template)))
    return g
