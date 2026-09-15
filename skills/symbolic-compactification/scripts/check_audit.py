#!/usr/bin/env python3
"""Fail-closed audit.json check.

Does not recertify mathematics by itself. Machine-green statuses require a
bound receipt that independently recomputes to ZERO when the engine is
present, and are illegal when the engine is absent.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


def _load_ledger():
    path = Path(__file__).resolve().parent / "ledger.py"
    spec = importlib.util.spec_from_file_location("ssc_skill_ledger", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check(data: dict) -> list[str]:
    return _load_ledger().check_ledger(data)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.audit.read_text(encoding="utf-8"))
    err = check(data)
    if err:
        print("CHECK_FAIL")
        for item in err:
            print(" -", item)
        return 1
    print("CHECK_OK", args.audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
