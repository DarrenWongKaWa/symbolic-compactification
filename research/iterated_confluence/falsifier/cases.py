"""Adversarial iterated-path families. Data only; checkers live next door.

Toy families that *look* pairwise-confluent along some one-parameter path
and are not a commuting family. ``expect`` is never FAMILY_ZERO on attacks:
a FAMILY_ZERO verdict is a false certification of the leap
pairwise confluence → global family.
"""
from __future__ import annotations

from typing import Any

from research.iterated_confluence.schema import FAMILY_NONZERO, FAMILY_UNKNOWN, FAMILY_ZERO

ATTACK_IDS = (
    "V3J_01_one_path_zero_other_nonzero",
    "V3J_02_noncommuting_limits",
    "V3J_03_hidden_pole",
    "V3J_04_corrupted_intermediate",
    "V3J_05_wrong_equality_surface",
    "V3J_06_path_dependent_repeated_node",
    "V3J_07_spectator_mismatch",
    "V3J_08_majority_path_unknown",
)

ATTACK_KINDS = (
    "one_path_zero_other_nonzero",
    "noncommuting_limits",
    "hidden_pole",
    "corrupted_intermediate",
    "wrong_equality_surface",
    "path_dependent_repeated_node",
    "spectator_mismatch",
    "majority_path_unknown",
)

CONTROL_IDS = (
    "V3J_POS_commuting_iterated_linear",
    "V3J_POS_commuting_cubic_nodes",
)

_SYMS = (
    {"name": "x", "real": True},
    {"name": "y", "real": True},
    {"name": "w", "real": True},
    {"name": "n", "real": True},
    {"name": "m", "real": True},
)


def _step(
    source: str,
    target: str,
    *,
    variable: str = "",
    target_value: str = "",
    relation: str = "one_parameter_confluence",
    opaque: bool = False,
    unknown_reason: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "source": source,
        "target": target,
        "variable": variable,
        "target_value": target_value,
        "relation": relation,
    }
    if opaque:
        row["opaque"] = True
        row["unknown_reason"] = unknown_reason or "size_guard"
    return row


def _path(
    path_id: str,
    start: str,
    end: str,
    steps: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "path_id": path_id,
        "start_member": start,
        "end_member": end,
        "steps": list(steps),
    }


def _rec(member_id: str, reconstructed: str) -> dict[str, str]:
    return {"member_id": member_id, "reconstructed": reconstructed}


def _cons(path_a: str, path_b: str, start: str, end: str) -> dict[str, str]:
    return {"path_a": path_a, "path_b": path_b, "start": start, "end": end}


def _case(
    cid: str,
    *,
    kind: str,
    expect: str,
    description: str,
    trap: str,
    members: dict[str, str],
    paths: list[dict[str, Any]],
    reconstructions: list[dict[str, str]] | None = None,
    consistency: list[dict[str, str]] | None = None,
    require_path_independence: bool = True,
    should_be_zero: bool = False,
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
        "members": dict(members),
        "paths": [dict(p) for p in paths],
        "reconstructions": [dict(r) for r in (reconstructions or [])],
        "consistency": [dict(c) for c in (consistency or [])],
        "require_path_independence": bool(require_path_independence),
        "extra": dict(extra or {}),
    }


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "V3J_01_one_path_zero_other_nonzero",
        kind="one_path_zero_other_nonzero",
        expect=FAMILY_NONZERO,
        trap="one_path_zero",
        description=(
            "Generic x+y coalesces to 2x along y→x (local edges ZERO) but the "
            "second path x→y is filled with 3y instead of 2y. One PATH_ZERO "
            "is not a family; the other path is PATH_NONZERO."
        ),
        members={"G": "x + y", "Dx": "2*x", "Dy": "3*y"},
        paths=[
            _path(
                "p_y",
                "G",
                "Dx",
                [_step("G", "Dx", variable="y", target_value="x")],
            ),
            _path(
                "p_x",
                "G",
                "Dy",
                [_step("G", "Dy", variable="x", target_value="y")],
            ),
        ],
        reconstructions=[_rec("Dx", "2*x"), _rec("Dy", "3*y")],
        extra={"true_dy": "2*y", "claimed_dy": "3*y"},
    ),
    _case(
        "V3J_02_noncommuting_limits",
        kind="noncommuting_limits",
        expect=FAMILY_NONZERO,
        trap="missing_consistency",
        description=(
            "Iterated limits of x/(x+y): y→0 then x→0 equals 1; x→0 then y→0 "
            "equals 0. Each declared path has locally ZERO steps against its "
            "own intermediates, but the two orders disagree. Iterated limit "
            "is not joint limit; consistency is INCONSISTENT_NONZERO."
        ),
        members={
            "G": "x/(x + y)",
            "A": "1",
            "B": "0",
            "Za": "1",
            "Zb": "0",
        },
        paths=[
            _path(
                "p_yx",
                "G",
                "Za",
                [
                    _step("G", "A", variable="y", target_value="0", relation="limit"),
                    _step("A", "Za", variable="x", target_value="0", relation="limit"),
                ],
            ),
            _path(
                "p_xy",
                "G",
                "Zb",
                [
                    _step("G", "B", variable="x", target_value="0", relation="limit"),
                    _step("B", "Zb", variable="y", target_value="0", relation="limit"),
                ],
            ),
        ],
        reconstructions=[
            _rec("A", "1"),
            _rec("B", "0"),
            _rec("Za", "1"),
            _rec("Zb", "0"),
        ],
        consistency=[_cons("p_yx", "p_xy", "G", "joint_0")],
        extra={"iter_yx": "1", "iter_xy": "0"},
    ),
    _case(
        "V3J_03_hidden_pole",
        kind="hidden_pole",
        expect=FAMILY_NONZERO,
        trap="ignore_polar_path",
        description=(
            "Sibling polynomial (x+y)→2x is PATH_ZERO, but the polar kernel "
            "(x**2-y**2)/(x-y)**2 is claimed to confluence to the same 2x. "
            "One (x-y) cancel leaves a pole; directional limits disagree "
            "and are infinite. One hidden pole is FAMILY_NONZERO."
        ),
        members={
            "Q": "x + y",
            "P": "(x**2 - y**2)/(x - y)**2",
            "D": "2*x",
        },
        paths=[
            _path(
                "p_poly",
                "Q",
                "D",
                [_step("Q", "D", variable="y", target_value="x")],
            ),
            _path(
                "p_pole",
                "P",
                "D",
                [_step("P", "D", variable="y", target_value="x")],
            ),
        ],
        reconstructions=[_rec("D", "2*x"), _rec("Q", "x + y")],
        consistency=[_cons("p_poly", "p_pole", "joint_generic", "D")],
        extra={"claimed_limit": "2*x", "true_cancelled": "(x + y)/(x - y)"},
    ),
    _case(
        "V3J_04_corrupted_intermediate",
        kind="corrupted_intermediate",
        expect=FAMILY_NONZERO,
        trap="skip_intermediate",
        description=(
            "True y→x coalescence of x**2+x*y+y**2 is 3x**2, but the declared "
            "path inserts a corrupted intermediate 2x**2. Start→end skipping "
            "the intermediate is ZERO; the required path through the branch "
            "is not. Reconstruction of the intermediate is NONZERO."
        ),
        members={"G": "x**2 + x*y + y**2", "Mid": "2*x**2", "End": "3*x**2"},
        paths=[
            _path(
                "through_mid",
                "G",
                "End",
                [
                    _step("G", "Mid", variable="y", target_value="x"),
                    _step("Mid", "End", relation="substitution"),
                ],
            ),
        ],
        reconstructions=[
            _rec("Mid", "3*x**2"),
            _rec("End", "3*x**2"),
            _rec("G", "x**2 + x*y + y**2"),
        ],
        extra={"true_mid": "3*x**2", "claimed_mid": "2*x**2", "skip_end": "3*x**2"},
    ),
    _case(
        "V3J_05_wrong_equality_surface",
        kind="wrong_equality_surface",
        expect=FAMILY_NONZERO,
        trap="surface_restricted_residual",
        description=(
            "x**2+y is claimed identical to x**2+x. The residual y-x vanishes "
            "on the degeneracy surface y=x but is not identically zero. A "
            "sibling (x+y)→2x path is genuinely PATH_ZERO; surface-restricted "
            "equality is the trap, not a certificate."
        ),
        members={"A": "x**2 + y", "B": "x**2 + x", "C": "x + y", "D": "2*x"},
        paths=[
            _path(
                "false_identity",
                "A",
                "B",
                [_step("A", "B", relation="substitution")],
            ),
            _path(
                "true_confluence",
                "C",
                "D",
                [_step("C", "D", variable="y", target_value="x")],
            ),
        ],
        reconstructions=[_rec("B", "x**2 + x"), _rec("D", "2*x")],
        extra={"surface": {"variable": "y", "value": "x"}, "residual": "y - x"},
    ),
    _case(
        "V3J_06_path_dependent_repeated_node",
        kind="path_dependent_repeated_node",
        expect=FAMILY_NONZERO,
        trap="one_repeated_node_path",
        description=(
            "Repeated-node coalescence y→x of 2x+y is 3x (PATH_ZERO), but the "
            "companion mixed node is x+2y+1, which coalesces to 3x+1. The two "
            "orders of forming the triple node disagree; one PATH_ZERO is not "
            "path independence."
        ),
        members={"M_xxy": "2*x + y", "M_xyy": "x + 2*y + 1", "M_xxx": "3*x"},
        paths=[
            _path(
                "p_xxy",
                "M_xxy",
                "M_xxx",
                [
                    _step(
                        "M_xxy",
                        "M_xxx",
                        variable="y",
                        target_value="x",
                        relation="repeated_node_confluence",
                    )
                ],
            ),
            _path(
                "p_xyy",
                "M_xyy",
                "M_xxx",
                [
                    _step(
                        "M_xyy",
                        "M_xxx",
                        variable="y",
                        target_value="x",
                        relation="repeated_node_confluence",
                    )
                ],
            ),
        ],
        reconstructions=[
            _rec("M_xxy", "2*x + y"),
            _rec("M_xxx", "3*x"),
            _rec("M_xyy", "x + 2*y"),
        ],
        consistency=[_cons("p_xxy", "p_xyy", "mixed", "M_xxx")],
        extra={"true_xyy": "x + 2*y", "claimed_xyy": "x + 2*y + 1"},
    ),
    _case(
        "V3J_07_spectator_mismatch",
        kind="spectator_mismatch",
        expect=FAMILY_NONZERO,
        trap="local_kernel_only",
        description=(
            "Local kernels (x+y)→2x are PATH_ZERO, and two members reconstruct "
            "against spectator n+m. The remaining degenerate member is "
            "(n+2m)*2x, a different spectator claimed as the same common "
            "factor. False common factor: reconstruction NONZERO."
        ),
        members={
            "K_xy": "(n + m)*(x + y)",
            "K_xx": "(n + 2*m)*(2*x)",
            "K_yy": "(n + m)*(2*y)",
            "L_xy": "x + y",
            "L_xx": "2*x",
        },
        paths=[
            _path(
                "p_local",
                "L_xy",
                "L_xx",
                [_step("L_xy", "L_xx", variable="y", target_value="x")],
            ),
        ],
        reconstructions=[
            _rec("K_xy", "(n + m)*(x + y)"),
            _rec("K_yy", "(n + m)*(2*y)"),
            _rec("K_xx", "(n + m)*(2*x)"),
        ],
        extra={
            "claimed_spectator": "n + m",
            "actual_xx_spectator": "n + 2*m",
        },
    ),
    _case(
        "V3J_08_majority_path_unknown",
        kind="majority_path_unknown",
        expect=FAMILY_UNKNOWN,
        trap="majority_paths",
        description=(
            "Two Newton paths (x+y)→2x and (x+w)→2x are PATH_ZERO. A third "
            "required path is size-guarded and therefore PATH_UNKNOWN. "
            "Majority PATH_ZERO plus one PATH_UNKNOWN is not FAMILY_ZERO. "
            "Timeout/size-guard is UNKNOWN, never ZERO."
        ),
        members={"A": "x + y", "Ax": "2*x", "B": "x + w", "Bx": "2*x", "Cx": "2*x"},
        paths=[
            _path(
                "p_a",
                "A",
                "Ax",
                [_step("A", "Ax", variable="y", target_value="x")],
            ),
            _path(
                "p_b",
                "B",
                "Bx",
                [_step("B", "Bx", variable="w", target_value="x")],
            ),
            _path(
                "p_c",
                "C",
                "Cx",
                [
                    _step(
                        "C",
                        "Cx",
                        variable="y",
                        target_value="x",
                        opaque=True,
                        unknown_reason="size_guard",
                    )
                ],
            ),
        ],
        reconstructions=[_rec("Ax", "2*x"), _rec("Bx", "2*x")],
        extra={"unknown_reason": "size_guard"},
    ),
]

CONTROL_CASES: list[dict[str, Any]] = [
    _case(
        "V3J_POS_commuting_iterated_linear",
        kind="commuting_iterated_linear",
        expect=FAMILY_ZERO,
        should_be_zero=True,
        trap="none",
        description=(
            "Genuine commuting iterated limits of the polynomial x+y: "
            "y→0 then x→0, and x→0 then y→0, both equal 0. All local "
            "edges ZERO, reconstruction ZERO, path consistency "
            "CONSISTENT_ZERO."
        ),
        members={"G": "x + y", "X": "x", "Y": "y", "Z": "0"},
        paths=[
            _path(
                "p_yx",
                "G",
                "Z",
                [
                    _step("G", "X", variable="y", target_value="0", relation="limit"),
                    _step("X", "Z", variable="x", target_value="0", relation="limit"),
                ],
            ),
            _path(
                "p_xy",
                "G",
                "Z",
                [
                    _step("G", "Y", variable="x", target_value="0", relation="limit"),
                    _step("Y", "Z", variable="y", target_value="0", relation="limit"),
                ],
            ),
        ],
        reconstructions=[
            _rec("X", "x"),
            _rec("Y", "y"),
            _rec("Z", "0"),
            _rec("G", "x + y"),
        ],
        consistency=[_cons("p_yx", "p_xy", "G", "Z")],
    ),
    _case(
        "V3J_POS_commuting_cubic_nodes",
        kind="commuting_cubic_nodes",
        expect=FAMILY_ZERO,
        should_be_zero=True,
        trap="none",
        description=(
            "Genuine cubic polynomial family: Newton x**2+xy+y**2 → 3x**2, "
            "and both mixed nodes 2x+y and x+2y coalesce to the triple 3x. "
            "The two repeated-node orders agree. All obligations ZERO and "
            "consistency CONSISTENT_ZERO."
        ),
        members={
            "M_xy": "x**2 + x*y + y**2",
            "M_xx": "3*x**2",
            "M_xxy": "2*x + y",
            "M_xyy": "x + 2*y",
            "M_xxx": "3*x",
        },
        paths=[
            _path(
                "p_newton",
                "M_xy",
                "M_xx",
                [_step("M_xy", "M_xx", variable="y", target_value="x")],
            ),
            _path(
                "p_xxy",
                "M_xxy",
                "M_xxx",
                [
                    _step(
                        "M_xxy",
                        "M_xxx",
                        variable="y",
                        target_value="x",
                        relation="repeated_node_confluence",
                    )
                ],
            ),
            _path(
                "p_xyy",
                "M_xyy",
                "M_xxx",
                [
                    _step(
                        "M_xyy",
                        "M_xxx",
                        variable="y",
                        target_value="x",
                        relation="repeated_node_confluence",
                    )
                ],
            ),
        ],
        reconstructions=[
            _rec("M_xy", "x**2 + x*y + y**2"),
            _rec("M_xx", "3*x**2"),
            _rec("M_xxy", "2*x + y"),
            _rec("M_xyy", "x + 2*y"),
            _rec("M_xxx", "3*x"),
        ],
        consistency=[_cons("p_xxy", "p_xyy", "mixed", "M_xxx")],
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
