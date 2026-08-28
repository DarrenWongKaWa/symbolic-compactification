"""Adversarial multi-branch families. Data only; checkers live next door.

Toy polynomial families that *look* like Hermite confluence of F(t)=t**3
but are wrong. ``should_be_zero`` is False: a FAMILY_ZERO verdict is a
false certification. The true five-member cubic control is separate and
must remain FAMILY_ZERO so the checker is not an always-NONZERO gate.
"""
from __future__ import annotations

from typing import Any

ATTACK_IDS = (
    "V2H_01_corrupted_branch_coefficient",
    "V2H_02_wrong_factorial",
    "V2H_03_broken_branch",
    "V2H_04_mixed_latent_F",
    "V2H_05_path_inconsistent_recurrence",
    "V2H_06_wrong_derivative_order",
    "V2H_07_wrong_degeneracy_variable",
    "V2H_08_pole_sensitive_false_confluence",
)

ATTACK_KINDS = (
    "corrupted_branch_coefficient",
    "wrong_factorial",
    "broken_branch",
    "mixed_latent_F",
    "path_inconsistent_recurrence",
    "wrong_derivative_order",
    "wrong_degeneracy_variable",
    "pole_sensitive_false_confluence",
)

CONTROL_IDS = ("V2H_TRUE_HERMITE_FAMILY",)

_SYMS = (
    {"name": "t", "real": True},
    {"name": "x", "real": True},
    {"name": "y", "real": True},
    {"name": "w", "real": True},
)

# True cubic Hermite confluence, F(t)=t**3:
#   F[x,y]=x**2+xy+y**2, F[x,x]=3x**2, F[x,x,y]=2x+y,
#   F[x,y,y]=x+2y, F[x,x,x]=F''(x)/2!=3x.
_TRUE_MEMBERS = {
    "M_xy": "x**2 + x*y + y**2",
    "M_xx": "3*x**2",
    "M_xxy": "2*x + y",
    "M_xyy": "x + 2*y",
    "M_xxx": "3*x",
}

_TRUE_MULT = {
    "M_xy": {"x": 1, "y": 1},
    "M_xx": {"x": 2},
    "M_xxy": {"x": 2, "y": 1},
    "M_xyy": {"x": 1, "y": 2},
    "M_xxx": {"x": 3},
}

_TRUE_RECON = (
    {"member_id": "M_xy", "kind": "newton_first"},
    {"member_id": "M_xx", "kind": "repeated_diagonal"},
    {"member_id": "M_xxy", "kind": "hermite_xxy"},
    {"member_id": "M_xyy", "kind": "hermite_xyy"},
    {"member_id": "M_xxx", "kind": "hermite_xxx"},
)

_TRUE_CONFLUENCE = (
    {
        "source": "M_xy",
        "target": "M_xx",
        "variable": "y",
        "target_value": "x",
        "relation": "one_parameter_confluence",
    },
    {
        "source": "M_xxy",
        "target": "M_xxx",
        "variable": "y",
        "target_value": "x",
        "relation": "repeated_node_confluence",
    },
    {
        "source": "M_xyy",
        "target": "M_xxx",
        "variable": "y",
        "target_value": "x",
        "relation": "repeated_node_confluence",
    },
)

_TRUE_RECURRENCE = (
    {
        "kind": "hermite_dd_recurrence",
        "left": "M_xx",
        "right": "M_xy",
        "denom": ["x", "y"],
        "target": "M_xxy",
    },
    {
        "kind": "hermite_dd_recurrence",
        "left": "M_yy",
        "right": "M_xy",
        "denom": ["y", "x"],
        "target": "M_xyy",
        "left_from": "repeated_yy",
    },
)

_TRUE_PATHS = (
    {
        "id": "path_xxy",
        "source": "M_xxy",
        "variable": "y",
        "target_value": "x",
        "target": "M_xxx",
    },
    {
        "id": "path_xyy",
        "source": "M_xyy",
        "variable": "y",
        "target_value": "x",
        "target": "M_xxx",
    },
)

_TRUE_GRAPH = (
    ["M_xy", "M_xx"],
    ["M_xx", "M_xxy"],
    ["M_xy", "M_xxy"],
    ["M_xy", "M_xyy"],
    ["M_xxy", "M_xxx"],
    ["M_xyy", "M_xxx"],
)


def _case(
    cid: str,
    *,
    kind: str,
    description: str,
    trap: str,
    members: dict[str, str],
    reconstructions: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    confluence: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    recurrences: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    paths: tuple[dict[str, Any], ...] | list[dict[str, Any]],
    graph_edges: tuple[list[str], ...] | list[list[str]],
    node_multiplicities: dict[str, dict[str, int]],
    latent_F: str | None = "t**3",
    latent_F_by_member: dict[str, str] | None = None,
    degeneracy_variables: list[str] | None = None,
    should_be_zero: bool = False,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "kind": kind,
        "description": description,
        "trap": trap,
        "should_be_zero": should_be_zero,
        "symbols": list(_SYMS),
        "latent_F": latent_F,
        "latent_F_by_member": dict(latent_F_by_member or {}),
        "members": dict(members),
        "reconstructions": [dict(r) for r in reconstructions],
        "confluence": [dict(e) for e in confluence],
        "recurrences": [dict(e) for e in recurrences],
        "paths": [dict(e) for e in paths],
        "graph_edges": [list(e) for e in graph_edges],
        "node_multiplicities": {
            k: dict(v) for k, v in node_multiplicities.items()
        },
        "degeneracy_variables": list(
            degeneracy_variables if degeneracy_variables is not None else ["y"]
        ),
        "extra": dict(extra or {}),
    }


def _true_members_with(**updates: str) -> dict[str, str]:
    out = dict(_TRUE_MEMBERS)
    out.update(updates)
    return out


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "V2H_01_corrupted_branch_coefficient",
        kind="corrupted_branch_coefficient",
        trap="majority_branch",
        description=(
            "Five-member cubic Hermite family except the generic Newton "
            "branch drops the mixed coefficient: claimed x**2+y**2 instead "
            "of x**2+xy+y**2. Four degenerate members are the true "
            "F[x,x], F[x,x,y], F[x,y,y], F[x,x,x]. Majority of branches "
            "match Hermite; one coefficient does not."
        ),
        members=_true_members_with(M_xy="x**2 + y**2"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "corrupted_member": "M_xy",
            "true_newton": "x**2 + x*y + y**2",
            "claimed_newton": "x**2 + y**2",
        },
    ),
    _case(
        "V2H_02_wrong_factorial",
        kind="wrong_factorial",
        trap="majority_branch",
        description=(
            "F[x,x,x] is claimed as F''(x)/3! = x instead of F''(x)/2! = 3x. "
            "The family still lists multiplicity 3 and the other four "
            "cubic Hermite members are correct. A checker that trusts the "
            "family's factorial instead of k = multiplicity-1 would ZERO."
        ),
        members=_true_members_with(M_xxx="x"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "claimed_factorial": 6,
            "true_factorial": 2,
            "claimed_xxx": "x",
            "true_xxx": "3*x",
        },
    ),
    _case(
        "V2H_03_broken_branch",
        kind="broken_branch",
        trap="majority_branch",
        description=(
            "The (1,2) mixed branch M_xyy is copied from M_xxy: claimed "
            "2x+y instead of x+2y. Four of five members are genuine cubic "
            "Hermite; one mixed branch is broken. Majority vote on branches "
            "is the trap."
        ),
        members=_true_members_with(M_xyy="2*x + y"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "broken_member": "M_xyy",
            "claimed": "2*x + y",
            "true": "x + 2*y",
        },
    ),
    _case(
        "V2H_04_mixed_latent_F",
        kind="mixed_latent_F",
        trap="forgotten_latent_flag",
        description=(
            "Two genuine one-parameter confluences glued as one family: "
            "F(t)=t**3 gives (x**2+xy+y**2)→3x**2, and G(t)=t**2 gives "
            "(x+y)→2x. Every local reconstruction and confluence edge is "
            "ZERO against its own latent polynomial. The required graph is "
            "disconnected and the latents are not compatible. A composer "
            "that only inspects edge ZERO would false-certify the family."
        ),
        members={
            "A_xy": "x**2 + x*y + y**2",
            "A_xx": "3*x**2",
            "B_xy": "x + y",
            "B_xx": "2*x",
        },
        latent_F=None,
        latent_F_by_member={
            "A_xy": "t**3",
            "A_xx": "t**3",
            "B_xy": "t**2",
            "B_xx": "t**2",
        },
        reconstructions=(
            {"member_id": "A_xy", "kind": "newton_first"},
            {"member_id": "A_xx", "kind": "repeated_diagonal"},
            {"member_id": "B_xy", "kind": "newton_first"},
            {"member_id": "B_xx", "kind": "repeated_diagonal"},
        ),
        confluence=(
            {
                "source": "A_xy",
                "target": "A_xx",
                "variable": "y",
                "target_value": "x",
                "relation": "one_parameter_confluence",
            },
            {
                "source": "B_xy",
                "target": "B_xx",
                "variable": "y",
                "target_value": "x",
                "relation": "one_parameter_confluence",
            },
        ),
        recurrences=(),
        paths=(),
        graph_edges=(["A_xy", "A_xx"], ["B_xy", "B_xx"]),
        node_multiplicities={
            "A_xy": {"x": 1, "y": 1},
            "A_xx": {"x": 2},
            "B_xy": {"x": 1, "y": 1},
            "B_xx": {"x": 2},
        },
        extra={"latents": ["t**3", "t**2"]},
    ),
    _case(
        "V2H_05_path_inconsistent_recurrence",
        kind="path_inconsistent_recurrence",
        trap="single_path",
        description=(
            "All five cubic Hermite members are algebraically correct, but "
            "both Newton recurrences are claimed to reconstruct the same "
            "mixed member M_xxy=2x+y. The (y,y) recurrence actually "
            "equals M_xyy=x+2y. One path ZERO is not path consistency; "
            "the two coalescence orders disagree as claimed."
        ),
        members=dict(_TRUE_MEMBERS),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=(
            _TRUE_RECURRENCE[0],
            {
                "kind": "hermite_dd_recurrence",
                "left": "M_yy",
                "right": "M_xy",
                "denom": ["y", "x"],
                "target": "M_xxy",
                "left_from": "repeated_yy",
            },
        ),
        paths=(
            _TRUE_PATHS[0],
            {
                "id": "path_xyy",
                "source": "M_xyy",
                "variable": "y",
                "target_value": "x",
                "target": "M_xxy",
            },
        ),
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "claimed_shared_member": "M_xxy",
            "true_xyy_recurrence": "x + 2*y",
        },
    ),
    _case(
        "V2H_06_wrong_derivative_order",
        kind="wrong_derivative_order",
        trap="majority_branch",
        description=(
            "The triple node is listed with multiplicity 3 but filled with "
            "F'(x)=3x**2 (the two-node diagonal) instead of F''(x)/2!=3x. "
            "Looks like Hermite confluence; the derivative order is one "
            "too low."
        ),
        members=_true_members_with(M_xxx="3*x**2"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "claimed_order": 1,
            "true_order": 2,
            "claimed_xxx": "3*x**2",
            "true_xxx": "3*x",
        },
    ),
    _case(
        "V2H_07_wrong_degeneracy_variable",
        kind="wrong_degeneracy_variable",
        trap="majority_branch",
        description=(
            "Claimed confluence is y→x, but the listed diagonal is the "
            "spectator coalescence y→w: x**2+x*w+w**2, not 3x**2. The "
            "degeneracy variable is wrong; four other cubic members stay "
            "true."
        ),
        members=_true_members_with(M_xx="x**2 + x*w + w**2"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        degeneracy_variables=["y"],
        extra={
            "claimed_limit": "y -> x",
            "actual_substitution": "y -> w",
            "claimed_xx": "x**2 + x*w + w**2",
            "true_xx": "3*x**2",
        },
    ),
    _case(
        "V2H_08_pole_sensitive_false_confluence",
        kind="pole_sensitive_false_confluence",
        trap="majority_branch",
        description=(
            "Generic slot is the polar kernel (x**3-y**3)/(x-y)**2, claimed "
            "to confluence to the polynomial diagonal 3x**2. After one "
            "(x-y) cancel the pole remains; two-sided limit is infinite "
            "and directional limits disagree in sign. The other four "
            "members are true cubic Hermite polynomials."
        ),
        members=_true_members_with(M_xy="(x**3 - y**3)/(x - y)**2"),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
        extra={
            "claimed_generic": "(x**3 - y**3)/(x - y)**2",
            "true_newton": "x**2 + x*y + y**2",
            "claimed_limit": "3*x**2",
        },
    ),
]

CONTROL_CASES: list[dict[str, Any]] = [
    _case(
        "V2H_TRUE_HERMITE_FAMILY",
        kind="true_hermite_family",
        trap="none",
        should_be_zero=True,
        description=(
            "Genuine five-member cubic Hermite confluence of F(t)=t**3: "
            "Newton F[x,y], repeated F[x,x], mixed F[x,x,y] and F[x,y,y], "
            "triple F[x,x,x]=F''(x)/2!. All required edges, recurrences, "
            "and both coalescence paths are identities."
        ),
        members=dict(_TRUE_MEMBERS),
        reconstructions=_TRUE_RECON,
        confluence=_TRUE_CONFLUENCE,
        recurrences=_TRUE_RECURRENCE,
        paths=_TRUE_PATHS,
        graph_edges=_TRUE_GRAPH,
        node_multiplicities=_TRUE_MULT,
    ),
]

CASES_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in ATTACK_CASES}
CONTROL_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in CONTROL_CASES}


def load_attack_cases() -> list[dict[str, Any]]:
    return list(ATTACK_CASES)


def load_control_cases() -> list[dict[str, Any]]:
    return list(CONTROL_CASES)
