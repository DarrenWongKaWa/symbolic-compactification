#!/usr/bin/env python3
"""Fail-closed sanity check for audit.json. Does not recertify mathematics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED = {
    "EXACT",
    "EXACT_IF_ASSUMPTIONS",
    "STRUCTURAL",
    "CITED_RULE",
    "ASYMPTOTIC_UNCERTIFIED",
    "HUMAN_REVIEW",
    "GAP",
    "NONZERO_RESIDUAL",
    "NUMERICAL_SUPPORT",
    "UNCERTIFIED",
}


def check(data: dict) -> list[str]:
    err = []
    if "paper" not in data:
        err.append("missing paper")
    if "claims" not in data:
        err.append("missing claims")
    if "edges" not in data:
        err.append("missing edges")
    if "inventory" not in data or "equations" not in (data.get("inventory") or {}):
        err.append("missing inventory.equations")
    for c in data.get("claims") or []:
        if c.get("status") not in ALLOWED:
            err.append(f"claim {c.get('id')} bad status {c.get('status')}")
        if c.get("status") == "EXACT" and "asymptotic" in (c.get("statement") or "").lower():
            err.append(f"claim {c.get('id')} Exact on asymptotic language")
    for e in data.get("edges") or []:
        if e.get("status") not in ALLOWED:
            err.append(f"edge {e.get('id')} bad status {e.get('status')}")
        if e.get("status") == "EXACT" and "asymptotic" in (e.get("transformation") or ""):
            err.append(f"edge {e.get('id')} Exact on asymptotic")
    for o in data.get("reviewer_obligations") or []:
        if o.get("status") not in ALLOWED:
            err.append(f"obligation {o.get('id')} bad status {o.get('status')}")
    return err


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True, type=Path)
    args = ap.parse_args()
    data = json.loads(args.audit.read_text(encoding="utf-8"))
    err = check(data)
    if err:
        print("CHECK_FAIL")
        for e in err:
            print(" -", e)
        return 1
    print("CHECK_OK", args.audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
