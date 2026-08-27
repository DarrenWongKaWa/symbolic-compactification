"""P1 vs frozen P0. Same model/SOL/budgets. New files only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.grounded_proposer.propose import propose_p1
from research.grounded_proposer.score import score_p1_hyp
from research.llm_abstraction.secrets import key_present, key_length, sanitize
from research.llm_abstraction.tasks import load_calibration, load_guo_item
from research.obligation_ir.source_index import build_index

OUT = Path(__file__).resolve().parent / "runs"
MD = Path(__file__).resolve().parent / "RESULTS_P1.md"


def _index(item: dict):
    return build_index(
        item["current"], item.get("symbols") or [], item.get("functions") or [],
    )


def run_item(item: dict, seed: int) -> dict:
    idx = _index(item)
    rec = propose_p1(item, idx, condition="A2")
    rec["seed"] = seed
    scores = []
    for h in rec.get("hypotheses") or []:
        scores.append({
            "type": h.get("representation_type"),
            "parse_status": h.get("parse_status"),
            "ids": [m.get("source_node_id") for m in (h.get("member_maps") or [])],
            **score_p1_hyp(
                h, idx,
                symbols=item.get("symbols") or [],
                functions=item.get("functions") or [],
            ),
        })
    rec["scores"] = scores
    rec["types_ok"] = [s["type"] for s in scores if s.get("parse_status") != "PARSE_FAILURE"]
    rec["n_ddcf"] = sum(1 for t in rec["types_ok"] if t in {
        "divided_difference", "confluent_representation",
    })
    rec["n_zero"] = sum(1 for s in scores if s.get("layer") == "OK")
    rec["n_nonzero"] = sum(1 for s in scores if s.get("detail") == "wrong_structure")
    rec["n_unknown"] = sum(1 for s in scores if s.get("layer") == "V")
    rec["n_gfail"] = sum(1 for s in scores if s.get("layer") == "G")
    return sanitize(rec)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"key_present={int(key_present())} key_len={key_length() if key_present() else 0}")
    if not key_present():
        print("P1 BLOCKED")
        return
    # contract smoke: CAL-G confluence toy
    calib = {it["id"]: it for it in load_calibration()}
    smoke = []
    if "CAL-G-confluence" in calib:
        p = OUT / "CAL-G-confluence__P1__s0.json"
        if p.is_file():
            rec = json.loads(p.read_text())
        else:
            rec = run_item(calib["CAL-G-confluence"], 0)
            p.write_text(json.dumps(rec, indent=2, default=str))
        smoke.append(rec)
        print("CAL-G", rec.get("parse_status"), rec.get("types_ok"), rec.get("n_zero"))
    guo = load_guo_item()
    guo_rows = []
    for seed in range(3):
        p = OUT / f"guo-sigma-abc__P1_A2__s{seed}.json"
        if p.is_file():
            rec = json.loads(p.read_text())
        else:
            rec = run_item(guo, seed)
            p.write_text(json.dumps(rec, indent=2, default=str))
        guo_rows.append(rec)
        print("Guo s"+str(seed), rec.get("parse_status"), "ddcf", rec.get("n_ddcf"),
              "OK", rec.get("n_zero"), "D", rec.get("n_nonzero"), "V", rec.get("n_unknown"),
              "Gfail", rec.get("n_gfail"), rec.get("types_ok"))
    lines = [
        "# Grounded-Proposer-v1 vs frozen P0",
        "",
        "Same SOL, same `deepseek-v4-pro`, same A2 packets, same budgets.",
        "Only the member contract changed (catalog IDs, no aliases).",
        "",
        "## Guo P1 A2 (3 seeds)",
        "",
        "| seed | parse | types | dd/conf | ZERO | NONZERO | UNKNOWN | G-fail |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ]
    for rec in guo_rows:
        lines.append(
            f"| {rec.get('seed')} | {rec.get('parse_status')} | "
            f"{', '.join(rec.get('types_ok') or []) or '—'} | {rec.get('n_ddcf')} | "
            f"{rec.get('n_zero')} | {rec.get('n_nonzero')} | {rec.get('n_unknown')} | "
            f"{rec.get('n_gfail')} |"
        )
    lines += [
        "",
        "Frozen P0 A2 Guo: G1 vocabulary often present; unique grounded confluence ZERO n=1;",
        "most DD aliases AMBIGUOUS. P1 asks whether that survives a grounding contract.",
        "",
        "A = grounded DD/confluence + ZERO (interface was hiding discovery).",
        "B = grounded + NONZERO (fair D).",
        "C = DD/confluence vanish (old G1 was linguistic).",
        "D = grounded + UNKNOWN (V).",
        "",
    ]
    MD.write_text("\n".join(lines) + "\n")
    print("wrote", MD)


if __name__ == "__main__":
    main()
