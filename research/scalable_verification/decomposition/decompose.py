"""Compositional proof-decomposition planner (Track V / V1).

Given A, B and a claimed relation, emit smaller typed steps plus exact
composition. Does not decide ZERO. Does not call sympy.limit on a claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence, Union

import sympy

from research.llm_abstraction.constructor import _equal, parse_flex
from research.scalable_verification.api import STRATEGIES, route_name

EQUALITY = "EQUALITY"
LIMIT = "LIMIT"
NEWTON_DD = "NEWTON_DD"
HERMITE_DD = "HERMITE_DD"
RELATIONS = (EQUALITY, LIMIT, NEWTON_DD, HERMITE_DD)

DIRECT = "DIRECT"
FACTOR_LOCAL = "FACTOR_LOCAL"
SERIES_LOCAL = "SERIES_LOCAL"
DD_CERTIFICATE = "DD_CERTIFICATE"
SPECIAL_FUNCTION_LOCAL = "SPECIAL_FUNCTION_LOCAL"

STATUS_CONSTANT_NONZERO = "constant_nonzero"
STATUS_NONZERO_ASSUMPTION = "nonzero_assumption"
STATUS_IDENTICALLY_CANCELLED = "identically_cancelled"
STATUS_UNCERTIFIED = "uncertified"

ROLE_SPECTATOR = "spectator"
ROLE_IDENTICAL_CANCEL = "identical_cancel"

_SPECIAL_HEADS = (
    sympy.gamma,
    sympy.polygamma,
    sympy.loggamma,
    sympy.digamma,
    sympy.zeta,
)

ExprLike = Union[sympy.Expr, str, int]


def _strategy(name: str) -> str:
    return route_name(name)


def _gens(*exprs: Optional[sympy.Expr]) -> tuple[sympy.Symbol, ...]:
    syms: set[sympy.Symbol] = set()
    for e in exprs:
        if isinstance(e, sympy.Expr):
            syms |= {s for s in e.free_symbols if isinstance(s, sympy.Symbol)}
    return tuple(sorted(syms, key=lambda s: s.name))


def _identically_zero(expr: sympy.Expr) -> bool:
    try:
        return sympy.expand(expr) == 0
    except Exception:
        return False


def _is_unit(expr: sympy.Expr) -> bool:
    try:
        e = sympy.expand(expr)
    except Exception:
        e = expr
    return e == 1 or e == -1


def _is_nonzero_number(expr: sympy.Expr) -> bool:
    try:
        if not expr.is_number:
            return False
        if expr == 0 or expr.has(sympy.nan, sympy.zoo, sympy.oo, -sympy.oo):
            return False
        return expr != 0
    except Exception:
        return False


def _fraction(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    n, d = sympy.fraction(sympy.together(expr))
    return sympy.expand(n), sympy.expand(d)


def _together(expr: sympy.Expr) -> sympy.Expr:
    try:
        return sympy.together(expr)
    except Exception:
        return expr


def _remap_by_name(expr: sympy.Expr, names: dict[str, sympy.Symbol]) -> sympy.Expr:
    if not isinstance(expr, sympy.Expr):
        return expr
    mapping = {s: names[s.name] for s in expr.free_symbols if s.name in names}
    return expr.xreplace(mapping) if mapping else expr


def _composition_identity(left: sympy.Expr, right: sympy.Expr) -> bool:
    """Exact split identity. Certifies A vs S*A_loc, never the original claim."""
    names = {s.name: s for s in left.free_symbols if isinstance(s, sympy.Symbol)}
    right = _remap_by_name(right, names)
    if left == right:
        return True
    try:
        if sympy.expand(left - right) == 0:
            return True
    except Exception:
        pass
    try:
        n, _d = sympy.fraction(sympy.together(left - right))
        if sympy.expand(n) == 0:
            return True
    except Exception:
        pass
    try:
        return bool(_equal(left, right))
    except Exception:
        return False


def _as_polys(
    a: sympy.Expr, b: sympy.Expr, gens: tuple[sympy.Symbol, ...]
) -> Optional[tuple[sympy.Poly, sympy.Poly]]:
    try:
        if gens:
            return (
                sympy.Poly(a, *gens, domain=sympy.ZZ),
                sympy.Poly(b, *gens, domain=sympy.ZZ),
            )
        return (
            sympy.Poly(a, domain=sympy.ZZ),
            sympy.Poly(b, domain=sympy.ZZ),
        )
    except (sympy.PolynomialError, sympy.CoercionFailed, ValueError, TypeError):
        try:
            if gens:
                return (
                    sympy.Poly(a, *gens, domain=sympy.QQ),
                    sympy.Poly(b, *gens, domain=sympy.QQ),
                )
            return (
                sympy.Poly(a, domain=sympy.QQ),
                sympy.Poly(b, domain=sympy.QQ),
            )
        except Exception:
            return None
    except Exception:
        return None


def _poly_gcd(a: sympy.Expr, b: sympy.Expr, gens: tuple[sympy.Symbol, ...]) -> sympy.Expr:
    a, b = sympy.expand(a), sympy.expand(b)
    if _identically_zero(a) or _identically_zero(b):
        return sympy.Integer(0)
    pair = _as_polys(a, b, gens)
    if pair is None:
        try:
            return sympy.expand(sympy.gcd(a, b))
        except Exception:
            return sympy.Integer(1)
    g = pair[0].gcd(pair[1]).as_expr()
    return sympy.expand(g)


def _exact_quo(
    num: sympy.Expr, den: sympy.Expr, gens: tuple[sympy.Symbol, ...]
) -> Optional[sympy.Expr]:
    """Polynomial quotient with remainder 0. Never the tautology num/den."""
    num, den = sympy.expand(num), sympy.expand(den)
    if _identically_zero(den):
        return None
    if den == 1:
        return num
    if den == -1:
        return sympy.expand(-num)
    pair = _as_polys(num, den, gens)
    if pair is None:
        return None
    try:
        q, r = pair[0].div(pair[1])
    except Exception:
        return None
    if not _identically_zero(r.as_expr()):
        return None
    return q.as_expr()


def _coerce(
    obj: Any,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, sympy.Expr):
        return obj
    if isinstance(obj, bool):
        return None
    if isinstance(obj, int):
        return sympy.Integer(obj)
    if isinstance(obj, str):
        got = parse_flex(obj, list(symbols or []), functions)
        return got
    try:
        return sympy.sympify(obj)
    except Exception:
        return None


def _nonzero_assumed(
    assumptions: Sequence[Any],
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> list[sympy.Expr]:
    out: list[sympy.Expr] = []
    for item in assumptions or ():
        if item is None:
            continue
        if isinstance(item, dict) and item.get("nonzero"):
            name = item.get("name")
            if name:
                out.append(sympy.Symbol(str(name)))
            continue
        if isinstance(item, sympy.Ne):
            if item.rhs == 0:
                out.append(item.lhs)
            elif item.lhs == 0:
                out.append(item.rhs)
            continue
        if isinstance(item, sympy.Rel) and getattr(item, "rel_op", None) == "!=":
            if item.rhs == 0:
                out.append(item.lhs)
            elif item.lhs == 0:
                out.append(item.rhs)
            continue
        if isinstance(item, str):
            raw = item.strip()
            low = raw.lower()
            if low.startswith("nonzero:"):
                e = _coerce(raw.split(":", 1)[1], symbols, functions)
                if e is not None:
                    out.append(e)
                continue
            if low.startswith("ne(") and raw.endswith(")"):
                inner = raw[3:-1]
                parts = [p.strip() for p in inner.split(",")]
                if len(parts) == 2 and parts[1] in {"0", "0.0"}:
                    e = _coerce(parts[0], symbols, functions)
                    if e is not None:
                        out.append(e)
                continue
            if "!=" in raw:
                left, right = raw.split("!=", 1)
                if right.strip() in {"0", "0.0"}:
                    e = _coerce(left, symbols, functions)
                    if e is not None:
                        out.append(e)
                continue
            e = _coerce(raw, symbols, functions)
            if e is not None:
                out.append(e)
            continue
        if isinstance(item, sympy.Expr):
            out.append(item)
    return out


def _spectator_status(
    s: sympy.Expr,
    assumptions: Sequence[Any],
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> str:
    if _is_nonzero_number(s):
        return STATUS_CONSTANT_NONZERO
    inferred = list(symbols or [])
    for sy in s.free_symbols:
        inferred.append({"name": sy.name, "real": True})
    assumed = _nonzero_assumed(assumptions, inferred, functions)
    for e in assumed:
        if _composition_identity(s, e):
            return STATUS_NONZERO_ASSUMPTION
    return STATUS_UNCERTIFIED


def _claim_equivalent(status: str) -> bool:
    return status in {
        STATUS_CONSTANT_NONZERO,
        STATUS_NONZERO_ASSUMPTION,
        STATUS_IDENTICALLY_CANCELLED,
    }


def _has_special(expr: sympy.Expr) -> bool:
    try:
        return any(expr.has(h) for h in _SPECIAL_HEADS)
    except Exception:
        return False


@dataclass
class Composition:
    """Exact multiplicative split. exact=True only after remainder-0 division."""

    spectator: sympy.Expr
    a_loc: sympy.Expr
    b_loc: sympy.Expr
    residual: sympy.Expr
    status: str
    role: str = ROLE_SPECTATOR
    exact: bool = True
    equivalent: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "spectator": str(self.spectator),
            "a_loc": str(self.a_loc),
            "b_loc": str(self.b_loc),
            "residual": str(self.residual),
            "status": self.status,
            "role": self.role,
            "exact": self.exact,
            "equivalent": self.equivalent,
        }


def _make_composition(
    spectator: sympy.Expr,
    a_loc: sympy.Expr,
    b_loc: sympy.Expr,
    *,
    status: str,
    role: str,
) -> Composition:
    return Composition(
        spectator=spectator,
        a_loc=a_loc,
        b_loc=b_loc,
        residual=sympy.expand(a_loc - b_loc),
        status=status,
        role=role,
        exact=True,
        equivalent=_claim_equivalent(status),
    )


def certify_composition(
    a: ExprLike,
    b: ExprLike,
    spectator: ExprLike,
    *,
    assumptions: Sequence[Any] = (),
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> Optional[Composition]:
    """Return a split iff A = S*A_loc and B = S*B_loc identically.

    False spectators (nonzero remainder, tautological A/S) return None.
    Does not decide A == B.
    """
    ae = _coerce(a, symbols, functions)
    be = _coerce(b, symbols, functions)
    se = _coerce(spectator, symbols, functions)
    if ae is None or be is None or se is None:
        return None
    if _identically_zero(se) or _is_unit(se):
        return None
    nA, dA = _fraction(ae)
    nB, dB = _fraction(be)
    nS, dS = _fraction(se)
    gens = _gens(nA, dA, nB, dB, nS, dS)
    nAl = _exact_quo(nA, nS, gens)
    nBl = _exact_quo(nB, nS, gens)
    dAl = _exact_quo(dA, dS, gens)
    dBl = _exact_quo(dB, dS, gens)
    if None in (nAl, nBl, dAl, dBl):
        return None
    a_loc = _together(nAl / dAl)
    b_loc = _together(nBl / dBl)
    if not _composition_identity(ae, se * a_loc):
        return None
    if not _composition_identity(be, se * b_loc):
        return None
    status = _spectator_status(se, assumptions, symbols, functions)
    return _make_composition(se, a_loc, b_loc, status=status, role=ROLE_SPECTATOR)


def certify_identical_cancel(
    expr: ExprLike,
    spectator: ExprLike,
    *,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    """Cancel S from num and den of expr. Both divisions must be exact."""
    ae = _coerce(expr, symbols, functions)
    se = _coerce(spectator, symbols, functions)
    if ae is None or se is None:
        return None
    if _identically_zero(se) or _is_unit(se):
        return None
    n, d = _fraction(ae)
    nS, dS = _fraction(se)
    if not _is_unit(dS):
        return None
    gens = _gens(n, d, nS)
    n_loc = _exact_quo(n, nS, gens)
    d_loc = _exact_quo(d, nS, gens)
    if n_loc is None or d_loc is None:
        return None
    if not _composition_identity(n, nS * n_loc):
        return None
    if not _composition_identity(d, nS * d_loc):
        return None
    return _together(n_loc / d_loc), nS


def _discover_spectator(
    a: sympy.Expr,
    b: sympy.Expr,
    *,
    assumptions: Sequence[Any],
    symbols: Optional[list],
    functions: Optional[list],
) -> Optional[Composition]:
    nA, dA = _fraction(a)
    nB, dB = _fraction(b)
    gens = _gens(nA, dA, nB, dB)
    g_n = _poly_gcd(nA, nB, gens)
    g_d = _poly_gcd(dA, dB, gens)
    if _identically_zero(g_n):
        g_n = sympy.Integer(1)
    if _identically_zero(g_d):
        g_d = sympy.Integer(1)
    if _is_unit(g_n) and _is_unit(g_d):
        return None
    if _is_unit(g_n):
        g_n = sympy.Integer(1)
    if _is_unit(g_d):
        g_d = sympy.Integer(1)
    s = g_n if _is_unit(g_d) else _together(g_n / g_d)
    if _is_unit(s) or _identically_zero(s):
        return None
    return certify_composition(
        a, b, s, assumptions=assumptions, symbols=symbols, functions=functions
    )


def _discover_identical_cancel(expr: sympy.Expr) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    n, d = _fraction(expr)
    gens = _gens(n, d)
    g = _poly_gcd(n, d, gens)
    if _is_unit(g) or _identically_zero(g):
        return None
    return certify_identical_cancel(expr, g)


def _cancel_factor_power(
    num: sympy.Expr,
    den: sympy.Expr,
    factor: sympy.Expr,
    gens: tuple[sympy.Symbol, ...],
    *,
    max_power: int = 16,
) -> tuple[sympy.Expr, sympy.Expr, int]:
    k = 0
    n, d = num, den
    while k < max_power:
        qn = _exact_quo(n, factor, gens)
        qd = _exact_quo(d, factor, gens)
        if qn is None or qd is None:
            break
        n, d = qn, qd
        k += 1
    return n, d, k


def _limit_cancel(
    a: sympy.Expr, var: sympy.Expr, to: sympy.Expr
) -> tuple[sympy.Expr, Optional[sympy.Expr], int, bool]:
    """Cancel (var-to)^k from num and den. Returns (a_loc, S, k, den_vanishes)."""
    n, d = _fraction(a)
    gens = _gens(n, d, var, to)
    factor = sympy.expand(var - to)
    if _is_unit(factor) or _identically_zero(factor):
        cancelled = _discover_identical_cancel(a)
        if cancelled is None:
            den_at = sympy.expand(d.xreplace({var: to}))
            return a, None, 0, _identically_zero(den_at)
        a_loc, s = cancelled
        _n2, d2 = _fraction(a_loc)
        den_at = sympy.expand(d2.xreplace({var: to}))
        return a_loc, s, 1, _identically_zero(den_at)
    n2, d2, k = _cancel_factor_power(n, d, factor, gens)
    if k == 0:
        cancelled = _discover_identical_cancel(a)
        if cancelled is None:
            den_at = sympy.expand(d.xreplace({var: to}))
            return a, None, 0, _identically_zero(den_at)
        a_loc, s = cancelled
        _n2, d2 = _fraction(a_loc)
        den_at = sympy.expand(d2.xreplace({var: to}))
        return a_loc, s, 1, _identically_zero(den_at)
    a_loc = _together(n2 / d2)
    den_at = sympy.expand(d2.xreplace({var: to}))
    s = sympy.expand(factor**k)
    return a_loc, s, k, _identically_zero(den_at)


@dataclass
class ObligationStep:
    step_id: str
    kind: str
    left: sympy.Expr
    right: sympy.Expr
    suggested_strategy: str
    provenance: str
    parent_id: Optional[str] = None
    assumptions: tuple[str, ...] = ()
    var: Optional[sympy.Expr] = None
    to: Optional[sympy.Expr] = None
    residual: Optional[sympy.Expr] = None
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.suggested_strategy = _strategy(self.suggested_strategy)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "step_id": self.step_id,
            "kind": self.kind,
            "left": str(self.left),
            "right": str(self.right),
            "suggested_strategy": self.suggested_strategy,
            "provenance": self.provenance,
            "parent_id": self.parent_id,
            "assumptions": list(self.assumptions),
            "notes": list(self.notes),
        }
        if self.var is not None:
            d["var"] = str(self.var)
        if self.to is not None:
            d["to"] = str(self.to)
        if self.residual is not None:
            d["residual"] = str(self.residual)
        return d


@dataclass
class DecompositionPlan:
    relation: str
    a: sympy.Expr
    b: sympy.Expr
    steps: list[ObligationStep] = field(default_factory=list)
    suggested_strategies: tuple[str, ...] = ()
    composition: Optional[Composition] = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = {
            "relation": self.relation,
            "a": str(self.a),
            "b": str(self.b),
            "steps": [s.to_dict() for s in self.steps],
            "suggested_strategies": list(self.suggested_strategies),
            "composition": None if self.composition is None else self.composition.to_dict(),
            "notes": list(self.notes),
        }
        return d


def _sid(i: int) -> str:
    return f"s{i}"


def _assumption_strs(assumptions: Sequence[Any]) -> tuple[str, ...]:
    out = []
    for a in assumptions or ():
        out.append(str(a))
    return tuple(out)


def _newton_definition(
    latent: sympy.Expr, z: sympy.Expr, nodes: Sequence[sympy.Expr]
) -> Optional[sympy.Expr]:
    if len(nodes) < 2:
        return None
    x, y = nodes[0], nodes[1]
    return (latent.xreplace({z: x}) - latent.xreplace({z: y})) / (x - y)


def _hermite_definition(
    latent: sympy.Expr,
    z: sympy.Expr,
    nodes: Sequence[sympy.Expr],
    multiplicities: Optional[Sequence[int]],
) -> Optional[sympy.Expr]:
    if multiplicities is None and len(nodes) == 1:
        multiplicities = (2,)
    if not nodes:
        return None
    if multiplicities is None:
        if len(nodes) >= 2:
            return _newton_definition(latent, z, nodes)
        return None
    seq: list[sympy.Expr] = []
    for n, m in zip(nodes, multiplicities):
        mm = int(m)
        if mm < 1:
            return None
        seq.extend([n] * mm)
    if len(seq) < 2:
        return None
    if all(seq[i] == seq[0] for i in range(len(seq))):
        k = len(seq) - 1
        return latent.diff(z, k).xreplace({z: seq[0]}) / sympy.factorial(k)
    if len(seq) == 2:
        return _newton_definition(latent, z, seq)
    return None


def _empty_plan(
    relation: str,
    a: sympy.Expr,
    b: sympy.Expr,
    *,
    notes: tuple[str, ...],
    strategy: str,
    var: Optional[sympy.Expr] = None,
    to: Optional[sympy.Expr] = None,
    assumptions: Sequence[Any] = (),
) -> DecompositionPlan:
    step = ObligationStep(
        step_id="s0",
        kind=relation if relation in RELATIONS else EQUALITY,
        left=a,
        right=b,
        suggested_strategy=strategy,
        provenance="input_claim",
        assumptions=_assumption_strs(assumptions),
        var=var,
        to=to,
        residual=sympy.expand(a - b),
        notes=notes,
    )
    return DecompositionPlan(
        relation=relation,
        a=a,
        b=b,
        steps=[step],
        suggested_strategies=(_strategy(strategy),),
        notes=notes,
    )


def decompose(
    a: ExprLike,
    b: ExprLike,
    relation: str,
    *,
    assumptions: Sequence[Any] = (),
    var: Optional[ExprLike] = None,
    to: Optional[ExprLike] = None,
    latent: Optional[ExprLike] = None,
    latent_var: Optional[ExprLike] = None,
    nodes: Optional[Sequence[ExprLike]] = None,
    multiplicities: Optional[Sequence[int]] = None,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> DecompositionPlan:
    """Plan smaller obligations for the claimed relation between A and B.

    Never assigns ZERO / NONZERO. Never calls sympy.limit.
    """
    rel = (relation or "").upper()
    ae = _coerce(a, symbols, functions)
    be = _coerce(b, symbols, functions)
    if ae is None or be is None:
        dummy = ae if ae is not None else sympy.Integer(0)
        dummy_b = be if be is not None else sympy.Integer(0)
        return _empty_plan(
            rel or "UNKNOWN",
            dummy,
            dummy_b,
            notes=("unparseable_input",),
            strategy="UNKNOWN",
            assumptions=assumptions,
        )
    ve = _coerce(var, symbols, functions) if var is not None else None
    te = _coerce(to, symbols, functions) if to is not None else None
    Fe = _coerce(latent, symbols, functions) if latent is not None else None
    ze = _coerce(latent_var, symbols, functions) if latent_var is not None else None
    node_exprs: list[sympy.Expr] = []
    if nodes:
        for n in nodes:
            ne = _coerce(n, symbols, functions)
            if ne is None:
                node_exprs = []
                break
            node_exprs.append(ne)

    if rel not in RELATIONS:
        return _empty_plan(
            rel or "UNKNOWN",
            ae,
            be,
            notes=("unknown_relation",),
            strategy="UNKNOWN",
            var=ve,
            to=te,
            assumptions=assumptions,
        )

    steps: list[ObligationStep] = []
    notes: list[str] = []
    composition: Optional[Composition] = None
    parent = "s0"
    i = 0

    def add(**kwargs: Any) -> ObligationStep:
        nonlocal i
        st = ObligationStep(step_id=_sid(i), **kwargs)
        steps.append(st)
        i += 1
        return st

    root_strategy = DIRECT
    if rel in {NEWTON_DD, HERMITE_DD}:
        root_strategy = DD_CERTIFICATE
    elif rel == LIMIT:
        root_strategy = SERIES_LOCAL
    if _has_special(ae) or _has_special(be):
        root_strategy = SPECIAL_FUNCTION_LOCAL

    add(
        kind=rel,
        left=ae,
        right=be,
        suggested_strategy=root_strategy,
        provenance="input_claim",
        assumptions=_assumption_strs(assumptions),
        var=ve,
        to=te,
        residual=sympy.expand(ae - be) if rel == EQUALITY else None,
        notes=("planner_emits_no_claim_decision",),
    )

    work_a, work_b = ae, be

    if rel == LIMIT:
        if ve is None or te is None:
            notes.append("limit_missing_var_or_point")
            strategies = tuple(dict.fromkeys(_strategy(s.suggested_strategy) for s in steps))
            return DecompositionPlan(
                relation=rel, a=ae, b=be, steps=steps,
                suggested_strategies=strategies, notes=tuple(notes),
            )
        a_loc, s_cancel, k, den_vanishes = _limit_cancel(work_a, ve, te)
        if s_cancel is not None and k > 0:
            composition = _make_composition(
                s_cancel,
                a_loc,
                work_b,
                status=STATUS_IDENTICALLY_CANCELLED,
                role=ROLE_IDENTICAL_CANCEL,
            )
            add(
                kind=EQUALITY,
                left=work_a,
                right=_together(s_cancel * a_loc) if k else work_a,
                suggested_strategy=FACTOR_LOCAL,
                provenance="identical_cancel",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                residual=composition.residual,
                notes=("num_den_exact_quo", f"power:{k}"),
            )
            work_a = a_loc
        n_loc, d_loc = _fraction(work_a)
        den_at = sympy.expand(d_loc.xreplace({ve: te}))
        still_vanishes = _identically_zero(den_at)
        if still_vanishes or den_vanishes:
            add(
                kind=LIMIT,
                left=work_a,
                right=work_b,
                suggested_strategy=SERIES_LOCAL,
                provenance="limit_after_cancel",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                var=ve,
                to=te,
                notes=("denominator_still_vanishes",),
            )
        else:
            left_eval = _together(n_loc.xreplace({ve: te}) / d_loc.xreplace({ve: te}))
            add(
                kind=EQUALITY,
                left=left_eval,
                right=work_b,
                suggested_strategy=FACTOR_LOCAL if k > 0 else DIRECT,
                provenance="limit_after_cancel",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                residual=sympy.expand(left_eval - work_b),
                notes=("local_evaluation_not_sympy_limit",),
            )

    if rel in {EQUALITY, NEWTON_DD, HERMITE_DD}:
        cancelled = _discover_identical_cancel(work_a)
        if cancelled is not None:
            a_loc, s_cancel = cancelled
            composition = _make_composition(
                s_cancel,
                a_loc,
                work_b,
                status=STATUS_IDENTICALLY_CANCELLED,
                role=ROLE_IDENTICAL_CANCEL,
            )
            add(
                kind=EQUALITY,
                left=work_a,
                right=s_cancel * a_loc,
                suggested_strategy=FACTOR_LOCAL,
                provenance="identical_cancel",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                residual=composition.residual,
                notes=("num_den_exact_quo",),
            )
            add(
                kind=EQUALITY,
                left=a_loc,
                right=work_b,
                suggested_strategy=FACTOR_LOCAL if rel == EQUALITY else DD_CERTIFICATE,
                provenance="residual_equality",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                residual=composition.residual,
            )
            work_a = a_loc
        split = _discover_spectator(
            work_a, work_b, assumptions=assumptions, symbols=symbols, functions=functions
        )
        if split is not None:
            composition = split
            add(
                kind=EQUALITY,
                left=work_a,
                right=split.spectator * split.a_loc,
                suggested_strategy=FACTOR_LOCAL,
                provenance="spectator_factor",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                notes=(f"status:{split.status}",),
            )
            add(
                kind=EQUALITY,
                left=work_b,
                right=split.spectator * split.b_loc,
                suggested_strategy=FACTOR_LOCAL,
                provenance="spectator_factor",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                notes=(f"status:{split.status}",),
            )
            if split.equivalent:
                add(
                    kind=EQUALITY,
                    left=split.a_loc,
                    right=split.b_loc,
                    suggested_strategy=FACTOR_LOCAL,
                    provenance="residual_equality",
                    parent_id=parent,
                    assumptions=_assumption_strs(assumptions)
                    + ((f"Ne({split.spectator}, 0)",) if split.status == STATUS_NONZERO_ASSUMPTION else ()),
                    residual=split.residual,
                    notes=("composition_equivalent",),
                )
            else:
                notes.append("spectator_uncertified_no_residual_swap")
                add(
                    kind=EQUALITY,
                    left=split.a_loc,
                    right=split.b_loc,
                    suggested_strategy=FACTOR_LOCAL,
                    provenance="spectator_factor",
                    parent_id=parent,
                    assumptions=_assumption_strs(assumptions),
                    residual=split.residual,
                    notes=("uncertified_spectator_not_equivalent",),
                )

    if rel in {NEWTON_DD, HERMITE_DD} and Fe is not None and ze is not None and node_exprs:
        if rel == NEWTON_DD:
            defn = _newton_definition(Fe, ze, node_exprs)
            prov = "newton_definition"
        else:
            defn = _hermite_definition(Fe, ze, node_exprs, multiplicities)
            prov = "hermite_definition"
        if defn is not None:
            add(
                kind=EQUALITY,
                left=defn,
                right=ae,
                suggested_strategy=DD_CERTIFICATE,
                provenance=prov,
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                notes=("unfold_definition_vs_left",),
            )
            add(
                kind=EQUALITY,
                left=defn,
                right=be,
                suggested_strategy=DD_CERTIFICATE,
                provenance=prov,
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                notes=("unfold_definition_vs_right",),
            )

    if rel in {NEWTON_DD, HERMITE_DD}:
        add(
            kind=rel,
            left=work_a,
            right=work_b,
            suggested_strategy=DD_CERTIFICATE,
            provenance="residual_dd",
            parent_id=parent,
            assumptions=_assumption_strs(assumptions),
            residual=sympy.expand(work_a - work_b),
        )

    if not any(s.provenance == "residual_equality" for s in steps) and rel == EQUALITY:
        if len(steps) == 1:
            add(
                kind=EQUALITY,
                left=work_a,
                right=work_b,
                suggested_strategy=DIRECT,
                provenance="residual_equality",
                parent_id=parent,
                assumptions=_assumption_strs(assumptions),
                residual=sympy.expand(work_a - work_b),
                notes=("no_split",),
            )

    strategies = tuple(dict.fromkeys(_strategy(s.suggested_strategy) for s in steps))
    for s in strategies:
        if s not in STRATEGIES:
            notes.append(f"illegal_strategy:{s}")
    return DecompositionPlan(
        relation=rel,
        a=ae,
        b=be,
        steps=steps,
        suggested_strategies=strategies,
        composition=composition,
        notes=tuple(notes),
    )
