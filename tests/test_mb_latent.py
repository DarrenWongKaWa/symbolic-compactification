"""Latent-F consistency. Not discovery. No Guo gold masters."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.latent import (
    CHECK_NAMES,
    UNKNOWN,
    as_bool,
    check_latent_consistency,
    latent_compatible,
)
from research.multibranch_verification.schema import (
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    compose_family_verdict,
)


def _hyp(**kw):
    raw = {
        "representation_type": "derivative_family",
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "repeated"},
        "latent_object": "F(z)=polygamma(0,z)",
        "latent_variables": ["z"],
        "nodes": [{"name": "x", "expression": "x", "multiplicity": 2}],
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "derivative",
                "args": {"var": "z", "order": 1, "at": "x"},
            },
        ],
    }
    raw.update(kw)
    return raw


def _confluence(**kw):
    raw = {
        "representation_type": "local_confluence",
        "member_ids": ["G0016", "G0013", "G0014", "G0015", "G0012"],
        "member_roles": {
            "G0016": "generic",
            "G0013": "degenerate",
            "G0014": "degenerate",
            "G0015": "degenerate",
            "G0012": "degenerate",
        },
        "latent_object": "F(m,n,ell)=G0016 (generic Piecewise branch)",
        "latent_variables": ["m", "n", "ell"],
        "nodes": [
            {"name": "m", "expression": "epsilon(m)", "multiplicity": 1},
            {"name": "n", "expression": "epsilon(n)", "multiplicity": 1},
            {"name": "ell", "expression": "epsilon(ell)", "multiplicity": 1},
        ],
        "operators": [
            {"member_id": "G0016", "kind": "identity", "args": {}},
            {
                "member_id": "G0013",
                "kind": "limit",
                "args": {"source": "epsilon(m)", "target": "epsilon(n)"},
            },
            {
                "member_id": "G0014",
                "kind": "limit",
                "args": {"source": "epsilon(ell)", "target": "epsilon(n)"},
            },
            {
                "member_id": "G0015",
                "kind": "limit",
                "args": {"source": "epsilon(ell)", "target": "epsilon(m)"},
            },
            {
                "member_id": "G0012",
                "kind": "limit",
                "args": {
                    "source1": "epsilon(m)",
                    "target1": "epsilon(n)",
                    "source2": "epsilon(ell)",
                    "target2": "epsilon(n)",
                },
            },
        ],
    }
    raw.update(kw)
    return raw


def _verdict_by_name(report):
    return {c.name: c.verdict for c in report.checks}


def test_public_api_and_check_names():
    assert UNKNOWN == "UNKNOWN"
    assert latent_compatible is not None
    report = check_latent_consistency(_hyp())
    names = {c.name for c in report.checks}
    for required in (
        "argument_compatibility",
        "derivative_order",
        "special_function_head",
        "shared_vars",
        "multiplicity",
        "recurrence_compatibility",
    ):
        assert required in names
    assert set(CHECK_NAMES) <= names | {"member_roles"}


def test_as_bool_does_not_treat_unknown_as_true():
    assert as_bool(True) is True
    assert as_bool(False) is False
    assert as_bool(UNKNOWN) is False
    assert bool(UNKNOWN) is True


def test_compatible_polygamma_derivative_is_true():
    assert latent_compatible(_hyp()) is True


def test_compatible_kwargs_match_dict():
    h = _hyp()
    assert (
        latent_compatible(
            latent_object=h["latent_object"],
            operators=h["operators"],
            member_roles=h["member_roles"],
            latent_variables=h["latent_variables"],
            nodes=h["nodes"],
            member_ids=h["member_ids"],
            representation_type=h["representation_type"],
        )
        is True
    )


def test_five_branch_signature_limits_are_syntactically_true():
    # Catalog pointer is not expanded. Signature + roles + limits only.
    assert latent_compatible(_confluence()) is True


def test_hermite_typed_coalescence_repeated_is_true():
    h = _confluence(
        representation_type="hermite_divided_difference",
        member_roles={
            "G0016": "generic",
            "G0013": "degenerate",
            "G0014": "degenerate",
            "G0015": "degenerate",
            "G0012": "repeated",
        },
        latent_object="F(m,n,ell) = B_true(m,n,ell)*h1(a,m,n) (true-branch of G0016)",
    )
    assert latent_compatible(h) is True


def test_argument_mismatch_is_false():
    h = _hyp(
        latent_object="F(z)=polygamma(0,z)",
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "derivative", "args": {"var": "w", "order": 1}},
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["argument_compatibility"] is False


def test_limit_on_unrelated_index_is_false():
    h = _confluence(
        operators=[
            {"member_id": "G0016", "kind": "identity", "args": {}},
            {"member_id": "G0013", "kind": "limit", "args": {"source": "t", "target": "0"}},
        ],
        member_ids=["G0016", "G0013"],
        member_roles={"G0016": "generic", "G0013": "degenerate"},
    )
    assert latent_compatible(h) is False


def test_derivative_order_zero_or_negative_is_false():
    for order in (0, -1):
        h = _hyp(
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
                {
                    "member_id": "G0002",
                    "kind": "derivative",
                    "args": {"var": "z", "order": order},
                },
            ]
        )
        assert latent_compatible(h) is False
        assert _verdict_by_name(check_latent_consistency(h))["derivative_order"] is False


def test_hermite_order_must_be_multiplicity_minus_one():
    h = _hyp(
        representation_type="hermite_divided_difference",
        member_roles={"G0001": "generic", "G0002": "repeated"},
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "hermite_dd",
                "args": {"var": "z", "multiplicity": 2, "order": 2, "at": "x"},
            },
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["derivative_order"] is False


def test_hermite_multiplicity_one_is_false():
    h = _hyp(
        representation_type="hermite_divided_difference",
        nodes=[{"name": "x", "expression": "x", "multiplicity": 1}],
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "hermite_dd",
                "args": {"var": "z", "multiplicity": 1, "at": "x"},
            },
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["multiplicity"] is False


def test_compatible_hermite_multiplicity_two_order_one():
    h = _hyp(
        representation_type="hermite_divided_difference",
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "hermite_dd",
                "args": {"var": "z", "multiplicity": 2, "order": 1, "at": "x"},
            },
        ],
    )
    assert latent_compatible(h) is True


def test_special_head_polygamma_vs_gamma_recurrence_is_false():
    h = _hyp(
        representation_type="recurrence_family",
        member_roles={"G0001": "generic", "G0002": "instance"},
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "recurrence",
                "args": {"var": "z", "delta": 1, "head": "gamma"},
            },
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["special_function_head"] is False


def test_algebraic_latent_vs_polygamma_head_is_false():
    h = _hyp(
        latent_object="F(z)=z**3",
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "derivative",
                "args": {"var": "z", "order": 1, "head": "polygamma"},
            },
        ],
    )
    assert latent_compatible(h) is False


def test_shared_vars_disjoint_is_false():
    h = {
        "latent_object": "F(z)=polygamma(0,z)",
        "latent_variables": ["z"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "instance"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "substitution", "args": {"w": "0"}},
        ],
    }
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["shared_vars"] is False


def test_recurrence_on_latent_index_is_true():
    h = {
        "representation_type": "recurrence_family",
        "latent_object": "F(n)=n",
        "latent_variables": ["n"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "instance"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "recurrence", "args": {"var": "n", "delta": 1}},
        ],
    }
    assert latent_compatible(h) is True


def test_recurrence_on_non_argument_is_false():
    h = {
        "representation_type": "recurrence_family",
        "latent_object": "F(z)=z",
        "latent_variables": ["z"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "instance"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "recurrence", "args": {"var": "n", "delta": 1}},
        ],
    }
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["recurrence_compatibility"] is False


def test_recurrence_family_without_shift_is_false():
    h = _hyp(
        representation_type="recurrence_family",
        member_roles={"G0001": "generic", "G0002": "degenerate"},
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {
                "member_id": "G0002",
                "kind": "limit",
                "args": {"source": "z", "target": "x"},
            },
        ],
        nodes=[{"name": "x", "expression": "x", "multiplicity": 1}],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["recurrence_compatibility"] is False


def test_derivative_wrt_polygamma_order_is_false():
    h = {
        "latent_object": "F(n,z)=polygamma(n,z)",
        "latent_variables": ["n", "z"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "repeated"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "derivative", "args": {"var": "n", "order": 1}},
        ],
    }
    assert latent_compatible(h) is False


def test_swapped_generic_degenerate_roles_are_false():
    h = _confluence(
        member_ids=["G0016", "G0013"],
        member_roles={"G0016": "degenerate", "G0013": "generic"},
        operators=[
            {"member_id": "G0016", "kind": "identity", "args": {}},
            {
                "member_id": "G0013",
                "kind": "limit",
                "args": {"source": "epsilon(m)", "target": "epsilon(n)"},
            },
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["member_roles"] is False


def test_repeated_identity_is_false():
    h = _hyp(
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "identity", "args": {}},
        ]
    )
    assert latent_compatible(h) is False


def test_unknown_operator_kind_is_false():
    h = _hyp(
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "confluence", "args": {"var": "z"}},
        ]
    )
    assert latent_compatible(h) is False


def test_unknown_member_role_is_false():
    h = _hyp(member_roles={"G0001": "generic", "G0002": "master"})
    assert latent_compatible(h) is False


def test_empty_latent_is_unknown():
    assert latent_compatible(_hyp(latent_object="")) == UNKNOWN
    assert latent_compatible(_hyp(latent_object="   ")) == UNKNOWN


def test_missing_or_empty_operators_is_unknown():
    h = _hyp()
    h.pop("operators")
    assert latent_compatible(h) == UNKNOWN
    assert latent_compatible(_hyp(operators=[])) == UNKNOWN


def test_unparsed_prose_with_derivative_is_unknown():
    h = _hyp(
        latent_object="maybe a unified object",
        latent_variables=[],
        nodes=[],
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "derivative", "args": {"var": "z", "order": 1}},
        ],
    )
    assert latent_compatible(h) == UNKNOWN


def test_missing_roles_is_unknown_not_true():
    h = _hyp(member_roles={})
    assert latent_compatible(h) == UNKNOWN


def test_invented_master_name_is_false():
    h = _hyp(latent_object="F(z)=Phi_Gamma(z)")
    assert latent_compatible(h) is False
    h2 = _hyp(latent_object="F(z)=L4(z)")
    assert latent_compatible(h2) is False


def test_coincident_newton_is_not_repeated():
    h = _hyp(
        representation_type="divided_difference",
        member_roles={"G0001": "generic", "G0002": "repeated"},
        nodes=[
            {"name": "x", "expression": "x", "multiplicity": 1},
            {"name": "y", "expression": "y", "multiplicity": 1},
        ],
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "newton_dd", "args": {"var": "z", "x": "x", "y": "x"}},
        ],
    )
    assert latent_compatible(h) is False
    assert _verdict_by_name(check_latent_consistency(h))["multiplicity"] is False


def test_size_guard_is_unknown():
    h = _hyp(latent_object="F(z)=" + ("z+" * 3000) + "z")
    assert latent_compatible(h) == UNKNOWN


def test_operator_member_outside_ids_is_false():
    h = _hyp(
        member_ids=["G0001", "G0002"],
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0099", "kind": "derivative", "args": {"var": "z", "order": 1}},
        ],
    )
    assert latent_compatible(h) is False


def test_does_not_read_catalog_or_runs(monkeypatch):
    reads: list[str] = []
    orig = Path.read_text

    def wrapped(self, *args, **kwargs):
        reads.append(str(self))
        return orig(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", wrapped)
    verdict = latent_compatible(_confluence())
    assert verdict is True
    joined = " ".join(reads)
    assert "GUO_OBLIGATION_MAP" not in joined
    assert "guo-sigma-abc__P2" not in joined
    assert "FROZEN_INPUTS_V2" not in joined


def test_unknown_blocks_family_zero():
    v = latent_compatible(_hyp(latent_object=""))
    assert v == UNKNOWN
    assert (
        compose_family_verdict(
            required_edge_verdicts=["ZERO", "ZERO"],
            recurrence_verdicts=["ZERO"],
            path_verdicts=["ZERO"],
            connected=True,
            multiplicities_consistent=True,
            latent_compatible=as_bool(v),
        )
        == FAMILY_UNKNOWN
    )


def test_false_blocks_family_zero():
    v = latent_compatible(
        _hyp(
            operators=[
                {"member_id": "G0001", "kind": "identity", "args": {}},
                {"member_id": "G0002", "kind": "derivative", "args": {"var": "w", "order": 1}},
            ]
        )
    )
    assert v is False
    assert (
        compose_family_verdict(
            required_edge_verdicts=["ZERO", "ZERO"],
            recurrence_verdicts=["ZERO"],
            path_verdicts=["ZERO"],
            connected=True,
            multiplicities_consistent=True,
            latent_compatible=as_bool(v),
        )
        == FAMILY_UNKNOWN
    )


def test_true_does_not_by_itself_invent_family_zero():
    v = latent_compatible(_hyp())
    assert v is True
    assert (
        compose_family_verdict(
            required_edge_verdicts=["ZERO", "ZERO"],
            recurrence_verdicts=["ZERO"],
            path_verdicts=["ZERO"],
            connected=True,
            multiplicities_consistent=True,
            latent_compatible=as_bool(v),
        )
        == FAMILY_ZERO
    )
    assert (
        compose_family_verdict(
            required_edge_verdicts=["ZERO", "UNKNOWN"],
            recurrence_verdicts=["ZERO"],
            path_verdicts=["ZERO"],
            connected=True,
            multiplicities_consistent=True,
            latent_compatible=as_bool(v),
        )
        == FAMILY_UNKNOWN
    )


def test_node_multiplicity_zero_is_false():
    h = _hyp(nodes=[{"name": "x", "expression": "x", "multiplicity": 0}])
    assert latent_compatible(h) is False


def test_kind_other_is_unknown_not_true():
    h = _hyp(
        operators=[
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "other", "args": {"var": "z"}},
        ]
    )
    assert latent_compatible(h) == UNKNOWN


def test_permutation_arity_mismatch_is_false():
    h = {
        "latent_object": "F(x,y)=x+y",
        "latent_variables": ["x", "y"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "instance"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "permutation", "args": {"perm": [0, 1, 2]}},
        ],
    }
    assert latent_compatible(h) is False


def test_compatible_permutation_swap():
    h = {
        "latent_object": "F(x,y)=x+y",
        "latent_variables": ["x", "y"],
        "member_ids": ["G0001", "G0002"],
        "member_roles": {"G0001": "generic", "G0002": "instance"},
        "operators": [
            {"member_id": "G0001", "kind": "identity", "args": {}},
            {"member_id": "G0002", "kind": "permutation", "args": {"swap": ["x", "y"]}},
        ],
    }
    assert latent_compatible(h) is True
