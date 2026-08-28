"""Freeze V3's 7 Guo families as V4 inputs. No LLM. No run rewrite."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
V3 = ROOT / "research" / "iterated_confluence" / "FROZEN_INPUTS_V3.json"
V3_RESCORE = ROOT / "research" / "iterated_confluence" / "GUO_ITERATED_RESCORE.json"
OUT = HERE / "FROZEN_INPUTS_V4.json"

PARENT_V3_CLOSE = "d2752f9"
PARENT_V3_FREEZE = "dcfb90c"


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build() -> dict:
    v3 = json.loads(V3.read_text())
    rescore = json.loads(V3_RESCORE.read_text()) if V3_RESCORE.is_file() else {}
    by = {r["family_id"]: r for r in rescore.get("rows") or []}
    hyps = []
    for h in v3["hypotheses"]:
        row = by.get(h["family_id"]) or {}
        rec = dict(h)
        rec["v3_family_verdict"] = row.get("family_verdict") or "FAMILY_UNKNOWN"
        rec["v3_n_zero_edges"] = row.get("n_zero_edges")
        rec["v3_n_unknown_edges"] = row.get("n_unknown_edges")
        rec["v3_unknown_reason"] = (
            "atom-scale polygamma series not attempted; whole-kernel timeout"
        )
        hyps.append(rec)
    return {
        "track": "V4",
        "no_llm_calls": True,
        "no_new_hypotheses": True,
        "parent_track_v3_close": PARENT_V3_CLOSE,
        "parent_track_v3_freeze": PARENT_V3_FREEZE,
        "v3_freeze_sha256": _sha(V3),
        "n_hypotheses": len(hyps),
        "family_ids": [h["family_id"] for h in hyps],
        "blocking_hop_class": "diagonal_to_triple_one_parameter",
        "hypotheses": hyps,
    }


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    print("wrote", OUT, "n", blob["n_hypotheses"])


if __name__ == "__main__":
    main()
