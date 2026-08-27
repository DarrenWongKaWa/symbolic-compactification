"""Shared experiment runner. Resume-safe. Sanitizes secrets."""
from __future__ import annotations

import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.llm_abstraction.config import CONFIG_ID, PROTOCOL_ID, ProposerConfig
from research.llm_abstraction.constructor import construct_and_verify
from research.llm_abstraction.evaluator import evaluate
from research.llm_abstraction.proposer import propose_abstraction
from research.llm_abstraction.reports import append_row
from research.llm_abstraction.schema import OK
from research.llm_abstraction.secrets import sanitize
from research.llm_abstraction.tasks import public_item

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"


def run_path(stage: str, item_id: str, condition: str, seed: int, model: str,
             extra: str = "") -> Path:
    name = f"{item_id}__{condition}__{model}__s{seed}"
    if extra:
        name += f"__{extra}"
    return RUNS / stage / f"{name}.json"


def already_done(path: Path) -> bool:
    return path.is_file()


def save_run(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(record), indent=2, default=str))


def run_llm_item(
    item: dict,
    condition: str,
    seed: int,
    model: str,
    *,
    packet_cap: int = 10,
    stage: str = "dev",
    sol_timeout_s: Optional[float] = None,
) -> dict[str, Any]:
    pub = public_item(item)
    cfg_kw = dict(
        model=model,
        condition=condition,
        packet_cap=packet_cap,
    )
    if sol_timeout_s is not None:
        cfg_kw["sol_timeout_s"] = sol_timeout_s
    config = ProposerConfig(**cfg_kw)
    t0 = time.time()
    err = None
    try:
        result = propose_abstraction(
            pub["current"],
            scientific_context=pub.get("scientific_context"),
            config=config,
            item=pub,
        )
    except Exception as exc:
        result = None
        err = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
    latency = round(time.time() - t0, 3)
    constructions = []
    if result is not None:
        for h in result.hypotheses:
            if h.parse_status == OK:
                constructions.append(
                    construct_and_verify(h, pub.get("symbols") or [], pub.get("functions") or [])
                )
        ev = evaluate(item, result, constructions)
        meta = result.meta or {}
        rec = {
            "stage": stage,
            "item_id": item.get("id"),
            "category": item.get("category"),
            "polarity": item.get("polarity"),
            "condition": condition,
            "seed": seed,
            "model": meta.get("model") or model,
            "config_id": CONFIG_ID,
            "protocol_id": PROTOCOL_ID,
            "packet_cap": packet_cap,
            "parse_status": result.parse_status,
            "parse_error": result.parse_error,
            "n_hypotheses": len([h for h in result.hypotheses if h.parse_status == OK]),
            "abstain": result.abstain,
            "usage": meta.get("usage") or {},
            "latency_s": meta.get("latency_s") or latency,
            "request_id": meta.get("request_id"),
            "reasoning_len": meta.get("reasoning_len"),
            "eval": ev,
            "constructions": constructions,
            "hypotheses": [h.to_dict() for h in result.hypotheses],
            "raw_content": (result.raw_content or "")[:8000],
            "error": err or meta.get("error"),
            "blocked": meta.get("blocked"),
        }
    else:
        rec = {
            "stage": stage,
            "item_id": item.get("id"),
            "category": item.get("category"),
            "condition": condition,
            "seed": seed,
            "model": model,
            "parse_status": "BLOCKED",
            "error": err,
            "latency_s": latency,
            "eval": {},
            "usage": {},
        }
    return sanitize(rec)


def run_matrix(
    items: list[dict],
    conditions: list[str],
    seeds: list[int],
    model: str,
    stage: str,
    *,
    packet_cap: int = 10,
    resume: bool = True,
    max_workers: int = 4,
    sol_timeout_s: Optional[float] = None,
) -> list[dict]:
    jobs = []
    for it in items:
        for cond in conditions:
            for seed in seeds:
                extra = f"cap{packet_cap}" if packet_cap not in (10, None) else ""
                path = run_path(stage, it["id"], cond, seed, model, extra)
                jobs.append((it, cond, seed, path))
    out = []
    def one(job):
        it, cond, seed, path = job
        if resume and already_done(path):
            rec = json.loads(path.read_text())
            rec["_resumed"] = True
            return rec
        rec = run_llm_item(
            it, cond, seed, model,
            packet_cap=packet_cap, stage=stage, sol_timeout_s=sol_timeout_s,
        )
        save_run(path, rec)
        try:
            append_row(rec)
        except Exception:
            pass
        return rec

    if max_workers <= 1:
        for j in jobs:
            out.append(one(j))
        return out
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = [ex.submit(one, j) for j in jobs]
        for fut in as_completed(futs):
            out.append(fut.result())
    return out
