"""Newton / Hermite compositional certificates.

Requires an explicit latent ``F`` and, for Hermite, explicit multiplicities.
Constructors are imported from ``research.representation_invention.dd``;
this module does not copy them and does not bind catalog members.

Verdicts are ZERO / NONZERO / UNKNOWN. Timeout, size-guard, missing data,
and ill-posed tableaux are UNKNOWN, never ZERO. Algebraic mismatch is
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
    repeated_diagonal,
)
from research.scalable_verification.api import NONZERO, UNKNOWN, ZERO

NEWTON_FIRST = "NEWTON_FIRST"
REPEATED = "REPEATED"
HERMITE = "HERMITE"

BACKEND_NEWTON = "research.representation_invention.dd.newton_first"
BACKEND_REPEATED = "research.representation_invention.dd.repeated_diagonal"
BACKEND_HERMITE = "research.representation_invention.dd.hermite_dd"

_FORMULA = {
    NEWTON_FIRST: "F[x,y]=(F(x)-F(y))/(x-y)",
    REPEATED: "F[x,x]=F'(x)",
    HERMITE: (
        "all-equal window of k+1 copies: F^{(k)}(a)/k!; "
        "distinct endpoints: Newton step"
    ),
}

# Fail closed on oversized latents (UNKNOWN, not ZERO).
_OPS_LIMIT = 200


@dataclass(frozen=True)
class Certificate:
    """One compositional DD/Hermite check."""

    verdict: str
    kind: str
    backend: str
    note: str = ""
    reconstruction: Optional[str] = None
    residual: Optional[str] = None
    nodes: tuple[str, ...] = ()
    multiplicities: tuple[int, ...] = ()
    provenance: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "kind": self.kind,
            "backend": self.backend,
            "note": self.note,
            "reconstruction": self.reconstruction,
            "residual": self.residual,
            "nodes": list(self.nodes),
            "multiplicities": list(self.multiplicities),
            "provenance": dict(self.provenance),
        }


def newton_first_ok(
    F: Any,
    z: Any,
    x: Any,
    y: Any,
    member: Any,
) -> Certificate:
    """Certificate that ``member`` equals ``F[x,y] = (F(x)-F(y))/(x-y)``.

    Coincident ``x=y`` is 0/0, not ``F'(x)``.
    """
    nodes = (x, y)
    mult = (1, 1)
    missing = _missing_expr(F=F, z=z, x=x, y=y, member=member)
    if missing:
        return _cert(
            UNKNOWN, NEWTON_FIRST, BACKEND_NEWTON, missing,
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    F, z, x, y, member = (_as_expr(F), _as_expr(z), _as_expr(x), _as_expr(y), _as_expr(member))
    nodes = (x, y)
    if _too_large(F, member):
        return _cert(
            UNKNOWN, NEWTON_FIRST, BACKEND_NEWTON, "size_guard",
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    try:
        recon = newton_first(F, z, x, y)
    except Exception as exc:
        return _cert(
            UNKNOWN, NEWTON_FIRST, BACKEND_NEWTON,
            f"constructor_failed:{type(exc).__name__}",
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    extra = {}
    if _coincident(x, y):
        extra["coincident_nodes"] = True
        extra["not_a_derivative"] = True
    return _compare(
        kind=NEWTON_FIRST,
        backend=BACKEND_NEWTON,
        F=F,
        z=z,
        member=member,
        reconstruction=recon,
        nodes=nodes,
        multiplicities=mult,
        extra=extra,
    )


def repeated_ok(F: Any, z: Any, x: Any, member: Any) -> Certificate:
    """Certificate that ``member`` equals ``F[x,x] = F'(x)``.

    Uses the ``repeated_diagonal`` definition. Cross-checks the Hermite
    tableau on explicit multiplicity 2. Does not substitute into
    ``newton_first``.
    """
    nodes = (x, x)
    mult = (2,)
    missing = _missing_expr(F=F, z=z, x=x, member=member)
    if missing:
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED, missing,
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    F, z, x, member = (_as_expr(F), _as_expr(z), _as_expr(x), _as_expr(member))
    nodes = (x, x)
    if _too_large(F, member):
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED, "size_guard",
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    try:
        recon = repeated_diagonal(F, z, x)
    except Exception as exc:
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED,
            f"constructor_failed:{type(exc).__name__}",
            F=F, z=z, member=member, nodes=nodes, multiplicities=mult,
        )
    extra: dict[str, Any] = {
        "explicit_multiplicities": True,
        "multiplicity": 2,
        "cross_check": BACKEND_HERMITE,
    }
    try:
        via_h = hermite_dd(F, z, [(x, 2)])
    except HermiteDDError:
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED, "hermite_ill_posed",
            F=F, z=z, member=member, reconstruction=recon,
            nodes=nodes, multiplicities=mult, extra=extra,
        )
    except Exception as exc:
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED,
            f"hermite_cross_check_failed:{type(exc).__name__}",
            F=F, z=z, member=member, reconstruction=recon,
            nodes=nodes, multiplicities=mult, extra=extra,
        )
    if not _same(recon, via_h):
        extra["definition_recurrence_disagree"] = True
        extra["hermite_reconstruction"] = str(via_h)
        return _cert(
            UNKNOWN, REPEATED, BACKEND_REPEATED, "definition_recurrence_disagree",
            F=F, z=z, member=member, reconstruction=recon,
            nodes=nodes, multiplicities=mult, extra=extra,
        )
    extra["hermite_reconstruction"] = str(via_h)
    return _compare(
        kind=REPEATED,
        backend=BACKEND_REPEATED,
        F=F,
        z=z,
        member=member,
        reconstruction=recon,
        nodes=nodes,
        multiplicities=mult,
        extra=extra,
    )


def hermite_ok(
    F: Any,
    z: Any,
    nodes: Sequence[Any],
    member: Any,
) -> Certificate:
    """Certificate that ``member`` equals the Hermite tableau on ``nodes``.

    ``nodes`` must be ``[(value, multiplicity), ...]`` with integer
    multiplicity ``>= 1``. Bare node lists without multiplicities are
    UNKNOWN. Ill-posed mixed endpoints are UNKNOWN (not guessed).
    """
    parsed, err = _require_multiplicity_blocks(nodes)
    values = tuple(v for v, _m in parsed) if parsed else ()
    mult = tuple(m for _v, m in parsed) if parsed else ()
    if err:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, err,
            F=F, z=z, member=member, nodes=values, multiplicities=mult,
            extra={"explicit_multiplicities": False},
        )
    missing = _missing_expr(F=F, z=z, member=member)
    if missing:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, missing,
            F=F, z=z, member=member, nodes=values, multiplicities=mult,
        )
    F, z, member = (_as_expr(F), _as_expr(z), _as_expr(member))
    if _too_large(F, member):
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, "size_guard",
            F=F, z=z, member=member, nodes=values, multiplicities=mult,
        )
    extra = {
        "explicit_multiplicities": True,
        "claimed": _block_label(parsed),
        "blocks": [[str(v), int(m)] for v, m in parsed],
    }
    try:
        recon = hermite_dd(F, z, parsed)
    except HermiteDDError:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, "hermite_ill_posed",
            F=F, z=z, member=member, nodes=values, multiplicities=mult,
            extra=extra,
        )
    except Exception as exc:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE,
            f"constructor_failed:{type(exc).__name__}",
            F=F, z=z, member=member, nodes=values, multiplicities=mult,
            extra=extra,
        )
    return _compare(
        kind=HERMITE,
        backend=BACKEND_HERMITE,
        F=F,
        z=z,
        member=member,
        reconstruction=recon,
        nodes=values,
        multiplicities=mult,
        extra=extra,
    )


def hermite_xxy_ok(F: Any, z: Any, x: Any, y: Any, member: Any) -> Certificate:
    """``F[x,x,y]`` via ``hermite_dd`` with multiplicities ``(2, 1)``."""
    if x is None or y is None:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, "missing_nodes",
            F=F, z=z, member=member, nodes=(x, y), multiplicities=(2, 1),
        )
    return hermite_ok(F, z, [(x, 2), (y, 1)], member)


def hermite_xyy_ok(F: Any, z: Any, x: Any, y: Any, member: Any) -> Certificate:
    """``F[x,y,y]`` via ``hermite_dd`` with multiplicities ``(1, 2)``."""
    if x is None or y is None:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, "missing_nodes",
            F=F, z=z, member=member, nodes=(x, y), multiplicities=(1, 2),
        )
    return hermite_ok(F, z, [(x, 1), (y, 2)], member)


def hermite_xxx_ok(F: Any, z: Any, x: Any, member: Any) -> Certificate:
    """``F[x,x,x] = F''(x)/2`` via ``hermite_dd`` with multiplicity ``3``."""
    if x is None:
        return _cert(
            UNKNOWN, HERMITE, BACKEND_HERMITE, "missing_nodes",
            F=F, z=z, member=member, nodes=(x,), multiplicities=(3,),
        )
    return hermite_ok(F, z, [(x, 3)], member)


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    return None


def _missing_expr(**kwargs: Any) -> Optional[str]:
    for name, value in kwargs.items():
        if _as_expr(value) is None:
            return f"missing_{name}"
    return None


def _require_multiplicity_blocks(
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


def _block_label(blocks: Sequence[tuple[sympy.Expr, int]]) -> str:
    parts: list[str] = []
    for value, m in blocks:
        parts.extend([str(value)] * int(m))
    return "F[" + ",".join(parts) + "]"


def _compare(
    *,
    kind: str,
    backend: str,
    F: Any,
    z: Any,
    member: Any,
    reconstruction: sympy.Expr,
    nodes: Sequence[Any],
    multiplicities: Sequence[int],
    extra: Optional[dict[str, Any]] = None,
) -> Certificate:
    mem = _as_expr(member)
    if mem is None or reconstruction is None:
        return _cert(
            UNKNOWN, kind, backend, "unparseable_side",
            F=F, z=z, member=member, reconstruction=reconstruction,
            nodes=nodes, multiplicities=multiplicities, extra=extra,
        )
    ind_m = _indeterminate(mem)
    ind_r = _indeterminate(reconstruction)
    if ind_m or ind_r:
        # 0/0 is not an identity. Finite member vs nan reconstruction is NONZERO.
        if ind_m and ind_r:
            verdict, note = UNKNOWN, "indeterminate"
        else:
            verdict, note = NONZERO, "indeterminate_mismatch"
        residual = None
        try:
            residual = str(mem - reconstruction)
        except Exception:
            residual = None
        return _cert(
            verdict, kind, backend, note,
            F=F, z=z, member=mem, reconstruction=reconstruction,
            residual=residual, nodes=nodes, multiplicities=multiplicities,
            extra=extra,
        )
    try:
        residual_expr = mem - reconstruction
    except Exception as exc:
        return _cert(
            UNKNOWN, kind, backend, f"residual_failed:{type(exc).__name__}",
            F=F, z=z, member=mem, reconstruction=reconstruction,
            nodes=nodes, multiplicities=multiplicities, extra=extra,
        )
    if _same(mem, reconstruction):
        return _cert(
            ZERO, kind, backend, "identity",
            F=F, z=z, member=mem, reconstruction=reconstruction,
            residual="0", nodes=nodes, multiplicities=multiplicities,
            extra=extra,
        )
    return _cert(
        NONZERO, kind, backend, "mismatch",
        F=F, z=z, member=mem, reconstruction=reconstruction,
        residual=str(residual_expr), nodes=nodes, multiplicities=multiplicities,
        extra=extra,
    )


def _cert(
    verdict: str,
    kind: str,
    backend: str,
    note: str,
    *,
    F: Any = None,
    z: Any = None,
    member: Any = None,
    reconstruction: Any = None,
    residual: Optional[str] = None,
    nodes: Sequence[Any] = (),
    multiplicities: Sequence[int] = (),
    extra: Optional[dict[str, Any]] = None,
) -> Certificate:
    node_s = tuple("None" if n is None else str(n) for n in nodes)
    mult_s = tuple(int(m) for m in multiplicities)
    recon_s = None if reconstruction is None else str(reconstruction)
    mem_s = None if member is None else str(member)
    provenance: dict[str, Any] = {
        "constructor": backend,
        "kind": kind,
        "formula": _FORMULA.get(kind, ""),
        "F": None if F is None else str(F),
        "z": None if z is None else str(z),
        "nodes": list(node_s),
        "multiplicities": list(mult_s),
        "member": mem_s,
        "reconstruction": recon_s,
        "residual": residual,
        "explicit_F": _as_expr(F) is not None,
        "explicit_multiplicities": len(mult_s) > 0,
        "note": note,
        "verdict": verdict,
    }
    if extra:
        provenance.update(extra)
    return Certificate(
        verdict=verdict,
        kind=kind,
        backend=backend,
        note=note,
        reconstruction=recon_s,
        residual=residual,
        nodes=node_s,
        multiplicities=mult_s,
        provenance=provenance,
    )
