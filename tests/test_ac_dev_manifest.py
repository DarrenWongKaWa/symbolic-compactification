"""DEV slice freeze: 14 tasks, no Guo, TEST not frozen."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

MAN = ROOT / "research" / "assumption_complete_representation" / "DEV_MANIFEST.json"
ADM = ROOT / "research" / "assumption_complete_representation" / "ADMITTED.json"


def test_dev_manifest_fourteen_no_guo_not_test():
    man = json.loads(MAN.read_text())
    adm = json.loads(ADM.read_text())
    ids = [t["case_id"] for t in man["tasks"]]
    assert man["n"] == 14
    assert ids == adm["DEV_proposal"]
    assert man["guo_in_dev_or_test"] is False
    assert man["not_test_freeze"] is True
    assert all("guo" not in i.lower() for i in ids)
    assert man["tag_counts"]["TRIVIAL"] == 0
    assert sum(man["tag_counts"].values()) == 14
