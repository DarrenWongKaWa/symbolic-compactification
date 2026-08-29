"""Adversarial remainder certificates. Data only; checkers live next door.

Toy expansions that *look* remainder-CERTIFIED from a truncated Taylor
formula, a Cauchy disk, or a real-segment remainder, and are not.
``expect`` is never CERTIFIED on attacks: a CERTIFIED remainder is a
false analytic-domain or order-algebra certificate.

Class C/D assumptions are declared on the claimed certificate so
``validate_certificate`` cannot return CERTIFIED.
"""
from __future__ import annotations

from typing import Any

from research.coefficient_laurent.schema import UNKNOWN as HOP_UNKNOWN
from research.coefficient_laurent.schema import ZERO as HOP_ZERO
from research.remainder_certification.schema import (
    A_DECLARED,
    ASSUMPTION_REQUIRED,
    B_DERIVED,
    C_GENERICITY,
    CERTIFIED,
    D_HUMAN_REQUIRED,
    NONANALYTIC,
    UNKNOWN,
)

ATTACK_IDS = (
    "RC9_01_expansion_point_at_pole",
    "RC9_02_symbolic_point_may_be_pole",
    "RC9_03_affine_path_cross_pole",
    "RC9_04_insufficient_taylor_order",
    "RC9_05_divergent_prefactor",
    "RC9_06_hidden_denominator_zero",
    "RC9_07_complex_path_real_only",
    "RC9_08_incorrect_boundedness",
    "RC9_09_symbolic_M_unproved",
    "RC9_10_ignore_remainder",
)

ATTACK_KINDS = (
    "expansion_point_at_pole",
    "symbolic_point_may_be_pole",
    "affine_path_cross_pole",
    "insufficient_taylor_order",
    "divergent_prefactor",
    "hidden_denominator_zero",
    "complex_path_real_only",
    "incorrect_boundedness",
    "symbolic_M_unproved",
    "ignore_remainder",
)

CONTROL_IDS = (
    "RC9_POS_entire_exp",
    "RC9_POS_pg_safe",
    "RC9_POS_prefactor_ok",
)

_SYMS = (
    {"name": "t", "real": True},
    {"name": "a", "real": True},
    {"name": "b", "real": True},
    {"name": "M"},
)

_T_COMPLEX = (
    {"name": "t", "real": False, "complex": True},
    {"name": "a", "real": True},
    {"name": "b", "real": True},
    {"name": "M"},
)


def _case(
    cid: str,
    *,
    kind: str,
    expect: str,
    description: str,
    trap: str,
    function_family: str,
    argument: str,
    expansion_point: str,
    domain_conditions: list[str],
    claimed_verdict: str = CERTIFIED,
    function_order: str = "",
    perturbation: str = "t",
    expansion_order: int | None = 4,
    prefactor_power: int = 0,
    needed_vanish_power: int = 1,
    expression: str = "",
    distance_to_singularity: str = "",
    remainder_form: str = "",
    bound: str = "",
    required_small_t_condition: str = "",
    assumptions_used: list[dict[str, Any]] | None = None,
    proof_dependencies: list[str] | None = None,
    analyticity_certificate: dict[str, Any] | None = None,
    neighborhood_verdict: str = UNKNOWN,
    symbols: tuple[dict[str, Any], ...] | None = None,
    class_c: bool = False,
    should_be_certified: bool = False,
    should_be_hop_zero: bool = False,
    force_remainder_unknown: bool = False,
    perturbation_complex: bool = False,
    real_only_assumption: bool = False,
    bound_radius: float | None = None,
    M_symbol: str = "",
    M_finiteness_proved: bool = False,
    numerator: str = "",
    denominator: str = "",
    hop: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    N = expansion_order
    if not remainder_form and N is not None:
        remainder_form = f"O(t^{N + 1})"
    return {
        "id": cid,
        "kind": kind,
        "expect": expect,
        "should_be_certified": should_be_certified,
        "should_be_hop_zero": should_be_hop_zero,
        "claimed_verdict": claimed_verdict,
        "class_c": class_c,
        "description": description,
        "trap": trap,
        "symbols": list(symbols if symbols is not None else _SYMS),
        "function_family": function_family,
        "function_order": function_order,
        "argument": argument,
        "expression": expression or argument,
        "expansion_point": expansion_point,
        "perturbation": perturbation,
        "degeneration_variable": "t",
        "expansion_order": N,
        "prefactor_power": int(prefactor_power),
        "needed_vanish_power": int(needed_vanish_power),
        "domain_conditions": list(domain_conditions),
        "analyticity_certificate": dict(analyticity_certificate or {}),
        "distance_to_singularity": distance_to_singularity,
        "remainder_form": remainder_form,
        "bound": bound,
        "required_small_t_condition": required_small_t_condition,
        "assumptions_used": list(assumptions_used or []),
        "proof_dependencies": list(proof_dependencies or []),
        "neighborhood_verdict": neighborhood_verdict,
        "force_remainder_unknown": force_remainder_unknown,
        "perturbation_complex": perturbation_complex,
        "real_only_assumption": real_only_assumption,
        "bound_radius": bound_radius,
        "M_symbol": M_symbol,
        "M_finiteness_proved": M_finiteness_proved,
        "numerator": numerator,
        "denominator": denominator,
        "hop": dict(hop) if hop else None,
        "extra": dict(extra or {}),
    }


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "RC9_01_expansion_point_at_pole",
        kind="expansion_point_at_pole",
        expect=NONANALYTIC,
        trap="taylor_at_pole",
        description=(
            "polygamma(0, t) expanded at t=0 sits on a pole. A Taylor "
            "polynomial and O(t^{N+1}) remainder are not holomorphic there."
        ),
        function_family="polygamma",
        function_order="0",
        argument="t",
        expansion_point="0",
        expression="polygamma(0, t)",
        expansion_order=3,
        distance_to_singularity="0",
        domain_conditions=["claimed holomorphic at 0"],
        analyticity_certificate={"claimed_holomorphic": True},
        required_small_t_condition="|t| < 1",
        extra={"pole": "0"},
    ),
    _case(
        "RC9_02_symbolic_point_may_be_pole",
        kind="symbolic_point_may_be_pole",
        expect=ASSUMPTION_REQUIRED,
        trap="generic_alpha_not_a_pole",
        class_c=True,
        description=(
            "polygamma(0, a+t) with symbolic a. Without a declared/derived "
            "proof that a is not a nonpositive integer, remainder CERTIFIED "
            "silently inserts class-C genericity."
        ),
        function_family="polygamma",
        function_order="0",
        argument="a + t",
        expansion_point="a",
        expression="polygamma(0, a + t)",
        expansion_order=4,
        distance_to_singularity="|a| (unproved)",
        domain_conditions=["generic a not a pole"],
        assumptions_used=[
            {
                "class": C_GENERICITY,
                "predicate": "a not in Z_<=0",
            }
        ],
        required_small_t_condition="|t| < dist(a, Z_<=0)",
        extra={"z0_free_symbols": True},
    ),
    _case(
        "RC9_03_affine_path_cross_pole",
        kind="affine_path_cross_pole",
        expect=ASSUMPTION_REQUIRED,
        trap="uniform_delta_ignores_slope",
        class_c=True,
        description=(
            "z(t)=1/2 + b t has a regular expansion point 1/2, but symbolic "
            "slope b makes the pole at 0 occur at t=-1/(2b), which can be "
            "arbitrarily small. No uniform |t|<delta remainder disk."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1/2 + b*t",
        expansion_point="1/2",
        expression="polygamma(0, 1/2 + b*t)",
        expansion_order=4,
        distance_to_singularity="1/(2|b|) (can be arbitrarily small)",
        domain_conditions=["1/2 is not a polygamma pole"],
        assumptions_used=[
            {
                "class": C_GENERICITY,
                "predicate": "|b| bounded so that poles stay outside |t|<1",
            }
        ],
        required_small_t_condition="|t| < 1 (independent of b)",
        extra={"delta_unproved": True, "safe_z0": "1/2", "slope": "b"},
    ),
    _case(
        "RC9_04_insufficient_taylor_order",
        kind="insufficient_taylor_order",
        expect=UNKNOWN,
        trap="order_too_low_for_claimed_tail",
        description=(
            "Entire exp(t) expanded to N=2 has remainder O(t^3). Claiming "
            "that this certifies an O(t^6) tail (needed_vanish_power=6) is "
            "an insufficient Taylor order."
        ),
        function_family="exp",
        argument="t",
        expansion_point="0",
        expression="exp(t)",
        expansion_order=2,
        needed_vanish_power=6,
        distance_to_singularity="oo",
        domain_conditions=["entire"],
        remainder_form="O(t^6) (claimed; true remainder is O(t^3))",
        extra={"true_remainder_power": 3, "claimed_remainder_power": 6},
    ),
    _case(
        "RC9_05_divergent_prefactor",
        kind="divergent_prefactor",
        expect=UNKNOWN,
        trap="prefactor_eats_tail",
        description=(
            "t^{-4} * exp(t) with Taylor order N=2 of the analytic factor. "
            "Remainder t^{-4} O(t^3) = O(t^{-1}); N+1-m = -1 <= 0 so the "
            "prefactor overwhelms the tail and it does not vanish."
        ),
        function_family="exp",
        argument="t",
        expansion_point="0",
        expression="t**(-4)*exp(t)",
        expansion_order=2,
        prefactor_power=-4,
        needed_vanish_power=1,
        distance_to_singularity="oo (analytic factor)",
        domain_conditions=["exp entire; prefactor monomial t^{-4}"],
        remainder_form="t^{-4} O(t^3) = O(t^{-1})",
        extra={"m": 4, "N": 2, "N_plus_1_minus_m": -1},
    ),
    _case(
        "RC9_06_hidden_denominator_zero",
        kind="hidden_denominator_zero",
        expect=NONANALYTIC,
        trap="cancelled_factor_hides_pole",
        description=(
            "(1+t)/(t*(1+t)) looks cancellable to 1, but the uncancelled "
            "denominator t*(1+t) vanishes at t=0 while the numerator does "
            "not. Hidden pole; remainder is not holomorphic."
        ),
        function_family="rational",
        argument="t",
        expansion_point="0",
        expression="(1+t)/(t*(1+t))",
        expansion_order=3,
        distance_to_singularity="0",
        domain_conditions=["claimed removable after cancelling (1+t)"],
        numerator="1+t",
        denominator="t*(1+t)",
        extra={"claimed_simplified": "1", "true_reduced": "1/t"},
    ),
    _case(
        "RC9_07_complex_path_real_only",
        kind="complex_path_real_only",
        expect=ASSUMPTION_REQUIRED,
        trap="real_lagrange_on_complex_t",
        class_c=True,
        description=(
            "z(t)=1+I t with t not proved real. A real-segment Lagrange "
            "remainder is class C/D when the perturbation is complex: the "
            "path can leave Re(z)=1 and hit polygamma poles."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1 + I*t",
        expansion_point="1",
        expression="polygamma(0, 1 + I*t)",
        perturbation="I*t",
        expansion_order=4,
        symbols=_T_COMPLEX,
        perturbation_complex=True,
        real_only_assumption=True,
        distance_to_singularity="1 (only along real t)",
        domain_conditions=["real path t in R"],
        assumptions_used=[
            {
                "class": C_GENERICITY,
                "predicate": "t real; remainder uses a real segment",
            }
        ],
        required_small_t_condition="t real and |t| < 1/2",
        extra={"path": "1+I*t"},
    ),
    _case(
        "RC9_08_incorrect_boundedness",
        kind="incorrect_boundedness",
        expect=UNKNOWN,
        trap="cauchy_disk_contains_pole",
        description=(
            "polygamma(0, 1+t) is holomorphic at t=0, but the claimed "
            "Cauchy bound uses |t|<3, which contains the pole t=-1. "
            "|f^{(N+1)}| is not bounded on that disk."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1 + t",
        expansion_point="1",
        expression="polygamma(0, 1 + t)",
        expansion_order=4,
        distance_to_singularity="1",
        bound_radius=3.0,
        bound="|f^{(N+1)}| <= 10 on |t|<3",
        domain_conditions=["claimed |polygamma| bounded on |t|<3"],
        required_small_t_condition="|t| < 3",
        extra={"true_distance": 1, "bound_radius": 3},
    ),
    _case(
        "RC9_09_symbolic_M_unproved",
        kind="symbolic_M_unproved",
        expect=ASSUMPTION_REQUIRED,
        trap="cauchy_M_assumed_finite",
        class_c=True,
        description=(
            "Cauchy remainder with symbolic M on a disk that avoids poles. "
            "M < oo is not proved; class C/D forbids CERTIFIED."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1 + t",
        expansion_point="1",
        expression="polygamma(0, 1 + t)",
        expansion_order=4,
        distance_to_singularity="1",
        bound_radius=0.25,
        M_symbol="M",
        M_finiteness_proved=False,
        bound="M * |t|^{N+1} / (N+1)!",
        domain_conditions=["|t|<1/4 subset of holomorphic disk"],
        assumptions_used=[
            {
                "class": C_GENERICITY,
                "predicate": "M < oo",
            }
        ],
        proof_dependencies=[],
        required_small_t_condition="|t| < 1/4",
        extra={"cauchy_M": "M"},
    ),
    _case(
        "RC9_10_ignore_remainder",
        kind="ignore_remainder",
        expect=UNKNOWN,
        trap="neg_c0_zero_skips_remainder",
        claimed_verdict=UNKNOWN,
        force_remainder_unknown=True,
        description=(
            "V5 regression: negatives ZERO + C0 ZERO + remainder UNKNOWN "
            "must not compose to hop ZERO. Remainder was never certified."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1 + t",
        expansion_point="1",
        expression="polygamma(0, 1 + t)",
        expansion_order=4,
        distance_to_singularity="1",
        domain_conditions=["LEVEL B coefficients only; remainder unproved"],
        hop={
            "reconstruction_ok": True,
            "atoms_expanded": True,
            "negative_verdict": HOP_ZERO,
            "constant_verdict": HOP_ZERO,
            "remainder_verdict": HOP_UNKNOWN,
        },
        extra={"v5_regression": True},
    ),
]

CONTROL_CASES: list[dict[str, Any]] = [
    _case(
        "RC9_POS_entire_exp",
        kind="entire_exp",
        expect=CERTIFIED,
        should_be_certified=True,
        trap="none",
        description="exp(t) is entire; Taylor remainder O(t^{N+1}) vanishes.",
        function_family="exp",
        argument="t",
        expansion_point="0",
        expression="exp(t)",
        expansion_order=5,
        distance_to_singularity="oo",
        domain_conditions=["entire"],
        assumptions_used=[
            {"class": A_DECLARED, "predicate": "exp is entire"},
        ],
        analyticity_certificate={"status": "entire"},
        neighborhood_verdict="CERTIFIED_NEIGHBORHOOD",
        required_small_t_condition="any t",
        claimed_verdict=CERTIFIED,
    ),
    _case(
        "RC9_POS_pg_safe",
        kind="pg_safe",
        expect=CERTIFIED,
        should_be_certified=True,
        trap="none",
        description=(
            "polygamma(0, 1+t) at t=0: z0=1 is a positive integer, not a "
            "pole; disk |t|<1/2 is pole-free; remainder O(t^{N+1})."
        ),
        function_family="polygamma",
        function_order="0",
        argument="1 + t",
        expansion_point="1",
        expression="polygamma(0, 1 + t)",
        expansion_order=4,
        distance_to_singularity="1",
        bound_radius=0.5,
        domain_conditions=["z0=1 not in Z_<=0"],
        assumptions_used=[
            {
                "class": B_DERIVED,
                "predicate": "1 is a positive integer, hence not in Z_<=0",
            }
        ],
        proof_dependencies=["1 is_positive_integer"],
        analyticity_certificate={"status": "holomorphic_disk", "radius": "1/2"},
        neighborhood_verdict="CERTIFIED_NEIGHBORHOOD",
        required_small_t_condition="|t| < 1/2",
        claimed_verdict=CERTIFIED,
    ),
    _case(
        "RC9_POS_prefactor_ok",
        kind="prefactor_ok",
        expect=CERTIFIED,
        should_be_certified=True,
        trap="none",
        description=(
            "t^{-2} exp(t) with N=4: N+1-m = 3 > 0, so the prefactor times "
            "the Taylor tail is O(t^3) and vanishes as t->0."
        ),
        function_family="exp",
        argument="t",
        expansion_point="0",
        expression="t**(-2)*exp(t)",
        expansion_order=4,
        prefactor_power=-2,
        needed_vanish_power=1,
        distance_to_singularity="oo (analytic factor)",
        domain_conditions=["exp entire", "prefactor monomial t^{-2}"],
        assumptions_used=[
            {"class": A_DECLARED, "predicate": "exp is entire"},
        ],
        analyticity_certificate={"analytic_factor": "exp", "prefactor": "t^{-2}"},
        neighborhood_verdict="CERTIFIED_NEIGHBORHOOD",
        extra={"m": 2, "N": 4, "N_plus_1_minus_m": 3},
        claimed_verdict=CERTIFIED,
    ),
]

CASES_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in ATTACK_CASES}
CONTROL_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in CONTROL_CASES}


def load_attack_cases() -> list[dict[str, Any]]:
    return list(ATTACK_CASES)


def load_control_cases() -> list[dict[str, Any]]:
    return list(CONTROL_CASES)


def load_all_cases() -> list[dict[str, Any]]:
    return list(ATTACK_CASES) + list(CONTROL_CASES)


def load_class_c_attacks() -> list[dict[str, Any]]:
    return [c for c in ATTACK_CASES if is_class_c_or_d(c)]


def is_class_c_or_d(case: dict[str, Any]) -> bool:
    if case.get("class_c"):
        return True
    for item in case.get("assumptions_used") or []:
        if isinstance(item, dict) and item.get("class") in (
            C_GENERICITY,
            D_HUMAN_REQUIRED,
        ):
            return True
    return False
