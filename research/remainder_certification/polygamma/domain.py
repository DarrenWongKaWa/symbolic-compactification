"""Polygamma pole-set predicates for remainder domain queries.

DLMF 5.15.1 / 5.2: for integer order ``k >= -1``, ``polygamma(k, z)`` is
meromorphic with singularities only at nonpositive integers of ``z``.
SymPy (Espinosa–Moll) for ``k <= -2``: entire in ``z``.

This module emits **domain** verdicts. CERTIFIED here means the affine
germ ``z0 + c t`` is pole-free for some ``delta > 0`` from class A/B
only — usable for a later remainder CERTIFIED. It is not a remainder
certificate and not hop ZERO. Class C/D is never inserted.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional

import sympy

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    NONANALYTIC,
    UNKNOWN,
)

METHOD = "rc-pg-domain-1"
TRUE = "TRUE"
FALSE = "FALSE"
UNPROVED = "UNPROVED"

PRED_ENTIRE = "order k <= -2 is entire"
PRED_IDENTICALLY_POLE = "z0 identically in Z_<=0"
PRED_NOT_IDENTICALLY_POLE = "z0 not identically in Z_<=0"
PRED_IM_NONZERO = "Im(z0) identically nonzero"
PRED_DIST_POS = "dist(z0, Z_<=0) certified positive"
PRED_POLE_EXCLUSION = "z0 not in Z_<=0"
PRED_NEIGHBORHOOD = "z0 + c t pole-free for sufficiently small |t|"
PRED_POSITIVE = "z0 > 0"
PRED_GENERICITY = "generic parameters avoid poles"

POLE_SET_Z_LE_0 = "nonpositive integers of the argument {0,-1,-2,...}"
POLE_SET_EMPTY = "entire (empty pole set)"
POLE_SET_UNKNOWN = "unknown"

REF_DLMF_POLES = (
    "DLMF 5.15.1: psi'(z)=sum_k 1/(k+z)^2 for z != 0,-1,-2,...; "
    "DLMF 5.2: Gamma/psi poles at nonpositive integers"
)
REF_DLMF_CHAIN = (
    "DLMF 5.15: polygamma(n,z)=d^n/dz^n psi(z) for n=1,2,... "
    "(poles remain at Z_<=0, order n+1)"
)
REF_SYMPY_LOGGAMMA = (
    "SymPy polygamma(-1,z) = loggamma(z) - log(2*pi)/2; "
    "loggamma singularities at Z_<=0"
)
REF_SYMPY_ENTIRE = (
    "SymPy polygamma (Espinosa-Moll) for integer k<=-2: entire in z; "
    "expand_func is polynomial plus d/ds zeta(s,z) at s=k+1<=-1 "
    "(DLMF 25.11.2: zeta(-n,z) is a Bernoulli polynomial)"
)
REF_ISOLATED = (
    "meromorphic poles on Z_<=0 are isolated: z0 not a pole and finite c "
    "imply exists delta>0 such that |t|<delta => z0+c*t not in Z_<=0"
)
REF_SYMPY_EVAL_ZOO = (
    "SymPy polygamma.eval returns zoo at nonpositive integers for every n, "
    "including k<=-2; that eval is not a pole certificate for entire orders"
)

OPS_CAP = 80
CHAR_CAP = 4096
K_ABS_CAP = 64
_NOTE = (
    "domain verdict only; remainder CERTIFIED is not emitted here; "
    "not a hop certificate; class C/D not inserted; D2 LOCKED"
)

_NONFINITE = (
    sympy.nan,
    sympy.zoo,
    sympy.oo,
    -sympy.oo,
    sympy.S.NaN,
    sympy.S.ComplexInfinity,
    sympy.S.Infinity,
    sympy.S.NegativeInfinity,
)


@dataclass(frozen=True)
class DomainPredicate:
    """One symbolic domain predicate with a proved status."""

    name: str
    status: str
    formula: str = ""
    proof: str = ""
    assumption_class: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "formula": self.formula,
            "proof": self.proof,
            "assumption_class": self.assumption_class,
        }


@dataclass(frozen=True)
class DomainReport:
    """Domain query for polygamma(k, z0 + c t). Not a remainder certificate."""

    function_family: str = "polygamma"
    function_order: str = ""
    argument: str = ""
    expansion_point: str = ""
    perturbation: str = ""
    pole_set: str = POLE_SET_UNKNOWN
    entire: bool = False
    predicates: tuple[DomainPredicate, ...] = ()
    domain_conditions: tuple[str, ...] = ()
    assumptions_used: tuple[dict[str, Any], ...] = ()
    missing_assumptions: tuple[dict[str, Any], ...] = ()
    verdict: str = UNKNOWN
    neighborhood_verdict: str = NEIGHBORHOOD_UNKNOWN
    analyticity_certificate: dict[str, Any] | None = None
    distance_to_singularity: str = ""
    required_small_t_condition: str = ""
    proof_dependencies: tuple[str, ...] = ()
    assumptions_hash: str = ""
    argument_text_hash: str = ""
    note: str = _NOTE
    method: str = METHOD

    @property
    def domain_usable_for_certified(self) -> bool:
        if self.verdict != CERTIFIED:
            return False
        return not any(
            item.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED)
            for item in self.assumptions_used
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "function_family": self.function_family,
            "function_order": self.function_order,
            "argument": self.argument,
            "expansion_point": self.expansion_point,
            "perturbation": self.perturbation,
            "pole_set": self.pole_set,
            "entire": self.entire,
            "predicates": [p.to_dict() for p in self.predicates],
            "domain_conditions": list(self.domain_conditions),
            "assumptions_used": [dict(x) for x in self.assumptions_used],
            "missing_assumptions": [dict(x) for x in self.missing_assumptions],
            "verdict": self.verdict,
            "neighborhood_verdict": self.neighborhood_verdict,
            "analyticity_certificate": dict(self.analyticity_certificate or {}),
            "distance_to_singularity": self.distance_to_singularity,
            "required_small_t_condition": self.required_small_t_condition,
            "proof_dependencies": list(self.proof_dependencies),
            "assumptions_hash": self.assumptions_hash,
            "argument_text_hash": self.argument_text_hash,
            "note": self.note,
            "method": self.method,
            "domain_usable_for_certified": self.domain_usable_for_certified,
        }

    def as_remainder_fields(self) -> dict[str, Any]:
        """Fields a remainder compiler may copy. Domain CERTIFIED is not remainder CERTIFIED."""
        if self.verdict == CERTIFIED:
            rem_verdict = UNKNOWN
            note = (
                "domain certified from A/B; remainder bound not this package; "
                + _NOTE
            )
        else:
            rem_verdict = self.verdict
            note = self.note
        return {
            "function_family": "polygamma",
            "function_order": self.function_order,
            "argument": self.argument,
            "expansion_point": self.expansion_point,
            "perturbation": self.perturbation,
            "domain_conditions": list(self.domain_conditions),
            "analyticity_certificate": dict(self.analyticity_certificate or {}),
            "distance_to_singularity": self.distance_to_singularity,
            "required_small_t_condition": self.required_small_t_condition,
            "assumptions_used": [dict(x) for x in self.assumptions_used],
            "proof_dependencies": list(self.proof_dependencies),
            "verdict": rem_verdict,
            "neighborhood_verdict": self.neighborhood_verdict,
            "assumptions_hash": self.assumptions_hash,
            "argument_text_hash": self.argument_text_hash,
            "method_version": METHOD,
            "note": note,
        }


def order_is_entire(k: Any) -> Optional[bool]:
    """True iff integer ``k <= -2``; False iff integer ``k >= -1``; else None."""
    n = _as_int(k)
    if n is None:
        return None
    return n <= -2


def pole_set_of_order(k: Any) -> str:
    entire = order_is_entire(k)
    if entire is True:
        return POLE_SET_EMPTY
    if entire is False:
        return POLE_SET_Z_LE_0
    return POLE_SET_UNKNOWN


def motivating_affine_z0(sign: Any = 1) -> Optional[sympy.Expr]:
    """``(beta*gamma ± I*beta*mu ∓ I*beta*epsilon + pi)/(2*pi)``.

    Free real symbols only (``real=True``). Not positive, not nonzero.
    ``sign`` is ``+1`` or ``-1``.
    """
    s = _as_int(sign)
    if s not in (1, -1):
        return None
    beta, gamma, mu, epsilon = sympy.symbols(
        "beta gamma mu epsilon", real=True
    )
    return (
        beta * gamma
        + s * sympy.I * beta * mu
        - s * sympy.I * beta * epsilon
        + sympy.pi
    ) / (2 * sympy.pi)


def classify_motivating_form(
    sign: Any = 1,
    *,
    k: Any = 0,
    c: Any = 1,
    t: Any = None,
    declared_assumptions: Any = None,
) -> DomainReport:
    """Domain query for the motivating affine class under given declarations."""
    z0 = motivating_affine_z0(sign)
    if z0 is None:
        return _fail(k, None, c, t, declared_assumptions, extra="sign")
    return classify_polygamma_domain(
        k, z0, c, t, declared_assumptions=declared_assumptions
    )


def classify_polygamma_domain(
    k: Any,
    z0: Any,
    c: Any = None,
    t: Any = None,
    *,
    declared_assumptions: Any = None,
) -> DomainReport:
    """Classify analyticity of ``polygamma(k, z0 + c t)`` near ``t = 0``.

    Verdicts:
    - CERTIFIED: pole-free neighborhood from A/B (usable for remainder CERTIFIED)
    - ASSUMPTION_REQUIRED: needs undeclared C/D (never silently inserted)
    - NONANALYTIC: ``z0`` identically a pole of this order
    - UNKNOWN: unparsed or unproved
    """
    try:
        return _classify(k, z0, c, t, declared_assumptions)
    except Exception:
        return _fail(k, z0, c, t, declared_assumptions, extra="exception")


def _classify(
    k: Any,
    z0: Any,
    c: Any,
    t: Any,
    declared_raw: Any,
) -> DomainReport:
    declared_items, declared_names, declared_classes = _parse_declared(
        declared_raw
    )
    k_e = _as_int(k)
    z0_e = _as_expr(z0)
    c_e = _as_expr(c) if c is not None else None
    t_e = _as_expr(t) if t is not None else None
    if z0_e is None:
        return _fail(k, z0, c, t, declared_raw, extra="unparsed_z0")
    if _too_large(z0_e) or (c_e is not None and _too_large(c_e)):
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="size_guard")
    if _nonfinite_expr(z0_e) or (c_e is not None and _nonfinite_expr(c_e)):
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="nonfinite")
    if isinstance(z0_e, (sympy.Float, float)) or (
        c_e is not None and isinstance(c_e, (sympy.Float, float))
    ):
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="float")
    if t_e is not None and z0_e.has(t_e):
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="z0_depends_on_t")
    if t_e is not None and c_e is not None and c_e.has(t_e):
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="c_depends_on_t")
    if k_e is None:
        return _fail(k, z0_e, c_e, t_e, declared_raw, extra="unknown_order")

    entire = k_e <= -2
    pole_set = POLE_SET_EMPTY if entire else POLE_SET_Z_LE_0
    z0_c = _canon(z0_e)
    used: list[dict[str, Any]] = []
    missing: list[dict[str, Any]] = []
    preds: list[DomainPredicate] = []
    deps: list[str] = [REF_DLMF_POLES, REF_DLMF_CHAIN]
    if k_e == -1:
        deps.append(REF_SYMPY_LOGGAMMA)
    if entire:
        deps.append(REF_SYMPY_ENTIRE)
        deps.append(REF_SYMPY_EVAL_ZOO)

    if entire:
        preds.append(
            DomainPredicate(
                PRED_ENTIRE,
                TRUE,
                formula=f"k={k_e}",
                proof=REF_SYMPY_ENTIRE,
                assumption_class=B_DERIVED,
            )
        )
        used.append(_item(B_DERIVED, PRED_ENTIRE))
        dist_txt = "oo"
        small_t = "any finite t (entire)"
        neigh = NEIGHBORHOOD_CERTIFIED
        conditions = ("entire",)
        preds.append(
            DomainPredicate(
                PRED_IDENTICALLY_POLE,
                FALSE,
                formula=str(z0_c),
                proof="empty pole set",
                assumption_class=B_DERIVED,
            )
        )
        preds.append(
            DomainPredicate(
                PRED_NEIGHBORHOOD,
                TRUE,
                formula=_affine_formula(z0_c, c_e, t_e),
                proof="entire",
                assumption_class=B_DERIVED,
            )
        )
        used.append(_item(B_DERIVED, PRED_NEIGHBORHOOD))
        verdict = CERTIFIED
        ident_pole = FALSE
        im_st = UNPROVED
        dist_st = TRUE
        return _finish(
            k_e,
            z0_c,
            c_e,
            t_e,
            pole_set=pole_set,
            entire=True,
            predicates=preds,
            conditions=conditions,
            used=used,
            missing=missing,
            declared_items=declared_items,
            verdict=verdict,
            neighborhood_verdict=neigh,
            dist_txt=dist_txt,
            small_t=small_t,
            deps=deps,
            ident_pole=ident_pole,
            im_st=im_st,
            dist_st=dist_st,
        )

    declared_exclusion = PRED_POLE_EXCLUSION in declared_names
    declared_im = PRED_IM_NONZERO in declared_names
    declared_dist = PRED_DIST_POS in declared_names
    declared_pos = PRED_POSITIVE in declared_names
    used_c_or_d = any(
        declared_classes.get(name) in (C_GENERICITY, D_HUMAN_REQUIRED)
        for name in (
            PRED_POLE_EXCLUSION,
            PRED_IM_NONZERO,
            PRED_DIST_POS,
            PRED_POSITIVE,
        )
        if name in declared_names
    )

    ident_pole, ident_proof = _identically_pole_status(z0_c)
    im_st, im_expr, im_proof = _im_nonzero_status(z0_c)
    if declared_im and not used_c_or_d:
        im_st = TRUE
        im_proof = "declared A: Im(z0) identically nonzero"
        used.append(_item(A_DECLARED, PRED_IM_NONZERO))
    elif im_st == TRUE:
        used.append(_item(B_DERIVED, PRED_IM_NONZERO))

    pos_flag = z0_c.is_positive is True or declared_pos
    if declared_pos and not used_c_or_d:
        used.append(_item(A_DECLARED, PRED_POSITIVE))
    elif z0_c.is_positive is True:
        used.append(_item(A_DECLARED, "z0.is_positive (symbol flag)"))

    dist_st, dist_txt, dist_proof = _dist_status(
        z0_c, ident_pole=ident_pole, im_st=im_st, im_expr=im_expr, pos=pos_flag
    )
    if declared_exclusion and not used_c_or_d:
        dist_st = TRUE
        dist_proof = "declared A: z0 not in Z_<=0"
        if dist_txt in ("", "unproved"):
            dist_txt = ">0 (declared pole-exclusion)"
        used.append(_item(A_DECLARED, PRED_POLE_EXCLUSION))
    elif declared_dist and not used_c_or_d:
        dist_st = TRUE
        dist_proof = "declared A: dist(z0, Z_<=0) certified positive"
        if dist_txt in ("", "unproved"):
            dist_txt = ">0 (declared)"
        used.append(_item(A_DECLARED, PRED_DIST_POS))
    elif dist_st == TRUE and PRED_DIST_POS not in {u.get("predicate") for u in used}:
        used.append(_item(B_DERIVED, PRED_DIST_POS))

    preds.append(
        DomainPredicate(
            PRED_IDENTICALLY_POLE,
            ident_pole,
            formula=str(z0_c),
            proof=ident_proof,
            assumption_class=B_DERIVED if ident_pole != UNPROVED else "",
        )
    )
    not_ident = (
        TRUE
        if ident_pole == FALSE
        else FALSE
        if ident_pole == TRUE
        else UNPROVED
    )
    preds.append(
        DomainPredicate(
            PRED_NOT_IDENTICALLY_POLE,
            not_ident,
            formula=str(z0_c),
            proof=(
                "not identically a pole is not pole-exclusion; "
                "do not insert genericity"
                if not_ident == TRUE
                else ident_proof
            ),
            assumption_class=B_DERIVED if not_ident != UNPROVED else "",
        )
    )
    if not_ident == TRUE:
        used.append(_item(B_DERIVED, PRED_NOT_IDENTICALLY_POLE))
    preds.append(
        DomainPredicate(
            PRED_IM_NONZERO,
            im_st,
            formula=str(im_expr) if im_expr is not None else f"Im({z0_c})",
            proof=im_proof,
            assumption_class=(
                A_DECLARED
                if declared_im and not used_c_or_d
                else B_DERIVED
                if im_st == TRUE
                else ""
            ),
        )
    )
    preds.append(
        DomainPredicate(
            PRED_DIST_POS,
            dist_st,
            formula=dist_txt,
            proof=dist_proof,
            assumption_class=(
                A_DECLARED
                if (declared_exclusion or declared_dist) and not used_c_or_d
                else B_DERIVED
                if dist_st == TRUE
                else ""
            ),
        )
    )

    pole_free = dist_st == TRUE or im_st == TRUE
    if ident_pole == TRUE:
        verdict = NONANALYTIC
        neigh = NEIGHBORHOOD_UNKNOWN
        conditions = (PRED_IDENTICALLY_POLE,)
        small_t = "no delta: t=0 sits on a pole"
        neigh_st = FALSE
        neigh_proof = "path hits a pole at t=0"
        if dist_txt in ("", "unproved"):
            dist_txt = "0"
    elif used_c_or_d and pole_free:
        verdict = ASSUMPTION_REQUIRED
        neigh = NEIGHBORHOOD_ASSUMPTION
        conditions = (
            "pole-exclusion tagged class C/D; cannot mint CERTIFIED",
        )
        small_t = "delta existence not certified under A/B"
        neigh_st = UNPROVED
        neigh_proof = "class C/D not usable for CERTIFIED"
        missing.append(
            _item(
                declared_classes.get(PRED_POLE_EXCLUSION)
                or declared_classes.get(PRED_IM_NONZERO)
                or C_GENERICITY,
                PRED_POLE_EXCLUSION,
            )
        )
    elif pole_free:
        deps.append(REF_ISOLATED)
        used.append(_item(B_DERIVED, PRED_NEIGHBORHOOD))
        verdict = CERTIFIED
        neigh = NEIGHBORHOOD_CERTIFIED
        conditions = (PRED_POLE_EXCLUSION, PRED_NEIGHBORHOOD)
        small_t = _small_t_text(dist_txt, c_e)
        neigh_st = TRUE
        neigh_proof = REF_ISOLATED
    elif ident_pole == UNPROVED:
        verdict = UNKNOWN
        neigh = NEIGHBORHOOD_UNKNOWN
        conditions = ("unproved pole membership",)
        small_t = "delta existence unproved"
        neigh_st = UNPROVED
        neigh_proof = "unproved"
    else:
        verdict = ASSUMPTION_REQUIRED
        neigh = NEIGHBORHOOD_ASSUMPTION
        conditions = (
            PRED_NOT_IDENTICALLY_POLE + " (insufficient without pole-exclusion)",
        )
        small_t = (
            "delta existence not certified; needs declared "
            + PRED_POLE_EXCLUSION
        )
        neigh_st = UNPROVED
        neigh_proof = "genericity not inserted"
        missing.append(_item(C_GENERICITY, PRED_POLE_EXCLUSION))

    preds.append(
        DomainPredicate(
            PRED_NEIGHBORHOOD,
            neigh_st,
            formula=_affine_formula(z0_c, c_e, t_e),
            proof=neigh_proof,
            assumption_class=B_DERIVED if neigh_st == TRUE else "",
        )
    )

    return _finish(
        k_e,
        z0_c,
        c_e,
        t_e,
        pole_set=pole_set,
        entire=False,
        predicates=preds,
        conditions=conditions,
        used=_dedupe_items(used),
        missing=_dedupe_items(missing),
        declared_items=declared_items,
        verdict=verdict,
        neighborhood_verdict=neigh,
        dist_txt=dist_txt,
        small_t=small_t,
        deps=deps,
        ident_pole=ident_pole,
        im_st=im_st,
        dist_st=dist_st,
    )


def _finish(
    k: int,
    z0: sympy.Expr,
    c: Optional[sympy.Expr],
    t: Optional[sympy.Expr],
    *,
    pole_set: str,
    entire: bool,
    predicates: list[DomainPredicate],
    conditions: tuple[str, ...],
    used: list[dict[str, Any]],
    missing: list[dict[str, Any]],
    declared_items: list[dict[str, Any]],
    verdict: str,
    neighborhood_verdict: str,
    dist_txt: str,
    small_t: str,
    deps: list[str],
    ident_pole: str,
    im_st: str,
    dist_st: str,
) -> DomainReport:
    if verdict == CERTIFIED and any(
        it.get("class") in (C_GENERICITY, D_HUMAN_REQUIRED) for it in used
    ):
        verdict = ASSUMPTION_REQUIRED
        neighborhood_verdict = NEIGHBORHOOD_ASSUMPTION
    if not conditions:
        conditions = ("stated",)
        if verdict == CERTIFIED:
            verdict = UNKNOWN
            neighborhood_verdict = NEIGHBORHOOD_UNKNOWN
    arg = _affine_formula(z0, c, t)
    perturb = _perturbation(c, t)
    used_t = tuple(_dedupe_items(used))
    cert = {
        "domain_verdict": verdict,
        "pole_set": pole_set,
        "order_class": "entire" if entire else "meromorphic_Z_le_0",
        "identically_pole": ident_pole,
        "im_identically_nonzero": im_st,
        "dist_certified_positive": dist_st,
        "not_identically_pole_is_not_exclusion": True,
        "references": list(deps),
        "sympy_eval_zoo_not_used": True,
    }
    return DomainReport(
        function_family="polygamma",
        function_order=str(k),
        argument=arg,
        expansion_point=str(z0),
        perturbation=perturb,
        pole_set=pole_set,
        entire=entire,
        predicates=tuple(predicates),
        domain_conditions=tuple(conditions),
        assumptions_used=used_t,
        missing_assumptions=tuple(_dedupe_items(missing)),
        verdict=verdict,
        neighborhood_verdict=neighborhood_verdict,
        analyticity_certificate=cert,
        distance_to_singularity=dist_txt,
        required_small_t_condition=small_t,
        proof_dependencies=tuple(deps),
        assumptions_hash=_hash_obj(
            {"used": list(used_t), "declared": declared_items}
        ),
        argument_text_hash=_hash_obj(
            {"k": str(k), "z0": str(z0), "c": str(c), "t": str(t)}
        ),
        note=_NOTE,
        method=METHOD,
    )


def _fail(
    k: Any,
    z0: Any,
    c: Any,
    t: Any,
    declared_raw: Any,
    *,
    extra: str,
) -> DomainReport:
    declared_items, _, _ = _parse_declared(declared_raw)
    note = f"{_NOTE} ({extra})"
    return DomainReport(
        function_family="polygamma",
        function_order=_s(k) or "",
        argument=_s(z0) or "",
        expansion_point=_s(z0) or "",
        perturbation=_perturbation(c if isinstance(c, sympy.Expr) else None, t if isinstance(t, sympy.Expr) else None),
        pole_set=pole_set_of_order(k),
        entire=False,
        predicates=(),
        domain_conditions=(f"unproved:{extra}",),
        assumptions_used=(),
        missing_assumptions=(),
        verdict=UNKNOWN,
        neighborhood_verdict=NEIGHBORHOOD_UNKNOWN,
        analyticity_certificate={
            "domain_verdict": UNKNOWN,
            "reason": extra,
            "sympy_eval_zoo_not_used": True,
        },
        distance_to_singularity="",
        required_small_t_condition="",
        proof_dependencies=(),
        assumptions_hash=_hash_obj({"declared": declared_items}),
        argument_text_hash=_hash_obj(
            {"k": _s(k), "z0": _s(z0), "c": _s(c), "t": _s(t)}
        ),
        note=note,
        method=METHOD,
    )


def _identically_pole_status(z0: sympy.Expr) -> tuple[str, str]:
    if _proved_nonpositive_integer(z0):
        return TRUE, "proved nonpositive integer"
    if _proved_not_nonpositive_integer(z0):
        return FALSE, "proved not a nonpositive integer"
    if z0.free_symbols:
        return FALSE, "free symbols remain; not identically a constant pole"
    return UNPROVED, "constant not classified as a nonpositive integer"


def _proved_nonpositive_integer(z0: sympy.Expr) -> bool:
    if z0.is_integer is True and z0.is_nonpositive is True:
        return True
    if isinstance(z0, sympy.Integer) or z0.is_Integer is True:
        try:
            return int(z0) <= 0
        except Exception:
            return False
    if z0.is_rational is True and z0.is_integer is True:
        try:
            return int(z0) <= 0
        except Exception:
            return False
    for n in range(0, -K_ABS_CAP - 1, -1):
        if _identically_zero(z0 - sympy.Integer(n)):
            return True
    return False


def _proved_not_nonpositive_integer(z0: sympy.Expr) -> bool:
    if z0.is_positive is True:
        return True
    if z0.is_integer is False:
        return True
    if z0.is_rational is True and z0.is_integer is not True:
        try:
            if int(z0.q) != 1:
                return True
        except Exception:
            pass
    im_st, _, _ = _im_nonzero_status(z0)
    if im_st == TRUE:
        return True
    if isinstance(z0, sympy.Integer) or z0.is_Integer is True:
        try:
            return int(z0) > 0
        except Exception:
            return False
    if z0.is_integer is True and z0.is_positive is True:
        return True
    try:
        s = sympy.simplify(sympy.sin(sympy.pi * z0))
    except Exception:
        s = None
    if s is not None and _proved_nonzero(s):
        return True
    if s == 0 or (s is not None and s.is_zero is True):
        if z0.is_positive is True:
            return True
        if z0.is_nonpositive is True:
            return False
    return False


def _im_nonzero_status(
    z0: sympy.Expr,
) -> tuple[str, Optional[sympy.Expr], str]:
    try:
        im_e = sympy.simplify(sympy.im(sympy.expand(z0)))
    except Exception:
        return UNPROVED, None, "Im not computed"
    if not isinstance(im_e, sympy.Expr):
        return UNPROVED, None, "Im not an expr"
    if im_e.is_zero is True or _identically_zero(im_e):
        return FALSE, im_e, "Im identically 0"
    if _proved_nonzero(im_e):
        return TRUE, im_e, "Im proved nonzero"
    return UNPROVED, im_e, "Im not proved identically nonzero"


def _dist_status(
    z0: sympy.Expr,
    *,
    ident_pole: str,
    im_st: str,
    im_expr: Optional[sympy.Expr],
    pos: bool,
) -> tuple[str, str, str]:
    if ident_pole == TRUE:
        return FALSE, "0", "z0 is a pole"
    if im_st == TRUE:
        bound = f"|{im_expr}|" if im_expr is not None else "|Im(z0)|"
        return TRUE, f">= {bound}", "dist >= |Im(z0)| > 0"
    if pos:
        return TRUE, ">0 (z0 > 0)", "positive reals miss Z_<=0"
    if z0.is_integer is False:
        return TRUE, ">0 (not an integer)", "not in Z, hence not in Z_<=0"
    if isinstance(z0, sympy.Integer) or z0.is_Integer is True:
        try:
            n = int(z0)
        except Exception:
            return UNPROVED, "unproved", "integer value unparsed"
        if n <= 0:
            return FALSE, "0", "nonpositive integer"
        return TRUE, str(n), "dist to 0"
    if z0.is_rational is True:
        try:
            r = sympy.Rational(z0)
        except Exception:
            return UNPROVED, "unproved", "rational unparsed"
        d = _rational_dist(r)
        if d == 0:
            return FALSE, "0", "nonpositive integer"
        return TRUE, str(d), "exact distance to Z_<=0"
    return UNPROVED, "unproved", "dist(z0, Z_<=0) not certified"


def _rational_dist(r: sympy.Rational) -> sympy.Expr:
    if r > 0:
        return r
    n0 = sympy.floor(r)
    n1 = sympy.ceiling(r)
    cands = [n for n in (n0, n1, sympy.Integer(0)) if n <= 0]
    if not cands:
        return sympy.Abs(r)
    return min((sympy.Abs(r - n) for n in cands), key=lambda x: x)


def _small_t_text(dist_txt: str, c: Optional[sympy.Expr]) -> str:
    if c is not None and _identically_zero(c):
        return "path constant; z0 pole-free"
    return (
        "exists delta > 0 such that |t| < delta implies "
        "z0 + c t not in Z_<=0 (isolated poles; "
        f"delta <= ({dist_txt}) / max(1, |c|) for finite c)"
    )


def _parse_declared(
    raw: Any,
) -> tuple[list[dict[str, Any]], frozenset[str], dict[str, str]]:
    items: list[dict[str, Any]] = []
    names: set[str] = set()
    classes: dict[str, str] = {}
    if raw is None:
        return items, frozenset(), classes
    seq: list[Any]
    if isinstance(raw, dict):
        seq = [raw]
    elif isinstance(raw, (list, tuple)):
        seq = list(raw)
    else:
        seq = [raw]
    for entry in seq:
        if isinstance(entry, str):
            klass = A_DECLARED
            pred_raw = entry
        elif isinstance(entry, dict):
            klass = str(entry.get("class") or A_DECLARED)
            pred_raw = entry.get("predicate", "")
        else:
            continue
        if klass not in (
            A_DECLARED,
            B_DERIVED,
            C_GENERICITY,
            D_HUMAN_REQUIRED,
        ):
            klass = A_DECLARED
        name = _canonicalize_predicate_text(str(pred_raw))
        if not name:
            continue
        item = _item(klass, name)
        items.append(item)
        if klass == A_DECLARED:
            names.add(name)
        if name not in classes:
            classes[name] = klass
        elif klass in (C_GENERICITY, D_HUMAN_REQUIRED):
            classes[name] = klass
    return items, frozenset(names), classes


def _canonicalize_predicate_text(text: str) -> str:
    s = text.strip().lower()
    replacements = (
        ("α₀", "z0"),
        ("α0", "z0"),
        ("alpha_0", "z0"),
        ("alpha0", "z0"),
        ("−", "-"),
        ("–", "-"),
        ("—", "-"),
        ("⩽", "<="),
        ("≤", "<="),
        ("≠", "!="),
        ("…", "..."),
        ("mathbb{z}", "z"),
        ("z_{<=0}", "z_<=0"),
        ("non-positive", "nonpositive"),
    )
    for a, b in replacements:
        s = s.replace(a, b)
    compact = "".join(s.split())
    if "generic" in compact and "pole" in compact:
        return PRED_GENERICITY
    if "identically" in compact and (
        "z_<=0" in compact or "nonpositive" in compact or "{0,-1,-2" in compact
    ):
        return PRED_NOT_IDENTICALLY_POLE
    if compact in {
        "z0notinz_<=0",
        "z0notin{0,-1,-2,...}",
        "z0notin{0,-1,-2,}",
        "argumentnotapolygammapole",
        "z0notanonpositiveinteger",
        "z0avoidspoles",
        pred_compact(PRED_POLE_EXCLUSION),
    } or (
        compact.startswith("z0notin") and "identically" not in compact
    ):
        return PRED_POLE_EXCLUSION
    if compact in {
        "im(z0)!=0",
        "im(z0)identicallynonzero",
        "im(z0)nonzero",
        pred_compact(PRED_IM_NONZERO),
    } or compact.replace(" ", "") in {"im(z0)!=0"}:
        return PRED_IM_NONZERO
    if "dist" in compact and ("z_<=0" in compact or "pole" in compact):
        return PRED_DIST_POS
    if compact in {"z0>0", "z0positive", pred_compact(PRED_POSITIVE)}:
        return PRED_POSITIVE
    if "k<=-2" in compact or compact == pred_compact(PRED_ENTIRE):
        return PRED_ENTIRE
    return text.strip()


def pred_compact(name: str) -> str:
    return "".join(name.lower().split())


def _item(klass: str, predicate: str) -> dict[str, Any]:
    return {"class": klass, "predicate": predicate}


def _dedupe_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in items:
        key = (str(item.get("class")), str(item.get("predicate")))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _identically_zero(expr: sympy.Expr) -> bool:
    try:
        if expr == 0 or expr.is_zero is True:
            return True
        d = sympy.expand(expr)
        if d == 0 or d.is_zero is True:
            return True
        if d.equals(0) is True:
            return True
    except Exception:
        return False
    return False


def _proved_nonzero(expr: sympy.Expr) -> bool:
    if _identically_zero(expr):
        return False
    if expr.is_nonzero is True:
        return True
    if expr.free_symbols:
        if expr.is_Mul:
            parts = expr.args
        else:
            try:
                parts = sympy.Mul.make_args(sympy.together(expr))
            except Exception:
                parts = (expr,)
        if parts and all(_factor_nonzero(p) for p in parts):
            return True
        return False
    if _nonfinite_expr(expr):
        return False
    if expr.is_number is True and expr != 0:
        if isinstance(expr, (sympy.Float, float)):
            return False
        return True
    return False


def _factor_nonzero(expr: sympy.Expr) -> bool:
    if _identically_zero(expr):
        return False
    if expr.is_nonzero is True:
        return True
    if expr.free_symbols:
        return expr.is_nonzero is True
    if expr.is_number is True and expr != 0 and not _nonfinite_expr(expr):
        if isinstance(expr, (sympy.Float, float)):
            return False
        return True
    return False


def _canon(z0: sympy.Expr) -> sympy.Expr:
    try:
        out = sympy.expand(z0)
    except Exception:
        out = z0
    if isinstance(out, sympy.Expr):
        return out
    return z0


def _as_int(value: Any) -> Optional[int]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        n = value
    elif isinstance(value, sympy.Integer):
        n = int(value)
    else:
        return None
    if abs(n) > K_ABS_CAP:
        return None
    return n


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, sympy.Expr):
        if getattr(value, "is_Relational", False):
            return None
        return value
    if isinstance(value, str):
        if not value or len(value) > CHAR_CAP:
            return None
        try:
            n = int(value)
        except ValueError:
            return None
        return sympy.Integer(n)
    return None


def _too_large(expr: sympy.Expr) -> bool:
    try:
        return int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    except Exception:
        return True


def _nonfinite_expr(expr: sympy.Expr) -> bool:
    try:
        if any(expr == sentinel for sentinel in _NONFINITE):
            return True
        if expr.has(*_NONFINITE):
            return True
    except Exception:
        return True
    try:
        if getattr(expr, "is_infinite", None) is True:
            return True
    except Exception:
        return True
    return False


def _affine_formula(
    z0: sympy.Expr, c: Optional[sympy.Expr], t: Optional[sympy.Expr]
) -> str:
    if c is None and t is None:
        return str(z0)
    cs = str(c) if c is not None else "c"
    ts = str(t) if t is not None else "t"
    return f"({z0}) + ({cs})*({ts})"


def _perturbation(c: Optional[sympy.Expr], t: Optional[sympy.Expr]) -> str:
    if c is None and t is None:
        return "c*t"
    cs = str(c) if c is not None else "c"
    ts = str(t) if t is not None else "t"
    return f"{cs}*{ts}"


def _hash_obj(obj: Any) -> str:
    blob = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _s(expr: Any) -> Optional[str]:
    if expr is None:
        return None
    return str(expr)
