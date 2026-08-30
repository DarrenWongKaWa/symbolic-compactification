"""Thin, evaluator-blind adapter from the frozen M2 frontier to S6.

The adapter deliberately owns no candidate extraction or legal-action logic.
It converts :class:`SearchState` objects into method-neutral verifier nodes and
delegates every successor calculation to ``search.expand_state``.  Verifier
feedback changes only the frozen controller priority band; it is never turned
into an unrecorded natural-language repair.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from research.representation_program_search.search import (
    CandidatePool,
    PublicCase,
    SearchPolicy,
    SearchState,
    expand_state,
    extract_candidate_pool,
    initial_state,
)

from .model import FEEDBACK_VALUES, FrontierContractError, VerifierFrontierNode


@dataclass
class M2VerifierFrontierAdapter:
    """Adapt one public M2 frontier without reading evaluator artifacts.

    ``leakage_status`` defaults to ``UNKNOWN``.  A scientific runner must pass
    ``CLEARED`` only after a separate, hash-bound leakage audit.  Merely
    loading through the public-case firewall does not prove that the source
    syntax itself is free from target leakage.
    """

    case: PublicCase
    grammar_id: str = "G_FULL"
    candidate_pool: CandidatePool | None = None
    search_policy: SearchPolicy = field(default_factory=SearchPolicy)
    leakage_status: str = "UNKNOWN"
    assumption_clearance: str = "UNKNOWN"
    _states: dict[str, SearchState] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.grammar_id not in {"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"}:
            raise FrontierContractError("GRAMMAR_ABLATION_UNKNOWN")
        if self.leakage_status not in {"CLEARED", "FOUND", "UNKNOWN"}:
            raise FrontierContractError("LEAKAGE_STATUS_INVALID")
        if self.assumption_clearance not in {"CLEARED", "INCOMPLETE", "UNKNOWN"}:
            raise FrontierContractError("ASSUMPTION_CLEARANCE_INVALID")
        if self.candidate_pool is None:
            self.candidate_pool = extract_candidate_pool(self.case)
        if self.candidate_pool.source_member_count != len(self.case.members):
            raise FrontierContractError("CANDIDATE_POOL_CASE_MISMATCH")
        member_ids = {item.member_id for item in self.case.members}
        for latent in self.candidate_pool.latents:
            if not set(latent.public_origins) <= member_ids:
                raise FrontierContractError("CANDIDATE_POOL_CASE_MISMATCH")
            if not {
                member_id for member_id, _values in latent.instance_maps
            } <= member_ids:
                raise FrontierContractError("CANDIDATE_POOL_CASE_MISMATCH")

    def _node(
        self,
        state: SearchState,
        *,
        parent_hash: str | None,
    ) -> VerifierFrontierNode:
        if state.grammar_id != self.grammar_id:
            raise FrontierContractError("STATE_GRAMMAR_MISMATCH")
        if state.case_fingerprint != self.case.proposer_view_sha256:
            raise FrontierContractError("STATE_PUBLIC_CASE_MISMATCH")
        node = VerifierFrontierNode(
            program=state.to_program(
                source_members=self.case.source_members,
                assumption_statuses=self.case.assumption_statuses,
            ),
            context=self.case.compile_context(self.grammar_id),
            public_state={
                "candidate_pool_hash": self.candidate_pool.canonical_hash,
                "search_state": state.scientific_payload(),
                "search_state_hash": state.canonical_hash,
            },
            complexity=state.complexity,
            depth=state.depth,
            public_priority=(state.complexity, state.depth, state.canonical_hash),
            leakage_status=self.leakage_status,
            assumption_clearance=self.assumption_clearance,
            parent_hash=parent_hash,
            action_from_parent=(
                None
                if state.action_from_parent is None
                else state.action_from_parent.to_dict()
            ),
        )
        previous = self._states.get(node.canonical_hash)
        if previous is not None and previous.canonical_hash != state.canonical_hash:
            raise FrontierContractError("ADAPTER_STATE_HASH_COLLISION")
        self._states[node.canonical_hash] = state
        return node

    def initial_node(self) -> VerifierFrontierNode:
        """Return the single frozen M2 root as an S6 frontier node."""
        return self._node(
            initial_state(self.case, grammar_id=self.grammar_id),
            parent_hash=None,
        )

    def expand(
        self,
        node: VerifierFrontierNode,
        feedback: str | None,
    ) -> tuple[VerifierFrontierNode, ...]:
        """Return the exact M2 legal children after aggregate S6 feedback."""
        if feedback is not None and feedback not in FEEDBACK_VALUES:
            raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")
        state = self._states.get(node.canonical_hash)
        if state is None:
            raise FrontierContractError("ADAPTER_STATE_UNKNOWN")
        expansion = expand_state(
            state,
            self.case,
            self.candidate_pool,
            self.search_policy,
        )
        return tuple(
            self._node(child, parent_hash=node.canonical_hash)
            for child in expansion.children
        )

    def public_contract(self) -> dict:
        """Return hashable method provenance for a surrounding run manifest."""
        return {
            "candidate_pool_hash": self.candidate_pool.canonical_hash,
            "assumption_clearance": self.assumption_clearance,
            "case_id": self.case.case_id,
            "grammar_id": self.grammar_id,
            "leakage_status": self.leakage_status,
            "proposer_view_sha256": self.case.proposer_view_sha256,
            "search_policy": self.search_policy.to_dict(),
            "successor_generation": "M2_EXPAND_STATE_UNCHANGED",
            "verifier_feedback_use": "FROZEN_PRIORITY_BAND_ONLY",
        }
