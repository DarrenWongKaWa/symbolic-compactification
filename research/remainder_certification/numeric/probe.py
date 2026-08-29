"""High-precision remainder / t^{N+1} scaling as t -> 0.

Not a verifier. Status is agree / disagree / undecided only.
Never returns ZERO or CERTIFIED. Disagreement is EXACT_INVESTIGATION
for an exact path; it does not mint NONANALYTIC. No LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import mpmath as mp
import sympy

AGREE = "agree"
DISAGREE = "disagree"
UNDECIDED = "undecided"
EXACT_INVESTIGATION = "EXACT_INVESTIGATION"

ALLOWED_STATUSES = frozenset({AGREE, DISAGREE, UNDECIDED})
FORBIDDEN_VERDICTS = frozenset(
    {"ZERO", "CERTIFIED", "NONANALYTIC", "NONZERO", "LEVEL_C"}
)

DPS = 80
OPS_CAP = 2000
CHAR_CAP = 20000
N_MAX = 8
MIN_TRAJECTORIES = 3
EPS_POWERS = (4, 6, 8, 10)
AGREE_DRIFT = mp.mpf("1e-3")
DISAGREE_GROWTH = mp.mpf("10")
ORDER_AGREE = mp.mpf("0.5")
ORDER_DISAGREE = mp.mpf("0.25")
TINY_R = mp.mpf("1e-40")
DIRECTIONS = (sympy.Integer(1), sympy.Integer(-1), sympy.I)
SPECTATOR_VALUES = (
    sympy.Integer(2),
    sympy.Integer(-3),
    sympy.Rational(1, 2),
    sympy.Rational(5, 3),
    sympy.Integer(7),
)
_NOTE = (
    "numeric remainder scaling only; never ZERO; never CERTIFIED; "
    "disagreement is investigation only, not NONANALYTIC"
)
_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)
_PARSE_LOCAL: dict[str, Any] = {
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "sinh": sympy.sinh,
    "cosh": sympy.cosh,
    "tanh": sympy.tanh,
    "sqrt": sympy.sqrt,
    "gamma": sympy.gamma,
    "loggamma": sympy.loggamma,
    "polygamma": sympy.polygamma,
    "PolyGamma": sympy.polygamma,
    "digamma": sympy.digamma,
    "psi": sympy.digamma,
    "pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "oo": sympy.oo,
    "Integer": sympy.Integer,
    "Rational": sympy.Rational,
}
if hasattr(sympy, "trigamma"):
    _PARSE_LOCAL["trigamma"] = sympy.trigamma
_NAMED = {
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "sinh": sympy.sinh,
    "cosh": sympy.cosh,
    "tanh": sympy.tanh,
    "sqrt": sympy.sqrt,
    "gamma": sympy.gamma,
    "loggamma": sympy.loggamma,
    "digamma": sympy.digamma,
    "psi": sympy.digamma,
    "polygamma": lambda z: sympy.polygamma(0, z),
}
_POLE_FUNCS = (
    sympy.log,
    sympy.gamma,
    sympy.polygamma,
    sympy.digamma,
    sympy.sqrt,
    sympy.tan,
    sympy.cot,
    sympy.sec,
    sympy.csc,
    sympy.zeta,
)


@dataclass(frozen=True)
class NumericProbeResult:
    """Diagnostic record. ``status`` is never ZERO or CERTIFIED."""

    status: str
    investigation: str = ""
    n_valid: int = 0
    n_agree: int = 0
    n_disagree: int = 0
    median_scaled: Optional[str] = None
    observed_order: Optional[str] = None
    expansion_order: Optional[int] = None
    note: str = _NOTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "investigation": self.investigation,
            "n_valid": self.n_valid,
            "n_agree": self.n_agree,
            "n_disagree": self.n_disagree,
            "median_scaled": self.median_scaled,
            "observed_order": self.observed_order,
            "expansion_order": self.expansion_order,
            "note": self.note,
        }


def numeric_probe(
    f: Any,
    z0: Any = None,
    c: Any = None,
    n: Any = None,
    *,
    t: Any = None,
    domain_conditions: Any = None,
    assignments: Any = None,
) -> str:
    """Check that remainder after order ``n`` scales as t^{n+1} as t -> 0.

    Returns ``agree``, ``disagree``, or ``undecided``. Never ``ZERO``
    or ``CERTIFIED``. Disagreement does not mint ``NONANALYTIC``.
    """
    try:
        status = probe_report(
            f,
            z0,
            c,
            n,
            t=t,
            domain_conditions=domain_conditions,
            assignments=assignments,
        ).status
    except Exception:
        return UNDECIDED
    if status not in ALLOWED_STATUSES or status in FORBIDDEN_VERDICTS:
        return UNDECIDED
    return status


def probe_report(
    f: Any,
    z0: Any = None,
    c: Any = None,
    n: Any = None,
    *,
    t: Any = None,
    domain_conditions: Any = None,
    assignments: Any = None,
) -> NumericProbeResult:
    """Full scaling record. ``investigation`` may be EXACT_INVESTIGATION."""
    try:
        result = _probe_report(
            f,
            z0,
            c,
            n,
            t=t,
            domain_conditions=domain_conditions,
            assignments=assignments,
        )
    except Exception:
        return _undecided("exception")
    if result.status not in ALLOWED_STATUSES or result.status in FORBIDDEN_VERDICTS:
        return _undecided("forbidden_status")
    if result.investigation in FORBIDDEN_VERDICTS:
        return _undecided("forbidden_investigation")
    return result


def _probe_report(
    f: Any,
    z0: Any,
    c: Any,
    n: Any,
    *,
    t: Any,
    domain_conditions: Any,
    assignments: Any,
) -> NumericProbeResult:
    parsed = _as_univariate(f)
    if parsed is None:
        return _undecided("unparsed")
    f_z, z = parsed
    if _too_large(f_z):
        return _undecided("ops_cap")
    z0_e = _as_expr(z0)
    c_e = _as_expr(c) if c is not None else sympy.Integer(1)
    n_i = _as_int(n)
    if z0_e is None or c_e is None or n_i is None:
        return _undecided("bad_parameters")
    if n_i < 0 or n_i > N_MAX:
        return _undecided("order_cap")
    t_sym = _bind_t(t, f_z, z0_e, c_e, z)
    z0_e, c_e = _unify_pair(z0_e, c_e)
    conditions = _conditions(domain_conditions)
    spectators = _spectators(z0_e, c_e, z, t_sym)
    rows = _assignment_rows(
        spectators,
        assignments,
        f_z,
        z,
        conditions,
    )
    if rows is None:
        return _undecided("no_assignments")
    with mp.workdps(DPS):
        return _run_samples(f_z, z, z0_e, c_e, n_i, rows)


def _run_samples(
    f_z: sympy.Expr,
    z: sympy.Expr,
    z0_e: sympy.Expr,
    c_e: sympy.Expr,
    n: int,
    rows: list[dict[sympy.Expr, sympy.Expr]],
) -> NumericProbeResult:
    labels: list[str] = []
    scaled_vals: list[Any] = []
    orders: list[Any] = []
    n_pole = 0
    for mapping in rows:
        z0_n = _eval_point(z0_e, mapping)
        c_n = _eval_point(c_e, mapping)
        if z0_n is None or c_n is None:
            continue
        z0_f = _nval(z0_n, {})
        c_f = _nval(c_n, {})
        if z0_f in (None, "nonfinite") or c_f in (None, "nonfinite"):
            continue
        coeffs = _taylor_coeffs(f_z, z, z0_n, n)
        if coeffs == "nonfinite":
            n_pole += 1
            labels.append(DISAGREE)
            continue
        if coeffs is None or len(coeffs) < n + 1:
            continue
        for direction in DIRECTIONS:
            lab, scaled, order = _trajectory(
                f_z, z, z0_f, c_f, coeffs[: n + 1], n, direction
            )
            if lab == UNDECIDED:
                continue
            labels.append(lab)
            if scaled is not None:
                scaled_vals.append(abs(scaled))
            if order is not None:
                orders.append(order)
    return _vote(labels, scaled_vals, orders, n, n_pole)


def _taylor_coeffs(
    f_z: sympy.Expr, z: sympy.Expr, z0_n: sympy.Expr, n: int
) -> Any:
    coeffs: list[Any] = []
    dk = f_z
    z0_f = _sym_float(z0_n)
    if z0_f is None:
        return None
    for k in range(n + 1):
        ck = _nval(dk, {z: z0_f})
        if ck == "nonfinite":
            return "nonfinite"
        if ck is None:
            return None
        coeffs.append(ck)
        if k == n:
            break
        try:
            dk = sympy.diff(dk, z)
        except Exception:
            return None
    return coeffs


def _trajectory(
    f_z: sympy.Expr,
    z: sympy.Expr,
    z0_f: Any,
    c_f: Any,
    coeffs: list[Any],
    n: int,
    direction: sympy.Expr,
) -> tuple[str, Optional[Any], Optional[Any]]:
    samples: list[Any] = []
    for power in EPS_POWERS:
        t_frac = direction * sympy.Rational(1, 10**power)
        t_f = _as_mpc(t_frac)
        if t_f in (None, "nonfinite"):
            continue
        fv = _eval_f(f_z, z, z0_f, c_f, t_f)
        pv = _poly_value(coeffs, c_f, t_f)
        if fv == "nonfinite" or pv == "nonfinite":
            samples.append("nonfinite")
            continue
        if fv is None or pv is None:
            continue
        rem = fv - pv
        if not (mp.isfinite(rem.real) and mp.isfinite(rem.imag)):
            samples.append("nonfinite")
            continue
        denom = t_f ** (n + 1)
        if denom == 0:
            continue
        scaled = rem / denom
        if not (mp.isfinite(scaled.real) and mp.isfinite(scaled.imag)):
            samples.append("nonfinite")
            continue
        samples.append({"t": t_f, "R": rem, "s": scaled})
    return _classify_trajectory(samples, n)


def _eval_f(
    f_z: sympy.Expr, z: sympy.Expr, z0_f: Any, c_f: Any, t_f: Any
) -> Any:
    arg = z0_f + c_f * t_f
    arg_s = _mpc_to_sym(arg)
    if arg_s is None:
        return None
    return _nval(f_z, {z: arg_s})


def _poly_value(coeffs: list[Any], c_f: Any, t_f: Any) -> Any:
    try:
        total = mp.mpc(0)
        ct = c_f * t_f
        pow_ct = mp.mpc(1)
        for k, ck in enumerate(coeffs):
            total += ck * pow_ct / mp.factorial(k)
            pow_ct *= ct
        if not (mp.isfinite(total.real) and mp.isfinite(total.imag)):
            return "nonfinite"
        return total
    except Exception:
        return None


def _classify_trajectory(
    samples: list[Any], n: int
) -> tuple[str, Optional[Any], Optional[Any]]:
    if not samples:
        return UNDECIDED, None, None
    if samples[-1] == "nonfinite":
        return DISAGREE, None, None
    finite = [item for item in samples if isinstance(item, dict)]
    if not finite:
        return DISAGREE, None, None
    t_vals = [item["t"] for item in finite]
    r_vals = [item["R"] for item in finite]
    s_vals = [item["s"] for item in finite]
    s_fine = s_vals[-1]
    s_coarse = s_vals[0]
    if all(abs(r) <= TINY_R for r in r_vals):
        return AGREE, s_fine, mp.inf
    order = _observed_order(t_vals, r_vals)
    growth = abs(s_fine) / max(abs(s_coarse), TINY_R)
    scale = max(mp.mpf("1"), abs(s_coarse), abs(s_fine))
    drift = abs(s_fine - s_coarse) / scale
    if growth >= DISAGREE_GROWTH:
        return DISAGREE, s_fine, order
    if order is not None:
        if order >= n + ORDER_AGREE:
            return AGREE, s_fine, order
        if order < n + ORDER_DISAGREE:
            return DISAGREE, s_fine, order
    if drift <= AGREE_DRIFT:
        return AGREE, s_fine, order
    return UNDECIDED, s_fine, order


def _observed_order(t_vals: list[Any], r_vals: list[Any]) -> Optional[Any]:
    pairs = [
        (t, r)
        for t, r in zip(t_vals, r_vals)
        if abs(r) > TINY_R and abs(t) > 0
    ]
    if len(pairs) < 2:
        return None
    t1, r1 = pairs[0]
    t2, r2 = pairs[-1]
    try:
        ratio_r = abs(r2) / abs(r1)
        ratio_t = abs(t2) / abs(t1)
        if ratio_r <= 0 or ratio_t <= 0 or ratio_t == 1:
            return None
        return mp.log(ratio_r) / mp.log(ratio_t)
    except Exception:
        return None


def _vote(
    labels: list[str],
    scaled_vals: list[Any],
    orders: list[Any],
    n: int,
    n_pole: int,
) -> NumericProbeResult:
    n_agree = sum(1 for lab in labels if lab == AGREE)
    n_disagree = sum(1 for lab in labels if lab == DISAGREE)
    n_valid = n_agree + n_disagree
    median_s = _err_str(_median(scaled_vals))
    median_o = _err_str(_median(orders))
    if n_pole > 0 and n_agree == 0:
        return NumericProbeResult(
            status=DISAGREE,
            investigation=EXACT_INVESTIGATION,
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_scaled=median_s,
            observed_order=median_o,
            expansion_order=n,
            note=_NOTE + "; expansion-point derivatives nonfinite",
        )
    if n_valid < MIN_TRAJECTORIES:
        return NumericProbeResult(
            status=UNDECIDED,
            investigation="",
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_scaled=median_s,
            observed_order=median_o,
            expansion_order=n,
            note=_NOTE + "; insufficient samples",
        )
    if n_disagree >= 2 and n_disagree >= n_agree:
        return NumericProbeResult(
            status=DISAGREE,
            investigation=EXACT_INVESTIGATION,
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_scaled=median_s,
            observed_order=median_o,
            expansion_order=n,
            note=_NOTE + "; exact path required",
        )
    if n_agree >= MIN_TRAJECTORIES and n_disagree == 0:
        return NumericProbeResult(
            status=AGREE,
            investigation="",
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_scaled=median_s,
            observed_order=median_o,
            expansion_order=n,
            note=_NOTE + "; agreement is not a certificate",
        )
    return NumericProbeResult(
        status=UNDECIDED,
        investigation="",
        n_valid=n_valid,
        n_agree=n_agree,
        n_disagree=n_disagree,
        median_scaled=median_s,
        observed_order=median_o,
        expansion_order=n,
        note=_NOTE + "; mixed samples",
    )


def _undecided(reason: str) -> NumericProbeResult:
    return NumericProbeResult(
        status=UNDECIDED,
        investigation="",
        note=f"undecided ({reason}); {_NOTE}",
    )


def _as_univariate(f: Any) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    if f is None:
        return None
    if isinstance(f, str):
        key = f.strip()
        if not key or len(key) > CHAR_CAP:
            return None
        named = _NAMED.get(key.lower())
        if named is not None:
            z = sympy.Dummy("z")
            try:
                return named(z), z
            except Exception:
                return None
        expr = _as_expr(key)
        if expr is None:
            return None
        return _univariate_from_expr(expr)
    if isinstance(f, sympy.FunctionClass):
        z = sympy.Dummy("z")
        try:
            if f is sympy.polygamma:
                return sympy.polygamma(0, z), z
            return f(z), z
        except Exception:
            return None
    expr = _as_expr(f)
    if expr is None:
        return None
    return _univariate_from_expr(expr)


def _univariate_from_expr(
    expr: sympy.Expr,
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    if getattr(expr, "is_Relational", False):
        return None
    if expr.func in (sympy.polygamma, sympy.digamma) and expr.args:
        arg = expr.args[-1]
        if getattr(arg, "is_symbol", False):
            return expr, arg
    free = list(getattr(expr, "free_symbols", set()) or [])
    if len(free) == 1:
        return expr, free[0]
    if not free:
        z = sympy.Dummy("z")
        return expr, z
    for s in sorted(free, key=str):
        if str(s) == "z":
            return expr, s
    return None


def _as_expr(obj: Any) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, bool):
        return None
    if isinstance(obj, int):
        return sympy.Integer(obj)
    if isinstance(obj, float):
        if obj != obj or obj in (float("inf"), float("-inf")):
            return None
        return sympy.Float(obj, DPS)
    if isinstance(obj, complex):
        return sympy.Integer(obj.real) + sympy.I * sympy.Integer(obj.imag) if (
            obj.real == int(obj.real) and obj.imag == int(obj.imag)
        ) else sympy.Float(obj.real, DPS) + sympy.I * sympy.Float(obj.imag, DPS)
    if isinstance(obj, sympy.Expr):
        if getattr(obj, "is_Relational", False):
            return None
        return obj
    if isinstance(obj, str):
        if not obj.strip() or len(obj) > CHAR_CAP:
            return None
        try:
            got = sympy.sympify(obj, locals=_PARSE_LOCAL)
        except (sympy.SympifyError, TypeError, ValueError, SyntaxError):
            return None
        except Exception:
            return None
        if isinstance(got, sympy.Expr) and not getattr(got, "is_Relational", False):
            return got
        return None
    try:
        got = sympy.sympify(obj)
    except Exception:
        return None
    if isinstance(got, sympy.Expr) and not getattr(got, "is_Relational", False):
        return got
    return None


def _as_int(n: Any) -> Optional[int]:
    if n is None or isinstance(n, bool):
        return None
    if isinstance(n, int):
        return n
    try:
        if isinstance(n, sympy.Integer):
            return int(n)
    except Exception:
        return None
    try:
        got = int(n)
    except Exception:
        return None
    try:
        if got != n:
            return None
    except Exception:
        return None
    return got


def _conditions(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        text = raw.strip()
        return [text] if text else []
    try:
        return [str(item).strip() for item in raw if str(item).strip()]
    except Exception:
        return []


def _bind_t(
    raw: Any,
    *exprs: sympy.Expr,
) -> sympy.Expr:
    if raw is None:
        return sympy.Dummy("t")
    if isinstance(raw, sympy.Expr) and raw.is_symbol:
        return raw
    if isinstance(raw, str) and raw.strip():
        for e in exprs:
            for s in getattr(e, "free_symbols", set()) or []:
                if str(s) == raw:
                    return s
        try:
            got = sympy.sympify(raw)
        except Exception:
            return sympy.Dummy("t")
        if isinstance(got, sympy.Expr) and got.is_symbol:
            return got
    return sympy.Dummy("t")


def _unify_pair(a: sympy.Expr, b: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    names: dict[str, sympy.Symbol] = {}
    for s in getattr(a, "free_symbols", set()) or []:
        names[str(s)] = s
    reps = {}
    for s in getattr(b, "free_symbols", set()) or []:
        key = str(s)
        if key in names and s is not names[key]:
            reps[s] = names[key]
        elif key not in names:
            names[key] = s
    if reps:
        b = b.xreplace(reps)
    return a, b


def _spectators(
    z0: sympy.Expr,
    c: sympy.Expr,
    z: sympy.Expr,
    t_sym: sympy.Expr,
) -> list[sympy.Expr]:
    free = set(getattr(z0, "free_symbols", set()) or [])
    free |= set(getattr(c, "free_symbols", set()) or [])
    free.discard(z)
    free.discard(t_sym)
    return sorted(free, key=str)


def _looks_entire(expr: sympy.Expr, z: sympy.Expr) -> bool:
    try:
        if not isinstance(expr, sympy.Expr):
            return False
        if expr.is_number or expr.is_symbol:
            return True
        if expr.has(*_POLE_FUNCS):
            return False
        den = sympy.denom(sympy.together(expr))
        if z in (getattr(den, "free_symbols", set()) or set()):
            return False
        if expr.is_polynomial(z):
            return True
    except Exception:
        return False
    allowed = (
        sympy.exp,
        sympy.sin,
        sympy.cos,
        sympy.sinh,
        sympy.cosh,
        sympy.tanh,
        sympy.erf,
    )
    try:
        for fn in expr.atoms(sympy.Function):
            func = getattr(fn, "func", None)
            if func not in allowed:
                return False
            for arg in fn.args:
                if not _looks_entire(arg, z):
                    return False
    except Exception:
        return False
    return True


def _has_nonpos_poles(expr: sympy.Expr) -> bool:
    try:
        return bool(expr.has(sympy.polygamma, sympy.gamma, sympy.digamma))
    except Exception:
        return False


def _is_nonpositive_integer(val: sympy.Expr) -> bool:
    try:
        if val.free_symbols:
            return False
        n = int(val)
        return val == n and n <= 0
    except Exception:
        return False


def _assignment_rows(
    spectators: list[sympy.Expr],
    assignments: Any,
    f_z: sympy.Expr,
    z: sympy.Expr,
    conditions: list[str],
) -> Optional[list[dict[sympy.Expr, sympy.Expr]]]:
    explicit = _coerce_assignments(assignments, spectators)
    if explicit is not None:
        return explicit if explicit else None
    if not spectators:
        return [{}]
    entire = _looks_entire(f_z, z)
    if not entire and not conditions:
        return None
    lattice = list(SPECTATOR_VALUES)
    if _has_nonpos_poles(f_z):
        lattice = [v for v in lattice if not _is_nonpositive_integer(v)]
    if not lattice:
        return None
    n = max(len(lattice), MIN_TRAJECTORIES)
    rows: list[dict[sympy.Expr, sympy.Expr]] = []
    for i in range(n):
        mapping: dict[sympy.Expr, sympy.Expr] = {}
        for j, s in enumerate(spectators):
            mapping[s] = lattice[(i + 2 * j) % len(lattice)]
        rows.append(mapping)
    return rows


def _coerce_assignments(
    assignments: Any, spectators: list[sympy.Expr]
) -> Optional[list[dict[sympy.Expr, sympy.Expr]]]:
    if assignments is None:
        return None
    if isinstance(assignments, dict):
        items = [assignments]
    else:
        try:
            items = list(assignments)
        except Exception:
            return []
    names = {str(s): s for s in spectators}
    rows: list[dict[sympy.Expr, sympy.Expr]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        mapping: dict[sympy.Expr, sympy.Expr] = {}
        ok = True
        for key, val in item.items():
            if isinstance(key, sympy.Expr) and key.is_symbol:
                sym = names.get(str(key), key)
            elif isinstance(key, str) and key in names:
                sym = names[key]
            else:
                ok = False
                break
            expr = _as_expr(val)
            if expr is None:
                ok = False
                break
            mapping[sym] = expr
        if ok:
            rows.append(mapping)
    return rows


def _eval_point(
    point: sympy.Expr, mapping: dict[sympy.Expr, sympy.Expr]
) -> Optional[sympy.Expr]:
    try:
        if point in mapping:
            return mapping[point]
        got = point.xreplace(mapping)
    except Exception:
        return None
    try:
        if getattr(got, "free_symbols", set()):
            return None
    except Exception:
        return None
    return got


def _too_large(expr: sympy.Expr) -> bool:
    try:
        return int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    except Exception:
        return True


def _sym_float(val: sympy.Expr) -> Optional[sympy.Expr]:
    try:
        if getattr(val, "free_symbols", set()):
            return None
    except Exception:
        return None
    try:
        num = val.evalf(n=DPS, strict=False)
    except Exception:
        return None
    if _is_nonfinite_expr(num):
        return None
    return num


def _nval(expr: sympy.Expr, mapping: dict[sympy.Expr, sympy.Expr]) -> Any:
    try:
        sub = expr.xreplace(mapping) if mapping else expr
    except Exception:
        try:
            sub = expr.subs(mapping, simultaneous=True) if mapping else expr
        except Exception:
            return None
    try:
        leftover = set(getattr(sub, "free_symbols", set()) or [])
        if leftover:
            return None
    except Exception:
        return None
    if _is_nonfinite_expr(sub):
        return "nonfinite"
    try:
        num = sub.evalf(n=DPS, strict=False)
    except Exception:
        return None
    if _is_nonfinite_expr(num):
        return "nonfinite"
    return _as_mpc(num)


def _is_nonfinite_expr(expr: Any) -> bool:
    if expr is None:
        return False
    try:
        if expr in _NONFINITE:
            return True
    except Exception:
        pass
    try:
        if getattr(expr, "is_infinite", None) is True:
            return True
    except Exception:
        pass
    try:
        if expr.has(*_NONFINITE):
            return True
    except Exception:
        return True
    return False


def _as_mpc(num: Any) -> Any:
    if isinstance(num, mp.mpc):
        if mp.isfinite(num.real) and mp.isfinite(num.imag):
            return num
        return "nonfinite"
    if isinstance(num, mp.mpf):
        if mp.isfinite(num):
            return mp.mpc(num, 0)
        return "nonfinite"
    try:
        re, im = num.as_real_imag()
    except Exception:
        try:
            re, im = num, sympy.Integer(0)
        except Exception:
            return None
    try:
        re_n = re.evalf(n=DPS, strict=False)
        im_n = im.evalf(n=DPS, strict=False)
    except Exception:
        return None
    if _is_nonfinite_expr(re_n) or _is_nonfinite_expr(im_n):
        return "nonfinite"
    try:
        re_f = mp.mpf(re_n._mpf_) if isinstance(re_n, sympy.Float) else mp.mpf(str(re_n))
        im_f = mp.mpf(im_n._mpf_) if isinstance(im_n, sympy.Float) else mp.mpf(str(im_n))
    except Exception:
        return None
    if not (mp.isfinite(re_f) and mp.isfinite(im_f)):
        return "nonfinite"
    return mp.mpc(re_f, im_f)


def _mpc_to_sym(val: Any) -> Optional[sympy.Expr]:
    try:
        re = sympy.Float(str(val.real), DPS)
        im = sympy.Float(str(val.imag), DPS)
        if im == 0:
            return re
        return re + sympy.I * im
    except Exception:
        return None


def _median(vals: list[Any]) -> Optional[Any]:
    clean = [v for v in vals if v is not None]
    finite = []
    for v in clean:
        try:
            if v is mp.inf or v == mp.inf:
                continue
            if not mp.isfinite(v if not hasattr(v, "real") else abs(v)):
                continue
        except Exception:
            continue
        finite.append(v)
    if not finite:
        return None
    ordered = sorted(finite, key=lambda x: abs(x) if hasattr(x, "real") else x)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2


def _err_str(err: Any) -> Optional[str]:
    if err is None:
        return None
    try:
        return mp.nstr(err, 12)
    except Exception:
        return str(err)
