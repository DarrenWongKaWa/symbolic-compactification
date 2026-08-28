"""Freeze 5-branch / Hermite Guo P2 hypotheses. No LLM. No run rewrite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
RESCORE = ROOT / "research" / "scalable_verification" / "FROZEN_RESCORE.json"
OUT = Path(__file__).resolve().parent / "FROZEN_INPUTS_V2.json"


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _keep(hyp: dict, row: dict | None) -> bool:
    n = len(hyp.get("member_ids") or [])
    t = hyp.get("claimed_type") or ""
    if t == "hermite_divided_difference":
        return True
    if t == "local_confluence" and n >= 4:
        return True
    if row and row.get("new") == "UNKNOWN" and t == "local_confluence" and n >= 4:
        return True
    return False


def build() -> dict:
    mblob = json.loads(MAP.read_text())
    rblob = json.loads(RESCORE.read_text())
    by = {(r["seed"], r["index"]): r for r in rblob.get("rows") or []}
    hyps = []
    for hyp in mblob.get("hypotheses") or []:
        key = (hyp.get("seed"), hyp.get("index"))
        row = by.get(key)
        if not _keep(hyp, row):
            continue
        members = []
        for m in hyp.get("members") or []:
            text = m.get("text") or ""
            members.append({
                "member_id": m.get("member_id"),
                "kind": m.get("kind"),
                "cond": m.get("cond"),
                "ops": m.get("ops"),
                "parent_gid": m.get("parent_gid"),
                "parent_sum_gid": m.get("parent_sum_gid"),
                "text_sha256": _sha(text),
                "text_len": len(text),
                # full text lives in GUO_OBLIGATION_MAP.json; do not duplicate
            })
        hyps.append({
            "family_id": f"guo-p2-s{hyp.get('seed')}-i{hyp.get('index')}",
            "source_path": hyp.get("source_path"),
            "source_sha256": hyp.get("source_sha256"),
            "seed": hyp.get("seed"),
            "index": hyp.get("index"),
            "claimed_type": hyp.get("claimed_type"),
            "member_ids": hyp.get("member_ids"),
            "operators": hyp.get("operators"),
            "reconstruction_rule": hyp.get("reconstruction_rule"),
            "members": members,
            "parent_sum_gid": hyp.get("parent_sum_gid"),
            "previous_verdict": (row or {}).get("new") or "UNKNOWN",
            "previous_gain": (row or {}).get("gain"),
            "previous_layer": (row or {}).get("layer"),
            "old_unknown_reason": (row or {}).get("note"),
            "n_members": len(hyp.get("member_ids") or []),
        })
    return {
        "track": "V2",
        "no_llm_calls": True,
        "parent_track_v": "38d6d4a",
        "source_map": str(MAP.relative_to(ROOT)),
        "n_hypotheses": len(hyps),
        "hypotheses": hyps,
    }


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    print("wrote", OUT, "n", blob["n_hypotheses"])


if __name__ == "__main__":
    main()
