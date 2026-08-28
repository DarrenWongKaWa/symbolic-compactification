"""V4 freeze is exactly the seven V3 families."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.freeze_v3 import build as build_v3  # noqa: E402
from research.polygamma_confluence.freeze_v4 import OUT, build  # noqa: E402


def test_v4_freeze_is_v3_families():
    blob = build()
    v3 = build_v3()
    assert blob["n_hypotheses"] == 7
    assert blob["no_llm_calls"] is True
    assert blob["family_ids"] == [h["family_id"] for h in v3["hypotheses"]]
    if OUT.is_file():
        import json
        disk = json.loads(OUT.read_text())
        assert disk["family_ids"] == blob["family_ids"]
