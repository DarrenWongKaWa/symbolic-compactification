"""Freeze the 7 Track-V2 Guo families as Track V3 inputs. No LLM. No run rewrite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V2_FREEZE = ROOT / "research" / "multibranch_verification" / "FROZEN_INPUTS_V2.json"
V2_GRAPHS = ROOT / "research" / "multibranch_verification" / "graph" / "BRANCH_GRAPHS.json"
V2_RESCORE = ROOT / "research" / "multibranch_verification" / "GUO_FAMILY_RESCORE.json"
V_RESCORE = ROOT / "research" / "scalable_verification" / "FROZEN_RESCORE.json"
OUT = HERE / "FROZEN_INPUTS_V3.json"

PARENT_V = "38d6d4a"
PARENT_V2_FREEZE = "4dee916"
PARENT_V2_CLOSE = "fe53ebc"

# Track V / V2 documented pairwise ZEROs. Not inferred from V3 methods.
KNOWN_ZERO_PAIRWISE = {
    "guo-p2-s2-i4": [
        {
            "source": "G0005",
            "target": "G0004",
            "relation": "one_parameter_confluence",
            "variable": "epsilon(m)",
            "target_value": "epsilon(n)",
            "authority": "38d6d4a+fe53ebc",
            "note": "two-member spectator-factor + series; Track V V_GAIN",
        },
        {
            "source": "G0009",
            "target": "G0008",
            "relation": "one_parameter_confluence",
            "variable": "epsilon(m)",
            "target_value": "epsilon(n)",
            "authority": "38d6d4a+fe53ebc",
            "note": "two-member spectator-factor + series; Track V V_GAIN",
        },
    ],
}

V2_UNKNOWN_REASON = {
    "guo-p2-s2-i4": (
        "2 ZERO one-parameter edges + 1 UNKNOWN substitution; "
        "composition forbids FAMILY_ZERO"
    ),
}


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_file(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _file_sha_or_empty(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        return ""
    return _sha_file(p)


def build() -> dict[str, Any]:
    v2 = json.loads(V2_FREEZE.read_text())
    graphs = json.loads(V2_GRAPHS.read_text())
    rescore = json.loads(V2_RESCORE.read_text())
    by_graph = {f["family_id"]: f for f in graphs.get("families") or []}
    by_row = {r["family_id"]: r for r in rescore.get("rows") or []}

    hyps = []
    for hyp in v2.get("hypotheses") or []:
        fid = hyp["family_id"]
        g = by_graph.get(fid) or {}
        row = by_row.get(fid) or {}
        members = list(hyp.get("members") or [])
        op_counts = {m["member_id"]: m.get("ops") for m in members}
        conds = {m["member_id"]: m.get("cond") for m in members}
        source_path = hyp.get("source_path") or ""
        disk_sha = _file_sha_or_empty(source_path)
        record = {
            "family_id": fid,
            "source_path": source_path,
            "source_sha256": hyp.get("source_sha256"),
            "source_sha256_on_disk": disk_sha,
            "source_sha_match": bool(disk_sha) and disk_sha == hyp.get("source_sha256"),
            "seed": hyp.get("seed"),
            "index": hyp.get("index"),
            "claimed_type": hyp.get("claimed_type"),
            "member_ids": list(hyp.get("member_ids") or []),
            "n_members": hyp.get("n_members"),
            "operators": hyp.get("operators"),
            "reconstruction_rule": hyp.get("reconstruction_rule"),
            "members": members,
            "parent_sum_gid": hyp.get("parent_sum_gid"),
            "branch_conditions": conds,
            "op_counts": op_counts,
            "generic_members": list(g.get("generic_members") or []),
            "degenerate_members": list(g.get("degenerate_members") or []),
            "degeneracy_variables": list(g.get("degeneracy_variables") or []),
            "node_multiplicities": dict(g.get("node_multiplicities") or {}),
            "v2_local_edges": list(g.get("local_edges") or []),
            "v2_family_verdict": row.get("family_verdict") or "FAMILY_UNKNOWN",
            "v2_n_zero_edges": row.get("n_zero_edges"),
            "v2_n_nonzero_edges": row.get("n_nonzero_edges"),
            "v2_n_unknown_edges": row.get("n_unknown_edges"),
            "v2_recurrence": row.get("recurrence"),
            "v2_bottleneck": row.get("bottleneck") or "V",
            "v2_connected": row.get("connected"),
            "previous_compiler_state": hyp.get("previous_layer"),
            "previous_verifier_verdict": hyp.get("previous_verdict"),
            "old_unknown_reason": hyp.get("old_unknown_reason"),
            "v2_unknown_reason": V2_UNKNOWN_REASON.get(
                fid,
                "ops_skip on 573-op generic kernels; 2-parameter star edge; "
                "no iterated 1-parameter path; recurrence without explicit F",
            ),
            "known_zero_pairwise_edges": list(KNOWN_ZERO_PAIRWISE.get(fid) or []),
        }
        hyps.append(record)

    blob = {
        "track": "V3",
        "no_llm_calls": True,
        "no_new_hypotheses": True,
        "parent_track_v": PARENT_V,
        "parent_track_v2_freeze": PARENT_V2_FREEZE,
        "parent_track_v2_close": PARENT_V2_CLOSE,
        "v2_freeze_path": str(V2_FREEZE.relative_to(ROOT)),
        "v2_freeze_sha256": _sha_file(V2_FREEZE),
        "v2_graphs_sha256": _sha_file(V2_GRAPHS),
        "v2_rescore_sha256": _sha_file(V2_RESCORE),
        "n_hypotheses": len(hyps),
        "v2_n_hypotheses": v2.get("n_hypotheses"),
        "family_ids": [h["family_id"] for h in hyps],
        "hypotheses": hyps,
    }
    blob["blob_content_sha256"] = _sha_text(
        json.dumps({k: blob[k] for k in blob if k != "blob_content_sha256"}, sort_keys=True)
    )
    return blob


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    print("wrote", OUT, "n", blob["n_hypotheses"], "sha", blob["blob_content_sha256"][:16])


if __name__ == "__main__":
    main()
