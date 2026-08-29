"""Existence of a pole-free disk about the affine path z0 + c t.

CERTIFIED_NEIGHBORHOOD is not remainder CERTIFIED and not hop ZERO.
Class-C/D pole-exclusion is not inserted. Existence of some delta is
enough; the explicit choice delta = rho / (2*(|c|+1)) is sufficient,
not optimal. If c = 0 the path is constant and the neighborhood is z0.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Callable, Optional

import sympy

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    D_HUMAN_REQUIRED,
    METHOD_VERSION,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    RemainderCertificate,
    UNKNOWN,
)

CERTIFIED_NEIGHBORHOOD = NEIGHBORHOOD_CERTIFIED
assert NEIGHBORHOOD_ASSUMPTION == ASSUMPTION_REQUIRED
assert NEIGHBORHOOD_UNKNOWN == UNKNOWN

NEIGHBORHOOD_VERDICTS = (
    CERTIFIED_NEIGHBORHOOD,
    ASSUMPTION_REQUIRED,
    UNKNOWN,
)

CHAR_CAP = 4096
OPS_CAP = 120
NEIGHBORHOOD_METHOD = "rc-neighborhood-1"

EMPTY_POLE_SET = "empty"
NONPOSITIVE_INTEGERS = "nonpositive_integers"

EMPTY_FAMILIES = frozenset({"exp", "entire", "exponential"})
NONPOS_FAMILIES = frozenset(
    {"", "polygamma", "gamma", "digamma", "trigamma", "loggamma", "psi", "pg"}
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

_PARSE_LOCAL: dict[str, Any] = {
    "pi": sympy.pi,
    "I": sympy.I,
    "E": sympy.E,
    "oo": sympy.oo,
    "exp": sympy.exp,
    "log": sympy.log,
    "sin": sympy.sin,
    "cos": sympy.cos,
    "sqrt": sympy.sqrt,
    "Abs": sympy.Abs,
    "re": sympy.re,
    "im": sympy.im,
    "Integer": sympy.Integer,
    "Rational": sympy.Rational,
}

PoleSetCallback = Callable[[Any], Any]


@dataclass(frozen=True)
class PoleQuery:
    """Classification of z0 against a pole set. R2 may return this."""

    kind: str
    distance: str = ""
    isolated: bool = True
    name: str = ""
    note: str = ""


@dataclass
class NeighborhoodCertificate:
    """Existence certificate for a pole-free affine neighborhood."""

    verdict: str = UNKNOWN
    z0: str = ""
    c: str = ""
    function_family: str = ""
    pole_set: str = ""
    distance_to_singularity: str = ""
    sufficient_delta: str = ""
    required_small_t_condition: str = ""
    domain_conditions: list[str] = field(default_factory=list)
    assumptions_used: list[dict[str, Any]] = field(default_factory=list)
    proof_dependencies: list[str] = field(default_factory=list)
    assumptions_hash: str = ""
    analyticity_certificate: dict[str, Any] = field(default_factory=dict)
    method_version: str = METHOD_VERSION
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def apply_to_remainder(
        self, cert: Optional[RemainderCertificate] = None
    ) -> RemainderCertificate:
        """Fill neighborhood fields. Never mints remainder CERTIFIED or hop ZERO."""
        base = cert if cert is not None else RemainderCertificate()
        return replace(
            base,
            neighborhood_verdict=self.verdict,
            expansion_point=self.z0 or base.expansion_point,
            perturbation=self.c if self.c != "" else base.perturbation,
            function_family=self.function_family or base.function_family,
            domain_conditions=list(self.domain_conditions),
            analyticity_certificate=dict(self.analyticity_certificate),
            distance_to_singularity=self.distance_to_singularity,
            required_small_t_condition=self.required_small_t_condition,
            assumptions_used=list(self.assumptions_used),
            proof_dependencies=list(self.proof_dependencies),
            assumptions_hash=self.assumptions_hash or base.assumptions_hash,
            note=self.note or base.note,
        )


def empty_pole_set(_z0: Any = None) -> PoleQuery:
    """Entire family: no finite poles (default for exp)."""
    return PoleQuery(
        kind="regular",
        distance="oo",
        isolated=True,
        name=EMPTY_POLE_SET,
        note="empty pole set",
    )


def nonpositive_integer_poles(z0: Any) -> PoleQuery:
    """Default meromorphic poles {0,-1,-2,...}. R2 may replace this."""
    expr = _as_expr(z0)
    if expr is None:
        return PoleQuery(
            kind="unknown",
            isolated=True,
            name=NONPOSITIVE_INTEGERS,
            note="unparsed z0",
        )
    return _query_nonpositive_integers(expr)


def default_pole_set(function_family: str = "") -> PoleSetCallback:
    """Select the shipped default callback for a function family."""
    fam = str(function_family or "").strip().lower()
    if fam in EMPTY_FAMILIES:
        return empty_pole_set
    if fam in NONPOS_FAMILIES:
        return nonpositive_integer_poles
    return _unsupported_pole_set


def explicit_sufficient_delta(rho: Any, c: Any) -> sympy.Expr:
    """Sufficient (not optimal) delta: rho / (2*(|c|+1)); 1 if rho = oo."""
    if rho is None:
        return sympy.Integer(1)
    if rho in (sympy.oo, sympy.S.Infinity, "oo"):
        return sympy.Integer(1)
    rho_e = rho if isinstance(rho, sympy.Expr) else _as_expr(rho)
    c_e = c if isinstance(c, sympy.Expr) else _as_expr(c)
    if rho_e is None or c_e is None:
        return sympy.Integer(1)
    return sympy.simplify(rho_e / (2 * (sympy.Abs(c_e) + 1)))


def certify_neighborhood(
    z0: Any,
    c: Any = 0,
    *,
    assumptions: Any = None,
    pole_set: Any = None,
    function_family: str = "",
) -> NeighborhoodCertificate:
    """Certify existence of delta > 0 with z0 + c t pole-free for |t| < delta."""
    fam = str(function_family or "")
    try:
        return _sanitize(_certify(z0, c, assumptions, pole_set, fam))
    except Exception as exc:
        return _sanitize(
            _fail(
                UNKNOWN,
                z0,
                c,
                fam,
                pole_name="",
                note=f"error:{type(exc).__name__}",
                domain=["neighborhood proof failed"],
            )
        )


def _unsupported_pole_set(_z0: Any = None) -> PoleQuery:
    return PoleQuery(kind="unknown", isolated=False, name="unsupported", note="unknown family")


def _certify(
    z0: Any,
    c: Any,
    assumptions: Any,
    pole_set: Any,
    function_family: str,
) -> NeighborhoodCertificate:
    z_expr = _as_expr(z0)
    c_expr = _as_expr(0 if c is None else c)
    if z_expr is None or c_expr is None:
        return _fail(
            UNKNOWN,
            z0,
            c,
            function_family,
            pole_name="",
            note="unparsed z0 or c",
            domain=["unparsed affine path"],
        )
    if _too_large(z_expr) or _too_large(c_expr):
        return _fail(
            UNKNOWN,
            z_expr,
            c_expr,
            function_family,
            pole_name="",
            note="size_guard",
            domain=["size_guard"],
        )
    if _nonfinite(z_expr) or _nonfinite(c_expr):
        return _fail(
            UNKNOWN,
            z_expr,
            c_expr,
            function_family,
            pole_name="",
            note="nonfinite z0 or c",
            domain=["nonfinite affine path"],
        )

    callback, pole_name, pole_known = _resolve_pole_set(pole_set, function_family)
    facts = _declared_facts(assumptions)
    if not pole_known:
        return _fail(
            UNKNOWN,
            z_expr,
            c_expr,
            function_family,
            pole_name=pole_name,
            note="unsupported pole set",
            domain=["unknown pole set"],
            facts=facts,
        )

    query = _run_pole_query(callback, z_expr, pole_name)
    pole_name = query.name or pole_name
    isolated = bool(query.isolated)

    if query.kind == "pole":
        return _fail(
            UNKNOWN,
            z_expr,
            c_expr,
            function_family,
            pole_name=pole_name,
            note="z0 is a pole; no pole-free disk about z0",
            domain=[f"z0 in pole set {pole_name}"],
            facts=facts,
            rho="0",
            proof=["z0 is a pole"],
        )

    rho_kind, rho_value = _combine_distance(query, facts, pole_name, isolated)
    uses_exclusion = query.kind != "regular"
    used = _assumptions_for_verdict(facts, pole_name, uses_exclusion, rho_kind)

    if rho_kind in ("explicit", "infinity", "existence"):
        return _certified(
            z_expr,
            c_expr,
            function_family,
            pole_name=pole_name,
            rho_kind=rho_kind,
            rho_value=rho_value,
            used=used,
            query=query,
            facts=facts,
        )

    if facts.has_cd:
        return _fail(
            ASSUMPTION_REQUIRED,
            z_expr,
            c_expr,
            function_family,
            pole_name=pole_name,
            note="class-C/D pole-exclusion is not a certificate",
            domain=[f"pole-exclusion for {pole_name} not a class-A/B fact"],
            facts=facts,
            proof=["class C/D may not be used to certify a neighborhood"],
        )
    if facts.has_unrecognized_a:
        return _fail(
            UNKNOWN,
            z_expr,
            c_expr,
            function_family,
            pole_name=pole_name,
            note="declared assumption not usable as pole-exclusion",
            domain=["declared domain hypothesis unproved"],
            facts=facts,
        )
    return _fail(
        ASSUMPTION_REQUIRED,
        z_expr,
        c_expr,
        function_family,
        pole_name=pole_name,
        note="symbolic z0 has no declared pole-exclusion",
        domain=[f"need z0 not in pole set {pole_name} (class C unless declared)"],
        facts=facts,
        proof=["pole-exclusion is class C when not declared"],
    )


def _certified(
    z_expr: sympy.Expr,
    c_expr: sympy.Expr,
    function_family: str,
    *,
    pole_name: str,
    rho_kind: str,
    rho_value: Any,
    used: list[dict[str, Any]],
    query: PoleQuery,
    facts: "_DeclaredFacts",
) -> NeighborhoodCertificate:
    constant = _is_zero(c_expr) is True
    proof = list(query.note and [query.note] or [])
    if pole_name == EMPTY_POLE_SET or rho_kind == "infinity":
        rho_str = "oo"
        delta_str = "1"
        domain = ["entire"]
        proof.extend(
            [
                "empty pole set",
                "any delta > 0 works; sufficient choice delta = 1",
            ]
        )
        argument = (
            "empty pole set: f is entire (or has no finite poles), so the "
            "affine path z0 + c t stays analytic for every t"
        )
        kind = "entire"
    else:
        if rho_kind == "explicit":
            rho_e = rho_value if isinstance(rho_value, sympy.Expr) else _as_expr(rho_value)
            if rho_e is None or not _is_positive(rho_e):
                return _fail(
                    UNKNOWN,
                    z_expr,
                    c_expr,
                    function_family,
                    pole_name=pole_name,
                    note="rho not proved positive",
                    domain=["distance to pole set unproved"],
                    facts=facts,
                )
            rho_str = _expr_str(rho_e)
            delta_e = explicit_sufficient_delta(rho_e, c_expr)
            delta_str = _expr_str(delta_e)
            domain = [f"disk |z - ({_expr_str(z_expr)})| < {rho_str} is pole-free"]
            proof.append(f"dist(z0, {pole_name}) = {rho_str} > 0")
            proof.append(
                f"delta = rho/(2*(|c|+1)) = {delta_str} satisfies |c|*delta < rho"
            )
            argument = (
                f"|z0 + c t - z0| = |c||t| < |c|*({delta_str}) < {rho_str}, "
                "so the path stays in the pole-free disk"
            )
        else:
            rho_str = ">0"
            delta_str = "rho/(2*(Abs(c)+1)) with rho=dist(z0,pole_set)>0"
            domain = [
                f"z0 not in {pole_name}; poles isolated ⇒ pole-free disk of some rho > 0"
            ]
            proof.append(
                f"{pole_name} is discrete and closed, so z0 not a pole implies dist > 0"
            )
            proof.append("delta = rho/(2*(|c|+1)) is a sufficient choice")
            argument = (
                "isolated poles and z0 not a pole give rho > 0; "
                "any 0 < |c|*delta < rho keeps the affine path inside the disk"
            )
        kind = "pole_free_disk"

    if constant:
        domain.append("c = 0: path is constant; neighborhood reduces to z0")
        proof.append("c = 0: path is z0 itself")
        argument = (
            "c = 0: the path is the point z0, which lies in a pole-free "
            "neighborhood of itself"
        )
        kind = "constant_path" if kind != "entire" else kind

    used = list(used)
    if rho_kind == "existence" or (used and pole_name != EMPTY_POLE_SET):
        if not any(item.get("class") == B_DERIVED for item in used):
            if rho_kind == "existence":
                used.append(
                    {
                        "class": B_DERIVED,
                        "predicate": (
                            f"{pole_name} discrete closed ⇒ "
                            "z0 not a pole implies dist(z0, pole_set) > 0"
                        ),
                    }
                )

    analytic = {
        "status": "proved",
        "kind": kind,
        "method": NEIGHBORHOOD_METHOD,
        "center": _expr_str(z_expr),
        "path": "z0 + c t",
        "radius": rho_str,
        "sufficient_delta": delta_str,
        "pole_set": pole_name,
        "argument": argument,
        "constant_path": constant,
    }
    small_t = (
        "any t (constant path)"
        if constant and kind != "entire"
        else f"|t| < {delta_str}"
    )
    return NeighborhoodCertificate(
        verdict=CERTIFIED_NEIGHBORHOOD,
        z0=_expr_str(z_expr),
        c=_expr_str(c_expr),
        function_family=function_family,
        pole_set=pole_name,
        distance_to_singularity=rho_str,
        sufficient_delta=delta_str,
        required_small_t_condition=small_t,
        domain_conditions=domain,
        assumptions_used=used,
        proof_dependencies=proof,
        assumptions_hash=_hash_assumptions(used),
        analyticity_certificate=analytic,
        method_version=METHOD_VERSION,
        note="existence of delta, not an optimal delta",
    )


def _fail(
    verdict: str,
    z0: Any,
    c: Any,
    function_family: str,
    *,
    pole_name: str,
    note: str,
    domain: list[str],
    facts: Optional["_DeclaredFacts"] = None,
    rho: str = "",
    proof: Optional[list[str]] = None,
) -> NeighborhoodCertificate:
    used: list[dict[str, Any]] = []
    if facts is not None:
        if verdict == ASSUMPTION_REQUIRED:
            used = list(facts.cd_items) or list(facts.declared_items)
            if not used:
                used = [
                    {
                        "class": C_GENERICITY,
                        "predicate": (
                            f"z0 not in pole set {pole_name or 'P'} "
                            "(not declared; not inserted)"
                        ),
                    }
                ]
        elif facts.declared_items:
            used = list(facts.declared_items)
    analytic = {
        "status": "missing" if verdict == UNKNOWN else "assumption_required",
        "kind": "missing",
        "method": NEIGHBORHOOD_METHOD,
        "pole_set": pole_name,
        "reason": note,
    }
    return NeighborhoodCertificate(
        verdict=verdict,
        z0=_expr_str(z0) if isinstance(z0, sympy.Basic) else str(z0),
        c=_expr_str(c) if isinstance(c, sympy.Basic) else str(c if c is not None else 0),
        function_family=function_family,
        pole_set=pole_name,
        distance_to_singularity=rho,
        sufficient_delta="",
        required_small_t_condition="",
        domain_conditions=list(domain) or ["neighborhood not certified"],
        assumptions_used=used,
        proof_dependencies=list(proof or []),
        assumptions_hash=_hash_assumptions(used),
        analyticity_certificate=analytic,
        method_version=METHOD_VERSION,
        note=note,
    )


def _sanitize(cert: NeighborhoodCertificate) -> NeighborhoodCertificate:
    if not cert.domain_conditions:
        cert.domain_conditions = ["neighborhood not certified"]
        if cert.verdict == CERTIFIED_NEIGHBORHOOD:
            cert.verdict = UNKNOWN
            cert.note = "empty domain_conditions"
    if cert.verdict == CERTIFIED_NEIGHBORHOOD and _uses_cd(cert.assumptions_used):
        cert.verdict = ASSUMPTION_REQUIRED
        cert.note = "class-C/D cannot certify a neighborhood"
        cert.analyticity_certificate = dict(cert.analyticity_certificate)
        cert.analyticity_certificate["status"] = "assumption_required"
    if cert.verdict not in NEIGHBORHOOD_VERDICTS:
        cert.verdict = UNKNOWN
    if cert.verdict == CERTIFIED_NEIGHBORHOOD and not cert.assumptions_hash:
        cert.assumptions_hash = _hash_assumptions(cert.assumptions_used)
    return cert


def _uses_cd(items: list[dict[str, Any]]) -> bool:
    for item in items:
        if isinstance(item, dict) and item.get("class") in (
            C_GENERICITY,
            D_HUMAN_REQUIRED,
        ):
            return True
    return False


def _resolve_pole_set(
    pole_set: Any, function_family: str
) -> tuple[PoleSetCallback, str, bool]:
    if callable(pole_set):
        name = getattr(pole_set, "__name__", "custom")
        if name == "empty_pole_set":
            return pole_set, EMPTY_POLE_SET, True
        if name == "nonpositive_integer_poles":
            return pole_set, NONPOSITIVE_INTEGERS, True
        if name == "_unsupported_pole_set":
            return pole_set, "unsupported", False
        return pole_set, str(name), True
    if isinstance(pole_set, str) and pole_set.strip():
        key = pole_set.strip().lower()
        if key in {"empty", "exp", "entire", "exponential"}:
            return empty_pole_set, EMPTY_POLE_SET, True
        if key in {
            "nonpositive_integers",
            "z_<=0",
            "z<=0",
            NONPOSITIVE_INTEGERS,
            "polygamma",
        }:
            return nonpositive_integer_poles, NONPOSITIVE_INTEGERS, True
        return _unsupported_pole_set, key, False
    cb = default_pole_set(function_family)
    fam = str(function_family or "").strip().lower()
    if cb is empty_pole_set:
        return cb, EMPTY_POLE_SET, True
    if cb is nonpositive_integer_poles:
        return cb, NONPOSITIVE_INTEGERS, True
    return cb, fam or "unsupported", False


def _run_pole_query(callback: PoleSetCallback, z_expr: sympy.Expr, pole_name: str) -> PoleQuery:
    raw = callback(z_expr)
    return _as_pole_query(raw, pole_name)


def _as_pole_query(raw: Any, default_name: str) -> PoleQuery:
    if isinstance(raw, PoleQuery):
        if raw.name:
            return raw
        return PoleQuery(
            kind=raw.kind,
            distance=raw.distance,
            isolated=raw.isolated,
            name=default_name,
            note=raw.note,
        )
    if isinstance(raw, dict):
        kind = str(raw.get("kind") or "unknown")
        dist = raw.get("distance", "")
        dist_s = "" if dist is None else str(dist)
        isolated = bool(raw.get("isolated", True))
        name = str(raw.get("name") or default_name)
        note = str(raw.get("note") or "")
        return PoleQuery(
            kind=kind, distance=dist_s, isolated=isolated, name=name, note=note
        )
    return PoleQuery(kind="unknown", name=default_name, note="malformed pole_set result")


def _query_nonpositive_integers(z: sympy.Expr) -> PoleQuery:
    name = NONPOSITIVE_INTEGERS
    isolated = True
    try:
        z_s = sympy.simplify(sympy.expand(z))
    except Exception:
        return PoleQuery(kind="unknown", isolated=isolated, name=name, note="simplify failed")
    if _nonfinite(z_s) or _has_float(z_s):
        return PoleQuery(kind="unknown", isolated=isolated, name=name, note="inexact or nonfinite")
    if _too_large(z_s):
        return PoleQuery(kind="unknown", isolated=isolated, name=name, note="size_guard")

    if not z_s.free_symbols:
        kind, rho = _classify_number_vs_nonpos(z_s)
        if kind == "pole":
            return PoleQuery(
                kind="pole",
                distance="0",
                isolated=isolated,
                name=name,
                note="z0 is a nonpositive integer",
            )
        if kind == "regular" and rho is not None:
            return PoleQuery(
                kind="regular",
                distance=_expr_str(rho),
                isolated=isolated,
                name=name,
                note=f"dist(z0, Z_<=0) = {_expr_str(rho)}",
            )
        return PoleQuery(kind="unknown", isolated=isolated, name=name, note="number unproved")

    re_z, im_z = _parts(z_s)
    re_num = _is_exact_number(re_z)
    im_num = _is_exact_number(im_z)
    if re_num and im_num:
        kind, rho = _classify_parts_vs_nonpos(re_z, im_z)
        if kind == "pole":
            return PoleQuery(
                kind="pole",
                distance="0",
                isolated=isolated,
                name=name,
                note="z0 is a nonpositive integer",
            )
        if kind == "regular" and rho is not None:
            return PoleQuery(
                kind="regular",
                distance=_expr_str(rho),
                isolated=isolated,
                name=name,
                note=f"dist(z0, Z_<=0) = {_expr_str(rho)}",
            )

    if re_num:
        re_kind = _is_nonpositive_integer(re_z)
        if re_kind is False:
            rho = _real_dist_to_nonpos(re_z)
            if rho is not None and _is_positive(rho):
                return PoleQuery(
                    kind="regular",
                    distance=_expr_str(rho),
                    isolated=isolated,
                    name=name,
                    note="Re(z0) not in Z_<=0; rho >= dist_R(Re(z0), Z_<=0)",
                )
        if re_kind is True:
            im_zero = _is_zero(im_z)
            if im_zero is True:
                return PoleQuery(
                    kind="pole",
                    distance="0",
                    isolated=isolated,
                    name=name,
                    note="z0 is a nonpositive integer",
                )
            if im_num and _is_zero(im_z) is False and _is_positive(sympy.Abs(im_z)):
                return PoleQuery(
                    kind="regular",
                    distance=_expr_str(sympy.Abs(im_z)),
                    isolated=isolated,
                    name=name,
                    note="Re(z0) in Z_<=0 but Im(z0) != 0",
                )

    return PoleQuery(
        kind="unknown",
        isolated=isolated,
        name=name,
        note="symbolic z0 vs Z_<=0 unproved",
    )


def _classify_number_vs_nonpos(z: sympy.Expr) -> tuple[str, Optional[sympy.Expr]]:
    re_z, im_z = _parts(z)
    return _classify_parts_vs_nonpos(re_z, im_z)


def _classify_parts_vs_nonpos(
    re_z: sympy.Expr, im_z: sympy.Expr
) -> tuple[str, Optional[sympy.Expr]]:
    if not _is_exact_number(re_z) or not _is_exact_number(im_z):
        return "unknown", None
    im_zero = _is_zero(im_z)
    if im_zero is True:
        flag = _is_nonpositive_integer(re_z)
        if flag is True:
            return "pole", sympy.Integer(0)
        if flag is False:
            rho = _real_dist_to_nonpos(re_z)
            if rho is not None:
                return "regular", rho
            return "unknown", None
        return "unknown", None
    if im_zero is False:
        rho = _complex_dist_to_nonpos(re_z, im_z)
        if rho is not None and _is_positive(rho):
            return "regular", rho
        return "unknown", None
    return "unknown", None


def _real_dist_to_nonpos(x: sympy.Expr) -> Optional[sympy.Expr]:
    if _is_nonpositive_integer(x) is True:
        return sympy.Integer(0)
    try:
        if x.is_real is False:
            return None
        pos = sympy.simplify(x > 0)
        if pos is True or (hasattr(pos, "is_Boolean") and bool(pos) is True):
            d = sympy.simplify(sympy.Abs(x))
            return d if _is_positive(d) or d == x else sympy.simplify(x)
        n_left = sympy.floor(x)
        n_right = sympy.simplify(n_left + 1)
        dists = [sympy.simplify(x - n_left)]
        try:
            if n_right <= 0 or (n_right.is_nonpositive is True):
                dists.append(sympy.simplify(n_right - x))
            elif int(n_right) <= 0:
                dists.append(sympy.simplify(n_right - x))
        except Exception:
            if n_right == 0 or n_right == sympy.Integer(0):
                dists.append(sympy.simplify(n_right - x))
        dists.append(sympy.simplify(sympy.Abs(x)))
        rho = sympy.simplify(sympy.Min(*dists))
        if _is_positive(rho):
            return rho
        return None
    except Exception:
        return None


def _complex_dist_to_nonpos(re_z: sympy.Expr, im_z: sympy.Expr) -> Optional[sympy.Expr]:
    z = re_z + sympy.I * im_z
    candidates: set[sympy.Expr] = {sympy.Integer(0)}
    try:
        n0 = sympy.floor(re_z)
        for k in (-2, -1, 0, 1, 2):
            n = sympy.Integer(int(n0 + k))
            if int(n) <= 0:
                candidates.add(n)
    except Exception:
        pass
    try:
        dists = [sympy.simplify(sympy.Abs(z - n)) for n in candidates]
        rho = sympy.simplify(sympy.Min(*dists))
        if _is_positive(rho):
            return rho
        return None
    except Exception:
        return None


@dataclass
class _DeclaredFacts:
    pole_exclusion: bool = False
    im_nonzero: bool = False
    re_positive: bool = False
    distance_ge: Optional[sympy.Expr] = None
    used_a: list[dict[str, Any]] = field(default_factory=list)
    cd_items: list[dict[str, Any]] = field(default_factory=list)
    declared_items: list[dict[str, Any]] = field(default_factory=list)
    has_cd: bool = False
    has_unrecognized_a: bool = False


def _declared_facts(assumptions: Any) -> _DeclaredFacts:
    facts = _DeclaredFacts()
    items, malformed = _as_assumption_list(assumptions)
    facts.declared_items = items
    if malformed:
        facts.has_unrecognized_a = True
    for item in items:
        klass = item.get("class") if isinstance(item, dict) else None
        if klass in (C_GENERICITY, D_HUMAN_REQUIRED):
            facts.has_cd = True
            facts.cd_items.append(item)
            continue
        if klass not in (None, A_DECLARED, B_DERIVED):
            facts.has_unrecognized_a = True
            continue
        kind = str(item.get("kind") or "").strip().lower()
        text = _pred_text(item)
        matched = False
        if _is_pole_exclusion(text, kind):
            facts.pole_exclusion = True
            facts.used_a.append(_as_a(item))
            matched = True
        if _is_im_nonzero(text, kind):
            facts.im_nonzero = True
            facts.pole_exclusion = True
            facts.used_a.append(_as_a(item))
            matched = True
        if _is_re_positive(text, kind):
            facts.re_positive = True
            facts.pole_exclusion = True
            facts.used_a.append(_as_a(item))
            matched = True
        ge = _distance_ge_value(item, kind, text)
        if ge is not None:
            facts.distance_ge = ge
            facts.pole_exclusion = True
            facts.used_a.append(_as_a(item))
            matched = True
        if not matched:
            if klass in (None, A_DECLARED, B_DERIVED):
                facts.has_unrecognized_a = True
    # de-duplicate used_a
    facts.used_a = _dedupe_assumptions(facts.used_a)
    return facts


def _as_a(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    if out.get("class") not in (A_DECLARED, B_DERIVED):
        out["class"] = A_DECLARED
    return out


def _assumptions_for_verdict(
    facts: _DeclaredFacts,
    pole_name: str,
    uses_exclusion: bool,
    rho_kind: str,
) -> list[dict[str, Any]]:
    if not uses_exclusion and rho_kind in ("explicit", "infinity"):
        return []
    used = list(facts.used_a)
    if facts.im_nonzero and pole_name == NONPOSITIVE_INTEGERS:
        used.append(
            {
                "class": B_DERIVED,
                "predicate": "Im(z0) != 0 ⇒ z0 not in Z_<=0",
            }
        )
    if facts.re_positive and pole_name == NONPOSITIVE_INTEGERS:
        used.append(
            {
                "class": B_DERIVED,
                "predicate": "Re(z0) > 0 ⇒ z0 not in Z_<=0",
            }
        )
    return _dedupe_assumptions(used)


def _combine_distance(
    query: PoleQuery,
    facts: _DeclaredFacts,
    pole_name: str,
    isolated: bool,
) -> tuple[str, Any]:
    """Return (kind, value) with kind in explicit|infinity|existence|none."""
    qkind, qval = _distance_kind(query.distance)
    if query.kind == "regular":
        if qkind == "infinity":
            return "infinity", sympy.oo
        if qkind == "explicit" and qval is not None:
            return "explicit", qval
        if isolated:
            return "existence", None
        return "none", None

    if facts.distance_ge is not None and _is_positive(facts.distance_ge):
        return "explicit", facts.distance_ge

    exclusion_ok = False
    if facts.pole_exclusion:
        exclusion_ok = True
    if facts.im_nonzero and pole_name in (NONPOSITIVE_INTEGERS, ""):
        exclusion_ok = True
    if facts.re_positive and pole_name in (NONPOSITIVE_INTEGERS, ""):
        exclusion_ok = True
    if exclusion_ok and isolated:
        return "existence", None
    if exclusion_ok and facts.distance_ge is not None:
        return "explicit", facts.distance_ge
    return "none", None


def _distance_kind(distance: str) -> tuple[str, Optional[sympy.Expr]]:
    text = str(distance or "").strip()
    if not text:
        return "none", None
    if text in {"oo", "zoo", "inf", "+inf", "infinity"}:
        return "infinity", sympy.oo
    if text.startswith(">"):
        return "existence", None
    expr = _as_expr(text)
    if expr is None:
        return "none", None
    if expr in (sympy.oo, sympy.S.Infinity):
        return "infinity", sympy.oo
    if _is_zero(expr) is True:
        return "zero", expr
    if _is_positive(expr):
        return "explicit", expr
    return "none", None


def _as_assumption_list(raw: Any) -> tuple[list[dict[str, Any]], bool]:
    if raw is None:
        return [], False
    if isinstance(raw, dict):
        return [raw], False
    if isinstance(raw, str):
        return [{"class": A_DECLARED, "predicate": raw}], False
    if isinstance(raw, (list, tuple)):
        out: list[dict[str, Any]] = []
        malformed = False
        for item in raw:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str):
                out.append({"class": A_DECLARED, "predicate": item})
            else:
                malformed = True
        return out, malformed
    return [], True


def _pred_text(item: dict[str, Any]) -> str:
    parts = [
        str(item.get("predicate") or ""),
        str(item.get("kind") or ""),
        str(item.get("claim") or ""),
        str(item.get("text") or ""),
    ]
    return " ".join(p for p in parts if p).lower()


_POLE_EXCL_KINDS = frozenset(
    {
        "not_in_nonpositive_integers",
        "not_in_pole_set",
        "pole_exclusion",
        "not_a_pole",
        "distance_positive",
        "outside_pole_set",
    }
)
_IM_KINDS = frozenset({"im_nonzero", "imag_nonzero", "im_ne_0"})
_RE_POS_KINDS = frozenset({"re_positive", "positive_real_part"})


def _is_pole_exclusion(text: str, kind: str) -> bool:
    if kind in _POLE_EXCL_KINDS:
        return True
    t = " ".join(text.lower().split())
    needles = (
        "not in z_<=0",
        "not in z<=0",
        "not in {0, -1, -2",
        "not in {0,-1,-2",
        "not a pole",
        "not a polygamma pole",
        "not in pole set",
        "not in the pole set",
        "not in nonpositive",
        "not a nonpositive integer",
        "outside the pole set",
        "z0 not in p",
    )
    return any(n in t for n in needles)


def _is_im_nonzero(text: str, kind: str) -> bool:
    if kind in _IM_KINDS:
        return True
    t = " ".join(text.lower().split())
    if "im(" not in t and "imag(" not in t:
        return False
    return any(tok in t for tok in ("!= 0", "!=0", "≠ 0", "nonzero", "not zero", "not 0"))


def _is_re_positive(text: str, kind: str) -> bool:
    if kind in _RE_POS_KINDS:
        return True
    t = " ".join(text.lower().split())
    if t in {"z0 > 0", "z0>0", "z0 positive", "alpha_0 > 0"}:
        return True
    if "re(" not in t:
        return False
    return any(tok in t for tok in ("> 0", ">0", "positive"))


def _distance_ge_value(
    item: dict[str, Any], kind: str, _text: str
) -> Optional[sympy.Expr]:
    if kind not in {"distance_ge", "rho_ge", "distance_at_least"}:
        return None
    raw = item.get("value", item.get("rho", item.get("distance")))
    if raw is None:
        return None
    expr = raw if isinstance(raw, sympy.Expr) else _as_expr(raw)
    if expr is None or not _is_positive(expr):
        return None
    return expr


def _dedupe_assumptions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for item in items:
        key = json.dumps(item, sort_keys=True, default=str, separators=(",", ":"))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _hash_assumptions(items: list[dict[str, Any]]) -> str:
    blobs = [
        json.dumps(item, sort_keys=True, default=str, separators=(",", ":"))
        for item in items
    ]
    canonical = "[" + ",".join(sorted(blobs)) + "]"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _parts(z: sympy.Expr) -> tuple[sympy.Expr, sympy.Expr]:
    try:
        re_z = sympy.simplify(sympy.re(z))
        im_z = sympy.simplify(sympy.im(z))
        return re_z, im_z
    except Exception:
        return z, sympy.Integer(0)


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, sympy.Integer)):
        return sympy.Integer(value)
    if isinstance(value, sympy.Rational):
        return value
    if isinstance(value, sympy.Basic):
        if isinstance(value, sympy.Float) or value.has(sympy.Float):
            return None
        return value
    if isinstance(value, float):
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text or len(text) > CHAR_CAP:
            return None
        try:
            out = sympy.parse_expr(text, local_dict=dict(_PARSE_LOCAL), evaluate=True)
        except Exception:
            return None
        if not isinstance(out, sympy.Expr):
            return None
        if isinstance(out, sympy.Float) or out.has(sympy.Float):
            return None
        return out
    return None


def _expr_str(expr: Any) -> str:
    if isinstance(expr, sympy.Basic):
        return str(sympy.simplify(expr))
    return str(expr)


def _too_large(expr: sympy.Expr) -> bool:
    try:
        return int(sympy.count_ops(expr, visual=False)) > OPS_CAP
    except Exception:
        return True


def _nonfinite(expr: sympy.Expr) -> bool:
    try:
        if any(expr == sentinel for sentinel in _NONFINITE):
            return True
        if expr.has(*_NONFINITE):
            return True
        if expr.is_infinite is True:
            return True
    except Exception:
        return True
    return False


def _has_float(expr: sympy.Expr) -> bool:
    try:
        return isinstance(expr, sympy.Float) or bool(expr.has(sympy.Float))
    except Exception:
        return True


def _is_exact_number(expr: sympy.Expr) -> bool:
    if not isinstance(expr, sympy.Basic):
        return False
    if expr.free_symbols or _has_float(expr) or _nonfinite(expr):
        return False
    try:
        return expr.is_number is True
    except Exception:
        return False


def _is_zero(expr: sympy.Expr) -> Optional[bool]:
    try:
        if expr == 0 or expr.is_zero is True:
            return True
        if expr.is_zero is False or expr.is_nonzero is True:
            return False
        s = sympy.simplify(expr)
        if s == 0:
            return True
        if s.is_number and s != 0 and not isinstance(s, sympy.Float):
            return False
    except Exception:
        return None
    return None


def _is_positive(expr: sympy.Expr) -> bool:
    try:
        if expr.is_positive is True:
            return True
        s = sympy.simplify(expr)
        if s.is_positive is True:
            return True
        if s.is_number and not isinstance(s, sympy.Float):
            cmp = s > 0
            return cmp is True or cmp is sympy.true
    except Exception:
        return False
    return False


def _is_nonpositive_integer(x: sympy.Expr) -> Optional[bool]:
    try:
        x = sympy.simplify(x)
    except Exception:
        return None
    if x.free_symbols or _has_float(x) or _nonfinite(x):
        return None
    if isinstance(x, sympy.Integer) or x.is_Integer is True:
        try:
            return int(x) <= 0
        except Exception:
            return None
    if x.is_integer is True:
        try:
            return int(x) <= 0
        except Exception:
            return None
    if x.is_rational is True:
        try:
            q = int(x.q)
            if q != 1:
                return False
            return int(x.p) <= 0
        except Exception:
            return None
    if x.is_integer is False:
        return False
    try:
        s = sympy.simplify(sympy.sin(sympy.pi * x))
        if s == 0:
            if x.is_positive is True:
                return False
            if x.is_nonpositive is True:
                return True
            return None
        if s != 0 and s.is_number and not isinstance(s, sympy.Float):
            return False
    except Exception:
        return None
    return None
