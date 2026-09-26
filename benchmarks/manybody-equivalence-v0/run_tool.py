#!/usr/bin/env python3
"""Tool arm: run each item's `symbolic-compactification manybody` command.

Mapping of tool output to an answer:
  CERTIFIED_BY_RULE or verdict ZERO           -> TRUE
  NONZERO                                     -> FALSE
  ASSUMPTION_REQUIRED, CONVERGENCE_FACTOR_REQUIRED -> CONDITIONAL
  anything else (UNKNOWN, NUMERICAL_SUPPORT)  -> ABSTAIN
The encoding of each claim (the CLI arguments in items.yaml) is written by
hand here; in real use an agent writes it, and its fidelity is not tested.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent


def answer(payload: dict) -> str:
    status = payload.get("status") or payload.get("verdict")
    reasons = payload.get("reasons") or []
    if status in ("CERTIFIED_BY_RULE", "ZERO"):
        return "TRUE"
    if status == "NONZERO":
        return "FALSE"
    if status == "ASSUMPTION_REQUIRED" or "CONVERGENCE_FACTOR_REQUIRED" in reasons:
        return "CONDITIONAL"
    return "ABSTAIN"


def main() -> None:
    items = yaml.safe_load((HERE / "items.yaml").read_text())["items"]
    rows = []
    for item in items:
        start = time.monotonic()
        done = subprocess.run(["symbolic-compactification", "manybody", *item["tool"]],
                              capture_output=True, text=True, timeout=600)
        payload = json.loads(done.stdout)
        rows.append({"id": item["id"], "answer": answer(payload),
                     "status": payload.get("status") or payload.get("verdict"),
                     "reasons": payload.get("reasons", []),
                     "numeric": payload.get("numeric"),
                     "seconds": round(time.monotonic() - start, 2)})
        print(f"{item['id']:3s} {rows[-1]['answer']:12s} {rows[-1]['status']} {rows[-1]['reasons']}")
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "arm_tool.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
