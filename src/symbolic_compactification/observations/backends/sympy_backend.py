"""SymPy observation adapter. Equality claims are witnesses, not promotions."""
from __future__ import annotations

from collections import defaultdict

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification.observations.discovery import version_of
from symbolic_compactification.observations.ir import (
    CANDIDATE_RELATION,
    DESCRIPTIVE_FACT,
    EXACT_FACT,
    CanonicalVariant,
    ObservationFamily,
    RelationEdge,
)
from symbolic_compactification.observations.nodes import index_by_srepr
from symbolic_compactification.structure import ordered_atoms


def run(expr: sympy.Expr, nodes, *, symbols=None, functions=None) -> dict:
    ver = version_of("sympy")
    by = index_by_srepr(nodes)
    rels: list[RelationEdge] = []
    fams: list[ObservationFamily] = []
    variants: list[CanonicalVariant] = []

    def nid(e) -> str | None:
        return by.get(sympy.srepr(e))

    # CSE (syntactic)
    try:
        repls, _red = sympy.cse(expr)
        for i, (sym, val) in enumerate(repls):
            vid = nid(val)
            if vid:
                rels.append(RelationEdge(
                    source_ids=[vid],
                    relation_type="CSE_SHARED",
                    backend="sympy",
                    exactness_class=DESCRIPTIVE_FACT,
                    evidence=f"sympy.cse replacement {sym}",
                    witness=str(val),
                    backend_version=ver,
                ))
                fams.append(ObservationFamily(
                    family_id=f"cse_{i}",
                    member_ids=[vid],
                    kind="CSE_SHARED",
                    backend="sympy",
                    note=str(sym),
                ))
    except Exception as exc:
        rels.append(RelationEdge(
            source_ids=[], relation_type="CSE_SHARED", backend="sympy",
            exactness_class=CANDIDATE_RELATION,
            evidence=f"cse_failed:{type(exc).__name__}",
        ))

    # AC / canonical Add-Mul sort as descriptive variant
    try:
        sorted_add = sympy.Add(*sorted(sympy.Add.make_args(expr),
                                       key=lambda a: sympy.srepr(a)),
                               evaluate=False) if isinstance(expr, sympy.Add) else expr
        rid = nid(expr)
        if rid:
            variants.append(CanonicalVariant(
                rid, str(sorted_add), "add_mul_srepr_sort", "sympy"))
    except Exception:
        pass

    # function families (descriptive)
    calls: dict[str, list] = defaultdict(list)
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, AppliedUndef):
            calls[type(sub).__name__].append(sub)
    fi = 0
    for name, occs in sorted(calls.items()):
        ids = [nid(o) for o in occs if nid(o)]
        ids = list(dict.fromkeys(ids))
        if len(ids) >= 2:
            fams.append(ObservationFamily(
                family_id=f"fn_{fi}", member_ids=ids,
                kind="SAME_FUNCTION_FAMILY", backend="sympy", note=name,
            ))
            rels.append(RelationEdge(
                source_ids=ids, relation_type="SAME_FUNCTION_FAMILY",
                backend="sympy", exactness_class=DESCRIPTIVE_FACT,
                evidence=f"AppliedUndef name={name} n={len(ids)}",
                backend_version=ver,
            ))
            fi += 1

    # denominator / pole signature (descriptive)
    dens = []
    for sub in sympy.preorder_traversal(expr):
        if isinstance(sub, sympy.Pow) and sub.exp.is_Integer and int(sub.exp) < 0:
            dens.append(sub.base)
    by_sig: dict[str, list] = defaultdict(list)
    for d in dens:
        sig = ",".join(sorted(s.name for s in d.free_symbols))
        i = nid(d)
        if i:
            by_sig[sig].append(i)
    for k, ids in by_sig.items():
        ids = list(dict.fromkeys(ids))
        if len(ids) >= 2:
            rels.append(RelationEdge(
                source_ids=ids, relation_type="SAME_POLE_SIGNATURE",
                backend="sympy", exactness_class=DESCRIPTIVE_FACT,
                evidence=f"denominator free-symbol signature {k}",
                backend_version=ver,
            ))
            rels.append(RelationEdge(
                source_ids=ids, relation_type="SAME_DENOMINATOR_FAMILY",
                backend="sympy", exactness_class=DESCRIPTIVE_FACT,
                evidence="shared denom symbol set (not algebraic identity)",
                backend_version=ver,
            ))

    # Piecewise inventory (descriptive)
    for pw in ordered_atoms(expr, sympy.Piecewise):
        pid = nid(pw)
        if not pid:
            continue
        n_br = len(pw.args)
        rels.append(RelationEdge(
            source_ids=[pid], relation_type="SAME_BRANCH_DEPENDENCY",
            backend="sympy", exactness_class=DESCRIPTIVE_FACT,
            evidence=f"Piecewise n_branches={n_br}",
            backend_version=ver,
        ))

    # permutation of 2-arg AppliedUndef (descriptive orbit, not "generator")
    seen_pair = set()
    apps = [s for s in sympy.preorder_traversal(expr) if isinstance(s, AppliedUndef) and len(s.args) == 2]
    for i, a in enumerate(apps):
        for b in apps[i + 1:]:
            if type(a).__name__ != type(b).__name__:
                continue
            if a.args == b.args[::-1] and a.args != b.args:
                key = tuple(sorted((sympy.srepr(a), sympy.srepr(b))))
                if key in seen_pair:
                    continue
                seen_pair.add(key)
                ia, ib = nid(a), nid(b)
                if ia and ib:
                    rels.append(RelationEdge(
                        source_ids=[ia, ib],
                        relation_type="PERMUTATION_RELATED",
                        backend="sympy", exactness_class=DESCRIPTIVE_FACT,
                        evidence="args reversed",
                        backend_version=ver,
                    ))
                    rels.append(RelationEdge(
                        source_ids=[ia, ib],
                        relation_type="SAME_INDEX_ORBIT",
                        backend="sympy", exactness_class=DESCRIPTIVE_FACT,
                        evidence="two-arg index swap (descriptive orbit only)",
                        backend_version=ver,
                    ))

    # derivative related — witness via sympy.diff, still not a master function
    subs = []
    for s in sympy.preorder_traversal(expr):
        if getattr(s, "args", ()) and not isinstance(s, (sympy.Rel, sympy.Piecewise)):
            subs.append(s)
        if len(subs) >= 40:
            break
    n_d = 0
    for i, a in enumerate(subs):
        if n_d >= 8:
            break
        for x in list(a.free_symbols)[:2]:
            try:
                da = sympy.diff(a, x)
            except Exception:
                continue
            for b in subs[i + 1:]:
                try:
                    if da == b or sympy.expand(da - b) == 0:
                        ia, ib = nid(a), nid(b)
                        if ia and ib:
                            rels.append(RelationEdge(
                                source_ids=[ia, ib],
                                relation_type="DERIVATIVE_RELATED",
                                backend="sympy",
                                exactness_class=EXACT_FACT,
                                evidence=f"sympy.diff wrt {x}",
                                witness=f"diff({a},{x}) == {b}",
                                assumptions=["declared sympy.diff semantics"],
                                backend_version=ver,
                            ))
                            n_d += 1
                except TypeError:
                    continue

    # IDENTICAL nodes sharing hash
    by_hash: dict[str, list[str]] = defaultdict(list)
    for n in nodes:
        by_hash[n.structural_hash].append(n.node_id)
    for h, ids in by_hash.items():
        if len(ids) >= 2:
            rels.append(RelationEdge(
                source_ids=ids, relation_type="IDENTICAL",
                backend="sympy", exactness_class=EXACT_FACT,
                evidence="equal structural_hash/srepr",
                backend_version=ver,
            ))

    return {
        "families": fams,
        "relations": rels,
        "canonical_variants": variants,
        "backend": "sympy",
        "version": ver,
    }
