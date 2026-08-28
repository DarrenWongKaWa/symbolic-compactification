"""Generic Newton / Hermite divided-difference recurrence checks.

Constructors are imported from ``research.representation_invention.dd``.
This module does not copy them and does not bind source members.

Named identities (definitional RHS uses constructors, not closed forms):

- ``F[x,x] = F'(x)``
- ``F[x,x,y] = (F[x,x] - F[x,y]) / (x - y)``
- ``F[x,y,y] = (F[x,y] - F[y,y]) / (x - y)``
- ``F[x,x,x] = F''(x) / 2``

Verdicts are ZERO / NONZERO / UNKNOWN. Size-guard, missing data, and
ill-posed tableaux are UNKNOWN, never ZERO. Algebraic mismatch is
NONZERO. False ZERO = 0.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import sympy

from research.representation_invention.dd import (
    HermiteDDError,
    hermite_dd,
    newton_first,
    newton_table,
    repeated_diagonal,
)

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"

KIND_FXX = "F[x,x]"
KIND_FXXY = "F[x,x,y]"
KIND_FXYY = "F[x,y,y]"
KIND_FXXX = "F[x,x,x]"
KIND_NEWTON_STEP = "newton_step"
KIND_HERMITE_STEP = "hermite_step"

REL_DD = "dd_recurrence"
REL_HERMITE = "hermite_dd_recurrence"

BACKEND_HERMITE = "research.representation_invention.dd.hermite_dd"
BACKEND_REPEATED = "research.representation_invention.dd.repeated_diagonal"
BACKEND_NEWTON_FIRST = "research.representation_invention.dd.newton_first"
BACKEND_NEWTON_TABLE = "research.representation_invention.dd.newton_table"

FORMULAS = {
    KIND_FXX: "F[x,x]=F'(x)",
    KIND_FXXY: "F[x,x,y]=(F[x,x]-F[x,y])/(x-y)",
    KIND_FXYY: "F[x,y,y]=(F[x,y]-F[y,y])/(x-y)",
    KIND_FXXX: "F[x,x,x]=F''(x)/2",
    KIND_NEWTON_STEP: "F[x0..xk]=(F[x1..xk]-F[x0..x_{k-1}])/(xk-x0)",
    KIND_HERMITE_STEP: (
        "all-equal window of k+1 copies: F^{(k)}(a)/k!; "
        "distinct endpoints: (F[z1..zk]-F[z0..z_{k-1}])/(zk-z0)"
    ),
}

_KIND_ALIASES = {
    KIND_FXX: KIND_FXX,
    "Fxx": KIND_FXX,
    "F_xx": KIND_FXX,
    "repeated": KIND_FXX,
    KIND_FXXY: KIND_FXXY,
    "Fxxy": KIND_FXXY,
    "F_xxy": KIND_FXXY,
    KIND_FXYY: KIND_FXYY,
    "Fxyy": KIND_FXYY,
    "F_xyy": KIND_FXYY,
    KIND_FXXX: KIND_FXXX,
    "Fxxx": KIND_FXXX,
    "F_xxx": KIND_FXXX,
    KIND_NEWTON_STEP: KIND_NEWTON_STEP,
    REL_DD: KIND_NEWTON_STEP,
    KIND_HERMITE_STEP: KIND_HERMITE_STEP,
    REL_HERMITE: KIND_HERMITE_STEP,
}

_NAMED_NEEDS_Y = {KIND_FXXY, KIND_FXYY}
_OPS_LIMIT = 200


@dataclass(frozen=True)
class RecurrenceResult:
    """One Newton / Hermite recurrence check."""

    verdict: str
    kind: str
    relation: str = REL_HERMITE
    note: str = ""
    formula: str = ""
    lhs: Optional[str] = None
    rhs: Optional[str] = None
    residual: Optional[str] = None
    nodes: tuple[str, ...] = ()
    multiplicities: tuple[int, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "kind": self.kind,
            "relation": self.relation,
            "note": self.note,
            "formula": self.formula,
            "lhs": self.lhs,
            "rhs": self.rhs,
            "residual": self.residual,
            "nodes": list(self.nodes),
            "multiplicities": list(self.multiplicities),
            "provenance": dict(self.provenance),
        }

    def to_obligation(self) -> dict[str, Any]:
        """Dict suitable for ``ConfluentFamilyCertificate.recurrence_obligations``."""
        return self.to_dict()


def check_recurrence(
    kind: str,
    F: Any = None,
    z: Any = None,
    x: Any = None,
    y: Any = None,
    *,
    claimed: Any = None,
    rhs: Any = None,
    nodes: Any = None,
) -> RecurrenceResult:
    """Check a Newton / Hermite recurrence identity.

    Reconstructs the left-hand divided difference from DD constructors.
    The right-hand side is the definitional formula for ``kind``, or an
    explicit ``rhs`` (adversarial orientation / factorial / derivative).
    ``claimed``, when given, is a claimed value of the left-hand DD.

    ZERO requires every comparison to be an exact symbolic identity.
    """
    canon = _normalize_kind(kind)
    raw_kind = "" if kind is None else str(kind)
    if canon is None:
        return _result(
            UNKNOWN, raw_kind, "unknown_kind",
            F=F, z=z, x=x, y=y, claimed=claimed, rhs=rhs,
        )

    missing = _missing_for_kind(canon, F=F, z=z, x=x, y=y, nodes=nodes)
    if missing:
        blocks = _named_blocks(canon, x, y) if canon not in {
            KIND_NEWTON_STEP, KIND_HERMITE_STEP,
        } else ()
        return _result(
            UNKNOWN, canon, missing,
            F=F, z=z, x=x, y=y, claimed=claimed, rhs=rhs,
            nodes=_node_strs(blocks or nodes),
            multiplicities=_mults(blocks),
        )

    F_e, z_e = _as_expr(F), _as_expr(z)
    x_e, y_e = _as_expr(x), _as_expr(y)
    claimed_e = None if claimed is None else _as_expr(claimed)
    if claimed is not None and claimed_e is None:
        return _result(
            UNKNOWN, canon, "missing_claimed",
            F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed, rhs=rhs,
        )
    rhs_given = rhs is not None
    rhs_e = None if rhs is None else _as_expr(rhs)
    if rhs_given and rhs_e is None:
        return _result(
            UNKNOWN, canon, "missing_rhs",
            F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e, rhs=rhs,
        )

    newton_nodes: Optional[list[sympy.Expr]] = None
    hermite_blocks: Optional[list[tuple[sympy.Expr, int]]] = None
    if canon == KIND_NEWTON_STEP:
        newton_nodes, err = _require_newton_nodes(nodes)
        if err:
            return _result(
                UNKNOWN, canon, err,
                F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e, rhs=rhs_e,
            )
    elif canon == KIND_HERMITE_STEP:
        hermite_blocks, err = _require_hermite_blocks(nodes)
        if err:
            return _result(
                UNKNOWN, canon, err,
                F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e, rhs=rhs_e,
                extra={"explicit_multiplicities": False},
            )
    else:
        hermite_blocks = list(_named_blocks(canon, x_e, y_e))

    node_exprs, multiplicities = _display_nodes(
        canon, x_e, y_e, newton_nodes, hermite_blocks,
    )
    extra: dict[str, Any] = {
        "explicit_F": True,
        "blocks": [[str(v), int(m)] for v, m in (hermite_blocks or [])],
        "claimed_label": _block_label(hermite_blocks or []),
    }
    if newton_nodes is not None:
        extra["newton_nodes"] = [str(n) for n in newton_nodes]
    if _coincident(x_e, y_e) and canon in _NAMED_NEEDS_Y:
        extra["coincident_nodes"] = True

    sized = [F_e, claimed_e, rhs_e]
    if _too_large(*sized):
        return _result(
            UNKNOWN, canon, "size_guard",
            F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e, rhs=rhs_e,
            nodes=node_exprs, multiplicities=multiplicities, extra=extra,
        )

    lhs_expr, lhs_note, used = _reconstruct_lhs(
        canon, F_e, z_e, x_e, y_e, newton_nodes, hermite_blocks,
    )
    extra["constructors"] = list(used)
    if lhs_note:
        return _result(
            UNKNOWN, canon, lhs_note,
            F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e, rhs=rhs_e,
            reconstruction=lhs_expr,
            nodes=node_exprs, multiplicities=multiplicities, extra=extra,
        )

    if rhs_given:
        rhs_expr = rhs_e
        extra["rhs_source"] = "supplied"
    else:
        rhs_expr, rhs_note, rhs_used = _definitional_rhs(
            canon, F_e, z_e, x_e, y_e, newton_nodes, hermite_blocks,
        )
        extra["constructors"] = list(dict.fromkeys([*used, *rhs_used]))
        extra["rhs_source"] = "definition"
        if rhs_note:
            return _result(
                UNKNOWN, canon, rhs_note,
                F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e,
                reconstruction=lhs_expr, rhs=rhs_expr,
                nodes=node_exprs, multiplicities=multiplicities, extra=extra,
            )

    checks: list[dict[str, Any]] = []
    pairs: list[tuple[str, sympy.Expr, sympy.Expr]] = [
        ("lhs_vs_rhs", lhs_expr, rhs_expr),
    ]
    if claimed_e is not None:
        pairs.insert(0, ("claimed_vs_lhs", claimed_e, lhs_expr))

    overall = ZERO
    notes: list[str] = []
    residual_out: Optional[str] = "0"
    for name, a, b in pairs:
        verdict, note, residual = _verdict_pair(a, b)
        checks.append({
            "name": name,
            "verdict": verdict,
            "note": note,
            "residual": residual,
        })
        notes.append(f"{name}:{note}")
        if verdict == NONZERO:
            overall = NONZERO
            residual_out = residual
        elif verdict == UNKNOWN and overall != NONZERO:
            overall = UNKNOWN
            if residual_out == "0":
                residual_out = residual
        elif overall == ZERO and residual_out == "0":
            residual_out = residual
    extra["checks"] = checks

    note = "identity" if overall == ZERO else (
        "mismatch" if overall == NONZERO else (notes[-1] if notes else "undecided")
    )
    if overall == NONZERO:
        for c in checks:
            if c["verdict"] == NONZERO:
                note = c["note"]
                break

    return _result(
        overall, canon, note,
        F=F_e, z=z_e, x=x_e, y=y_e, claimed=claimed_e,
        reconstruction=lhs_expr, rhs=rhs_expr, residual=residual_out,
        nodes=node_exprs, multiplicities=multiplicities, extra=extra,
    )


def _normalize_kind(kind: Any) -> Optional[str]:
    if kind is None:
        return None
    if not isinstance(kind, str):
        return None
    key = kind.strip()
    return _KIND_ALIASES.get(key)


def _missing_for_kind(kind: str, **kwargs: Any) -> Optional[str]:
    if _as_expr(kwargs.get("F")) is None:
        return "missing_F"
    if _as_expr(kwargs.get("z")) is None:
        return "missing_z"
    if kind == KIND_NEWTON_STEP:
        if kwargs.get("nodes") is None:
            return "missing_nodes"
        return None
    if kind == KIND_HERMITE_STEP:
        if kwargs.get("nodes") is None:
            return "missing_multiplicities"
        return None
    if _as_expr(kwargs.get("x")) is None:
        return "missing_x"
    if kind in _NAMED_NEEDS_Y and _as_expr(kwargs.get("y")) is None:
        return "missing_y"
    return None


def _named_blocks(
    kind: str, x: Any, y: Any,
) -> tuple[tuple[Any, int], ...]:
    if kind == KIND_FXX:
        return ((x, 2),)
    if kind == KIND_FXXY:
        return ((x, 2), (y, 1))
    if kind == KIND_FXYY:
        return ((x, 1), (y, 2))
    if kind == KIND_FXXX:
        return ((x, 3),)
    return ()


def _display_nodes(
    kind: str,
    x: Any,
    y: Any,
    newton_nodes: Optional[Sequence[Any]],
    hermite_blocks: Optional[Sequence[tuple[Any, int]]],
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    if newton_nodes is not None:
        return tuple("None" if n is None else str(n) for n in newton_nodes), ()
    if hermite_blocks:
        vals = tuple("None" if v is None else str(v) for v, _m in hermite_blocks)
        mult = tuple(int(m) for _v, m in hermite_blocks)
        return vals, mult
    nodes = []
    if x is not None:
        nodes.append(str(x))
    if y is not None and kind in _NAMED_NEEDS_Y:
        nodes.append(str(y))
    return tuple(nodes), _mults(hermite_blocks)


def _mults(blocks: Any) -> tuple[int, ...]:
    if not blocks:
        return ()
    try:
        return tuple(int(m) for _v, m in blocks)
    except Exception:
        return ()


def _node_strs(nodes: Any) -> tuple[str, ...]:
    if not nodes:
        return ()
    out: list[str] = []
    try:
        for item in nodes:
            if isinstance(item, (tuple, list)) and item:
                out.append("None" if item[0] is None else str(item[0]))
            else:
                out.append("None" if item is None else str(item))
    except TypeError:
        return ()
    return tuple(out)


def _reconstruct_lhs(
    kind: str,
    F: sympy.Expr,
    z: sympy.Expr,
    x: Optional[sympy.Expr],
    y: Optional[sympy.Expr],
    newton_nodes: Optional[list[sympy.Expr]],
    hermite_blocks: Optional[list[tuple[sympy.Expr, int]]],
) -> tuple[Optional[sympy.Expr], str, list[str]]:
    if kind == KIND_NEWTON_STEP:
        val, err = _call(newton_table, F, z, list(newton_nodes or []))
        return val, err or "", [BACKEND_NEWTON_TABLE]
    if kind == KIND_FXX:
        via_h, err_h = _call(hermite_dd, F, z, [(x, 2)])
        if err_h:
            return None, err_h, [BACKEND_HERMITE]
        via_d, err_d = _call(repeated_diagonal, F, z, x)
        if err_d:
            return via_h, "", [BACKEND_HERMITE, BACKEND_REPEATED]
        if via_h is not None and via_d is not None and not _same(via_h, via_d):
            # Both constructors claim to be F[x,x]; disagreement is not a claim.
            return via_h, "definition_recurrence_disagree", [
                BACKEND_HERMITE, BACKEND_REPEATED,
            ]
        return via_h, "", [BACKEND_HERMITE, BACKEND_REPEATED]
    val, err = _call(hermite_dd, F, z, list(hermite_blocks or []))
    return val, err or "", [BACKEND_HERMITE]


def _definitional_rhs(
    kind: str,
    F: sympy.Expr,
    z: sympy.Expr,
    x: Optional[sympy.Expr],
    y: Optional[sympy.Expr],
    newton_nodes: Optional[list[sympy.Expr]],
    hermite_blocks: Optional[list[tuple[sympy.Expr, int]]],
) -> tuple[Optional[sympy.Expr], str, list[str]]:
    used: list[str] = []
    if kind == KIND_FXX:
        val, err = _call(repeated_diagonal, F, z, x)
        return val, err or "", [BACKEND_REPEATED]
    if kind == KIND_FXXX:
        try:
            val = F.diff(z, 2).xreplace({z: x}) / sympy.factorial(2)
        except Exception as exc:
            return None, f"constructor_failed:{type(exc).__name__}", used
        return val, "", used
    if kind == KIND_FXXY:
        fxx, err_xx = _call(repeated_diagonal, F, z, x)
        fxy, err_xy = _call(newton_first, F, z, x, y)
        used = [BACKEND_REPEATED, BACKEND_NEWTON_FIRST]
        if err_xx:
            return None, err_xx, used
        if err_xy:
            return None, err_xy, used
        try:
            return (fxx - fxy) / (x - y), "", used
        except Exception as exc:
            return None, f"constructor_failed:{type(exc).__name__}", used
    if kind == KIND_FXYY:
        fxy, err_xy = _call(newton_first, F, z, x, y)
        fyy, err_yy = _call(repeated_diagonal, F, z, y)
        used = [BACKEND_NEWTON_FIRST, BACKEND_REPEATED]
        if err_xy:
            return None, err_xy, used
        if err_yy:
            return None, err_yy, used
        try:
            return (fxy - fyy) / (x - y), "", used
        except Exception as ext:
            return None, f"constructor_failed:{type(ext).__name__}", used
    if kind == KIND_NEWTON_STEP:
        seq = list(newton_nodes or [])
        if len(seq) < 2:
            return None, "missing_nodes", [BACKEND_NEWTON_TABLE]
        left, err_l = _call(newton_table, F, z, seq[1:])
        right, err_r = _call(newton_table, F, z, seq[:-1])
        used = [BACKEND_NEWTON_TABLE]
        if err_l:
            return None, err_l, used
        if err_r:
            return None, err_r, used
        try:
            return (left - right) / (seq[-1] - seq[0]), "", used
        except Exception as exc:
            return None, f"constructor_failed:{type(exc).__name__}", used
    if kind == KIND_HERMITE_STEP:
        return _hermite_step_rhs(F, z, list(hermite_blocks or []))
    return None, "unknown_kind", used


def _hermite_step_rhs(
    F: sympy.Expr,
    z: sympy.Expr,
    blocks: list[tuple[sympy.Expr, int]],
) -> tuple[Optional[sympy.Expr], str, list[str]]:
    seq: list[sympy.Expr] = []
    for value, multiplicity in blocks:
        seq.extend([value] * int(multiplicity))
    if not seq:
        return None, "missing_multiplicities", [BACKEND_HERMITE]
    used = [BACKEND_HERMITE]
    if all(s == seq[0] for s in seq):
        order = len(seq) - 1
        try:
            val = F.diff(z, order).xreplace({z: seq[0]}) / sympy.factorial(order)
        except Exception as exc:
            return None, f"constructor_failed:{type(exc).__name__}", used
        return val, "", used
    if seq[0] == seq[-1]:
        return None, "hermite_ill_posed", used
    left, err_l = _call(hermite_dd, F, z, _runs(seq[1:]))
    right, err_r = _call(hermite_dd, F, z, _runs(seq[:-1]))
    if err_l:
        return None, err_l, used
    if err_r:
        return None, err_r, used
    try:
        return (left - right) / (seq[-1] - seq[0]), "", used
    except Exception as exc:
        return None, f"constructor_failed:{type(exc).__name__}", used


def _runs(seq: Sequence[sympy.Expr]) -> list[tuple[sympy.Expr, int]]:
    if not seq:
        return []
    out: list[tuple[sympy.Expr, int]] = []
    cur = seq[0]
    n = 1
    for v in seq[1:]:
        if v == cur:
            n += 1
        else:
            out.append((cur, n))
            cur = v
            n = 1
    out.append((cur, n))
    return out


def _call(fn: Any, *args: Any) -> tuple[Optional[sympy.Expr], str]:
    try:
        return fn(*args), ""
    except HermiteDDError:
        return None, "hermite_ill_posed"
    except Exception as exc:
        return None, f"constructor_failed:{type(exc).__name__}"


def _require_newton_nodes(
    nodes: Any,
) -> tuple[Optional[list[sympy.Expr]], str]:
    if nodes is None:
        return None, "missing_nodes"
    try:
        seq = list(nodes)
    except TypeError:
        return None, "missing_nodes"
    if len(seq) < 2:
        return None, "missing_nodes"
    out: list[sympy.Expr] = []
    for item in seq:
        if isinstance(item, (tuple, list)):
            return None, "missing_nodes"
        expr = _as_expr(item)
        if expr is None:
            return None, "missing_nodes"
        out.append(expr)
    return out, ""


def _require_hermite_blocks(
    nodes: Any,
) -> tuple[Optional[list[tuple[sympy.Expr, int]]], str]:
    if nodes is None:
        return None, "missing_multiplicities"
    try:
        seq = list(nodes)
    except TypeError:
        return None, "missing_multiplicities"
    if not seq:
        return None, "missing_multiplicities"
    out: list[tuple[sympy.Expr, int]] = []
    for item in seq:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            return None, "missing_multiplicities"
        value, raw_m = item
        expr = _as_expr(value)
        mult = _as_multiplicity(raw_m)
        if expr is None:
            return None, "missing_nodes"
        if mult is None:
            return None, "missing_multiplicities"
        out.append((expr, mult))
    return out, ""


def _as_multiplicity(m: Any) -> Optional[int]:
    if isinstance(m, bool):
        return None
    if isinstance(m, int):
        return m if m >= 1 else None
    if isinstance(m, sympy.Integer):
        mi = int(m)
        if mi != m or mi < 1:
            return None
        return mi
    return None


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    return None


def _too_large(*exprs: Any) -> bool:
    for expr in exprs:
        if expr is None:
            continue
        try:
            n = int(sympy.count_ops(expr))
        except Exception:
            return True
        if n > _OPS_LIMIT:
            return True
    return False


def _coincident(a: Any, b: Any) -> bool:
    if a is None or b is None:
        return False
    if a == b:
        return True
    try:
        return sympy.expand(a - b) == 0
    except Exception:
        return False


def _indeterminate(expr: sympy.Expr) -> bool:
    if expr is None:
        return True
    try:
        if expr.has(sympy.nan, sympy.zoo):
            return True
    except Exception:
        return True
    return expr in (sympy.nan, sympy.zoo)


def _same(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        diff = a - b
    except Exception:
        return False
    for fn in (sympy.expand, sympy.cancel, sympy.together, sympy.simplify):
        try:
            if fn(diff) == 0:
                return True
        except Exception:
            continue
    return False


def _verdict_pair(
    a: Optional[sympy.Expr],
    b: Optional[sympy.Expr],
) -> tuple[str, str, Optional[str]]:
    if a is None or b is None:
        return UNKNOWN, "unparseable_side", None
    ind_a = _indeterminate(a)
    ind_b = _indeterminate(b)
    residual = None
    try:
        residual = str(a - b)
    except Exception:
        residual = None
    if ind_a or ind_b:
        if ind_a and ind_b:
            return UNKNOWN, "indeterminate", residual
        return NONZERO, "indeterminate_mismatch", residual
    if _same(a, b):
        return ZERO, "identity", "0"
    return NONZERO, "mismatch", residual


def _block_label(blocks: Sequence[tuple[Any, int]]) -> str:
    parts: list[str] = []
    for value, m in blocks:
        parts.extend([str(value)] * int(m))
    if not parts:
        return ""
    return "F[" + ",".join(parts) + "]"


def _relation_for(kind: str) -> str:
    if kind == KIND_NEWTON_STEP:
        return REL_DD
    if kind in {
        KIND_FXX, KIND_FXXY, KIND_FXYY, KIND_FXXX, KIND_HERMITE_STEP,
    }:
        return REL_HERMITE
    return REL_HERMITE


def _result(
    verdict: str,
    kind: str,
    note: str,
    *,
    F: Any = None,
    z: Any = None,
    x: Any = None,
    y: Any = None,
    claimed: Any = None,
    reconstruction: Any = None,
    rhs: Any = None,
    residual: Optional[str] = None,
    nodes: Sequence[str] = (),
    multiplicities: Sequence[int] = (),
    extra: Optional[dict[str, Any]] = None,
) -> RecurrenceResult:
    node_s = tuple(str(n) for n in nodes)
    mult_s = tuple(int(m) for m in multiplicities)
    lhs_s = None if reconstruction is None else str(reconstruction)
    rhs_s = None if rhs is None else str(rhs)
    claimed_s = None if claimed is None else str(claimed)
    backend = BACKEND_NEWTON_TABLE if kind == KIND_NEWTON_STEP else BACKEND_HERMITE
    if kind == KIND_FXX:
        backend = BACKEND_HERMITE
    formula = FORMULAS.get(kind, "")
    relation = _relation_for(kind)
    provenance: dict[str, Any] = {
        "constructor": backend,
        "kind": kind,
        "relation": relation,
        "formula": formula,
        "F": None if F is None else str(F),
        "z": None if z is None else str(z),
        "x": None if x is None else str(x),
        "y": None if y is None else str(y),
        "nodes": list(node_s),
        "multiplicities": list(mult_s),
        "claimed": claimed_s,
        "lhs": lhs_s,
        "rhs": rhs_s,
        "residual": residual,
        "explicit_F": _as_expr(F) is not None,
        "note": note,
        "verdict": verdict,
    }
    if extra:
        provenance.update(extra)
    return RecurrenceResult(
        verdict=verdict,
        kind=kind,
        relation=relation,
        note=note,
        formula=formula,
        lhs=lhs_s,
        rhs=rhs_s,
        residual=residual,
        nodes=node_s,
        multiplicities=mult_s,
        provenance=provenance,
    )
