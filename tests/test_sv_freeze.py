"""Frozen Track-V input manifest. Historical runs are not rewritten."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.freeze_inputs import OUT, build


def test_freeze_covers_guo_p1_p2_and_newton():
    blob = build()
    families = {f["family"] for f in blob["files"]}
    assert "guo_p1" in families
    assert "guo_p2" in families
    assert "newton" in families
    assert "hermite" in families
    assert "special_fn" in families
    assert blob["n_hypotheses"] >= 20
    assert blob["no_llm_calls"] is True


def test_hashes_match_bytes_on_disk():
    blob = build()
    for rec in blob["files"][:8]:
        p = ROOT / rec["path"]
        got = hashlib.sha256(p.read_bytes()).hexdigest()
        assert got == rec["sha256"]


def test_manifest_roundtrip_if_written(tmp_path):
    blob = build()
    p = tmp_path / "FROZEN_INPUTS.json"
    p.write_text(json.dumps(blob))
    loaded = json.loads(p.read_text())
    assert loaded["n_files"] == blob["n_files"]
