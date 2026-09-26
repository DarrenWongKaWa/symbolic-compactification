#!/usr/bin/env python3
"""Score results/arm_*.json against truth.json (step id -> claim is valid)."""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    truth = json.loads((HERE / "truth.json").read_text())
    invalid = {s for s, ok in truth.items() if not ok}
    print("| Arm | Correct | Planted errors caught | False alarms | Steps computed | Steps decided by the tool |")
    print("|---|---:|---:|---:|---:|---:|")
    for path in sorted((HERE / "results").glob("arm_*.json")):
        rows = {r["id"]: r for r in json.loads(path.read_text())}
        says = {s: rows.get(s, {}).get("verdict") == "VALID" for s in truth}
        caught = sum(not says[s] for s in invalid)
        alarms = sum(not says[s] for s in truth if s not in invalid)
        correct = sum(says[s] == truth[s] for s in truth)
        computed = sum(bool(rows.get(s, {}).get("computed")) for s in truth)
        decided = sum(str(rows.get(s, {}).get("tool_status") or "").startswith(("ZERO", "NONZERO", "CERTIFIED"))
                      for s in truth)
        print(f"| {path.stem[4:]} | {correct}/{len(truth)} | {caught}/{len(invalid)} | "
              f"{alarms}/{len(truth) - len(invalid)} | {computed}/{len(truth)} | {decided} |")


if __name__ == "__main__":
    main()
