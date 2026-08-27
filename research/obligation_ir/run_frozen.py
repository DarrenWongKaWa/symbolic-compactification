"""Compile frozen DeepSeek outputs. Does not mutate llm_abstraction/runs."""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from research.llm_abstraction.schema import LLMStructureHypothesis, OK, PARSE_FAILURE, ProposeResult
from research.llm_abstraction.tasks import load_calibration, load_dev_primary, load_guo_item
from research.obligation_ir.compiler import compile_hypothesis
from research.obligation_ir.guo import g1_discovery, g2_formalization, g3_compile, g4_certify
from research.obligation_ir.labels import layer_label
from research.obligation_ir.verify import verify_obligation

FROZEN = ROOT / "research" / "llm_abstraction" / "runs"
OUT = ROOT / "research" / "obligation_ir" / "results"
CSV_PATH = ROOT / "research" / "obligation_ir" / "RESULTS_FROZEN.csv"


def _hyp(raw: dict) -> LLMStructureHypothesis:
    if (raw.get("parse_status") or OK) == PARSE_FAILURE:
        return LLMStructureHypothesis.parse_failure(raw.get("parse_error") or "x", raw)
    return LLMStructureHypothesis(
        hypothesis_type=raw["hypothesis_type"],
        target_members=list(raw.get("target_members") or []),
        latent_object=str(raw.get("latent_object") or ""),
        parameters=list(raw.get("parameters") or []),
        operators=list(raw.get("operators") or []),
        instance_maps=list(raw.get("instance_maps") or []),
        construction_plan=str(raw.get("construction_plan") or ""),
        required_assumptions=list(raw.get("required_assumptions") or []),
        proof_obligations=list(raw.get("proof_obligations") or []),
        rationale=str(raw.get("rationale") or ""),
        confidence=float(raw.get("confidence") or 0),
        parse_status=OK,
        quality_flags=list(raw.get("quality_flags") or []),
    )


def _items() -> dict:
    out = {}
    for it in load_calibration() + load_dev_primary():
        out[it["id"]] = it
    g = load_guo_item()
    out[g["id"]] = g
    return out


def run() -> list[dict]:
    items = _items()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in sorted(FROZEN.rglob("*.json")):
        if f.name.startswith("frozen") or f.parent.name == "_cache":
            continue
        d = json.loads(f.read_text())
        if "hypotheses" not in d:
            continue
        it = items.get(d.get("item_id"))
        if it is None:
            continue
        hyps = [_hyp(h) for h in d.get("hypotheses") or []]
        result = ProposeResult(
            hypotheses=hyps,
            parse_status=d.get("parse_status") or OK,
            abstain=bool(d.get("abstain")),
            raw_content=d.get("raw_content") or "",
        )
        compiles = []
        verifs = []
        for h in hyps:
            if h.parse_status != OK:
                continue
            cr = compile_hypothesis(
                h, symbols=it.get("symbols") or [], functions=it.get("functions") or [],
            )
            compiles.append(cr)
            for obl in cr.obligations:
                verifs.append(verify_obligation(
                    obl, symbols=it.get("symbols") or [], functions=it.get("functions") or [],
                ))
        n_ok = sum(c.n_ok for c in compiles)
        n_fail = sum(c.n_fail for c in compiles)
        lab = layer_label(it, result, n_ok, n_fail, verifs)
        rec = {
            "file": str(f.relative_to(ROOT)),
            "item_id": d.get("item_id"),
            "stage": d.get("stage") or f.parent.name,
            "condition": d.get("condition"),
            "seed": d.get("seed"),
            "category": it.get("category"),
            "layer": lab["layer"],
            "layer_detail": lab["detail"],
            "n_compile_ok": n_ok,
            "n_compile_fail": n_fail,
            "n_zero": sum(1 for v in verifs if v.verdict == "ZERO"),
            "n_nonzero": sum(1 for v in verifs if v.verdict == "NONZERO"),
            "n_unknown": sum(1 for v in verifs if v.verdict == "UNKNOWN"),
            "types": [h.hypothesis_type for h in hyps if h.parse_status == OK],
            "old_certified": (d.get("eval") or {}).get("certified"),
        }
        if d.get("item_id") == "guo-sigma-abc":
            rec["G1"] = g1_discovery(hyps)
            rec["G2"] = g2_formalization(hyps)
            rec["G3"] = g3_compile(compiles)
            rec["G4"] = g4_certify([v.verdict for v in verifs])
        rows.append(rec)
        if d.get("item_id") == "guo-sigma-abc" or d.get("item_id", "").startswith("T7") or d.get("item_id", "").startswith("CAL-D"):
            (OUT / (f.stem + ".json")).write_text(json.dumps({
                "rec": rec,
                "compiles": [c.to_dict() for c in compiles],
                "verifs": [v.to_dict() for v in verifs],
            }, indent=2, default=str))
    fields = [
        "item_id", "stage", "condition", "seed", "category", "layer", "layer_detail",
        "n_compile_ok", "n_compile_fail", "n_zero", "n_nonzero", "n_unknown",
        "old_certified",
    ]
    with CSV_PATH.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return rows


if __name__ == "__main__":
    rows = run()
    from collections import Counter
    print("n", len(rows))
    print("layer", Counter(r["layer"] for r in rows))
    guo = [r for r in rows if r["item_id"] == "guo-sigma-abc"]
    print("guo", len(guo))
    for r in guo:
        print(r["condition"], "s"+str(r["seed"]), "layer", r["layer"],
              "G1", (r.get("G1") or {}).get("pass"),
              "G2", (r.get("G2") or {}).get("pass"),
              "G3", (r.get("G3") or {}).get("pass"),
              "G4", (r.get("G4") or {}).get("pass"),
              "G1types", (r.get("G1") or {}).get("types"),
              "Cok", r["n_compile_ok"], "Cfail", r["n_compile_fail"],
              "Z", r["n_zero"])
    t7 = [r for r in rows if r.get("item_id") == "T7-pos-swap"]
    print("T7 layers", Counter(r["layer"] for r in t7), "n", len(t7))
    t1 = [r for r in rows if r.get("item_id") == "A-pos-born"]
    print("T1 layers", Counter((r["condition"], r["layer"]) for r in t1))
