"""Holomorphic Taylor remainder hypotheses for affine paths.

Classical one-variable analysis (Ahlfors / Conway / Rudin). Not novelty.
CERTIFIED remainder is not hop ZERO. No Cauchy majorant (R4). No
polygamma pole location (R2). Class-C genericity cannot CERTIFY.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Protocol

import sympy

from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    HOP_ZERO,
    NEIGHBORHOOD_ASSUMPTION,
    NEIGHBORHOOD_CERTIFIED,
    NEIGHBORHOOD_UNKNOWN,
    NONANALYTIC,
    RemainderCertificate,
    UNKNOWN,
    remainder_cannot_be_hop_zero,
    validate_certificate,
)

# --- named theorems (THEOREMS.md); classical, not novelty ---

T1_HOLOMORPHIC_TAYLOR = "T1_holomorphic_taylor"
T2_CAUCHY_ESTIMATES = "T2_cauchy_estimates"
T3_CAUCHY_INTEGRAL_REMAINDER = "T3_cauchy_integral_remainder"
T4_LAGRANGE_REAL_SEGMENT = "T4_lagrange_real_segment"
T5_INTEGRAL_REMAINDER_REAL_SEGMENT = "T5_integral_remainder_real_segment"
T6_RADIUS_DISTANCE_TO_SINGULARITY = "T6_radius_equals_distance_to_singularity"
T7_AFFINE_HOLOMORPHIC_REMAINDER = "T7_affine_holomorphic_remainder"

THEOREM_IDS = (
    T1_HOLOMORPHIC_TAYLOR,
    T2_CAUCHY_ESTIMATES,
    T3_CAUCHY_INTEGRAL_REMAINDER,
    T4_LAGRANGE_REAL_SEGMENT,
    T5_INTEGRAL_REMAINDER_REAL_SEGMENT,
    T6_RADIUS_DISTANCE_TO_SINGULARITY,
    T7_AFFINE_HOLOMORPHIC_REMAINDER,
)

# Verifier checks in THEOREMS.md (T7 checklist plus T4/T6 tags).
H1_HOLOMORPHIC_DISK = "H1_holomorphic_disk"
H2_AFFINE_PATH = "H2_affine_path"
H3_PATH_STAYS_INSIDE = "H3_path_stays_inside"
H4_EXPANSION_ORDER = "H4_expansion_order"
H5_NO_CLASS_CD = "H5_no_class_cd"
H6_REMAINDER_ORDER = "H6_remainder_order"
H7_SINGULARITY_AT_EXPANSION = "H7_singularity_at_expansion"
H8_NOT_HOP_ZERO = "H8_not_hop_zero"
H_LAGRANGE_T_REAL = "H_lagrange_t_real"
H_LAGRANGE_SEGMENT = "H_lagrange_segment"
H_CAUCHY_CIRCLE = "H_cauchy_circle"
H_CAUCHY_FINITE_M = "H_cauchy_finite_M"

VERIFIER_CHECKS = (
    H1_HOLOMORPHIC_DISK,
    H2_AFFINE_PATH,
    H3_PATH_STAYS_INSIDE,
    H4_EXPANSION_ORDER,
    H5_NO_CLASS_CD,
    H6_REMAINDER_ORDER,
    H7_SINGULARITY_AT_EXPANSION,
    H8_NOT_HOP_ZERO,
)

HOLOMORPHY_DECLARED_ENTIRE = "declared_entire"
HOLOMORPHY_DECLARED_DISK = "declared_disk"
HOLOMORPHY_DISTANCE_TO_SINGULARITY = "distance_to_singularity"
HOLOMORPHY_GENERICITY = "genericity"

ENTIRE_FAMILIES = frozenset(
    {
        "exp",
        "sin",
        "cos",
        "sinh",
        "cosh",
        "entire",
        "polynomial",
        "poly",
        "id",
        "identity",
    }
)

# Classical excluded points for named families. Polygamma is R2.
CLASSICAL_EXCLUDED_POINTS = {
    "log": (0,),
    "sqrt": (0,),
    "inv": (0,),
}

_WITNESS_DELTA_LEMMA = (
    "If rho>0 and c is finite, delta=rho/(2(1+|c|)) satisfies "
    "|c|*delta <= rho/2 < rho."
)
_WITNESS_ENTIRE_DELTA = (
    "If rho=+oo (entire) and c is finite, delta=1 satisfies |c|*delta < rho."
)


# ---------------------------------------------------------------------------
# dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HolomorphicDisk:
    """Claim: f is holomorphic on the open disk |z-z0| < rho."""

    z0: Any
    rho: Any
    function_family: str = ""
    source: str = HOLOMORPHY_DECLARED_DISK
    excluded_points: tuple = ()
    rho_positive: Optional[bool] = None
    well_formed: bool = False
    may_certify: bool = False
    note: str = ""


@dataclass(frozen=True)
class AffinePath:
    """Claim: z(t) = z0 + c t with c independent of t."""

    z0: Any
    c: Any
    t: Any = "t"
    delta: Any = None
    affine: Optional[bool] = None
    c_finite: Optional[bool] = None
    note: str = ""


@dataclass(frozen=True)
class PathStaysInside:
    """Predicate |c| * delta < rho for |t| < delta (open disk)."""

    z0: Any
    c: Any
    delta: Any
    rho: Any
    modulus_c: Any = None
    product: Any = None
    holds: Optional[bool] = None
    reason: str = ""


@dataclass(frozen=True)
class DistanceToSingularity:
    """dist(z0, singularities). R1 does not compute polygamma poles."""

    z0: Any
    distance: Any
    isolated: Optional[bool] = True
    source: str = ""
    well_formed: bool = False
    vanishing: Optional[bool] = None
    note: str = ""


@dataclass(frozen=True)
class CauchyBoundRequest:
    """Payload for R4. R1 does not fill M or a numeric majorant."""

    z0: Any
    rho: Any
    N: Optional[int] = None
    circle_radius: Any = None
    M: Any = None
    bound: str = ""
    well_formed: bool = False
    theorem: str = T2_CAUCHY_ESTIMATES
    note: str = (
        "Cauchy estimates require 0<r<rho and finite M on |z-z0|=r; "
        "not computed here (R4)."
    )


@dataclass(frozen=True)
class SingularityQuery:
    """Payload for R2. R1 does not locate polygamma poles."""

    z0: Any
    function_family: str = ""
    function_order: str = ""
    note: str = "Nearest-singularity distance is supplied by R2, not R1."


class CauchyBoundProvider(Protocol):
    """R4 implements this. R1 ships no provider."""

    def bound_remainder(self, request: CauchyBoundRequest) -> CauchyBoundRequest:
        ...


class SingularityDistanceProvider(Protocol):
    """R2 implements this. R1 ships no polygamma locator."""

    def distance_to_nearest_singularity(
        self, query: SingularityQuery
    ) -> DistanceToSingularity:
        ...


@dataclass(frozen=True)
class AffineRemainderHypotheses:
    """Discharged (or failed) T7 checks. Not a hop certificate."""

    disk: Optional[HolomorphicDisk]
    path: Optional[AffinePath]
    stays: Optional[PathStaysInside]
    distance: Optional[DistanceToSingularity]
    N: Optional[int]
    remainder_form: str
    lagrange_ok: bool
    integral_ok: bool
    verdict: str
    neighborhood_verdict: str
    domain_conditions: tuple[str, ...]
    proof_dependencies: tuple[str, ...]
    failed_checks: tuple[str, ...]
    required_small_t_condition: str
    assumptions_used: tuple[dict[str, Any], ...]
    note: str
    analyticity_certificate: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# quantity helpers (exact; floats are UNKNOWN)
# ---------------------------------------------------------------------------


def _as_expr(value: Any) -> Optional[sympy.Expr]:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, sympy.Basic):
        return value
    if isinstance(value, int):
        return sympy.Integer(value)
    if isinstance(value, float):
        return None
    if isinstance(value, str):
        s = value.strip()
        if not s or len(s) > 128:
            return None
        if s in {"oo", "+oo", "inf", "infinity"}:
            return sympy.oo
        if s in {"-oo", "-inf"}:
            return sympy.S.NegativeInfinity
        if s.isidentifier():
            return sympy.Symbol(s)
        if "/" in s and s.count("/") == 1:
            p, q = s.split("/")
            try:
                return sympy.Integer(p) / sympy.Integer(q)
            except (TypeError, ValueError):
                return None
        try:
            return sympy.Integer(s)
        except (TypeError, ValueError):
            return None
    return None


def _as_symbol(value: Any) -> Optional[sympy.Symbol]:
    if isinstance(value, sympy.Symbol):
        return value
    if isinstance(value, str) and value.strip().isidentifier() and len(value) <= 64:
        return sympy.Symbol(value.strip())
    return None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _is_nan(expr: sympy.Expr) -> bool:
    return expr is sympy.nan or expr == sympy.nan


def _is_infinite(expr: sympy.Expr) -> Optional[bool]:
    if expr in (
        sympy.oo,
        -sympy.oo,
        sympy.zoo,
        sympy.S.Infinity,
        sympy.S.NegativeInfinity,
    ):
        return True
    try:
        flag = expr.is_infinite
    except (AttributeError, TypeError, ValueError):
        return None
    if flag is True:
        return True
    if flag is False:
        return False
    return None


def _has_forbidden_infinity(expr: sympy.Expr) -> bool:
    return bool(expr.has(sympy.oo, sympy.zoo, sympy.S.Infinity, sympy.S.NegativeInfinity))


def _modulus(expr: sympy.Expr) -> sympy.Expr:
    if _is_infinite(expr) is True:
        return sympy.oo
    return sympy.Abs(expr)


def _strictly_positive(expr: sympy.Expr) -> Optional[bool]:
    if expr == sympy.oo:
        return True
    if expr in (sympy.zoo, sympy.nan, sympy.S.NegativeInfinity, -sympy.oo):
        return False
    if expr.has(sympy.Float):
        return None
    try:
        if expr.is_positive is True:
            return True
        if expr.is_nonpositive is True:
            return False
    except (AttributeError, TypeError, ValueError):
        return None
    if expr.is_number:
        try:
            return bool(expr > 0)
        except (TypeError, ValueError):
            return None
    return None


def _is_zero(expr: sympy.Expr) -> Optional[bool]:
    if expr.has(sympy.Float):
        return None
    try:
        if expr.is_zero is True:
            return True
        if expr.is_zero is False:
            return False
    except (AttributeError, TypeError, ValueError):
        return None
    if expr.is_number:
        try:
            return bool(expr == 0)
        except (TypeError, ValueError):
            return None
    return None


def _strictly_less(left: sympy.Expr, right: sympy.Expr) -> Optional[bool]:
    if left.has(sympy.Float) or right.has(sympy.Float):
        return None
    if right == sympy.oo:
        if _is_infinite(left) is True:
            return False
        return True
    if _is_infinite(left) is True:
        return False
    try:
        diff = sympy.simplify(right - left)
    except (TypeError, ValueError, AttributeError):
        return None
    pos = _strictly_positive(diff)
    if pos is True:
        return True
    if pos is False:
        return False
    z = _is_zero(diff)
    if z is True:
        return False
    return None


def _depends_on_t(expr: Any, t: Any) -> Optional[bool]:
    e = _as_expr(expr)
    t_sym = _as_symbol(t)
    if e is None:
        return None
    if t_sym is None:
        return False
    return t_sym in e.free_symbols


def _c_finite(c: sympy.Expr) -> Optional[bool]:
    if _is_nan(c):
        return False
    inf = _is_infinite(c)
    if inf is True:
        return False
    if _has_forbidden_infinity(c):
        return False
    if inf is False:
        return True
    # Parameters in C are finite; symbols are class-A complex numbers.
    return True


def _norm_family(name: str) -> str:
    return (name or "").strip().lower()


def _as_nonneg_int(N: Any) -> Optional[int]:
    if isinstance(N, bool):
        return None
    if isinstance(N, int):
        return N if N >= 0 else None
    if isinstance(N, sympy.Integer):
        n = int(N)
        return n if n >= 0 else None
    return None


def _assumption_classes(assumptions_used: Optional[list | tuple]) -> tuple[str, ...]:
    out: list[str] = []
    if not assumptions_used:
        return ()
    for item in assumptions_used:
        if isinstance(item, dict):
            klass = item.get("class")
            if isinstance(klass, str):
                out.append(klass)
    return tuple(out)


# ---------------------------------------------------------------------------
# predicates / factories
# ---------------------------------------------------------------------------


def holomorphic_disk(
    z0: Any,
    rho: Any,
    *,
    function_family: str = "",
    source: str = HOLOMORPHY_DECLARED_DISK,
    excluded_points: tuple = (),
) -> HolomorphicDisk:
    """Build a holomorphic-disk hypothesis. Does not locate poles of f."""
    family = _norm_family(function_family)
    z0_e = _as_expr(z0)
    rho_e = _as_expr(rho)
    extra = CLASSICAL_EXCLUDED_POINTS.get(family, ())
    excluded = tuple(excluded_points) + tuple(
        p for p in extra if p not in tuple(excluded_points)
    )
    if z0_e is None or rho_e is None:
        return HolomorphicDisk(
            z0=z0,
            rho=rho,
            function_family=family,
            source=source,
            excluded_points=excluded,
            rho_positive=None,
            well_formed=False,
            may_certify=False,
            note="unparsed z0 or rho",
        )
    pos = _strictly_positive(rho_e)
    well = pos is True
    may = well and source != HOLOMORPHY_GENERICITY
    note = ""
    if source == HOLOMORPHY_GENERICITY:
        note = "class-C genericity cannot CERTIFY"
        may = False
    elif pos is False:
        note = "non-positive disk radius"
    elif pos is None:
        note = "radius positivity unproved"
    return HolomorphicDisk(
        z0=z0_e,
        rho=rho_e,
        function_family=family,
        source=source,
        excluded_points=excluded,
        rho_positive=pos,
        well_formed=well,
        may_certify=may,
        note=note,
    )


def affine_path(
    z0: Any,
    c: Any,
    *,
    t: Any = "t",
    delta: Any = None,
) -> AffinePath:
    z0_e = _as_expr(z0)
    c_e = _as_expr(c)
    if z0_e is None or c_e is None:
        return AffinePath(
            z0=z0,
            c=c,
            t=t,
            delta=delta,
            affine=None,
            c_finite=None,
            note="unparsed z0 or c",
        )
    dep_z = _depends_on_t(z0_e, t)
    dep_c = _depends_on_t(c_e, t)
    affine: Optional[bool]
    if dep_z is True or dep_c is True:
        affine = False
    elif dep_z is None or dep_c is None:
        affine = None
    else:
        affine = True
    return AffinePath(
        z0=z0_e,
        c=c_e,
        t=t,
        delta=delta,
        affine=affine,
        c_finite=_c_finite(c_e),
        note="" if affine else "z0 or c depends on t",
    )


def path_stays_inside(z0: Any, c: Any, delta: Any, rho: Any) -> PathStaysInside:
    """Return whether |c|*delta < rho with delta>0.

    None means the comparison is unproved (fail closed), not True.
    """
    z0_e = _as_expr(z0)
    c_e = _as_expr(c)
    d_e = _as_expr(delta)
    r_e = _as_expr(rho)
    if c_e is None or d_e is None or r_e is None:
        return PathStaysInside(
            z0=z0 if z0_e is None else z0_e,
            c=c,
            delta=delta,
            rho=rho,
            holds=None,
            reason="unparsed c, delta, or rho",
        )
    mod = _modulus(c_e)
    try:
        product = sympy.simplify(mod * d_e)
    except (TypeError, ValueError, AttributeError):
        product = mod * d_e
    dpos = _strictly_positive(d_e)
    rpos = _strictly_positive(r_e)
    if dpos is False:
        return PathStaysInside(
            z0=z0_e,
            c=c_e,
            delta=d_e,
            rho=r_e,
            modulus_c=mod,
            product=product,
            holds=False,
            reason="delta is not positive",
        )
    if rpos is False:
        return PathStaysInside(
            z0=z0_e,
            c=c_e,
            delta=d_e,
            rho=r_e,
            modulus_c=mod,
            product=product,
            holds=False,
            reason="rho is not positive",
        )
    if _is_constructed_staying_witness(c_e, d_e, r_e):
        return PathStaysInside(
            z0=z0_e,
            c=c_e,
            delta=d_e,
            rho=r_e,
            modulus_c=mod,
            product=product,
            holds=True,
            reason=_WITNESS_DELTA_LEMMA,
        )
    if r_e == sympy.oo and _c_finite(c_e) is True and dpos is True:
        return PathStaysInside(
            z0=z0_e,
            c=c_e,
            delta=d_e,
            rho=r_e,
            modulus_c=mod,
            product=product,
            holds=True,
            reason="entire/infinite radius; finite c and positive delta",
        )
    if _is_zero(mod) is True and rpos is True and dpos is True:
        return PathStaysInside(
            z0=z0_e,
            c=c_e,
            delta=d_e,
            rho=r_e,
            modulus_c=mod,
            product=product,
            holds=True,
            reason="c=0; path is the point z0",
        )
    cmp = _strictly_less(product, r_e)
    if cmp is True and dpos is True:
        holds: Optional[bool] = True
        reason = "|c|*delta < rho"
    elif cmp is False:
        holds = False
        reason = "|c|*delta is not < rho"
    else:
        holds = None
        reason = "comparison unproved"
        if dpos is None:
            reason = "delta positivity unproved"
    return PathStaysInside(
        z0=z0_e,
        c=c_e,
        delta=d_e,
        rho=r_e,
        modulus_c=mod,
        product=product,
        holds=holds,
        reason=reason,
    )


def staying_delta(c: Any, rho: Any) -> Optional[sympy.Expr]:
    """Explicit positive delta with |c|*delta < rho, or None."""
    c_e = _as_expr(c)
    r_e = _as_expr(rho)
    if c_e is None or r_e is None:
        return None
    if _c_finite(c_e) is not True:
        return None
    if r_e == sympy.oo:
        return sympy.Integer(1)
    if _strictly_positive(r_e) is not True:
        return None
    mod = _modulus(c_e)
    return r_e / (2 * (1 + mod))


def exists_positive_staying_delta(c: Any, rho: Any) -> Optional[bool]:
    d = staying_delta(c, rho)
    if d is None:
        r_e = _as_expr(rho)
        if r_e is not None and _strictly_positive(r_e) is False:
            return False
        return None
    return True


def _is_constructed_staying_witness(
    c: sympy.Expr, delta: sympy.Expr, rho: sympy.Expr
) -> bool:
    expected = staying_delta(c, rho)
    if expected is None:
        return False
    try:
        return sympy.simplify(sympy.expand(delta - expected)) == 0
    except (TypeError, ValueError, AttributeError):
        return False


def distance_to_singularity(
    z0: Any,
    distance: Any,
    *,
    isolated: Optional[bool] = True,
    source: str = "",
) -> DistanceToSingularity:
    d_e = _as_expr(distance)
    z0_e = _as_expr(z0)
    if d_e is None or z0_e is None:
        return DistanceToSingularity(
            z0=z0,
            distance=distance,
            isolated=isolated,
            source=source,
            well_formed=False,
            vanishing=None,
            note="unparsed z0 or distance",
        )
    vanishing = _is_zero(d_e)
    pos = _strictly_positive(d_e)
    well = pos is True or vanishing is True
    note = ""
    if vanishing is True:
        note = "distance 0: no positive-radius holomorphic disk"
    elif pos is None:
        note = "distance positivity unproved"
        well = False
    elif pos is False:
        note = "negative distance"
        well = False
    return DistanceToSingularity(
        z0=z0_e,
        distance=d_e,
        isolated=isolated,
        source=source,
        well_formed=well,
        vanishing=vanishing,
        note=note,
    )


def open_disk_radius_from_distance(distance: Any) -> Optional[sympy.Expr]:
    """Admissible open-disk radius: rho = d when d>0 (singularity not interior).

    A Cauchy circle must be strictly smaller; this function does not
    return a Cauchy radius (R4 / cauchy_bound_request).
    """
    rec = distance_to_singularity(0, distance)
    if rec.vanishing is True:
        return None
    if rec.well_formed and _strictly_positive(rec.distance) is True:
        return rec.distance
    return None


def cauchy_bound_request(
    z0: Any,
    rho: Any,
    N: Any = None,
    *,
    r: Any = None,
) -> CauchyBoundRequest:
    """Interface object for R4. Does not compute M."""
    n = _as_nonneg_int(N) if N is not None else None
    if N is not None and n is None:
        return CauchyBoundRequest(
            z0=z0,
            rho=rho,
            N=None,
            well_formed=False,
            note="N is not a nonnegative integer; no Cauchy request",
        )
    rho_e = _as_expr(rho)
    r_e = _as_expr(r) if r is not None else None
    well = False
    note = (
        "Cauchy estimates require 0<r<rho and finite M on |z-z0|=r; "
        "not computed here (R4)."
    )
    if r_e is None:
        # R1 does not pick r.
        return CauchyBoundRequest(
            z0=z0,
            rho=rho if rho_e is None else rho_e,
            N=n,
            circle_radius=None,
            M=None,
            bound="",
            well_formed=False,
            note=note,
        )
    if rho_e is None:
        return CauchyBoundRequest(
            z0=z0,
            rho=rho,
            N=n,
            circle_radius=r_e,
            well_formed=False,
            note="unparsed rho",
        )
    inside = _strictly_less(r_e, rho_e)
    rpos = _strictly_positive(r_e)
    well = inside is True and rpos is True
    if inside is False:
        note = "Cauchy circle is not strictly inside the holomorphic disk"
    elif rpos is not True:
        note = "Cauchy circle radius not proved positive"
    return CauchyBoundRequest(
        z0=z0,
        rho=rho_e,
        N=n,
        circle_radius=r_e,
        M=None,
        bound="",
        well_formed=well,
        note=note,
    )


def lagrange_remainder_applicable(
    *, t_is_real: bool, segment_in_domain: bool
) -> bool:
    """Lagrange/integral remainder only for a real segment in the disk."""
    return bool(t_is_real) and bool(segment_in_domain)


def integral_remainder_applicable(
    *, t_is_real: bool, segment_in_domain: bool
) -> bool:
    return lagrange_remainder_applicable(
        t_is_real=t_is_real, segment_in_domain=segment_in_domain
    )


def remainder_order_big_o(N: int) -> str:
    return f"O(t^{N + 1})"


def _point_in_open_disk(point: Any, z0: Any, rho: Any) -> Optional[bool]:
    p = _as_expr(point)
    z = _as_expr(z0)
    r = _as_expr(rho)
    if p is None or z is None or r is None:
        return None
    if r == sympy.oo:
        if _is_infinite(p) is True:
            return False
        return True
    return _strictly_less(_modulus(p - z), r)


def _excluded_point_in_disk(disk: HolomorphicDisk) -> Optional[bool]:
    seen_unknown = False
    for pt in disk.excluded_points:
        hit = _point_in_open_disk(pt, disk.z0, disk.rho)
        if hit is True:
            return True
        if hit is None:
            seen_unknown = True
    if seen_unknown:
        return None
    return False


# ---------------------------------------------------------------------------
# T7 assembly
# ---------------------------------------------------------------------------


def _source_class(source: str) -> str:
    if source == HOLOMORPHY_GENERICITY:
        return C_GENERICITY
    if source == HOLOMORPHY_DISTANCE_TO_SINGULARITY:
        return B_DERIVED
    return A_DECLARED


def collect_affine_remainder_hypotheses(
    *,
    function_family: str = "",
    z0: Any,
    c: Any,
    N: Any,
    rho: Any = None,
    delta: Any = None,
    t: Any = "t",
    disk: Optional[HolomorphicDisk] = None,
    distance: Optional[DistanceToSingularity] = None,
    holomorphy_source: Optional[str] = None,
    t_is_real: bool = False,
    assumptions_used: Optional[list] = None,
) -> AffineRemainderHypotheses:
    """Discharge T7 checks. Never returns hop ZERO."""
    failed: list[str] = []
    deps: list[str] = [T1_HOLOMORPHIC_TAYLOR, T3_CAUCHY_INTEGRAL_REMAINDER, T7_AFFINE_HOLOMORPHIC_REMAINDER]
    family = _norm_family(function_family)
    assumptions = tuple(assumptions_used or ())
    klasses = _assumption_classes(assumptions)

    n = _as_nonneg_int(N)
    if n is None:
        failed.append(H4_EXPANSION_ORDER)

    path = affine_path(z0, c, t=t, delta=delta)
    if path.affine is not True:
        failed.append(H2_AFFINE_PATH)
    if path.c_finite is False:
        failed.append(H2_AFFINE_PATH)

    if distance is None:
        dist_rec = None
    else:
        dist_rec = distance
        deps.append(T6_RADIUS_DISTANCE_TO_SINGULARITY)

    source = holomorphy_source
    if disk is not None:
        source = disk.source
        family = disk.function_family or family
    if source is None:
        source = (
            HOLOMORPHY_DECLARED_ENTIRE
            if family in ENTIRE_FAMILIES
            else HOLOMORPHY_DECLARED_DISK
        )

    if disk is None:
        rho_use = rho
        if rho_use is None and family in ENTIRE_FAMILIES:
            rho_use = sympy.oo
        if rho_use is None and dist_rec is not None:
            derived = open_disk_radius_from_distance(dist_rec.distance)
            if derived is not None:
                rho_use = derived
                source = HOLOMORPHY_DISTANCE_TO_SINGULARITY
        if rho_use is None:
            disk = HolomorphicDisk(
                z0=z0,
                rho=None,
                function_family=family,
                source=source,
                well_formed=False,
                may_certify=False,
                note="no holomorphic disk supplied",
            )
        else:
            disk = holomorphic_disk(
                z0,
                rho_use,
                function_family=family,
                source=source,
            )
    else:
        disk = holomorphic_disk(
            disk.z0,
            disk.rho,
            function_family=disk.function_family or family,
            source=disk.source,
            excluded_points=disk.excluded_points,
        )

    excluded_hit = _excluded_point_in_disk(disk)
    singularity = False
    if dist_rec is not None and dist_rec.vanishing is True:
        singularity = True
    rho_e = _as_expr(disk.rho) if disk.rho is not None else None
    if rho_e is not None and _is_zero(rho_e) is True:
        singularity = True
    if excluded_hit is True:
        singularity = True
    if singularity:
        failed.append(H7_SINGULARITY_AT_EXPANSION)

    if not disk.well_formed or not disk.may_certify:
        if disk.source == HOLOMORPHY_GENERICITY:
            if H5_NO_CLASS_CD not in failed:
                failed.append(H5_NO_CLASS_CD)
        elif H7_SINGULARITY_AT_EXPANSION not in failed:
            failed.append(H1_HOLOMORPHIC_DISK)

    if C_GENERICITY in klasses or D_HUMAN_REQUIRED in klasses:
        if H5_NO_CLASS_CD not in failed:
            failed.append(H5_NO_CLASS_CD)
    if disk.source == HOLOMORPHY_GENERICITY and H5_NO_CLASS_CD not in failed:
        failed.append(H5_NO_CLASS_CD)

    used_delta = delta
    witness = False
    if used_delta is None:
        used_delta = staying_delta(path.c if path.c is not None else c, disk.rho)
        witness = used_delta is not None
    stays = None
    if used_delta is None:
        failed.append(H3_PATH_STAYS_INSIDE)
    else:
        stays = path_stays_inside(disk.z0, path.c, used_delta, disk.rho)
        if stays.holds is True:
            if witness:
                rho_e = _as_expr(disk.rho)
                lemma = (
                    _WITNESS_ENTIRE_DELTA
                    if rho_e == sympy.oo
                    else _WITNESS_DELTA_LEMMA
                )
                assumptions = assumptions + (
                    {
                        "class": B_DERIVED,
                        "predicate": lemma,
                    },
                )
        elif stays.holds is False:
            # Caller delta too large: shrink to the algebraic witness if possible.
            alt = staying_delta(path.c, disk.rho)
            if alt is not None:
                stays_alt = path_stays_inside(disk.z0, path.c, alt, disk.rho)
                if stays_alt.holds is True:
                    stays = stays_alt
                    used_delta = alt
                    witness = True
                    rho_e = _as_expr(disk.rho)
                    lemma = (
                        _WITNESS_ENTIRE_DELTA
                        if rho_e == sympy.oo
                        else _WITNESS_DELTA_LEMMA
                    )
                    assumptions = assumptions + (
                        {
                            "class": B_DERIVED,
                            "predicate": lemma,
                        },
                    )
                else:
                    failed.append(H3_PATH_STAYS_INSIDE)
            else:
                failed.append(H3_PATH_STAYS_INSIDE)
        else:
            failed.append(H3_PATH_STAYS_INSIDE)

    segment_ok = stays is not None and stays.holds is True
    lagrange_ok = lagrange_remainder_applicable(
        t_is_real=t_is_real, segment_in_domain=segment_ok
    )
    integral_ok = lagrange_ok
    if lagrange_ok:
        deps.extend([T4_LAGRANGE_REAL_SEGMENT, T5_INTEGRAL_REMAINDER_REAL_SEGMENT])

    forms = [remainder_order_big_o(n)] if n is not None else ["O(t^{N+1})"]
    forms.append("cauchy_integral")
    if lagrange_ok:
        forms.append("lagrange")
        forms.append("integral_real_segment")
    remainder_form = "+".join(forms)

    domain: list[str] = []
    if family in ENTIRE_FAMILIES or disk.source == HOLOMORPHY_DECLARED_ENTIRE:
        domain.append("entire")
    if disk.well_formed:
        domain.append(f"holomorphic_disk(|z-z0|<{_text(disk.rho)})")
    if stays is not None and stays.holds is True:
        domain.append(
            f"path_stays_inside(|c|*delta<{_text(disk.rho)}; delta={_text(used_delta)})"
        )
    if family:
        domain.append(f"function_family={family}")

    t_cond = ""
    if used_delta is not None and disk.rho is not None:
        t_cond = f"|t| < {used_delta} with |c|*delta < {disk.rho}"
        if witness:
            t_cond += " (witness delta=rho/(2(1+|c|)) or delta=1 if entire)"

    analyticity = {
        "kind": "holomorphic_disk",
        "z0": _text(disk.z0),
        "rho": _text(disk.rho),
        "source": disk.source,
        "theorem": T7_AFFINE_HOLOMORPHIC_REMAINDER,
        "path_c": _text(path.c),
        "delta": _text(used_delta),
        "N": n,
        "remainder": remainder_order_big_o(n) if n is not None else "",
        "cauchy_bound": "",
        "assumption_class": _source_class(disk.source),
    }

    # Verdict: never hop ZERO. Do not upgrade.
    neighborhood = NEIGHBORHOOD_UNKNOWN
    if H5_NO_CLASS_CD in failed:
        verdict = ASSUMPTION_REQUIRED
        neighborhood = NEIGHBORHOOD_ASSUMPTION
        note = "class C/D or genericity source; ASSUMPTION_REQUIRED not CERTIFIED"
    elif H7_SINGULARITY_AT_EXPANSION in failed:
        verdict = NONANALYTIC
        note = "no positive-radius holomorphic disk, or excluded point in the disk"
    elif failed:
        verdict = UNKNOWN
        note = "hypotheses unproved: " + ",".join(failed)
    else:
        verdict = CERTIFIED
        neighborhood = NEIGHBORHOOD_CERTIFIED
        note = (
            f"{remainder_order_big_o(n)} from holomorphic Taylor on a disk "
            "containing the affine path; not hop ZERO"
        )
        if not domain:
            verdict = UNKNOWN
            neighborhood = NEIGHBORHOOD_UNKNOWN
            failed.append(H1_HOLOMORPHIC_DISK)
            note = "CERTIFIED requires nonempty domain_conditions"

    if excluded_hit is None and family in CLASSICAL_EXCLUDED_POINTS:
        if verdict == CERTIFIED:
            verdict = UNKNOWN
            neighborhood = NEIGHBORHOOD_UNKNOWN
            failed.append(H1_HOLOMORPHIC_DISK)
            note = "classical excluded point vs disk comparison unproved"

    assert remainder_cannot_be_hop_zero(verdict)
    assert verdict != HOP_ZERO

    return AffineRemainderHypotheses(
        disk=disk,
        path=path,
        stays=stays,
        distance=dist_rec,
        N=n,
        remainder_form=remainder_form,
        lagrange_ok=lagrange_ok,
        integral_ok=integral_ok,
        verdict=verdict,
        neighborhood_verdict=neighborhood,
        domain_conditions=tuple(domain),
        proof_dependencies=tuple(dict.fromkeys(deps)),
        failed_checks=tuple(dict.fromkeys(failed)),
        required_small_t_condition=t_cond,
        assumptions_used=tuple(assumptions),
        note=note,
        analyticity_certificate=analyticity,
    )


def affine_taylor_remainder_certificate(
    *,
    function_family: str = "",
    function_order: str = "",
    z0: Any,
    c: Any,
    N: Any,
    rho: Any = None,
    delta: Any = None,
    t: Any = "t",
    disk: Optional[HolomorphicDisk] = None,
    distance: Optional[DistanceToSingularity] = None,
    holomorphy_source: Optional[str] = None,
    t_is_real: bool = False,
    assumptions_used: Optional[list] = None,
    argument: str = "",
    expansion_point: str = "",
    perturbation: str = "",
) -> RemainderCertificate:
    """RemainderCertificate for f(z0+c t). CERTIFIED is not hop ZERO."""
    hyp = collect_affine_remainder_hypotheses(
        function_family=function_family,
        z0=z0,
        c=c,
        N=N,
        rho=rho,
        delta=delta,
        t=t,
        disk=disk,
        distance=distance,
        holomorphy_source=holomorphy_source,
        t_is_real=t_is_real,
        assumptions_used=assumptions_used,
    )
    arg = argument or f"{_text(z0)} + ({_text(c)})*{_text(t)}"
    dist_txt = ""
    if hyp.distance is not None:
        dist_txt = _text(hyp.distance.distance)
    cert = RemainderCertificate(
        function_family=_norm_family(function_family),
        function_order=function_order,
        argument=arg,
        expansion_point=expansion_point or _text(z0),
        perturbation=perturbation or _text(c),
        expansion_order=hyp.N,
        domain_conditions=list(hyp.domain_conditions),
        analyticity_certificate=dict(hyp.analyticity_certificate),
        distance_to_singularity=dist_txt,
        remainder_form=hyp.remainder_form,
        bound="",
        required_small_t_condition=hyp.required_small_t_condition,
        assumptions_used=[dict(a) for a in hyp.assumptions_used],
        proof_dependencies=list(hyp.proof_dependencies),
        verdict=hyp.verdict,
        neighborhood_verdict=hyp.neighborhood_verdict,
        note=hyp.note,
    )
    sealed = validate_certificate(cert)
    if sealed != cert.verdict:
        cert.verdict = sealed
        if sealed == ASSUMPTION_REQUIRED:
            cert.neighborhood_verdict = NEIGHBORHOOD_ASSUMPTION
            cert.note = "validate_certificate demoted class C/D CERTIFIED"
        elif sealed == UNKNOWN:
            cert.neighborhood_verdict = NEIGHBORHOOD_UNKNOWN
            cert.note = "validate_certificate demoted ill-formed certificate"
    assert cert.verdict != HOP_ZERO
    assert remainder_cannot_be_hop_zero(cert.verdict)
    return cert
