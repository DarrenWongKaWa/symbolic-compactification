"""Held-out TEST LLM. GENERAL_FINAL=P0, also P2. No retune. No Guo."""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.eval.ac_compile import COMPILER_VERSION
from research.assumption_complete_representation.eval.ac_parser import parse_model_output
from research.assumption_complete_representation.eval.ac_prompts import messages_for
from research.assumption_complete_representation.eval.ac_score import score_run
from research.assumption_complete_representation.eval.run_matrix import (
    already_done,
    atomic_write,
    hashlib_sha,
)
from research.assumption_complete_representation.eval.test_packs import (
    CORE,
    HIDDEN,
    PUBLIC_PACKS,
)
from research.llm_abstraction.client import chat_complete
from research.llm_abstraction.config import CONFIG_ID, PROTOCOL_ID, ProposerConfig
from research.llm_abstraction.secrets import key_present, sanitize

HERE = Path(__file__).resolve().parents[1]
RUNS = HERE / "runs" / "test_matrix"
SOL = HERE / "packs" / "test" / "sol"


def run_path(task_id, condition, seed, model):
    return RUNS / f"{task_id}__{condition}__{model}__s{seed}.json"


def run_one(task_id, condition, seed, model="deepseek-v4-pro"):
    pack = PUBLIC_PACKS[task_id]
    hidden = HIDDEN[task_id]
    basic = None
    sol_text = None
    sol_hash = None
    bp = SOL / f"{task_id}.basic.json"
    sp = SOL / f"{task_id}.json"
    if condition == "P1" and bp.is_file():
        basic = json.loads(bp.read_text())
    if condition == "P2" and sp.is_file():
        sol_obj = json.loads(sp.read_text())
        sol_text = sol_obj.get("text") or ""
        sol_hash = hashlib_sha(sp.read_bytes())
    msgs, hashes = messages_for(pack, condition, basic_summary=basic, sol_text=sol_text)
    cfg = ProposerConfig(model=model, condition=condition)
    t0 = time.time()
    rec = chat_complete(msgs, cfg)
    latency = round(time.time() - t0, 3)
    parsed = parse_model_output(rec.get("content") or "")
    if rec.get("blocked"):
        parsed["parse_status"] = "FAILED_OPERATIONAL"
        parsed["parse_error"] = rec.get("error") or "BLOCKED"
    scored = score_run(parsed, pack, hidden)
    usage = rec.get("usage") or {}
    out = {
        "task_id": task_id,
        "public_id": pack.get("public_id"),
        "structural_cluster_id": pack.get("cluster_id"),
        "stratum": "CORE_COMPARABLE",
        "condition": condition,
        "seed": seed,
        "model": rec.get("model") or model,
        "config_id": rec.get("config_id") or CONFIG_ID,
        "protocol_id": PROTOCOL_ID,
        "prompt_sha256": hashes["prompt_sha256"],
        "input_sha256": hashes["input_sha256"],
        "sol_packet_sha256": sol_hash,
        "latency_s": rec.get("latency_s") if rec.get("latency_s") is not None else latency,
        "usage": usage,
        "parse_status": parsed.get("parse_status"),
        "n_hypotheses": scored.get("n_hypotheses"),
        "raw_response": rec.get("content") or "",
        "parsed": {k: parsed[k] for k in parsed if k != "raw_obj"},
        "eval": scored,
        "blocked": rec.get("blocked"),
        "error": rec.get("error"),
        "compiler_version": COMPILER_VERSION,
        "guo": False,
        "split": "TEST",
        "GENERAL_FINAL": "P0",
    }
    return sanitize(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--conditions", default="P0,P2")
    p.add_argument("--seeds", default="0,1,2,3,4")
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--model", default="deepseek-v4-pro")
    args = p.parse_args()
    if not key_present():
        print(json.dumps({"blocked": True, "error": "NO_API_KEY"}))
        return
    conds = [c.strip() for c in args.conditions.split(",") if c.strip()]
    seeds = [int(x) for x in args.seeds.split(",") if x.strip() != ""]
    jobs = []
    for tid in CORE:
        for c in conds:
            for s in seeds:
                path = run_path(tid, c, s, args.model)
                if already_done(path):
                    continue
                jobs.append((tid, c, s, path))
    results = []

    def _do(item):
        tid, c, s, path = item
        rec = run_one(tid, c, s, args.model)
        atomic_write(path, rec)
        return {"task": tid, "condition": c, "seed": s, "parse": rec.get("parse_status"),
                "op": (rec.get("eval") or {}).get("any_operational_success"),
                "blocked": rec.get("blocked")}

    RUNS.mkdir(parents=True, exist_ok=True)
    if jobs:
        with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
            futs = [ex.submit(_do, j) for j in jobs]
            for fut in as_completed(futs):
                results.append(fut.result())
    print(json.dumps({"n_jobs": len(jobs), "n_ran": len(results),
                      "blocked": sum(1 for r in results if r.get("blocked")),
                      "op": sum(1 for r in results if r.get("op")),
                      "split": "TEST", "guo": False}, indent=2))


if __name__ == "__main__":
    main()
