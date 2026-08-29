"""Run DEV waves 1→2→3 without waiting for approval. Resume-safe."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from research.assumption_complete_representation.eval.run_matrix import run_wave
from research.assumption_complete_representation.eval.summarize_dev import main as summarize

HERE = Path(__file__).resolve().parents[1]


def main() -> None:
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    all_out = []
    for wave in (1, 2, 3):
        print(f"=== WAVE {wave} workers={workers} ===", flush=True)
        out = run_wave(wave, seeds=[0, 1, 2, 3, 4], max_workers=workers)
        print(json.dumps({k: out[k] for k in out if k != "results"}, indent=2), flush=True)
        all_out.append({k: out[k] for k in out if k != "results"})
        if out.get("blocked"):
            print("BLOCKED — stop waves", flush=True)
            break
    summary = summarize()
    (HERE / "DEV_MATRIX_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n")
    print("=== SUMMARY ===", flush=True)
    print(json.dumps({
        "n_runs": summary.get("n_runs"),
        "TASK_WEIGHTED": summary.get("TASK_WEIGHTED"),
        "CLUSTER_WEIGHTED": summary.get("CLUSTER_WEIGHTED"),
        "waves": all_out,
    }, indent=2), flush=True)


if __name__ == "__main__":
    main()
