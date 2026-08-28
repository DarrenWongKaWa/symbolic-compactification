"""Adversarial Track-V claims. Data only; checkers live next door.

Each attack has ``should_be_zero`` False: a ZERO verdict is a false
certification. Controls are separate and must remain ZERO so the
checker is not an always-NONZERO gate.
"""
from __future__ import annotations

from typing import Any

ATTACK_IDS = (
    "V7_01_wrong_limit_target",
    "V7_02_false_removable_singularity",
    "V7_03_pole_sensitive",
    "V7_04_wrong_branch",
    "V7_05_nonuniform_limit_sketch",
    "V7_06_coefficient_corruption",
    "V7_07_hidden_assumption",
    "V7_08_fake_dd_structure",
)

ATTACK_KINDS = (
    "wrong_limit_target",
    "false_removable_singularity",
    "pole_sensitive",
    "wrong_branch",
    "nonuniform_limit_sketch",
    "coefficient_corruption",
    "hidden_assumption",
    "fake_dd_structure",
)

CONTROL_IDS = (
    "V7_TRUE_LIMIT_CONTROL",
    "V7_TRUE_NEWTON_CONTROL",
)

_XY = (
    {"name": "x", "real": True},
    {"name": "y", "real": True},
)
_XYZ = (
    {"name": "x", "real": True},
    {"name": "y", "real": True},
    {"name": "z", "real": True},
)
_XYE = (
    {"name": "x", "real": True},
    {"name": "y", "real": True},
    {"name": "eps", "real": True, "nonzero": True},
)
_Z = ({"name": "z", "real": True},)
_X = ({"name": "x", "real": True},)


def _case(
    cid: str,
    *,
    kind: str,
    description: str,
    primary_engine: str,
    symbols: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    math: dict[str, Any],
    should_be_zero: bool = False,
    functions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "kind": kind,
        "description": description,
        "should_be_zero": should_be_zero,
        "primary_engine": primary_engine,
        "symbols": list(symbols),
        "functions": list(functions or []),
        "math": math,
    }


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "V7_01_wrong_limit_target",
        kind="wrong_limit_target",
        primary_engine="confluence",
        description=(
            "Generic Newton kernel (sin(x)-sin(y))/(x-y) is claimed to tend "
            "to sin(x) as y→x. The true confluence is cos(x)."
        ),
        symbols=_XY,
        math={
            "kind": "LIMIT",
            "expr": "(sin(x) - sin(y))/(x - y)",
            "var": "y",
            "to": "x",
            "claimed": "sin(x)",
            "true": "cos(x)",
            "check_directional": False,
            "probes": [{"x": 0}],
            "source_piecewise": (
                "Piecewise((sin(x), Eq(x, y)), "
                "((sin(x) - sin(y))/(x - y), True))"
            ),
        },
    ),
    _case(
        "V7_02_false_removable_singularity",
        kind="false_removable_singularity",
        primary_engine="confluence",
        description=(
            "Pole 1/(x-y) is claimed to be a removable singularity whose "
            "y→x limit is the derivative F'(x)=1 of F(z)=z (as if the "
            "numerator were F(x)-F(y)). Directional limits disagree; the "
            "value is infinite, not a derivative."
        ),
        symbols=_XYZ,
        math={
            "kind": "LIMIT",
            "expr": "1/(x - y)",
            "var": "y",
            "to": "x",
            "claimed": "1",
            "F": "z",
            "F_var": "z",
            "true_derivative": "1",
            "check_directional": True,
            "probes": [],
        },
    ),
    _case(
        "V7_03_pole_sensitive",
        kind="pole_sensitive",
        primary_engine="confluence",
        description=(
            "Trigamma is given the digamma-style shift "
            "polygamma(1, z+1) = polygamma(1, z) + 1/z**2. The true shift "
            "subtracts 1/z**2; the error is the polar part -2/z**2."
        ),
        symbols=_Z,
        math={
            "kind": "EQUALITY",
            "left": "polygamma(1, z + 1)",
            "claimed": "polygamma(1, z) + 1/z**2",
            "true": "polygamma(1, z) - 1/z**2",
            "use_expand_func": True,
            "probes": [{"z": 2}],
        },
    ),
    _case(
        "V7_04_wrong_branch",
        kind="wrong_branch",
        primary_engine="confluence",
        description=(
            "Principal logarithm: log(-1) is claimed to be -I*pi (the "
            "other sheet). The principal value is I*pi."
        ),
        symbols=_X,
        math={
            "kind": "EQUALITY",
            "left": "log(-1)",
            "claimed": "-I*pi",
            "true": "I*pi",
            "probes": [],
        },
    ),
    _case(
        "V7_05_nonuniform_limit_sketch",
        kind="nonuniform_limit_sketch",
        primary_engine="confluence",
        description=(
            "Generic-in-eps sketch lim_{eps→0} (x-y)/((x-y)+eps) = 1 is "
            "used as certified data for the y→x confluence, including on "
            "the diagonal. The limits do not commute: y→x first is 0; "
            "eps→0 first is 1 off-diagonal. At x=y the family is 0."
        ),
        symbols=_XYE,
        math={
            "kind": "LIMIT",
            "expr": "(x - y)/((x - y) + eps)",
            "var": "y",
            "to": "x",
            "claimed": "1",
            "sketch_var": "eps",
            "sketch_to": "0",
            "sketch_claimed": "1",
            "check_directional": False,
            "substitute_diagonal": True,
            "probes": [{"x": 1, "y": 1, "eps": 1}],
        },
    ),
    _case(
        "V7_06_coefficient_corruption",
        kind="coefficient_corruption",
        primary_engine="factor",
        description=(
            "Spectator split of x**3-y**3 drops the mixed coefficient: "
            "claimed (x-y)*(x**2+y**2) instead of (x-y)*(x**2+x*y+y**2)."
        ),
        symbols=_XY,
        math={
            "kind": "FACTOR",
            "left": "x**3 - y**3",
            "claimed": "(x - y)*(x**2 + y**2)",
            "true": "(x - y)*(x**2 + x*y + y**2)",
            "cancelled_left": "(x**3 - y**3)/(x - y)",
            "cancelled_claimed": "x**2 + y**2",
            "probes": [{"x": 2, "y": 1}],
        },
    ),
    _case(
        "V7_07_hidden_assumption",
        kind="hidden_assumption",
        primary_engine="confluence",
        description=(
            "sqrt(x**2) is claimed equal to x. That needs x>=0 (or a "
            "positive declaration). For real x the identity is Abs(x), "
            "and x=-1 is an exact counterexample."
        ),
        symbols=_X,
        math={
            "kind": "EQUALITY",
            "left": "sqrt(x**2)",
            "claimed": "x",
            "true": "Abs(x)",
            "forbidden_assumptions": ["positive", "nonnegative", "x>=0"],
            "probes": [{"x": -1}],
        },
    ),
    _case(
        "V7_08_fake_dd_structure",
        kind="fake_dd_structure",
        primary_engine="dd_cert",
        description=(
            "Two-node Newton member (x**3-y**3)/(x-y) for F(z)=z**3 is "
            "claimed to be the repeated-node value F[x,x]=F'(x)=3*x**2."
        ),
        symbols=_XYZ,
        math={
            "kind": "HERMITE_DD",
            "F": "z**3",
            "F_var": "z",
            "member": "(x**3 - y**3)/(x - y)",
            "claimed": "3*x**2",
            "true_newton": "x**2 + x*y + y**2",
            "node_x": "x",
            "node_y": "y",
            "nodes": ["x", "x"],
            "probes": [{"x": 1, "y": 0}],
        },
    ),
]


CONTROL_CASES: list[dict[str, Any]] = [
    _case(
        "V7_TRUE_LIMIT_CONTROL",
        kind="true_limit_control",
        primary_engine="confluence",
        should_be_zero=True,
        description=(
            "Genuine confluence: lim_{y→x} (sin(x)-sin(y))/(x-y) = cos(x)."
        ),
        symbols=_XY,
        math={
            "kind": "LIMIT",
            "expr": "(sin(x) - sin(y))/(x - y)",
            "var": "y",
            "to": "x",
            "claimed": "cos(x)",
            "true": "cos(x)",
            "check_directional": False,
            "probes": [{"x": 0}],
        },
    ),
    _case(
        "V7_TRUE_NEWTON_CONTROL",
        kind="true_newton_control",
        primary_engine="dd_cert",
        should_be_zero=True,
        description="Genuine first Newton identity: (x**2-y**2)/(x-y) = x+y.",
        symbols=_XY,
        math={
            "kind": "EQUALITY",
            "left": "(x**2 - y**2)/(x - y)",
            "claimed": "x + y",
            "true": "x + y",
            "probes": [{"x": 2, "y": 1}],
        },
    ),
]


CASES_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in ATTACK_CASES}
CONTROL_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in CONTROL_CASES}


def load_attack_cases() -> list[dict[str, Any]]:
    return list(ATTACK_CASES)
