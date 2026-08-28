"""Per-atom series confluence. Timeout/size-guard is UNKNOWN, never ZERO.

Does not use Guo identities. Each additive polygamma term is series-expanded
independently, then a Laurent ``t^0`` coefficient is compared to the target.
"""
from __future__ import annotations

from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.iterated_confluence.spectator import split_edge
from research.polygamma_confluence.schema import (
    ATOM_SERIES,
    NONZERO,
    UNKNOWN,
    ZERO,
    AtomSeriesCertificate,
)
from symbolic_compactification.budgets import BudgetExceeded

NTERMS = 6
NOUT = 2
LAURENT_SHIFT = 8
TOGETHER_OPS_CAP = 5000
SERIES_OPS_CAP = 120


def _count_ops(expr: Any) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return SERIES_OPS_CAP + 1


def _peel_undef(expr: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    spec: list[sympy.Expr] = []
    rest: list[sympy.Expr] = []
    for a in sympy.Mul.make_args(expr):
        if isinstance(a, AppliedUndef):
            spec.append(a)
        else:
            rest.append(a)
    S = sympy.Mul(*spec) if spec else sympy.Integer(1)
    K = sympy.Mul(*rest) if rest else sympy.Integer(1)
    return S, K


def _split_pref_add(
    expr: sympy.Expr,
) -> tuple[sympy.Expr, sympy.Expr, bool]:
    """K = pref * Add, Add holds the polygamma terms. Reconstruction required."""
    pre: list[sympy.Expr] = []
    add: Optional[sympy.Expr] = None
    for a in sympy.Mul.make_args(expr):
        if isinstance(a, sympy.Add) and a.atoms(sympy.polygamma):
            add = a
        else:
            pre.append(a)
    if add is None:
        return sympy.Integer(1), expr, True
    pref = sympy.Mul(*pre) if pre else sympy.Integer(1)
    ok = (pref * add) == expr
    if not ok:
        try:
            ok = sympy.expand(pref * add - expr) == 0
        except Exception:
            ok = False
    return pref, add, bool(ok)


def _series_term(term: sympy.Expr, var: sympy.Expr, point: sympy.Expr, t: sympy.Expr) -> Optional[sympy.Expr]:
    if _count_ops(term) > SERIES_OPS_CAP:
        return None
    try:
        s = term.xreplace({var: point + t}).series(t, 0, NTERMS)
    except Exception:
        return None
    if not isinstance(s, sympy.Expr):
        return None
    if s.has(sympy.Order):
        return s.removeO()
    return s


def _laurent_c0(expr: sympy.Expr, t: sympy.Expr) -> tuple[Optional[sympy.Expr], Optional[bool], list[str]]:
    steps: list[str] = []
    ops = _count_ops(expr)
    steps.append(f"together_ops:{ops}")
    if ops > TOGETHER_OPS_CAP:
        steps.append("size_guard:together")
        return None, None, steps
    try:
        s = expr.series(t, 0, NOUT)
    except Exception as exc:
        steps.append(f"total_series:{type(exc).__name__}")
        return None, None, steps
    expanded = s.removeO() if isinstance(s, sympy.Expr) and s.has(sympy.Order) else s
    try:
        expanded = sympy.expand(expanded)
        w = sympy.expand(sympy.together(expanded * t ** LAURENT_SHIFT))
        p = sympy.Poly(w, t, domain=sympy.EX)
    except Exception as exc:
        steps.append(f"laurent:{type(exc).__name__}")
        return None, None, steps
    poles_ok = True
    for k in range(-6, 0):
        ck = p.nth(k + LAURENT_SHIFT)
        if not (ck == 0 or sympy.expand(ck) == 0):
            poles_ok = False
            steps.append(f"pole_t^{k}:nonzero")
            break
    if poles_ok:
        steps.append("poles_vanished")
    return p.nth(LAURENT_SHIFT), poles_ok, steps


def _equal(a: sympy.Expr, b: sympy.Expr) -> Optional[bool]:
    if a == b:
        return True
    try:
        if sympy.expand(a - b) == 0:
            return True
    except Exception:
        pass
    try:
        d = sympy.cancel(a - b)
        if d == 0:
            return True
        if d != 0 and d.is_number:
            return False
    except Exception:
        pass
    return None


def atom_series_confluence(
    source: Any,
    target: Any,
    variable: Any,
    target_value: Any,
    symbols: Any = None,
    functions: Any = None,
) -> AtomSeriesCertificate:
    """Certify ``lim_{variable -> target_value} source = target`` by atom series."""
    steps: list[str] = []
    try:
        return _run(source, target, variable, target_value, steps)
    except BudgetExceeded:
        steps.append("timeout")
        return AtomSeriesCertificate(UNKNOWN, "timeout", steps=tuple(steps))
    except Exception as exc:
        steps.append(f"error:{type(exc).__name__}")
        return AtomSeriesCertificate(UNKNOWN, "UNKNOWN", steps=tuple(steps))


def _run(
    source: Any,
    target: Any,
    variable: Any,
    target_value: Any,
    steps: list[str],
) -> AtomSeriesCertificate:
    if not isinstance(source, sympy.Expr) or not isinstance(target, sympy.Expr):
        return AtomSeriesCertificate(UNKNOWN, "parse", steps=("parse",))
    var = variable if isinstance(variable, sympy.Expr) else None
    point = target_value if isinstance(target_value, sympy.Expr) else None
    if var is None or point is None:
        return AtomSeriesCertificate(UNKNOWN, "parse", steps=("parse:var",))

    full_ops = max(_count_ops(source), _count_ops(target))
    split = split_edge(source, target, degeneration=var)
    if split["certified"]:
        work_s, work_t = split["A_local"], split["B_local"]
        steps.append(f"split:{split['note']}")
        local_ops = max(_count_ops(work_s), _count_ops(work_t))
    else:
        work_s, work_t = source, target
        local_ops = full_ops
        steps.append(f"split:none:{split.get('note')}")

    pref, add, recon = _split_pref_add(work_s)
    steps.append(f"decompose:n={len(sympy.Add.make_args(add))}")
    if not recon:
        steps.append("reconstruction_failed")
        return AtomSeriesCertificate(
            UNKNOWN, "reconstruction", n_atoms=len(sympy.Add.make_args(add)),
            reconstruction_ok=False, full_ops=full_ops, local_ops=local_ops,
            steps=tuple(steps),
        )

    t = sympy.Dummy("t")
    cores: list[sympy.Expr] = []
    terms = list(sympy.Add.make_args(add))
    for i, term in enumerate(terms):
        core = _series_term(term, var, point, t)
        if core is None:
            steps.append(f"term{i}:UNKNOWN")
            return AtomSeriesCertificate(
                UNKNOWN, "term_series", n_atoms=len(terms),
                reconstruction_ok=True, full_ops=full_ops, local_ops=local_ops,
                steps=tuple(steps),
            )
        cores.append(core)
        steps.append(f"term{i}:series")

    combined = sympy.together(pref.xreplace({var: point + t}) * sum(cores))
    c0, poles_ok, extra = _laurent_c0(combined, t)
    steps.extend(extra)
    if c0 is None:
        return AtomSeriesCertificate(
            UNKNOWN, "laurent", n_atoms=len(terms), reconstruction_ok=True,
            poles_ok=poles_ok, full_ops=full_ops, local_ops=local_ops,
            together_ops=_count_ops(combined), steps=tuple(steps),
        )
    if poles_ok is False:
        steps.append("nonzero_pole")
        return AtomSeriesCertificate(
            NONZERO, "nonzero_pole", n_atoms=len(terms), reconstruction_ok=True,
            poles_ok=False, full_ops=full_ops, local_ops=local_ops,
            together_ops=_count_ops(combined), c0_ops=_count_ops(c0),
            steps=tuple(steps),
        )

    eq = _equal(c0, work_t)
    if eq is True:
        steps.append("t0:ZERO")
        return AtomSeriesCertificate(
            ZERO, f"{ATOM_SERIES}:t0", n_atoms=len(terms), reconstruction_ok=True,
            poles_ok=True, full_ops=full_ops, local_ops=local_ops,
            together_ops=_count_ops(combined), c0_ops=_count_ops(c0),
            steps=tuple(steps),
        )
    if eq is False:
        steps.append("t0:NONZERO")
        return AtomSeriesCertificate(
            NONZERO, f"{ATOM_SERIES}:t0", n_atoms=len(terms), reconstruction_ok=True,
            poles_ok=True, full_ops=full_ops, local_ops=local_ops,
            together_ops=_count_ops(combined), c0_ops=_count_ops(c0),
            steps=tuple(steps),
        )
    steps.append("t0:undecided")
    return AtomSeriesCertificate(
        UNKNOWN, "UNKNOWN", n_atoms=len(terms), reconstruction_ok=True,
        poles_ok=True, full_ops=full_ops, local_ops=local_ops,
        together_ops=_count_ops(combined), c0_ops=_count_ops(c0),
        steps=tuple(steps),
    )
