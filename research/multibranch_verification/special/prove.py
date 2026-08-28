"""Local polygamma prover for Track V2.

After a certified spectator split, prove or refute:

- ``d/dz polygamma(n, z) = polygamma(n + 1, z)``
- Newton first DD of ``polygamma(0, ·)`` vs ``(psi(x) - psi(y))/(x - y)``
- series of Newton DD of ``polygamma(n, ·)`` at a node ``= polygamma(n + 1, node)``

ZERO only from those identities (or identical special-function expressions).
Recurrence, reflection, chain rule, masters, and Guo kernels are not ZERO
rules. Polygamma recurrence expansion and CAS limits are not used.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Optional

import sympy

from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO
from research.scalable_verification.factor import split_additive, split_multiplicative
from research.scalable_verification.special.classify import (
    SUPPORTED,
    _MAX_CHARS,
    _UNSUPPORTED_NAME,
    _as_pair,
    _collect_texts,
    _eval_pg_d_dz,
    _has_special_fn,
    _newton_pg0_nodes,
    _too_big,
    _two_term_diff,
    classify_identity,
)

DERIVATIVE = "derivative"
NEWTON_FIRST = "newton_first"
SERIES = "series"
IDENTICAL = "identical"

SERIES_RELATIONS = frozenset({
    "series",
    "limit",
    "one_parameter_confluence",
})

_SERIES_NTERMS = 2
_SERIES_POINTS = (1, 2, sympy.Rational(3, 2))
_ONE = sympy.Integer(1)
_NEG_ONE = sympy.Integer(-1)


@dataclass(frozen=True)
class LocalProof:
    """Verdict of a local polygamma identity after spectators are removed."""

    verdict: str
    provenance: str
    steps: tuple[str, ...] = ()
    identity: str = ""
    witness: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def prove_local(
    expr_or_pair: Any,
    right: Any = None,
    *,
    relation: str = "",
    variable: Any = None,
    target: Any = None,
) -> LocalProof:
    """Return ZERO, NONZERO, or UNKNOWN for a local polygamma claim.

    ``expr_or_pair`` matches ``classify_identity`` (pair, ``Eq``, residual,
    string, or ``left``/``right`` dict). Optional ``relation`` / ``variable``
    / ``target`` select the series identity (diagonal Newton DD). Series ZERO
    is not an algebraic equality of the Newton quotient with ``polygamma(1)``.
    """
    try:
        return _prove_local(
            expr_or_pair,
            right,
            relation=relation,
            variable=variable,
            target=target,
        )
    except Exception:
        return _unknown(("exception",))


def _prove_local(
    expr_or_pair: Any,
    right: Any,
    *,
    relation: str,
    variable: Any,
    target: Any,
) -> LocalProof:
    obj: Any = expr_or_pair
    if right is not None:
        obj = (expr_or_pair, right)
    if isinstance(obj, dict):
        relation = str(obj.get("relation") or obj.get("kind") or relation or "")
        if variable is None:
            variable = obj.get("variable", obj.get("var"))
        if target is None:
            target = obj.get("target", obj.get("target_value", obj.get("to")))

    texts = _collect_texts(obj)
    if any(len(t) > _MAX_CHARS for t in texts):
        return _unknown(("size_guard:chars",))
    if any(_UNSUPPORTED_NAME.search(t) for t in texts):
        return _unknown(("master_or_L4_L7",))

    pair = _as_pair(obj)
    if pair is None and isinstance(obj, sympy.Expr):
        pair = _as_pair(sympy.expand(obj))
    if pair is None:
        return _unknown(("unparsed",))
    left, right_e = pair
    if _too_big(left) or _too_big(right_e):
        return _unknown(("size_guard:ops",))

    had_special = _has_special_fn(left) or _has_special_fn(right_e)
    steps: list[str] = []

    clf0 = classify_identity((left, right_e))
    steps.append(f"classify_identity:{clf0}")
    if clf0 == SUPPORTED:
        ident = _supported_kind(left, right_e)
        return _zero(ident, "classify_identity", steps)

    mismatch0 = _form_mismatch(left, right_e)
    if mismatch0 is not None:
        ident, witness = mismatch0
        return _nonzero(ident, ident, steps, witness)

    left, right_e, spec_steps = _strip_spectators(left, right_e)
    steps.extend(spec_steps)
    if _too_big(left) or _too_big(right_e):
        return _unknown(tuple(steps + ["size_guard:ops_local"]))

    local_special = _has_special_fn(left) or _has_special_fn(right_e)
    if not local_special:
        if had_special and spec_steps:
            if _expr_eq(left, right_e):
                return _zero(IDENTICAL, "identical", steps)
            if _sure_unequal(left, right_e):
                return _nonzero(IDENTICAL, "spectator_unit_mismatch", steps)
        return _unknown(tuple(steps + ["no_special_function"]))

    if _expr_eq(left, right_e):
        return _zero(IDENTICAL, "identical", steps)

    clf = classify_identity((left, right_e))
    if clf != clf0:
        steps.append(f"classify_identity_local:{clf}")
    if clf == SUPPORTED:
        ident = _supported_kind(left, right_e)
        return _zero(ident, "classify_identity", steps)

    mismatch = _form_mismatch(left, right_e)
    if mismatch is not None:
        ident, witness = mismatch
        return _nonzero(ident, ident, steps, witness)

    rel = (relation or "").strip().lower()
    series_mode = rel in SERIES_RELATIONS or (variable is not None and target is not None)
    if series_mode:
        got = _series_identity(left, right_e, variable, target, steps)
        if got is not None:
            return got

    residual = _refute_residual_series(left, right_e)
    if residual is not None:
        return _nonzero("", "residual_series", steps, residual)

    return _unknown(tuple(steps + ["undecided"]))


def _strip_spectators(
    a: sympy.Expr,
    b: sympy.Expr,
) -> tuple[sympy.Expr, sympy.Expr, list[str]]:
    """Exact spectator split. Units and zero are not spectators."""
    steps: list[str] = []
    mul = split_multiplicative(a, b)
    if mul["certified"] and not _is_unit(mul["S"]):
        a, b = mul["A_local"], mul["B_local"]
        steps.append(f"spectator_mul:{mul['note']}")
    add = split_additive(a, b)
    if add["certified"] and add["S"] != 0:
        a, b = add["A_local"], add["B_local"]
        steps.append(f"spectator_add:{add['note']}")
    return a, b, steps


def _supported_kind(a: sympy.Expr, b: sympy.Expr) -> str:
    if _eval_pg_d_dz(a) is not None or _eval_pg_d_dz(b) is not None:
        return DERIVATIVE
    if _newton_pg0_nodes(a) is not None or _newton_pg0_nodes(b) is not None:
        return NEWTON_FIRST
    if isinstance(a, sympy.polygamma) and isinstance(b, sympy.polygamma):
        return DERIVATIVE
    return DERIVATIVE


def _form_mismatch(
    a: sympy.Expr,
    b: sympy.Expr,
) -> Optional[tuple[str, str]]:
    for left, right in ((a, b), (b, a)):
        ev = _eval_pg_d_dz(left)
        if ev is not None and _sure_unequal(ev, right):
            return DERIVATIVE, str(ev)
    pa = _newton_pg_nodes(a)
    pb = _newton_pg_nodes(b)
    if pa is not None and pb is not None:
        n1, u1, v1, s1 = pa
        n2, u2, v2, s2 = pb
        nodes1 = frozenset((u1, v1))
        nodes2 = frozenset((u2, v2))
        same = (
            s1 == 1
            and s2 == 1
            and _expr_eq(n1, n2)
            and nodes1 == nodes2
            and len(nodes1) == 2
        )
        if not same:
            return NEWTON_FIRST, "newton_mismatch"
    return None


def _series_identity(
    a: sympy.Expr,
    b: sympy.Expr,
    variable: Any,
    target: Any,
    steps: list[str],
) -> Optional[LocalProof]:
    var, to = _coerce_var(variable, (a, b)), _coerce_var(target, (a, b))
    if var is None or to is None:
        var, to = _infer_series_nodes(a, b)
    if var is None or to is None:
        var, to = _infer_series_nodes(b, a)
    if var is None or to is None:
        steps.append("series:missing_var_or_target")
        return None
    steps.append(f"series:{var}->{to}")
    const = _series_leading(a, var, to)
    if const is None:
        steps.append("series:failed")
        return None
    if _expr_eq(const, b):
        return _zero(SERIES, "series", steps, str(const))
    if _sure_unequal(const, b):
        return _nonzero(SERIES, "series", steps, str(const))
    const_b = _series_leading(b, var, to)
    if const_b is not None and _expr_eq(const, const_b):
        return _zero(SERIES, "series", steps, str(const))
    if const_b is not None and _sure_unequal(const, const_b):
        return _nonzero(SERIES, "series", steps, str(const))
    steps.append("series:undecided")
    return None


def _infer_series_nodes(
    newton_side: sympy.Expr,
    claimed: sympy.Expr,
) -> tuple[Optional[sympy.Expr], Optional[sympy.Expr]]:
    nodes = _newton_pg_nodes(newton_side)
    if nodes is None or not isinstance(claimed, sympy.polygamma) or len(claimed.args) != 2:
        return None, None
    n_ord, u, v, sign = nodes
    if sign != 1:
        return None, None
    arg = claimed.args[1]
    order = claimed.args[0]
    if not _expr_eq(order, n_ord + 1):
        if arg == u:
            return v, u
        if arg == v:
            return u, v
        return None, None
    if arg == u:
        return v, u
    if arg == v:
        return u, v
    return None, None


def _series_leading(
    expr: sympy.Expr,
    moving: sympy.Expr,
    target: sympy.Expr,
) -> Optional[sympy.Expr]:
    if _too_big(expr):
        return None
    if not expr.has(moving):
        try:
            val = expr.xreplace({moving: target})
        except Exception:
            return None
        if _nonfinite(val):
            return None
        return val
    t = sympy.Dummy("t")
    try:
        e = expr.xreplace({moving: target + t})
        s = e.series(t, 0, _SERIES_NTERMS)
    except Exception:
        return None
    if not isinstance(s, sympy.Expr) or s.has(sympy.Limit):
        return None
    try:
        core = s.removeO() if s.has(sympy.Order) else s
        const = sympy.expand(core.xreplace({t: 0}))
    except Exception:
        return None
    if _nonfinite(const):
        return None
    return const


def _refute_residual_series(a: sympy.Expr, b: sympy.Expr) -> Optional[str]:
    """NONZERO witness: series constant with ``is_zero is False``.

    A vanishing series (recurrence, admitted identities) is not ZERO here.
    """
    try:
        residual = a - b
    except Exception:
        return None
    if _too_big(residual):
        return None
    variables = _residual_vars(residual)
    for var in variables:
        for z0 in _SERIES_POINTS:
            try:
                s = residual.series(var, z0, 1)
            except Exception:
                continue
            if not isinstance(s, sympy.Expr) or s.has(sympy.Limit):
                continue
            try:
                core = s.removeO() if s.has(sympy.Order) else s
                const = sympy.expand(core.xreplace({var: z0}))
            except Exception:
                continue
            if _nonfinite(const):
                continue
            try:
                if const.is_zero is False:
                    return str(const)
            except Exception:
                continue
    return None


def _residual_vars(expr: sympy.Expr) -> list[sympy.Expr]:
    args = [p.args[1] for p in expr.atoms(sympy.polygamma) if len(p.args) == 2]
    out: list[sympy.Expr] = []
    seen: set[sympy.Expr] = set()
    for v in args + list(expr.free_symbols):
        if v in seen:
            continue
        if isinstance(v, sympy.Integer):
            continue
        seen.add(v)
        out.append(v)
    return out


def _newton_pg_nodes(
    expr: sympy.Expr,
) -> Optional[tuple[sympy.Expr, sympy.Expr, sympy.Expr, int]]:
    """``±(polygamma(n,u)-polygamma(n,v))/(u-v)`` → ``(n, u, v, sign)``."""
    num, den = expr.as_numer_denom()
    nd = _two_term_diff(den)
    nn = _two_term_diff(num)
    if nd is None or nn is None:
        return None
    u, v = nd
    fa, fb = nn
    if not isinstance(fa, sympy.polygamma) or not isinstance(fb, sympy.polygamma):
        return None
    if len(fa.args) != 2 or len(fb.args) != 2:
        return None
    n_a, n_b = fa.args[0], fb.args[0]
    if not _expr_eq(n_a, n_b):
        return None
    xa, xb = fa.args[1], fb.args[1]
    if xa == u and xb == v:
        return n_a, u, v, 1
    if xa == v and xb == u:
        return n_a, u, v, -1
    return None


def _coerce_var(val: Any, exprs: tuple[sympy.Expr, sympy.Expr]) -> Optional[sympy.Expr]:
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, sympy.Expr):
        return val
    if isinstance(val, str):
        name = val.strip()
        if not name:
            return None
        for e in exprs:
            for atom in list(e.free_symbols) + list(e.atoms(sympy.Function)):
                if str(atom) == name:
                    return atom
        try:
            got = sympy.sympify(name)
        except Exception:
            return sympy.Symbol(name)
        return got if isinstance(got, sympy.Expr) else sympy.Symbol(name)
    return None


def _expr_eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        if sympy.expand(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        if sympy.cancel(a - b) == 0:
            return True
    except Exception:
        pass
    return False


def _sure_unequal(a: sympy.Expr, b: sympy.Expr) -> bool:
    if _expr_eq(a, b):
        return False
    if isinstance(a, sympy.polygamma) and isinstance(b, sympy.polygamma):
        if len(a.args) == 2 and len(b.args) == 2:
            na, za = a.args
            nb, zb = b.args
            if _expr_eq(za, zb) and not _expr_eq(na, nb):
                return True
            if _expr_eq(na, nb) and not _expr_eq(za, zb):
                return True
    try:
        d = sympy.expand(a - b)
    except Exception:
        d = a - b
    try:
        if d.is_zero is False:
            return True
    except Exception:
        pass
    if getattr(d, "is_number", False):
        try:
            if d != 0:
                return True
        except Exception:
            pass
    try:
        coeff, rest = d.as_coeff_Mul()
    except Exception:
        return False
    if isinstance(rest, sympy.polygamma) and coeff.is_number and coeff != 0:
        return True
    return False


def _is_unit(expr: sympy.Expr) -> bool:
    return expr in (1, -1, _ONE, _NEG_ONE, sympy.S.One, sympy.S.NegativeOne)


def _nonfinite(expr: Any) -> bool:
    if expr is None or not isinstance(expr, sympy.Basic):
        return True
    try:
        if expr.has(sympy.nan, sympy.zoo, sympy.oo, sympy.Limit):
            return True
    except Exception:
        return True
    return expr in (sympy.nan, sympy.zoo, sympy.oo)


def _zero(
    identity: str,
    provenance: str,
    steps: list[str],
    witness: Optional[str] = None,
) -> LocalProof:
    return LocalProof(
        ZERO, provenance, tuple(steps), identity, witness,
    )


def _nonzero(
    identity: str,
    provenance: str,
    steps: list[str],
    witness: Optional[str] = None,
) -> LocalProof:
    return LocalProof(
        NONZERO, provenance, tuple(steps), identity, witness,
    )


def _unknown(steps: tuple[str, ...]) -> LocalProof:
    return LocalProof(UNKNOWN, "UNKNOWN", steps, "", None)
