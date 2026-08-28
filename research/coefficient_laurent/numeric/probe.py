"""High-precision numeric samples of lim t->0 E_gen vs E_diag.

Not a verifier. Status is agree / disagree / undecided only.
Never returns ZERO. Strong disagreement is SUSPECT_NONZERO for
investigation; an exact path is still required. No LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import mpmath as mp
import sympy

AGREE = "agree"
DISAGREE = "disagree"
UNDECIDED = "undecided"
SUSPECT_NONZERO = "SUSPECT_NONZERO"

ALLOWED_STATUSES = frozenset({AGREE, DISAGREE, UNDECIDED})

DPS = 60
OPS_CAP = 2000
CHAR_CAP = 20000
MIN_TRAJECTORIES = 3
AGREE_ERR = mp.mpf("1e-16")
DISAGREE_ERR = mp.mpf("1e-4")
STRONG_ERR = mp.mpf("1e-2")
EPS_POWERS = (6, 10, 14, 18)
SPECTATOR_VALUES = (
    sympy.Integer(2),
    sympy.Integer(-3),
    sympy.Rational(1, 2),
    sympy.Rational(5, 3),
    sympy.Integer(7),
)
_PARAM_NAMES = frozenset(
    {"t", "h", "eps", "epsilon", "delta", "tau", "lam", "lambda"}
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


@dataclass(frozen=True)
class NumericProbeResult:
    """Diagnostic record. ``status`` is never ZERO."""

    status: str
    investigation: str = ""
    n_valid: int = 0
    n_agree: int = 0
    n_disagree: int = 0
    median_err: Optional[str] = None
    degeneration: tuple[str, str] = ("", "")
    note: str = "numeric samples only; never a ZERO certificate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "investigation": self.investigation,
            "n_valid": self.n_valid,
            "n_agree": self.n_agree,
            "n_disagree": self.n_disagree,
            "median_err": self.median_err,
            "degeneration": list(self.degeneration),
            "note": self.note,
        }


def numeric_probe(
    e_gen: Any,
    e_diag: Any,
    var: Any = None,
    point: Any = None,
    *,
    degeneration_variable: Any = None,
    target_value: Any = None,
) -> str:
    """Compare high-precision samples of E_gen vs E_diag as t -> 0.

    Returns ``agree``, ``disagree``, or ``undecided``. Never ``ZERO``.
    """
    try:
        status = probe_report(
            e_gen,
            e_diag,
            var,
            point,
            degeneration_variable=degeneration_variable,
            target_value=target_value,
        ).status
    except Exception:
        return UNDECIDED
    if status not in ALLOWED_STATUSES:
        return UNDECIDED
    return status


def probe_report(
    e_gen: Any,
    e_diag: Any,
    var: Any = None,
    point: Any = None,
    *,
    degeneration_variable: Any = None,
    target_value: Any = None,
) -> NumericProbeResult:
    """Full sample record. ``investigation`` may be SUSPECT_NONZERO."""
    try:
        result = _probe_report(
            e_gen,
            e_diag,
            var,
            point,
            degeneration_variable=degeneration_variable,
            target_value=target_value,
        )
    except Exception:
        return _undecided("exception")
    if result.status not in ALLOWED_STATUSES:
        return _undecided("forbidden_status")
    return result


def _probe_report(
    e_gen: Any,
    e_diag: Any,
    var: Any,
    point: Any,
    *,
    degeneration_variable: Any,
    target_value: Any,
) -> NumericProbeResult:
    gen = _as_expr(e_gen)
    diag = _as_expr(e_diag)
    if gen is None or diag is None:
        return _undecided("unparsed")
    if _too_large(gen) or _too_large(diag):
        return _undecided("ops_cap")

    gen, diag = _unify_pair(gen, diag)
    raw_var = (
        degeneration_variable if degeneration_variable is not None else var
    )
    raw_point = target_value if target_value is not None else point
    inferred = _infer_degeneration(gen, diag, raw_var, raw_point)
    if inferred is None:
        return _compare_without_limit(gen, diag)

    var_s, point_s = inferred
    spectators = _spectators(gen, diag, var_s)
    assignments = _spectator_assignments(spectators)
    if not assignments:
        return _undecided("no_assignments")

    with mp.workdps(DPS):
        traj = _trajectories(gen, diag, var_s, point_s, assignments)
        return _decide(traj, var_s, point_s)


def _compare_without_limit(
    gen: sympy.Expr, diag: sympy.Expr
) -> NumericProbeResult:
    """Numeric function samples when no degeneration is identified."""
    spectators = _spectators(gen, diag, None)
    assignments = _spectator_assignments(spectators)
    if not assignments:
        assignments = [{}]
    with mp.workdps(DPS):
        labels: list[str] = []
        errs: list[Any] = []
        for mapping in assignments:
            fmap = _float_map(mapping)
            vg = _nval(gen, fmap)
            vd = _nval(diag, fmap)
            lab, err = _classify_pair(vg, vd)
            if lab == UNDECIDED:
                continue
            labels.append(lab)
            if err is not None:
                errs.append(err)
        return _vote(
            labels,
            errs,
            degeneration=("", ""),
            note="no degeneration inferred; sampled as functions; never ZERO",
        )


def _trajectories(
    gen: sympy.Expr,
    diag: sympy.Expr,
    var: sympy.Expr,
    point: sympy.Expr,
    assignments: list[dict[sympy.Expr, sympy.Expr]],
) -> tuple[list[str], list[Any]]:
    labels: list[str] = []
    finest_errs: list[Any] = []
    for mapping in assignments:
        point_n = _eval_point(point, mapping)
        if point_n is None:
            continue
        for sign in (1, -1):
            seq: list[Any] = []
            pair_seq: list[tuple[Any, Any]] = []
            for power in EPS_POWERS:
                t = sign * sympy.Rational(1, 10**power)
                try:
                    var_n = point_n + t
                except Exception:
                    continue
                gmap = _float_map(mapping)
                gmap[var] = _as_float(var_n)
                dmap = _float_map(mapping)
                if var in diag.free_symbols:
                    dmap[var] = _as_float(point_n)
                vg = _nval(gen, gmap)
                vd = _nval(diag, dmap)
                pair_seq.append((vg, vd))
                if vg == "nonfinite" or vd == "nonfinite":
                    seq.append("nonfinite")
                    continue
                if vg is None or vd is None:
                    continue
                seq.append(_scaled_err(vg, vd))
            lab, err = _classify_trajectory(seq, pair_seq)
            if lab == UNDECIDED:
                continue
            labels.append(lab)
            if err is not None:
                finest_errs.append(err)
    return labels, finest_errs


def _classify_trajectory(
    seq: list[Any], pair_seq: list[tuple[Any, Any]]
) -> tuple[str, Optional[Any]]:
    if not seq:
        return UNDECIDED, None
    if any(item == "nonfinite" for item in seq):
        # Finite diagonal vs inf/NaN on approach is a strong mismatch.
        finite_diag = False
        for vg, vd in pair_seq:
            if vd not in (None, "nonfinite") and vg == "nonfinite":
                finite_diag = True
                break
        if finite_diag:
            return DISAGREE, STRONG_ERR
        return UNDECIDED, None
    errs = [e for e in seq if e is not None and e != "nonfinite"]
    if not errs:
        return UNDECIDED, None
    fine = errs[-1]
    coarse = errs[0]
    shrinking = None
    if coarse > 0:
        try:
            shrinking = fine / coarse
        except Exception:
            shrinking = None
    if fine <= AGREE_ERR:
        return AGREE, fine
    if (
        shrinking is not None
        and shrinking <= mp.mpf("1e-6")
        and fine <= DISAGREE_ERR
    ):
        return AGREE, fine
    if fine >= DISAGREE_ERR and (
        shrinking is None or shrinking > mp.mpf("0.1")
    ):
        return DISAGREE, fine
    return UNDECIDED, fine


def _classify_pair(vg: Any, vd: Any) -> tuple[str, Optional[Any]]:
    if vg == "nonfinite" or vd == "nonfinite":
        if vg == "nonfinite" and vd not in (None, "nonfinite"):
            return DISAGREE, STRONG_ERR
        if vd == "nonfinite" and vg not in (None, "nonfinite"):
            return DISAGREE, STRONG_ERR
        return UNDECIDED, None
    if vg is None or vd is None:
        return UNDECIDED, None
    err = _scaled_err(vg, vd)
    if err <= AGREE_ERR:
        return AGREE, err
    if err >= DISAGREE_ERR:
        return DISAGREE, err
    return UNDECIDED, err


def _decide(
    traj: tuple[list[str], list[Any]],
    var: sympy.Expr,
    point: sympy.Expr,
) -> NumericProbeResult:
    labels, errs = traj
    return _vote(
        labels,
        errs,
        degeneration=(str(var), str(point)),
        note="numeric samples of lim t->0 E_gen vs E_diag; never ZERO",
    )


def _vote(
    labels: list[str],
    errs: list[Any],
    *,
    degeneration: tuple[str, str],
    note: str,
) -> NumericProbeResult:
    n_agree = sum(1 for lab in labels if lab == AGREE)
    n_disagree = sum(1 for lab in labels if lab == DISAGREE)
    n_valid = n_agree + n_disagree
    median = _median(errs)
    median_s = _err_str(median)
    if n_valid < MIN_TRAJECTORIES:
        return NumericProbeResult(
            status=UNDECIDED,
            investigation="",
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_err=median_s,
            degeneration=degeneration,
            note=note + "; insufficient samples",
        )
    if n_disagree >= 2 and n_disagree >= n_agree:
        return NumericProbeResult(
            status=DISAGREE,
            investigation=SUSPECT_NONZERO,
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_err=median_s,
            degeneration=degeneration,
            note=note + "; investigation only, exact path required",
        )
    if n_agree >= MIN_TRAJECTORIES and n_disagree == 0:
        return NumericProbeResult(
            status=AGREE,
            investigation="",
            n_valid=n_valid,
            n_agree=n_agree,
            n_disagree=n_disagree,
            median_err=median_s,
            degeneration=degeneration,
            note=note + "; agreement is not a certificate",
        )
    return NumericProbeResult(
        status=UNDECIDED,
        investigation="",
        n_valid=n_valid,
        n_agree=n_agree,
        n_disagree=n_disagree,
        median_err=median_s,
        degeneration=degeneration,
        note=note + "; mixed samples",
    )


def _undecided(reason: str) -> NumericProbeResult:
    return NumericProbeResult(
        status=UNDECIDED,
        investigation="",
        note=f"undecided ({reason}); numeric samples only; never ZERO",
    )


def _as_expr(obj: Any) -> Optional[sympy.Expr]:
    if obj is None:
        return None
    if isinstance(obj, sympy.Expr):
        if getattr(obj, "is_Relational", False):
            return None
        return obj
    if isinstance(obj, str):
        if not obj.strip() or len(obj) > CHAR_CAP:
            return None
        try:
            got = sympy.sympify(obj)
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


def _unify_pair(gen: sympy.Expr, diag: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    names: dict[str, sympy.Symbol] = {}
    for s in gen.free_symbols:
        names[str(s)] = s
    reps = {}
    for s in diag.free_symbols:
        key = str(s)
        if key in names and s is not names[key]:
            reps[s] = names[key]
        elif key not in names:
            names[key] = s
    if reps:
        diag = diag.xreplace(reps)
    return gen, diag


def _bind_symbol(raw: Any, *exprs: sympy.Expr) -> Optional[sympy.Expr]:
    if raw is None:
        return None
    if isinstance(raw, sympy.Expr) and raw.is_symbol:
        names = {str(s): s for e in exprs for s in e.free_symbols}
        return names.get(str(raw), raw)
    if isinstance(raw, str):
        if not raw.strip() or len(raw) > CHAR_CAP:
            return None
        for e in exprs:
            for s in e.free_symbols:
                if str(s) == raw:
                    return s
        try:
            got = sympy.sympify(raw)
        except Exception:
            return None
        if isinstance(got, sympy.Expr) and got.is_symbol:
            return got
        return None
    try:
        got = sympy.sympify(raw)
    except Exception:
        return None
    if isinstance(got, sympy.Expr) and got.is_symbol:
        names = {str(s): s for e in exprs for s in e.free_symbols}
        return names.get(str(got), got)
    return None


def _bind_point(raw: Any, *exprs: sympy.Expr) -> Optional[sympy.Expr]:
    if raw is None:
        return None
    if isinstance(raw, sympy.Expr):
        names = {str(s): s for e in exprs for s in e.free_symbols}
        reps = {s: names[str(s)] for s in raw.free_symbols if str(s) in names}
        return raw.xreplace(reps) if reps else raw
    if isinstance(raw, str):
        if not raw.strip() or len(raw) > CHAR_CAP:
            return None
        for e in exprs:
            for s in e.free_symbols:
                if str(s) == raw:
                    return s
        try:
            return sympy.sympify(raw)
        except Exception:
            return None
    try:
        return sympy.sympify(raw)
    except Exception:
        return None


def _infer_degeneration(
    gen: sympy.Expr,
    diag: sympy.Expr,
    raw_var: Any,
    raw_point: Any,
) -> Optional[tuple[sympy.Expr, sympy.Expr]]:
    var = _bind_symbol(raw_var, gen, diag)
    point = _bind_point(raw_point, gen, diag)
    if var is not None and point is not None:
        return var, point
    extra = set(gen.free_symbols) - set(diag.free_symbols)
    shared = set(gen.free_symbols) & set(diag.free_symbols)
    if var is None and len(extra) == 1:
        var = next(iter(extra))
    if var is None:
        named = [s for s in gen.free_symbols if str(s) in _PARAM_NAMES]
        if len(named) == 1:
            var = named[0]
    if var is None:
        return None
    if point is not None:
        return var, point
    if str(var) in _PARAM_NAMES:
        return var, sympy.Integer(0)
    if len(shared) == 1:
        return var, next(iter(shared))
    candidates = []
    for s in sorted(shared, key=str):
        if _looks_singular_at(gen, var, s):
            candidates.append(s)
    if len(candidates) == 1:
        return var, candidates[0]
    if _looks_singular_at(gen, var, sympy.Integer(0)):
        return var, sympy.Integer(0)
    if not shared:
        return var, sympy.Integer(0)
    return None


def _looks_singular_at(
    expr: sympy.Expr, var: sympy.Expr, point: sympy.Expr
) -> bool:
    try:
        den = sympy.denom(expr)
    except Exception:
        return False
    try:
        val = den.xreplace({var: point})
    except Exception:
        return False
    try:
        if val == 0:
            return True
        if val.is_zero is True:
            return True
    except Exception:
        return False
    return False


def _spectators(
    gen: sympy.Expr, diag: sympy.Expr, var: Optional[sympy.Expr]
) -> list[sympy.Expr]:
    free = set(gen.free_symbols) | set(diag.free_symbols)
    if var is not None:
        free.discard(var)
    return sorted(free, key=str)


def _spectator_assignments(
    spectators: list[sympy.Expr],
) -> list[dict[sympy.Expr, sympy.Expr]]:
    if not spectators:
        return [{}]
    lattice = SPECTATOR_VALUES
    n = max(len(lattice), MIN_TRAJECTORIES)
    rows: list[dict[sympy.Expr, sympy.Expr]] = []
    for i in range(n):
        mapping: dict[sympy.Expr, sympy.Expr] = {}
        for j, s in enumerate(spectators):
            mapping[s] = lattice[(i + 2 * j) % len(lattice)]
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


def _as_float(val: Any) -> sympy.Float:
    if isinstance(val, sympy.Float):
        return val
    return sympy.Float(val, DPS)


def _float_map(
    mapping: dict[sympy.Expr, sympy.Expr],
) -> dict[sympy.Expr, sympy.Expr]:
    return {sym: _as_float(val) for sym, val in mapping.items()}


def _nval(
    expr: sympy.Expr, mapping: dict[sympy.Expr, sympy.Expr]
) -> Any:
    try:
        sub = expr.xreplace(mapping)
    except Exception:
        try:
            sub = expr.subs(mapping, simultaneous=True)
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


def _scaled_err(a: Any, b: Any) -> Any:
    diff = abs(a - b)
    scale = max(mp.mpf("1"), abs(a), abs(b))
    return diff / scale


def _median(vals: list[Any]) -> Optional[Any]:
    clean = [v for v in vals if v is not None]
    if not clean:
        return None
    ordered = sorted(clean)
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
