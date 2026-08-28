"""Source-lattice coverage for frozen Track V3 families.

Does not invent expressions. A missing degeneration is reported as an
index-set, never as an interpolated kernel. The generic builder remains
the only construction path.
"""
from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path
from typing import Any

from research.multibranch_verification.piecewise import (
    DIAGONAL,
    GENERIC,
    HIGHER_DEGENERACY,
    UNKNOWN_ROLE,
    classify_condition,
)

FROZEN_PATH = (
    Path(__file__).resolve().parents[1] / "FROZEN_INPUTS_V3.json"
)


def frozen_source_lattice_coverage(
    frozen: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Coverage of index-equality nodes by source G#### members."""
    blob = frozen if frozen is not None else _load_frozen()
    out: list[dict[str, Any]] = []
    for hyp in blob.get("hypotheses") or []:
        out.append(_family_coverage(hyp))
    return out


def intermediates_required_for_frozen_families(
    frozen: dict[str, Any] | None = None,
) -> dict[str, bool]:
    """False when source members already occupy the equality lattice."""
    return {
        row["family_id"]: bool(row["intermediates_required"])
        for row in frozen_source_lattice_coverage(frozen)
    }


def _load_frozen() -> dict[str, Any]:
    return json.loads(FROZEN_PATH.read_text(encoding="utf-8"))


def _family_coverage(hyp: dict[str, Any]) -> dict[str, Any]:
    fid = str(hyp.get("family_id") or "")
    members = list(hyp.get("members") or [])
    conds = dict(hyp.get("branch_conditions") or {})
    member_ids = [str(m.get("member_id") or "") for m in members]
    present: dict[frozenset[str], list[str]] = {}
    index_names: set[str] = set()
    unclassified: list[str] = []
    for member in members:
        mid = str(member.get("member_id") or "")
        cond = conds.get(mid, member.get("cond"))
        info = classify_condition(cond)
        role = info.get("role")
        names = [str(n) for n in (info.get("index_symbols") or [])]
        if role == UNKNOWN_ROLE:
            unclassified.append(mid)
            continue
        if role not in (GENERIC, DIAGONAL, HIGHER_DEGENERACY):
            unclassified.append(mid)
            continue
        node = frozenset(names)
        index_names.update(names)
        present.setdefault(node, []).append(mid)

    expected = _expected_nodes(index_names)
    missing = sorted(
        [sorted(node) for node in expected if node not in present],
        key=lambda seq: (len(seq), seq),
    )
    complete = not unclassified and not missing and bool(expected)
    return {
        "family_id": fid,
        "member_ids": member_ids,
        "n_members": len(member_ids),
        "index_names": sorted(index_names),
        "present_nodes": [
            {"indices": sorted(node), "member_ids": mids}
            for node, mids in sorted(present.items(), key=lambda kv: (len(kv[0]), sorted(kv[0])))
        ],
        "missing_nodes": missing,
        "unclassified_members": unclassified,
        "intermediates_required": not complete,
        "constructed_intermediates": [],
        "note": (
            "source G#### members occupy the index-equality lattice; "
            "no intermediate expression is required"
            if complete
            else "source lattice incomplete or unclassified; no interpolated kernel"
        ),
    }


def _expected_nodes(index_names: set[str]) -> set[frozenset[str]]:
    names = sorted(index_names)
    nodes = {frozenset()}
    if len(names) >= 2:
        for a, b in combinations(names, 2):
            nodes.add(frozenset({a, b}))
    if len(names) >= 3:
        nodes.add(frozenset(names))
    return nodes
