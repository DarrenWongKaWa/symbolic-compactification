"""V2 contract: catalog IDs required; aliases are PARSE_FAILURE."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.ladder import TYPE_TO_R_HINT, R_LEVELS
from research.representation_invention.schema import (
    PARSE_FAILURE,
    OK,
    REPRESENTATION_TYPES,
    parse_document_v2,
    parse_hypothesis_v2,
)

CAT = {"G0001", "G0002", "G0007"}


def _base(**kw):
    raw = {
        "representation_type": "local_confluence",
        "member_ids": ["G0001", "G0007"],
        "member_roles": {"G0001": "generic", "G0007": "degenerate"},
        "latent_object": "F(z)",
        "latent_variables": ["z"],
        "nodes": [
            {"name": "x", "expression": "epsilon(m)", "multiplicity": 1},
            {"name": "y", "expression": "epsilon(n)", "multiplicity": 1},
        ],
        "operators": [
            {"member_id": "G0001", "kind": "limit", "args": {"to": "y"}},
        ],
        "instance_maps": {},
        "reconstruction_rule": "limit F(x)->F(y)",
        "required_assumptions": [],
        "proof_obligations": [
            {
                "kind": "CONFLUENCE",
                "member_ids": ["G0001", "G0007"],
                "expected": "limit(G0001)==G0007",
            }
        ],
        "scientific_rationale": "branch limit",
        "confidence": 0.5,
    }
    raw.update(kw)
    return raw


def test_allowed_types_match_protocol():
    assert "local_confluence" in REPRESENTATION_TYPES
    assert "divided_difference" in REPRESENTATION_TYPES
    assert "hermite_divided_difference" in REPRESENTATION_TYPES
    assert "confluent_representation" not in REPRESENTATION_TYPES
    assert set(TYPE_TO_R_HINT) == set(REPRESENTATION_TYPES)
    assert R_LEVELS[0] == "R0" and R_LEVELS[-1] == "R8"


def test_good_hypothesis_parses():
    h = parse_hypothesis_v2(_base(), CAT)
    assert h.parse_status == OK, h.parse_error
    assert h.member_ids == ["G0001", "G0007"]
    assert h.operators[0].kind == "limit"


def test_alias_s1_true_is_parse_failure():
    h = parse_hypothesis_v2(_base(member_ids=["S1_True", "G0007"]), CAT)
    assert h.parse_status == PARSE_FAILURE
    assert "alias" in (h.parse_error or "")


def test_generic_branch_alias_is_parse_failure():
    h = parse_hypothesis_v2(_base(member_ids=["generic_branch"]), CAT)
    assert h.parse_status == PARSE_FAILURE


def test_short_gid_is_parse_failure():
    h = parse_hypothesis_v2(_base(member_ids=["G1"]), CAT)
    assert h.parse_status == PARSE_FAILURE


def test_id_not_in_catalog():
    h = parse_hypothesis_v2(_base(member_ids=["G0001", "G0099"]), CAT)
    assert h.parse_status == PARSE_FAILURE
    assert "id_not_in_catalog" in (h.parse_error or "")


def test_missing_member_ids():
    raw = _base()
    del raw["member_ids"]
    h = parse_hypothesis_v2(raw, CAT)
    assert h.parse_status == PARSE_FAILURE
    assert h.parse_error == "member_ids_required"


def test_p1_confluent_type_rejected():
    h = parse_hypothesis_v2(_base(representation_type="confluent_representation"), CAT)
    assert h.parse_status == PARSE_FAILURE
    assert "p1_type_not_accepted" in (h.parse_error or "")


def test_empty_latent_rejected():
    h = parse_hypothesis_v2(_base(latent_object="  "), CAT)
    assert h.parse_status == PARSE_FAILURE


def test_role_id_must_be_member():
    h = parse_hypothesis_v2(
        _base(member_roles={"G0001": "generic", "G0002": "instance"}),
        CAT,
    )
    assert h.parse_status == PARSE_FAILURE
    assert "role_id_not_in_member_ids" in (h.parse_error or "")


def test_operator_alias_rejected():
    h = parse_hypothesis_v2(
        _base(operators=[{"member_id": "S1_True", "kind": "limit", "args": {}}]),
        CAT,
    )
    assert h.parse_status == PARSE_FAILURE


def test_document_mixed_status_keeps_ok_hyps():
    doc = parse_document_v2(
        {
            "hypotheses": [
                _base(),
                _base(member_ids=["S1_True"]),
            ]
        },
        CAT,
    )
    assert doc["n_ok"] == 1
    assert doc["n_parse_failure"] == 1
    assert doc["parse_status"] == OK
