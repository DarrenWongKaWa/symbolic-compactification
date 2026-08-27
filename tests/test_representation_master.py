"""Gold-free master-object quality and fail-closed instantiation."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import sympy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS
from research.representation_invention.master import (
    UNIT_INTERVAL_AXES,
    instantiate_operator,
    score_master_hypothesis,
)
from research.representation_invention.schema import (
    OK,
    OPERATOR_KINDS,
    OperatorSpec,
    PARSE_FAILURE,
    RepresentationHypothesisV2,
    parse_hypothesis_v2,
)

CAT = {"G0001", "G0002", "G0007"}
MASTER_ROOT = ROOT / "research" / "representation_invention" / "master"
GID_RE = re.compile(r"^G\d{4}$")


def _base(**kw):
    raw = {
        "representation_type": "master_function",
        "member_ids": ["G0001"],
        "member_roles": {"G0001": "instance"},
        "latent_object": "F(z)",
        "latent_variables": ["z"],
        "nodes": [],
        "operators": [{"member_id": "G0001", "kind": "identity", "args": {}}],
        "instance_maps": {"G0001": {"theta": {}}},
        "reconstruction_rule": "",
        "required_assumptions": [],
        "proof_obligations": [],
        "scientific_rationale": "single identity instance",
        "confidence": 0.4,
    }
    raw.update(kw)
    return raw


def _three_ops(**kw):
    raw = {
        "representation_type": "master_function",
        "member_ids": ["G0001", "G0002", "G0007"],
        "member_roles": {
            "G0001": "instance",
            "G0002": "instance",
            "G0007": "instance",
        },
        "latent_object": "F(z)",
        "latent_variables": ["z"],
        "nodes": [
            {"name": "z1", "expression": "z1", "multiplicity": 1},
            {"name": "z2", "expression": "z2", "multiplicity": 1},
            {"name": "z3", "expression": "z3", "multiplicity": 1},
            {"name": "z4", "expression": "z4", "multiplicity": 1},
        ],
        "operators": [
            {
                "member_id": "G0001",
                "kind": "substitution",
                "args": {"theta": {"z": "z1"}},
            },
            {
                "member_id": "G0002",
                "kind": "derivative",
                "args": {"var": "z", "at": "z2", "order": 1},
            },
            {
                "member_id": "G0007",
                "kind": "newton_dd",
                "args": {"var": "z", "nodes": ["z3", "z4"]},
            },
        ],
        "instance_maps": {
            "G0001": {"theta": {"z": "z1"}},
            "G0002": {"theta": {"z": "z2"}},
            "G0007": {"theta": {"z": "z"}, "nodes": ["z3", "z4"]},
        },
        "reconstruction_rule": "A1=F(z1); A2=dF/dz(z2); A3=F[z3,z4]",
        "required_assumptions": ["z3 != z4"],
        "proof_obligations": [
            {
                "kind": "MASTER_INSTANCE",
                "member_ids": ["G0001"],
                "operator": "substitution",
                "expected": "member == F(z1)",
            }
        ],
        "scientific_rationale": "one latent F under substitution, derivative, first DD",
        "confidence": 0.7,
    }
    raw.update(kw)
    return raw


def _assert_unit_interval(score: dict) -> None:
    for axis in UNIT_INTERVAL_AXES:
        val = score[axis]
        assert val is None or (isinstance(val, (int, float)) and 0.0 <= float(val) <= 1.0), axis
    assert isinstance(score["reuse"], int) and score["reuse"] >= 0
    assert isinstance(score["structural_depth"], int) and score["structural_depth"] >= 0
    assert score["tautological_wrapper"] in (True, False)


def test_tautology_identity_used_once():
    h = parse_hypothesis_v2(
        _base(
            latent_object="sin(x)+x**2",
            latent_variables=["x"],
            operators=[{"member_id": "G0001", "kind": "identity", "args": {}}],
        ),
        CAT,
    )
    assert h.parse_status == OK, h.parse_error
    kinds_before = [op.kind for op in h.operators]
    score = score_master_hypothesis(h, member_texts={"G0001": "sin(x)+x**2"})
    _assert_unit_interval(score)
    assert score["tautological_wrapper"] is True
    assert score["reuse"] <= 1
    assert score["structural_depth"] == 0
    assert [op.kind for op in h.operators] == kinds_before


def test_three_members_substitution_derivative_newton_dd():
    h = parse_hypothesis_v2(_three_ops(), CAT)
    assert h.parse_status == OK, h.parse_error
    assert {op.kind for op in h.operators} >= {"substitution", "derivative", "newton_dd"}
    score = score_master_hypothesis(h)
    _assert_unit_interval(score)
    assert score["tautological_wrapper"] is False
    assert score["reuse"] >= 3
    assert score["structural_depth"] >= 2
    assert score["coverage"] == 1.0
    assert score["operator_coherence"] == 1.0
    assert 0.0 <= score["parameter_coherence"] <= 1.0
    assert score["description_length_gain"] is None


def test_description_length_gain_none_without_member_texts():
    h = parse_hypothesis_v2(_three_ops(), CAT)
    score = score_master_hypothesis(h)
    assert score["description_length_gain"] is None
    texts = {
        "G0001": "alpha(z1)*alpha(z1)+beta(z1)",
        "G0002": "2*alpha(z2)*dalpha(z2)+dbeta(z2)",
        "G0007": "(alpha(z3)*alpha(z3)-alpha(z4)*alpha(z4))/(z3-z4)",
    }
    scored = score_master_hypothesis(h, member_texts=texts)
    assert scored["description_length_gain"] is not None
    assert 0.0 <= scored["description_length_gain"] <= 1.0


def test_scores_are_unit_interval_or_none():
    hyps = [
        parse_hypothesis_v2(_base(), CAT),
        parse_hypothesis_v2(_three_ops(), CAT),
    ]
    for h in hyps:
        score = score_master_hypothesis(h)
        _assert_unit_interval(score)
        for axis in UNIT_INTERVAL_AXES:
            val = score[axis]
            assert val is None or 0.0 <= float(val) <= 1.0


def test_does_not_rewrite_shallow_wrapper():
    h = parse_hypothesis_v2(_base(latent_object="G0001"), CAT)
    assert h.parse_status == OK, h.parse_error
    score = score_master_hypothesis(h)
    assert score["tautological_wrapper"] is True
    assert h.operators[0].kind == "identity"
    assert h.latent_object == "G0001"


def test_unknown_kind_is_incoherent_not_repaired():
    h = RepresentationHypothesisV2(
        representation_type="master_function",
        member_ids=["G0001", "G0002"],
        latent_object="F(z)",
        latent_variables=["z"],
        operators=[
            OperatorSpec(member_id="G0001", kind="not_a_kind", args={}),
            OperatorSpec(member_id="G0002", kind="derivative", args={"var": "z"}),
        ],
        confidence=0.2,
    )
    score = score_master_hypothesis(h)
    _assert_unit_interval(score)
    assert score["operator_coherence"] < 1.0
    assert h.operators[0].kind == "not_a_kind"


def test_catalog_ids_in_fixtures():
    for raw in (_base(), _three_ops()):
        h = parse_hypothesis_v2(raw, CAT)
        assert h.parse_status == OK, h.parse_error
        assert h.member_ids
        assert all(GID_RE.fullmatch(m) for m in h.member_ids)
        assert all(GID_RE.fullmatch(op.member_id) for op in h.operators)


def test_aliases_are_parse_failure_not_repaired():
    h = parse_hypothesis_v2(_base(member_ids=["S1_True"]), CAT)
    assert h.parse_status == PARSE_FAILURE
    assert "alias" in (h.parse_error or "")


def test_master_sources_have_no_gold_or_alias_tokens():
    blob = ""
    for path in MASTER_ROOT.rglob("*"):
        if path.suffix in {".py", ".md"} and path.is_file():
            blob += path.read_text(encoding="utf-8")
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert not re.search(pat, blob), pat
    assert "S1_True" not in blob
    assert "generic_branch" not in blob


def test_instantiate_substitution_derivative_newton():
    symbols = [{"name": n, "real": True} for n in ("z", "z1", "z2", "z3", "z4")]
    subst = instantiate_operator(
        "z**2",
        OperatorSpec(member_id="G0001", kind="substitution", args={"theta": {"z": "z1"}}),
        symbols,
        None,
    )
    deriv = instantiate_operator(
        "z**2",
        {
            "member_id": "G0002",
            "kind": "derivative",
            "args": {"var": "z", "at": "z2", "order": 1},
        },
        symbols,
        None,
    )
    dd = instantiate_operator(
        "z**2",
        OperatorSpec(
            member_id="G0007",
            kind="newton_dd",
            args={"var": "z", "nodes": ["z3", "z4"]},
        ),
        symbols,
        None,
    )
    z1, z2, z3, z4 = sympy.symbols("z1 z2 z3 z4", real=True)
    assert subst is not None and sympy.expand(subst - z1**2) == 0
    assert deriv is not None and sympy.expand(deriv - 2 * z2) == 0
    assert dd is not None
    assert sympy.expand(dd * (z4 - z3) - (z4**2 - z3**2)) == 0


def test_instantiate_fail_closed():
    symbols = [{"name": "z", "real": True}]
    assert instantiate_operator("z**2", {"kind": "shift", "args": {}}, symbols, None) is None
    assert instantiate_operator("z**2", {"kind": "other", "args": {}}, symbols, None) is None
    assert instantiate_operator("z**2", {"kind": "not_a_kind", "args": {}}, symbols, None) is None
    assert instantiate_operator("", {"kind": "identity", "args": {}}, symbols, None) is None
    assert instantiate_operator(
        "z**2",
        {"kind": "newton_dd", "args": {"var": "z", "nodes": ["z"]}},
        symbols,
        None,
    ) is None


def test_operator_kinds_match_schema():
    assert "substitution" in OPERATOR_KINDS
    assert "derivative" in OPERATOR_KINDS
    assert "newton_dd" in OPERATOR_KINDS
    assert "permutation" in OPERATOR_KINDS
    assert "divided_difference" not in OPERATOR_KINDS
