"""Track V3 freeze: exactly the 7 V2 families. No new hypotheses."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.freeze_v3 import OUT, build  # noqa: E402
from research.multibranch_verification.freeze_v2 import build as build_v2  # noqa: E402


def test_freeze_is_the_seven_v2_families():
    blob = build()
    v2 = build_v2()
    assert blob["n_hypotheses"] == 7
    assert blob["no_llm_calls"] is True
    assert blob["no_new_hypotheses"] is True
    assert blob["parent_track_v2_close"] == "fe53ebc"
    ids = [h["family_id"] for h in blob["hypotheses"]]
    v2_ids = [h["family_id"] for h in v2["hypotheses"]]
    assert ids == v2_ids
    assert blob["family_ids"] == v2_ids


def test_each_record_has_required_fields():
    blob = build()
    required = {
        "family_id",
        "member_ids",
        "source_sha256",
        "branch_conditions",
        "degeneracy_variables",
        "v2_family_verdict",
        "v2_unknown_reason",
        "known_zero_pairwise_edges",
        "op_counts",
        "v2_local_edges",
        "old_unknown_reason",
        "previous_verifier_verdict",
        "previous_compiler_state",
    }
    for h in blob["hypotheses"]:
        missing = required - set(h)
        assert not missing, (h["family_id"], missing)
        assert h["v2_family_verdict"] == "FAMILY_UNKNOWN"
        assert h["source_sha_match"] is True
        assert h["n_members"] == len(h["member_ids"]) == len(h["members"])
        for mid, ops in h["op_counts"].items():
            assert isinstance(ops, int) and ops > 0
            assert mid in h["branch_conditions"]


def test_known_zero_edges_only_on_s2_i4():
    blob = build()
    for h in blob["hypotheses"]:
        zeros = h["known_zero_pairwise_edges"]
        if h["family_id"] == "guo-p2-s2-i4":
            pairs = {(z["source"], z["target"]) for z in zeros}
            assert pairs == {("G0005", "G0004"), ("G0009", "G0008")}
        else:
            assert zeros == []


def test_manifest_matches_builder_if_present():
    if OUT.is_file():
        disk = json.loads(OUT.read_text())
        built = build()
        assert disk["n_hypotheses"] == built["n_hypotheses"]
        assert disk["family_ids"] == built["family_ids"]
        assert disk["v2_freeze_sha256"] == built["v2_freeze_sha256"]
