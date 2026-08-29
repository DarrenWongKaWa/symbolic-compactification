"""DEV LLM matrix. Atomic run files. Resume-safe. No TEST. No Guo."""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.eval.ac_parser import parse_model_output
from research.assumption_complete_representation.eval.ac_prompts import messages_for
from research.assumption_complete_representation.eval.ac_score import score_run
from research.assumption_complete_representation.eval.pack_data import (
    CLUSTER_OF,
    CORE,
    HIDDEN,
    P4_ELIGIBLE,
    PUBLIC_PACKS,
)
from research.llm_abstraction.client import chat_complete
from research.llm_abstraction.config import CONFIG_ID, PROTOCOL_ID, ProposerConfig
from research.llm_abstraction.secrets import key_present, sanitize

HERE = Path(__file__).resolve().parents[1]
RUNS = HERE / "runs" / "dev_matrix"
SOL = HERE / "packs" / "dev" / "sol"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def run_path(task_id: str, condition: str, seed: int, model: str) -> Path:
    return RUNS / f"{task_id}__{condition}__{model}__s{seed}.json"


def atomic_write(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(sanitize(obj), indent=2, default=str))
    tmp.replace(path)


def already_done(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        rec = _load_json(path)
    except Exception:
        return False
    if rec.get("blocked"):
        return False
    return rec.get("parse_status") in {
        "OK", "PARSE_FAILURE", "ABSTAIN", "FAILED_OPERATIONAL",
    }


def jobs_for(wave: int, seeds: list[int]) -> list[tuple[str, str, int]]:
    jobs = []
    if wave == 1:
        conds = ["P0"]
        tasks = CORE
    elif wave == 2:
        conds = ["P1", "P2"]
        tasks = CORE
    elif wave == 3:
        # P3 on all CORE; P4 only predeclared unlabeled families
        for cid in CORE:
            for s in seeds:
                jobs.append((cid, "P3", s))
        for cid in P4_ELIGIBLE:
            for s in seeds:
                jobs.append((cid, "P4", s))
        return jobs
    else:
        raise ValueError(f"unknown wave {wave}")
    for cid in tasks:
        for c in conds:
            for s in seeds:
                jobs.append((cid, c, s))
    return jobs


def run_one(
    task_id: str,
    condition: str,
    seed: int,
    model: str = "deepseek-v4-pro",
) -> dict[str, Any]:
    pack = PUBLIC_PACKS[task_id]
    hidden = HIDDEN[task_id]
    basic = None
    sol_text = None
    sol_hash = None
    bp = SOL / f"{task_id}.basic.json"
    sp = SOL / f"{task_id}.json"
    if condition == "P1" and bp.is_file():
        basic = _load_json(bp)
    if condition == "P2" and sp.is_file():
        sol_obj = _load_json(sp)
        sol_text = sol_obj.get("text") or ""
        sol_hash = hashlib_sha(sp.read_bytes())
    msgs, hashes = messages_for(
        pack, condition, basic_summary=basic, sol_text=sol_text,
    )
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
        "structural_cluster_id": CLUSTER_OF.get(task_id),
        "stratum": "CORE_COMPARABLE",
        "condition": condition,
        "seed": seed,
        "model": rec.get("model") or model,
        "config_id": rec.get("config_id") or CONFIG_ID,
        "protocol_id": PROTOCOL_ID,
        "prompt_sha256": hashes["prompt_sha256"],
        "input_sha256": hashes["input_sha256"],
        "system_sha256": hashes["system_sha256"],
        "user_sha256": hashes["user_sha256"],
        "sol_packet_sha256": sol_hash,
        "assumption_contract_sha256": hashlib_sha(
            json.dumps(pack.get("assumptions") or [], sort_keys=True).encode()
        ),
        "source_catalog_sha256": hashlib_sha(
            json.dumps(pack.get("catalog") or [], sort_keys=True).encode()
        ),
        "latency_s": rec.get("latency_s") if rec.get("latency_s") is not None else latency,
        "usage": usage,
        "reasoning_tokens": usage.get("reasoning_tokens"),
        "output_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "request_id": rec.get("request_id"),
        "reasoning_len": rec.get("reasoning_len"),
        "reasoning_sha": rec.get("reasoning_sha"),
        "parse_status": parsed.get("parse_status"),
        "parse_error": parsed.get("parse_error"),
        "format_wrap": parsed.get("format_wrap"),
        "n_hypotheses": scored.get("n_hypotheses"),
        "raw_response": rec.get("content") or "",
        "parsed": {k: parsed[k] for k in parsed if k != "raw_obj"},
        "eval": scored,
        "blocked": rec.get("blocked"),
        "error": rec.get("error"),
        "guo": False,
        "split": "DEV",
    }
    return sanitize(out)


def hashlib_sha(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


def run_wave(
    wave: int,
    seeds: Optional[list[int]] = None,
    max_workers: int = 4,
    model: str = "deepseek-v4-pro",
) -> dict:
    seeds = seeds or [0, 1, 2, 3, 4]
    RUNS.mkdir(parents=True, exist_ok=True)
    if not key_present():
        return {"blocked": True, "error": "NO_API_KEY", "wave": wave}
    jobs = jobs_for(wave, seeds)
    pending = []
    skipped = 0
    for cid, cond, seed in jobs:
        path = run_path(cid, cond, seed, model)
        if already_done(path):
            skipped += 1
            continue
        pending.append((cid, cond, seed, path))
    results = []
    errors = []

    def _do(item):
        cid, cond, seed, path = item
        try:
            rec = run_one(cid, cond, seed, model)
            atomic_write(path, rec)
            return {"ok": True, "path": str(path), "parse": rec.get("parse_status"),
                    "task": cid, "condition": cond, "seed": seed,
                    "blocked": rec.get("blocked")}
        except Exception as exc:
            traceback.print_exc()
            fail = {
                "task_id": cid, "condition": cond, "seed": seed,
                "parse_status": "FAILED_OPERATIONAL",
                "error": f"{type(exc).__name__}",
                "blocked": True,
                "guo": False,
            }
            atomic_write(path, sanitize(fail))
            return {"ok": False, "path": str(path), "error": type(exc).__name__,
                    "task": cid, "condition": cond, "seed": seed}

    if pending:
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = [ex.submit(_do, p) for p in pending]
            for fut in as_completed(futs):
                r = fut.result()
                results.append(r)
                if not r.get("ok"):
                    errors.append(r)
    return {
        "wave": wave,
        "n_jobs": len(jobs),
        "n_pending": len(pending),
        "n_skipped": skipped,
        "n_ran": len(results),
        "n_errors": len(errors),
        "results": results,
        "model": model,
        "guo": False,
        "split": "DEV",
    }


def main(argv: Optional[list[str]] = None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--wave", type=int, required=True, choices=[1, 2, 3])
    p.add_argument("--seeds", default="0,1,2,3,4")
    p.add_argument("--max-workers", type=int, default=4)
    p.add_argument("--model", default="deepseek-v4-pro")
    args = p.parse_args(argv)
    seeds = [int(x) for x in args.seeds.split(",") if x.strip() != ""]
    out = run_wave(args.wave, seeds=seeds, max_workers=args.max_workers, model=args.model)
    print(json.dumps({k: out[k] for k in out if k != "results"} | {
        "results_n": len(out.get("results") or []),
        "blocked_n": sum(1 for r in (out.get("results") or []) if r.get("blocked")),
        "parse_ok_n": sum(1 for r in (out.get("results") or []) if r.get("parse") == "OK"),
    }, indent=2))


if __name__ == "__main__":
    main()
