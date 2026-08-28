"""Rescore frozen 5-branch covering hops with atom-series. No LLM."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import sympy

from research.iterated_confluence.compose import compose_path
from research.iterated_confluence.schema import (
    CONSISTENCY_UNKNOWN,
    PathStep,
    compose_family_verdict,
)
from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item
from research.polygamma_confluence.engine import atom_series_confluence
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
FREEZE = HERE / "FROZEN_INPUTS_V4.json"
PATHS = ROOT / "research" / "iterated_confluence" / "paths" / "PATH_CANDIDATES.json"
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT_JSON = HERE / "GUO_HOP_RESCORE.json"
OUT_CSV = HERE / "GUO_HOP_RESCORE.csv"
OUT_MD = HERE / "GUO_HOP_RESCORE.md"

EDGE_SECONDS = 30.0


def _eps(token: str) -> sympy.Expr:
    raw = (token or "").strip()
    if raw.startswith("epsilon(") and raw.endswith(")"):
        name = raw[len("epsilon(") : -1]
        return sympy.Function("epsilon")(sympy.Symbol(name, real=True))
    return sympy.Function("epsilon")(sympy.Symbol(raw, real=True))


def _job(A, B, var, point):
    r = atom_series_confluence(A, B, var, point)
    return r.to_dict()


def _budgeted(A, B, var, point) -> dict[str, Any]:
    try:
        return run_with_budget(
            _job, args=(A, B, var, point), seconds=EDGE_SECONDS,
            operation="v4_atom_series", mode="process",
        )
    except BudgetExceeded:
        return {"verdict": "UNKNOWN", "provenance": "timeout", "steps": ["timeout"]}
    except Exception as exc:
        return {"verdict": "UNKNOWN", "provenance": f"error:{type(exc).__name__}"}


def rescore() -> dict[str, Any]:
    item = load_guo_item()
    freeze = json.loads(FREEZE.read_text())
    paths_blob = json.loads(PATHS.read_text())
    mmap = json.loads(MAP.read_text())
    by_si = {(h["seed"], h["index"]): h for h in mmap.get("hypotheses") or []}
    by_paths = {f["family_id"]: f for f in paths_blob.get("families") or []}
    cache: dict[tuple, dict[str, Any]] = {}
    edge_rows = []
    family_rows = []

    for hyp in freeze["hypotheses"]:
        fid = hyp["family_id"]
        src = by_si[(hyp["seed"], hyp["index"])]
        texts = {m["member_id"]: m for m in src.get("members") or []}
        parsed: dict[str, Any] = {}

        def expr_of(gid: str):
            if gid not in parsed:
                parsed[gid] = parse_flex(
                    texts[gid]["text"], item["symbols"], item["functions"],
                )
            return parsed[gid]

        fam = by_paths[fid]
        unique = []
        seen = set()
        for p in fam.get("paths") or []:
            for st in p.get("steps") or []:
                k = (st["source"], st["target"], st.get("variable"), st.get("target_value"))
                if k in seen:
                    continue
                seen.add(k)
                unique.append(st)

        edge_v: dict[tuple, dict[str, Any]] = {}
        for st in unique:
            def _tsha(gid: str) -> str:
                return hashlib.sha256((texts[gid].get("text") or "").encode()).hexdigest()

            key = (
                _tsha(st["source"]),
                _tsha(st["target"]),
                st.get("variable"),
                st.get("target_value"),
            )
            if key not in cache:
                A, B = expr_of(st["source"]), expr_of(st["target"])
                if A is None or B is None:
                    cache[key] = {"verdict": "UNKNOWN", "provenance": "unparseable"}
                else:
                    cache[key] = _budgeted(
                        A, B, _eps(st.get("variable") or ""), _eps(st.get("target_value") or ""),
                    )
            cert = cache[key]
            edge_v[(st["source"], st["target"], st.get("variable"), st.get("target_value"))] = cert
            edge_rows.append({
                "family_id": fid,
                "source": st["source"],
                "target": st["target"],
                "variable": st.get("variable"),
                "target_value": st.get("target_value"),
                "verdict": cert.get("verdict"),
                "provenance": cert.get("provenance"),
                "n_atoms": cert.get("n_atoms"),
                "c0_ops": cert.get("c0_ops"),
                "together_ops": cert.get("together_ops"),
            })

        path_rows = []
        for p in fam.get("paths") or []:
            steps = [
                PathStep(
                    source=st["source"], target=st["target"],
                    variable=st.get("variable") or "",
                    target_value=st.get("target_value") or "",
                    verdict=edge_v[(st["source"], st["target"], st.get("variable"), st.get("target_value"))]["verdict"],
                    provenance=edge_v[(st["source"], st["target"], st.get("variable"), st.get("target_value"))].get("provenance") or "",
                )
                for st in p.get("steps") or []
            ]
            pc = compose_path(steps, path_id=p["path_id"], start=p["start_member"], end=p["end_member"])
            path_rows.append(pc)

        covering = [p for p in path_rows if len(p.steps) >= 2] or path_rows
        # R2: do not auto CONSISTENT_ZERO from shared endpoints.
        cons = [CONSISTENCY_UNKNOWN] if len(covering) > 1 else []
        require_ind = bool(cons)
        fam_v = compose_family_verdict(
            path_verdicts=[p.path_verdict for p in covering],
            consistency_verdicts=cons,
            reconstruction_verdicts=["ZERO"],
            require_path_independence=require_ind,
        )
        n_z = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "ZERO")
        n_nz = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "NONZERO")
        n_u = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "UNKNOWN")
        family_rows.append({
            "family_id": fid,
            "n_members": hyp["n_members"],
            "claimed_type": hyp["claimed_type"],
            "n_zero_edges": n_z,
            "n_nonzero_edges": n_nz,
            "n_unknown_edges": n_u,
            "n_path_zero": sum(1 for p in path_rows if p.path_verdict == "PATH_ZERO"),
            "family_verdict": fam_v,
        })

    n_fz = sum(1 for r in family_rows if r["family_verdict"] == "FAMILY_ZERO")
    n_fn = sum(1 for r in family_rows if r["family_verdict"] == "FAMILY_NONZERO")
    n_fu = sum(1 for r in family_rows if r["family_verdict"] == "FAMILY_UNKNOWN")
    n_diag_z = sum(1 for e in edge_rows if e["verdict"] == "ZERO")
    if n_fz:
        case = "J-A"
    elif n_fn:
        case = "J-B"
    elif n_diag_z:
        case = "J-C"
    else:
        case = "J-D"
    report = {
        "n_families": len(family_rows),
        "FAMILY_ZERO": n_fz,
        "FAMILY_NONZERO": n_fn,
        "FAMILY_UNKNOWN": n_fu,
        "n_zero_edges": n_diag_z,
        "case": case,
        "rows": family_rows,
        "edges": edge_rows,
        "no_llm": True,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(family_rows[0].keys()) if family_rows else ["family_id"])
        w.writeheader()
        for r in family_rows:
            w.writerow(r)
    lines = [
        "# Guo hop rescore — atom-series polygamma confluence",
        "",
        f"FAMILY_ZERO={n_fz} FAMILY_NONZERO={n_fn} FAMILY_UNKNOWN={n_fu} ZERO_edges={n_diag_z}",
        f"case: **{case}**",
        "",
        "| family | ZERO | UNK | NZ | PATH_ZERO | family |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for r in family_rows:
        lines.append(
            f"| {r['family_id']} | {r['n_zero_edges']} | {r['n_unknown_edges']} | "
            f"{r['n_nonzero_edges']} | {r['n_path_zero']} | {r['family_verdict']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = rescore()
    print(json.dumps({k: rep[k] for k in ("n_families", "FAMILY_ZERO", "FAMILY_NONZERO", "FAMILY_UNKNOWN", "n_zero_edges", "case")}))
