"""Experimental proposer record schema. Not a product API."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


def write_candidates(
    root: Path,
    proposer_id: str,
    task_id: str,
    candidates: list[dict[str, Any]],
    extra: dict[str, Any] | None = None,
) -> Path:
    d = root / "candidates" / proposer_id / task_id
    d.mkdir(parents=True, exist_ok=True)
    rec = {
        "proposer_id": proposer_id,
        "task_id": task_id,
        "generated_unix": int(time.time()),
        "candidates": candidates,
        "extra": extra or {},
        "claimed_edge_type_is_not_authoritative": True,
        "rationale_is_not_authoritative": True,
    }
    path = d / "candidates.json"
    path.write_text(json.dumps(rec, indent=2) + "\n")
    for i, c in enumerate(candidates):
        (d / f"H{i}.txt").write_text(c["expression"].strip() + "\n")
    return path
