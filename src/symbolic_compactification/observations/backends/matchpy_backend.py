"""MatchPy adapter: AC/associative pattern matching. Matching ≠ scientific identity."""
from __future__ import annotations

from typing import Any

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification.observations.discovery import probe_backend, version_of
from symbolic_compactification.observations.ir import (
    DESCRIPTIVE_FACT,
    CanonicalVariant,
    ObservationFamily,
    RelationEdge,
)
from symbolic_compactification.observations.nodes import index_by_srepr


def available() -> bool:
    return probe_backend("matchpy").startswith("AVAILABLE")


def _ops():
    from matchpy import Arity, Operation
    Add = Operation.new("Add", Arity.variadic, "Add",
                        associative=True, commutative=True)
    Mul = Operation.new("Mul", Arity.variadic, "Mul",
                        associative=True, commutative=True)
    return Add, Mul


def sympy_to_matchpy(expr: sympy.Expr, Add, Mul, Symbol):
    if isinstance(expr, sympy.Add):
        return Add(*[sympy_to_matchpy(a, Add, Mul, Symbol) for a in expr.args])
    if isinstance(expr, sympy.Mul):
        return Mul(*[sympy_to_matchpy(a, Add, Mul, Symbol) for a in expr.args])
    if expr.is_Symbol:
        return Symbol(expr.name)
    if isinstance(expr, AppliedUndef):
        # treat as opaque symbol of printed form
        return Symbol(str(expr))
    if expr.is_Number:
        return Symbol(str(expr))
    return Symbol(str(expr))


def matchpy_to_str(obj: Any) -> str:
    return str(obj)


def run(expr: sympy.Expr, nodes, *, symbols=None, functions=None) -> dict:
    if not available():
        return {"unavailable": True, "backend": "matchpy"}
    from matchpy import Symbol, Wildcard, substitute, replace_all
    Add, Mul = _ops()
    ver = version_of("matchpy")
    by = index_by_srepr(nodes)
    rels: list[RelationEdge] = []
    fams: list[ObservationFamily] = []
    variants: list[CanonicalVariant] = []

    try:
        mp = sympy_to_matchpy(expr, Add, Mul, Symbol)
        # Round-trip check on Add/Mul-only fragments is done in tests;
        # here we match terms against an AC Add of two dots.
        terms = list(sympy.Add.make_args(expr))
        mp_terms = [sympy_to_matchpy(t, Add, Mul, Symbol) for t in terms]
        # AC: two Mul terms that match Mul(x, y) vs Mul(y, x)
        if len(mp_terms) >= 2:
            x = Wildcard.dot("x")
            y = Wildcard.dot("y")
            from matchpy import Pattern, match
            pat = Pattern(Mul(x, y))
            hits = []
            for t, mt in zip(terms, mp_terms):
                try:
                    ms = list(match(mt, pat))
                except Exception:
                    ms = []
                if ms:
                    hits.append((t, mt))
            if len(hits) >= 2:
                ids = []
                for t, _mt in hits:
                    i = by.get(sympy.srepr(t))
                    if i:
                        ids.append(i)
                ids = list(dict.fromkeys(ids))
                if len(ids) >= 2:
                    fams.append(ObservationFamily(
                        "mp_ac_mul", ids, "PATTERN_MATCH", "matchpy",
                        "Mul(x,y) AC pattern",
                    ))
                    rels.append(RelationEdge(
                        source_ids=ids,
                        relation_type="PATTERN_MATCH",
                        backend="matchpy",
                        exactness_class=DESCRIPTIVE_FACT,
                        evidence="MatchPy AC Mul(x,y) many-to-one",
                        backend_version=ver,
                    ))
                    rels.append(RelationEdge(
                        source_ids=ids,
                        relation_type="AC_EQUIVALENT",
                        backend="matchpy",
                        exactness_class=DESCRIPTIVE_FACT,
                        evidence="same AC Mul pattern (not scientific object)",
                        theory="AC",
                        backend_version=ver,
                    ))
        rid = by.get(sympy.srepr(expr))
        if rid:
            variants.append(CanonicalVariant(
                rid, matchpy_to_str(mp), "matchpy_tree", "matchpy"))
    except Exception as exc:
        rels.append(RelationEdge(
            source_ids=[], relation_type="PATTERN_MATCH", backend="matchpy",
            exactness_class=DESCRIPTIVE_FACT,
            evidence=f"matchpy_failed:{type(exc).__name__}",
        ))
    return {
        "families": fams, "relations": rels,
        "canonical_variants": variants, "backend": "matchpy", "version": ver,
    }
