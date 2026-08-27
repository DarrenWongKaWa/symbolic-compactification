"""Format proposer-visible catalog rows. Does not invent members or gold names."""
from __future__ import annotations

from typing import Any


def catalog_ids(entries: list[dict]) -> set[str]:
    out: set[str] = set()
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        gid = str(e.get("source_node_id") or e.get("gid") or "").strip()
        if gid:
            out.add(gid)
    return out


def render_catalog(entries: list[dict[str, Any]]) -> str:
    lines = [
        "SOURCE CATALOG — cite these source_node_id values only.",
        "Do not invent aliases (S1_True, branch_generic, O2(n,m)).",
        "",
    ]
    for e in entries or []:
        if not isinstance(e, dict):
            continue
        gid = str(e.get("source_node_id") or e.get("gid") or "").strip()
        if not gid:
            continue
        fp = e.get("fingerprint") if isinstance(e.get("fingerprint"), dict) else {}
        kind = e.get("kind") or "-"
        parent = e.get("parent_gid") or "-"
        arity = fp.get("arity", e.get("arity", "-"))
        cond = fp.get("branch_condition") or e.get("cond") or "-"
        h = fp.get("h_factors") or fp.get("functions") or ""
        text = e.get("text") or ""
        lines.append(
            f"{gid}  kind={kind}  parent={parent}  "
            f"arity={arity}  cond={cond}  h={h}"
        )
        if text:
            lines.append(f"  text: {text}")
    return "\n".join(lines)
