"""DEV ablation. Flagship L0 vs L2: 5 seeds. L1/L3: 3 seeds. Packet-size on two items."""
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
from research.llm_abstraction.tasks import load_calibration, load_frozen_dev, load_local_bench


def run(*, flagship_seeds: int = 5, secondary_seeds: int = 3, max_workers: int = 4) -> dict:
    # Multi-seed on frozen DEV + new local bench. Calibration already ran 1 seed.
    items = load_local_bench() + load_frozen_dev()
    print(f"dev items={len(items)} key_len={key_length() if key_present() else 0}")
    frozen_dir = RUNS / "dev_frozen"
    frozen_dir.mkdir(parents=True, exist_ok=True)
    for it in items:
        p = frozen_dir / f"frozen__{it['id']}.json"
        if not p.is_file():
            save_run(p, run_all_frozen(it))
    if not key_present():
        print("dev LLM BLOCKED")
        return {"blocked": True, "n_items": len(items)}
    l0l2 = run_matrix(
        items, ["A0", "A2"], list(range(flagship_seeds)), PRIMARY_MODEL,
        "dev", max_workers=max_workers,
    )
    l1l3 = run_matrix(
        items, ["A1", "A3"], list(range(secondary_seeds)), PRIMARY_MODEL,
        "dev", max_workers=max_workers,
    )
    # packet-size ablation: two calibration items, A2, seed 0
    calib = {it["id"]: it for it in load_calibration()}
    pk_items = [calib[k] for k in ("CAL-B-lgg", "CAL-C-deriv") if k in calib]
    pk_runs = []
    for cap in (5, 10, 20, 24):
        pk_runs.extend(run_matrix(
            pk_items, ["A2"], [0], PRIMARY_MODEL, "packet_size",
            packet_cap=cap, max_workers=max_workers,
        ))
    return {
        "n_items": len(items),
        "n_l0l2": len(l0l2),
        "n_l1l3": len(l1l3),
        "n_packet": len(pk_runs),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
