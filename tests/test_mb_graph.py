"""Track V2-A branch graphs. Evaluation-only; no FAMILY_ZERO adjudication."""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.freeze_v2 import OUT as FROZEN_PATH
from research.multibranch_verification.graph import (
    OUT,
    build,
    build_certificates,
    dumps,
    required_graph_connected,
)
from research.multibranch_verification.graph.build import (
    ONE_PARAMETER,
    REPEATED_NODE,
    SUBSTITUTION,
    _is_true,
    _parse_equalities,
)
from research.multibranch_verification.schema import (
    EDGE_RELATIONS,
    FAMILY_UNKNOWN,
    ConfluentFamilyCertificate,
    LocalEdge,
)
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS
from research.representation_invention.schema import is_catalog_id

MAP_PATH = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
GID_RE = re.compile(r"^G\d{4}$")
INVENTED = frozenset({"dd_recurrence", "hermite_dd_recurrence", "derivative"})


@pytest.fixture(scope="module")
def frozen():
    return json.loads(FROZEN_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built():
    return build()


@pytest.fixture(scope="module")
def certs():
    return build_certificates()


def _family_map(blob: dict) -> dict[str, dict]:
    return {f["family_id"]: f for f in blob["families"]}


def _edges_by_pair(family: dict) -> dict[tuple[str, str], list[dict]]:
    out: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for e in family["local_edges"]:
        out[(e["source"], e["target"])].append(e)
    return out


def test_seven_frozen_families(built, frozen, certs):
    assert frozen["n_hypotheses"] == 7
    assert built["n_families"] == 7
    assert len(built["families"]) == 7
    assert len(certs) == 7
    assert built["no_llm_calls"] is True
    assert built["evaluation_only"] is True
    assert built["does_not_adjudicate"] is True
    ids = [f["family_id"] for f in built["families"]]
    assert ids == [h["family_id"] for h in frozen["hypotheses"]]
    assert all(isinstance(c, ConfluentFamilyCertificate) for c in certs)


def test_nodes_are_member_gids(built, frozen):
    by_h = {h["family_id"]: h for h in frozen["hypotheses"]}
    for fam in built["families"]:
        hyp = by_h[fam["family_id"]]
        assert fam["member_ids"] == hyp["member_ids"]
        assert fam["member_ids"]
        for gid in fam["member_ids"]:
            assert is_catalog_id(gid)
            assert GID_RE.match(gid)
        assert set(fam["generic_members"] + fam["degenerate_members"]) == set(fam["member_ids"])
        assert not (set(fam["generic_members"]) & set(fam["degenerate_members"]))
        for e in fam["local_edges"]:
            assert e["source"] in fam["member_ids"]
            assert e["target"] in fam["member_ids"]
            assert e["source"] != e["target"]


def test_edges_only_allowed_relations(built):
    for fam in built["families"]:
        assert fam["family_verdict"] == FAMILY_UNKNOWN
        assert fam["recurrence_obligations"] == []
        assert fam["consistency_obligations"] == []
        seen = set()
        for e in fam["local_edges"]:
            assert e["relation"] in EDGE_RELATIONS
            assert e["relation"] != "other"
            assert e["verdict"] == "UNKNOWN"
            key = (e["source"], e["target"], e["relation"])
            assert key not in seen
            seen.add(key)
            assert isinstance(e["variable"], str)
            assert isinstance(e["target_value"], str)


def test_no_invented_dd_or_hermite_tableau_edges(built):
    for fam in built["families"]:
        rels = {e["relation"] for e in fam["local_edges"]}
        assert rels.isdisjoint(INVENTED)


def test_true_vs_eq_mn_is_one_parameter_confluence(frozen, built):
    families = _family_map(built)
    for hyp in frozen["hypotheses"]:
        fam = families[hyp["family_id"]]
        pairs = _edges_by_pair(fam)
        by_parent: dict[str, list[dict]] = defaultdict(list)
        for m in hyp["members"]:
            by_parent[str(m.get("parent_gid") or "")].append(m)
        for group in by_parent.values():
            trues = [m for m in group if _is_true(m.get("cond") or "")]
            eq_mn = [
                m
                for m in group
                if _parse_equalities(m.get("cond") or "") == [("m", "n")]
                or (
                    len(_parse_equalities(m.get("cond") or "")) == 1
                    and set(_parse_equalities(m.get("cond") or "")[0]) == {"m", "n"}
                )
            ]
            for src in trues:
                for tgt in eq_mn:
                    found = pairs.get((src["member_id"], tgt["member_id"])) or []
                    conf = [e for e in found if e["relation"] == ONE_PARAMETER]
                    assert conf, (hyp["family_id"], src["member_id"], tgt["member_id"])
                    e = conf[0]
                    assert "epsilon(m)" in e["variable"]
                    assert "epsilon(n)" in e["target_value"]


def test_eq_involving_ell_is_one_parameter(frozen, built):
    families = _family_map(built)
    n_ell = 0
    for hyp in frozen["hypotheses"]:
        fam = families[hyp["family_id"]]
        pairs = _edges_by_pair(fam)
        by_parent: dict[str, list[dict]] = defaultdict(list)
        for m in hyp["members"]:
            by_parent[str(m.get("parent_gid") or "")].append(m)
        for group in by_parent.values():
            trues = [m for m in group if _is_true(m.get("cond") or "")]
            for tgt in group:
                eqs = _parse_equalities(tgt.get("cond") or "")
                if len(eqs) != 1:
                    continue
                a, b = eqs[0]
                if "ell" not in {a, b}:
                    continue
                n_ell += 1
                for src in trues:
                    found = pairs.get((src["member_id"], tgt["member_id"])) or []
                    conf = [e for e in found if e["relation"] == ONE_PARAMETER]
                    assert conf, (hyp["family_id"], src["member_id"], tgt["member_id"], tgt.get("cond"))
                    e = conf[0]
                    assert "epsilon(ell)" in e["variable"]
    assert n_ell >= 2


def test_full_coalescence_is_repeated_node(frozen, built):
    families = _family_map(built)
    n = 0
    for hyp in frozen["hypotheses"]:
        fam = families[hyp["family_id"]]
        pairs = _edges_by_pair(fam)
        by_parent: dict[str, list[dict]] = defaultdict(list)
        for m in hyp["members"]:
            by_parent[str(m.get("parent_gid") or "")].append(m)
        for group in by_parent.values():
            trues = [m for m in group if _is_true(m.get("cond") or "")]
            ands = [m for m in group if len(_parse_equalities(m.get("cond") or "")) >= 2]
            for src in trues:
                for tgt in ands:
                    n += 1
                    found = pairs.get((src["member_id"], tgt["member_id"])) or []
                    conf = [e for e in found if e["relation"] == REPEATED_NODE]
                    assert conf, (hyp["family_id"], src["member_id"], tgt["member_id"])
                    e = conf[0]
                    assert "epsilon(m)" in e["variable"]
                    assert "epsilon(ell)" in e["variable"]
                    assert "epsilon(n)" in e["target_value"]
    assert n >= 1


def test_no_edges_between_incomparable_one_parameter_branches(frozen, built):
    families = _family_map(built)
    for hyp in frozen["hypotheses"]:
        fam = families[hyp["family_id"]]
        one_param: list[str] = []
        for m in hyp["members"]:
            if len(_parse_equalities(m.get("cond") or "")) == 1:
                one_param.append(m["member_id"])
        edge_pairs = {(e["source"], e["target"]) for e in fam["local_edges"]}
        for i, a in enumerate(one_param):
            for b in one_param[i + 1 :]:
                assert (a, b) not in edge_pairs
                assert (b, a) not in edge_pairs


def test_five_member_star_and_four_member_swap(built, certs):
    n5 = 0
    n4 = 0
    for fam, cert in zip(built["families"], certs):
        assert required_graph_connected(fam["member_ids"], cert.local_edges)
        n = len(fam["member_ids"])
        rels = {e["relation"] for e in fam["local_edges"]}
        if n == 5:
            n5 += 1
            assert len(fam["generic_members"]) == 1
            assert len(fam["degenerate_members"]) == 4
            assert len(fam["local_edges"]) == 4
            assert rels == {ONE_PARAMETER, REPEATED_NODE}
            assert fam["node_multiplicities"][fam["generic_members"][0]] == 1
            assert 3 in fam["node_multiplicities"].values()
            assert 2 in fam["node_multiplicities"].values()
        elif n == 4:
            n4 += 1
            assert fam["family_id"] == "guo-p2-s2-i4"
            assert set(fam["generic_members"]) == {"G0005", "G0009"}
            assert set(fam["degenerate_members"]) == {"G0004", "G0008"}
            assert len(fam["local_edges"]) == 3
            assert SUBSTITUTION in rels
            assert ONE_PARAMETER in rels
            assert REPEATED_NODE not in rels
            pairs = {(e["source"], e["target"], e["relation"]) for e in fam["local_edges"]}
            assert ("G0005", "G0004", ONE_PARAMETER) in pairs
            assert ("G0009", "G0008", ONE_PARAMETER) in pairs
            assert ("G0005", "G0009", SUBSTITUTION) in pairs
            assert ("G0005", "G0008") not in {(a, b) for a, b, _ in pairs}
            assert ("G0004", "G0008") not in {(a, b) for a, b, _ in pairs}
            sub = next(e for e in fam["local_edges"] if e["relation"] == SUBSTITUTION)
            assert sub["variable"] == "b"
            assert sub["target_value"] == "c"
        else:
            raise AssertionError(f"unexpected family size {n}: {fam['family_id']}")
    assert n5 == 6
    assert n4 == 1


def test_generic_members_are_true_branches(frozen, built):
    families = _family_map(built)
    for hyp in frozen["hypotheses"]:
        fam = families[hyp["family_id"]]
        true_ids = [m["member_id"] for m in hyp["members"] if _is_true(m.get("cond") or "")]
        assert fam["generic_members"] == true_ids


def test_schema_roundtrip_fields(certs):
    for cert in certs:
        payload = cert.to_dict()
        assert payload["family_id"] == cert.family_id
        assert payload["family_verdict"] == FAMILY_UNKNOWN
        for raw, edge in zip(payload["local_edges"], cert.local_edges):
            assert isinstance(edge, LocalEdge)
            assert raw == edge.to_dict()
            assert raw["verdict"] == "UNKNOWN"


def test_no_forbidden_gold_names(built):
    blob = dumps(built)
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, blob) is None, pat
    src = (ROOT / "research" / "multibranch_verification" / "graph" / "build.py").read_text(
        encoding="utf-8"
    )
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, src) is None, pat


def test_committed_json_matches_builder(built):
    assert OUT.is_file(), f"missing {OUT}"
    disk = json.loads(OUT.read_text(encoding="utf-8"))
    assert dumps(disk) == dumps(built)
    assert disk["n_families"] == built["n_families"]


def test_conds_overlay_matches_obligation_map(frozen):
    mblob = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    by = {(r["seed"], r["index"]): r for r in mblob["hypotheses"]}
    for hyp in frozen["hypotheses"]:
        row = by[(hyp["seed"], hyp["index"])]
        mapped = {m["member_id"]: m["cond"] for m in row["members"]}
        for m in hyp["members"]:
            assert mapped[m["member_id"]] == m["cond"]
