"""Rescore frozen generic→diagonal hops with sparse Laurent. No LLM."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import sympy

from research.coefficient_laurent.cache import CertificateCache, certificate_key
from research.coefficient_laurent.engine import sparse_laurent_limit
from research.coefficient_laurent.freeze_v5 import OUT as FREEZE
from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item
from research.iterated_confluence.compose import compose_path
from research.iterated_confluence.schema import CONSISTENCY_UNKNOWN, PathStep, compose_family_verdict
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget

ROOT = Path(__file__).resolve().parents[3]
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
PATHS = ROOT / "research" / "iterated_confluence" / "paths" / "PATH_CANDIDATES.json"
HERE = Path(__file__).resolve().parents[1]
OUT_JSON = HERE / "GUO_V5_RESCORE.json"
OUT_CSV = HERE / "GUO_V5_RESCORE.csv"
OUT_MD = HERE / "GUO_V5_RESCORE.md"
V4_HOPS = ROOT / "research" / "polygamma_confluence" / "GUO_HOP_RESCORE.json"

EDGE_SECONDS = 40.0


def _eps(token: str) -> sympy.Expr:
    raw = (token or "").strip()
    if raw.startswith("epsilon(") and raw.endswith(")"):
        name = raw[len("epsilon("):-1]
        return sympy.Function("epsilon")(sympy.Symbol(name, real=True))
    return sympy.Function("epsilon")(sympy.Symbol(raw, real=True))


def _job(A, B, var, point, src_t, tgt_t, sm, tm):
    return sparse_laurent_limit(
        A, B, var, point, source_text=src_t, target_text=tgt_t,
        source_member=sm, target_member=tm,
    ).to_dict()


def rescore() -> dict:
    item = load_guo_item()
    freeze = json.loads(FREEZE.read_text())
    mmap = json.loads(MAP.read_text())
    by_si = {(h.get("seed"), h.get("index")): h for h in mmap.get("hypotheses") or []}
    cache = CertificateCache()
    hop_rows = []
    for hop in freeze["hops"]:
        src_row = by_si[(hop["seed"], hop["index"])]
        mem = {m["member_id"]: m for m in src_row.get("members") or []}
        src_t = mem[hop["source_member"]]["text"]
        tgt_t = mem[hop["target_member"]]["text"]
        key = certificate_key(
            source_text=src_t,
            target_text=tgt_t,
            degeneration_variable=hop["degeneration_variable"],
            target_value=hop["target_value"],
            atom_decomposition_hash=hop["source"]["text_sha256"] + hop["target"]["text_sha256"],
            source_member=hop["source"],
            target_member=hop["target"],
        )
        existing = cache.get(key)
        if existing is None:
            A = parse_flex(src_t, item["symbols"], item["functions"])
            B = parse_flex(tgt_t, item["symbols"], item["functions"])
            try:
                existing = run_with_budget(
                    _job,
                    args=(A, B, _eps(hop["degeneration_variable"]), _eps(hop["target_value"]),
                          src_t, tgt_t, hop["source_member"], hop["target_member"]),
                    seconds=EDGE_SECONDS, operation="v5_sparse", mode="process",
                )
            except BudgetExceeded:
                existing = {
                    "final_verdict": "UNKNOWN",
                    "proof_level": "LEVEL_A",
                    "provenance": "timeout",
                    "negative_coefficients_verdict": "UNKNOWN",
                    "constant_term_verdict": "UNKNOWN",
                    "remainder_verdict": "UNKNOWN",
                    "used_full_together": False,
                }
            except Exception as exc:
                existing = {
                    "final_verdict": "UNKNOWN",
                    "proof_level": "LEVEL_A",
                    "error": type(exc).__name__,
                    "negative_coefficients_verdict": "UNKNOWN",
                    "constant_term_verdict": "UNKNOWN",
                    "remainder_verdict": "UNKNOWN",
                    "used_full_together": False,
                }
            cache.put(key, existing)
        hop_rows.append({
            "hop_id": hop["hop_id"],
            "family_id": hop["family_id"],
            "source": hop["source_member"],
            "target": hop["target_member"],
            "is_primary": hop.get("is_primary"),
            "verdict": existing.get("final_verdict"),
            "level": existing.get("proof_level"),
            "neg": existing.get("negative_coefficients_verdict"),
            "c0": existing.get("constant_term_verdict"),
            "remainder": existing.get("remainder_verdict"),
            "max_ops": existing.get("max_intermediate_ops"),
            "together": existing.get("used_full_together"),
            "v4": hop.get("v4_verdict"),
        })

    n_z = sum(1 for r in hop_rows if r["verdict"] == "ZERO")
    n_nz = sum(1 for r in hop_rows if r["verdict"] == "NONZERO")
    n_u = sum(1 for r in hop_rows if r["verdict"] == "UNKNOWN")
    primary = next(r for r in hop_rows if r.get("is_primary"))
    if primary["verdict"] == "ZERO":
        case = "L-A"
    elif primary["verdict"] == "NONZERO":
        case = "L-B" if primary.get("neg") == "NONZERO" else "L-C"
    else:
        case = "L-D"
    report = {
        "n_hops": len(hop_rows),
        "ZERO": n_z, "NONZERO": n_nz, "UNKNOWN": n_u,
        "case": case,
        "primary": primary,
        "rows": hop_rows,
        "no_llm": True,
    }

    # Family recompose using V4 ZERO edges + V5 hop verdicts
    v4 = json.loads(V4_HOPS.read_text()) if V4_HOPS.is_file() else {"edges": []}
    paths = json.loads(PATHS.read_text())
    v5_by = {(r["family_id"], r["source"], r["target"]): r["verdict"] for r in hop_rows}
    fam_rows = []
    for fam in paths.get("families") or []:
        fid = fam["family_id"]
        path_rows = []
        for p in fam.get("paths") or []:
            steps = []
            for st in p.get("steps") or []:
                key = (fid, st["source"], st["target"])
                if key in v5_by:
                    verd = v5_by[key]
                else:
                    verd = "UNKNOWN"
                    for e in v4.get("edges") or []:
                        if e.get("family_id") == fid and e.get("source") == st["source"] and e.get("target") == st["target"]:
                            verd = e.get("verdict") or "UNKNOWN"
                            break
                steps.append(PathStep(
                    source=st["source"], target=st["target"],
                    variable=st.get("variable") or "", target_value=st.get("target_value") or "",
                    verdict=verd,
                ))
            path_rows.append(compose_path(steps, path_id=p["path_id"], start=p["start_member"], end=p["end_member"]))
        covering = [p for p in path_rows if len(p.steps) >= 2] or path_rows
        # Never auto-CONSISTENT_ZERO (V3 R2). Never fake reconstruction ZERO (V5 R4).
        fam_v = compose_family_verdict(
            path_verdicts=[p.path_verdict for p in covering],
            consistency_verdicts=[CONSISTENCY_UNKNOWN],
            reconstruction_verdicts=["UNKNOWN"],
            require_path_independence=True,
        )
        fam_rows.append({
            "family_id": fid,
            "n_path_zero": sum(1 for p in path_rows if p.path_verdict == "PATH_ZERO"),
            "family_verdict": fam_v,
        })
    n_fz = sum(1 for r in fam_rows if r["family_verdict"] == "FAMILY_ZERO")
    report["families"] = fam_rows
    report["FAMILY_ZERO"] = n_fz
    report["FAMILY_NONZERO"] = sum(1 for r in fam_rows if r["family_verdict"] == "FAMILY_NONZERO")
    report["FAMILY_UNKNOWN"] = sum(1 for r in fam_rows if r["family_verdict"] == "FAMILY_UNKNOWN")
    report["d2_unlocked"] = n_fz > 0 or report["FAMILY_NONZERO"] > 0

    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(hop_rows[0].keys()))
        w.writeheader()
        for r in hop_rows:
            w.writerow(r)
    lines = [
        "# Track V5 generic→diagonal rescore",
        "",
        f"hops ZERO={n_z} NONZERO={n_nz} UNKNOWN={n_u} case **{case}**",
        f"primary {primary['hop_id']}: {primary['verdict']} ({primary['level']}) neg={primary['neg']} c0={primary['c0']}",
        f"FAMILY_ZERO={report['FAMILY_ZERO']} D2 unlocked={report['d2_unlocked']}",
        "",
        "| hop | verdict | level | neg | c0 | max_ops |",
        "|---|---|---|---|---|---:|",
    ]
    for r in hop_rows:
        lines.append(
            f"| {r['hop_id']} | {r['verdict']} | {r['level']} | {r['neg']} | {r['c0']} | {r['max_ops']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = rescore()
    print(json.dumps({k: rep[k] for k in ("n_hops", "ZERO", "NONZERO", "UNKNOWN", "case", "FAMILY_ZERO", "d2_unlocked")}))
