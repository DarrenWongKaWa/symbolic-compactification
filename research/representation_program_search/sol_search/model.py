"""Typed records for frozen-SOL-conditioned deterministic search (S3)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import freeze_json, thaw_json
from research.representation_program_search.search import SearchResult

SOL_ARTIFACT_SCHEMA = "RPSSOLArtifactV1"
SOL_AUTHORITY_COMMIT = "0a2905b"
SOL_LAYER = "structural-observation-layer-v1"
SOL_PRIORITY_POLICY_VERSION = "RPSSOLPriorityPolicyV1"
SOL_STATUSES = frozenset({"AVAILABLE", "NO_ELIGIBLE_SOL", "UNAVAILABLE"})
SOL_ROUTING_UNITS = {
    "SOL_BASIS_FAMILY": 8,
    "SOL_BASIS_RECONSTRUCTION": 8,
    "SOL_COMPOSITION_CHAIN": 2,
    "SOL_DERIVATIVE_HERMITE": 12,
    "SOL_DERIVATIVE_OPERATOR": 12,
    "SOL_DERIVATIVE_REPEATED_NODE": 8,
    "SOL_FAMILY_NEWTON": 3,
    "SOL_LINEAR_REUSE": 4,
    "SOL_MEMBER_ASSIGNMENT": 3,
    "SOL_MEMBER_GROUP": 9,
    "SOL_PARAMETER_FAMILY": 5,
    "SOL_PERMUTATION_OPERATOR": 12,
    "SOL_POLE_NEWTON": 10,
    "SOL_RECURRENCE_OPERATOR": 12,
    "SOL_SHARED_LATENT": 5,
}


@dataclass(frozen=True)
class ProjectedSOLRelation:
    """One proposer-eligible frozen SOL edge projected onto public members."""

    relation_id: str
    relation_type: str
    exactness_class: str
    backend: str
    source_node_ids: tuple[str, ...]
    affected_member_ids: tuple[str, ...]
    node_symbols: tuple[str, ...]
    source_artifact_sha256: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "affected_member_ids": list(self.affected_member_ids),
            "backend": self.backend,
            "exactness_class": self.exactness_class,
            "node_symbols": list(self.node_symbols),
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "source_artifact_sha256": self.source_artifact_sha256,
            "source_node_ids": list(self.source_node_ids),
        }


@dataclass(frozen=True)
class SOLProjection:
    """Fail-closed result of loading and projecting one immutable SOL artifact."""

    status: str
    reason_codes: tuple[str, ...]
    source_artifact_sha256: str | None
    expected_artifact_sha256: str | None
    public_case_sha256: str
    relations: tuple[ProjectedSOLRelation, ...] = ()
    authority_commit: str = SOL_AUTHORITY_COMMIT
    layer: str = SOL_LAYER
    schema_version: str = SOL_ARTIFACT_SCHEMA

    def __post_init__(self) -> None:
        if self.status not in SOL_STATUSES:
            raise ValueError(f"SOL_STATUS_UNKNOWN:{self.status}")
        if self.status == "AVAILABLE" and not self.relations:
            raise ValueError("SOL_AVAILABLE_WITHOUT_RELATIONS")
        if self.status != "AVAILABLE" and self.relations:
            raise ValueError("SOL_UNAVAILABLE_WITH_RELATIONS")

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_commit": self.authority_commit,
            "expected_artifact_sha256": self.expected_artifact_sha256,
            "layer": self.layer,
            "public_case_sha256": self.public_case_sha256,
            "reason_codes": list(self.reason_codes),
            "relations": [item.to_dict() for item in self.relations],
            "schema_version": self.schema_version,
            "source_artifact_sha256": self.source_artifact_sha256,
            "status": self.status,
        }


@dataclass(frozen=True)
class SOLContribution:
    """One auditable integer contribution from one frozen SOL relation."""

    relation_id: str
    relation_type: str
    rule_id: str
    units: int
    source_artifact_sha256: str
    action_hash: str
    affected_state_hash: str

    def __post_init__(self) -> None:
        if not isinstance(self.units, int) or isinstance(self.units, bool) or self.units <= 0:
            raise ValueError("SOL_CONTRIBUTION_UNITS_INVALID")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_hash": self.action_hash,
            "affected_state_hash": self.affected_state_hash,
            "relation_id": self.relation_id,
            "relation_type": self.relation_type,
            "rule_id": self.rule_id,
            "source_artifact_sha256": self.source_artifact_sha256,
            "units": self.units,
        }


@dataclass(frozen=True)
class SOLRoutingDecision:
    """Public, replayable record for ranking one legal M2 child."""

    parent_state_hash: str
    child_state_hash: str
    action: Mapping[str, Any]
    action_hash: str
    parent_priority: int
    incremental_priority: int
    child_priority: int
    contributions: tuple[SOLContribution, ...]

    def __post_init__(self) -> None:
        frozen = freeze_json(self.action)
        if not isinstance(frozen, Mapping):
            raise ValueError("SOL_ROUTING_ACTION_INVALID")
        object.__setattr__(self, "action", frozen)
        if self.incremental_priority != sum(item.units for item in self.contributions):
            raise ValueError("SOL_ROUTING_CONTRIBUTION_MISMATCH")
        if self.child_priority != self.parent_priority + self.incremental_priority:
            raise ValueError("SOL_ROUTING_PRIORITY_MISMATCH")

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": thaw_json(self.action),
            "action_hash": self.action_hash,
            "child_priority": self.child_priority,
            "child_state_hash": self.child_state_hash,
            "contributions": [item.to_dict() for item in self.contributions],
            "incremental_priority": self.incremental_priority,
            "parent_priority": self.parent_priority,
            "parent_state_hash": self.parent_state_hash,
        }

    @property
    def semantic_hash(self) -> str:
        import hashlib

        return hashlib.sha256(canonical_json(self.to_dict()).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class SOLSearchResult:
    """S3 result or an explicit fail-closed unavailability record."""

    projection: SOLProjection
    budget_requested: int
    grammar_id: str
    candidate_pool_hash: str | None
    search_result: SearchResult | None
    routing_decisions: tuple[SOLRoutingDecision, ...] = ()
    priority_policy_version: str = SOL_PRIORITY_POLICY_VERSION
    llm_tokens: int = 0
    ordering_uses_verifier_outcomes: bool = False
    private_reasoning_recorded: bool = False

    def __post_init__(self) -> None:
        if self.projection.status == "AVAILABLE" and self.search_result is None:
            raise ValueError("SOL_AVAILABLE_WITHOUT_SEARCH_RESULT")
        if self.projection.status != "AVAILABLE" and self.search_result is not None:
            raise ValueError("SOL_UNAVAILABLE_WITH_SEARCH_RESULT")
        if self.llm_tokens != 0:
            raise ValueError("SOL_SEARCH_LLM_TOKENS_NONZERO")
        if self.ordering_uses_verifier_outcomes:
            raise ValueError("SOL_SEARCH_VERIFIER_ORDERING_FORBIDDEN")

    @property
    def semantic_trace_hash(self) -> str:
        import hashlib

        payload = {
            "budget_requested": self.budget_requested,
            "candidate_pool_hash": self.candidate_pool_hash,
            "expanded_state_hashes": (
                []
                if self.search_result is None
                else [item.canonical_hash for item in self.search_result.expanded_states]
            ),
            "grammar_id": self.grammar_id,
            "priority_policy_version": self.priority_policy_version,
            "projection": self.projection.to_dict(),
            "routing_decision_hashes": [
                item.semantic_hash for item in self.routing_decisions
            ],
        }
        return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()

    def to_dict(self, *, include_states: bool = False) -> dict[str, Any]:
        base = (
            {
                "budget_requested": self.budget_requested,
                "candidate_pool_hash": self.candidate_pool_hash,
                "condition": "S3",
                "frontier_exhausted": None,
                "grammar_id": self.grammar_id,
                "states_expanded": 0,
            }
            if self.search_result is None
            else self.search_result.to_dict(include_states=include_states)
        )
        base.update({
            "condition": "S3",
            "llm_tokens": self.llm_tokens,
            "ordering_uses_verifier_outcomes": self.ordering_uses_verifier_outcomes,
            "priority_policy_version": self.priority_policy_version,
            "priority_policy": {
                "routing_units": dict(sorted(SOL_ROUTING_UNITS.items())),
                "task_configurable": False,
                "tie_break": [
                    "negative_cumulative_sol_units",
                    "complexity",
                    "depth",
                    "canonical_hash",
                ],
                "version": self.priority_policy_version,
            },
            "private_reasoning_recorded": self.private_reasoning_recorded,
            "routing_decisions": [item.to_dict() for item in self.routing_decisions],
            "semantic_trace_hash": self.semantic_trace_hash,
            "sol_projection": self.projection.to_dict(),
            "sol_status": self.projection.status,
        })
        return base
