"""Adversarial representation claims. Data only; checkers live next door.

Each case is a JSON-serializable dict. `should_be_zero` is always False:
these are attacks, not identities. Audit classes are from
`research.representation_invention.labels.AUDIT_CLASSES`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

ATTACK_IDS = (
    "F01_fake_confluence",
    "F02_wrong_repeated_node",
    "F03_pole_sensitive_recurrence",
    "F04_special_function_order",
    "F05_invalid_limit",
    "F06_sign_flipped_dd",
    "F07_broken_symmetry_coefficient",
    "F08_tautological_master",
    "F09_overgeneralized_latent",
    "F10_ambiguous_member_maps",
)

# Residual of A-A is algebraically ZERO; the claim is still false.
# Local structural audit must reject; an obligations residual-ZERO here
# is a tautology leak, not certification.
TAUTOLOGY_RESIDUAL_IDS = (
    "F08_tautological_master",
    "F09_overgeneralized_latent",
)

MATH_NONZERO_IDS = tuple(
    i for i in ATTACK_IDS if i not in TAUTOLOGY_RESIDUAL_IDS
)


def _hyp(**kwargs: Any) -> dict[str, Any]:
    base = {
        "representation_type": "other_explicit",
        "member_ids": [],
        "member_roles": {},
        "latent_object": "F(z)",
        "latent_variables": ["z"],
        "nodes": [],
        "operators": [],
        "instance_maps": {},
        "reconstruction_rule": "",
        "required_assumptions": [],
        "proof_obligations": [],
        "scientific_rationale": "",
        "confidence": 0.8,
    }
    base.update(kwargs)
    return base


def _case(
    cid: str,
    *,
    description: str,
    expected_audit_class: str,
    attack_kind: str,
    catalog: dict[str, str],
    hypothesis: dict[str, Any],
    math: dict[str, Any] | None = None,
    member_maps: list[dict[str, Any]] | None = None,
    checkable: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": cid,
        "description": description,
        "should_be_zero": False,
        "expected_audit_class": expected_audit_class,
        "attack_kind": attack_kind,
        "catalog": catalog,
        "hypothesis": hypothesis,
        "math": math or {},
        "member_maps": member_maps or [],
        "checkable": checkable
        or {
            "local_residual": True,
            "structural_audit": False,
            "parse": True,
            "obligations": "if_present",
        },
    }


ATTACK_CASES: list[dict[str, Any]] = [
    _case(
        "F01_fake_confluence",
        description=(
            "Piecewise true-branch (sin(x)-sin(y))/(x-y) is claimed confluent "
            "to the Eq-branch sin(x). The branches look related, but "
            "limit(y->x) of the generic branch is cos(x), not sin(x)."
        ),
        expected_audit_class="WRONG_CONFLUENCE",
        attack_kind="fake_confluence",
        catalog={
            "G0001": "(sin(x) - sin(y))/(x - y)",
            "G0002": "sin(x)",
        },
        hypothesis=_hyp(
            representation_type="local_confluence",
            member_ids=["G0001", "G0002"],
            member_roles={"G0001": "generic", "G0002": "degenerate"},
            latent_object="F(z) = sin(z)",
            latent_variables=["z"],
            nodes=[
                {"name": "x", "expression": "x", "multiplicity": 1},
                {"name": "y", "expression": "y", "multiplicity": 1},
            ],
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
                {
                    "member_id": "G0002",
                    "kind": "limit",
                    "args": {"var": "y", "to": "x"},
                },
            ],
            instance_maps={
                "G0001": {"theta": {}, "branch": "True"},
                "G0002": {"theta": {"y": "x"}, "branch": "Eq(x, y)"},
            },
            reconstruction_rule="limit(G0001, y -> x) == G0002",
            proof_obligations=[
                {
                    "kind": "CONFLUENCE",
                    "member_ids": ["G0001", "G0002"],
                    "left": "(sin(x) - sin(y))/(x - y)",
                    "right": "sin(x)",
                    "operator": "limit",
                    "expected": "limit(generic, y, x) == degenerate",
                    "variables": {"var": "y", "to": "x"},
                }
            ],
            scientific_rationale=(
                "Both Piecewise branches mention sin, so the diagonal is "
                "claimed to be the same kernel."
            ),
            confidence=0.86,
        ),
        math={
            "symbols": [
                {"name": "x", "real": True},
                {"name": "y", "real": True},
            ],
            "functions": [],
            "generic": "(sin(x) - sin(y))/(x - y)",
            "degenerate": "sin(x)",
            "limit_var": "y",
            "limit_to": "x",
            "source_piecewise": (
                "Piecewise(((sin(x)-sin(y))/(x-y), True), (sin(x), Eq(x, y)))"
            ),
        },
        checkable={
            "local_residual": True,
            "structural_audit": False,
            "parse": True,
            "obligations": "if_present",
        },
    ),
    _case(
        "F02_wrong_repeated_node",
        description=(
            "Off-diagonal Newton F[x,y] for F(z)=z**3 is claimed to be the "
            "repeated-node value F[x,x]=F'(x)=3*x**2. Nodes are written with "
            "multiplicity 2, but the member still depends on distinct x,y."
        ),
        expected_audit_class="WRONG_DD_NODE_STRUCTURE",
        attack_kind="wrong_repeated_node",
        catalog={"G0001": "(x**3 - y**3)/(x - y)"},
        hypothesis=_hyp(
            representation_type="hermite_divided_difference",
            member_ids=["G0001"],
            member_roles={"G0001": "repeated"},
            latent_object="F(z) = z**3",
            latent_variables=["z"],
            nodes=[{"name": "x", "expression": "x", "multiplicity": 2}],
            operators=[
                {
                    "member_id": "G0001",
                    "kind": "hermite_dd",
                    "args": {"nodes": ["x", "x"]},
                }
            ],
            instance_maps={
                "G0001": {"theta": {"z": "x"}, "nodes": ["x", "x"]},
            },
            reconstruction_rule="A = F[x,x] = dF/dz at x",
            proof_obligations=[
                {
                    "kind": "HERMITE_DD",
                    "member_ids": ["G0001"],
                    "left": "(x**3 - y**3)/(x - y)",
                    "right": "3*x**2",
                    "operator": "hermite_dd",
                    "expected": "member == F[x,x]",
                }
            ],
            scientific_rationale="Repeated-node DD claimed for a two-node member.",
            confidence=0.84,
        ),
        math={
            "symbols": [
                {"name": "x", "real": True},
                {"name": "y", "real": True},
                {"name": "z", "real": True},
            ],
            "functions": [],
            "F": "z**3",
            "F_var": "z",
            "member": "(x**3 - y**3)/(x - y)",
            "claimed_repeated": "3*x**2",
            "node_x": "x",
            "node_y": "y",
        },
    ),
    _case(
        "F03_pole_sensitive_recurrence",
        description=(
            "Trigamma is given the digamma-style recurrence "
            "polygamma(1,z+1) = polygamma(1,z) + 1/z**2. The true shift is "
            "minus 1/z**2; the error is the polar part and blows up at z=0."
        ),
        expected_audit_class="NONZERO",
        attack_kind="pole_sensitive_recurrence",
        catalog={
            "G0001": "polygamma(1, z)",
            "G0002": "polygamma(1, z + 1)",
        },
        hypothesis=_hyp(
            representation_type="recurrence_family",
            member_ids=["G0001", "G0002"],
            member_roles={"G0001": "generic", "G0002": "instance"},
            latent_object="F(z) = polygamma(1, z)",
            latent_variables=["z"],
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
                {
                    "member_id": "G0002",
                    "kind": "recurrence",
                    "args": {
                        "shift": "z",
                        "step": "1",
                        "rhs": "1/z**2",
                        "addend": "1/z**2",
                    },
                },
            ],
            instance_maps={
                "G0001": {"theta": {"z": "z"}},
                "G0002": {"theta": {"z": "z + 1"}},
            },
            reconstruction_rule="F(z+1) = F(z) + 1/z**2",
            proof_obligations=[
                {
                    "kind": "RECURRENCE",
                    "member_ids": ["G0001", "G0002"],
                    "left": "polygamma(1, z + 1)",
                    "right": "polygamma(1, z) + 1/z**2",
                    "operator": "recurrence",
                    "expected": "G0002 - G0001 - 1/z**2 == 0",
                    "variables": {"rhs": "1/z**2", "shift": "z", "step": "1"},
                }
            ],
            scientific_rationale=(
                "Copies the n=0 shift sign onto n=1; false at the pole z=0."
            ),
            confidence=0.8,
        ),
        math={
            "symbols": [{"name": "z", "real": True}],
            "functions": [],
            "left": "polygamma(1, z + 1)",
            "claimed_right": "polygamma(1, z) + 1/z**2",
            "true_right": "polygamma(1, z) - 1/z**2",
            "pole": "0",
            "use_expand_func": True,
            "rational_witness_left": "1/z - 1/(z - 1)",
            "rational_witness_right": "1/(z*(z - 1))",
        },
    ),
    _case(
        "F04_special_function_order",
        description=(
            "polygamma(1,z) is claimed to be the identity instance of "
            "F(z)=polygamma(0,z). The functions match by name and argument "
            "but not by order: d/dz polygamma(0,z) = polygamma(1,z)."
        ),
        expected_audit_class="WRONG_OPERATOR",
        attack_kind="special_function_order",
        catalog={
            "G0001": "polygamma(0, z)",
            "G0002": "polygamma(1, z)",
        },
        hypothesis=_hyp(
            representation_type="derivative_family",
            member_ids=["G0001", "G0002"],
            member_roles={"G0001": "generic", "G0002": "instance"},
            latent_object="F(z) = polygamma(0, z)",
            latent_variables=["z"],
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
                {"member_id": "G0002", "kind": "identity", "args": {}},
            ],
            instance_maps={
                "G0001": {"theta": {"z": "z"}},
                "G0002": {"theta": {"z": "z"}},
            },
            reconstruction_rule="G0002 = F(z)  (identity, not d/dz)",
            proof_obligations=[
                {
                    "kind": "EQUALITY",
                    "member_ids": ["G0001", "G0002"],
                    "left": "polygamma(1, z)",
                    "right": "polygamma(0, z)",
                    "operator": "identity",
                    "expected": "polygamma(1, z) == polygamma(0, z)",
                }
            ],
            scientific_rationale="Same special function, wrong order.",
            confidence=0.77,
        ),
        math={
            "symbols": [{"name": "z", "real": True}],
            "functions": [],
            "left": "polygamma(0, z)",
            "right": "polygamma(1, z)",
            "order_left": 0,
            "order_right": 1,
        },
    ),
    _case(
        "F05_invalid_limit",
        description=(
            "Claimed two-sided limit y->x of 1/(x-y) equals the finite "
            "diagonal value 0 (the dummy Eq-branch of a Piecewise). "
            "Directional limits disagree (oo vs -oo); no finite limit exists."
        ),
        expected_audit_class="WRONG_CONFLUENCE",
        attack_kind="invalid_limit",
        catalog={"G0001": "1/(x - y)", "G0002": "0"},
        hypothesis=_hyp(
            representation_type="local_confluence",
            member_ids=["G0001", "G0002"],
            member_roles={"G0001": "generic", "G0002": "degenerate"},
            latent_object="F(z) = 1/z",
            latent_variables=["z"],
            nodes=[
                {"name": "x", "expression": "x", "multiplicity": 1},
                {"name": "y", "expression": "y", "multiplicity": 1},
            ],
            operators=[
                {
                    "member_id": "G0002",
                    "kind": "limit",
                    "args": {"var": "y", "to": "x"},
                }
            ],
            instance_maps={
                "G0001": {"theta": {}},
                "G0002": {"theta": {"y": "x"}},
            },
            reconstruction_rule="limit(1/(x-y), y->x) == 0",
            proof_obligations=[
                {
                    "kind": "LIMIT",
                    "member_ids": ["G0001", "G0002"],
                    "left": "1/(x - y)",
                    "right": "0",
                    "operator": "limit",
                    "expected": "limit == 0",
                    "variables": {"var": "y", "to": "x"},
                }
            ],
            scientific_rationale=(
                "Substituting the Piecewise Eq branch for a limit of a pole."
            ),
            confidence=0.7,
        ),
        math={
            "symbols": [
                {"name": "x", "real": True},
                {"name": "y", "real": True},
            ],
            "functions": [],
            "expr": "1/(x - y)",
            "limit_var": "y",
            "limit_to": "x",
            "claimed_value": "0",
            "check_directional": True,
        },
    ),
    _case(
        "F06_sign_flipped_dd",
        description=(
            "Member is the sign-flipped formula (F(y)-F(x))/(x-y) for "
            "F(z)=z**3, claimed as the Newton first DD (F(x)-F(y))/(x-y)."
        ),
        expected_audit_class="WRONG_OPERATOR",
        attack_kind="sign_flipped_dd",
        catalog={"G0001": "(y**3 - x**3)/(x - y)"},
        hypothesis=_hyp(
            representation_type="divided_difference",
            member_ids=["G0001"],
            member_roles={"G0001": "generic"},
            latent_object="F(z) = z**3",
            latent_variables=["z"],
            nodes=[
                {"name": "x", "expression": "x", "multiplicity": 1},
                {"name": "y", "expression": "y", "multiplicity": 1},
            ],
            operators=[
                {
                    "member_id": "G0001",
                    "kind": "newton_dd",
                    "args": {"nodes": ["x", "y"], "sign": -1},
                }
            ],
            instance_maps={"G0001": {"theta": {}, "nodes": ["x", "y"]}},
            reconstruction_rule="A = (F(x)-F(y))/(x-y)",
            proof_obligations=[
                {
                    "kind": "NEWTON_DD",
                    "member_ids": ["G0001"],
                    "left": "(y**3 - x**3)/(x - y)",
                    "right": "(x**3 - y**3)/(x - y)",
                    "operator": "newton_dd",
                    "expected": "member == newton_first",
                }
            ],
            scientific_rationale="DD with swapped numerator sign.",
            confidence=0.82,
        ),
        math={
            "symbols": [
                {"name": "x", "real": True},
                {"name": "y", "real": True},
                {"name": "z", "real": True},
            ],
            "functions": [],
            "F": "z**3",
            "F_var": "z",
            "node_x": "x",
            "node_y": "y",
            "member": "(y**3 - x**3)/(x - y)",
        },
    ),
    _case(
        "F07_broken_symmetry_coefficient",
        description=(
            "Orbit sum f(i,j)+f(j,i) is reconstructed as 2*f(i,j). That "
            "coefficient is valid only if f is already symmetric; for a "
            "generic kernel the swapped term is dropped."
        ),
        expected_audit_class="WRONG_OPERATOR",
        attack_kind="broken_symmetry_coefficient",
        catalog={"G0001": "f(i, j) + f(j, i)"},
        hypothesis=_hyp(
            representation_type="invariant_basis",
            member_ids=["G0001"],
            member_roles={"G0001": "kernel"},
            latent_object="F(x, y) = f(x, y)",
            latent_variables=["x", "y"],
            operators=[
                {
                    "member_id": "G0001",
                    "kind": "permutation",
                    "args": {"coefficient": 2, "swap": False},
                }
            ],
            instance_maps={
                "G0001": {"theta": {"x": "i", "y": "j"}, "coefficient": 2},
            },
            reconstruction_rule="A = 2*F(i,j)",
            proof_obligations=[
                {
                    "kind": "PERMUTATION",
                    "member_ids": ["G0001"],
                    "left": "f(i, j) + f(j, i)",
                    "right": "2*f(i, j)",
                    "operator": "permutation",
                    "expected": "orbit_sum == 2*identity",
                }
            ],
            scientific_rationale="Symmetrizer coefficient 2 without the swap.",
            confidence=0.75,
        ),
        math={
            "symbols": [
                {"name": "i", "real": True},
                {"name": "j", "real": True},
            ],
            "functions": ["f"],
            "left": "f(i, j) + f(j, i)",
            "claimed_right": "2*f(i, j)",
        },
    ),
    _case(
        "F08_tautological_master",
        description=(
            "Master object is F := A used once: a single member, identity "
            "operator, latent RHS identical to that member. Residual A-A is "
            "trivial zero and must not certify discovery."
        ),
        expected_audit_class="TAUTOLOGICAL_MASTER",
        attack_kind="tautological_master",
        catalog={"G0001": "x**2 + 1"},
        hypothesis=_hyp(
            representation_type="master_function",
            member_ids=["G0001"],
            member_roles={"G0001": "instance"},
            latent_object="F(z) := x**2 + 1",
            latent_variables=["z"],
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
            ],
            instance_maps={"G0001": {"theta": {}}},
            reconstruction_rule="F := A",
            proof_obligations=[
                {
                    "kind": "MASTER_INSTANCE",
                    "member_ids": ["G0001"],
                    "left": "x**2 + 1",
                    "right": "x**2 + 1",
                    "operator": "identity",
                    "expected": "A == F",
                }
            ],
            scientific_rationale="One wrapper equal to the only member.",
            confidence=0.9,
        ),
        math={
            "symbols": [{"name": "x", "real": True}, {"name": "z", "real": True}],
            "functions": [],
            "member": "x**2 + 1",
            "latent_rhs": "x**2 + 1",
        },
        checkable={
            "local_residual": True,
            "structural_audit": True,
            "parse": True,
            "obligations": "if_present",
        },
    ),
    _case(
        "F09_overgeneralized_latent",
        description=(
            "Latent F(u)=u (identity) with substitutions u->sin(x) and "
            "u->x**2+1 'explains' unrelated members. Any expression is an "
            "instance; this is not a master object."
        ),
        expected_audit_class="SHALLOW_REPACKAGING",
        attack_kind="overgeneralized_latent",
        catalog={"G0001": "sin(x)", "G0002": "x**2 + 1"},
        hypothesis=_hyp(
            representation_type="master_function",
            member_ids=["G0001", "G0002"],
            member_roles={"G0001": "instance", "G0002": "instance"},
            latent_object="F(u) = u",
            latent_variables=["u"],
            operators=[
                {
                    "member_id": "G0001",
                    "kind": "substitution",
                    "args": {"u": "sin(x)"},
                },
                {
                    "member_id": "G0002",
                    "kind": "substitution",
                    "args": {"u": "x**2 + 1"},
                },
            ],
            instance_maps={
                "G0001": {"theta": {"u": "sin(x)"}},
                "G0002": {"theta": {"u": "x**2 + 1"}},
            },
            reconstruction_rule="A = F(A)",
            proof_obligations=[
                {
                    "kind": "MASTER_INSTANCE",
                    "member_ids": ["G0001"],
                    "left": "sin(x)",
                    "right": "sin(x)",
                    "operator": "substitution",
                    "expected": "F(sin(x)) == sin(x)",
                },
                {
                    "kind": "MASTER_INSTANCE",
                    "member_ids": ["G0002"],
                    "left": "x**2 + 1",
                    "right": "x**2 + 1",
                    "operator": "substitution",
                    "expected": "F(x**2+1) == x**2+1",
                },
            ],
            scientific_rationale="Identity template absorbs every member.",
            confidence=0.88,
        ),
        math={
            "symbols": [{"name": "x", "real": True}, {"name": "u", "real": True}],
            "functions": [],
            "latent_template": "u",
            "latent_var": "u",
        },
        checkable={
            "local_residual": True,
            "structural_audit": True,
            "parse": True,
            "obligations": "if_present",
        },
    ),
    _case(
        "F10_ambiguous_member_maps",
        description=(
            "Member maps mix catalog nicknames S1_True / generic_branch "
            "(never repaired) with the same G0001 assigned both generic and "
            "degenerate roles and two incompatible forms."
        ),
        expected_audit_class="UNGROUNDABLE",
        attack_kind="ambiguous_member_maps",
        catalog={"G0001": "(sin(x) - sin(y))/(x - y)", "G0002": "cos(x)"},
        hypothesis=_hyp(
            representation_type="divided_difference",
            member_ids=["S1_True", "generic_branch"],
            member_roles={"G0001": "generic"},
            latent_object="F(z) = sin(z)",
            latent_variables=["z"],
            operators=[],
            instance_maps={},
            reconstruction_rule="A = F[x,y]",
            scientific_rationale="Alias ids plus conflicting roles for one member.",
            confidence=0.6,
        ),
        member_maps=[
            {
                "member_id": "S1_True",
                "role": "generic",
                "form": "(sin(x)-sin(y))/(x-y)",
            },
            {
                "member_id": "generic_branch",
                "role": "generic",
                "form": "(sin(x)-sin(y))/(x-y)",
            },
            {
                "member_id": "G0001",
                "role": "generic",
                "form": "(sin(x)-sin(y))/(x-y)",
            },
            {
                "member_id": "G0001",
                "role": "degenerate",
                "form": "sin(x)",
            },
        ],
        math={
            "symbols": [
                {"name": "x", "real": True},
                {"name": "y", "real": True},
            ],
            "functions": [],
            "alias_ids": ["S1_True", "generic_branch"],
        },
        checkable={
            "local_residual": False,
            "structural_audit": True,
            "parse": True,
            "obligations": "if_present",
        },
    ),
]


CASES_BY_ID: dict[str, dict[str, Any]] = {c["id"]: c for c in ATTACK_CASES}


def load_attack_cases() -> list[dict[str, Any]]:
    """Return the frozen in-repo attack list (copied to fixtures/)."""
    return list(ATTACK_CASES)


def load_fixture(case_id: str) -> dict[str, Any]:
    path = FIXTURES_DIR / f"{case_id}.json"
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def export_fixtures(directory: Path | None = None) -> list[Path]:
    """Write one JSON file per case plus index.json. Deterministic."""
    directory = directory or FIXTURES_DIR
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    index = []
    for case in ATTACK_CASES:
        path = directory / f"{case['id']}.json"
        path.write_text(
            json.dumps(case, indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
        )
        written.append(path)
        index.append(
            {
                "id": case["id"],
                "expected_audit_class": case["expected_audit_class"],
                "should_be_zero": case["should_be_zero"],
                "attack_kind": case["attack_kind"],
            }
        )
    idx_path = directory / "index.json"
    idx_path.write_text(
        json.dumps(index, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )
    written.append(idx_path)
    return written
