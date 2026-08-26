#!/usr/bin/env python3
"""Verify collected proposer JSON against the engine. DEV only."""
from __future__ import annotations

import json
import re
from pathlib import Path

from symbolic_compactification import NONZERO, UNKNOWN, ZERO, verify_equivalent

ROOT = Path(__file__).resolve().parents[2]
HARD = ROOT / "research/search_bottleneck/dev_hard"
OUT = ROOT / "research/search_bottleneck/runs"


def load_item(iid: str) -> dict:
    return json.loads((HARD / f"{iid}.json").read_text())


def verify_one(item, cand_text, definitions):
    functions = list(item.get("functions") or [])
    expanded = cand_text
    if definitions:
        for name, body in definitions.items():
            # naive token replace of name(...) left to engine if still a Function
            expanded = expanded.replace(name, f"({body})")
            functions.append(name)
    try:
        r = verify_equivalent(
            item["current"], cand_text, item["symbols"],
            functions=functions or None)
        return r
    except Exception as exc:
        class _R:
            verdict = UNKNOWN
            seconds = 0.0
            evidence = [{"kind": "verify_exception", "msg": str(exc)}]
            counterexample = None
        return _R()


def main():
    raw_dir = OUT / "raw_proposals"
    rows = []
    if not raw_dir.exists():
        print("no raw_proposals yet")
        return
    for path in sorted(raw_dir.glob("*.json")):
        blob = json.loads(path.read_text())
        iid = blob["id"]
        item = load_item(iid)
        if not item.get("current"):
            rows.append({**blob, "verify": "skipped_no_current"})
            continue
        for i, c in enumerate(blob.get("candidates") or []):
            text = c.get("candidate_text") or ""
            defs = c.get("hypothesis_definitions") or {}
            r = verify_one(item, text, defs)
            rows.append({
                "file": path.name,
                "arm": blob.get("arm"),
                "id": iid,
                "seed": blob.get("seed", 0),
                "i": i,
                "candidate_text": text,
                "abstraction_level": c.get("abstraction_level"),
                "hypothesis_family": c.get("hypothesis_family"),
                "claimed_proven": c.get("claimed_proven"),
                "verdict": r.verdict,
                "seconds": r.seconds,
                "evidence0": (r.evidence or [{}])[0].get("kind"),
            })
            print(blob.get("arm"), iid, r.verdict, text[:80])
    (OUT / "verified_rows.json").write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
