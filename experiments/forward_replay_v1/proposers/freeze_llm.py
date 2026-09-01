#!/usr/bin/env python3
"""Materialize frozen llm_masked candidates from the isolated-subagent dump.

The dump was generated from contexts/<task>/ only. This script does not
call a model; it writes immutable per-task candidates.json files.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from proposers.interface import write_candidates  # noqa: E402


def main() -> None:
    raw_path = ROOT / "candidates" / "llm_masked" / "_raw.json"
    raw = json.loads(raw_path.read_text())
    for tid, cands in raw["tasks"].items():
        recs = [
            {
                "candidate_id": c["candidate_id"],
                "expression": c["expression"],
                "claimed_edge_type": "ALGEBRAIC_EQUIVALENCE",
                "rationale": c.get("rationale"),
            }
            for c in cands
        ]
        write_candidates(
            ROOT,
            "llm_masked",
            tid,
            recs,
            extra={
                "model": raw.get("model"),
                "subagent_id": raw.get("subagent_id"),
                "isolation": raw.get("isolation"),
                "k": len(recs),
                "source": str(raw_path.relative_to(ROOT)),
            },
        )
        print(tid, len(recs))


if __name__ == "__main__":
    main()
