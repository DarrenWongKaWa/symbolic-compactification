#!/usr/bin/env python3
"""Aggregate Experiment A/B metrics from frozen verification records."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
K_DEFAULT = 4


def load_rows() -> list[dict]:
    return json.loads((ROOT / "verification" / "records.json").read_text())


def recovery_tasks(frozen: dict) -> list[str]:
    return [t["task_id"] for t in frozen["tasks"] if t["role"] == "recovery"]


def target_recovery_at_k(rows: list[dict], proposer: str, tasks: list[str], k: int) -> dict:
    by_task: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r["proposer_id"] != proposer:
            continue
        if r["task_id"] not in tasks:
            continue
        if r.get("is_gold_control"):
            continue
        by_task[r["task_id"]].append(r)
    hits = []
    per_task = {}
    for tid in tasks:
        cands = by_task.get(tid, [])
        recovered = any(c.get("recovered") for c in cands[:k])
        per_task[tid] = {
            "n_candidates": len(cands),
            "recovered": recovered,
            "k_used": min(k, len(cands)),
            "recovered_ids": [c["candidate_id"] for c in cands[:k] if c.get("recovered")],
        }
        hits.append(int(recovered))
    n = len(tasks)
    return {
        "proposer_id": proposer,
        "k": k,
        "n_tasks": n,
        "n_recovered": sum(hits),
        "target_recovery_at_k": (sum(hits) / n) if n else None,
        "per_task": per_task,
    }


def status_hist(rows: list[dict]) -> dict:
    c = Counter(r["promotion"]["result"] for r in rows)
    return dict(c)


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    rows = load_rows()
    rec_tasks = recovery_tasks(frozen)
    proposers = sorted({r["proposer_id"] for r in rows})

    gold_rows = [r for r in rows if r["proposer_id"] == "gold_control" and r.get("is_gold_control")]
    gold_rec = sum(1 for r in gold_rows if r.get("recovered"))
    gold_promo = sum(1 for r in gold_rows if r["promotion"]["promoted"])
    gold_refused = [r for r in gold_rows if not r["promotion"]["promoted"]]

    injected = [r for r in rows if r["injected_negative"] or r["proposer_id"] == "injected_negative"]
    false_promo = [r for r in injected if r["promotion"]["promoted"]]
    inj_hist = Counter(r["promotion"]["result"] for r in injected)

    nc = [r for r in rows if r["task_id"] == "FR-NC-01"]
    nc_zero_cands = [
        r
        for r in nc
        if r["expression"].strip() in {"0", "0\n"} or r["candidate_id"] == "neg-zero"
    ]
    nc_zero_promo = [r for r in nc_zero_cands if r["promotion"]["promoted"]]

    recovery_at_k = {}
    for p in proposers:
        if p in {"gold_control", "injected_negative"}:
            continue
        k = 2 if p == "gplearn" else K_DEFAULT
        recovery_at_k[p] = target_recovery_at_k(rows, p, rec_tasks, k)

    gplearn_raw_only = target_recovery_at_k(
        [r for r in rows if not (r["proposer_id"] == "gplearn" and r["candidate_id"] == "gplearn-identity")],
        "gplearn",
        rec_tasks,
        1,
    )
    gplearn_raw_only["note"] = (
        "gplearn-identity copies E_t and is not SR discovery. This row is "
        "gplearn-raw only."
    )

    subst_tasks = ["FR-06", "FR-08"]
    subst = [
        {
            "task_id": r["task_id"],
            "proposer_id": r["proposer_id"],
            "candidate_id": r["candidate_id"],
            "promoted_vs_current": r["promotion"]["promoted"],
            "promotion_result": r["promotion"]["result"],
            "recovered_vs_target": r.get("recovered"),
        }
        for r in gold_rows
        if r["task_id"] in subst_tasks
    ]

    metrics = {
        "n_records": len(rows),
        "status_histogram_promotion": status_hist(rows),
        "gold_control": {
            "n": len(gold_rows),
            "target_recovery": gold_rec,
            "promoted_vs_current": gold_promo,
            "refused_vs_current": [
                {
                    "task_id": r["task_id"],
                    "result": r["promotion"]["result"],
                    "recovered": r.get("recovered"),
                }
                for r in gold_refused
            ],
            "note": (
                "Gold is a pipeline positive control, not proposer success. "
                "Promotion is Mode A ZERO(current, H). Substitution-conditioned "
                "gold (FR-06, FR-08) is expected to recover the hidden target "
                "while remaining NONZERO vs current unless identities are compiled."
            ),
        },
        "experiment_b_injected_negatives": {
            "n": len(injected),
            "false_promotions": len(false_promo),
            "false_promotion_rate": (len(false_promo) / len(injected)) if injected else None,
            "false_promotion_ids": [
                {
                    "task_id": r["task_id"],
                    "candidate_id": r["candidate_id"],
                    "result": r["promotion"]["result"],
                }
                for r in false_promo
            ],
            "status_histogram": dict(inj_hist),
            "nonzero_count": inj_hist.get("NONZERO", 0),
            "unknown_count": inj_hist.get("UNKNOWN", 0),
            "parse_failure_count": inj_hist.get("PARSE_FAILURE", 0),
            "compile_failure_count": inj_hist.get("COMPILE_FAILURE", 0),
        },
        "negative_control_FR-NC-01": {
            "n": len(nc),
            "zero_collapse_candidates": len(nc_zero_cands),
            "zero_collapse_promoted": len(nc_zero_promo),
            "note": (
                "A remainder collapse to 0 must not promote. Algebraic rewrites "
                "that remain equivalent to the current remainder may still "
                "promote as stay-put; that is not remainder certification."
            ),
        },
        "target_recovery_at_k": recovery_at_k,
        "gplearn_raw_only_target_recovery_at_1": gplearn_raw_only,
        "substitution_gold_product_gap": subst,
        "proposers": proposers,
        "recovery_tasks": rec_tasks,
    }
    out = ROOT / "metrics" / "experiment_ab.json"
    out.write_text(json.dumps(metrics, indent=2) + "\n")

    lines = [
        "# Experiment A/B metrics",
        "",
        f"Records: {len(rows)}",
        "",
        "## Gold control (not proposer success)",
        "",
        f"- target recovery: {gold_rec}/{len(gold_rows)}",
        f"- promoted vs current: {gold_promo}/{len(gold_rows)}",
        "",
        "## TargetRecovery@K (gold excluded)",
        "",
        "| proposer | K | recovered tasks | rate |",
        "|---|---:|---:|---:|",
    ]
    for p, rec in recovery_at_k.items():
        rate = rec["target_recovery_at_k"]
        rate_s = "" if rate is None else f"{rate:.3f}"
        lines.append(f"| {p} | {rec['k']} | {rec['n_recovered']}/{rec['n_tasks']} | {rate_s} |")
    gr = gplearn_raw_only
    gr_rate = "" if gr["target_recovery_at_k"] is None else f"{gr['target_recovery_at_k']:.3f}"
    lines.append(
        f"| gplearn-raw only | {gr['k']} | {gr['n_recovered']}/{gr['n_tasks']} | {gr_rate} |"
    )
    lines += [
        "",
        "## Experiment B — injected negatives",
        "",
        f"- n = {len(injected)}",
        f"- false promotions = {len(false_promo)}",
        f"- false promotion rate = {metrics['experiment_b_injected_negatives']['false_promotion_rate']}",
        f"- status histogram = {dict(inj_hist)}",
        "",
        "## Promotion status histogram (all candidates)",
        "",
        f"`{metrics['status_histogram_promotion']}`",
        "",
        "## FR-NC-01 remainder collapse to 0",
        "",
        f"- zero-collapse candidates: {len(nc_zero_cands)}",
        f"- promoted: {len(nc_zero_promo)}",
        "",
    ]
    (ROOT / "tables" / "experiment_ab.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({k: metrics[k] for k in ("n_records", "gold_control", "experiment_b_injected_negatives") if k in metrics}, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
