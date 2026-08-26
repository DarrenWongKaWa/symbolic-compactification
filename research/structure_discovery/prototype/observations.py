"""Deterministic structural observations. Facts only — no target structures.

Every feature is documented in observations/FEATURES.md. Observations must
not mention gold names, reconstruction targets, or hidden polarity.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

import sympy
from sympy.core.function import AppliedUndef

from symbolic_compactification import parse_expression, structure_summary
from symbolic_compactification.structure import ordered_atoms

_MAX_NODES = 4000
_MAX_ITEMS = 24


def _text(e: sympy.Expr) -> str:
    return str(e)


def _srepr(e: sympy.Expr) -> str:
    return sympy.srepr(e)


def _ops(e: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(e))
    except Exception:
        return 0


def _walk(expr: sympy.Expr):
    n = 0
    for sub in sympy.preorder_traversal(expr):
        n += 1
        if n > _MAX_NODES:
            break
        yield sub


def _terms(expr: sympy.Expr) -> list[sympy.Expr]:
    if isinstance(expr, sympy.Add):
        return list(expr.args)
    return [expr]


def _denominators(expr: sympy.Expr) -> list[sympy.Expr]:
    dens: list[sympy.Expr] = []
    for sub in _walk(expr):
        if isinstance(sub, sympy.Pow) and sub.exp.is_Integer and int(sub.exp) < 0:
            dens.append(sub.base)
        elif isinstance(sub, sympy.Mul):
            for a in sub.args:
                if isinstance(a, sympy.Pow) and a.exp == -1:
                    dens.append(a.base)
    # unique by srepr, preserve order
    seen = set()
    out = []
    for d in dens:
        k = _srepr(d)
        if k not in seen:
            seen.add(k)
            out.append(d)
    return out


def _applied_with_sign(e: sympy.Expr):
    """Return (sign, AppliedUndef) for ±F(u), else None."""
    if isinstance(e, AppliedUndef):
        return 1, e
    coeff, rest = e.as_coeff_Mul()
    if isinstance(rest, AppliedUndef) and coeff in (1, -1):
        return int(coeff), rest
    return None


def _is_dd_term(term: sympy.Expr) -> dict | None:
    """Detect (f(x)-f(y))/(x-y) up to overall sign."""
    num, den = sympy.fraction(sympy.together(term))
    if not isinstance(num, sympy.Add) or len(num.args) != 2:
        return None
    if not isinstance(den, sympy.Add) or len(den.args) != 2:
        return None
    parsed = []
    for arg in num.args:
        got = _applied_with_sign(arg)
        if got is None:
            return None
        parsed.append(got)
    (s1, f1), (s2, f2) = parsed
    if type(f1).__name__ != type(f2).__name__:
        return None
    if len(f1.args) != 1 or len(f2.args) != 1:
        return None
    if s1 == s2:
        return None
    # num = s1 F(u) + s2 F(v) with s1 = -s2
    u, v = f1.args[0], f2.args[0]
    if s1 == 1:
        pos, neg = u, v
    else:
        pos, neg = v, u
    if sympy.expand(den - (pos - neg)) == 0 or sympy.expand(den - (neg - pos)) == 0:
        return {
            "function": type(f1).__name__,
            "u": _text(u),
            "v": _text(v),
            "term": _text(term),
        }
    return None


def observe_parsed(expr: sympy.Expr) -> dict[str, Any]:
    """Fact sheet from an already-parsed expression (Guo diagnostic path)."""
    return _observe_expr(expr)


def observe_expression(text: str, symbols: list, functions: list | None) -> dict[str, Any]:
    """Return a JSON-serializable fact sheet. Never includes gold fields."""
    expr = parse_expression(text, symbols, functions=functions or None)
    return _observe_expr(expr)


def _observe_expr(expr: sympy.Expr) -> dict[str, Any]:
    summary = structure_summary(expr)
    counts: Counter[str] = Counter()
    examples: dict[str, sympy.Expr] = {}
    for sub in _walk(expr):
        if not getattr(sub, "args", ()):
            continue
        if sub == expr:
            continue
        key = _srepr(sub)
        counts[key] += 1
        examples[key] = sub

    repeated = []
    for key, c in counts.most_common(_MAX_ITEMS):
        if c < 2:
            continue
        sub = examples[key]
        ops = _ops(sub)
        # keep function calls even if ops is 0; drop trivial symbols
        if ops < 1 and not isinstance(sub, AppliedUndef):
            continue
        repeated.append({
            "srepr": key,
            "text": _text(sub),
            "count": int(c),
            "ops": ops,
            "head": type(sub).__name__,
        })

    dens = _denominators(expr)
    denom_inv = []
    den_counts: Counter[str] = Counter(_srepr(d) for d in dens)
    # recount actual occurrences in walk
    den_occ: Counter[str] = Counter()
    den_ex = {}
    for sub in _walk(expr):
        if isinstance(sub, sympy.Pow) and sub.exp.is_Integer and int(sub.exp) < 0:
            den_occ[_srepr(sub.base)] += 1
            den_ex[_srepr(sub.base)] = sub.base
    for key, c in den_occ.most_common(_MAX_ITEMS):
        d = den_ex[key]
        denom_inv.append({
            "srepr": key,
            "text": _text(d),
            "count": int(c),
            "ops": _ops(d),
            "free_symbols": sorted(str(s) for s in d.free_symbols),
        })

    families: dict[str, list[str]] = defaultdict(list)
    calls = []
    for sub in _walk(expr):
        if isinstance(sub, AppliedUndef):
            name = type(sub).__name__
            args = [_text(a) for a in sub.args]
            families[name].append(_text(sub))
            calls.append({"name": name, "args": args, "text": _text(sub)})

    function_families = []
    for name, occs in sorted(families.items()):
        uniq = sorted(set(occs))
        function_families.append({
            "name": name,
            "n_occurrences": len(occs),
            "n_distinct": len(uniq),
            "examples": uniq[:8],
        })

    perm_pairs = []
    seen_pair = set()
    for i, a in enumerate(calls):
        for b in calls[i + 1:]:
            if a["name"] != b["name"]:
                continue
            if a["args"] == b["args"]:
                continue
            if sorted(a["args"]) == sorted(b["args"]) and len(a["args"]) >= 2:
                key = tuple(sorted((a["text"], b["text"])))
                if key in seen_pair:
                    continue
                seen_pair.add(key)
                perm_pairs.append({
                    "name": a["name"],
                    "left": a["text"],
                    "right": b["text"],
                    "left_args": a["args"],
                    "right_args": b["args"],
                })

    pw = []
    for p in ordered_atoms(expr, sympy.Piecewise):
        branches = []
        for val, cond in p.args:
            branches.append({"value": _text(val), "cond": _text(cond)})
        values = [b["value"] for b in branches]
        pw.append({
            "text": _text(p),
            "n_branches": len(branches),
            "branches": branches,
            "all_values_equal": len(set(values)) == 1,
        })

    terms = _terms(expr)
    term_recs = []
    coeff_clusters: dict[str, list[str]] = defaultdict(list)
    for t in terms:
        coeff, rest = t.as_coeff_Mul()
        skel = _srepr(rest)
        coeff_clusters[skel].append(_text(t))
        term_recs.append({
            "text": _text(t),
            "coeff": _text(coeff),
            "rest": _text(rest),
        })

    dd_hits = []
    for t in terms:
        hit = _is_dd_term(t)
        if hit:
            dd_hits.append(hit)
    if not dd_hits:
        hit = _is_dd_term(expr)
        if hit:
            dd_hits.append(hit)

    poly_calls = []
    for sub in _walk(expr):
        if getattr(sub, "func", None) is sympy.polygamma:
            poly_calls.append({"n": _text(sub.args[0]), "z": _text(sub.args[1]), "text": _text(sub)})

    poles = []
    for d in dens[:_MAX_ITEMS]:
        poles.append({
            "denominator": _text(d),
            "ops": _ops(d),
            "symbols": sorted(str(s) for s in d.free_symbols),
        })

    # Common multiplicative factors across all top-level terms (e.g. A*f + A*g).
    common_factors = []
    if len(terms) >= 2:
        factor_maps = []
        for t in terms:
            if isinstance(t, sympy.Mul):
                factor_maps.append({_srepr(a): a for a in t.args})
            else:
                factor_maps.append({})
        if all(factor_maps):
            common_keys = set.intersection(*(set(d) for d in factor_maps))
            for k in sorted(common_keys):
                fac = factor_maps[0][k]
                if not getattr(fac, "args", ()) and not fac.is_Symbol:
                    continue
                common_factors.append({
                    "text": _text(fac),
                    "srepr": k,
                    "ops": _ops(fac),
                    "n_terms": len(terms),
                })

    builtin_fams: dict[str, list[str]] = defaultdict(list)
    watched = {sympy.polygamma, sympy.exp, sympy.log, sympy.sin, sympy.cos}
    for sub in _walk(expr):
        if getattr(sub, "func", None) in watched:
            builtin_fams[sub.func.__name__].append(_text(sub))
    builtin_families = []
    for name, occs in sorted(builtin_fams.items()):
        uniq = sorted(set(occs))
        builtin_families.append({
            "name": name,
            "n_occurrences": len(occs),
            "n_distinct": len(uniq),
            "examples": uniq[:8],
        })

    subst = []
    for r in repeated[:8]:
        subst.append({
            "candidate": r["text"],
            "count": r["count"],
            "reason": "repeated_subtree",
        })
    for cf in common_factors[:4]:
        subst.append({
            "candidate": cf["text"],
            "count": cf["n_terms"],
            "reason": "common_factor",
        })

    indexed_names = sorted({c["name"] for c in calls})
    bipartite = {name: sorted({tuple(c["args"]) for c in calls if c["name"] == name})
                 for name in indexed_names}
    bipartite_json = {k: [list(t) for t in v] for k, v in bipartite.items()}

    return {
        "facts_only": True,
        "structure_summary": summary,
        "term_count": len(terms),
        "terms": term_recs[:_MAX_ITEMS],
        "repeated_subtrees": repeated,
        "denominators": denom_inv,
        "poles": poles,
        "function_families": function_families,
        "indexed_calls": calls[:_MAX_ITEMS],
        "permutation_pairs": perm_pairs,
        "piecewise": pw,
        "divided_difference_hits": dd_hits,
        "polygamma_calls": poly_calls,
        "coefficient_clusters": [
            {"skeleton": k, "terms": v, "n": len(v)}
            for k, v in list(coeff_clusters.items())[:_MAX_ITEMS]
            if len(v) >= 2
        ],
        "substitution_candidates": subst,
        "common_factors": common_factors,
        "builtin_families": builtin_families,
        "term_symbol_bipartite": bipartite_json,
        "free_symbols": sorted(str(s) for s in expr.free_symbols),
    }


def proposer_safe_observations(report: dict) -> dict:
    """Strip anything that could be confused with gold. Currently identity
    because the observer never sees gold; kept as an explicit boundary."""
    assert report.get("facts_only") is True
    forbidden = ("gold", "human_reference", "target_compact", "hidden_gold")
    blob = str(report).lower()
    for k in forbidden:
        if k in blob:
            raise RuntimeError(f"observation leakage key {k}")
    return report
