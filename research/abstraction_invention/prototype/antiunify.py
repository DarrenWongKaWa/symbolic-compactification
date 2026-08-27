"""First-order anti-unification (least general generalization) of SymPy terms.

This is NOT repeated-subtree CSE. Identical sreprs are exact matches; invention
requires a template with holes that instantiates to *distinct* members.

Holes are reused when the same pair of disagreeing subterms recurs
(so V(p)*G0(p)*V(p) vs V(q)*G0(q)*V(q) shares one parameter).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from itertools import permutations
from typing import Optional

import sympy
from sympy.core.function import AppliedUndef

_MAX_COMM = 5  # permute at most this many commutative args


def _s(e: sympy.Expr) -> str:
    return sympy.srepr(e)


def _sig(e: sympy.Expr) -> tuple:
    if isinstance(e, AppliedUndef):
        return ("undef", type(e).__name__, len(e.args))
    if not e.args:
        return ("leaf", type(e).__name__)
    return ("head", str(e.func), len(e.args))


def _mk_theta(i: int) -> sympy.Symbol:
    return sympy.Symbol(f"theta{i}", real=True, commutative=True)


@dataclass
class PairGeneralization:
    template: sympy.Expr
    # theta_name -> (left_subexpr, right_subexpr)
    substitutions: dict[str, tuple[sympy.Expr, sympy.Expr]] = field(default_factory=dict)

    @property
    def n_holes(self) -> int:
        return len(self.substitutions)

    @property
    def ops_kept(self) -> int:
        t = self.template
        # holes count as 0 ops
        n = int(sympy.count_ops(t))
        return n

    def trivial(self) -> bool:
        """Whole-term hole, or no hole (exact match)."""
        if self.n_holes == 0:
            return True
        if not self.template.args and self.n_holes == 1:
            return True
        return False

    def useful(self) -> bool:
        return (not self.trivial()) and self.ops_kept >= 1 and 1 <= self.n_holes <= 4


def _same_head(a: sympy.Expr, b: sympy.Expr) -> bool:
    if isinstance(a, AppliedUndef) or isinstance(b, AppliedUndef):
        return (
            isinstance(a, AppliedUndef)
            and isinstance(b, AppliedUndef)
            and type(a).__name__ == type(b).__name__
            and len(a.args) == len(b.args)
        )
    return a.func is b.func and len(a.args) == len(b.args) and bool(a.args)


def lgg_pair(e1: sympy.Expr, e2: sympy.Expr) -> PairGeneralization:
    """Least general generalization of two terms with consistent holes."""
    store: dict[tuple[str, str], sympy.Symbol] = {}
    pieces: dict[str, tuple[sympy.Expr, sympy.Expr]] = {}
    counter = {"i": 0}

    def hole(a: sympy.Expr, b: sympy.Expr) -> sympy.Symbol:
        k1, k2 = _s(a), _s(b)
        key = (k1, k2) if k1 <= k2 else (k2, k1)
        if key in store:
            th = store[key]
            # keep the left/right orientation of the original pair
            return th
        # reuse if this exact oriented pair already stored
        oriented = (k1, k2)
        if oriented in store:
            return store[oriented]
        th = _mk_theta(counter["i"])
        counter["i"] += 1
        store[key] = th
        store[oriented] = th
        store[(k2, k1)] = th
        pieces[th.name] = (a, b)
        return th

    def rec(a: sympy.Expr, b: sympy.Expr) -> sympy.Expr:
        if a == b:
            return a
        if _same_head(a, b):
            commutative = a.func in (sympy.Add, sympy.Mul) and a.is_commutative
            if commutative:
                paired = _pair_commutative(a.args, b.args)
                if paired is None:
                    return hole(a, b)
                gens = [rec(x, y) for x, y in paired]
                return a.func(*gens)
            gens = [rec(x, y) for x, y in zip(a.args, b.args)]
            return a.func(*gens)
        return hole(a, b)

    templ = rec(e1, e2)
    return PairGeneralization(template=templ, substitutions=pieces)


def _pair_commutative(args1, args2) -> Optional[list[tuple]]:
    a1, a2 = list(args1), list(args2)
    if len(a1) != len(a2):
        return None
    n = len(a1)
    # Group by signature
    from collections import defaultdict
    buckets2: dict[tuple, list] = defaultdict(list)
    for x in a2:
        buckets2[_sig(x)].append(x)
    # If signature bags differ, try full permute for tiny n else fail
    sigs1 = sorted(_sig(x) for x in a1)
    sigs2 = sorted(_sig(x) for x in a2)
    if sigs1 != sigs2:
        if n <= _MAX_COMM:
            best = None
            best_score = -1
            for perm in permutations(a2):
                score = sum(1 for x, y in zip(a1, perm) if _sig(x) == _sig(y) or x.func is y.func)
                if score > best_score:
                    best_score = score
                    best = list(zip(a1, perm))
            return best
        return None
    used = {s: 0 for s in buckets2}
    out = []
    for x in a1:
        s = _sig(x)
        bucket = buckets2[s]
        j = used[s]
        if j >= len(bucket):
            return None
        out.append((x, bucket[j]))
        used[s] = j + 1
    return out


def lgg_family(exprs: list[sympy.Expr]) -> Optional[PairGeneralization]:
    """Fold LGG over ≥2 expressions (pairwise with the running template via
    instantiating holes is hard; we LGG the first two then require others
    to match the same template shape by a second pass).

    For v1 we LGG e0 with every ei and require identical templates modulo
    hole names, then merge substitution columns.
    """
    if len(exprs) < 2:
        return None
    base = lgg_pair(exprs[0], exprs[1])
    if not base.useful():
        return None
    # For extra members, LGG with first; template must match structure
    for e in exprs[2:]:
        g = lgg_pair(exprs[0], e)
        if not _template_shape_eq(base.template, g.template):
            return None
    return base


def _template_shape_eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    """Equal up to renaming theta* symbols."""
    def norm(e: sympy.Expr) -> str:
        mapping = {}
        i = 0
        e2 = e
        for s in sorted(e.free_symbols, key=lambda x: x.name):
            if s.name.startswith("theta"):
                mapping[s] = sympy.Symbol(f"TH{i}")
                i += 1
        if mapping:
            e2 = e.xreplace(mapping)
        return sympy.srepr(e2)
    return norm(a) == norm(b)


def instantiate(template: sympy.Expr, theta_values: dict[str, sympy.Expr]) -> sympy.Expr:
    mapping = {}
    for s in template.free_symbols:
        if s.name in theta_values:
            mapping[s] = theta_values[s.name]
    return template.xreplace(mapping) if mapping else template


def hole_values_for(gen: PairGeneralization, which: int) -> dict[str, sympy.Expr]:
    """which=0 left member, which=1 right member of the defining pair."""
    return {name: pair[which] for name, pair in gen.substitutions.items()}
