"""P2/P3/P4 representation-search runs. Same model/SOL as P1; V2 contract only.

Does not mutate frozen P0/P1 JSON. Writes new files under llm/runs/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.grounded_proposer.catalog import catalog_entries
from research.llm_abstraction.secrets import key_length, key_present, sanitize
from research.llm_abstraction.tasks import load_calibration, load_guo_item
from research.obligation_ir.source_index import build_index
from research.representation_invention.bench.loader import load_dev, proposer_view
from research.representation_invention.eval.classify import summarize_record
from research.representation_invention.llm.run_p2 import run_item

OUT = Path(__file__).resolve().parents[1] / "llm" / "runs"
SUMMARY = Path(__file__).resolve().parents[1] / "RESULTS_DEV.md"
SUMMARY_JSON = Path(__file__).resolve().parents[1] / "RESULTS_DEV.json"

DEV_BENCH_IDS = (
    "dev-a-newton-first",
    "dev-a-repeated-node",
    "dev-a-hermite-two",
    "dev-a-wrong-sign-dd",
    "dev-b-piecewise-dd",
    "dev-b-special-fn",
    "dev-b-master-induct",
    "dev-b-tautological-master",
)


def _index(item: dict):
    return build_index(
        item["current"],
        item.get("symbols") or [],
        item.get("functions") or [],
    )


def _bench_as_item(task: dict) -> tuple[dict, list[dict]]:
    pub = proposer_view(task)
    current = pub.get("current") or ""
    if not current and pub.get("source_expressions"):
        current = pub["source_expressions"][0] if isinstance(pub["source_expressions"], list) else str(pub["source_expressions"])
    item = {
        "id": pub.get("id") or task.get("id"),
        "current": current,
        "symbols": pub.get("symbols") or task.get("symbols") or [],
        "functions": pub.get("functions") or task.get("functions") or [],
        "scientific_context": pub.get("scientific_context") or [],
        "split": "dev",
    }
    catalog = []
    for e in pub.get("catalog") or task.get("catalog") or []:
        if not isinstance(e, dict):
            continue
        catalog.append({
            "source_node_id": e.get("id") or e.get("source_node_id"),
            "kind": e.get("kind") or "expr",
            "text": e.get("text") or "",
            "fingerprint": e.get("fingerprint") or {},
        })
    return item, catalog


def out_path(item_id: str, condition: str, seed: int) -> Path:
    return OUT / f"{item_id}__{condition}__s{seed}.json"


def run_one(
    item: dict,
    *,
    condition: str,
    seed: int,
    catalog: Optional[list[dict]] = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    path = out_path(str(item.get("id")), condition, seed)
    if path.is_file() and not overwrite:
        return json.loads(path.read_text())
    rec = run_item(item, condition=condition, seed=seed, catalog=catalog)
    rec["summary"] = summarize_record(rec)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sanitize(rec), indent=2, default=str))
    return rec


def matrix(flagship_seeds: int = 5) -> list[tuple]:
    jobs: list[tuple] = []
    calib = {it["id"]: it for it in load_calibration()}
    if "CAL-G-confluence" in calib:
        jobs.append(("cal", calib["CAL-G-confluence"], "P2", 0, None))
    bench = {t["id"]: t for t in load_dev()}
    for tid in DEV_BENCH_IDS:
        if tid not in bench:
            continue
        item, cat = _bench_as_item(bench[tid])
        for seed in range(flagship_seeds):
            jobs.append(("bench", item, "P2", seed, cat))
    guo = load_guo_item()
    gcat = catalog_entries(_index(guo))
    for seed in range(flagship_seeds):
        jobs.append(("guo", guo, "P2", seed, gcat))
    for seed in range(flagship_seeds):
        jobs.append(("guo", guo, "P3", seed, gcat))
    return jobs


def write_summary(records: list[dict[str, Any]]) -> None:
    rows = [summarize_record(r) if "summary" not in r else r.get("summary") or summarize_record(r) for r in records]
    SUMMARY_JSON.write_text(json.dumps({"n": len(rows), "rows": rows}, indent=2, default=str))
    lines = [
        "# Representation invention DEV results",
        "",
        "P1 frozen runs were not mutated. New files are under `llm/runs/`.",
        "",
        "| item | cond | seed | parse | n_ok | grounded | ZERO | NONZERO | UNKNOWN | DD-OK | confluence |",
        "|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r.get('item_id')} | {r.get('condition')} | {r.get('seed')} | "
            f"{r.get('parse_status')} | {r.get('n_ok')} | {r.get('n_grounded')} | "
            f"{r.get('n_zero')} | {r.get('n_nonzero')} | {r.get('n_unknown')} | "
            f"{r.get('n_dd_ok')} | {r.get('n_local_confluence')} |"
        )
    SUMMARY.write_text("\n".join(lines) + "\n")


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    seeds = 5
    if "--seeds" in argv:
        seeds = int(argv[argv.index("--seeds") + 1])
    only = None
    if "--only" in argv:
        only = argv[argv.index("--only") + 1]
    print(f"key_present={int(key_present())} key_len={key_length() if key_present() else 0}")
    if not key_present():
        print("EXPERIMENT BLOCKED: no API key")
        return 2
    jobs = matrix(seeds)
    if only:
        jobs = [j for j in jobs if only in (j[0], j[1].get("id"), j[2])]
    recs = []
    for i, (fam, item, cond, seed, cat) in enumerate(jobs):
        iid = item.get("id")
        print(f"[{i+1}/{len(jobs)}] {fam} {iid} {cond} s{seed}", flush=True)
        try:
            rec = run_one(item, condition=cond, seed=seed, catalog=cat)
        except Exception as exc:
            rec = sanitize({
                "item_id": iid, "condition": cond, "seed": seed,
                "blocked": True, "error": f"{type(exc).__name__}:{exc}",
                "hypotheses": [], "n_ok": 0,
            })
            out_path(str(iid), cond, seed).write_text(json.dumps(rec, indent=2, default=str))
        recs.append(rec)
        print(
            " ", rec.get("parse_status"), "ok", rec.get("n_ok"),
            "Z", rec.get("n_zero"), "NZ", rec.get("n_nonzero"),
            "U", rec.get("n_unknown"), "dd_ok", (rec.get("summary") or {}).get("n_dd_ok"),
            rec.get("error"),
            flush=True,
        )
    write_summary(recs)
    print("wrote", SUMMARY)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
