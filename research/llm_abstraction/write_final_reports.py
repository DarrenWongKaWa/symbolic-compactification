"""Render RESULTS_DEV.md, GUO_DEV.md, DECISION.md from run artifacts."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from research.llm_abstraction.reports import (
    CSV_PATH,
    decision_case,
    load_csv,
    summarize,
    write_token_costs,
)
from research.llm_abstraction.run_lib import RUNS

HERE = Path(__file__).resolve().parent


def _by(rows, key):
    g = defaultdict(list)
    for r in rows:
        g[r.get(key)].append(r)
    return g


def render() -> None:
    rows = load_csv()
    write_token_costs(rows)
    calib = [r for r in rows if r.get("stage") == "calibration"]
    dev = [r for r in rows if r.get("stage") == "dev"]
    guo = [r for r in rows if r.get("stage") == "guo"]
    flash = [r for r in rows if r.get("stage") == "flash"]
    pk = [r for r in rows if r.get("stage") == "packet_size"]

    def block(title, rs):
        lines = [f"## {title}", ""]
        if not rs:
            lines += ["(no rows)", ""]
            return "\n".join(lines)
        overall = summarize(rs)
        lines.append(f"n={overall['n']} success={overall['success_rate']} "
                     f"type+target={overall['correct_hypothesis_rate']} "
                     f"certified={overall['certified_rate']} "
                     f"parse_fail={overall['parse_failure_rate']} "
                     f"unnecessary={overall['unnecessary_rate']} "
                     f"repr_chg={overall['representation_change_rate']} "
                     f"false_abs={overall['false_abstraction_rate']} "
                     f"abstain={overall['abstention_rate']}")
        lines.append("")
        lines.append("| condition | n | success | type+target | certified | unnec | repr | false_abs | abstain | parse_fail |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for cond, grp in sorted(_by(rs, "condition").items(), key=lambda kv: str(kv[0])):
            s = summarize(grp)
            lines.append(
                f"| {cond} | {s['n']} | {s['success_rate']} | {s['correct_hypothesis_rate']} | "
                f"{s['certified_rate']} | {s['unnecessary_rate']} | {s['representation_change_rate']} | "
                f"{s['false_abstraction_rate']} | {s['abstention_rate']} | {s['parse_failure_rate']} |"
            )
        lines.append("")
        lines.append("| category | n | success | certified | repr |")
        lines.append("|---|---:|---:|---:|---:|")
        for cat, grp in sorted(_by(rs, "category").items(), key=lambda kv: str(kv[0])):
            s = summarize(grp)
            lines.append(f"| {cat} | {s['n']} | {s['success_rate']} | {s['certified_rate']} | {s['representation_change_rate']} |")
        lines.append("")
        return "\n".join(lines)

    a0 = summarize(calib + dev, condition="A0")
    a2 = summarize(calib + dev, condition="A2")
    letter, reason = decision_case(a0, a2)

    md = []
    md.append("# DeepSeek abstraction DEV results")
    md.append("")
    md.append("Infrastructure experiment. Not a paper result. Frozen B9/LGG/SOL were not mutated.")
    md.append("")
    md.append(f"Primary contrast A0 RAW vs A2 RAW+SOL: **CASE {letter}** — {reason}")
    md.append("")
    md.append(block("Calibration (1 seed, A–H)", calib))
    md.append(block("DEV multi-seed (frozen + local bench)", dev))
    md.append(block("Packet-size ablation", pk))
    md.append(block("Guo DEV", guo))
    md.append(block("Flash A0 vs A2 (same prompts)", flash))
    md.append("## Tokens")
    md.append("")
    tot = summarize(rows)
    md.append(f"prompt={tot['prompt_tokens']} completion={tot['completion_tokens']} "
              f"reasoning={tot['reasoning_tokens']} est_usd_offpeak={tot['est_usd_offpeak']}")
    md.append("")
    md.append("Certified ZERO on obligations is the only exact truth. Verbal master-function talk is not success.")
    (HERE / "RESULTS_DEV.md").write_text("\n".join(md) + "\n")

    gmd = ["# Guo DEV", ""]
    if not guo:
        gmd.append("No Guo LLM rows yet, or BLOCKED.")
    else:
        gmd.append(block("Guo conditions G0–G3 recorded as A0–A3", guo))
        gmd.append("Do not treat this as discovering Φ_Γ or PRB closed form.")
    # packets
    gfiles = list((RUNS / "guo").glob("*.json")) if (RUNS / "guo").is_dir() else []
    gmd.append(f"run files: {len(gfiles)}")
    (HERE / "GUO_DEV.md").write_text("\n".join(gmd) + "\n")

    dec = []
    dec.append("# Decision")
    dec.append("")
    dec.append(f"CASE **{letter}**: {reason}")
    dec.append("")
    dec.append("## A0 RAW")
    dec.append(json.dumps(a0, indent=2))
    dec.append("")
    dec.append("## A2 RAW+SOL")
    dec.append(json.dumps(a2, indent=2))
    dec.append("")
    dec.append("## Claim boundary")
    dec.append("")
    dec.append("At most: a relation-rich structural representation may change LLM abstraction proposals")
    dec.append("under controlled symbolic tasks. Not: AI discovers physics.")
    dec.append("")
    dec.append("Protocol remains DEV. Not frozen for held-out TEST until this file says so.")
    (HERE / "DECISION.md").write_text("\n".join(dec) + "\n")
    print("CASE", letter, reason)
    print("wrote RESULTS_DEV.md GUO_DEV.md DECISION.md")


if __name__ == "__main__":
    render()
