"""Evaluate atom decomposition on frozen V5 hops. Does not adjudicate ZERO.

Reads full member texts from GUO_OBLIGATION_MAP.json. No LLM. No identities.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.coefficient_laurent.atoms.core import (
    AtomDecomposition,
    decompose,
    sha256_text,
)
from research.coefficient_laurent.schema import METHOD_VERSION
from research.llm_abstraction.constructor import parse_flex
from research.llm_abstraction.tasks import load_guo_item

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
FREEZE = ROOT / "research" / "coefficient_laurent" / "FROZEN_INPUTS_V5.json"
MAP = (
    ROOT
    / "research"
    / "scalable_verification"
    / "guo_map"
    / "GUO_OBLIGATION_MAP.json"
)
OUT = HERE / "ATOM_MAP.json"


def build() -> dict[str, Any]:
    freeze = json.loads(FREEZE.read_text())
    mmap = json.loads(MAP.read_text())
    item = load_guo_item()
    by_si = {(h.get("seed"), h.get("index")): h for h in mmap.get("hypotheses") or []}
    hops: list[dict[str, Any]] = []
    for hop in freeze.get("hops") or []:
        hops.append(_eval_hop(hop, by_si, item))
    n_ok = sum(1 for h in hops if h.get("reconstruction_ok"))
    return {
        "track": "V5",
        "artifact": "ATOM_MAP",
        "method_version": METHOD_VERSION,
        "no_llm_calls": True,
        "does_not_adjudicate_zero": True,
        "used_full_together": False,
        "n_hops": len(hops),
        "n_reconstruction_ok": n_ok,
        "primary_hop": freeze.get("primary_hop") or "",
        "hops": hops,
    }


def _eval_hop(
    hop: dict[str, Any],
    by_si: dict[tuple[Any, Any], dict[str, Any]],
    item: dict[str, Any],
) -> dict[str, Any]:
    src_id = hop["source_member"]
    tgt_id = hop["target_member"]
    var = hop["degeneration_variable"]
    point = hop["target_value"]
    row = by_si.get((hop.get("seed"), hop.get("index"))) or {}
    members = {m["member_id"]: m for m in row.get("members") or []}
    src_text = (members.get(src_id) or {}).get("text") or ""
    tgt_text = (members.get(tgt_id) or {}).get("text") or ""
    src_hash = sha256_text(src_text)
    tgt_hash = sha256_text(tgt_text)
    freeze_src = (hop.get("source") or {}).get("text_sha256") or ""
    freeze_tgt = (hop.get("target") or {}).get("text_sha256") or ""
    if not src_text:
        return _hop_record(hop, src_hash, tgt_hash, None, note="missing_source_text")
    source = parse_flex(src_text, item["symbols"], item["functions"])
    target = parse_flex(tgt_text, item["symbols"], item["functions"]) if tgt_text else None
    if source is None:
        return _hop_record(hop, src_hash, tgt_hash, None, note="unparseable_source")
    if freeze_src and freeze_src != src_hash:
        note = "source_hash_mismatch"
    else:
        note = ""
    out = decompose(
        source,
        var,
        point,
        src_id,
        src_hash,
        partner=target,
    )
    rec = _hop_record(hop, src_hash, tgt_hash, out, note=note or out.note)
    rec["freeze_source_text_hash"] = freeze_src
    rec["freeze_target_text_hash"] = freeze_tgt
    rec["target_text_hash_match"] = (not freeze_tgt) or freeze_tgt == tgt_hash
    rec["source_text_hash_match"] = (not freeze_src) or freeze_src == src_hash
    return rec


def _hop_record(
    hop: dict[str, Any],
    src_hash: str,
    tgt_hash: str,
    out: AtomDecomposition | None,
    *,
    note: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "hop_id": hop.get("hop_id"),
        "family_id": hop.get("family_id"),
        "seed": hop.get("seed"),
        "index": hop.get("index"),
        "source_member": hop.get("source_member"),
        "target_member": hop.get("target_member"),
        "degeneration_variable": hop.get("degeneration_variable"),
        "target_value": hop.get("target_value"),
        "is_primary": bool(hop.get("is_primary")),
        "source_text_hash": src_hash,
        "target_text_hash": tgt_hash,
        "note": note,
    }
    if out is None:
        payload.update(
            {
                "spectator": "1",
                "pref": "1",
                "pref_srepr": "Integer(1)",
                "n_atoms": 0,
                "atom_classes": {},
                "reconstruction_ok": False,
                "atom_decomposition_hash": "",
                "split_note": "",
                "atoms": [],
            }
        )
        return payload
    blob = out.to_dict()
    payload.update(
        {
            "spectator": blob["spectator"],
            "pref": blob["pref"],
            "pref_srepr": blob["pref_srepr"],
            "n_atoms": blob["n_atoms"],
            "atom_classes": blob["atom_classes"],
            "reconstruction_ok": blob["reconstruction_ok"],
            "atom_decomposition_hash": blob["atom_decomposition_hash"],
            "split_note": blob["split_note"],
            "atoms": blob["atoms"],
        }
    )
    return payload


def main() -> None:
    blob = build()
    OUT.write_text(json.dumps(blob, indent=2) + "\n")
    classes: Counter[str] = Counter()
    for hop in blob["hops"]:
        for cls, n in (hop.get("atom_classes") or {}).items():
            classes[cls] += int(n)
    print(
        "wrote",
        OUT,
        "n_hops",
        blob["n_hops"],
        "reconstruction_ok",
        blob["n_reconstruction_ok"],
        "classes",
        dict(classes),
    )


if __name__ == "__main__":
    main()
