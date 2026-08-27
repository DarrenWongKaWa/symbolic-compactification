"""Gold-free quality for master-object hypotheses A_i = O_i[F].

Scores a RepresentationHypothesisV2. Does not repair aliases, rewrite
operators, or specialize to any catalog's closed form.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from research.representation_invention.schema import (
    OPERATOR_KINDS,
    OperatorSpec,
    RepresentationHypothesisV2,
    is_catalog_id,
)

UNIT_INTERVAL_AXES = (
    "coverage",
    "parameter_coherence",
    "operator_coherence",
    "description_length_gain",
)

# Count axes (not unit-interval): reuse, structural_depth.
NONTRIVIAL_KINDS = frozenset(OPERATOR_KINDS) - {"identity"}

_THETA_META = frozenset(
    {
        "member",
        "member_id",
        "O",
        "kind",
        "operator",
        "operator_on_template",
        "theta",
        "map",
        "note",
        "nodes",
        "order",
        "n",
        "n_diff",
        "times",
        "var",
        "wrt",
        "variable",
        "index",
        "at",
        "to",
        "point",
        "delta",
        "step",
        "perm",
        "swap",
        "x",
        "y",
        "multiplicity",
    }
)
_VAR_ARG_KEYS = ("var", "wrt", "variable", "index")
_NODE_ARG_KEYS = ("nodes", "at", "point", "to", "x", "y")


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _ops(h: RepresentationHypothesisV2) -> list[OperatorSpec]:
    out: list[OperatorSpec] = []
    for raw in h.operators or []:
        if isinstance(raw, OperatorSpec):
            out.append(raw)
            continue
        if not isinstance(raw, dict):
            continue
        mid = str(raw.get("member_id") or raw.get("member") or "").strip()
        kind = str(raw.get("kind") or raw.get("O") or "").strip()
        args = raw.get("args") if isinstance(raw.get("args"), dict) else {}
        out.append(OperatorSpec(member_id=mid, kind=kind, args=dict(args)))
    return out


def _nodes(h: RepresentationHypothesisV2) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for raw in h.nodes or []:
        if hasattr(raw, "name"):
            out.append((str(raw.name), str(getattr(raw, "expression", "") or "")))
            continue
        if isinstance(raw, dict):
            out.append(
                (
                    str(raw.get("name") or "").strip(),
                    str(raw.get("expression") or raw.get("expr") or "").strip(),
                )
            )
    return out


def _instance_maps(h: RepresentationHypothesisV2) -> dict[str, Any]:
    raw = h.instance_maps or {}
    if isinstance(raw, dict):
        return raw
    return {}


def _theta_from(blob: Any) -> dict[str, str]:
    if not isinstance(blob, dict):
        return {}
    nested = blob.get("theta") or blob.get("map") or {}
    if isinstance(nested, dict) and nested:
        return {str(k): str(v) for k, v in nested.items()}
    return {
        str(k): str(v)
        for k, v in blob.items()
        if k not in _THETA_META and isinstance(v, (str, int, float))
    }


def _norm_text(text: str) -> str:
    t = (text or "").strip().strip("`")
    if not t:
        return ""
    t = t.replace(":=", "=")
    try:
        from research.llm_abstraction.constructor import symbolic_core

        t = symbolic_core(t)
    except Exception:
        if "=" in t:
            depth = 0
            last = None
            for i, ch in enumerate(t):
                if ch in "([{":
                    depth += 1
                elif ch in ")]}":
                    depth = max(0, depth - 1)
                elif ch == "=" and depth == 0:
                    last = i
            if last is not None:
                t = t[last + 1 :].strip()
    return re.sub(r"\s+", "", t)


def _applied_member_ids(h: RepresentationHypothesisV2, ops: list[OperatorSpec]) -> set[str]:
    members = set(h.member_ids or [])
    applied: set[str] = set()
    for op in ops:
        if op.member_id and op.member_id in members:
            applied.add(op.member_id)
    for key in _instance_maps(h):
        ks = str(key)
        if ks in members and is_catalog_id(ks):
            applied.add(ks)
    return applied


def _only_identity(ops: list[OperatorSpec]) -> bool:
    if not ops:
        return True
    return all((op.kind or "identity") == "identity" for op in ops)


def _f_copies_single_member(
    h: RepresentationHypothesisV2,
    member_texts: Optional[dict[str, str]],
) -> bool:
    latent = h.latent_object or ""
    core = _norm_text(latent)
    compact = re.sub(r"\s+", "", latent.replace(":=", "="))
    members = list(h.member_ids or [])
    hits: list[str] = []
    for mid in members:
        if compact in {mid, f"F={mid}", f"F({mid})"} or core == mid:
            hits.append(mid)
            continue
        if member_texts and mid in member_texts:
            mcore = _norm_text(str(member_texts[mid]))
            if mcore and core and core == mcore:
                hits.append(mid)
    if member_texts:
        for mid, text in member_texts.items():
            if mid not in members:
                continue
            mcore = _norm_text(str(text))
            if mcore and core and core == mcore and mid not in hits:
                hits.append(mid)
    return len(set(hits)) == 1


def _parameter_coherence(h: RepresentationHypothesisV2, ops: list[OperatorSpec]) -> float:
    latent = {str(x) for x in (h.latent_variables or []) if str(x).strip()}
    node_rows = _nodes(h)
    node_names = {n for n, _ in node_rows if n}
    node_exprs = {e for _, e in node_rows if e}
    node_ids = node_names | node_exprs

    theta_keys: list[str] = []
    node_refs: list[str] = []
    var_refs: list[str] = []

    def _absorb_args(blob: Any) -> None:
        if not isinstance(blob, dict):
            return
        theta_keys.extend(_theta_from(blob).keys())
        for vk in _VAR_ARG_KEYS:
            if blob.get(vk) not in (None, ""):
                var_refs.append(str(blob[vk]))
        for nk in _NODE_ARG_KEYS:
            val = blob.get(nk)
            if val is None:
                continue
            if isinstance(val, (list, tuple)):
                for item in val:
                    if isinstance(item, dict):
                        name = str(item.get("name") or item.get("expression") or "").strip()
                        if name:
                            node_refs.append(name)
                    elif str(item).strip():
                        node_refs.append(str(item).strip())
            elif str(val).strip():
                node_refs.append(str(val).strip())

    for op in ops:
        _absorb_args(op.args)
    for imap in _instance_maps(h).values():
        _absorb_args(imap)

    checks: list[bool] = []
    for k in theta_keys:
        checks.append(k in latent)
    for v in var_refs:
        checks.append(v in latent)
    if node_ids:
        for ref in node_refs:
            checks.append(ref in node_ids)

    if not checks:
        return 1.0
    return _clip01(sum(1 for c in checks if c) / len(checks))


def _operator_coherence(h: RepresentationHypothesisV2, ops: list[OperatorSpec]) -> float:
    if not ops:
        return 0.0
    members = set(h.member_ids or [])
    good = 0
    for op in ops:
        if op.kind in OPERATOR_KINDS and op.member_id in members:
            good += 1
    return _clip01(good / len(ops))


def _description_length_gain(
    h: RepresentationHypothesisV2,
    member_texts: Optional[dict[str, str]],
) -> Optional[float]:
    if not member_texts:
        return None
    lengths = [
        len(str(member_texts[m]))
        for m in (h.member_ids or [])
        if m in member_texts and str(member_texts[m]).strip()
    ]
    if not lengths:
        return None
    total = sum(lengths)
    if total <= 0:
        return None
    latent_len = len((h.latent_object or "").strip())
    return _clip01((total - latent_len) / total)


def _structural_depth(ops: list[OperatorSpec]) -> int:
    kinds = {op.kind for op in ops if op.kind}
    return len(kinds & NONTRIVIAL_KINDS)


def score_master_hypothesis(
    h: RepresentationHypothesisV2,
    member_texts: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Return gold-free quality axes. Does not rewrite the hypothesis."""
    ops = _ops(h)
    members = list(h.member_ids or [])
    n_members = len(members)
    covered = {op.member_id for op in ops if op.member_id in set(members)}
    coverage = _clip01(len(covered) / n_members) if n_members else 0.0
    applied = _applied_member_ids(h, ops)
    reuse = len(applied)
    tautological = (reuse <= 1 and _only_identity(ops)) or (
        reuse <= 1 and _f_copies_single_member(h, member_texts)
    )
    return {
        "coverage": coverage,
        "reuse": reuse,
        "parameter_coherence": _parameter_coherence(h, ops),
        "operator_coherence": _operator_coherence(h, ops),
        "description_length_gain": _description_length_gain(h, member_texts),
        "structural_depth": _structural_depth(ops),
        "tautological_wrapper": bool(tautological),
    }
