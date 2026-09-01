#!/usr/bin/env python3
"""Gold control (after generation) and injected negatives. Not proposer success."""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from proposers.interface import write_candidates  # noqa: E402


def mutate(expr: str, kind: str) -> str:
    if kind == "sign_flip":
        return f"-({expr})"
    if kind == "times_two":
        return f"2*({expr})"
    if kind == "zero":
        return "0"
    if kind == "drop_term":
        return f"({expr}) + 1"
    raise ValueError(kind)


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    for task in frozen["tasks"]:
        tid = task["task_id"]
        current = (ROOT / "contexts" / tid / "current.txt").read_text().strip()
        target = (ROOT / "hidden" / "targets" / task["hidden_target_file"]).read_text().strip()
        gold = []
        if task["role"] == "recovery":
            gold = [
                {
                    "candidate_id": "gold-hidden-target",
                    "expression": target,
                    "claimed_edge_type": task["expected_claim_type"],
                    "rationale": "positive control; inserted after generation; not proposer success",
                    "is_gold_control": True,
                }
            ]
        write_candidates(ROOT, "gold_control", tid, gold, extra={"inserted_after_generation": True})
        negs = [
            {
                "candidate_id": f"neg-{kind}",
                "expression": mutate(current, kind),
                "claimed_edge_type": "ALGEBRAIC_EQUIVALENCE",
                "rationale": kind,
                "injected_negative": True,
                "kind": kind,
            }
            for kind in ("sign_flip", "times_two", "zero", "drop_term")
        ]
        write_candidates(ROOT, "injected_negative", tid, negs)
        print(tid, "gold", len(gold), "neg", len(negs))


if __name__ == "__main__":
    main()
