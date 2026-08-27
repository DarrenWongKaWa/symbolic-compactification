"""Experimental representation obligations. False ZERO must stay 0."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.obligations import (
    COMPILE_FAILURE,
    COMPILE_OK,
    CONFLUENCE,
    KINDS,
    NEWTON_DD,
    NONZERO,
    UNKNOWN,
    ZERO,
    compile_hypothesis,
    verify_obligation,
)
from research.representation_invention.schema import (
    OK,
    PARSE_FAILURE,
    OBLIGATION_KINDS,
    NodeSpec,
    ObligationDraft,
    OperatorSpec,
    RepresentationHypothesisV2,
    parse_hypothesis_v2,
)
from symbolic_compactification import NONZERO as ENG_NZ
from symbolic_compactification import UNKNOWN as ENG_UNK
from symbolic_compactification import ZERO as ENG_ZERO

SYMS = [{"name": n, "real": True} for n in ("x", "y", "z", "n", "a", "b", "i", "j", "w")]
FALSE_ZERO = []


def _hyp(**kw) -> RepresentationHypothesisV2:
    base = dict(
        representation_type="divided_difference",
        member_ids=["G0001"],
        member_roles={"G0001": "generic"},
        latent_object="F(z) = z**2",
        latent_variables=["z"],
        nodes=[NodeSpec("x", "x", 1), NodeSpec("y", "y", 1)],
        operators=[OperatorSpec("G0001", "newton_dd", {"nodes": ["x", "y"]})],
        instance_maps={"G0001": {"nodes": ["x", "y"]}},
        reconstruction_rule="(F(x)-F(y))/(x-y)",
        required_assumptions=["Ne(x, y)"],
        proof_obligations=[
            ObligationDraft(
                kind="NEWTON_DD",
                member_ids=["G0001"],
                operator="newton_dd",
                expected="equal",
            )
        ],
        scientific_rationale="test",
        confidence=1.0,
        parse_status=OK,
    )
    base.update(kw)
    return RepresentationHypothesisV2(**base)


def _run(h, catalog, symbols=None, functions=None):
    symbols = symbols or SYMS
    functions = functions or []
    cr = compile_hypothesis(h, catalog, symbols, functions)
    vs = [
        verify_obligation(o, symbols=symbols, functions=functions)
        for o in cr.obligations
    ]
    return cr, vs


def _fields(obl):
    assert obl.member_ids == obl.source_member_ids
    assert isinstance(obl.exact_expressions, dict)
    assert isinstance(obl.variables, dict)
    assert isinstance(obl.assumptions, list)
    assert obl.operator
    assert obl.expected_relation
    assert obl.provenance
    if obl.compile_status == COMPILE_OK:
        assert obl.left
        assert obl.exact_expressions


def _not_zero(v, label):
    if v.verdict == ZERO:
        FALSE_ZERO.append(label)
    assert v.verdict != ZERO, (label, v.to_dict())
    assert v.compile_status == COMPILE_OK, (label, v.to_dict())


# --------------------------------------------------------------------------- #
# Contract
# --------------------------------------------------------------------------- #


def test_limit_source_target_args_and_role_pair():
    h = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001", "G0002"],
        member_roles={"G0001": "generic", "G0002": "degenerate"},
        operators=[
            OperatorSpec("G0001", "identity", {}),
            OperatorSpec("G0002", "limit", {"source": "x", "target": "y"}),
        ],
        proof_obligations=[
            ObligationDraft(
                kind="LIMIT",
                member_ids=["G0002"],
                operator="limit",
                expected="limit",
            )
        ],
        reconstruction_rule="limit x -> y",
    )
    cr, vs = _run(
        h,
        {"G0001": "(x**2 - y**2)/(x - y)", "G0002": "2*y"},
    )
    assert cr.n_ok >= 1, [o.compile_error for o in cr.obligations]
    assert any(v.verdict == ZERO for v in vs), [v.to_dict() for v in vs]


def test_kinds_match_v2_contract():
    assert KINDS == OBLIGATION_KINDS
    assert "DIVIDED_DIFFERENCE" not in KINDS
    assert NEWTON_DD in KINDS and CONFLUENCE in KINDS
    assert ZERO == ENG_ZERO and NONZERO == ENG_NZ and UNKNOWN == ENG_UNK


def test_compiled_obligation_carries_required_fields():
    cr, vs = _run(_hyp(), {"G0001": "(x**2 - y**2)/(x - y)"})
    assert cr.n_ok == 1 and cr.n_fail == 0
    assert cr.compile_status == COMPILE_OK
    assert "n_unknown" not in cr.to_dict()
    o = cr.obligations[0]
    _fields(o)
    assert o.kind == NEWTON_DD
    assert o.compile_status == COMPILE_OK
    assert vs[0].verdict == ZERO


# --------------------------------------------------------------------------- #
# Positive controls (Phase 5 preview)
# --------------------------------------------------------------------------- #


def test_newton_first_dd_z2_zero():
    cr, vs = _run(_hyp(), {"G0001": "(x**2 - y**2)/(x - y)"})
    assert cr.n_fail == 0
    assert vs[0].verdict == ZERO
    assert vs[0].compile_status == COMPILE_OK
    assert vs[0].backend != "none"


def test_newton_first_dd_z3_zero():
    h = _hyp(latent_object="F(z) = z**3")
    cr, vs = _run(h, {"G0001": "(x**3 - y**3)/(x - y)"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


def test_repeated_node_derivative_limit_Fxx_zero():
    h = _hyp(
        representation_type="hermite_divided_difference",
        latent_object="F(z) = z**2",
        nodes=[NodeSpec("x", "x", 2)],
        operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x"]})],
        instance_maps={"G0001": {"nodes": ["x", "x"]}},
        reconstruction_rule="F[x,x]=F'(x)",
        proof_obligations=[
            ObligationDraft(
                kind="HERMITE_DD",
                member_ids=["G0001"],
                operator="hermite_dd",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "2*x"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    lim_h = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001", "G0007"],
        member_roles={"G0001": "generic", "G0007": "degenerate"},
        operators=[OperatorSpec("G0001", "limit", {"var": "y", "to": "x"})],
        instance_maps={},
        reconstruction_rule="lim y->x F[x,y] = F'(x)",
        proof_obligations=[
            ObligationDraft(
                kind="LIMIT",
                member_ids=["G0001", "G0007"],
                operator="limit",
                variables={"var": "y", "to": "x"},
                expected="limit_equal",
            )
        ],
    )
    cr2, vs2 = _run(
        lim_h,
        {"G0001": "(x**2 - y**2)/(x - y)", "G0007": "2*x"},
    )
    assert cr2.n_ok == 1, cr2.to_dict()
    assert cr2.obligations[0].kind == "LIMIT"
    assert vs2[0].verdict == ZERO, vs2[0].to_dict()


def test_hermite_one_repeated_node_Fxxy_zero():
    h = _hyp(
        representation_type="hermite_divided_difference",
        latent_object="F(z) = z**3",
        nodes=[
            NodeSpec("x", "x", 2),
            NodeSpec("y", "y", 1),
        ],
        operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x", "y"]})],
        instance_maps={"G0001": {"nodes": ["x", "x", "y"]}},
        reconstruction_rule="F[x,x,y]=(F[x,x]-F[x,y])/(x-y)",
        proof_obligations=[
            ObligationDraft(
                kind="HERMITE_DD",
                member_ids=["G0001"],
                operator="hermite_dd",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "2*x + y"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


def test_hermite_two_repeated_Fxxx_zero():
    h = _hyp(
        representation_type="hermite_divided_difference",
        latent_object="F(z) = z**3",
        nodes=[NodeSpec("x", "x", 3)],
        operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x", "x"]})],
        instance_maps={"G0001": {"nodes": ["x", "x", "x"]}},
        reconstruction_rule="F[x,x,x]=F''(x)/2",
        proof_obligations=[
            ObligationDraft(
                kind="HERMITE_DD",
                member_ids=["G0001"],
                operator="hermite_dd",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "3*x"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


def test_piecewise_generic_vs_diagonal_confluence_zero():
    two = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001", "G0007"],
        member_roles={"G0001": "generic", "G0007": "degenerate"},
        operators=[OperatorSpec("G0001", "limit", {"var": "x", "to": "y"})],
        instance_maps={},
        reconstruction_rule="limit generic -> diagonal",
        proof_obligations=[
            ObligationDraft(
                kind="CONFLUENCE",
                member_ids=["G0001", "G0007"],
                operator="limit",
                variables={"var": "x", "to": "y"},
                expected="limit_equal",
            )
        ],
    )
    cr, vs = _run(
        two,
        {"G0001": "(x**2 - y**2)/(x - y)", "G0007": "2*y"},
    )
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    pw = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001"],
        member_roles={"G0001": "generic"},
        nodes=[NodeSpec("x", "x", 1), NodeSpec("y", "y", 1)],
        operators=[OperatorSpec("G0001", "limit", {"var": "x", "to": "y"})],
        instance_maps={},
        reconstruction_rule="Piecewise generic vs diagonal",
        proof_obligations=[
            ObligationDraft(
                kind="CONFLUENCE",
                member_ids=["G0001"],
                operator="limit",
                variables={"var": "x", "to": "y"},
                expected="limit_equal",
            )
        ],
    )
    cr2, vs2 = _run(
        pw,
        {"G0001": "Piecewise((2*y, Eq(x, y)), ((x**2 - y**2)/(x - y), True))"},
    )
    assert cr2.n_ok == 1, cr2.to_dict()
    assert vs2[0].verdict == ZERO, vs2[0].to_dict()


def test_polygamma_newton_dd_explicit_difference():
    h = _hyp(latent_object="F(z) = polygamma(0, z)")
    member = "(polygamma(0, x) - polygamma(0, y))/(x - y)"
    cr, vs = _run(h, {"G0001": member})
    assert cr.n_ok == 1, cr.to_dict()
    assert vs[0].verdict == ZERO, vs[0].to_dict()
    # Non-identity rewrite that _equal does not need to decide: must not ZERO.
    cr_bad, vs_bad = _run(h, {"G0001": "polygamma(1, x)"})
    _not_zero(vs_bad[0], "polygamma_wrong_form")


# --------------------------------------------------------------------------- #
# Other kinds — positive
# --------------------------------------------------------------------------- #


def test_substitution_derivative_permutation_equality_zero():
    sub = _hyp(
        representation_type="other_explicit",
        latent_object="F(z) = z**2",
        operators=[OperatorSpec("G0001", "substitution", {})],
        instance_maps={"G0001": {"theta": {"z": "a + 1"}}},
        reconstruction_rule="F(a+1)",
        proof_obligations=[
            ObligationDraft(
                kind="SUBSTITUTION",
                member_ids=["G0001"],
                operator="substitution",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(sub, {"G0001": "(a + 1)**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    der = _hyp(
        representation_type="derivative_family",
        latent_object="F(z) = z**3",
        operators=[OperatorSpec("G0001", "derivative", {"order": 1, "var": "z"})],
        instance_maps={"G0001": {"theta": {}}},
        reconstruction_rule="F'(z)",
        proof_obligations=[
            ObligationDraft(
                kind="DERIVATIVE",
                member_ids=["G0001"],
                operator="derivative",
                variables={"order": "1", "var": "z"},
                expected="equal",
            )
        ],
    )
    cr, vs = _run(der, {"G0001": "3*z**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    perm = _hyp(
        representation_type="other_explicit",
        latent_object="T(x, y)",
        latent_variables=["x", "y"],
        operators=[OperatorSpec("G0001", "permutation", {})],
        instance_maps={"G0001": {"theta": {"x": "i", "y": "j"}}},
        reconstruction_rule="swap",
        proof_obligations=[
            ObligationDraft(
                kind="PERMUTATION",
                member_ids=["G0001"],
                operator="permutation",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(perm, {"G0001": "T(j, i)"}, functions=["T"])
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    eq = _hyp(
        representation_type="other_explicit",
        latent_object="F(z) = z**2",
        operators=[OperatorSpec("G0001", "identity", {})],
        instance_maps={"G0001": {"theta": {}}},
        reconstruction_rule="F",
        proof_obligations=[
            ObligationDraft(
                kind="EQUALITY",
                member_ids=["G0001"],
                operator="identity",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(eq, {"G0001": "z**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


def test_recurrence_master_basis_zero():
    rec = _hyp(
        representation_type="recurrence_family",
        member_ids=["G0001"],
        latent_object="F(n) = n**2",
        latent_variables=["n"],
        nodes=[],
        operators=[
            OperatorSpec(
                "G0001", "recurrence",
                {"shift": "n", "step": 1, "rhs": "2*n + 1"},
            )
        ],
        instance_maps={},
        reconstruction_rule="F(n+1)-F(n)=2n+1",
        proof_obligations=[
            ObligationDraft(
                kind="RECURRENCE",
                member_ids=["G0001"],
                operator="recurrence",
                variables={"shift": "n", "step": "1", "rhs": "2*n + 1"},
                expected="equal_zero",
            )
        ],
    )
    cr, vs = _run(rec, {"G0001": "n**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    master = _hyp(
        representation_type="master_function",
        latent_object="F(z) = z**2",
        operators=[OperatorSpec("G0001", "identity", {})],
        instance_maps={"G0001": {"theta": {"z": "a"}}},
        reconstruction_rule="A = F(a)",
        proof_obligations=[
            ObligationDraft(
                kind="MASTER_INSTANCE",
                member_ids=["G0001"],
                operator="identity",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(master, {"G0001": "a**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()

    basis = _hyp(
        representation_type="invariant_basis",
        latent_object="F(z) = z",
        operators=[
            OperatorSpec(
                "G0001",
                "other",
                {
                    "basis": ["1", "z", "z**2"],
                    "coefficients": ["1", "2", "3"],
                },
            )
        ],
        instance_maps={"G0001": {"theta": {"z": "x"}}},
        reconstruction_rule="1+2x+3x**2",
        proof_obligations=[
            ObligationDraft(
                kind="BASIS_RECONSTRUCTION",
                member_ids=["G0001"],
                operator="other",
                expected="equal",
            )
        ],
    )
    cr, vs = _run(basis, {"G0001": "1 + 2*x + 3*x**2"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


# --------------------------------------------------------------------------- #
# Adversarial mutations — must not false-ZERO
# --------------------------------------------------------------------------- #


def test_newton_adversarial_sign_coeff_node():
    h = _hyp(latent_object="F(z) = z**3")
    good = "(x**3 - y**3)/(x - y)"
    cr, vs = _run(h, {"G0001": good})
    assert vs[0].verdict == ZERO
    o = cr.obligations[0]
    _fields(o)

    cr_s, vs_s = _run(h, {"G0001": f"-({good})"})
    _not_zero(vs_s[0], "newton_sign")
    assert vs_s[0].verdict == NONZERO

    cr_c, vs_c = _run(h, {"G0001": f"2*({good})"})
    _not_zero(vs_c[0], "newton_coeff")

    mutated = replace(o, nodes=["x", "w"])
    v = verify_obligation(mutated, symbols=SYMS)
    _not_zero(v, "newton_wrong_node")


def test_hermite_wrong_multiplicity_and_order_like_nodes():
    h = _hyp(
        representation_type="hermite_divided_difference",
        latent_object="F(z) = z**3",
        nodes=[NodeSpec("x", "x", 2), NodeSpec("y", "y", 1)],
        operators=[OperatorSpec("G0001", "hermite_dd", {"nodes": ["x", "x", "y"]})],
        instance_maps={"G0001": {"nodes": ["x", "x", "y"]}},
        proof_obligations=[
            ObligationDraft(kind="HERMITE_DD", member_ids=["G0001"], operator="hermite_dd")
        ],
    )
    cr, vs = _run(h, {"G0001": "2*x + y"})
    assert vs[0].verdict == ZERO
    o = cr.obligations[0]
    v_mult = verify_obligation(replace(o, nodes=["x", "x", "x"]), symbols=SYMS)
    _not_zero(v_mult, "hermite_wrong_multiplicity")
    assert v_mult.verdict == NONZERO
    v_sign = verify_obligation(replace(o, left="-(2*x + y)"), symbols=SYMS)
    _not_zero(v_sign, "hermite_sign")
    v_co = verify_obligation(replace(o, left="3*(2*x + y)"), symbols=SYMS)
    _not_zero(v_co, "hermite_coeff")


def test_derivative_wrong_order():
    h = _hyp(
        representation_type="derivative_family",
        latent_object="F(z) = z**3",
        operators=[OperatorSpec("G0001", "derivative", {"order": 1, "var": "z"})],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(
                kind="DERIVATIVE",
                member_ids=["G0001"],
                operator="derivative",
                variables={"order": "1", "var": "z"},
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "3*z**2"})
    assert vs[0].verdict == ZERO
    o = cr.obligations[0]
    v = verify_obligation(replace(o, order=2), symbols=SYMS)
    _not_zero(v, "derivative_wrong_order")
    assert v.verdict == NONZERO
    v2 = verify_obligation(replace(o, left="6*z"), symbols=SYMS)
    _not_zero(v2, "derivative_wrong_member")


def test_limit_wrong_value_and_member_swap():
    h = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001", "G0007"],
        member_roles={"G0001": "generic", "G0007": "degenerate"},
        operators=[OperatorSpec("G0001", "limit", {"var": "x", "to": "y"})],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(
                kind="CONFLUENCE",
                member_ids=["G0001", "G0007"],
                operator="limit",
                variables={"var": "x", "to": "y"},
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "(x**2 - y**2)/(x - y)", "G0007": "2*y"})
    assert vs[0].verdict == ZERO
    o = cr.obligations[0]
    v_pt = verify_obligation(replace(o, to="0"), symbols=SYMS)
    _not_zero(v_pt, "limit_wrong_value")
    swapped = replace(o, left=o.right, right=o.left)
    v_sw = verify_obligation(swapped, symbols=SYMS)
    _not_zero(v_sw, "wrong_branch_member_swap")
    v_sign = verify_obligation(replace(o, right="-2*y"), symbols=SYMS)
    _not_zero(v_sign, "confluence_sign")


def test_recurrence_wrong_rhs():
    h = _hyp(
        representation_type="recurrence_family",
        latent_object="F(n) = n**2",
        latent_variables=["n"],
        nodes=[],
        operators=[
            OperatorSpec("G0001", "recurrence", {"shift": "n", "step": 1, "rhs": "2*n + 1"})
        ],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(
                kind="RECURRENCE",
                member_ids=["G0001"],
                operator="recurrence",
                variables={"shift": "n", "step": "1", "rhs": "2*n + 1"},
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "n**2"})
    assert vs[0].verdict == ZERO
    o = cr.obligations[0]
    v = verify_obligation(replace(o, recurrence_rhs="2*n - 1"), symbols=SYMS)
    _not_zero(v, "wrong_recurrence")
    assert v.verdict == NONZERO
    v_sign = verify_obligation(replace(o, recurrence_rhs="-(2*n + 1)"), symbols=SYMS)
    _not_zero(v_sign, "recurrence_sign")
    v_mem = verify_obligation(replace(o, left="n**3"), symbols=SYMS)
    _not_zero(v_mem, "recurrence_wrong_member")


def test_permutation_unpermuted_is_nonzero():
    h = _hyp(
        representation_type="other_explicit",
        latent_object="T(x, y)",
        operators=[OperatorSpec("G0001", "permutation", {})],
        instance_maps={"G0001": {"theta": {"x": "i", "y": "j"}}},
        proof_obligations=[
            ObligationDraft(kind="PERMUTATION", member_ids=["G0001"], operator="permutation")
        ],
    )
    cr, vs = _run(h, {"G0001": "T(i, j)"}, functions=["T"])
    _not_zero(vs[0], "permutation_unpermuted")
    assert vs[0].verdict == NONZERO


def test_substitution_and_basis_coeff_errors():
    sub = _hyp(
        representation_type="other_explicit",
        operators=[OperatorSpec("G0001", "substitution", {})],
        instance_maps={"G0001": {"theta": {"z": "a + 1"}}},
        proof_obligations=[
            ObligationDraft(kind="SUBSTITUTION", member_ids=["G0001"], operator="substitution")
        ],
    )
    cr, vs = _run(sub, {"G0001": "(a - 1)**2"})
    _not_zero(vs[0], "substitution_wrong")

    basis = _hyp(
        representation_type="invariant_basis",
        operators=[
            OperatorSpec(
                "G0001",
                "other",
                {"basis": ["1", "z", "z**2"], "coefficients": ["1", "2", "3"]},
            )
        ],
        instance_maps={"G0001": {"theta": {"z": "x"}}},
        proof_obligations=[
            ObligationDraft(kind="BASIS_RECONSTRUCTION", member_ids=["G0001"], operator="other")
        ],
    )
    cr, vs = _run(basis, {"G0001": "1 + 2*x + 4*x**2"})
    _not_zero(vs[0], "basis_coeff")


# --------------------------------------------------------------------------- #
# COMPILE_FAILURE ≠ UNKNOWN ≠ ZERO
# --------------------------------------------------------------------------- #


def test_missing_nodes_is_compile_failure_not_unknown():
    h = _hyp(
        nodes=[],
        operators=[OperatorSpec("G0001", "newton_dd", {})],
        instance_maps={},
    )
    cr, vs = _run(h, {"G0001": "x + y"})
    assert cr.n_ok == 0 and cr.n_fail >= 1
    assert cr.compile_status == COMPILE_FAILURE
    assert "n_unknown" not in cr.to_dict()
    o = cr.obligations[0]
    assert o.compile_status == COMPILE_FAILURE
    assert "reconstruction_cannot_be_built" in (o.compile_error or "")
    v = vs[0]
    assert v.compile_status == COMPILE_FAILURE
    assert v.verdict is None
    assert v.verdict != UNKNOWN
    assert v.verdict != ZERO
    assert v.verdict != NONZERO


def test_limit_missing_var_is_compile_failure():
    h = _hyp(
        representation_type="local_confluence",
        member_ids=["G0001", "G0007"],
        member_roles={"G0001": "generic", "G0007": "degenerate"},
        nodes=[],
        operators=[OperatorSpec("G0001", "limit", {})],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(
                kind="CONFLUENCE",
                member_ids=["G0001", "G0007"],
                operator="limit",
            )
        ],
    )
    cr, vs = _run(h, {"G0001": "x + y", "G0007": "2*y"})
    assert cr.compile_status == COMPILE_FAILURE
    assert vs[0].verdict is None
    assert vs[0].compile_status == COMPILE_FAILURE
    assert vs[0].verdict != UNKNOWN


def test_parse_failure_hypothesis_is_compile_failure():
    raw = {
        "representation_type": "divided_difference",
        "member_ids": ["S1_True"],
        "latent_object": "F(z) = z**2",
        "confidence": 0.5,
    }
    h = parse_hypothesis_v2(raw, {"G0001"})
    assert h.parse_status == PARSE_FAILURE
    cr, vs = _run(h, {"G0001": "x"})
    assert cr.n_ok == 0
    assert cr.compile_status == COMPILE_FAILURE
    assert vs[0].verdict is None
    assert vs[0].verdict != UNKNOWN


def test_missing_catalog_and_unparseable_latent():
    cr, vs = _run(_hyp(), {})
    assert cr.compile_status == COMPILE_FAILURE
    assert vs[0].verdict is None

    h = _hyp(latent_object="not a closed form ???")
    cr2, vs2 = _run(h, {"G0001": "(x**2 - y**2)/(x - y)"})
    assert cr2.compile_status == COMPILE_FAILURE
    assert vs2[0].compile_status == COMPILE_FAILURE
    assert vs2[0].verdict != UNKNOWN
    assert vs2[0].verdict != ZERO


def test_recurrence_and_basis_missing_reconstruction():
    rec = _hyp(
        representation_type="recurrence_family",
        latent_object="F(n) = n**2",
        latent_variables=["n"],
        nodes=[],
        operators=[OperatorSpec("G0001", "recurrence", {"shift": "n"})],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(kind="RECURRENCE", member_ids=["G0001"], operator="recurrence")
        ],
    )
    cr, vs = _run(rec, {"G0001": "n**2"})
    assert cr.compile_status == COMPILE_FAILURE
    assert vs[0].verdict is None

    basis = _hyp(
        representation_type="invariant_basis",
        operators=[OperatorSpec("G0001", "other", {})],
        instance_maps={},
        proof_obligations=[
            ObligationDraft(kind="BASIS_RECONSTRUCTION", member_ids=["G0001"], operator="other")
        ],
    )
    cr, vs = _run(basis, {"G0001": "x"})
    assert cr.compile_status == COMPILE_FAILURE
    assert vs[0].verdict is None


def test_v2_parse_then_compile_newton():
    raw = {
        "representation_type": "divided_difference",
        "member_ids": ["G0001"],
        "member_roles": {"G0001": "generic"},
        "latent_object": "F(z) = z**2",
        "latent_variables": ["z"],
        "nodes": [
            {"name": "x", "expression": "x", "multiplicity": 1},
            {"name": "y", "expression": "y", "multiplicity": 1},
        ],
        "operators": [
            {"member_id": "G0001", "kind": "newton_dd", "args": {"nodes": ["x", "y"]}}
        ],
        "instance_maps": {"G0001": {"nodes": ["x", "y"]}},
        "reconstruction_rule": "(F(x)-F(y))/(x-y)",
        "required_assumptions": [],
        "proof_obligations": [
            {"kind": "NEWTON_DD", "member_ids": ["G0001"], "operator": "newton_dd"}
        ],
        "scientific_rationale": "parsed",
        "confidence": 0.9,
    }
    h = parse_hypothesis_v2(raw, {"G0001"})
    assert h.parse_status == OK, h.parse_error
    cr, vs = _run(h, {"G0001": "(x**2 - y**2)/(x - y)"})
    assert vs[0].verdict == ZERO, vs[0].to_dict()


def test_false_zero_count_is_zero():
    # Self-contained so collection order cannot hide a false ZERO.
    hits = list(FALSE_ZERO)
    h = _hyp(latent_object="F(z) = z**3")
    good = "(x**3 - y**3)/(x - y)"
    cr, _vs = _run(h, {"G0001": good})
    o = cr.obligations[0]
    mutations = [
        ("sign", replace(o, left=f"-({good})")),
        ("coeff", replace(o, left=f"2*({good})")),
        ("nodes", replace(o, nodes=["x", "w"])),
        ("limit_pt", replace(o, kind="CONFLUENCE", left=good, right="2*y", var="x", to="0", compile_status=COMPILE_OK)),
    ]
    for label, obl in mutations:
        v = verify_obligation(obl, symbols=SYMS)
        if v.verdict == ZERO:
            hits.append(label)
    assert hits == [], hits
