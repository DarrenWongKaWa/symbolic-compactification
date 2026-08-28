"""Rescore frozen Guo 5-branch/Hermite families. No LLM. No run rewrite."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item
from research.multibranch_verification.compose import certify_family
from research.multibranch_verification.edges import certify_edge
from research.multibranch_verification.schema import LocalEdge

ROOT = Path(__file__).resolve().parents[2]
GRAPHS = ROOT / "multibranch_verification" / "graph" / "BRANCH_GRAPHS.json"
MAP = ROOT / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT_CSV = ROOT / "multibranch_verification" / "GUO_FAMILY_RESCORE.csv"
OUT_MD = ROOT / "multibranch_verification" / "GUO_FAMILY_RESCORE.md"
OUT_JSON = ROOT / "multibranch_verification" / "GUO_FAMILY_RESCORE.json"

OPS_SKIP = 250


def _texts(seed, index, mmap):
    for h in mmap["hypotheses"]:
        if h.get("seed") == seed and h.get("index") == index:
            return {m["member_id"]: m for m in h.get("members") or []}
    return {}


def rescore() -> dict:
    item = load_guo_item()
    graphs = json.loads(GRAPHS.read_text())
    mmap = json.loads(MAP.read_text())
    rows = []
    for fam in graphs.get("families") or []:
        fid = fam["family_id"]
        # parse seed/index from family_id guo-p2-s0-i3
        seed = fam.get("seed")
        index = fam.get("index")
        if seed is None:
            parts = fid.replace("guo-p2-s", "").split("-i")
            seed, index = int(parts[0]), int(parts[1])
        mem = _texts(seed, index, mmap)
        edges_out = []
        n_z = n_nz = n_u = 0
        for e in fam.get("local_edges") or []:
            src, tgt = e["source"], e["target"]
            sm, tm = mem.get(src) or {}, mem.get(tgt) or {}
            sops = int(sm.get("ops") or 0)
            tops = int(tm.get("ops") or 0)
            if max(sops, tops) > OPS_SKIP:
                verdict, prov = "UNKNOWN", f"ops_skip:{max(sops, tops)}"
            else:
                A = parse_flex(sm.get("text") or "", item["symbols"], item["functions"])
                B = parse_flex(tm.get("text") or "", item["symbols"], item["functions"])
                if A is None or B is None:
                    verdict, prov = "UNKNOWN", "unparseable"
                else:
                    cert = certify_edge(
                        A, B, e.get("relation"), e.get("variable"),
                        e.get("target_value"), item["symbols"], item["functions"],
                    )
                    verdict, prov = cert.verdict, cert.provenance
            if verdict == "ZERO":
                n_z += 1
            elif verdict == "NONZERO":
                n_nz += 1
            else:
                n_u += 1
            edges_out.append(LocalEdge(
                src, tgt, e.get("relation") or "limit",
                e.get("variable") or "", e.get("target_value") or "",
                e.get("obligation_id") or "", verdict, prov,
            ))
        # no explicit latent F for frozen Guo 5-branch → recurrence UNKNOWN, not ZERO
        rec_v = ["UNKNOWN"] if any(
            "repeated" in (e.relation or "") or "hermite" in (e.relation or "")
            for e in edges_out
        ) else []
        fam_res = certify_family(
            member_ids=fam.get("member_ids") or [],
            edges=edges_out,
            recurrence_verdicts=rec_v,
            node_multiplicities=fam.get("node_multiplicities") or {},
            latent_compatible=True,
        )
        rows.append({
            "family_id": fid,
            "n_members": len(fam.get("member_ids") or []),
            "n_edges": len(edges_out),
            "n_zero_edges": n_z,
            "n_nonzero_edges": n_nz,
            "n_unknown_edges": n_u,
            "recurrence": rec_v[0] if rec_v else "n/a",
            "family_verdict": fam_res.family_verdict,
            "connected": fam_res.connected if hasattr(fam_res, "connected") else None,
            "bottleneck": "V" if fam_res.family_verdict == "FAMILY_UNKNOWN" else (
                "D" if fam_res.family_verdict == "FAMILY_NONZERO" else "OK"
            ),
        })
    n_fz = sum(1 for r in rows if r["family_verdict"] == "FAMILY_ZERO")
    n_fn = sum(1 for r in rows if r["family_verdict"] == "FAMILY_NONZERO")
    n_fu = sum(1 for r in rows if r["family_verdict"] == "FAMILY_UNKNOWN")
    report = {
        "n_families": len(rows),
        "FAMILY_ZERO": n_fz,
        "FAMILY_NONZERO": n_fn,
        "FAMILY_UNKNOWN": n_fu,
        "case": "H-A" if n_fz else ("H-B" if n_fn and not n_fz else "H-C"),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(report, indent=2, default=str) + "\n")
    with OUT_CSV.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["family_id"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    lines = [
        "# Guo 5-branch / Hermite family rescore",
        "",
        f"FAMILY_ZERO={n_fz} FAMILY_NONZERO={n_fn} FAMILY_UNKNOWN={n_fu}",
        f"case: **{report['case']}**",
        "",
        "| family | n | ZERO edges | UNK edges | NZ | recurrence | family |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['family_id']} | {r['n_members']} | {r['n_zero_edges']} | "
            f"{r['n_unknown_edges']} | {r['n_nonzero_edges']} | {r['recurrence']} | {r['family_verdict']} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n")
    return report


if __name__ == "__main__":
    rep = rescore()
    print(json.dumps({k: rep[k] for k in ("n_families", "FAMILY_ZERO", "FAMILY_NONZERO", "FAMILY_UNKNOWN", "case")}))
