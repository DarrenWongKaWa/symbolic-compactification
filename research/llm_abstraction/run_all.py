"""Execute the DEV program. Resume-safe. Never prints API keys."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.reports import (
    decision_case,
    load_csv,
    summarize,
    write_token_costs,
)
from research.llm_abstraction.secrets import key_length, key_present


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--stage", default="all",
                   choices=["calibration", "dev", "guo", "flash", "all", "baselines"])
    p.add_argument("--workers", type=int, default=4)
    args = p.parse_args(argv)
    print(f"key_present={int(key_present())} key_len={key_length() if key_present() else 0}")
    if args.stage in {"calibration", "all", "baselines"}:
        from research.llm_abstraction.run_calibration import run as run_cal
        run_cal(max_workers=args.workers)
    if args.stage in {"dev", "all"}:
        from research.llm_abstraction.run_dev import run as run_dev
        print(json.dumps(run_dev(max_workers=args.workers), indent=2))
    if args.stage in {"guo", "all"}:
        from research.llm_abstraction.run_guo import run as run_guo
        try:
            print(json.dumps(run_guo(), indent=2, default=str))
        except Exception as exc:
            print(f"GUO BLOCKED_OR_FAILED {type(exc).__name__}: {exc}")
    if args.stage in {"flash", "all"}:
        from research.llm_abstraction.run_flash import run as run_flash
        print(json.dumps(run_flash(), indent=2))
    rows = load_csv()
    if rows:
        write_token_costs(rows)
        raw = summarize(rows, condition="A0")
        sol = summarize(rows, condition="A2")
        letter, reason = decision_case(raw, sol)
        print("RAW", raw)
        print("SOL", sol)
        print("CASE", letter, reason)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
