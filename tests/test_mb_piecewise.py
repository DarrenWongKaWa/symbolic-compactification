"""Piecewise family normalizer. Roles from conditions only. No confluence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import sympy
from sympy.core.function import AppliedUndef

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.piecewise import (  # noqa: E402
    DIAGONAL,
    GENERIC,
    HIGHER_DEGENERACY,
    UNKNOWN_ROLE,
    classify_condition,
    normalize_piecewise_family,
)
from research.scalable_verification.factor.split import (  # noqa: E402
    split_multiplicative,
)

FROZEN = ROOT / "research" / "multibranch_verification" / "FROZEN_INPUTS_V2.json"

m, n, ell = sympy.symbols("m n ell", real=True)
x, y, z = sympy.symbols("x y z")
h1 = sympy.Function("h1")
h2 = sympy.Function("h2")


def _eq(a: sympy.Expr, b: sympy.Expr) -> bool:
    if a == b:
        return True
    try:
        return sympy.cancel(a - b) == 0
    except Exception:
        return False


def _ids(out: dict, role: str) -> list[str]:
    return [row["member_id"] for row in out["members"] if row["role"] == role]


def test_public_api_and_role_labels():
    assert GENERIC == "generic"
    assert DIAGONAL == "diagonal"
    assert HIGHER_DEGENERACY == "higher-degeneracy"
    assert UNKNOWN_ROLE == "unknown"
    assert callable(normalize_piecewise_family)
    assert callable(classify_condition)


def test_true_is_generic():
    for cond in (True, sympy.true, sympy.S.true, "True", "true"):
        assert classify_condition(cond)["role"] == GENERIC


def test_pairwise_eq_is_diagonal():
    assert classify_condition(sympy.Eq(m, n))["role"] == DIAGONAL
    assert classify_condition(sympy.Eq(ell, n))["role"] == DIAGONAL
    assert classify_condition(sympy.Eq(ell, m))["role"] == DIAGONAL
    srepr = "Equality(Symbol('m', real=True), Symbol('n', real=True))"
    got = classify_condition(srepr)
    assert got["role"] == DIAGONAL
    assert got["n_indices"] == 2
    assert got["index_symbols"] == ["m", "n"]


def test_three_index_and_is_higher_degeneracy():
    cond = sympy.And(sympy.Eq(ell, m), sympy.Eq(m, n))
    got = classify_condition(cond)
    assert got["role"] == HIGHER_DEGENERACY
    assert got["n_indices"] == 3
    assert got["index_symbols"] == ["ell", "m", "n"]
    srepr = (
        "And(Equality(Symbol('ell', real=True), Symbol('m', real=True)), "
        "Equality(Symbol('m', real=True), Symbol('n', real=True)))"
    )
    assert classify_condition(srepr)["role"] == HIGHER_DEGENERACY
    triple = sympy.And(sympy.Eq(ell, m), sympy.Eq(m, n), sympy.Eq(ell, n))
    assert classify_condition(triple)["role"] == HIGHER_DEGENERACY


def test_roles_ignore_branch_text():
    # Diagonal-looking kernel under True is still generic.
    out = normalize_piecewise_family([
        {"member_id": "g", "cond": True, "text": h1(m, n) * (m - n)},
        {"member_id": "d", "cond": sympy.Eq(m, n), "text": h1(m, n) * (x + y)},
    ])
    assert _ids(out, GENERIC) == ["g"]
    assert _ids(out, DIAGONAL) == ["d"]


def test_five_branch_family_not_collapsed():
    spec = h1(m, n) * h1(ell, m) * h2(n, ell)
    members = [
        {"member_id": "G0012", "cond": sympy.And(sympy.Eq(ell, m), sympy.Eq(m, n)),
         "text": spec * sympy.Integer(3)},
        {"member_id": "G0013", "cond": sympy.Eq(m, n), "text": spec * (x + 1)},
        {"member_id": "G0014", "cond": sympy.Eq(ell, n), "text": spec * (x + 2)},
        {"member_id": "G0015", "cond": sympy.Eq(ell, m), "text": spec * (x + 3)},
        {"member_id": "G0016", "cond": True, "text": spec * (x + y)},
    ]
    out = normalize_piecewise_family(members)
    assert out["n_members"] == 5
    assert [row["member_id"] for row in out["members"]] == [
        "G0012", "G0013", "G0014", "G0015", "G0016",
    ]
    assert out["collapsed"] is False
    assert out["confluence_inferred"] is False
    assert "reconstruction_rule" not in out
    assert "family_verdict" not in out
    assert "local_edges" not in out
    assert out["n_generic"] == 1
    assert out["n_diagonal"] == 3
    assert out["n_higher_degeneracy"] == 1
    assert out["roles"][GENERIC] == ["G0016"]
    assert out["roles"][DIAGONAL] == ["G0013", "G0014", "G0015"]
    assert out["roles"][HIGHER_DEGENERACY] == ["G0012"]
    # Three pairwise coincidences stay three members.
    assert len(out["members"]) == len(members)


def test_common_applied_undef_spectator_certified():
    spec = h1(m) * h2(n)
    A = spec * (x + 1)
    B = spec * (y + 2)
    C = spec * (x + y)
    out = normalize_piecewise_family([
        {"member_id": "a", "cond": True, "text": A},
        {"member_id": "b", "cond": sympy.Eq(m, n), "text": B},
        {"member_id": "c", "cond": sympy.And(sympy.Eq(ell, m), sympy.Eq(m, n)),
         "text": C},
    ])
    assert out["spectator_certified"] is True
    assert out["spectator_note"] == "exact_applied_undef_factor"
    assert isinstance(out["spectator"], AppliedUndef) or out["spectator"].is_Mul
    assert set(sympy.Mul.make_args(out["spectator"])) == {h1(m), h2(n)}
    by_id = {row["member_id"]: row for row in out["members"]}
    assert _eq(out["spectator"] * by_id["a"]["local"], A)
    assert _eq(out["spectator"] * by_id["b"]["local"], B)
    assert _eq(out["spectator"] * by_id["c"]["local"], C)


def test_two_member_spectator_matches_split_multiplicative_undef():
    spec = h1(m, n) * h2(ell)
    A = spec * (x + 1)
    B = spec * z
    out = normalize_piecewise_family([
        {"cond": True, "text": A},
        {"cond": sympy.Eq(m, n), "text": B},
    ])
    split = split_multiplicative(A, B)
    assert split["certified"] is True
    assert out["spectator_certified"] is True
    assert _eq(out["spectator"], split["S"])
    assert _eq(out["members"][0]["local"], split["A_local"])
    assert _eq(out["members"][1]["local"], split["B_local"])


def test_polynomial_gcd_is_not_an_applied_undef_spectator():
    A = (x + 1) * y
    B = (x + 1) * z
    split = split_multiplicative(A, B)
    assert split["certified"] is True
    out = normalize_piecewise_family([
        {"cond": True, "text": A},
        {"cond": sympy.Eq(m, n), "text": B},
    ])
    assert out["spectator_certified"] is False
    assert out["spectator"] == 1
    assert out["spectator_note"] == "no_exact_common_applied_undef"


def test_missing_undef_on_one_member_not_certified():
    spec = h1(m) * h2(n)
    out = normalize_piecewise_family([
        {"cond": True, "text": spec * x},
        {"cond": sympy.Eq(m, n), "text": h1(m) * y},
        {"cond": sympy.Eq(ell, n), "text": z},
    ])
    assert out["spectator_certified"] is False
    assert out["spectator"] == 1


def test_partial_common_undef_kept():
    out = normalize_piecewise_family([
        {"cond": True, "text": h1(m) * h2(n) * x},
        {"cond": sympy.Eq(m, n), "text": h1(m) * y},
    ])
    assert out["spectator_certified"] is True
    assert _eq(out["spectator"], h1(m))
    assert _eq(out["members"][0]["local"], h2(n) * x)
    assert _eq(out["members"][1]["local"], y)


def test_unknown_conditions_fail_closed():
    assert classify_condition(sympy.Ne(m, n))["role"] == UNKNOWN_ROLE
    assert classify_condition(m > n)["role"] == UNKNOWN_ROLE
    assert classify_condition("")["role"] == UNKNOWN_ROLE
    assert classify_condition(None)["role"] == UNKNOWN_ROLE
    assert classify_condition(sympy.Eq(m, 0))["role"] == UNKNOWN_ROLE
    assert classify_condition(False)["role"] == UNKNOWN_ROLE
    out = normalize_piecewise_family([
        {"member_id": "u", "cond": sympy.Ne(m, n), "text": x},
    ])
    assert out["roles"][UNKNOWN_ROLE] == ["u"]
    assert out["n_unknown"] == 1


def test_piecewise_input_preserves_branch_order():
    spec = h1(n)
    # True last: a leading True branch is the whole Piecewise under SymPy.
    pw = sympy.Piecewise(
        (spec * z, sympy.And(sympy.Eq(ell, m), sympy.Eq(m, n))),
        (spec * y, sympy.Eq(m, n)),
        (spec * x, True),
        evaluate=False,
    )
    assert isinstance(pw, sympy.Piecewise)
    out = normalize_piecewise_family(pw)
    assert out["n_members"] == 3
    assert [row["role"] for row in out["members"]] == [
        HIGHER_DEGENERACY, DIAGONAL, GENERIC,
    ]
    assert out["collapsed"] is False
    assert out["spectator_certified"] is True
    assert _eq(out["spectator"], h1(n))


def test_tuple_members_are_expr_cond():
    out = normalize_piecewise_family([
        (h1(n) * x, True),
        (h1(n) * y, sympy.Eq(m, n)),
    ])
    assert [row["role"] for row in out["members"]] == [GENERIC, DIAGONAL]
    assert out["spectator_certified"] is True
    assert _eq(out["spectator"], h1(n))


def test_two_generic_branches_not_merged():
    out = normalize_piecewise_family([
        {"member_id": "g1", "cond": True, "text": h1(n) * x},
        {"member_id": "g2", "cond": "True", "text": h1(n) * y},
    ])
    assert out["n_generic"] == 2
    assert out["n_members"] == 2
    assert out["collapsed"] is False
    assert out["roles"][GENERIC] == ["g1", "g2"]


def test_unparseable_text_does_not_invent_spectator():
    out = normalize_piecewise_family([
        {"cond": True, "text": h1(n) * x},
        {"cond": sympy.Eq(m, n), "text": ""},
    ])
    assert out["spectator_certified"] is False
    assert out["spectator_note"] == "unparseable_member_text"
    assert [row["role"] for row in out["members"]] == [GENERIC, DIAGONAL]


def test_frozen_five_branch_roles_without_text_or_confluence():
    blob = json.loads(FROZEN.read_text())
    hyp = next(
        h for h in blob["hypotheses"]
        if h.get("n_members") == 5 and h.get("claimed_type") == "local_confluence"
    )
    out = normalize_piecewise_family(hyp["members"])
    assert out["n_members"] == 5
    assert out["collapsed"] is False
    assert out["confluence_inferred"] is False
    assert out["spectator_certified"] is False
    by = {row["member_id"]: row["role"] for row in out["members"]}
    assert by["G0016"] == GENERIC
    assert by["G0013"] == DIAGONAL
    assert by["G0014"] == DIAGONAL
    assert by["G0015"] == DIAGONAL
    assert by["G0012"] == HIGHER_DEGENERACY
    assert [row["member_id"] for row in out["members"]] == [
        m["member_id"] for m in hyp["members"]
    ]


def test_hypothesis_dict_payload_accepted():
    payload = {
        "family_id": "toy",
        "members": [
            {"member_id": "g", "cond": True, "text": h1(n) * x},
            {"member_id": "d", "cond": sympy.Eq(m, n), "text": h1(n) * y},
        ],
        "reconstruction_rule": "should be ignored",
    }
    out = normalize_piecewise_family(payload)
    assert "reconstruction_rule" not in out
    assert out["roles"][GENERIC] == ["g"]
    assert out["roles"][DIAGONAL] == ["d"]
    assert out["confluence_inferred"] is False


def test_peel_finds_applied_undef_not_only_top_mul_args():
    A = h1(n) * (x + 1) + h1(n) * (x + 2)
    B = h1(n) * (x + 3) + h1(n) * x
    out = normalize_piecewise_family([
        {"cond": True, "text": A},
        {"cond": sympy.Eq(m, n), "text": B},
    ])
    assert out["spectator_certified"] is True
    assert _eq(out["spectator"], h1(n))
    assert _eq(out["spectator"] * out["members"][0]["local"], A)
    assert _eq(out["spectator"] * out["members"][1]["local"], B)


def test_empty_family_structure_only():
    out = normalize_piecewise_family([])
    assert out["n_members"] == 0
    assert out["collapsed"] is False
    assert out["confluence_inferred"] is False
    assert out["spectator_certified"] is False
    assert out["spectator"] == 1
