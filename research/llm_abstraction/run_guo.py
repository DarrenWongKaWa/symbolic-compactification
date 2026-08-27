"""Guo DEV-only. G0–G3. Do not leak gold names into prompts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.config import PRIMARY_MODEL
from research.llm_abstraction.leak import gold_name_hits
from research.llm_abstraction.packetizer import packets_for_item
from research.llm_abstraction.run_lib import run_matrix
from research.llm_abstraction.secrets import key_present
from research.llm_abstraction.tasks import load_guo_item, public_item


def run(*, seeds: int = 3, max_workers: int = 2) -> dict:
    item = load_guo_item()
    pub = public_item(item)
    assert "Phi_Gamma" not in json.dumps(pub)
    assert "Hermite" not in json.dumps(pub)
    packets, summary, text = packets_for_item(
        item, cap=10, backends="relations", timeout_s=180.0,
    )
    hits = gold_name_hits(text, item)
    if hits:
        raise RuntimeError(f"Guo packet leak: {hits}")
    if not key_present():
        return {"blocked": True, "n_packets": len(packets), "summary": summary}
    recs = run_matrix(
        [item], ["A0", "A1", "A2", "A3"], list(range(seeds)), PRIMARY_MODEL,
        "guo", packet_cap=10, max_workers=max_workers, sol_timeout_s=180.0,
    )
    return {"n": len(recs), "n_packets": len(packets), "ops": summary.get("count_ops")}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
