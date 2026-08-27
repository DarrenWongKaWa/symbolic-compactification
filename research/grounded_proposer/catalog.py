"""Source catalog for P1. Built from Track B source_index, not SOL ranking."""
from __future__ import annotations

from research.obligation_ir.grounding import _arity_of_node, _node_cond_fp
from research.obligation_ir.source_index import SourceIndex, SourceNode


def _fp(n: SourceNode) -> dict:
    hs = [h.replace(" ", "") for h in n.h_factors]
    fns = sorted({h.split("(")[0] for h in hs if "(" in h})
    return {
        "functions": fns,
        "h_factors": hs,
        "indices": ["m", "n", "ell"] if _arity_of_node(n) == 3 else ["m", "n"],
        "branch_condition": _node_cond_fp(n) if n.kind == "piecewise_branch" else "",
        "arity": _arity_of_node(n),
    }


def catalog_entries(index: SourceIndex, *, text_cap: int = 220) -> list[dict]:
    out = []
    for n in index.nodes:
        if n.kind not in {"sum", "piecewise_branch"}:
            continue
        text = n.text
        if len(text) > text_cap:
            text = text[:text_cap] + "…"
        out.append({
            "source_node_id": n.gid,
            "sol_node_id": n.sol_node_id,
            "kind": n.kind,
            "parent_gid": n.parent_gid,
            "ops": n.ops,
            "fingerprint": _fp(n),
            "text": text,
        })
    return out


def render_catalog(entries: list[dict]) -> str:
    lines = ["SOURCE CATALOG — cite these source_node_id values only.",
             "Do not invent aliases (S1_True, branch_generic, O2(n,m)).",
             ""]
    for e in entries:
        fp = e["fingerprint"]
        lines.append(
            f"{e['source_node_id']}  kind={e['kind']}  parent={e['parent_gid'] or '-'}  "
            f"arity={fp['arity']}  cond={fp['branch_condition'] or '-'}  "
            f"h={fp['h_factors']}"
        )
        lines.append(f"  text: {e['text']}")
    return "\n".join(lines)


def catalog_ids(entries: list[dict]) -> set[str]:
    return {e["source_node_id"] for e in entries}
