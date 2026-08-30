"""Frozen deterministic relation-to-action routing for S3."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import thaw_json
from research.representation_program_search.search import (
    CandidatePool,
    LegalAction,
    SearchState,
)

from .model import (
    SOL_PRIORITY_POLICY_VERSION,
    SOL_ROUTING_UNITS,
    ProjectedSOLRelation,
    SOLContribution,
    SOLProjection,
    SOLRoutingDecision,
)

_FAMILY = frozenset({
    "IDENTICAL",
    "AC_EQUIVALENT",
    "CANONICALLY_EQUIVALENT",
    "SUBSTITUTION_INSTANCE",
    "LGG_FAMILY",
    "PATTERN_MATCH",
    "KNOWN_REWRITE_EQUIVALENT",
    "EGRAPH_EQUIVALENT",
    "SAME_FUNCTION_FAMILY",
})
_PARAMETER = frozenset({
    "SUBSTITUTION_INSTANCE", "LGG_FAMILY", "SAME_FUNCTION_FAMILY",
})
_POLE = frozenset({"SAME_POLE_SIGNATURE", "SAME_DENOMINATOR_FAMILY"})
_PERMUTATION = frozenset({
    "PERMUTATION_RELATED",
    "INDEX_RENAMING_RELATED",
    "SAME_INDEX_ORBIT",
    "TENSOR_SYMMETRY_RELATED",
})
_SHARED_STRUCTURE = _FAMILY | _POLE | _PERMUTATION | frozenset({
    "DERIVATIVE_RELATED", "RECURRENCE_CANDIDATE",
})


@dataclass(frozen=True)
class SOLPriorityPolicy:
    """Version lock; rule units below are intentionally not task-configurable."""

    version: str = SOL_PRIORITY_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.version != SOL_PRIORITY_POLICY_VERSION:
            raise ValueError("SOL_PRIORITY_POLICY_UNKNOWN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "integer_units_only": True,
            "routing_units": dict(sorted(SOL_ROUTING_UNITS.items())),
            "task_configurable": False,
            "tie_break": ["negative_cumulative_sol_units", "complexity", "depth", "canonical_hash"],
            "version": self.version,
        }


def _action_hash(action: LegalAction) -> str:
    return hashlib.sha256(action.canonical_key.encode("utf-8")).hexdigest()


def _candidate_origins(action: LegalAction, pool: CandidatePool) -> set[str]:
    candidate_id = thaw_json(action.payload).get("candidate_id")
    for candidate in pool.latents:
        if candidate.candidate_id == candidate_id:
            return set(candidate.public_origins)
    return set()


def _latent_origins(action: LegalAction, state: SearchState, pool: CandidatePool) -> set[str]:
    latent_id = thaw_json(action.payload).get("latent_id")
    if not isinstance(latent_id, str):
        return set()
    candidate_id = latent_id.removeprefix("F_")
    for candidate in pool.latents:
        if candidate.candidate_id == candidate_id:
            return set(candidate.public_origins)
    return set()


def _repeated_symbols(action: LegalAction, state: SearchState) -> set[str]:
    payload = thaw_json(action.payload)
    if action.action == "ADD_REPEATED_NODE":
        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            return set()
        return {
            item for item in nodes
            if isinstance(item, str) and nodes.count(item) > 1
        }
    if action.action == "ADD_HERMITE_DD":
        node_id = payload.get("node_id")
        for node in state.node_structures:
            if node.node_id == node_id:
                return {
                    item for item in node.nodes if node.nodes.count(item) > 1
                }
    return set()


def _relation_rule(
    relation: ProjectedSOLRelation,
    action: LegalAction,
    parent: SearchState,
    pool: CandidatePool,
) -> tuple[str, int] | None:
    kind = action.action
    relation_members = set(relation.affected_member_ids)
    relation_symbols = set(relation.node_symbols)
    payload = thaw_json(action.payload)
    if kind == "GROUP_MEMBERS":
        members = set(payload.get("member_ids") or [])
        if len(members) >= 2 and members <= relation_members:
            return "SOL_MEMBER_GROUP", SOL_ROUTING_UNITS["SOL_MEMBER_GROUP"]
    if kind in {"CREATE_LATENT", "CREATE_BASIS"}:
        origins = _candidate_origins(action, pool)
        if (
            kind == "CREATE_BASIS"
            and origins & relation_members
            and relation.relation_type in _PERMUTATION
        ):
            return "SOL_BASIS_FAMILY", SOL_ROUTING_UNITS["SOL_BASIS_FAMILY"]
        if len(origins & relation_members) >= 2 and relation.relation_type in _SHARED_STRUCTURE:
            return "SOL_SHARED_LATENT", SOL_ROUTING_UNITS["SOL_SHARED_LATENT"]
    if kind == "ADD_MEMBER":
        member_id = payload.get("member_id")
        if member_id in relation_members and relation.relation_type in _PARAMETER:
            return "SOL_MEMBER_ASSIGNMENT", SOL_ROUTING_UNITS["SOL_MEMBER_ASSIGNMENT"]
    origins = _latent_origins(action, parent, pool)
    if origins and not (origins & relation_members):
        return None
    if kind in {"ADD_PARAMETER", "SUBSTITUTE_PARAMETER"} and relation.relation_type in _PARAMETER:
        return "SOL_PARAMETER_FAMILY", SOL_ROUTING_UNITS["SOL_PARAMETER_FAMILY"]
    if kind == "ADD_DERIVATIVE" and relation.relation_type == "DERIVATIVE_RELATED":
        return "SOL_DERIVATIVE_OPERATOR", SOL_ROUTING_UNITS["SOL_DERIVATIVE_OPERATOR"]
    if kind == "ADD_NEWTON_DD":
        if relation.relation_type in _POLE:
            return "SOL_POLE_NEWTON", SOL_ROUTING_UNITS["SOL_POLE_NEWTON"]
        if relation.relation_type in _PARAMETER:
            return "SOL_FAMILY_NEWTON", SOL_ROUTING_UNITS["SOL_FAMILY_NEWTON"]
    if kind == "ADD_RECURRENCE" and relation.relation_type == "RECURRENCE_CANDIDATE":
        return "SOL_RECURRENCE_OPERATOR", SOL_ROUTING_UNITS["SOL_RECURRENCE_OPERATOR"]
    if kind == "ADD_PERMUTATION" and relation.relation_type in _PERMUTATION:
        return "SOL_PERMUTATION_OPERATOR", SOL_ROUTING_UNITS["SOL_PERMUTATION_OPERATOR"]
    if kind in {"ADD_REPEATED_NODE", "ADD_HERMITE_DD"}:
        repeated = _repeated_symbols(action, parent)
        if (
            relation.relation_type == "DERIVATIVE_RELATED"
            and repeated
            and repeated & relation_symbols
        ):
            return (
                "SOL_DERIVATIVE_HERMITE" if kind == "ADD_HERMITE_DD"
                else "SOL_DERIVATIVE_REPEATED_NODE",
                SOL_ROUTING_UNITS[
                    "SOL_DERIVATIVE_HERMITE"
                    if kind == "ADD_HERMITE_DD"
                    else "SOL_DERIVATIVE_REPEATED_NODE"
                ],
            )
    if kind == "ADD_LINEAR_COMBINATION" and relation.relation_type in {
        "CSE_SHARED", "KNOWN_REWRITE_EQUIVALENT", "EGRAPH_EQUIVALENT",
    }:
        return "SOL_LINEAR_REUSE", SOL_ROUTING_UNITS["SOL_LINEAR_REUSE"]
    if kind == "RECONSTRUCT_FROM_BASIS" and relation.relation_type in _PERMUTATION:
        return "SOL_BASIS_RECONSTRUCTION", SOL_ROUTING_UNITS["SOL_BASIS_RECONSTRUCTION"]
    if kind == "ADD_COMPOSE" and relation.relation_type in {
        "DERIVATIVE_RELATED", "RECURRENCE_CANDIDATE",
    }:
        return "SOL_COMPOSITION_CHAIN", SOL_ROUTING_UNITS["SOL_COMPOSITION_CHAIN"]
    return None


def route_legal_child(
    projection: SOLProjection,
    *,
    parent: SearchState,
    action: LegalAction,
    child: SearchState,
    candidate_pool: CandidatePool,
    parent_priority: int,
) -> SOLRoutingDecision:
    """Rank one already-legal M2 child; this function never creates a child."""
    if projection.status != "AVAILABLE" or projection.source_artifact_sha256 is None:
        raise ValueError("SOL_PROJECTION_NOT_AVAILABLE")
    action_hash = _action_hash(action)
    contributions: list[SOLContribution] = []
    for relation in projection.relations:
        rule = _relation_rule(relation, action, parent, candidate_pool)
        if rule is None:
            continue
        rule_id, units = rule
        contributions.append(SOLContribution(
            relation_id=relation.relation_id,
            relation_type=relation.relation_type,
            rule_id=rule_id,
            units=units,
            source_artifact_sha256=relation.source_artifact_sha256,
            action_hash=action_hash,
            affected_state_hash=child.canonical_hash,
        ))
    ordered = tuple(sorted(
        contributions,
        key=lambda item: (item.relation_id, item.rule_id, item.action_hash),
    ))
    increment = sum(item.units for item in ordered)
    return SOLRoutingDecision(
        parent_state_hash=parent.canonical_hash,
        child_state_hash=child.canonical_hash,
        action=action.to_dict(),
        action_hash=action_hash,
        parent_priority=parent_priority,
        incremental_priority=increment,
        child_priority=parent_priority + increment,
        contributions=ordered,
    )
