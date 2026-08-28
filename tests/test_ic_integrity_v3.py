"""Track V3 freeze integrity. Do not rewrite historical runs."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.freeze_v3 import OUT, build  # noqa: E402

EXPECTED_SHA = "e1fc6df85b0d293f3251ec87c1827409f402c01752a73251be8899f5b00c41db"


def test_frozen_inputs_sha_and_n():
    assert OUT.is_file()
    disk = json.loads(OUT.read_text())
    sha = hashlib.sha256(OUT.read_bytes()).hexdigest()
    assert sha == EXPECTED_SHA
    assert disk["n_hypotheses"] == 7
    assert disk["no_llm_calls"] is True
    assert disk["parent_track_v2_close"] == "fe53ebc"
    built = build()
    assert built["family_ids"] == disk["family_ids"]
    assert all(h["v2_family_verdict"] == "FAMILY_UNKNOWN" for h in disk["hypotheses"])
