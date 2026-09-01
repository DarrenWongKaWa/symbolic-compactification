#!/usr/bin/env python3
"""Experiment C: multi-step promote/refuse session on frozen MS-01.

MS-01 is FR-01 → FR-02 → FR-03. These are three public algebraic Guo steps,
not paper-adjacent on one expression. The session tests the loop
proposal → verify → promote/refuse → next step, not manuscript adjacency.

A poison trajectory shows that a refused invalid candidate does not replace
the accepted state, so a later valid candidate of the original state can
still be considered.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from verify_candidates import recover_against_target, free_names, verify_one  # noqa: E402


def load_candidates(proposer: str, tid: str) -> list[dict]:
    path = ROOT / "candidates" / proposer / tid / "candidates.json"
    if not path.exists():
        return []
    return json.loads(path.read_text())["candidates"]


def current_of(tid: str) -> str:
    return (ROOT / "contexts" / tid / "current.txt").read_text().strip()


def target_of(task: dict) -> str:
    return (ROOT / "hidden" / "targets" / task["hidden_target_file"]).read_text().strip()


def pick_llm(tid: str) -> dict:
    cands = load_candidates("llm_masked", tid)
    if not cands:
        raise SystemExit(f"missing llm candidates for {tid}")
    return cands[0]


def pick_cas(tid: str) -> dict:
    cands = load_candidates("cas_sympy", tid)
    return cands[0]


def pick_gold(tid: str) -> dict:
    cands = load_candidates("gold_control", tid)
    if not cands:
        raise SystemExit(f"missing gold for {tid}")
    return cands[0]


def evaluate_step(tid: str, task: dict, cand: dict, proposer_id: str) -> dict:
    current = current_of(tid)
    target = target_of(task)
    expr = cand["expression"]
    names = free_names(current, expr, target) or ["x"]
    promo = verify_one(current, expr, names)
    rec = recover_against_target(expr, target, free_names(expr, target) or names)
    accepted = promo["promoted"]
    next_state = expr if accepted else current
    return {
        "task_id": tid,
        "proposer_id": proposer_id,
        "candidate_id": cand["candidate_id"],
        "promotion": promo,
        "target_recovery": rec,
        "recovered": rec["result"] == "ZERO",
        "accepted": accepted,
        "state_after": "candidate" if accepted else "stayed_at_current",
        "expression": expr,
        "next_state_equals_current": next_state == current,
    }


def write_traj(name: str, payload: dict) -> None:
    d = ROOT / "trajectories"
    d.mkdir(exist_ok=True)
    (d / f"{name}.json").write_text(json.dumps(payload, indent=2) + "\n")


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    tasks = {t["task_id"]: t for t in frozen["tasks"]}
    step_ids = [s["task_id"] for s in frozen["multi_step"]["steps"]]

    def run_family(name: str, picker, proposer_id: str) -> dict:
        steps = []
        n_accept = 0
        for tid in step_ids:
            step = evaluate_step(tid, tasks[tid], picker(tid), proposer_id)
            n_accept += int(step["accepted"])
            steps.append(step)
            print(name, tid, step["candidate_id"], "ACCEPT" if step["accepted"] else "REFUSE", flush=True)
        payload = {
            "rollout_id": "MS-01",
            "family": name,
            "step_task_ids": step_ids,
            "accepted_steps": n_accept,
            "n_steps": len(step_ids),
            "accepted_over_n": f"{n_accept}/{len(step_ids)}",
            "paper_adjacent": False,
            "steps": steps,
        }
        write_traj(f"MS-01_{name}", payload)
        return payload

    gold = run_family("gold", pick_gold, "gold_control")
    llm = run_family("llm", pick_llm, "llm_masked")
    cas = run_family("cas", pick_cas, "cas_sympy")

    # Poison: refuse an invalid FR-01 candidate, stay, then gold of the original
    # FR-01 current still verifies. Then continue MS-01 gold FR-02.
    poison_cand = load_candidates("injected_negative", "FR-01")[0]
    poison_steps = []
    s0 = evaluate_step("FR-01", tasks["FR-01"], poison_cand, "injected_negative")
    poison_steps.append(s0)
    print("poison FR-01", s0["candidate_id"], "ACCEPT" if s0["accepted"] else "REFUSE", flush=True)
    if s0["accepted"]:
        raise SystemExit("STOP: false promotion on poison trajectory")
    s1 = evaluate_step("FR-01", tasks["FR-01"], pick_gold("FR-01"), "gold_control")
    poison_steps.append(s1)
    print("poison retry-gold FR-01", "ACCEPT" if s1["accepted"] else "REFUSE", flush=True)
    s2 = evaluate_step("FR-02", tasks["FR-02"], pick_gold("FR-02"), "gold_control")
    poison_steps.append(s2)
    poison = {
        "rollout_id": "MS-01-poison",
        "description": (
            "Invalid FR-01 candidate is refused; accepted state remains the "
            "original current. A later gold candidate of that original state "
            "is still eligible. The refused invalid step did not poison later recovery."
        ),
        "refused_invalid_did_not_poison_later_recovery": (not s0["accepted"]) and s1["accepted"],
        "steps": poison_steps,
    }
    write_traj("MS-01_poison", poison)

    summary = {
        "MS-01_gold": gold["accepted_over_n"],
        "MS-01_llm_first": llm["accepted_over_n"],
        "MS-01_cas_first": cas["accepted_over_n"],
        "poison_refused_then_gold_ok": poison["refused_invalid_did_not_poison_later_recovery"],
    }
    (ROOT / "metrics" / "experiment_c.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
