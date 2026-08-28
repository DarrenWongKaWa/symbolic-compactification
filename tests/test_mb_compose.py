"""Family composition: pairwise ZERO is not FAMILY_ZERO; no majority."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.compose import (  # noqa: E402
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    NONZERO,
    UNKNOWN,
    ZERO,
    certify_family,
    compose_operators,
    multiplicities_consistent,
    operators_agree,
    path_consistency,
    required_graph_connected,
)
from research.multibranch_verification.schema import (  # noqa: E402
    ConfluentFamilyCertificate,
    LocalEdge,
    compose_family_verdict,
)


def _e(src, tgt, verdict="ZERO", relation="limit", variable="", target_value="", operator=None):
    d = {
        "source": src,
        "target": tgt,
        "relation": relation,
        "variable": variable,
        "target_value": target_value,
        "verdict": verdict,
    }
    if operator is not None:
        d["operator"] = operator
    return d


def _lim(src, tgt, mapping, verdict="ZERO"):
    return _e(src, tgt, verdict=verdict, relation="limit", operator={"kind": "limit", "args": mapping})


def _star_edges(generic, members, verdicts, mapping=None):
    mapping = mapping or {"x": "y"}
    return [_lim(generic, m, mapping, verdict=v) for m, v in zip(members, verdicts)]


def test_public_api_importable():
    assert certify_family is not None
    assert path_consistency is not None
    assert compose_family_verdict is not None


def test_certify_family_delegates_to_schema(monkeypatch):
    called = {}

    def fake(**kwargs):
        called.update(kwargs)
        return FAMILY_UNKNOWN

    monkeypatch.setattr(
        "research.multibranch_verification.compose.family.compose_family_verdict",
        fake,
    )
    r = certify_family(
        member_ids=["A", "B"],
        edges=[_lim("A", "B", {"x": "y"})],
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert called
    assert called["connected"] is True
    assert called["required_edge_verdicts"] == [ZERO]
    assert called["recurrence_verdicts"] == [ZERO]
    assert called["path_verdicts"]
    assert r.family_verdict == FAMILY_UNKNOWN


def test_majority_zero_is_not_family_zero():
    members = ["G", "A", "B", "C", "D", "E"]
    edges = _star_edges("G", ["A", "B", "C", "D", "E"], [ZERO, ZERO, ZERO, ZERO, UNKNOWN])
    r = certify_family(
        member_ids=members,
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO
    assert r.required_edge_verdicts.count(ZERO) == 4
    assert UNKNOWN in r.required_edge_verdicts


def test_ten_zero_plus_one_unknown_is_not_family_zero():
    leaves = [f"M{i}" for i in range(11)]
    verdicts = [ZERO] * 10 + [UNKNOWN]
    edges = _star_edges("G", leaves, verdicts)
    r = certify_family(
        member_ids=["G", *leaves],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_any_required_nonzero_is_family_nonzero():
    r = certify_family(
        member_ids=["A", "B"],
        edges=[_lim("A", "B", {"x": "y"}, verdict=NONZERO)],
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.family_verdict == FAMILY_NONZERO


def test_disconnected_all_zero_is_unknown_not_zero():
    edges = [
        _lim("A", "B", {"x": "y"}),
        _lim("C", "D", {"x": "y"}),
    ]
    r = certify_family(
        member_ids=["A", "B", "C", "D"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.connected is False
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO
    assert all(v == ZERO for v in r.required_edge_verdicts)


def test_pairwise_zero_disagreeing_paths_is_not_family_zero():
    """All three edges ZERO, but A→B operators do not agree."""
    edges = [
        _lim("A", "B", {"x": "y"}),
        _lim("A", "C", {"x": "z"}),
        _e("C", "B", relation="identity", operator={"kind": "identity", "args": {}}),
    ]
    r = certify_family(
        member_ids=["A", "B", "C"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert all(v == ZERO for v in r.required_edge_verdicts)
    assert r.connected is True
    assert r.path_consistency.verdict == NONZERO
    assert r.family_verdict == FAMILY_NONZERO
    assert r.family_verdict != FAMILY_ZERO


def test_pairwise_zero_opaque_second_path_is_unknown():
    edges = [
        _lim("A", "B", {"x": "y"}),
        _e("A", "C", operator={"kind": "other", "args": {"note": "opaque"}}),
        _e("C", "B", operator={"kind": "other", "args": {"note": "opaque2"}}),
    ]
    r = certify_family(
        member_ids=["A", "B", "C"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert all(v == ZERO for v in r.required_edge_verdicts)
    assert r.path_consistency.verdict == UNKNOWN
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_connected_all_zero_vacuous_paths_is_family_zero():
    edges = [
        _lim("A", "B", {"x": "y"}),
        _lim("B", "C", {"z": "y"}),
    ]
    r = certify_family(
        member_ids=["A", "B", "C"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        node_multiplicities={"x": 1, "z": 1, "y": 2},
        latent_compatible=True,
    )
    assert r.connected is True
    assert r.path_consistency.verdict == ZERO
    assert r.family_verdict == FAMILY_ZERO


def test_commuting_diamond_is_family_zero():
    edges = [
        _lim("G", "M", {"m": "n"}),
        _lim("G", "L", {"ell": "n"}),
        _lim("G", "D", {"m": "n", "ell": "n"}),
        _lim("M", "D", {"ell": "n"}),
        _lim("L", "D", {"m": "n"}),
    ]
    r = certify_family(
        member_ids=["G", "M", "L", "D"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.connected is True
    assert r.path_consistency.verdict == ZERO
    assert r.family_verdict == FAMILY_ZERO


def test_five_branch_remaining_limits_family_zero():
    """Generic plus three simple degeneracies plus full coalescence."""
    g, m, ell, em, d = "G0016", "G0013", "G0014", "G0015", "G0012"
    edges = [
        _lim(g, m, {"m": "n"}),
        _lim(g, ell, {"ell": "n"}),
        _lim(g, em, {"ell": "m"}),
        _lim(g, d, {"ell": "n", "m": "n"}),
        _lim(m, d, {"ell": "n"}),
        _lim(ell, d, {"m": "n"}),
        _lim(em, d, {"m": "n"}),
    ]
    r = certify_family(
        member_ids=[g, m, ell, em, d],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    pc = path_consistency(edges, members=[g, m, ell, em, d])
    assert pc.verdict == ZERO
    assert r.family_verdict == FAMILY_ZERO


def test_wrong_remaining_limit_is_family_nonzero():
    edges = [
        _lim("G", "M", {"m": "n"}),
        _lim("G", "D", {"m": "n", "ell": "n"}),
        _lim("M", "D", {"ell": "m"}),
    ]
    r = certify_family(
        member_ids=["G", "M", "D"],
        edges=edges,
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.path_consistency.verdict == NONZERO
    assert r.family_verdict == FAMILY_NONZERO


def test_recurrence_unknown_blocks_family_zero():
    r = certify_family(
        member_ids=["A", "B"],
        edges=[_lim("A", "B", {"x": "y"})],
        recurrence_verdicts=["UNKNOWN"],
        latent_compatible=True,
    )
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_multiplicity_conflict_blocks_family_zero():
    r = certify_family(
        member_ids=["A", "B"],
        edges=[_lim("A", "B", {"x": "y"})],
        recurrence_verdicts=["ZERO"],
        node_multiplicities=[("x", 2), ("x", 3)],
        latent_compatible=True,
    )
    assert r.multiplicities_consistent is False
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_multiplicity_zero_is_inconsistent():
    assert multiplicities_consistent({"x": 2}) is True
    assert multiplicities_consistent({"x": 0}) is False
    assert multiplicities_consistent({"x": -1}) is False
    assert multiplicities_consistent(None) is True


def test_latent_incompatible_blocks_family_zero():
    r = certify_family(
        member_ids=["A", "B"],
        edges=[_lim("A", "B", {"x": "y"})],
        recurrence_verdicts=["ZERO"],
        latent_compatible=False,
    )
    assert r.latent_compatible is False
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_empty_family_is_unknown():
    r = certify_family(member_ids=[], edges=[], latent_compatible=True)
    assert r.family_verdict == FAMILY_UNKNOWN
    assert r.family_verdict != FAMILY_ZERO


def test_no_edges_connected_pair_is_unknown():
    r = certify_family(
        member_ids=["A", "B"],
        edges=[],
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.connected is False
    assert r.family_verdict == FAMILY_UNKNOWN


def test_disconnected_nonzero_is_still_family_nonzero():
    r = certify_family(
        member_ids=["A", "B", "C"],
        edges=[_lim("A", "B", {"x": "y"}, verdict=NONZERO)],
        recurrence_verdicts=["ZERO"],
        latent_compatible=True,
    )
    assert r.connected is False
    assert r.family_verdict == FAMILY_NONZERO


def test_path_consistency_xy_vs_xz_nonzero():
    pc = path_consistency(
        paths=[
            [{"kind": "limit", "args": {"x": "y"}}],
            [{"kind": "limit", "args": {"x": "z"}}],
        ]
    )
    assert pc.verdict == NONZERO
    assert pc.verdict != ZERO


def test_path_consistency_vacuous_single_path_zero():
    pc = path_consistency(paths=[[{"kind": "limit", "args": {"x": "y"}}]])
    assert pc.verdict == ZERO


def test_path_consistency_empty_is_unknown():
    assert path_consistency(paths=[]).verdict == UNKNOWN
    assert path_consistency(edges=[]).verdict == UNKNOWN


def test_identity_is_unit_of_composition():
    lim = {"kind": "limit", "args": {"x": "y"}}
    assert operators_agree(compose_operators({"kind": "identity"}, lim), lim) == ZERO
    assert operators_agree(compose_operators(lim, "identity"), lim) == ZERO


def test_independent_limits_commute():
    a = compose_operators({"kind": "limit", "args": {"x": "a"}}, {"kind": "limit", "args": {"y": "b"}})
    b = compose_operators({"kind": "limit", "args": {"y": "b"}}, {"kind": "limit", "args": {"x": "a"}})
    assert operators_agree(a, b) == ZERO


def test_sequential_limits_do_not_commute():
    a = compose_operators({"kind": "limit", "args": {"x": "y"}}, {"kind": "limit", "args": {"y": "z"}})
    b = compose_operators({"kind": "limit", "args": {"y": "z"}}, {"kind": "limit", "args": {"x": "y"}})
    assert operators_agree(a, b) == NONZERO


def test_swap_commutes_with_independent_limit():
    swap = {"kind": "substitution", "args": {"substitution": {"b": "c", "c": "b"}}}
    lim = {"kind": "limit", "args": {"var": "epsilon(m)", "to": "epsilon(n)"}}
    assert operators_agree(compose_operators(swap, lim), compose_operators(lim, swap)) == ZERO


def test_frozen_compose_swap_then_limit():
    nested = {
        "kind": "other",
        "args": {
            "compose": [
                {"kind": "substitution", "args": {"b": "c", "c": "b"}},
                {"kind": "limit", "args": {"var": "epsilon(m)", "to": "epsilon(n)"}},
            ]
        },
    }
    swap = {"kind": "substitution", "args": {"b": "c", "c": "b"}}
    lim = {"kind": "limit", "args": {"var": "epsilon(m)", "to": "epsilon(n)"}}
    assert operators_agree(nested, compose_operators(swap, lim)) == ZERO


def test_constraint_string_and_numbered_sources():
    a = compose_operators({"kind": "limit", "args": {"constraint": "x -> y and z -> y"}})
    b = compose_operators(
        {
            "kind": "limit",
            "args": {
                "source1": "x",
                "target1": "y",
                "source2": "z",
                "target2": "y",
            },
        }
    )
    assert operators_agree(a, b) == ZERO


def test_hermite_vs_limit_is_unknown_not_zero():
    assert (
        operators_agree(
            {"kind": "hermite_dd_recurrence", "args": {"variable": "x", "multiplicity": 2}},
            {"kind": "limit", "args": {"y": "x"}},
        )
        == UNKNOWN
    )


def test_localedge_certificate_roundtrip():
    edges = [
        LocalEdge(source="A", target="B", relation="limit", variable="x", target_value="y", verdict=ZERO),
        LocalEdge(source="B", target="C", relation="limit", variable="z", target_value="y", verdict=ZERO),
    ]
    cert = ConfluentFamilyCertificate(
        family_id="toy",
        member_ids=["A", "B", "C"],
        local_edges=edges,
        recurrence_obligations=[{"verdict": ZERO}],
        node_multiplicities={"y": 2},
    )
    r = certify_family(cert, latent_compatible=True)
    assert r.family_verdict == FAMILY_ZERO
    assert r.certificate is not None
    assert r.certificate.family_verdict == FAMILY_ZERO


def test_required_graph_connected():
    assert required_graph_connected(["A", "B"], [_lim("A", "B", {"x": "y"})]) is True
    assert required_graph_connected(["A", "B", "C"], [_lim("A", "B", {"x": "y"})]) is False
    assert required_graph_connected(["A"], []) is True
    assert required_graph_connected([], []) is False


def test_schema_compose_family_verdict_still_no_majority():
    assert (
        compose_family_verdict(
            required_edge_verdicts=[ZERO, ZERO, ZERO, ZERO, UNKNOWN],
            recurrence_verdicts=[ZERO],
            path_verdicts=[ZERO],
            connected=True,
            multiplicities_consistent=True,
        )
        == FAMILY_UNKNOWN
    )
