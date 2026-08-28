"""Adversarial Laurent hops. Data only; checkers live next door.

Toy degenerations that *look* like LEVEL-C ZERO from a truncated or
partial atom series and are not hop ZERO. ``expect`` is never ZERO on
attacks: a ZERO verdict is a false certification of t^0 match, a wrong
polygamma order, a missing atom, a sign-flipped pole, or an insufficient
series window.
"""
from __future__ import annotations

from typing import Any

from research.coefficient_laurent.schema import NONZERO, UNKNOWN, ZERO

ATTACK_IDS = (
    "V5L_01_t0_match_surviving_pole",
    "V5L_02_wrong_polygamma_order",
    "V5L_03_missing_atom",
    "V5L_04_sign_flip",
    "V5L_05_insufficient_order",
)

ATTACK_KINDS = (
    "t0_match_surviving_pole",
    "wrong_polygamma_order",
    "missing_atom",
    "sign_flip",
    "insufficient_order",
)

CONTROL_IDS = (
    "V5L_POS_rational_pole_cancel",
    "V5L_POS_newton_polygamma",
)

_SYMS = (
    {"name": "t", "real": True},
    {"name": "x", "real": True},
    {"name": "a", "real": True},
    {"name": "b", "real": True},
)

_NEWTON_ATOMS = (
    "polygamma(0, x + t)/t",
    "-polygamma(0, x)/t",
)
_NEWTON_SOURCE = "(polygamma(0, x + t) - polygamma(0, x))/t"


def _case(
    cid: str,
    *,
    kind: str,
    expect: str,
    description: str,
    trap: str,
    atoms: list[str],
    target: str,
    source: str = "",
    source_atoms: list[str] | None = None,
    series_nterms: int = 4,
    required_power_min: int = -6,
    required_power_max: int = 0,
    should_be_zero: bool = False,
    probes: list[dict[str, int]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "kind": kind,
        "expect": expect,
        "should_be_zero": should_be_zero,
        "description": description,
        "trap": trap,
        "symbols": list(_SYMS),
        "atoms": list(atoms),
        "source": source,
        "source_atoms": list(source_atoms) if source_atoms is not None else None,
        "target": target,
        "degeneration_variable": "t",
        "target_value": "0",
        "series_nterms": int(series_nterms),
        "required_power_min": int(required_power_min),
        "required_power_max": int(required_power_max),
        "probes": list(probes or []),
        "extra": dict(extra or {}),
    }


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "V5L_01_t0_match_surviving_pole",
        kind="t0_match_surviving_pole",
        expect=NONZERO,
        trap="t0_match_ignores_pole",
        description=(
            "Rational atom a + 1/t has t^0 equal to the claimed target a, "
            "but t^{-1} survives. A t^0 match is not hop ZERO."
        ),
        atoms=["a + 1/t"],
        target="a",
        series_nterms=3,
        extra={"true_t0": "a", "surviving_power": -1},
    ),
    _case(
        "V5L_02_wrong_polygamma_order",
        kind="wrong_polygamma_order",
        expect=NONZERO,
        trap="wrong_order_as_t0",
        description=(
            "Newton quotient of polygamma(0) has t^0 = polygamma(1, x). "
            "Filling the diagonal with polygamma(2, x) is the wrong "
            "polygamma order; poles vanish and the constant term does not."
        ),
        atoms=list(_NEWTON_ATOMS),
        source=_NEWTON_SOURCE,
        target="polygamma(2, x)",
        series_nterms=4,
        probes=[{"x": 1}, {"x": 2}],
        extra={"true_t0": "polygamma(1, x)", "claimed_order": 2, "true_order": 1},
    ),
    _case(
        "V5L_03_missing_atom",
        kind="missing_atom",
        expect=UNKNOWN,
        trap="skip_reconstruction_t0_matches",
        description=(
            "True Newton source is polygamma(0, x+t)/t - polygamma(0, x)/t. "
            "Dropping the second atom leaves t^0 = polygamma(1, x) matching "
            "the diagonal while t^{-1} = polygamma(0, x) survives. "
            "Reconstruction of the declared atoms fails."
        ),
        atoms=["polygamma(0, x + t)/t"],
        source=_NEWTON_SOURCE,
        source_atoms=list(_NEWTON_ATOMS),
        target="polygamma(1, x)",
        series_nterms=4,
        probes=[{"x": 1}, {"x": 2}],
        extra={"missing": "-polygamma(0, x)/t"},
    ),
    _case(
        "V5L_04_sign_flip",
        kind="sign_flip",
        expect=NONZERO,
        trap="t0_match_ignores_pole",
        description=(
            "Canceling pole pair with the second atom's sign flipped: "
            "(a + 1/t) + (b + 1/t). t^0 still equals a + b; t^{-1} = 2 "
            "survives. Sign-flipped cancellation is not hop ZERO."
        ),
        atoms=["a + 1/t", "b + 1/t"],
        target="a + b",
        series_nterms=3,
        extra={"true_second_atom": "b - 1/t", "flipped": "b + 1/t"},
    ),
    _case(
        "V5L_05_insufficient_order",
        kind="insufficient_order",
        expect=UNKNOWN,
        trap="poles_vanished_without_t0",
        description=(
            "Newton polygamma quotient expanded only to nterms=0 is O(1): "
            "negative powers of the combined atom series vanish, but t^0 "
            "and the remainder live inside O(1). Insufficient order is "
            "LEVEL B UNKNOWN, never LEVEL C ZERO."
        ),
        atoms=list(_NEWTON_ATOMS),
        source=_NEWTON_SOURCE,
        target="polygamma(1, x)",
        series_nterms=0,
        probes=[{"x": 1}, {"x": 2}],
        extra={"true_nterms": 4},
    ),
]

CONTROL_CASES: list[dict[str, Any]] = [
    _case(
        "V5L_POS_rational_pole_cancel",
        kind="rational_pole_cancel",
        expect=ZERO,
        should_be_zero=True,
        trap="none",
        description=(
            "Genuine pole cancellation: (a + 1/t) + (b - 1/t) has vanishing "
            "t^{<0} and t^0 = a + b."
        ),
        atoms=["a + 1/t", "b - 1/t"],
        target="a + b",
        series_nterms=3,
    ),
    _case(
        "V5L_POS_newton_polygamma",
        kind="newton_polygamma",
        expect=ZERO,
        should_be_zero=True,
        trap="none",
        description=(
            "Genuine Newton quotient of polygamma(0): poles of "
            "polygamma(0, x+t)/t and -polygamma(0, x)/t cancel, t^0 equals "
            "polygamma(1, x) at sufficient series order."
        ),
        atoms=list(_NEWTON_ATOMS),
        source=_NEWTON_SOURCE,
        target="polygamma(1, x)",
        series_nterms=4,
        probes=[{"x": 1}, {"x": 2}],
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
