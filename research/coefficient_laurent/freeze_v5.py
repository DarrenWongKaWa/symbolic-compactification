"""Freeze generic→diagonal hops. No LLM. No run rewrite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V4_FREEZE = ROOT / "research" / "polygamma_confluence" / "FROZEN_INPUTS_V4.json"
V4_RESCORE = ROOT / "research" / "polygamma_confluence" / "GUO_HOP_RESCORE.json"
MAP = ROOT / "research" / "scalable_verification" / "guo_map" / "GUO_OBLIGATION_MAP.json"
OUT = HERE / "FROZEN_INPUTS_V5.json"

PARENT_V4 = "248d247"
METHOD_VERSION = "v5-coeff-laurent-1"

# Frozen covering hops that V4 left UNKNOWN (generic → diagonal).
PRIMARY = ("G0016", "G0013", "epsilon(m)", "epsilon(n)")
SIBLINGS = (
    ("G0016", "G0014", "epsilon(ell)", "epsilon(n)"),
    ("G0016", "G0015", "epsilon(ell)", "epsilon(m)"),
    ("G0023", "G0020", "epsilon(m)", "epsilon(n)"),
    ("G0023", "G0021", "epsilon(ell)", "epsilon(n)"),
    ("G0023", "G0022", "epsilon(ell)", "epsilon(m)"),
)


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha_text(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _sha_file(p: Path) -> str:
    return _sha_bytes(p.read_bytes())


def _member_blob(m: dict[str, Any]) -> dict[str, Any]:
    text = m.get("text") or ""
    return {
        "member_id": m.get("member_id"),
        "kind": m.get("kind"),
        "cond": m.get("cond"),
        "ops": m.get("ops"),
        "parent_gid": m.get("parent_gid"),
        "parent_sum_gid": m.get("parent_sum_gid"),
        "text_len": len(text),
        "text_sha256": _sha_text(text),
        "stored_text_sha256": m.get("text_sha256") or "",
        # full text lives in GUO_OBLIGATION_MAP.json
    }


def build() -> dict[str, Any]:
    v4 = json.loads(V4_FREEZE.read_text())
    hops_json = json.loads(V4_RESCORE.read_text()) if V4_RESCORE.is_file() else {}
    mmap = json.loads(MAP.read_text())
    by_si = {(h.get("seed"), h.get("index")): h for h in mmap.get("hypotheses") or []}
    v4_edges = hops_json.get("edges") or []

    def v4_edge(fid: str, src: str, tgt: str) -> dict[str, Any]:
        for e in v4_edges:
            if e.get("family_id") == fid and e.get("source") == src and e.get("target") == tgt:
                return e
        return {}

    wanted = (PRIMARY,) + SIBLINGS
    hops = []
    for hyp in v4.get("hypotheses") or []:
        fid = hyp["family_id"]
        src_row = by_si.get((hyp.get("seed"), hyp.get("index"))) or {}
        mem = {m["member_id"]: m for m in src_row.get("members") or []}
        for src, tgt, var, point in wanted:
            if src not in mem or tgt not in mem:
                continue
            ve = v4_edge(fid, src, tgt)
            hops.append({
                "hop_id": f"{fid}:{src}->{tgt}",
                "family_id": fid,
                "seed": hyp.get("seed"),
                "index": hyp.get("index"),
                "source_member": src,
                "target_member": tgt,
                "degeneration_variable": var,
                "target_value": point,
                "source": _member_blob(mem[src]),
                "target": _member_blob(mem[tgt]),
                "v4_verdict": ve.get("verdict") or "UNKNOWN",
                "v4_provenance": ve.get("provenance") or "",
                "v4_together_ops": ve.get("together_ops"),
                "old_unknown_reason": ve.get("provenance") or "together_or_timeout",
                "is_primary": (src, tgt, var, point) == PRIMARY and fid == "guo-p2-s0-i3",
            })
    return {
        "track": "V5",
        "no_llm_calls": True,
        "no_new_hypotheses": True,
        "parent_track_v4": PARENT_V4,
        "method_version": METHOD_VERSION,
        "v4_freeze_sha256": _sha_file(V4_FREEZE),
        "v4_rescore_sha256": _sha_file(V4_RESCORE) if V4_RESCORE.is_file() else "",
        "primary_hop": "guo-p2-s0-i3:G0016->G0013",
        "n_hops": len(hops),
        "hops": hops,
    }


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    print("wrote", OUT, "n", blob["n_hops"])


if __name__ == "__main__":
    main()
