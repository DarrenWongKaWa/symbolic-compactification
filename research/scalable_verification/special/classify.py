"""Classify local polygamma identities already in SymPy.

Admitted identities:

- ``d/dz polygamma(n, z) = polygamma(n + 1, z)``
- Newton first DD of ``polygamma(0, ·)`` vs ``(psi(x) - psi(y))/(x - y)``

``psi`` is parsed as ``digamma``, which SymPy stores as ``polygamma(0, ·)``.

This is not a verifier and not a confluence engine. It does not invent
masters (no ``Phi_Gamma``, no L4–L7) and does not take Guo-scale limits.
"""
from __future__ import annotations

import re
from typing import Any, Optional

import sympy
from sympy.parsing.sympy_parser import parse_expr

SUPPORTED = "supported"
UNSUPPORTED = "unsupported"
UNKNOWN = "UNKNOWN"

# Local identities are tiny. Guo source is ~22k characters; do not parse it.
_MAX_CHARS = 4096
_MAX_OPS = 80

# Rejected names: not constructed, only detected so they cannot be "supported".
_UNSUPPORTED_NAME = re.compile(
    r"(?i)(?:\\Phi_\\Gamma|\bPhi[_\s-]*Gamma\b|\bPhiGamma\b|\bL[4-7]\b)"
)

_SF_NAMES = frozenset({
    "polygamma",
    "PolyGamma",
    "digamma",
    "trigamma",
    "psi",
    "gamma",
    "loggamma",
})
_SF_NAMES_LOWER = frozenset(s.lower() for s in _SF_NAMES)


def _diff_uneval(f: sympy.Expr, *vars: Any) -> sympy.Derivative:
    return sympy.Derivative(f, *vars)


_PARSE_LOCAL: dict[str, Any] = {
    "polygamma": sympy.polygamma,
    "PolyGamma": sympy.polygamma,
    "psi": sympy.digamma,
    "digamma": sympy.digamma,
    "gamma": sympy.gamma,
    "loggamma": sympy.loggamma,
    "Derivative": sympy.Derivative,
    "diff": _diff_uneval,
    "Eq": sympy.Eq,
    "pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "oo": sympy.oo,
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "factorial": sympy.factorial,
    "cot": sympy.cot,
}
if hasattr(sympy, "trigamma"):
    _PARSE_LOCAL["trigamma"] = sympy.trigamma


def classify_identity(expr_or_pair: Any) -> str:
    """Return ``supported``, ``unsupported``, or ``UNKNOWN``.

    ``expr_or_pair`` may be an ``Eq``, a ``(left, right)`` pair, a string
    containing ``=``, a two-key dict (``left``/``right`` or ``lhs``/``rhs``),
    or a two-term residual ``Derivative(...) - polygamma(...)``.
    """
    try:
        texts = _collect_texts(expr_or_pair)
        if any(len(t) > _MAX_CHARS for t in texts):
            return UNKNOWN
        if any(_UNSUPPORTED_NAME.search(t) for t in texts):
            return UNSUPPORTED
        pair = _as_pair(expr_or_pair)
        if pair is None:
            return UNKNOWN
        left, right = pair
        if _too_big(left) or _too_big(right):
            return UNKNOWN
        if _is_polygamma_derivative_identity(left, right):
            return SUPPORTED
        if _is_polygamma_newton_first_identity(left, right):
            return SUPPORTED
        if _has_special_fn(left) or _has_special_fn(right):
            return UNSUPPORTED
        return UNKNOWN
    except Exception:
        return UNKNOWN


def _collect_texts(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, (tuple, list)):
        out: list[str] = []
        for item in obj:
            if isinstance(item, str):
                out.append(item)
        return out
    if isinstance(obj, dict):
        out = []
        for key in ("left", "right", "lhs", "rhs"):
            val = obj.get(key)
            if isinstance(val, str):
                out.append(val)
        return out
    return []


def _as_pair(obj: Any) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    if obj is None:
        return None
    if isinstance(obj, sympy.Equality):
        return _rewrite(obj.lhs), _rewrite(obj.rhs)
    if isinstance(obj, dict):
        if "left" in obj and "right" in obj:
            return _coerce_pair(obj["left"], obj["right"])
        if "lhs" in obj and "rhs" in obj:
            return _coerce_pair(obj["lhs"], obj["rhs"])
        return None
    if isinstance(obj, (tuple, list)):
        if len(obj) != 2:
            return None
        return _coerce_pair(obj[0], obj[1])
    if isinstance(obj, str):
        split = _split_equality_string(obj)
        if split is not None:
            return _coerce_pair(split[0], split[1])
        expr = _coerce(obj)
        if expr is None:
            return None
        return _maybe_residual_pair(expr)
    if isinstance(obj, sympy.Expr):
        if isinstance(obj, sympy.Equality):
            return _rewrite(obj.lhs), _rewrite(obj.rhs)
        return _maybe_residual_pair(_rewrite(obj))
    return None


def _coerce_pair(a: Any, b: Any) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    left = _coerce(a)
    right = _coerce(b)
    if left is None or right is None:
        return None
    return left, right


def _coerce(obj: Any) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, sympy.Expr):
        return _rewrite(obj)
    if isinstance(obj, str):
        text = obj.strip()
        if not text or len(text) > _MAX_CHARS:
            return None
        return _parse(text)
    return None


def _parse(text: str) -> Optional[sympy.Expr]:
    try:
        expr = parse_expr(text, local_dict=dict(_PARSE_LOCAL))
    except Exception:
        return None
    if not isinstance(expr, sympy.Expr):
        return None
    return _rewrite(expr)


def _split_equality_string(s: str) -> Optional[tuple[str, str]]:
    depth = 0
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c in "([{":
            depth += 1
        elif c in ")]}":
            depth = max(0, depth - 1)
        elif depth == 0 and c == "=":
            if i + 1 < n and s[i + 1] == "=":
                left, right = s[:i], s[i + 2:]
            else:
                left, right = s[:i], s[i + 1:]
            left, right = left.strip(), right.strip()
            if left and right:
                return left, right
            return None
        i += 1
    return None


def _rewrite(expr: sympy.Expr) -> sympy.Expr:
    """Map ``psi``/``digamma``/``PolyGamma`` heads onto ``polygamma``."""
    repl: dict[sympy.Expr, sympy.Expr] = {}
    for f in expr.atoms(sympy.Function):
        name = getattr(f.func, "__name__", "") or str(f.func)
        if name in {"psi", "digamma"} and len(f.args) == 1:
            repl[f] = sympy.polygamma(0, f.args[0])
        elif name == "PolyGamma" and len(f.args) == 2:
            repl[f] = sympy.polygamma(f.args[0], f.args[1])
    if repl:
        return expr.xreplace(repl)
    return expr


def _too_big(expr: sympy.Expr) -> bool:
    try:
        return int(sympy.count_ops(expr)) > _MAX_OPS
    except Exception:
        return True


def _maybe_residual_pair(
    expr: sympy.Expr,
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    if expr.func != sympy.Add or len(expr.args) != 2:
        return None
    a, b = expr.args
    return a, -b


def _same_polygamma(a: sympy.Expr, b: sympy.Expr) -> bool:
    return (
        isinstance(a, sympy.polygamma)
        and isinstance(b, sympy.polygamma)
        and a == b
    )


def _eval_pg_d_dz(expr: sympy.Expr) -> Optional[sympy.Expr]:
    """Local rule: ``d/dz polygamma(n, z) -> polygamma(n + 1, z)``.

    Differentiates only with respect to the polygamma argument, once.
    No chain rule, no ``d/dn``, no higher order.
    """
    coeff: sympy.Expr = sympy.Integer(1)
    core = expr
    if isinstance(expr, sympy.Mul):
        ders = [a for a in expr.args if isinstance(a, sympy.Derivative)]
        if len(ders) != 1:
            return None
        rest = sympy.Mul(*(a for a in expr.args if a is not ders[0]))
        if rest not in (1, -1, sympy.Integer(1), sympy.Integer(-1)):
            return None
        coeff = rest
        core = ders[0]
    if not isinstance(core, sympy.Derivative):
        return None
    f = core.expr
    if not isinstance(f, sympy.polygamma) or len(f.args) != 2:
        return None
    n, arg = f.args
    counts = list(core.variable_count)
    if len(counts) != 1:
        return None
    var, cnt = counts[0]
    if cnt != 1 or var != arg:
        return None
    return coeff * sympy.polygamma(n + 1, arg)


def _is_polygamma_derivative_identity(a: sympy.Expr, b: sympy.Expr) -> bool:
    for left, right in ((a, b), (b, a)):
        ev = _eval_pg_d_dz(left)
        if ev is not None and ev == right:
            return True
        if ev is not None and _same_polygamma(ev, right):
            return True
    # SymPy ``diff`` already applies the same fdiff rule.
    if _same_polygamma(a, b):
        return True
    return False


def _two_term_diff(expr: sympy.Expr) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    e = sympy.expand(expr)
    if not isinstance(e, sympy.Add) or len(e.args) != 2:
        return None
    t0, t1 = e.args
    s0 = t0.could_extract_minus_sign()
    s1 = t1.could_extract_minus_sign()
    if s0 == s1:
        return None
    if s1:
        return t0, -t1
    return t1, -t0


def _newton_pg0_nodes(
    expr: sympy.Expr,
) -> Optional[tuple[sympy.Expr, sympy.Expr, int]]:
    """If ``expr`` is ``±(polygamma(0,u)-polygamma(0,v))/(u-v)``, return nodes."""
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
    if fa.args[0] != 0 or fb.args[0] != 0:
        return None
    xa, xb = fa.args[1], fb.args[1]
    if xa == u and xb == v:
        return u, v, 1
    if xa == v and xb == u:
        return u, v, -1
    return None


def _is_polygamma_newton_first_identity(a: sympy.Expr, b: sympy.Expr) -> bool:
    pa = _newton_pg0_nodes(a)
    pb = _newton_pg0_nodes(b)
    if pa is None or pb is None:
        return False
    u1, v1, s1 = pa
    u2, v2, s2 = pb
    # sign +1 is F[u, v] = F[v, u]; sign -1 is the flipped DD (F06).
    if s1 != 1 or s2 != 1:
        return False
    nodes1 = frozenset((u1, v1))
    nodes2 = frozenset((u2, v2))
    return nodes1 == nodes2 and len(nodes1) == 2


def _has_special_fn(expr: sympy.Expr) -> bool:
    if expr.atoms(sympy.polygamma):
        return True
    if expr.atoms(sympy.gamma) or expr.atoms(sympy.loggamma):
        return True
    for f in expr.atoms(sympy.Function):
        name = getattr(f.func, "__name__", "") or str(f.func)
        if name in _SF_NAMES or name.lower() in _SF_NAMES_LOWER:
            return True
        if isinstance(f, sympy.Derivative) and _has_special_fn(f.expr):
            return True
    for d in expr.atoms(sympy.Derivative):
        if _has_special_fn(d.expr):
            return True
    return False
