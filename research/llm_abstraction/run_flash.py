"""deepseek-v4-flash RAW vs SOL. Same prompts. Not multi-model generalization."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.config import FLASH_MODEL
from research.llm_abstraction.run_lib import run_matrix
from research.llm_abstraction.secrets import key_present
from research.llm_abstraction.tasks import load_calibration


def run(*, seeds: int = 3, max_workers: int = 4) -> dict:
    items = load_calibration()
    if not key_present():
        return {"blocked": True}
    recs = run_matrix(
        items, ["A0", "A2"], list(range(seeds)), FLASH_MODEL,
        "flash", max_workers=max_workers,
    )
    return {"n": len(recs), "model": FLASH_MODEL}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
