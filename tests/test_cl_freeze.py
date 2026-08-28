"""V5 freeze: generic→diagonal hops only. No new hypotheses."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.freeze_v5 import OUT, PRIMARY, build  # noqa: E402


def test_freeze_has_primary_and_siblings():
    blob = build()
    assert blob["no_llm_calls"] is True
    assert blob["no_new_hypotheses"] is True
    assert blob["parent_track_v4"] == "248d247"
    ids = [h["hop_id"] for h in blob["hops"]]
    assert any(h.endswith("G0016->G0013") for h in ids)
    assert blob["primary_hop"] == "guo-p2-s0-i3:G0016->G0013"
    primary = [h for h in blob["hops"] if h.get("is_primary")]
    assert len(primary) == 1
    p = primary[0]
    assert p["source_member"] == PRIMARY[0]
    assert p["target_member"] == PRIMARY[1]
    assert p["source"]["text_sha256"]
    assert p["source"]["text_sha256"] != p["target"]["text_sha256"]
    assert p["v4_verdict"] == "UNKNOWN"


def test_every_member_has_computed_text_hash():
    blob = build()
    for h in blob["hops"]:
        assert len(h["source"]["text_sha256"]) == 64
        assert len(h["target"]["text_sha256"]) == 64
        assert h["source"]["text_len"] > 0
        assert h["target"]["text_len"] > 0


def test_manifest_matches_if_present():
    if OUT.is_file():
        disk = json.loads(OUT.read_text())
        assert disk["n_hops"] == build()["n_hops"]
        assert disk["primary_hop"] == build()["primary_hop"]
