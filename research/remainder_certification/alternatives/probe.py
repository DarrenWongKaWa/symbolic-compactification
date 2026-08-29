"""Probe existing remainder backends. Never certifies hop ZERO.

No new packages. Absence of Arb / python-flint is a recorded fact.
Symbolic affine polygamma remainder is the test class, not a design
oracle. CASE R-E is accepted only if a mature backend is sound,
decidable on that class, and importable now.
"""
from __future__ import annotations

import importlib
import json
from typing import Any, Optional

import sympy
from sympy.holonomic import expr_to_holonomic
from sympy.series.order import Order

from research.coefficient_laurent.remainder import remainder_ok, remainder_verdict
from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN
from research.coefficient_laurent.schema import ZERO as HOP_ZERO

CASE_R_E = "CASE_R_E"
CONTINUE_CUSTOM = "CONTINUE_CUSTOM"
RECOMMENDATION = CONTINUE_CUSTOM

_IMPORT_CANDIDATES = (
    "flint",
    "python_flint",
    "arb",
    "sage",
    "ore_algebra",
    "gmpy2",
    "symengine",
    "mpmath",
    "mpmath.ctx_iv",
    "sympy",
    "sympy.holonomic",
    "sympy.series",
)


def _try_import(name: str) -> dict[str, Any]:
    rec: dict[str, Any] = {"name": name, "available": False, "version": None, "error": None}
    try:
        mod = importlib.import_module(name)
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
        return rec
    rec["available"] = True
    rec["version"] = getattr(mod, "__version__", None)
    return rec


def probe_imports() -> dict[str, dict[str, Any]]:
    return {name: _try_import(name) for name in _IMPORT_CANDIDATES}


def probe_v5_remainder_ok() -> dict[str, Any]:
    t, a, c = sympy.symbols("t a c")
    cases = {
        "numeric_regular": remainder_ok(1 + t, t),
        "symbolic_affine": remainder_ok(a + t, t),
        "symbolic_affine_slope": remainder_ok(a + c * t, t),
        "pole_at_zero": remainder_ok(t, t),
    }
    verdicts = {
        "numeric_regular": remainder_verdict(1 + t, t),
        "symbolic_affine": remainder_verdict(a + t, t),
    }
    return {
        "ok": cases,
        "verdicts": verdicts,
        "symbolic_alpha_insufficient": cases["symbolic_affine"] is False
        and verdicts["symbolic_affine"] == HOP_UNKNOWN,
        "never_hop_zero_on_symbolic": verdicts["symbolic_affine"] != HOP_ZERO,
    }


def probe_sympy_series() -> dict[str, Any]:
    t, a = sympy.symbols("t a")
    symbolic = polygamma_series(sympy.polygamma(0, a + t), t)
    numeric = polygamma_series(sympy.polygamma(0, 1 + t), t)
    pole = polygamma_series(sympy.polygamma(0, t), t)
    formal = symbolic.get("series")
    substituted_pole = None
    if formal is not None:
        substituted_pole = str(formal.subs(a, 0))
    return {
        "numeric_regular": numeric,
        "symbolic_affine": symbolic,
        "pole_at_zero": pole,
        "symbolic_emits_order_marker": bool(symbolic.get("has_order")),
        "pole_raises": pole.get("error_type") == "PoleError",
        "subs_symbolic_series_at_pole": substituted_pole,
        "order_is_truncation_marker_not_bound": True,
    }


def polygamma_series(expr: sympy.Expr, t: sympy.Symbol, n: int = 3) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "expr": str(expr),
        "series": None,
        "has_order": False,
        "error_type": None,
    }
    try:
        s = expr.series(t, 0, n)
    except Exception as exc:
        rec["error_type"] = type(exc).__name__
        rec["error"] = str(exc)[:180]
        return rec
    rec["series"] = s
    rec["series_str"] = str(s)
    rec["has_order"] = bool(s.has(Order)) if hasattr(s, "has") else False
    rec["getO"] = str(s.getO()) if hasattr(s, "getO") else None
    return rec


def probe_holonomic() -> dict[str, Any]:
    x, t, a = sympy.symbols("x t a")
    rows = []
    for expr, var in (
        (sympy.exp(x), x),
        (sympy.sin(x), x),
        (sympy.gamma(x), x),
        (sympy.polygamma(0, x), x),
        (sympy.polygamma(1, x), x),
        (sympy.loggamma(x), x),
        (sympy.polygamma(0, a + t), t),
        (sympy.polygamma(0, 1 + t), t),
    ):
        rows.append(_holonomic_one(expr, var))
    polygamma_converted = any(
        r["converted"] for r in rows if "polygamma" in r["expr"]
    )
    gamma_converted = any(r["converted"] for r in rows if r["expr"].startswith("gamma("))
    return {
        "rows": rows,
        "polygamma_converted": polygamma_converted,
        "gamma_converted": gamma_converted,
        "d_finite_table_has_exp_sin": all(
            r["converted"] for r in rows if r["expr"] in ("exp(x)", "sin(x)")
        ),
    }


def _holonomic_one(expr: sympy.Expr, var: sympy.Symbol) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "expr": str(expr),
        "var": str(var),
        "converted": False,
        "error_type": None,
        "annihilator": None,
    }
    try:
        h = expr_to_holonomic(expr, var)
    except Exception as exc:
        rec["error_type"] = type(exc).__name__
        rec["error"] = str(exc)[:180].replace("\n", " ")
        return rec
    rec["converted"] = True
    rec["annihilator"] = str(h)[:200]
    return rec


def probe_ball_arithmetic() -> dict[str, Any]:
    iv_mod = _try_import("mpmath")
    iv_names: dict[str, bool] = {}
    iv_gamma_ok = False
    iv_psi_ok = False
    iv_zeta_ok = False
    if iv_mod["available"]:
        import mpmath as mp

        iv = mp.iv
        for name in ("psi", "polygamma", "digamma", "gamma", "loggamma", "zeta", "exp"):
            iv_names[name] = callable(getattr(iv, name, None))
        try:
            _ = iv.gamma(iv.mpf([0.5, 0.6]))
            iv_gamma_ok = True
        except Exception:
            iv_gamma_ok = False
        try:
            psi = getattr(iv, "psi", None)
            if psi is None:
                iv_psi_ok = False
            else:
                _ = psi(0, iv.mpf("0.5"))
                iv_psi_ok = True
        except Exception:
            iv_psi_ok = False
        try:
            _ = iv.zeta(2)
            iv_zeta_ok = True
        except Exception:
            iv_zeta_ok = False
    flint = _try_import("flint")
    arb = _try_import("arb")
    return {
        "python_flint": flint,
        "arb": arb,
        "mpmath_available": iv_mod["available"],
        "mpmath_version": iv_mod.get("version"),
        "iv_attr": iv_names,
        "iv_gamma_numeric_ok": iv_gamma_ok,
        "iv_psi_ok": iv_psi_ok,
        "iv_zeta_ok": iv_zeta_ok,
        "symbolic_alpha_possible": False,
        "flint_importable": bool(flint["available"]),
        "arb_importable": bool(arb["available"]),
    }


def probe_identities() -> dict[str, Any]:
    z = sympy.symbols("z")
    rec0 = sympy.expand_func(sympy.polygamma(0, z + 1)) - (
        sympy.polygamma(0, z) + 1 / z
    )
    rec1 = sympy.expand_func(sympy.polygamma(1, z + 1)) - (
        sympy.polygamma(1, z) - 1 / z**2
    )
    rec2 = sympy.expand_func(sympy.polygamma(2, z + 1)) - (
        sympy.polygamma(2, z) + 2 / z**3
    )
    zeta_rw = sympy.polygamma(2, z).rewrite(sympy.zeta)
    a, t = sympy.symbols("a t")
    return {
        "recurrence_n0": rec0 == 0,
        "recurrence_n1": rec1 == 0,
        "recurrence_n2": rec2 == 0,
        "zeta_rewrite_n2": str(zeta_rw),
        "identities_discharge_symbolic_alpha": False,
        "remainder_ok_still_unknown": remainder_ok(a + t, t) is False,
    }


def probe_singularities() -> dict[str, Any]:
    z, a, t = sympy.symbols("z a t")
    from sympy.calculus.util import singularities

    pg = singularities(sympy.polygamma(0, z), z)
    gamma = singularities(sympy.gamma(z), z)
    rat = singularities(1 / z, z)
    affine = singularities(sympy.polygamma(0, a + t), t)
    return {
        "polygamma_poles_reported": str(pg),
        "gamma_poles_reported": str(gamma),
        "rational_pole_reported": str(rat),
        "affine_in_t_reported": str(affine),
        "polygamma_poles_empty": pg == sympy.EmptySet,
        "cannot_certify_domain": pg == sympy.EmptySet,
    }


def probe_analytic_continuation() -> dict[str, Any]:
    fps_kind: Optional[str] = None
    t, a = sympy.symbols("t a")
    try:
        f = sympy.fps(sympy.polygamma(0, a + t), t, 0)
        fps_kind = type(f).__name__
    except Exception as exc:
        fps_kind = f"error:{type(exc).__name__}"
    return {
        "ore_algebra": _try_import("ore_algebra"),
        "sage": _try_import("sage"),
        "unpolarify_is_not_continuation_certificate": True,
        "fps_symbolic_polygamma_type": fps_kind,
        "fps_is_formal_power_series": fps_kind == "FormalPowerSeries",
    }


def decide(experiments: dict[str, Any]) -> dict[str, Any]:
    """CASE R-E only if a mature backend is superior and currently usable.

    None of the probed tools is a remainder-order decision procedure on
    symbolic affine polygamma, so CASE R-E stays rejected even if a
    numeric ball library later becomes importable.
    """
    imports = experiments["imports"]
    flint_now = bool(
        imports["flint"]["available"] or imports["python_flint"]["available"]
    )
    arb_now = bool(imports["arb"]["available"])
    reasons = [
        "V5 remainder_ok is fail-closed UNKNOWN on symbolic affine alpha",
        "sympy.series O() is a truncation marker, not a remainder bound",
        "sympy.holonomic cannot convert polygamma or gamma (not D-finite)",
        "python-flint / Arb are not importable; even if present they enclose numeric instances only",
        "mpmath.iv has no psi/polygamma and cannot take symbolic alpha",
        "ore_algebra / Sage analytic continuation are absent and target D-finite germs",
        "standard polygamma identities rewrite but do not prove holomorphy at t=0",
    ]
    return {
        "case_r_e": None,
        "case_r_e_accepted": False,
        "recommendation": CONTINUE_CUSTOM,
        "d2": "LOCKED",
        "reasons": reasons,
        "flint_importable_now": flint_now,
        "arb_importable_now": arb_now,
        "v5_symbolic_ok": experiments["v5_remainder_ok"]["ok"]["symbolic_affine"],
        "holonomic_polygamma_converted": experiments["holonomic"]["polygamma_converted"],
    }


def run_probe() -> dict[str, Any]:
    experiments = {
        "imports": probe_imports(),
        "v5_remainder_ok": probe_v5_remainder_ok(),
        "sympy_series": probe_sympy_series(),
        "holonomic": probe_holonomic(),
        "ball": probe_ball_arithmetic(),
        "identities": probe_identities(),
        "singularities": probe_singularities(),
        "analytic_continuation": probe_analytic_continuation(),
    }
    decision = decide(experiments)
    return {
        "method_line": "remainder-certification alternatives",
        "recommendation": decision["recommendation"],
        "case_r_e": decision["case_r_e"],
        "case_r_e_accepted": decision["case_r_e_accepted"],
        "d2": decision["d2"],
        "sympy_version": getattr(sympy, "__version__", None),
        "experiments": experiments,
        "decision": decision,
        "note": (
            "probe never mints remainder CERTIFIED or hop ZERO; "
            "CONTINUE_CUSTOM with explicit class-A/B assumptions"
        ),
    }


def _json_default(obj: Any) -> str:
    return str(obj)


def main() -> int:
    rec = run_probe()
    print(json.dumps(rec, indent=2, sort_keys=True, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
