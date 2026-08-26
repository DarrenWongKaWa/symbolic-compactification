#!/usr/bin/env python3
"""B3/B4/B5/B7-agent runners.

These arms require a callable LLM. This module refuses to invent results.
If no model is configured, it writes a skipped manifest instead of numbers.

    .venv/bin/python research/baselines/runners/run_llm_arms.py --probe-only
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "research" / "runs" / "protocol_v0"


def probe_models() -> dict:
    return {
        "grok_harness": True,
        "ANTHROPIC_AUTH_TOKEN": bool(os.environ.get("ANTHROPIC_AUTH_TOKEN")),
        "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY": bool(os.environ.get("OPENAI_API_KEY")),
        "XAI_API_KEY": bool(os.environ.get("XAI_API_KEY")),
        "GEMINI_API_KEY": bool(os.environ.get("GEMINI_API_KEY")),
        "note": "A callable third family is required for C3 confirmation. "
                "Grok-in-session is not an API batch runner by itself.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe-only", action="store_true")
    args = parser.parse_args()
    probe = probe_models()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "llm_probe.json").write_text(json.dumps(probe, indent=2) + "\n")
    print(json.dumps(probe, indent=2))
    if args.probe_only:
        return 0
    print("LLM batch arms are not silently filled. Use the skill protocol "
          "per item (AGENTS.md) or implement a real client. Writing skip.",
          file=sys.stderr)
    skip = {
        "status": "skipped_no_batch_llm_client",
        "arms": ["B3", "B4", "B5", "B7-agent"],
        "reason": "No batch LLM client is wired; Grok session can run case "
                  "studies but must not invent a 5-seed table.",
        "probe": probe,
    }
    (OUT / "llm_arms_skipped.json").write_text(json.dumps(skip, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
