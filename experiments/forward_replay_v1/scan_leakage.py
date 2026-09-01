#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    rows = []
    failures = []
    for task in frozen["tasks"]:
        if task["role"] != "recovery":
            continue
        tid = task["task_id"]
        target = (ROOT / "hidden" / "targets" / task["hidden_target_file"]).read_text().strip()
        ctx = ROOT / "contexts" / tid
        hits = []
        for p in ctx.rglob("*"):
            if p.is_file():
                text = p.read_text()
                if target and target in text:
                    hits.append(str(p.relative_to(ROOT)))
        row = {"task_id": tid, "target_in_context": bool(hits), "hits": hits}
        rows.append(row)
        if hits:
            failures.append(row)
    out = {"n": len(rows), "failures": failures, "rows": rows, "ok": not failures}
    (ROOT / "metrics").mkdir(exist_ok=True)
    (ROOT / "metrics" / "leakage_scan.json").write_text(json.dumps(out, indent=2) + "\n")
    if failures:
        raise SystemExit(f"LEAKAGE: {failures}")
    print("leakage scan PASS", len(rows), "recovery tasks")


if __name__ == "__main__":
    main()
