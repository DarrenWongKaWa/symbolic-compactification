"""Exact one-parameter intermediates from source substitution or Eq imposition.

Construction is raw ``xreplace`` only. Limits, cancel, together, series,
and algebraic interpolation are not intermediates. reconstruction_ok is
True only when the constructed expression is exactly the finite
substitution image of the parent.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Optional

import sympy
from sympy.core.function import AppliedUndef

from research.iterated_confluence.schema import IntermediateExpression

SUBSTITUTION = "substitution"
EQ_IMPOSITION = "eq_imposition"

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


@dataclass(frozen=True)
class IntermediateBuild:
    """Schema record plus the constructed expr when reconstruction_ok."""

    record: IntermediateExpression
    expr: Optional[Any] = None

    @property
    def reconstruction_ok(self) -> bool:
        return bool(self.record.reconstruction_ok)

    def to_dict(self) -> dict[str, Any]:
        d = self.record.to_dict()
        d["expr"] = sympy.srepr(self.expr) if isinstance(self.expr, sympy.Basic) else None
        return d


def build_intermediate(
    parent_expr: Any,
    variable: Any,
    target_value: Any,
    parent_id: Any,
    symbols: Any = None,
    *,
    condition: Any = None,
) -> IntermediateBuild:
    """Build a source-derived intermediate by exact substitution.

    ``variable`` / ``target_value`` declare ``symbol -> value``. An
    ``Eq`` in ``variable``, ``target_value``, or ``condition`` is Eq
    imposition. A vanishing denominator is a limit edge, not an
    intermediate.
    """
    pid = str(parent_id or "").strip()
    parent = _coerce(parent_expr, None, symbols)
    if parent is None or not pid:
        return _refuse(pid, "", "refused:parse_failed")

    resolved = _resolve_substitution(variable, target_value, condition, parent, symbols)
    if resolved is None:
        return _refuse(pid, "", "refused:no_declared_substitution")
    var, val, kind = resolved
    transformation = kind

    if condition is not None and not _condition_allows(condition, var, val, parent, symbols):
        return _refuse(pid, transformation, "refused:not_from_condition", var, val)

    if _denominator_blocks(parent, var, val):
        return _refuse(pid, transformation, "refused:requires_limit", var, val)

    try:
        constructed = parent.xreplace({var: val})
    except Exception:
        return _refuse(pid, transformation, "refused:substitution_failed", var, val)

    if not _is_finite(constructed):
        return _refuse(pid, transformation, "refused:not_finite", var, val)

    if not _reconstruction_agrees(parent, var, val, constructed):
        return _refuse(pid, transformation, "refused:reconstruction_mismatch", var, val)

    record = IntermediateExpression(
        intermediate_id=_intermediate_id(pid, var, val),
        parent_id=pid,
        transformation=transformation,
        reconstruction_ok=True,
        provenance=(
            f"reconstruction: parent.xreplace({{{_srepr(var)}: {_srepr(val)}}}) "
            f"== constructed; constructed is finite"
        ),
        expr_sha256=_sha(constructed),
    )
    return IntermediateBuild(record=record, expr=constructed)


def _refuse(
    parent_id: str,
    transformation: str,
    provenance: str,
    var: Any = None,
    val: Any = None,
) -> IntermediateBuild:
    iid = _intermediate_id(parent_id, var, val) if parent_id else ""
    record = IntermediateExpression(
        intermediate_id=iid,
        parent_id=parent_id,
        transformation=transformation,
        reconstruction_ok=False,
        provenance=provenance,
        expr_sha256="",
    )
    return IntermediateBuild(record=record, expr=None)


def _reconstruction_agrees(
    parent: sympy.Expr,
    var: sympy.Expr,
    val: sympy.Expr,
    constructed: sympy.Expr,
) -> bool:
    try:
        raw = parent.xreplace({var: val})
    except Exception:
        return False
    if constructed != raw:
        return False
    try:
        subbed = parent.subs(var, val)
    except Exception:
        subbed = None
    if subbed is not None and _is_finite(subbed) and subbed != constructed:
        return False
    return True


def _resolve_substitution(
    variable: Any,
    target_value: Any,
    condition: Any,
    parent: sympy.Expr,
    symbols: Any,
) -> Optional[tuple[sympy.Expr, sympy.Expr, str]]:
    var_eq = _as_equality(variable, parent, symbols)
    if var_eq is not None:
        lhs, rhs = _align_pair(var_eq.lhs, var_eq.rhs, parent)
        if lhs is None or rhs is None:
            return None
        if target_value is not None and not _is_empty(target_value):
            tv = _coerce(target_value, parent, symbols)
            tv_eq = _as_equality(target_value, parent, symbols)
            if tv_eq is not None:
                if not _same_eq(var_eq, tv_eq, parent):
                    return None
            elif tv is None or (tv != rhs and tv != lhs):
                return None
        return lhs, rhs, EQ_IMPOSITION

    tv_eq = _as_equality(target_value, parent, symbols)
    if tv_eq is not None:
        lhs, rhs = _align_pair(tv_eq.lhs, tv_eq.rhs, parent)
        if lhs is None or rhs is None:
            return None
        if variable is not None and not _is_empty(variable):
            var = _coerce(variable, parent, symbols)
            if var is None:
                return None
            var = _align(var, parent)
            if var == lhs:
                return lhs, rhs, EQ_IMPOSITION
            if var == rhs:
                return rhs, lhs, EQ_IMPOSITION
            return None
        return lhs, rhs, EQ_IMPOSITION

    if variable is not None and not _is_empty(variable) and target_value is not None and not _is_empty(target_value):
        var = _coerce(variable, parent, symbols)
        val = _coerce(target_value, parent, symbols)
        if var is None or val is None:
            return None
        var, val = _align(var, parent), _align(val, parent)
        if var is None or val is None:
            return None
        return var, val, SUBSTITUTION

    cond_eqs = _condition_equalities(condition, parent, symbols)
    if len(cond_eqs) == 1:
        lhs, rhs = cond_eqs[0]
        return lhs, rhs, EQ_IMPOSITION
    return None


def _condition_allows(
    condition: Any,
    var: sympy.Expr,
    val: sympy.Expr,
    parent: sympy.Expr,
    symbols: Any,
) -> bool:
    parsed = _coerce_condition(condition, parent, symbols)
    if parsed is None:
        return False
    if _is_true(parsed):
        return True
    pairs = _condition_equalities(condition, parent, symbols)
    if not pairs:
        return False
    for lhs, rhs in pairs:
        if (var == lhs and val == rhs) or (var == rhs and val == lhs):
            return True
    return False


def _condition_equalities(
    condition: Any,
    parent: sympy.Expr,
    symbols: Any,
) -> list[tuple[sympy.Expr, sympy.Expr]]:
    parsed = _coerce_condition(condition, parent, symbols)
    if parsed is None or _is_true(parsed):
        return []
    eqs = _equality_atoms(parsed)
    if eqs is None:
        return []
    out: list[tuple[sympy.Expr, sympy.Expr]] = []
    for eq in eqs:
        lhs, rhs = _align_pair(eq.lhs, eq.rhs, parent)
        if lhs is None or rhs is None:
            return []
        out.append((lhs, rhs))
    return out


def _denominator_blocks(parent: sympy.Expr, var: sympy.Expr, val: sympy.Expr) -> bool:
    """True when a denominator vanishes identically — a limit, not a sub."""
    for base in _negative_pow_bases(parent):
        try:
            hit = base.xreplace({var: val})
        except Exception:
            return True
        if not _is_finite(hit):
            return True
        if _identically_zero(hit) is True:
            return True
    return False


def _negative_pow_bases(expr: sympy.Expr):
    if not isinstance(expr, sympy.Basic):
        return
    if expr.is_Pow:
        try:
            if expr.exp.is_number and expr.exp < 0:
                yield expr.base
        except Exception:
            pass
        yield from _negative_pow_bases(expr.base)
        yield from _negative_pow_bases(expr.exp)
        return
    for arg in expr.args:
        yield from _negative_pow_bases(arg)


def _identically_zero(expr: Any) -> Optional[bool]:
    if expr is None:
        return None
    if expr == 0:
        return True
    iz = getattr(expr, "is_zero", None)
    if iz is True:
        return True
    if iz is False:
        return False
    return None


def _is_finite(expr: Any) -> bool:
    if expr is None:
        return False
    if not isinstance(expr, sympy.Basic):
        try:
            expr = sympy.sympify(expr)
        except Exception:
            return False
    if any(expr == sentinel for sentinel in _NONFINITE):
        return False
    try:
        if expr.has(*_NONFINITE) or expr.has(sympy.nan):
            return False
    except Exception:
        return False
    if isinstance(expr, sympy.Limit) or expr.has(sympy.Limit):
        return False
    try:
        if expr.is_infinite is True:
            return False
    except Exception:
        pass
    return True


def _intermediate_id(parent_id: str, var: Any, val: Any) -> str:
    if not parent_id:
        return ""
    if var is None and val is None:
        return f"{parent_id}|refused"
    return f"{parent_id}|{_srepr(var)}->{_srepr(val)}"


def _sha(expr: sympy.Expr) -> str:
    return hashlib.sha256(sympy.srepr(expr).encode("utf-8")).hexdigest()


def _srepr(obj: Any) -> str:
    if isinstance(obj, sympy.Basic):
        return sympy.srepr(obj)
    if obj is None:
        return ""
    return str(obj)


def _is_empty(obj: Any) -> bool:
    if obj is None:
        return True
    if isinstance(obj, str) and not obj.strip():
        return True
    return False


def _is_true(cond: Any) -> bool:
    if cond is True or cond is sympy.S.true:
        return True
    if isinstance(cond, str) and cond.strip() == "True":
        return True
    return False


def _as_equality(obj: Any, parent: sympy.Expr, symbols: Any) -> Optional[sympy.Equality]:
    if obj is None or isinstance(obj, bool):
        return None
    if isinstance(obj, sympy.Equality):
        return obj
    coerced = _coerce_condition(obj, parent, symbols)
    if isinstance(coerced, sympy.Equality):
        return coerced
    return None


def _same_eq(a: sympy.Equality, b: sympy.Equality, parent: sympy.Expr) -> bool:
    al, ar = _align_pair(a.lhs, a.rhs, parent)
    bl, br = _align_pair(b.lhs, b.rhs, parent)
    if None in (al, ar, bl, br):
        return False
    return (al == bl and ar == br) or (al == br and ar == bl)


def _equality_atoms(cond: Any) -> Optional[list[sympy.Equality]]:
    if cond is True or cond is sympy.S.true:
        return []
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


def _coerce_condition(obj: Any, parent: sympy.Expr, symbols: Any) -> Any:
    if obj is None:
        return None
    if obj is True or obj is False or obj is sympy.S.true or obj is sympy.S.false:
        return obj
    if isinstance(obj, sympy.Basic):
        return _align(obj, parent)
    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None
        if s == "True":
            return True
        loc = _locals(parent, symbols)
        loc.update(
            {
                "Equality": sympy.Equality,
                "Eq": sympy.Eq,
                "And": sympy.And,
                "Or": sympy.Or,
                "Not": sympy.Not,
                "Symbol": sympy.Symbol,
                "Integer": sympy.Integer,
                "true": sympy.S.true,
                "false": sympy.S.false,
                "True": True,
                "False": False,
            }
        )
        try:
            parsed = sympy.sympify(s, locals=loc, evaluate=False)
        except (sympy.SympifyError, TypeError, ValueError, SyntaxError):
            return None
        return _align(parsed, parent) if isinstance(parsed, sympy.Basic) else parsed
    return None


def _coerce(obj: Any, parent: Optional[sympy.Expr], symbols: Any) -> Optional[sympy.Expr]:
    if obj is None or isinstance(obj, bool):
        return None
    if isinstance(obj, sympy.Expr):
        return _align(obj, parent) if parent is not None else obj
    if isinstance(obj, int):
        return sympy.Integer(obj)
    if isinstance(obj, str):
        s = obj.strip()
        if not s:
            return None
        loc = _locals(parent, symbols)
        try:
            parsed = sympy.sympify(s, locals=loc, evaluate=False)
        except (sympy.SympifyError, TypeError, ValueError, SyntaxError):
            return None
        if not isinstance(parsed, sympy.Expr):
            return None
        return _align(parsed, parent) if parent is not None else parsed
    try:
        parsed = sympy.sympify(obj)
    except (sympy.SympifyError, TypeError, ValueError):
        return None
    if not isinstance(parsed, sympy.Expr):
        return None
    return _align(parsed, parent) if parent is not None else parsed


def _locals(parent: Optional[sympy.Expr], symbols: Any) -> dict[str, Any]:
    loc: dict[str, Any] = {}
    if isinstance(parent, sympy.Basic):
        for s in parent.free_symbols:
            if isinstance(s, sympy.Symbol):
                loc[s.name] = s
        for fn in parent.atoms(AppliedUndef):
            loc[str(fn.func)] = fn.func
    for item in list(symbols or []):
        if isinstance(item, sympy.Symbol):
            loc.setdefault(item.name, item)
        elif isinstance(item, str) and item:
            loc.setdefault(item, sympy.Symbol(item))
        elif isinstance(item, dict):
            name = item.get("name")
            if name:
                loc.setdefault(str(name), sympy.Symbol(str(name)))
    return loc


def _align(expr: Any, parent: Optional[sympy.Expr]) -> Any:
    if parent is None or not isinstance(expr, sympy.Basic) or not isinstance(parent, sympy.Basic):
        return expr
    cmap: dict[str, sympy.Symbol] = {}
    for s in parent.free_symbols:
        if isinstance(s, sympy.Symbol) and s.name not in cmap:
            cmap[s.name] = s
    repl = {
        s: cmap[s.name]
        for s in expr.free_symbols
        if isinstance(s, sympy.Symbol) and s.name in cmap and s != cmap[s.name]
    }
    return expr.xreplace(repl) if repl else expr


def _align_pair(
    lhs: Any, rhs: Any, parent: sympy.Expr
) -> tuple[Optional[sympy.Expr], Optional[sympy.Expr]]:
    a = lhs if isinstance(lhs, sympy.Expr) else None
    b = rhs if isinstance(rhs, sympy.Expr) else None
    if a is None or b is None:
        return None, None
    return _align(a, parent), _align(b, parent)
