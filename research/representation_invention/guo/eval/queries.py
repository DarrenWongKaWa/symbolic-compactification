"""Guo DEV evaluation queries. Not given to the proposer.

These are checks the evaluator may run on a later hypothesis. They do not
select a representation and do not certify any family.
"""
from __future__ import annotations

from typing import Any, Optional

QUERY_LOCAL_CONFLUENCE = {
    "id": "Q-local-confluence",
    "family": "local_confluence",
    "ask": (
        "Does a hypothesis pair a generic piecewise_branch (branch_condition "
        "true) with a coincident branch under the same parent, using an "
        "explicit limit operator and G#### member ids?"
    ),
    "required_types": ["local_confluence"],
    "required_operator_kinds": ["limit"],
    "min_grounded_members": 2,
    "notes": "Baseline local-relation check. Not an upgrade to a stronger type.",
}

QUERY_NEWTON_DD_CANDIDATE = {
    "id": "Q-newton-dd-candidate",
    "family": "newton_dd_candidate",
    "ask": (
        "Does a hypothesis write an explicit first Newton formula "
        "F[x,y] = (F(x)-F(y))/(x-y) on grounded catalog members? "
        "A candidate is not a certified representation."
    ),
    "required_types": ["divided_difference"],
    "required_operator_kinds": ["newton_dd"],
    "min_grounded_members": 1,
    "notes": "Candidate check only. This query does not decide the representation.",
}

QUERY_REPEATED_NODE_DD = {
    "id": "Q-repeated-node-dd",
    "family": "repeated_node_dd",
    "ask": (
        "Does a hypothesis state a repeated-node formula (F[x,x] = F'(x) "
        "and/or F[x,x,y] / higher) with explicit node multiplicities on "
        "coincident catalog branches?"
    ),
    "required_types": ["divided_difference", "hermite_divided_difference"],
    "required_operator_kinds": ["hermite_dd", "newton_dd"],
    "min_grounded_members": 1,
    "notes": "Repeated-node check. Multiplicities must be explicit if claimed.",
}

QUERY_MASTER_FAMILIES = {
    "id": "Q-possible-master-families",
    "family": "possible_master_families",
    "ask": (
        "Do at least two structurally distinct catalog members share one "
        "explicit latent F via nontrivial operators (not F := A1 used once)?"
    ),
    "required_types": [
        "master_function",
        "derivative_family",
        "recurrence_family",
        "generating_function",
    ],
    "min_distinct_members": 2,
    "notes": "Possible-family check. Naming a master is not sufficient.",
}

QUERIES: tuple[dict[str, Any], ...] = (
    QUERY_LOCAL_CONFLUENCE,
    QUERY_NEWTON_DD_CANDIDATE,
    QUERY_REPEATED_NODE_DD,
    QUERY_MASTER_FAMILIES,
)

QUERY_IDS: tuple[str, ...] = tuple(q["id"] for q in QUERIES)


def _branches_by_parent(entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for e in entries:
        if e.get("kind") != "piecewise_branch":
            continue
        out.setdefault(e.get("parent_gid") or "", []).append(e)
    return out


def confluence_candidate_pairs(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Generic/coincident pairs under one piecewise parent. Structural only."""
    pairs: list[dict[str, str]] = []
    for parent, group in _branches_by_parent(entries).items():
        generics = [
            e for e in group
            if (e.get("fingerprint") or {}).get("branch_condition") == "true"
        ]
        coinc = [
            e for e in group
            if (e.get("fingerprint") or {}).get("branch_condition") not in {"true", "", None}
        ]
        for g in generics:
            for d in coinc:
                pairs.append({
                    "generic": g["source_node_id"],
                    "degenerate": d["source_node_id"],
                    "parent": parent,
                    "cond_generic": "true",
                    "cond_degenerate": str(
                        (d.get("fingerprint") or {}).get("branch_condition") or ""
                    ),
                })
    return pairs


def repeated_node_candidates(entries: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Coincident branches (not the generic true branch). Structural only."""
    out: list[dict[str, str]] = []
    for e in entries:
        if e.get("kind") != "piecewise_branch":
            continue
        cond = str((e.get("fingerprint") or {}).get("branch_condition") or "")
        if cond in {"", "true"}:
            continue
        out.append({
            "member": e["source_node_id"],
            "cond": cond,
            "parent": e.get("parent_gid") or "",
        })
    return out


def possible_master_groups(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Arity/kind groupings a master-family query may inspect. Not a claim."""
    sums = [e for e in entries if e.get("kind") == "sum"]
    branches = [e for e in entries if e.get("kind") == "piecewise_branch"]

    def ids(rows: list[dict[str, Any]]) -> list[str]:
        return [r["source_node_id"] for r in rows]

    def arity(e: dict[str, Any]) -> int:
        return int((e.get("fingerprint") or {}).get("arity") or 0)

    groups = [
        {"id": "all-sums", "members": ids(sums)},
        {"id": "sums-arity-2", "members": ids([e for e in sums if arity(e) == 2])},
        {"id": "sums-arity-3", "members": ids([e for e in sums if arity(e) == 3])},
        {
            "id": "branches-arity-2",
            "members": ids([e for e in branches if arity(e) == 2]),
        },
        {
            "id": "branches-arity-3",
            "members": ids([e for e in branches if arity(e) == 3]),
        },
    ]
    return [g for g in groups if len(g["members"]) >= 2]


def instantiate_queries(
    entries: Optional[list[dict[str, Any]]] = None,
) -> list[dict[str, Any]]:
    """Copy query templates and, if given, attach catalog-derived candidates."""
    out: list[dict[str, Any]] = []
    for q in QUERIES:
        row = dict(q)
        if entries is not None:
            if q["id"] == "Q-local-confluence":
                row["candidate_pairs"] = confluence_candidate_pairs(entries)
            elif q["id"] == "Q-newton-dd-candidate":
                row["candidate_pairs"] = confluence_candidate_pairs(entries)
            elif q["id"] == "Q-repeated-node-dd":
                row["candidate_members"] = repeated_node_candidates(entries)
            elif q["id"] == "Q-possible-master-families":
                row["candidate_families"] = possible_master_groups(entries)
        out.append(row)
    return out


__all__ = [
    "QUERIES",
    "QUERY_IDS",
    "QUERY_LOCAL_CONFLUENCE",
    "QUERY_MASTER_FAMILIES",
    "QUERY_NEWTON_DD_CANDIDATE",
    "QUERY_REPEATED_NODE_DD",
    "confluence_candidate_pairs",
    "instantiate_queries",
    "possible_master_groups",
    "repeated_node_candidates",
]
