"""Rescore frozen Guo P2 local-confluence pairs. No LLM. No run-file rewrite."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import sympy

from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item
from research.scalable_verification.api import UNKNOWN, ZERO, gain_label
from research.scalable_verification.confluence import check_limit
from research.scalable_verification.factor import split_multiplicative

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT_JSON = ROOT / "scalable_verification" / "FROZEN_RESCORE.json"
OUT_CSV = ROOT / "scalable_verification" / "FROZEN_RESCORE.csv"
OUT_MD = ROOT / "scalable_verification" / "FROZEN_RESCORE.md"


def _eps(index: str) -> sympy.Expr:
    return sympy.Function("epsilon")(sympy.Symbol(index, real=True))


def rescore() -> dict:
    item = load_guo_item()
    blob = json.loads(MAP.read_text())
    rows = []
    for hyp in blob["hypotheses"]:
        rtype = hyp.get("claimed_type")
        texts = {m["member_id"]: m["text"] for m in hyp.get("members") or []}
        old = "UNKNOWN"
        ops_list = [int(m.get("ops") or 0) for m in hyp.get("members") or []]
        if rtype != "local_confluence" or len(texts) != 2 or (ops_list and max(ops_list) > 200):
            rows.append({
                "seed": hyp.get("seed"),
                "index": hyp.get("index"),
                "type": rtype,
                "member_ids": hyp.get("member_ids"),
                "old": old,
                "new": UNKNOWN,
                "gain": "NO_GAIN",
                "layer": "V",
                "note": "not_local_confluence_pair",
            })
            continue
        gen = None
        deg = None
        for m in hyp["members"]:
            cond = (m.get("cond") or "").lower()
            if cond == "true":
                gen = m["member_id"]
            else:
                deg = m["member_id"]
        if not gen or not deg:
            ids = hyp["member_ids"]
            gen, deg = ids[1], ids[0]
        A = parse_flex(texts[gen], item["symbols"], item["functions"])
        B = parse_flex(texts[deg], item["symbols"], item["functions"])
        if A is None or B is None:
            rows.append({
                "seed": hyp.get("seed"), "index": hyp.get("index"),
                "type": rtype, "member_ids": hyp.get("member_ids"),
                "old": old, "new": UNKNOWN, "gain": "NO_GAIN",
                "layer": "C", "note": "unparseable_member",
            })
            continue
        sp = split_multiplicative(A, B)
        F, G = (sp["A_local"], sp["B_local"]) if sp["certified"] else (A, B)
        args = {}
        for op in hyp.get("operators") or []:
            if op.get("kind") == "limit":
                args = op.get("args") or {}
        ytxt = str(args.get("source") or "epsilon(m)")
        xtxt = str(args.get("target") or "epsilon(n)")
        y = _eps("m") if "m" in ytxt else _eps("n")
        x = _eps("n") if "n" in xtxt else _eps("m")
        result = check_limit(F, y, x, G)
        new = result.verdict
        gain = "V_GAIN" if new == ZERO else "NO_GAIN"
        rows.append({
            "seed": hyp.get("seed"),
            "index": hyp.get("index"),
            "type": rtype,
            "member_ids": hyp.get("member_ids"),
            "old": old,
            "new": new,
            "gain": gain,
            "layer": "V" if new == UNKNOWN else ("OK" if new == ZERO else "D"),
            "note": f"{sp['note']}|{result.provenance}",
            "factor_certified": sp["certified"],
        })
    n_conf = [r for r in rows if r["type"] == "local_confluence"]
    n_z = sum(1 for r in n_conf if r["new"] == ZERO)
    n_nz = sum(1 for r in n_conf if r["new"] == "NONZERO")
    n_u = sum(1 for r in n_conf if r["new"] == UNKNOWN)
    n_h = [r for r in rows if r["type"] == "hermite_divided_difference"]
    report = {
        "n_hypotheses": len(rows),
        "n_confluence": len(n_conf),
        "confluence_ZERO": n_z,
        "confluence_NONZERO": n_nz,
        "confluence_UNKNOWN": n_u,
        "hermite_n": len(n_h),
        "hermite_ZERO": 0,
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["seed", "index", "type", "old", "new", "gain", "layer", "note"])
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in w.fieldnames})
    lines = [
        "# Frozen Guo P2 rescore (Track V)",
        "",
        f"local_confluence: ZERO={n_z} NONZERO={n_nz} UNKNOWN={n_u} (n={len(n_conf)})",
        f"hermite_divided_difference: n={len(n_h)} ZERO=0 (not discharged by confluence cascade)",
        "",
        "| seed | i | type | new | gain | note |",
        "|---:|---:|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['seed']} | {r['index']} | {r['type']} | {r['new']} | {r['gain']} | {str(r.get('note') or '')[:60]} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = rescore()
    print(
        "confluence",
        "ZERO", rep["confluence_ZERO"],
        "NONZERO", rep["confluence_NONZERO"],
        "UNKNOWN", rep["confluence_UNKNOWN"],
    )
