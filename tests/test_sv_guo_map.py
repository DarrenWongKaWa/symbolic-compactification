"""Frozen Guo P2 → local source members. Evaluation-only; no adjudication."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.grounded_proposer.catalog import catalog_entries  # noqa: E402
from research.representation_invention.guo.catalog import load_guo_catalog  # noqa: E402
from research.representation_invention.labels import FORBIDDEN_GOLD_PATTERNS  # noqa: E402
from research.representation_invention.schema import is_catalog_id  # noqa: E402
from research.scalable_verification.guo_map.build import (  # noqa: E402
    MAP_PATH,
    P2_GLOB,
    RECONSTRUCTION_CAP,
    assert_member_ids,
    build_obligation_map,
    dumps_map,
    frozen_p2_paths,
    load_obligation_map,
    proposer_like_blob,
)

FROZEN_INPUTS = ROOT / "research" / "scalable_verification" / "FROZEN_INPUTS.json"
P2_RUNS = ROOT / "research" / "representation_invention" / "llm" / "runs"
PROPOSER_LIKE_KEYS = ("claimed_type", "reconstruction_rule", "operators")


@pytest.fixture(scope="module")
def catalog():
    return load_guo_catalog()


@pytest.fixture(scope="module")
def built():
    return build_obligation_map()


@pytest.fixture(scope="module")
def committed():
    assert MAP_PATH.is_file(), f"missing {MAP_PATH}"
    return load_obligation_map()


def test_n_hypotheses_positive(committed, built):
    assert committed["n_hypotheses"] > 0
    assert len(committed["hypotheses"]) == committed["n_hypotheses"]
    assert built["n_hypotheses"] == committed["n_hypotheses"]
    n_frozen = 0
    for p in frozen_p2_paths():
        rec = json.loads(p.read_text(encoding="utf-8"))
        n_frozen += len(rec.get("hypotheses") or [])
    assert committed["n_hypotheses"] == n_frozen
    assert committed["evaluation_only"] is True
    assert committed["does_not_adjudicate"] is True
    assert committed["no_llm_calls"] is True
    assert committed["catalog_text_cap_applied"] is False


def test_ids_are_gxxxx(committed):
    assert_member_ids(committed)
    for h in committed["hypotheses"]:
        assert h["member_ids"]
        for gid in h["member_ids"]:
            assert is_catalog_id(gid)
        for m in h["members"]:
            assert is_catalog_id(m["member_id"])
            parent = m.get("parent_sum_gid") or ""
            if parent:
                assert is_catalog_id(parent)
        for mid, parent in (h.get("parent_sum_gid") or {}).items():
            assert is_catalog_id(mid)
            if parent:
                assert is_catalog_id(parent)


def test_no_forbidden_gold_in_proposer_like_fields(committed):
    blob = proposer_like_blob(committed)
    assert blob.strip()
    for pat in FORBIDDEN_GOLD_PATTERNS:
        assert re.search(pat, blob) is None, pat
    assert "use Hermite" not in blob
    for h in committed["hypotheses"]:
        for key in PROPOSER_LIKE_KEYS:
            piece = h.get(key)
            text = piece if isinstance(piece, str) else json.dumps(piece or "", ensure_ascii=True)
            for pat in FORBIDDEN_GOLD_PATTERNS:
                assert re.search(pat, text) is None, (key, pat)
            assert "use Hermite" not in text


def test_local_texts_are_full_node_text_not_catalog_cap(committed, catalog):
    entries = {e["source_node_id"]: e for e in catalog_entries(catalog.index)}
    for h in committed["hypotheses"]:
        for m in h["members"]:
            gid = m["member_id"]
            node = catalog.index.by_gid[gid]
            assert m["in_index"] is True
            assert m["text"] == node.text
            assert m["kind"] == node.kind
            capped = entries[gid]["text"]
            if len(node.text) > 220:
                assert capped.endswith("…")
                assert m["text"] != capped
                assert len(m["text"]) == len(node.text)
                assert len(m["text"]) > 220


def test_parent_sum_gid_walks_to_sum(committed, catalog):
    for h in committed["hypotheses"]:
        for m in h["members"]:
            node = catalog.index.by_gid[m["member_id"]]
            if node.kind == "sum":
                assert m["parent_sum_gid"] == node.gid
            else:
                parent = catalog.index.by_gid[m["parent_sum_gid"]]
                assert parent.kind == "sum"
            assert h["parent_sum_gid"][m["member_id"]] == m["parent_sum_gid"]


def test_reconstruction_truncated_and_claimed_fields_copied(committed):
    by_key = {}
    for p in frozen_p2_paths():
        rec = json.loads(p.read_text(encoding="utf-8"))
        for i, h in enumerate(rec.get("hypotheses") or []):
            by_key[(p.name, i)] = h
    assert by_key
    for mapped in committed["hypotheses"]:
        src = Path(mapped["source_path"]).name
        raw_h = by_key[(src, mapped["index"])]
        assert mapped["claimed_type"] == (raw_h.get("representation_type") or "")
        assert mapped["member_ids"] == [str(x) for x in (raw_h.get("member_ids") or [])]
        assert mapped["reconstruction_rule"] == (raw_h.get("reconstruction_rule") or "")[:RECONSTRUCTION_CAP]
        assert len(mapped["reconstruction_rule"]) <= RECONSTRUCTION_CAP
        kinds = [o.get("kind") for o in mapped["operators"]]
        raw_kinds = [o.get("kind") for o in (raw_h.get("operators") or []) if isinstance(o, dict)]
        assert kinds == raw_kinds


def test_committed_map_matches_builder(committed, built):
    assert dumps_map(built) == dumps_map(committed)


def test_frozen_p2_bytes_unchanged():
    manifest = json.loads(FROZEN_INPUTS.read_text(encoding="utf-8"))
    expected = {
        f["path"]: f["sha256"]
        for f in manifest["files"]
        if f.get("family") == "guo_p2"
    }
    assert expected
    paths = list(P2_RUNS.glob(P2_GLOB))
    assert paths
    for p in paths:
        rel = str(p.relative_to(ROOT))
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        assert got == expected[rel]


def test_map_does_not_adjudicate(committed):
    for h in committed["hypotheses"]:
        assert "verdict" not in h
        assert "previous_verdict" not in h
        assert "n_zero" not in h
        assert "claim_true" not in h
