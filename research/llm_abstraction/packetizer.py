"""Deterministic gold-free SOL packetizer. Does not modify frozen SOL."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Optional, Union

from research.llm_abstraction.leak import assert_no_packet_interpretation
from symbolic_compactification.observations.api import observe
from symbolic_compactification.observations.ir import ObservationBundle
from symbolic_compactification.parser import parse_expression
from symbolic_compactification.structure import structure_summary

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "research" / "llm_abstraction" / "runs" / "_cache"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def basic_summary(
    expression: Union[str, Any],
    symbols: list,
    functions: Optional[list] = None,
) -> dict:
    if isinstance(expression, str):
        expr = parse_expression(expression, symbols, functions=functions or None)
        raw = expression
    else:
        expr = expression
        raw = str(expression)
    s = structure_summary(expr)
    return {
        "ops": s.get("count_ops"),
        "count_ops": s.get("count_ops"),
        "free_symbols": s.get("free_symbols") or [],
        "functions": list(functions or []) or s.get("indexed_names") or [],
        "n_piecewise": s.get("piecewise") or 0,
        "n_branches": s.get("piecewise_branches") or 0,
        "indexed_names": s.get("indexed_names") or [],
        "indexed_calls": s.get("indexed_calls") or 0,
        "n_sums": s.get("sums") or 0,
        "raw_chars": len(raw),
    }


def observe_cached(
    expression: str,
    symbols: list,
    functions: Optional[list] = None,
    *,
    backends: str = "relations",
    timeout_s: float = 12.0,
) -> dict:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = _sha(json.dumps({
        "e": expression, "s": symbols, "f": functions or [],
        "b": backends, "t": timeout_s,
    }, sort_keys=True))
    path = CACHE / f"observe_{key}.json"
    if path.is_file():
        return json.loads(path.read_text())
    bundle = observe(
        expression, symbols, functions or [],
        backends=backends, timeout_s=timeout_s,
    )
    data = bundle.to_dict()
    path.write_text(json.dumps(data, default=str))
    return data


def _find(parent, x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _union(parent, a, b):
    ra, rb = _find(parent, a), _find(parent, b)
    if ra != rb:
        parent[rb] = ra


def packetize(
    bundle: Union[ObservationBundle, dict],
    *,
    cap: int = 10,
    max_members: int = 8,
    max_member_chars: int = 280,
) -> list[dict]:
    data = bundle.to_dict() if hasattr(bundle, "to_dict") else dict(bundle)
    nodes = {n["node_id"]: n for n in data.get("nodes") or [] if n.get("node_id")}
    rels = list(data.get("relations") or [])
    parent: dict[str, str] = {}
    orphans: list[dict] = []
    for r in rels:
        ids = [i for i in (r.get("source_ids") or []) if i]
        if len(ids) >= 2:
            for x in ids[1:]:
                _union(parent, ids[0], x)
        elif len(ids) == 1:
            _find(parent, ids[0])
        else:
            orphans.append(r)

    groups: dict[str, list[dict]] = defaultdict(list)
    for r in rels:
        ids = [i for i in (r.get("source_ids") or []) if i]
        if not ids:
            continue
        groups[_find(parent, ids[0])].append(r)

    families = []
    for root, rs in groups.items():
        members = []
        for r in rs:
            members.extend(r.get("source_ids") or [])
        members = list(dict.fromkeys(members))
        types = sorted({r.get("relation_type") for r in rs if r.get("relation_type")})
        backends = sorted({r.get("backend") for r in rs if r.get("backend")})
        exact = sorted({r.get("exactness_class") for r in rs if r.get("exactness_class")})
        ops = [int(nodes[m].get("ops") or 0) for m in members if m in nodes]
        depth = (sum(ops) / len(ops)) if ops else 0.0
        relset = set(types)
        coh = 1.0 if relset & {
            "SUBSTITUTION_INSTANCE", "LGG_FAMILY", "DERIVATIVE_RELATED",
            "PERMUTATION_RELATED", "INDEX_RENAMING_RELATED",
        } else 0.4
        abstr = 2.0 if relset & {
            "LGG_FAMILY", "DERIVATIVE_RELATED", "PERMUTATION_RELATED",
        } else 1.0
        score = (
            len(members)
            + 0.05 * depth
            + 2.0 * len(backends)
            + coh
            + len(types)
            + abstr
        )
        member_rows = []
        for mid in members[:max_members]:
            n = nodes.get(mid) or {}
            text = str(n.get("text") or mid)
            if len(text) > max_member_chars:
                text = text[:max_member_chars] + "…"
            member_rows.append({
                "id": mid,
                "text": text,
                "ops": n.get("ops"),
                "functions": n.get("functions") or [],
            })
        evidence = []
        for r in rs[:6]:
            evidence.append({
                "relation_type": r.get("relation_type"),
                "backend": r.get("backend"),
                "exactness_class": r.get("exactness_class"),
                "evidence": (r.get("evidence") or "")[:240],
                "witness": (r.get("witness") or None),
                "assumptions": r.get("assumptions") or [],
            })
        families.append({
            "score": round(score, 4),
            "members": member_rows,
            "n_members": len(members),
            "relations": types,
            "backends": backends,
            "exactness_classes": exact,
            "n_relations": len(rs),
            "evidence": evidence,
            "coverage": len(members),
            "structural_depth": round(depth, 3),
            "backend_agreement": len(backends),
            "parameter_coherence": coh,
            "relation_diversity": len(types),
        })

    for i, r in enumerate(orphans):
        families.append({
            "score": 0.5,
            "members": [],
            "n_members": 0,
            "relations": [r.get("relation_type")],
            "backends": [r.get("backend")] if r.get("backend") else [],
            "exactness_classes": [r.get("exactness_class")] if r.get("exactness_class") else [],
            "n_relations": 1,
            "evidence": [{
                "relation_type": r.get("relation_type"),
                "backend": r.get("backend"),
                "exactness_class": r.get("exactness_class"),
                "evidence": (r.get("evidence") or "")[:240],
                "witness": r.get("witness"),
                "assumptions": r.get("assumptions") or [],
            }],
            "coverage": 0,
            "structural_depth": 0.0,
            "backend_agreement": 1,
            "parameter_coherence": 0.2,
            "relation_diversity": 1,
            "orphan": True,
        })

    families.sort(key=lambda f: (-f["score"], -f["n_members"], f["relations"]))
    out = []
    for i, fam in enumerate(families[:cap], start=1):
        fam = dict(fam)
        fam["packet_id"] = f"F{i:02d}"
        fam["note"] = "observation only; not a scientific object name"
        out.append(fam)
    assert_no_packet_interpretation(out)
    return out


def render_packets(packets: list[dict]) -> str:
    blocks = []
    for p in packets:
        lines = [f"FAMILY {p['packet_id']}"]
        lines.append("members:")
        if p.get("members"):
            for m in p["members"]:
                lines.append(f"  {m['id']}: {m['text']}")
        else:
            lines.append("  (none)")
        lines.append("relations:")
        for r in p.get("relations") or []:
            lines.append(f"  {r}")
        lines.append("evidence:")
        for e in p.get("evidence") or []:
            bits = [e.get("backend") or "?", e.get("exactness_class") or ""]
            wit = e.get("witness")
            ev = e.get("evidence") or ""
            lines.append(f"  {'/'.join(x for x in bits if x)}: {ev}")
            if wit:
                lines.append(f"  witness: {wit}")
        lines.append(f"exactness_classes: {', '.join(p.get('exactness_classes') or [])}")
        lines.append("note: observation only; not a scientific object name")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) if blocks else "(no ranked families)"


def packets_for_item(
    item: dict,
    *,
    cap: int = 10,
    backends: str = "relations",
    timeout_s: float = 12.0,
) -> tuple[list[dict], dict, str]:
    current = item["current"]
    symbols = item.get("symbols") or []
    functions = item.get("functions") or []
    bundle = observe_cached(
        current, symbols, functions,
        backends=backends, timeout_s=timeout_s,
    )
    packets = packetize(bundle, cap=cap)
    extra = []
    gold = item.get("hidden_gold") or {}
    extra.extend(gold.get("aux_names") or [])
    extra.extend(item.get("gold_auxiliaries") or [])
    assert_no_packet_interpretation(packets, extra)
    text = render_packets(packets)
    assert_no_packet_interpretation(text, extra)
    summary = basic_summary(current, symbols, functions)
    return packets, summary, text
