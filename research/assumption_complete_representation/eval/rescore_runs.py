"""Rescore stored raw responses after a compiler/parser software fix.

Does not call the API. Labels COMPILER_GAIN when V/Q change.
"""
from __future__ import annotations

import json
from pathlib import Path

from research.assumption_complete_representation.eval.ac_compile import COMPILER_VERSION
from research.assumption_complete_representation.eval.ac_parser import parse_model_output
from research.assumption_complete_representation.eval.ac_score import score_run
from research.assumption_complete_representation.eval.pack_data import HIDDEN, PUBLIC_PACKS
from research.llm_abstraction.secrets import sanitize

RUNS = Path(__file__).resolve().parents[1] / "runs" / "dev_matrix"


def rescore_file(path: Path) -> dict:
    rec = json.loads(path.read_text())
    tid = rec.get("task_id")
    if tid not in PUBLIC_PACKS:
        return {"path": str(path), "skipped": "unknown_task"}
    parsed = parse_model_output(rec.get("raw_response") or "")
    if rec.get("blocked"):
        parsed["parse_status"] = rec.get("parse_status") or "FAILED_OPERATIONAL"
    old = rec.get("eval") or {}
    new = score_run(parsed, PUBLIC_PACKS[tid], HIDDEN[tid])
    old_v = (old.get("best") or {}).get("V")
    new_v = (new.get("best") or {}).get("V")
    old_q = (old.get("best") or {}).get("Q")
    new_q = (new.get("best") or {}).get("Q")
    gain = (old_v != new_v) or (old_q != new_q) or (
        bool(old.get("any_operational_success")) != bool(new.get("any_operational_success"))
    )
    rec["eval_v0"] = rec.get("eval_v0") or old
    rec["eval"] = new
    rec["parsed"] = {k: parsed[k] for k in parsed if k != "raw_obj"}
    rec["compiler_version"] = COMPILER_VERSION
    rec["COMPILER_GAIN"] = bool(gain)
    rec["parse_status"] = parsed.get("parse_status")
    rec["n_hypotheses"] = new.get("n_hypotheses")
    path.write_text(json.dumps(sanitize(rec), indent=2, default=str))
    return {
        "path": path.name,
        "task_id": tid,
        "COMPILER_GAIN": gain,
        "old_V": old_v, "new_V": new_v,
        "old_Q": old_q, "new_Q": new_q,
        "operational_success": new.get("any_operational_success"),
    }


def main() -> dict:
    rows = []
    if RUNS.is_dir():
        for p in sorted(RUNS.glob("*.json")):
            if p.name.endswith(".tmp"):
                continue
            rows.append(rescore_file(p))
    return {
        "compiler_version": COMPILER_VERSION,
        "n": len(rows),
        "n_gain": sum(1 for r in rows if r.get("COMPILER_GAIN")),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
