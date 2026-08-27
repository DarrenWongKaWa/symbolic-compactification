"""Abstraction inventor: related-but-not-identical families → H=(T,θ,O,F).

Does not add local CSE detectors. Exact identical sreprs are left to frozen B9.
"""
from __future__ import annotations

from collections import defaultdict

import sympy
from sympy.core.function import AppliedUndef

from research.abstraction_invention.prototype.antiunify import (
    hole_values_for,
    instantiate,
    lgg_pair,
)
from research.abstraction_invention.prototype.schema import (
    AbstractionHypothesis,
    InstanceMap,
)
from symbolic_compactification import parse_expression

_MAX_SUBS = 60
_MAX_PAIRS = 80


def _subs(expr: sympy.Expr) -> list[sympy.Expr]:
    seen = set()
    out = []
    n = 0
    for sub in sympy.preorder_traversal(expr):
        n += 1
        if n > 4000:
            break
        if sub == expr or not getattr(sub, "args", ()):
            continue
        ops = int(sympy.count_ops(sub))
        if ops < 1 and not isinstance(sub, AppliedUndef):
            continue
        k = sympy.srepr(sub)
        if k in seen:
            continue
        seen.add(k)
        out.append(sub)
        if len(out) >= _MAX_SUBS:
            break
    return out


def _too_shallow(gen) -> bool:
    t = gen.template
    if isinstance(t, AppliedUndef):
        if all(isinstance(a, sympy.Symbol) and str(a).startswith("theta")
               for a in t.args):
            return True
    holes = {s.name for s in t.free_symbols if s.name.startswith("theta")}
    kept_syms = {s.name for s in t.free_symbols} - holes
    has_named_call = any(
        isinstance(s, AppliedUndef) for s in sympy.preorder_traversal(t)
    )
    # Reject a pure hole-product with no remaining named structure
    # (V*G0*V vs W*H0*W → theta0*theta1*theta0).
    if not has_named_call and not kept_syms:
        return True
    return False


def invent_antiunifications(expr: sympy.Expr) -> list[AbstractionHypothesis]:
    subs = _subs(expr)
    # Index by coarse signature so we do not pair unrelated heads.
    buckets: dict[tuple, list] = defaultdict(list)
    for s in subs:
        if isinstance(s, AppliedUndef):
            buckets[("undef", type(s).__name__, len(s.args))].append(s)
        else:
            buckets[("head", str(s.func), min(len(s.args), 6))].append(s)
    out = []
    pairs = 0
    for group in buckets.values():
        if len(group) < 2:
            continue
        # Prefer composite (Mul/Add) groups — that is the Born miss.
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if a == b:
                    continue
                pairs += 1
                if pairs > _MAX_PAIRS:
                    return out
                gen = lgg_pair(a, b)
                if not gen.useful() or _too_shallow(gen):
                    continue
                left = hole_values_for(gen, 0)
                right = hole_values_for(gen, 1)
                inst_l = instantiate(gen.template, left)
                inst_r = instantiate(gen.template, right)
                if inst_l != a or inst_r != b:
                    # still accept if equal after expand
                    if sympy.expand(inst_l - a) != 0 or sympy.expand(inst_r - b) != 0:
                        continue
                hy = AbstractionHypothesis(
                    operator="antiunification",
                    family=[str(a), str(b)],
                    latent_variables=sorted(gen.substitutions),
                    template=str(gen.template),
                    instance_maps=[
                        InstanceMap(str(a), {k: str(v) for k, v in left.items()}),
                        InstanceMap(str(b), {k: str(v) for k, v in right.items()}),
                    ],
                    reason="least-general generalization of non-identical subterms",
                    proof_obligations=[
                        f"{a} - F({','.join(left)}) = 0",
                        f"{b} - F({','.join(right)}) = 0",
                    ],
                    confidence=min(0.9, 0.4 + 0.1 * gen.ops_kept),
                    source="lgg",
                )
                out.append(hy)
    # de-dup by template string + family set
    uniq, seen = [], set()
    for h in out:
        key = (h.template, frozenset(h.family))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    uniq.sort(key=lambda h: (-h.confidence, h.template))
    return uniq[:12]


def invent_derivative_masters(expr: sympy.Expr) -> list[AbstractionHypothesis]:
    """If T appears and sympy.diff(S, x) == T, propose S as master.

    Not a polygamma whitelist: any pair of subexpressions.
    """
    subs = [s for s in _subs(expr)
            if isinstance(s, sympy.Expr) and not isinstance(s, sympy.Rel)]
    out = []
    for i, s in enumerate(subs):
        if isinstance(s, sympy.Piecewise):
            continue
        for x in list(s.free_symbols)[:3]:
            try:
                ds = sympy.diff(s, x)
            except Exception:
                continue
            if not isinstance(ds, sympy.Expr) or isinstance(ds, sympy.Rel):
                continue
            for t in subs[i + 1:]:
                if isinstance(t, (sympy.Rel, sympy.Piecewise)):
                    continue
                try:
                    same = ds == t or sympy.expand(ds - t) == 0
                except TypeError:
                    continue
                if same:
                    out.append(AbstractionHypothesis(
                        operator="master_derivative",
                        family=[str(s), str(t)],
                        latent_variables=[str(x)],
                        template=str(s),
                        instance_maps=[
                            InstanceMap(str(s), {}, "identity"),
                            InstanceMap(str(t), {str(x): str(x)}, "d/dtheta"),
                        ],
                        reason=f"{t} is d/d{x} of {s}",
                        proof_obligations=[
                            f"{s} - F = 0",
                            f"{t} - dF/d{x} = 0",
                        ],
                        confidence=0.7,
                        source="derivative_relation",
                    ))
    uniq, seen = [], set()
    for h in out:
        key = frozenset(h.family)
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    return uniq[:8]


def invent_piecewise_confluence(expr: sympy.Expr) -> list[AbstractionHypothesis]:
    """Anti-unify unequal Piecewise branch *values* (not identical-fold)."""
    out = []
    for pw in expr.atoms(sympy.Piecewise):
        vals = [val for val, _cond in pw.args]
        if len(vals) < 2:
            continue
        if all(v == vals[0] for v in vals):
            continue  # exact identical values: B9's job
        gen = lgg_pair(vals[0], vals[1])
        if not gen.useful() or _too_shallow(gen):
            continue
        left = hole_values_for(gen, 0)
        right = hole_values_for(gen, 1)
        out.append(AbstractionHypothesis(
            operator="confluence",
            family=[str(vals[0]), str(vals[1])],
            latent_variables=sorted(gen.substitutions),
            template=str(gen.template),
            instance_maps=[
                InstanceMap(str(vals[0]), {k: str(v) for k, v in left.items()}),
                InstanceMap(str(vals[1]), {k: str(v) for k, v in right.items()}),
            ],
            reason="unequal Piecewise branches specialize one template",
            proof_obligations=[
                f"branch0 - F(theta) = 0",
                f"branch1 - F(theta') = 0",
            ],
            confidence=0.65,
            source="piecewise_lgg",
        ))
    return out


def invent_from_parsed(expr: sympy.Expr) -> list[AbstractionHypothesis]:
    hyps: list[AbstractionHypothesis] = []
    hyps.extend(invent_antiunifications(expr))
    hyps.extend(invent_derivative_masters(expr))
    hyps.extend(invent_piecewise_confluence(expr))
    return hyps[:16]


def invent_from_expression(text: str, symbols: list, functions: list | None
                           ) -> list[AbstractionHypothesis]:
    expr = parse_expression(text, symbols, functions=functions or None)
    return invent_from_parsed(expr)
