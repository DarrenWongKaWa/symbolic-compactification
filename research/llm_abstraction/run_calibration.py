"""Calibration A–H, conditions A0–A3, 1 seed. Plus frozen baselines."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.baselines_wrap import run_all_frozen
from research.llm_abstraction.config import PRIMARY_MODEL
from research.llm_abstraction.run_lib import RUNS, run_matrix, save_run
from research.llm_abstraction.secrets import key_length, key_present
from research.llm_abstraction.tasks import load_calibration


def run(max_workers: int = 4) -> list[dict]:
    items = load_calibration()
    base_dir = RUNS / "calibration"
    base_dir.mkdir(parents=True, exist_ok=True)
    frozen = []
    for it in items:
        p = base_dir / f"frozen__{it['id']}.json"
        if not p.is_file():
            rec = run_all_frozen(it)
            save_run(p, rec)
        frozen.append(json.loads(p.read_text()) if p.is_file() else {})
    llm = []
    if key_present():
        print(f"calibration LLM key_len={key_length()} items={len(items)}")
        llm = run_matrix(
            items, ["A0", "A1", "A2", "A3"], [0], PRIMARY_MODEL,
            "calibration", packet_cap=10, max_workers=max_workers,
        )
    else:
        print("calibration LLM BLOCKED (no key)")
    print(f"calibration done frozen={len(frozen)} llm={len(llm)}")
    return llm


if __name__ == "__main__":
    run()
