"""P1 contract: catalog IDs only. No live API."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.grounded_proposer.catalog import catalog_entries, catalog_ids, render_catalog
from research.grounded_proposer.parser import parse_p1
from research.obligation_ir.source_index import build_index


def _idx():
    expr = (
        "Sum(Piecewise((K(n), Eq(m, n)), (G(m, n)*h1(b, n, m)*h2(a, c, m, n), True)), "
        "(n, 1, N), (m, 1, N))"
    )
    return build_index(
        expr,
        [{"name": x, "real": True} for x in ("n", "m", "N", "a", "b", "c")],
        ["K", "G", "h1", "h2"],
    )


def test_catalog_has_branches_not_aliases():
    entries = catalog_entries(_idx())
    ids = catalog_ids(entries)
    assert any(e["kind"] == "piecewise_branch" for e in entries)
    assert all(i.startswith("G") for i in ids)
    assert not any(e["source_node_id"].startswith("S") for e in entries)


def test_alias_is_parse_failure():
    idx = _idx()
    ids = catalog_ids(catalog_entries(idx))
    raw = """{
      "hypotheses": [{
        "representation_type": "confluent_representation",
        "latent_object": "F",
        "member_maps": [{"source_node_id": "S1_True", "role": "generic"}],
        "operators": [],
        "proof_obligations": [],
        "required_assumptions": [],
        "rationale": "x",
        "confidence": 0.4
      }]
    }"""
    p = parse_p1(raw, ids)
    assert p["n_ok"] == 0
    assert p["hypotheses"][0].parse_status == "PARSE_FAILURE"


def test_catalog_id_ok():
    idx = _idx()
    ids = catalog_ids(catalog_entries(idx))
    gid = sorted(ids)[0]
    raw = json_hyp(gid)
    p = parse_p1(raw, ids)
    assert p["n_ok"] == 1, p


def json_hyp(gid: str) -> str:
    return (
        '{"hypotheses":[{"representation_type":"confluent_representation",'
        '"latent_object":"K(x,y)","generic_member":"%s","degenerate_member":"%s",'
        '"member_maps":[{"source_node_id":"%s","role":"generic"}],'
        '"operators":[],"proof_obligations":[],"required_assumptions":[],'
        '"rationale":"x","confidence":0.5}]}' % (gid, gid, gid)
    )
