"""Map frozen Guo P2 hypotheses to local source members.

Evaluation-only. Reads frozen run JSON; does not rewrite it, call an LLM,
or adjudicate whether a claim is true.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from research.obligation_ir.source_index import SourceIndex
from research.representation_invention.guo.catalog import load_guo_catalog
from research.representation_invention.schema import is_catalog_id

ROOT = Path(__file__).resolve().parents[3]
P2_DIR = ROOT / "research" / "representation_invention" / "llm" / "runs"
P2_GLOB = "guo-sigma-abc__P2__s*.json"
MAP_PATH = Path(__file__).resolve().parent / "GUO_OBLIGATION_MAP.json"

# Same slice as freeze_inputs._hyp_record reconstruction_rule.
RECONSTRUCTION_CAP = 240


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _truncate(text: str, cap: int = RECONSTRUCTION_CAP) -> str:
    return (text or "")[:cap]


def _copy_operators(ops: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for o in ops or []:
        if not isinstance(o, dict):
            continue
        rec: dict[str, Any] = {
            "member_id": str(o.get("member_id") or o.get("member") or ""),
            "kind": str(o.get("kind") or o.get("O") or ""),
        }
        if "args" in o:
            rec["args"] = o["args"]
        out.append(rec)
    return out


def _parent_sum_gid(index: SourceIndex, gid: str) -> str:
    seen: set[str] = set()
    cur = gid
    while cur and cur not in seen:
        seen.add(cur)
        node = index.by_gid.get(cur)
        if node is None:
            return ""
        if node.kind == "sum":
            return node.gid
        cur = node.parent_gid or ""
    return ""


def _member_record(index: SourceIndex, gid: str) -> dict[str, Any]:
    node = index.by_gid.get(gid)
    if node is None:
        return {
            "member_id": gid,
            "kind": "",
            "parent_gid": "",
            "parent_sum_gid": "",
            "ops": None,
            "cond": "",
            "text": "",
            "in_index": False,
        }
    return {
        "member_id": node.gid,
        "kind": node.kind,
        "parent_gid": node.parent_gid or "",
        "parent_sum_gid": _parent_sum_gid(index, node.gid),
        "ops": node.ops,
        "cond": node.cond or "",
        "text": node.text,
        "in_index": True,
    }


def frozen_p2_paths() -> list[Path]:
    return sorted(P2_DIR.glob(P2_GLOB))


def _map_hypothesis(
    path: Path,
    raw: bytes,
    rec: dict[str, Any],
    h: dict[str, Any],
    index: int,
    source_index: SourceIndex,
) -> dict[str, Any]:
    member_ids = [str(x) for x in (h.get("member_ids") or [])]
    members = [_member_record(source_index, gid) for gid in member_ids]
    return {
        "source_path": str(path.relative_to(ROOT)),
        "source_sha256": sha256_bytes(raw),
        "seed": rec.get("seed"),
        "index": index,
        "claimed_type": h.get("representation_type") or "",
        "member_ids": member_ids,
        "operators": _copy_operators(h.get("operators")),
        "reconstruction_rule": _truncate(str(h.get("reconstruction_rule") or "")),
        "members": members,
        "parent_sum_gid": {
            m["member_id"]: m["parent_sum_gid"] for m in members
        },
    }


def build_obligation_map() -> dict[str, Any]:
    catalog = load_guo_catalog()
    source_index = catalog.index
    hypotheses: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    for path in frozen_p2_paths():
        raw = path.read_bytes()
        rec = json.loads(raw)
        hyps = rec.get("hypotheses") or []
        files.append(
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": sha256_bytes(raw),
                "nbytes": len(raw),
                "seed": rec.get("seed"),
                "n_hypotheses": len(hyps),
            }
        )
        for i, h in enumerate(hyps):
            if not isinstance(h, dict):
                continue
            hypotheses.append(
                _map_hypothesis(path, raw, rec, h, i, source_index)
            )
    return {
        "track": "V",
        "agent": "V8",
        "evaluation_only": True,
        "no_llm_calls": True,
        "does_not_adjudicate": True,
        "item_id": "guo-sigma-abc",
        "condition": "P2",
        "runs_glob": str(P2_DIR.relative_to(ROOT) / P2_GLOB),
        "n_files": len(files),
        "n_hypotheses": len(hypotheses),
        "reconstruction_cap": RECONSTRUCTION_CAP,
        "catalog_text_cap_applied": False,
        "files": files,
        "hypotheses": hypotheses,
    }


def dumps_map(blob: dict[str, Any]) -> str:
    return json.dumps(blob, indent=2, ensure_ascii=True) + "\n"


def write_obligation_map(path: Path | None = None) -> Path:
    dest = path or MAP_PATH
    dest.parent.mkdir(parents=True, exist_ok=True)
    text = dumps_map(build_obligation_map())
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(dest)
    return dest


def load_obligation_map(path: Path | None = None) -> dict[str, Any]:
    return json.loads((path or MAP_PATH).read_text(encoding="utf-8"))


def proposer_like_blob(blob: dict[str, Any]) -> str:
    """Concatenate claimed proposer fields. Evaluation metadata is omitted."""
    parts: list[str] = []
    for h in blob.get("hypotheses") or []:
        if not isinstance(h, dict):
            continue
        parts.append(str(h.get("claimed_type") or ""))
        parts.append(str(h.get("reconstruction_rule") or ""))
        parts.append(json.dumps(h.get("operators") or [], ensure_ascii=True))
        for mid in h.get("member_ids") or []:
            parts.append(str(mid))
    return "\n".join(parts)


def assert_member_ids(blob: dict[str, Any]) -> None:
    hyps = blob.get("hypotheses") or []
    if not hyps:
        raise AssertionError("obligation map has no hypotheses")
    for h in hyps:
        ids = h.get("member_ids") or []
        if not ids:
            raise AssertionError(f"hypothesis {h.get('index')} has no member_ids")
        for gid in ids:
            if not is_catalog_id(str(gid)):
                raise AssertionError(f"member id is not G####: {gid!r}")
        for m in h.get("members") or []:
            mid = str(m.get("member_id") or "")
            if not is_catalog_id(mid):
                raise AssertionError(f"member id is not G####: {mid!r}")
            parent = str(m.get("parent_sum_gid") or "")
            if parent and not is_catalog_id(parent):
                raise AssertionError(f"parent_sum_gid is not G####: {parent!r}")


__all__ = [
    "MAP_PATH",
    "P2_DIR",
    "P2_GLOB",
    "RECONSTRUCTION_CAP",
    "assert_member_ids",
    "build_obligation_map",
    "dumps_map",
    "frozen_p2_paths",
    "load_obligation_map",
    "proposer_like_blob",
    "write_obligation_map",
]


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(ROOT))
    out = write_obligation_map()
    blob = load_obligation_map(out)
    print("wrote", out, "files", blob["n_files"], "hyps", blob["n_hypotheses"])
