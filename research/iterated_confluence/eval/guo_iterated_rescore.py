"""Rescore frozen Guo families via iterated one-parameter paths. No LLM."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import sympy

from research.iterated_confluence.compose import compose_path
from research.iterated_confluence.edges import certify_one_parameter
from research.iterated_confluence.schema import (
    CONSISTENT_ZERO,
    CONSISTENCY_UNKNOWN,
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    INCONSISTENT_NONZERO,
    PATH_NONZERO,
    PATH_ZERO,
    PathStep,
    compose_family_verdict,
)
from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item
from research.multibranch_verification.edges import certify_edge
from research.scalable_verification.api import UNKNOWN
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
FREEZE = HERE / "FROZEN_INPUTS_V3.json"
PATHS = HERE / "paths" / "PATH_CANDIDATES.json"
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT_JSON = HERE / "GUO_ITERATED_RESCORE.json"
OUT_CSV = HERE / "GUO_ITERATED_RESCORE.csv"
OUT_MD = HERE / "GUO_ITERATED_RESCORE.md"

EDGE_SECONDS = 25.0


def _eps(token: str) -> sympy.Expr:
    raw = (token or "").strip()
    if raw.startswith("epsilon(") and raw.endswith(")"):
        name = raw[len("epsilon(") : -1]
        return sympy.Function("epsilon")(sympy.Symbol(name, real=True))
    return sympy.Function("epsilon")(sympy.Symbol(raw, real=True))


def _edge_key(step: dict[str, Any], texts: dict[str, dict[str, Any]]) -> tuple:
    src = step["source"]
    tgt = step["target"]
    return (
        texts.get(src, {}).get("text_sha256") or src,
        texts.get(tgt, {}).get("text_sha256") or tgt,
        step.get("relation") or "",
        step.get("variable") or "",
        step.get("target_value") or "",
    )


def _certify_confluence(A, B, var, point, item) -> dict[str, Any]:
    r = certify_one_parameter(
        A, B, var, point, item["symbols"], item["functions"],
    )
    return {
        "verdict": r.verdict,
        "provenance": r.provenance,
        "full_ops": r.full_ops,
        "local_ops": r.local_ops,
        "reduction_ratio": r.reduction_ratio,
        "split_certified": r.split_certified,
        "steps": list(r.steps),
    }


def _certify_substitution(A, B, var, point, item) -> dict[str, Any]:
    r = certify_edge(
        A, B, "substitution", var, point, item["symbols"], item["functions"],
    )
    return {
        "verdict": r.verdict,
        "provenance": r.provenance,
        "full_ops": None,
        "local_ops": None,
        "reduction_ratio": None,
        "split_certified": False,
        "steps": list(r.steps),
    }


def _budgeted(fn, *args) -> dict[str, Any]:
    try:
        return run_with_budget(
            fn, args=args, seconds=EDGE_SECONDS, operation="v3_edge", mode="process",
        )
    except BudgetExceeded:
        return {
            "verdict": UNKNOWN,
            "provenance": "timeout",
            "full_ops": None,
            "local_ops": None,
            "reduction_ratio": None,
            "split_certified": False,
            "steps": ["timeout"],
        }
    except Exception as exc:
        return {
            "verdict": UNKNOWN,
            "provenance": f"error:{type(exc).__name__}",
            "full_ops": None,
            "local_ops": None,
            "reduction_ratio": None,
            "split_certified": False,
            "steps": [f"error:{type(exc).__name__}"],
        }


def _endpoint_consistency(path_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compare covering paths that share start and end.

    Two PATH_ZERO chains to the same source member do **not** prove that
    iterated limits commute or that a joint limit exists (e.g.
    ``xy/(x^2+y^2)``). Auto-CONSISTENT_ZERO is forbidden. A PATH_NONZERO
    path against a claimed common end is INCONSISTENT_NONZERO. Otherwise
    UNKNOWN until ``check_two_paths`` (or equivalent) decides.
    """
    by_ends: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for p in path_rows:
        key = (p["start_member"], p["end_member"])
        by_ends.setdefault(key, []).append(p)
    out = []
    for (start, end), group in sorted(by_ends.items()):
        if len(group) < 2:
            continue
        verdicts = [g["path_verdict"] for g in group]
        if any(v == PATH_NONZERO for v in verdicts):
            v = INCONSISTENT_NONZERO
        else:
            v = CONSISTENCY_UNKNOWN
        out.append({
            "start": start,
            "end": end,
            "n_paths": len(group),
            "verdict": v,
            "path_ids": [g["path_id"] for g in group],
        })
    return out


def rescore() -> dict[str, Any]:
    item = load_guo_item()
    freeze = json.loads(FREEZE.read_text())
    paths_blob = json.loads(PATHS.read_text())
    mmap = json.loads(MAP.read_text())
    by_si = {(h["seed"], h["index"]): h for h in mmap.get("hypotheses") or []}
    by_fam_paths = {f["family_id"]: f for f in paths_blob.get("families") or []}

    cache: dict[tuple, dict[str, Any]] = {}
    family_rows = []
    edge_rows = []

    for hyp in freeze["hypotheses"]:
        fid = hyp["family_id"]
        src = by_si[(hyp["seed"], hyp["index"])]
        texts = {m["member_id"]: m for m in src.get("members") or []}
        parsed: dict[str, Any] = {}

        def expr_of(gid: str):
            if gid in parsed:
                return parsed[gid]
            text = texts[gid]["text"]
            parsed[gid] = parse_flex(text, item["symbols"], item["functions"])
            return parsed[gid]

        fam_paths = by_fam_paths[fid]
        unique_steps: list[dict[str, Any]] = []
        seen = set()
        for p in fam_paths.get("paths") or []:
            for st in p.get("steps") or []:
                k = _edge_key(st, texts)
                if k in seen:
                    continue
                seen.add(k)
                unique_steps.append(st)
        for st in fam_paths.get("substitutions") or []:
            k = _edge_key(st, texts)
            if k in seen:
                continue
            seen.add(k)
            unique_steps.append(st)

        edge_verdicts: dict[tuple, dict[str, Any]] = {}
        for st in unique_steps:
            k = _edge_key(st, texts)
            if k not in cache:
                A = expr_of(st["source"])
                B = expr_of(st["target"])
                if A is None or B is None:
                    cache[k] = {
                        "verdict": UNKNOWN,
                        "provenance": "unparseable",
                        "full_ops": None,
                        "local_ops": None,
                        "reduction_ratio": None,
                        "split_certified": False,
                        "steps": ["parse"],
                    }
                else:
                    rel = st.get("relation") or "one_parameter_confluence"
                    var_s = st.get("variable") or ""
                    pt_s = st.get("target_value") or ""
                    if rel == "substitution":
                        var = sympy.Symbol(var_s, real=True) if var_s else None
                        point = sympy.Symbol(pt_s, real=True) if pt_s else None
                        cache[k] = _budgeted(
                            _certify_substitution, A, B, var, point, item,
                        )
                    else:
                        cache[k] = _budgeted(
                            _certify_confluence, A, B, _eps(var_s), _eps(pt_s), item,
                        )
            cert = cache[k]
            edge_verdicts[(st["source"], st["target"], st.get("variable"), st.get("target_value"))] = cert
            edge_rows.append({
                "family_id": fid,
                "source": st["source"],
                "target": st["target"],
                "relation": st.get("relation"),
                "variable": st.get("variable"),
                "target_value": st.get("target_value"),
                **{kk: cert.get(kk) for kk in (
                    "verdict", "provenance", "full_ops", "local_ops",
                    "reduction_ratio", "split_certified",
                )},
            })

        path_rows = []
        for p in fam_paths.get("paths") or []:
            steps = []
            for st in p.get("steps") or []:
                cert = edge_verdicts[
                    (st["source"], st["target"], st.get("variable"), st.get("target_value"))
                ]
                steps.append(PathStep(
                    source=st["source"],
                    target=st["target"],
                    variable=st.get("variable") or "",
                    target_value=st.get("target_value") or "",
                    verdict=cert["verdict"],
                    provenance=cert.get("provenance") or "",
                    relation=st.get("relation") or "one_parameter_confluence",
                    old_ops=cert.get("full_ops"),
                    local_ops=cert.get("local_ops"),
                ))
            pc = compose_path(
                steps,
                path_id=p["path_id"],
                start=p["start_member"],
                end=p["end_member"],
            )
            path_rows.append({
                "path_id": p["path_id"],
                "start_member": p["start_member"],
                "end_member": p["end_member"],
                "n_steps": len(steps),
                "path_verdict": pc.path_verdict,
                "step_verdicts": [s.verdict for s in steps],
            })

        cons = _endpoint_consistency(path_rows)
        covering = [pr for pr in path_rows if pr["n_steps"] >= 2]
        if not covering:
            covering = path_rows
        require_ind = any(int(c.get("n_paths") or 0) >= 2 for c in cons)
        sub_verdicts = [
            edge_verdicts[(s["source"], s["target"], s.get("variable"), s.get("target_value"))]["verdict"]
            for s in fam_paths.get("substitutions") or []
        ]
        fam_v = compose_family_verdict(
            path_verdicts=[pr["path_verdict"] for pr in covering],
            consistency_verdicts=[c["verdict"] for c in cons] if require_ind else [],
            reconstruction_verdicts=["ZERO"],
            required_edge_verdicts=sub_verdicts,
            require_path_independence=require_ind,
        )
        n_z = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "ZERO")
        n_nz = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "NONZERO")
        n_u = sum(1 for e in edge_rows if e["family_id"] == fid and e["verdict"] == "UNKNOWN")
        family_rows.append({
            "family_id": fid,
            "n_members": hyp["n_members"],
            "n_paths": len(path_rows),
            "n_covering_paths": len(covering),
            "n_zero_edges": n_z,
            "n_nonzero_edges": n_nz,
            "n_unknown_edges": n_u,
            "n_path_zero": sum(1 for p in path_rows if p["path_verdict"] == PATH_ZERO),
            "n_path_nonzero": sum(1 for p in path_rows if p["path_verdict"] == PATH_NONZERO),
            "consistency": cons[0]["verdict"] if cons else "n/a",
            "family_verdict": fam_v,
            "require_path_independence": require_ind,
            "claimed_type": hyp["claimed_type"],
        })

    n_fz = sum(1 for r in family_rows if r["family_verdict"] == FAMILY_ZERO)
    n_fn = sum(1 for r in family_rows if r["family_verdict"] == FAMILY_NONZERO)
    n_fu = sum(1 for r in family_rows if r["family_verdict"] == FAMILY_UNKNOWN)
    n_five_z = sum(
        1 for r in family_rows if r["n_members"] >= 5 and r["family_verdict"] == FAMILY_ZERO
    )
    if n_five_z:
        case = "I-A"
    elif n_fn:
        case = "I-B"
    elif any(r["n_zero_edges"] and r["consistency"] == CONSISTENCY_UNKNOWN for r in family_rows):
        case = "I-C"
    elif any(r["n_unknown_edges"] for r in family_rows):
        case = "I-D"
    else:
        case = "I-E"

    report = {
        "n_families": len(family_rows),
        "FAMILY_ZERO": n_fz,
        "FAMILY_NONZERO": n_fn,
        "FAMILY_UNKNOWN": n_fu,
        "case": case,
        "edge_seconds": EDGE_SECONDS,
        "rows": family_rows,
        "edges": edge_rows,
        "no_llm": True,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        fields = list(family_rows[0].keys()) if family_rows else ["family_id"]
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for r in family_rows:
            w.writerow(r)
    lines = [
        "# Guo iterated one-parameter rescore",
        "",
        f"FAMILY_ZERO={n_fz} FAMILY_NONZERO={n_fn} FAMILY_UNKNOWN={n_fu}",
        f"case: **{case}**",
        "",
        "| family | n | ZERO edges | UNK | NZ | PATH_ZERO | consistency | family |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for r in family_rows:
        lines.append(
            f"| {r['family_id']} | {r['n_members']} | {r['n_zero_edges']} | "
            f"{r['n_unknown_edges']} | {r['n_nonzero_edges']} | {r['n_path_zero']} | "
            f"{r['consistency']} | {r['family_verdict']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = rescore()
    print(json.dumps({
        k: rep[k] for k in (
            "n_families", "FAMILY_ZERO", "FAMILY_NONZERO", "FAMILY_UNKNOWN", "case",
        )
    }))
