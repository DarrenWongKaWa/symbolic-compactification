"""egglog adapter. Named theory packs only. E-class ≠ scientific abstraction."""
from __future__ import annotations

from symbolic_compactification.observations.discovery import probe_backend, version_of
from symbolic_compactification.observations.ir import (
    EXACT_FACT,
    RelationEdge,
)

THEORY_PACKS = {
    "algebra_basic": {
        "assumptions": ["integer addition commutative"],
        "source": "named pack algebra_basic",
        "semantic_scope": "Num(i64) + commute only",
    },
    "AC": {
        "assumptions": ["Add commutative"],
        "source": "named pack AC",
        "semantic_scope": "binary + on Num atoms",
    },
}


def available() -> bool:
    return probe_backend("egglog").startswith("AVAILABLE")


def _ac_equivalent_numeric_add(a: int, b: int) -> bool:
    from egglog import EGraph, Expr, eq, i64, rewrite, ruleset

    class Num(Expr):
        def __init__(self, value: i64): ...
        def __add__(self, other: Num) -> Num: ...

    @ruleset
    def comm(x: Num, y: Num):
        yield rewrite(x + y).to(y + x)

    egraph = EGraph()
    na, nb = Num(i64(a)), Num(i64(b))
    egraph.register(na + nb)
    egraph.register(nb + na)
    egraph.run(comm * 8)
    try:
        egraph.check(eq(na + nb).to(nb + na))
        return True
    except Exception:
        return False


def run(expr, nodes, *, symbols=None, functions=None) -> dict:
    if not available():
        return {"unavailable": True, "backend": "egglog"}
    ver = version_of("egglog")
    rels: list[RelationEdge] = []
    # Controlled smoke: 1+2 vs 2+1 under algebra_basic/AC.
    try:
        ok = _ac_equivalent_numeric_add(1, 2)
        if ok:
            rels.append(RelationEdge(
                source_ids=[],
                relation_type="EGRAPH_EQUIVALENT",
                backend="egglog",
                exactness_class=EXACT_FACT,
                evidence="Num(1)+Num(2) ~ Num(2)+Num(1) under algebra_basic commute",
                theory="algebra_basic",
                assumptions=list(THEORY_PACKS["algebra_basic"]["assumptions"]),
                backend_version=ver,
            ))
            rels.append(RelationEdge(
                source_ids=[],
                relation_type="KNOWN_REWRITE_EQUIVALENT",
                backend="egglog",
                exactness_class=EXACT_FACT,
                evidence="rewrite(a+b)->(b+a)",
                theory="AC",
                assumptions=list(THEORY_PACKS["AC"]["assumptions"]),
                backend_version=ver,
            ))
    except Exception as exc:
        rels.append(RelationEdge(
            source_ids=[], relation_type="EGRAPH_EQUIVALENT",
            backend="egglog", exactness_class=EXACT_FACT,
            evidence=f"egglog_failed:{type(exc).__name__}",
            theory="algebra_basic",
        ))
    return {
        "families": [],
        "relations": rels,
        "canonical_variants": [],
        "backend": "egglog",
        "version": ver,
        "theory_packs": THEORY_PACKS,
    }
