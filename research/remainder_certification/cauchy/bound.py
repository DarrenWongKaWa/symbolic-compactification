"""Cauchy remainder order bound from a certified pole-free disk.

R4. This package does not certify a disk (that is R3). A missing
neighborhood is UNKNOWN, including for entire families such as exp.

Given a certified open disk |z - z0| < rho and a contour radius r with
0 < r < rho, Cauchy estimates on |z - z0| = r yield, for |c t| < r,

    |R_N(t)| <= M * q(t)**(N+1)

with q = |c t|/r = |c| |t| / r (equivalently |c| |t| / rho' for a
strict subradius rho' = r). M may stay symbolic: holomorphic on the
compact disk |z - z0| <= r subset of the certified open disk implies
M = max |f| < infinity (class B). Without that lemma, M < infinity is
class C/D and the verdict is UNKNOWN or ASSUMPTION_REQUIRED, never
CERTIFIED.

The goal is order control R_N(t) = O(t**(N+1)), not a sharp constant.
Remainder CERTIFIED is not hop ZERO. No LLM. Track D2 locked.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Optional

import sympy

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    CERTIFIED,
    HOP_ZERO,
    METHOD_VERSION,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    RemainderCertificate,
    UNKNOWN,
    UNSUPPORTED,
    validate_certificate,
)

CHAR_CAP = 4096
OPS_CAP = 80

CAUCHY_BOUND_FORM = "M * q(t)**(N+1)"
Q_FORM = "|c|*|t|/r"
Q_FORM_ALT = "|c|*|t|/rho_prime"
M_FINITE_LEMMA = (
    "holomorphic on compact disk |z-z0|<=r < rho implies M < infinity"
)
ORDER_NOTE = (
    "order control R_N(t)=O(t**(N+1)); M symbolic finite; "
    "remainder CERTIFIED is not hop ZERO; disk not claimed here"
)

_PARSE_LOCAL: dict[str, Any] = {
    "Integer": sympy.Integer,
    "Rational": sympy.Rational,
    "pi": sympy.pi,
    "E": sympy.E,
    "I": sympy.I,
    "oo": sympy.oo,
    "zoo": sympy.zoo,
    "inf": sympy.oo,
    "exp": sympy.exp,
    "sqrt": sympy.sqrt,
    "Abs": sympy.Abs,
    "abs": sympy.Abs,
}

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
)


def cauchy_remainder_bound(
    neighborhood: Any = None,
    *,
    N: Any = None,
    r: Any = None,
    rho: Any = None,
    rho_prime: Any = None,
    z0: Any = None,
    c: Any = None,
    t: Any = None,
    function_family: str = "",
    function_order: str = "",
    argument: Any = None,
    expansion_point: Any = None,
    perturbation: Any = None,
    M: Any = None,
    assumptions_used: Any = None,
    domain_conditions: Any = None,
) -> RemainderCertificate:
    """Return a remainder certificate from Cauchy estimates on a certified disk.

    ``neighborhood`` must already be a certified pole-free disk (R3).
    This function never invents a radius. Missing disk, ``r >= rho``,
    or missing ``N`` fail closed (UNKNOWN / ASSUMPTION_REQUIRED).
    """
    try:
        return _cauchy_remainder_bound(
            neighborhood,
            N=N,
            r=r,
            rho=rho,
            rho_prime=rho_prime,
            z0=z0,
            c=c,
            t=t,
            function_family=function_family,
            function_order=function_order,
            argument=argument,
            expansion_point=expansion_point,
            perturbation=perturbation,
            M=M,
            assumptions_used=assumptions_used,
            domain_conditions=domain_conditions,
        )
    except Exception:
        return _certificate(
            verdict=UNKNOWN,
            note="cauchy bound failed closed",
            domain_conditions=["cauchy bound failed closed"],
        )


def _cauchy_remainder_bound(
    neighborhood: Any,
    *,
    N: Any,
    r: Any,
    rho: Any,
    rho_prime: Any,
    z0: Any,
    c: Any,
    t: Any,
    function_family: str,
    function_order: str,
    argument: Any,
    expansion_point: Any,
    perturbation: Any,
    M: Any,
    assumptions_used: Any,
    domain_conditions: Any,
) -> RemainderCertificate:
    neigh = _extract_neighborhood(neighborhood)
    family = str(function_family or neigh.get("function_family") or "")
    order = str(function_order or neigh.get("function_order") or "")
    nv = str(neigh.get("verdict") or NEIGHBORHOOD_UNKNOWN)
    extra_assumptions = _as_assumption_list(assumptions_used)
    extra_assumptions = _merge_assumptions(
        _as_assumption_list(neigh.get("assumptions_used")), extra_assumptions
    )
    extra_domain = _merge_text(
        _as_text_list(neigh.get("domain_conditions")),
        _as_text_list(domain_conditions),
    )
    z0_raw = (
        z0
        if z0 is not None
        else (
            expansion_point
            if expansion_point is not None
            else neigh.get("center")
        )
    )
    rho_raw = rho if rho is not None else neigh.get("rho")
    t_raw = t if t is not None else "t"
    c_raw = c
    arg_raw = argument if argument is not None else neigh.get("argument")

    base = dict(
        function_family=family,
        function_order=order,
        neighborhood_verdict=nv,
        assumptions_used=extra_assumptions,
        expansion_point=_s(z0_raw),
        perturbation=_s(perturbation) if perturbation is not None else "",
        argument=_s(arg_raw),
    )

    if not neigh.get("present"):
        return _certificate(
            verdict=UNKNOWN,
            note="neighborhood missing; Cauchy bound does not invent a disk",
            domain_conditions=_merge_text(
                extra_domain,
                ["neighborhood missing; Cauchy bound does not invent a disk"],
            ),
            **base,
        )
    if nv == NEIGHBORHOOD_ASSUMPTION or nv == ASSUMPTION_REQUIRED:
        return _certificate(
            verdict=ASSUMPTION_REQUIRED,
            note="neighborhood ASSUMPTION_REQUIRED; M finiteness not proved",
            domain_conditions=_merge_text(
                extra_domain,
                ["neighborhood ASSUMPTION_REQUIRED; disk not certified"],
            ),
            **base,
        )
    if nv in (NEIGHBORHOOD_UNKNOWN, UNKNOWN, UNSUPPORTED, ""):
        return _certificate(
            verdict=UNKNOWN,
            note="neighborhood not certified; Cauchy bound does not invent a disk",
            domain_conditions=_merge_text(
                extra_domain,
                ["neighborhood not certified; Cauchy bound does not invent a disk"],
            ),
            **base,
        )
    if nv != NEIGHBORHOOD_CERTIFIED:
        return _certificate(
            verdict=UNKNOWN,
            note="neighborhood verdict is not CERTIFIED_NEIGHBORHOOD",
            domain_conditions=_merge_text(
                extra_domain,
                ["neighborhood verdict is not CERTIFIED_NEIGHBORHOOD"],
            ),
            **base,
        )

    n_int = _as_nat(N)
    if n_int is None:
        return _certificate(
            verdict=UNKNOWN,
            note="N missing; cannot form O(t**(N+1))",
            domain_conditions=_merge_text(
                extra_domain, ["N missing; cannot form O(t**(N+1))"]
            ),
            expansion_order=None,
            **base,
        )

    rho_expr = _as_expr(rho_raw)
    if rho_expr is None or _too_large(rho_expr) or _has_nonfinite(rho_expr):
        return _certificate(
            verdict=UNKNOWN,
            note="certified neighborhood missing a usable radius rho",
            domain_conditions=_merge_text(
                extra_domain,
                ["certified neighborhood missing a usable radius rho"],
            ),
            expansion_order=n_int,
            **base,
        )
    rho_pos = _proved_positive(rho_expr)
    if rho_pos is not True:
        return _certificate(
            verdict=UNKNOWN,
            note="rho > 0 unproved; Cauchy bound does not invent a disk",
            domain_conditions=_merge_text(
                extra_domain, ["rho > 0 unproved"]
            ),
            expansion_order=n_int,
            distance_to_singularity=_s(rho_expr),
            **base,
        )

    r_raw = r if r is not None else rho_prime
    r_expr = _as_expr(r_raw)
    if r_expr is None:
        # Contour inside a certified finite disk, not a new neighborhood.
        if rho_expr.is_infinite is True:
            return _certificate(
                verdict=UNKNOWN,
                note="r missing; infinite rho still needs an explicit finite contour",
                domain_conditions=_merge_text(
                    extra_domain, ["r missing for infinite certified radius"]
                ),
                expansion_order=n_int,
                distance_to_singularity=_s(rho_expr),
                **base,
            )
        r_expr = sympy.simplify(rho_expr / 2)
    if _too_large(r_expr) or _has_nonfinite(r_expr):
        return _certificate(
            verdict=UNKNOWN,
            note="Cauchy contour radius r unusable",
            domain_conditions=_merge_text(
                extra_domain, ["Cauchy contour radius r unusable"]
            ),
            expansion_order=n_int,
            distance_to_singularity=_s(rho_expr),
            **base,
        )

    r_inside = _strict_inside(r_expr, rho_expr)
    if r_inside is not True:
        if _proved_positive(r_expr) is not True or r_expr.is_infinite is True:
            why = "r not proved finite positive"
        elif r_inside is False:
            why = "r >= rho; compact disk is not inside the certified open disk"
        else:
            why = "r < rho unproved; M finiteness not proved"
        return _certificate(
            verdict=UNKNOWN,
            note=why,
            domain_conditions=_merge_text(extra_domain, [why]),
            expansion_order=n_int,
            distance_to_singularity=_s(rho_expr),
            **base,
        )

    m_ok, m_note = _m_finiteness(M, compact_inside=True)
    if not m_ok:
        verdict = (
            ASSUMPTION_REQUIRED
            if m_note == "M < infinity assumed without a finiteness proof"
            else UNKNOWN
        )
        return _certificate(
            verdict=verdict,
            note=m_note,
            domain_conditions=_merge_text(extra_domain, [m_note]),
            expansion_order=n_int,
            distance_to_singularity=_s(rho_expr),
            **base,
        )

    t_expr = _as_expr(t_raw)
    c_expr = _as_expr(c_raw) if c_raw is not None else None
    z0_expr = _as_expr(z0_raw) if z0_raw is not None else None
    if t_expr is not None and _too_large(t_expr):
        return _certificate(
            verdict=UNKNOWN,
            note="perturbation coordinate t unusable",
            domain_conditions=_merge_text(
                extra_domain, ["perturbation coordinate t unusable"]
            ),
            expansion_order=n_int,
            **base,
        )
    if c_expr is not None and t_expr is not None:
        if t_expr.free_symbols and (c_expr.free_symbols & t_expr.free_symbols):
            return _certificate(
                verdict=UNKNOWN,
                note="perturbation coefficient c depends on t",
                domain_conditions=_merge_text(
                    extra_domain, ["perturbation coefficient c depends on t"]
                ),
                expansion_order=n_int,
                **base,
            )
    if z0_expr is not None and t_expr is not None:
        if t_expr.free_symbols and (z0_expr.free_symbols & t_expr.free_symbols):
            return _certificate(
                verdict=UNKNOWN,
                note="expansion point z0 depends on t",
                domain_conditions=_merge_text(
                    extra_domain, ["expansion point z0 depends on t"]
                ),
                expansion_order=n_int,
                **base,
            )

    c_s = _s(c_expr if c_expr is not None else (c_raw if c_raw is not None else "c"))
    t_s = _s(t_expr if t_expr is not None else t_raw)
    z0_s = _s(z0_expr if z0_expr is not None else (z0_raw if z0_raw is not None else "z0"))
    r_s = _s(r_expr)
    rho_s = _s(rho_expr)
    exp_n = n_int + 1
    pert = perturbation if perturbation is not None else f"{c_s}*{t_s}"
    arg = arg_raw if arg_raw not in (None, "") else f"{z0_s} + {pert}"
    bound = f"M*(|{c_s}|*|{t_s}|/({r_s}))**({exp_n})"
    remainder_form = f"|R_{n_int}(t)| <= M * q(t)**({exp_n})"
    c_zero = c_expr is not None and _proved_zero(c_expr) is True
    if c_zero:
        small_t = "c = 0; remainder is identically 0 for N >= 0"
        bound = "0"
        remainder_form = f"|R_{n_int}(t)| = 0"
    else:
        c_pos = c_expr is not None and _proved_positive(sympy.Abs(c_expr)) is True
        if c_pos:
            small_t = f"|{c_s}*{t_s}| < {r_s} < {rho_s}; |{t_s}| < {r_s}/|{c_s}|"
        else:
            small_t = f"|{c_s}*{t_s}| < {r_s} < {rho_s}"

    domain = _merge_text(
        extra_domain,
        [
            f"certified pole-free disk |z - ({z0_s})| < {rho_s} (R3; not claimed here)",
            f"Cauchy contour |z - ({z0_s})| = {r_s} with 0 < {r_s} < {rho_s}",
            small_t,
            M_FINITE_LEMMA,
        ],
    )
    assumptions = _merge_assumptions(
        extra_assumptions,
        [
            {
                "class": A_DECLARED,
                "predicate": "neighborhood_verdict=CERTIFIED_NEIGHBORHOOD",
            },
            {"class": B_DERIVED, "predicate": f"0 < r < rho with r={r_s}, rho={rho_s}"},
            {"class": B_DERIVED, "predicate": M_FINITE_LEMMA},
        ],
    )
    analyticity = {
        "engine": "cauchy",
        "rho": rho_s,
        "r": r_s,
        "rho_prime": r_s,
        "q": Q_FORM,
        "q_alt": Q_FORM_ALT,
        "N": n_int,
        "M_finite": True,
        "M_symbol": "M",
        "M_finiteness": M_FINITE_LEMMA,
        "order": f"O(t**{exp_n})",
        "bound": bound,
        "equivalent_integral_bound": (
            "M_r * q**(N+1) / (1-q) for |c t| < r; "
            "on |c t| <= r/2 the factor 1/(1-q) <= 2 is absorbed into finite M"
        ),
        "function_family": family,
        "does_not_claim_disk": True,
        "neighborhood_verdict": nv,
    }
    return _certificate(
        function_family=family,
        function_order=order,
        argument=_s(arg),
        expansion_point=z0_s,
        perturbation=_s(pert),
        expansion_order=n_int,
        domain_conditions=domain,
        analyticity_certificate=analyticity,
        distance_to_singularity=rho_s,
        remainder_form=remainder_form,
        bound=bound,
        required_small_t_condition=small_t,
        assumptions_used=assumptions,
        proof_dependencies=[
            "neighborhood_certificate",
            "cauchy_integral_formula",
            "cauchy_estimates",
            "holomorphic_on_compact_disk_implies_bounded",
        ],
        verdict=CERTIFIED,
        neighborhood_verdict=nv,
        note=ORDER_NOTE,
    )


def _extract_neighborhood(neighborhood: Any) -> dict[str, Any]:
    if neighborhood is None:
        return {"present": False, "verdict": NEIGHBORHOOD_UNKNOWN}
    if isinstance(neighborhood, RemainderCertificate):
        ac = dict(neighborhood.analyticity_certificate or {})
        rho = (
            ac.get("rho")
            or ac.get("radius")
            or ac.get("disk_radius")
            or neighborhood.distance_to_singularity
        )
        center = ac.get("center") or ac.get("z0") or neighborhood.expansion_point
        return {
            "present": True,
            "verdict": neighborhood.neighborhood_verdict or NEIGHBORHOOD_UNKNOWN,
            "rho": rho,
            "center": center,
            "function_family": neighborhood.function_family,
            "function_order": neighborhood.function_order,
            "argument": neighborhood.argument,
            "domain_conditions": list(neighborhood.domain_conditions or []),
            "assumptions_used": list(neighborhood.assumptions_used or []),
            "analyticity_certificate": ac,
        }
    if isinstance(neighborhood, dict):
        if not neighborhood:
            return {"present": False, "verdict": NEIGHBORHOOD_UNKNOWN}
        nv = neighborhood.get("neighborhood_verdict")
        if nv in (None, ""):
            nv = neighborhood.get("verdict")
        ac = neighborhood.get("analyticity_certificate") or {}
        if not isinstance(ac, dict):
            ac = {}
        rho = (
            neighborhood.get("rho")
            or neighborhood.get("radius")
            or neighborhood.get("disk_radius")
            or ac.get("rho")
            or ac.get("radius")
            or neighborhood.get("distance_to_singularity")
        )
        center = (
            neighborhood.get("center")
            or neighborhood.get("z0")
            or neighborhood.get("expansion_point")
            or ac.get("center")
            or ac.get("z0")
        )
        return {
            "present": True,
            "verdict": nv or NEIGHBORHOOD_UNKNOWN,
            "rho": rho,
            "center": center,
            "function_family": neighborhood.get("function_family") or "",
            "function_order": neighborhood.get("function_order") or "",
            "argument": neighborhood.get("argument") or "",
            "domain_conditions": list(neighborhood.get("domain_conditions") or []),
            "assumptions_used": list(neighborhood.get("assumptions_used") or []),
            "analyticity_certificate": ac,
        }
    nv = getattr(neighborhood, "neighborhood_verdict", None)
    if nv in (None, ""):
        nv = getattr(neighborhood, "verdict", None)
    ac = getattr(neighborhood, "analyticity_certificate", None) or {}
    if not isinstance(ac, dict):
        ac = {}
    rho = (
        getattr(neighborhood, "rho", None)
        or getattr(neighborhood, "radius", None)
        or ac.get("rho")
        or ac.get("radius")
        or getattr(neighborhood, "distance_to_singularity", None)
    )
    return {
        "present": True,
        "verdict": nv or NEIGHBORHOOD_UNKNOWN,
        "rho": rho,
        "center": getattr(neighborhood, "center", None)
        or getattr(neighborhood, "z0", None)
        or ac.get("center"),
        "function_family": getattr(neighborhood, "function_family", "") or "",
        "function_order": getattr(neighborhood, "function_order", "") or "",
        "argument": getattr(neighborhood, "argument", "") or "",
        "domain_conditions": list(
            getattr(neighborhood, "domain_conditions", None) or []
        ),
        "assumptions_used": list(
            getattr(neighborhood, "assumptions_used", None) or []
        ),
        "analyticity_certificate": ac,
    }


def _m_finiteness(M: Any, *, compact_inside: bool) -> tuple[bool, str]:
    """Finiteness of M is the compact-disk lemma, not a silent assumption."""
    if not compact_inside:
        if M is None:
            return False, "M < infinity unproved (no compact subdisk)"
        return False, "M < infinity assumed without a finiteness proof"
    if M is None:
        return True, M_FINITE_LEMMA
    m_expr = _as_expr(M)
    if m_expr is None:
        return False, "supplied M is unusable; M finiteness not proved"
    if _has_nonfinite(m_expr) or m_expr.is_infinite is True:
        return False, "supplied M is not finite"
    if _proved_positive(m_expr) is False and _proved_zero(m_expr) is not True:
        # a proved-negative max-modulus is nonsense; fail closed
        if m_expr.is_real is True and _proved_positive(-m_expr) is True:
            return False, "supplied M is not a finite bound"
    return True, M_FINITE_LEMMA


def _strict_inside(r: sympy.Expr, rho: sympy.Expr) -> Optional[bool]:
    """True iff 0 < r < rho with r finite. False if proved otherwise."""
    if _has_nonfinite(r) or _has_nonfinite(rho):
        return False
    if r.is_infinite is True:
        return False
    r_pos = _proved_positive(r)
    if r_pos is False:
        return False
    if r_pos is not True:
        gap_only = _proved_positive(rho - r)
        if gap_only is False:
            return False
        return None
    gap = _proved_positive(rho - r)
    if gap is True:
        return True
    if gap is False:
        return False
    return None


def _proved_positive(expr: sympy.Expr) -> Optional[bool]:
    try:
        e = sympy.simplify(expr)
    except Exception:
        return None
    if _has_nonfinite(e):
        return None
    if e.is_positive is True:
        return True
    if e.is_nonpositive is True:
        return False
    if e.is_negative is True or e.is_zero is True:
        return False
    return None


def _proved_zero(expr: sympy.Expr) -> Optional[bool]:
    try:
        e = sympy.simplify(expr)
    except Exception:
        return None
    if e.is_zero is True:
        return True
    if e.is_zero is False:
        return False
    return None


def _as_nat(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, sympy.Integer):
        n = int(value)
        return n if n >= 0 else None
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("+"):
            text = text[1:]
        if text.isdigit():
            return int(text)
        return None
    return None


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, float):
        return None
    if isinstance(value, sympy.Expr):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text or len(text) > CHAR_CAP:
            return None
        lowered = text.lower()
        if lowered in ("oo", "inf", "+inf", "infinity", "∞"):
            return sympy.oo
        try:
            expr = sympy.parse_expr(
                text, local_dict=dict(_PARSE_LOCAL), evaluate=True
            )
        except Exception:
            return None
        if not isinstance(expr, sympy.Expr):
            return None
        return expr
    return None


def _too_large(expr: sympy.Expr) -> bool:
    try:
        if len(str(expr)) > CHAR_CAP:
            return True
        return int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    except Exception:
        return True


def _has_nonfinite(expr: sympy.Expr) -> bool:
    try:
        if any(expr == sentinel for sentinel in _NONFINITE):
            return True
        return bool(expr.has(*_NONFINITE))
    except Exception:
        return True


def _as_assumption_list(value: Any) -> list[dict[str, Any]]:
    if not value:
        return []
    if isinstance(value, dict):
        return [dict(value)]
    out: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, dict):
            out.append(dict(item))
    return out


def _as_text_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value] if value else []
    return [str(x) for x in value if str(x)]


def _merge_text(*groups: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for group in groups:
        for item in group:
            if item not in seen:
                seen.add(item)
                out.append(item)
    return out


def _merge_assumptions(*groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for group in groups:
        for item in group:
            key = json.dumps(item, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                out.append(item)
    return out


def _s(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _sha(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _sha_json(obj: Any) -> str:
    return _sha(json.dumps(obj, sort_keys=True, default=str))


def _certificate(**kwargs: Any) -> RemainderCertificate:
    assumptions = list(kwargs.get("assumptions_used") or [])
    kwargs["assumptions_used"] = assumptions
    domain = list(kwargs.get("domain_conditions") or [])
    if not domain:
        domain = [str(kwargs.get("note") or "cauchy hypotheses unproved")]
    kwargs["domain_conditions"] = domain
    kwargs.setdefault("method_version", METHOD_VERSION)
    kwargs.setdefault("argument_text_hash", _sha(str(kwargs.get("argument") or "")))
    kwargs.setdefault("assumptions_hash", _sha_json(assumptions))
    allowed = RemainderCertificate.__dataclass_fields__
    cert = RemainderCertificate(**{k: v for k, v in kwargs.items() if k in allowed})
    cert.verdict = validate_certificate(cert)
    if cert.verdict == HOP_ZERO:
        cert.verdict = UNKNOWN
    return cert
