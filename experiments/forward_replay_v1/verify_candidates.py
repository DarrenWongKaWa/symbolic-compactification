#!/usr/bin/env python3
"""Run frozen candidates through the frozen Mode A verifier. Does not modify src/."""
from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

import sympy as sp
import yaml
from symbolic_compactification.models import (
    ASSUMPTION_REQUIRED,
    COMPILE_FAILURE,
    NONZERO,
    PARSE_FAILURE,
    UNKNOWN,
    ZERO,
)
from symbolic_compactification.research_api import verify_hypothesis
from symbolic_compactification.workspace import load_workspace

ROOT = Path(__file__).resolve().parent
PROPOSERS = ("cas_sympy", "gplearn", "gold_control", "injected_negative", "llm_masked")

PROMOTE = {ZERO}


def parse_expr(text: str) -> sp.Expr:
    return sp.sympify(text, locals={"Rational": sp.Rational, "I": sp.I})


def free_names(*texts: str) -> list[str]:
    names: set[str] = set()
    for t in texts:
        try:
            names |= {str(s) for s in parse_expr(t).free_symbols}
        except Exception:
            continue
    return sorted(names)


def write_workspace(dest: Path, current: str, candidate: str, names: list[str]) -> None:
    (dest / "expressions").mkdir()
    (dest / "assumptions").mkdir()
    (dest / "hypotheses").mkdir()
    (dest / "notes").mkdir()
    (dest / "references").mkdir()
    (dest / "expressions" / "current.txt").write_text(current.strip() + "\n")
    (dest / "expressions" / "candidate.txt").write_text(candidate.strip() + "\n")
    symbols = [{"name": n, "real": True, "nonzero": n in {"e12", "e21"}} for n in names]
    yaml.safe_dump({"symbols": symbols, "functions": []}, (dest / "assumptions" / "assumptions.yaml").open("w"))
    (dest / "project.yaml").write_text(
        "project_name: forward-replay\n"
        "objective: Forward candidate vs current state.\n"
        "expression_entrypoint: expressions/current.txt\n"
        "assumptions_file: assumptions/assumptions.yaml\n"
        "optional_notes:\n  - notes/research_notes.md\n"
        "optional_references:\n  - references/README.md\n"
    )
    (dest / "notes" / "research_notes.md").write_text("Forward replay candidate.\n")
    (dest / "references" / "README.md").write_text("None.\n")
    hyp = {
        "assumptions_used": names,
        "hypothesis_type": "equivalence",
        "instance_maps": {
            "expressions/candidate.txt": {"presentation": "candidate"},
            "expressions/current.txt": {"presentation": "current"},
        },
        "latent_object": None,
        "members": ["expressions/current.txt", "expressions/candidate.txt"],
        "operators": ["EQUIVALENCE"],
        "proof_obligations": [
            {
                "left": "expressions/current.txt",
                "obligation_id": "forward-equiv",
                "relation": "equivalent",
                "right": "expressions/candidate.txt",
            }
        ],
        "reconstruction_rule": "Exact residual current - candidate.",
        "schema_version": 1,
    }
    (dest / "hypotheses" / "hypothesis.json").write_text(json.dumps(hyp, indent=2) + "\n")


def recover_against_target(candidate: str, target: str, names: list[str]) -> str:
    tmp = Path(tempfile.mkdtemp(prefix="ssc-rec-"))
    try:
        write_workspace(tmp, target, candidate, names)
        result = verify_hypothesis(tmp)
        return str(result.result)
    except Exception as exc:  # noqa: BLE001
        return f"ERROR:{type(exc).__name__}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verify_one(current: str, candidate: str, names: list[str]) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix="ssc-fwd-"))
    try:
        write_workspace(tmp, current, candidate, names)
        result = verify_hypothesis(tmp)
        status = str(result.result)
        return {
            "result": status,
            "error_code": result.error_code,
            "promoted": status in {str(ZERO)},
            "run_id": result.run_id,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "result": "ERROR",
            "error_code": type(exc).__name__,
            "promoted": False,
            "detail": repr(exc),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    tasks = {t["task_id"]: t for t in frozen["tasks"]}
    rows = []
    out_dir = ROOT / "verification"
    out_dir.mkdir(exist_ok=True)
    for proposer in PROPOSERS:
        pdir = ROOT / "candidates" / proposer
        if not pdir.exists():
            continue
        for task_dir in sorted(pdir.iterdir()):
            rec_path = task_dir / "candidates.json"
            if not rec_path.exists():
                continue
            rec = json.loads(rec_path.read_text())
            tid = rec["task_id"]
            task = tasks[tid]
            current = (ROOT / "contexts" / tid / "current.txt").read_text().strip()
            target = (ROOT / "hidden" / "targets" / task["hidden_target_file"]).read_text().strip()
            for cand in rec["candidates"]:
                expr = cand["expression"]
                names = free_names(current, expr, target)
                if not names:
                    names = ["x"]
                promo = verify_one(current, expr, names)
                recovery = None
                if task["role"] == "recovery":
                    recovery = recover_against_target(expr, target, free_names(expr, target) or names)
                row = {
                    "proposer_id": proposer,
                    "task_id": tid,
                    "candidate_id": cand["candidate_id"],
                    "role": task["role"],
                    "is_gold_control": bool(cand.get("is_gold_control")),
                    "injected_negative": bool(cand.get("injected_negative")),
                    "promotion": promo,
                    "target_recovery_result": recovery,
                    "recovered": recovery == str(ZERO),
                    "expression": expr,
                }
                rows.append(row)
                print(
                    proposer,
                    tid,
                    cand["candidate_id"],
                    promo["result"],
                    "rec" if row["recovered"] else "",
                    "PROMOTED" if promo["promoted"] else "refuse",
                )
    (out_dir / "records.json").write_text(json.dumps(rows, indent=2) + "\n")
    print("n_records", len(rows))


if __name__ == "__main__":
    main()
