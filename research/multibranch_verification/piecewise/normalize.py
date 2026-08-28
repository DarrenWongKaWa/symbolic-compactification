"""Normalize a Piecewise family from conditions only.

Roles:

- ``True`` -> generic
- a pairwise ``Eq`` of two index symbols -> diagonal
- ``Eq`` / ``And`` of equalities involving three or more index symbols
  -> higher-degeneracy

This module does not collapse branches, does not infer confluence, and
does not emit FAMILY_ZERO. A common AppliedUndef spectator is reported
only when it exactly divides every member.
"""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

import sympy
from sympy.core.function import AppliedUndef

from research.scalable_verification.factor.split import (
    _exact_eq,
    _is_unit,
    _peel_applied_undef,
    split_multiplicative,
)

GENERIC = "generic"
DIAGONAL = "diagonal"
HIGHER_DEGENERACY = "higher-degeneracy"
UNKNOWN_ROLE = "unknown"

ROLES = (GENERIC, DIAGONAL, HIGHER_DEGENERACY, UNKNOWN_ROLE)

_ONE = sympy.Integer(1)
_PEEL_OPS_CAP = 80

_COND_LOCALS: dict[str, Any] = {
    "Equality": sympy.Equality,
    "Eq": sympy.Eq,
    "Unequality": sympy.Unequality,
    "Ne": sympy.Ne,
    "StrictLessThan": sympy.StrictLessThan,
    "Lt": sympy.Lt,
    "StrictGreaterThan": sympy.StrictGreaterThan,
    "Gt": sympy.Gt,
    "LessThan": sympy.LessThan,
    "Le": sympy.Le,
    "GreaterThan": sympy.GreaterThan,
    "Ge": sympy.Ge,
    "And": sympy.And,
    "Or": sympy.Or,
    "Not": sympy.Not,
    "Symbol": sympy.Symbol,
    "Integer": sympy.Integer,
    "Rational": sympy.Rational,
    "true": sympy.S.true,
    "false": sympy.S.false,
    "True": True,
    "False": False,
}


def classify_condition(cond: Any) -> dict[str, Any]:
    """Role of one Piecewise condition. Does not inspect branch text."""
    parsed = _parse_cond(cond)
    if parsed is None:
        return _role_payload(UNKNOWN_ROLE, [], [], "unparsed_condition")
    if _is_true(parsed):
        return _role_payload(GENERIC, [], [], "tautology")
    eqs = _equality_atoms(parsed)
    if eqs is None:
        return _role_payload(UNKNOWN_ROLE, [], [], "not_pure_index_equality")
    if not eqs:
        return _role_payload(GENERIC, [], [], "tautology")
    names = _index_names(eqs)
    if names is None:
        return _role_payload(UNKNOWN_ROLE, [], [sympy.srepr(eq) for eq in eqs],
                             "equality_not_symbol_pair")
    eq_reprs = [sympy.srepr(eq) for eq in eqs]
    if len(names) == 2:
        return _role_payload(DIAGONAL, names, eq_reprs, "pairwise_index_equality")
    if len(names) >= 3:
        return _role_payload(HIGHER_DEGENERACY, names, eq_reprs,
                             "three_or_more_index_equality")
    return _role_payload(UNKNOWN_ROLE, names, eq_reprs, "too_few_index_symbols")


def normalize_piecewise_family(members: Any) -> dict[str, Any]:
    """Assign roles and extract a common AppliedUndef spectator if exact.

    Input is a sequence of ``{cond, text}`` (optional ``member_id`` /
    ``expr``), a frozen hypothesis dict with ``members``, a sequence of
    ``(expr, cond)`` pairs, or a ``sympy.Piecewise``. Branch order is
    preserved. Branches are never merged.
    """
    recs = _coerce_members(members)
    classified: list[dict[str, Any]] = []
    exprs: list[Optional[sympy.Expr]] = []
    for rec in recs:
        role_info = classify_condition(rec.get("cond"))
        expr = _member_expr(rec)
        exprs.append(expr)
        classified.append({
            "member_id": rec["member_id"],
            "role": role_info["role"],
            "cond": rec.get("cond"),
            "n_indices": role_info["n_indices"],
            "index_symbols": list(role_info["index_symbols"]),
            "equalities": list(role_info["equalities"]),
            "role_note": role_info["note"],
            "text": rec.get("text"),
            "expr": expr,
            "local": expr,
        })

    roles = {r: [] for r in ROLES}
    for row in classified:
        roles[row["role"]].append(row["member_id"])

    spectator, locals_, certified, note = _common_spectator(exprs)
    if certified:
        for row, loc in zip(classified, locals_):
            row["local"] = loc

    return {
        "members": classified,
        "n_members": len(classified),
        "roles": roles,
        "n_generic": len(roles[GENERIC]),
        "n_diagonal": len(roles[DIAGONAL]),
        "n_higher_degeneracy": len(roles[HIGHER_DEGENERACY]),
        "n_unknown": len(roles[UNKNOWN_ROLE]),
        "spectator": spectator,
        "spectator_certified": certified,
        "spectator_note": note,
        "collapsed": False,
        "confluence_inferred": False,
        "note": (
            "roles from conditions only; branches not collapsed; "
            "no confluence inferred"
        ),
    }


def _role_payload(
    role: str,
    names: Sequence[str],
    equalities: Sequence[str],
    note: str,
) -> dict[str, Any]:
    return {
        "role": role,
        "n_indices": len(names),
        "index_symbols": list(names),
        "equalities": list(equalities),
        "note": note,
    }


def _is_true(cond: Any) -> bool:
    return cond is True or cond is sympy.S.true or cond == sympy.true


def _parse_cond(cond: Any) -> Optional[sympy.Basic]:
    if cond is None:
        return None
    if isinstance(cond, bool):
        return sympy.S.true if cond else sympy.S.false
    if _is_true(cond):
        return sympy.S.true
    if cond is False or cond is sympy.S.false or cond == sympy.false:
        return sympy.S.false
    if isinstance(cond, sympy.Basic):
        return cond
    if isinstance(cond, str):
        s = cond.strip()
        if not s:
            return None
        if s in ("True", "true"):
            return sympy.S.true
        if s in ("False", "false"):
            return sympy.S.false
        try:
            parsed = sympy.sympify(s, locals=dict(_COND_LOCALS), evaluate=False)
        except (sympy.SympifyError, TypeError, ValueError, SyntaxError):
            return None
        if isinstance(parsed, bool):
            return sympy.S.true if parsed else sympy.S.false
        if isinstance(parsed, sympy.Basic):
            return parsed
        return None
    return None


def _equality_atoms(cond: sympy.Basic) -> Optional[list[sympy.Equality]]:
    if _is_true(cond):
        return []
    if cond is False or cond == sympy.false:
        return None
    if isinstance(cond, sympy.Equality):
        return [cond]
    if isinstance(cond, sympy.And):
        atoms: list[sympy.Equality] = []
        for arg in cond.args:
            sub = _equality_atoms(arg)
            if sub is None:
                return None
            atoms.extend(sub)
        return atoms
    return None


def _index_names(eqs: Sequence[sympy.Equality]) -> Optional[list[str]]:
    names: list[str] = []
    seen: set[str] = set()
    for eq in eqs:
        lhs, rhs = eq.lhs, eq.rhs
        if not (isinstance(lhs, sympy.Symbol) and isinstance(rhs, sympy.Symbol)):
            return None
        for sym in (lhs, rhs):
            if sym.name not in seen:
                seen.add(sym.name)
                names.append(sym.name)
    names.sort()
    return names


def _coerce_members(members: Any) -> list[dict[str, Any]]:
    if isinstance(members, sympy.Piecewise):
        return [
            {
                "member_id": f"b{i}",
                "cond": cond,
                "text": expr,
                "expr": expr,
            }
            for i, (expr, cond) in enumerate(members.args)
        ]
    if isinstance(members, Mapping) and "members" in members:
        members = members["members"]
    if members is None:
        return []
    if not isinstance(members, Sequence) or isinstance(members, (str, bytes)):
        return []
    out: list[dict[str, Any]] = []
    for i, raw in enumerate(members):
        out.append(_coerce_one(raw, i))
    return out


def _coerce_one(raw: Any, index: int) -> dict[str, Any]:
    fallback = f"b{index}"
    if isinstance(raw, Mapping):
        mid = raw.get("member_id") or raw.get("id") or raw.get("gid") or fallback
        rec = {
            "member_id": str(mid),
            "cond": raw.get("cond"),
            "text": raw.get("text"),
        }
        if "expr" in raw:
            rec["expr"] = raw["expr"]
        return rec
    if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)) and len(raw) == 2:
        expr, cond = raw[0], raw[1]
        return {
            "member_id": fallback,
            "cond": cond,
            "text": expr,
            "expr": expr if isinstance(expr, sympy.Expr) else None,
        }
    return {"member_id": fallback, "cond": None, "text": raw}


def _member_expr(rec: Mapping[str, Any]) -> Optional[sympy.Expr]:
    for key in ("expr", "text"):
        val = rec.get(key)
        expr = _to_expr(val)
        if expr is not None:
            return expr
    return None


def _to_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, float):
        return sympy.Float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        return _parse_text(s)
    return None


def _parse_text(text: str) -> Optional[sympy.Expr]:
    try:
        from research.llm_abstraction.constructor import parse_flex
    except Exception:
        parse_flex = None
    if parse_flex is not None:
        try:
            expr = parse_flex(text, [], ["h1", "h2", "epsilon"])
        except Exception:
            expr = None
        if isinstance(expr, sympy.Expr):
            return expr
    try:
        parsed = sympy.sympify(text, evaluate=False)
    except (sympy.SympifyError, TypeError, ValueError, SyntaxError):
        return None
    return parsed if isinstance(parsed, sympy.Expr) else None


def _count_ops(expr: sympy.Expr) -> int:
    try:
        return int(sympy.count_ops(expr, visual=False))
    except Exception:
        return _PEEL_OPS_CAP + 1


def _undef_factors(expr: sympy.Expr) -> list[sympy.Expr]:
    explicit = [
        arg for arg in sympy.Mul.make_args(expr) if isinstance(arg, AppliedUndef)
    ]
    if explicit:
        return explicit
    if _count_ops(expr) > _PEEL_OPS_CAP:
        return []
    try:
        spectator, _rest = _peel_applied_undef(expr)
    except Exception:
        return []
    return [
        arg for arg in sympy.Mul.make_args(spectator)
        if isinstance(arg, AppliedUndef)
    ]


def _intersect_undef(groups: Sequence[Sequence[sympy.Expr]]) -> list[sympy.Expr]:
    if not groups:
        return []
    common = list(groups[0])
    for other in groups[1:]:
        used = [False] * len(other)
        nxt: list[sympy.Expr] = []
        for xa in common:
            for i, xb in enumerate(other):
                if used[i]:
                    continue
                if xa == xb:
                    nxt.append(xa)
                    used[i] = True
                    break
        common = nxt
        if not common:
            break
    return common


def _sorted_product(factors: Sequence[sympy.Expr]) -> sympy.Expr:
    facs = [f for f in factors if f not in (1, _ONE)]
    facs.sort(key=sympy.default_sort_key)
    if not facs:
        return _ONE
    return sympy.Mul(*facs)


def _strip_undef(expr: sympy.Expr, factors: Sequence[sympy.Expr]) -> Optional[sympy.Expr]:
    if not factors:
        return expr
    args = list(sympy.Mul.make_args(expr))
    used = [False] * len(factors)
    rest: list[sympy.Expr] = []
    for arg in args:
        taken = False
        if isinstance(arg, AppliedUndef):
            for i, fac in enumerate(factors):
                if used[i]:
                    continue
                if arg == fac:
                    used[i] = True
                    taken = True
                    break
        if not taken:
            rest.append(arg)
    if not all(used):
        return None
    local = sympy.Mul(*rest) if rest else _ONE
    if _exact_eq(expr, _sorted_product(factors) * local):
        return local
    return None


def _divide_peel(expr: sympy.Expr, spectator: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        local = sympy.cancel(expr / spectator)
    except Exception:
        return None
    if _exact_eq(spectator * local, expr):
        return local
    return None


def _pair_undef_agrees(exprs: Sequence[sympy.Expr], spectator: sympy.Expr) -> bool:
    """When exactly two members exist, split_multiplicative must not contradict."""
    if len(exprs) != 2:
        return True
    try:
        split = split_multiplicative(exprs[0], exprs[1])
    except Exception:
        return True
    if not split["certified"]:
        return False
    s = split["S"]
    if _is_unit(s):
        return False
    s_undef = [
        arg for arg in sympy.Mul.make_args(s) if isinstance(arg, AppliedUndef)
    ]
    if not s_undef:
        return False
    return _exact_eq(_sorted_product(s_undef), spectator)


def _common_spectator(
    exprs: Sequence[Optional[sympy.Expr]],
) -> tuple[sympy.Expr, list[Optional[sympy.Expr]], bool, str]:
    if not exprs:
        return _ONE, [], False, "no_member_expressions"
    if any(e is None for e in exprs):
        return _ONE, list(exprs), False, "unparseable_member_text"
    parsed: list[sympy.Expr] = list(exprs)  # type: ignore[arg-type]
    groups = [_undef_factors(e) for e in parsed]
    common = _intersect_undef(groups)
    if not common:
        return _ONE, list(parsed), False, "no_exact_common_applied_undef"
    spectator = _sorted_product(common)
    if _is_unit(spectator):
        return _ONE, list(parsed), False, "unit_spectator"
    locals_: list[Optional[sympy.Expr]] = []
    for expr in parsed:
        local = _strip_undef(expr, common)
        if local is None and _count_ops(expr) <= _PEEL_OPS_CAP:
            local = _divide_peel(expr, spectator)
        if local is None or not _exact_eq(spectator * local, expr):
            return _ONE, list(parsed), False, "reconstruction_failed"
        locals_.append(local)
    if not _pair_undef_agrees(parsed, spectator):
        return _ONE, list(parsed), False, "split_multiplicative_mismatch"
    return spectator, locals_, True, "exact_applied_undef_factor"
