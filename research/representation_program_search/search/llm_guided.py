"""S4 state-ranking and S5 action-ranking over the frozen M2 frontier."""
from __future__ import annotations

import hashlib
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.grammar_v1 import BUDGET_STATES
from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import freeze_json, thaw_json

from .actions import SearchPolicy, expand_state, initial_state
from .beam_policy import (
    BATCHED_BEAM_MERGE_POLICY_VERSION,
    CROSS_PARENT_PRIORITY_FIELDS,
    cross_parent_rank_key,
)
from .candidates import CandidatePool, extract_candidate_pool
from .llm_contract import (
    LLM_BATCH_SIZE,
    LLM_BEAM_WIDTH,
    LLM_RANKING_SCHEMA_VERSION,
    LLM_SEARCH_PROTOCOL_VERSION,
    LLM_SEED_LABELS,
    ChatCompletionsTransport,
    DeepSeekSearchConfig,
    TokenUsage,
    atomic_write_json,
    build_ranking_request,
    call_and_validate_ranking,
    candidate_state_items,
    decision_record_hash,
    legal_action_items,
    public_case_payload,
    public_state_payload,
    request_hash,
)
from .model import SearchContractError, SearchState
from .public_case import PublicCase
from .results import ExpansionRecord, SearchResult, public_manifest

LLM_SEARCH_POLICY_VERSION = "RPSLLMBeamBatchPolicyV1"
LLM_FALLBACK_POLICY = "PRESENTED_CANONICAL_ORDER_V1"
LLM_CAUSAL_VALIDITY_POLICY_VERSION = "RPSLLMCausalValidityV1"
LLM_CAUSAL_STATUS_VALID = "VALID_LLM_GUIDED_SCIENTIFIC_RUN"
LLM_CAUSAL_STATUS_INVALID = "INVALID_LLM_GUIDED_DIAGNOSTIC_ONLY"
LLM_CAUSAL_REASON_FALLBACK = "FALLBACK_DECISION_PRESENT"
LLM_CAUSAL_REASON_INCOMPLETE_USAGE = "USAGE_INCOMPLETE"
LLM_CAUSAL_REASON_ZERO_ACCEPTED = "ZERO_ACCEPTED_LLM_DECISIONS"
SYMBOLIC_COMPARISON_REQUIRES_MATCHED_BATCH_CONTROL = True
SYMBOLIC_COMPARISON_STATUS = "UNMATCHED_FRONTIER_DO_NOT_CLAIM_AI_ADVANTAGE"
LLM_RUN_HEADER_VERSION = "RPSLLMRunHeaderV1"


def _causal_invalid_reasons(
    *,
    accepted_llm_decisions: int,
    fallback_decisions: int,
    usage_complete_for_all_decisions: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fallback_decisions:
        reasons.append(LLM_CAUSAL_REASON_FALLBACK)
    if not usage_complete_for_all_decisions:
        reasons.append(LLM_CAUSAL_REASON_INCOMPLETE_USAGE)
    if accepted_llm_decisions == 0:
        reasons.append(LLM_CAUSAL_REASON_ZERO_ACCEPTED)
    return tuple(reasons)


@dataclass(frozen=True)
class LLMSearchLayerRecord:
    depth: int
    candidate_state_hashes: tuple[str, ...]
    selected_state_hashes: tuple[str, ...]
    beam_pruned_state_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "beam_pruned_state_count": self.beam_pruned_state_count,
            "candidate_state_hashes": list(self.candidate_state_hashes),
            "depth": self.depth,
            "selected_state_hashes": list(self.selected_state_hashes),
        }


@dataclass(frozen=True)
class LLMGuidedSearchResult(SearchResult):
    model: str = ""
    seed_label: str = ""
    protocol_version: str = LLM_SEARCH_PROTOCOL_VERSION
    llm_search_policy_version: str = LLM_SEARCH_POLICY_VERSION
    merge_policy_version: str = BATCHED_BEAM_MERGE_POLICY_VERSION
    ranking_schema_version: str = LLM_RANKING_SCHEMA_VERSION
    batch_size: int = LLM_BATCH_SIZE
    beam_width: int = LLM_BEAM_WIDTH
    decision_records: tuple[Mapping[str, Any], ...] = ()
    decision_artifacts: tuple[str, ...] = ()
    llm_layer_records: tuple[LLMSearchLayerRecord, ...] = ()
    llm_batch_states_pruned: int = 0
    llm_beam_states_pruned: int = 0
    fallback_decisions: int = 0
    invalid_response_decisions: int = 0
    accepted_llm_decisions: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    usage_complete_for_all_decisions: bool = True
    llm_causal_validity_policy_version: str = LLM_CAUSAL_VALIDITY_POLICY_VERSION
    llm_causal_valid: bool = False
    llm_causal_validity_status: str = LLM_CAUSAL_STATUS_INVALID
    llm_causal_invalid_reasons: tuple[str, ...] = (
        LLM_CAUSAL_REASON_ZERO_ACCEPTED,
    )
    llm_guided_scientific_run_eligible: bool = False
    run_header_artifact: str = "run_header.json"
    run_header_sha256: str = ""
    search_result_artifact: str = "search_result.json"
    llm_search_complete: bool = False
    self_certifies_success: bool = False
    success_evaluation: str = "EXTERNAL_EVALUATOR_REQUIRED"
    states_to_first_success: int | None = None
    time_to_first_success_seconds: float | None = None
    tokens_to_first_success: int | None = None
    symbolic_comparison_requires_matched_batch_control: bool = (
        SYMBOLIC_COMPARISON_REQUIRES_MATCHED_BATCH_CONTROL
    )
    symbolic_comparison_status: str = SYMBOLIC_COMPARISON_STATUS
    required_symbolic_control_condition: str = "S2_MATCHED_BATCH32"
    strongest_symbolic_baseline_condition: str = "S2"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.condition not in {"S4", "S5"}:
            raise ValueError("LLM_SEARCH_CONDITION_INVALID")
        if self.batch_size != LLM_BATCH_SIZE or self.beam_width != LLM_BEAM_WIDTH:
            raise ValueError("LLM_SEARCH_POLICY_NOT_FROZEN")
        if self.ordering_uses_verifier_outcomes or self.self_certifies_success:
            raise ValueError("LLM_SEARCH_CAUSAL_BOUNDARY_INVALID")
        if self.llm_tokens != self.prompt_tokens + self.completion_tokens:
            raise ValueError("LLM_SEARCH_TOKEN_TOTAL_MISMATCH")
        if not self.symbolic_comparison_requires_matched_batch_control:
            raise ValueError("LLM_SEARCH_UNMATCHED_COMPARISON_GATE_MISSING")
        if self.seed_label not in LLM_SEED_LABELS:
            raise ValueError("LLM_SEARCH_SEED_LABEL_INVALID")
        if self.seed != int(self.seed_label.removeprefix("seed-")):
            raise ValueError("LLM_SEARCH_SEED_BINDING_INVALID")
        if self.fallback_decisions != self.invalid_response_decisions:
            raise ValueError("LLM_SEARCH_INVALID_FALLBACK_COUNT_MISMATCH")
        if self.llm_causal_validity_policy_version != (
            LLM_CAUSAL_VALIDITY_POLICY_VERSION
        ):
            raise ValueError("LLM_SEARCH_CAUSAL_POLICY_NOT_FROZEN")
        if self.merge_policy_version != BATCHED_BEAM_MERGE_POLICY_VERSION:
            raise ValueError("LLM_SEARCH_MERGE_POLICY_NOT_FROZEN")
        if self.required_symbolic_control_condition != "S2_MATCHED_BATCH32":
            raise ValueError("LLM_SEARCH_MATCHED_CONTROL_INVALID")
        if self.strongest_symbolic_baseline_condition != "S2":
            raise ValueError("LLM_SEARCH_STRONGEST_SYMBOLIC_BASELINE_INVALID")
        expected_accepted = len(self.decision_records) - self.invalid_response_decisions
        if self.accepted_llm_decisions != expected_accepted:
            raise ValueError("LLM_SEARCH_ACCEPTED_DECISION_COUNT_MISMATCH")
        expected_reasons = _causal_invalid_reasons(
            accepted_llm_decisions=self.accepted_llm_decisions,
            fallback_decisions=self.fallback_decisions,
            usage_complete_for_all_decisions=self.usage_complete_for_all_decisions,
        )
        if self.llm_causal_invalid_reasons != expected_reasons:
            raise ValueError("LLM_SEARCH_CAUSAL_REASON_MISMATCH")
        expected_valid = not expected_reasons
        expected_status = (
            LLM_CAUSAL_STATUS_VALID if expected_valid else LLM_CAUSAL_STATUS_INVALID
        )
        if self.llm_causal_valid != expected_valid:
            raise ValueError("LLM_SEARCH_CAUSAL_VALIDITY_MISMATCH")
        if self.llm_causal_validity_status != expected_status:
            raise ValueError("LLM_SEARCH_CAUSAL_STATUS_MISMATCH")
        if self.llm_guided_scientific_run_eligible != expected_valid:
            raise ValueError("LLM_SEARCH_SCIENTIFIC_ELIGIBILITY_MISMATCH")
        object.__setattr__(
            self,
            "decision_records",
            tuple(freeze_json(item) for item in self.decision_records),
        )

    def to_dict(self, *, include_states: bool = False) -> dict[str, Any]:
        payload = super().to_dict(include_states=include_states)
        payload.update({
            "accepted_llm_decisions": self.accepted_llm_decisions,
            "batch_size": self.batch_size,
            "beam_width": self.beam_width,
            "completion_tokens": self.completion_tokens,
            "decision_artifacts": list(self.decision_artifacts),
            "decision_count": len(self.decision_records),
            "decision_records": [thaw_json(item) for item in self.decision_records],
            "fallback_decisions": self.fallback_decisions,
            "invalid_response_decisions": self.invalid_response_decisions,
            "llm_batch_states_pruned": self.llm_batch_states_pruned,
            "llm_beam_states_pruned": self.llm_beam_states_pruned,
            "llm_causal_invalid_reasons": list(self.llm_causal_invalid_reasons),
            "llm_causal_valid": self.llm_causal_valid,
            "llm_causal_validity_policy_version": (
                self.llm_causal_validity_policy_version
            ),
            "llm_causal_validity_status": self.llm_causal_validity_status,
            "llm_guided_scientific_run_eligible": (
                self.llm_guided_scientific_run_eligible
            ),
            "llm_layer_records": [item.to_dict() for item in self.llm_layer_records],
            "merge_policy_version": self.merge_policy_version,
            "llm_search_complete": self.llm_search_complete,
            "llm_search_policy_version": self.llm_search_policy_version,
            "model": self.model,
            "prompt_cache_hit_tokens": self.prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": self.prompt_cache_miss_tokens,
            "prompt_tokens": self.prompt_tokens,
            "protocol_version": self.protocol_version,
            "ranking_schema_version": self.ranking_schema_version,
            "reasoning_tokens": self.reasoning_tokens,
            "required_symbolic_control_condition": (
                self.required_symbolic_control_condition
            ),
            "run_header_artifact": self.run_header_artifact,
            "run_header_sha256": self.run_header_sha256,
            "search_result_artifact": self.search_result_artifact,
            "seed_label": self.seed_label,
            "self_certifies_success": self.self_certifies_success,
            "states_to_first_success": self.states_to_first_success,
            "strongest_symbolic_baseline_condition": (
                self.strongest_symbolic_baseline_condition
            ),
            "success_evaluation": self.success_evaluation,
            "time_to_first_success_seconds": self.time_to_first_success_seconds,
            "tokens_to_first_success": self.tokens_to_first_success,
            "usage_complete_for_all_decisions": self.usage_complete_for_all_decisions,
            "symbolic_comparison_requires_matched_batch_control": (
                self.symbolic_comparison_requires_matched_batch_control
            ),
            "symbolic_comparison_status": self.symbolic_comparison_status,
        })
        return payload


@dataclass(frozen=True)
class _Decision:
    ordered_children: tuple[SearchState, ...]
    record: Mapping[str, Any]
    artifact: str
    usage: TokenUsage
    fallback_used: bool
    batch_pruned: int


def _prompt_hash(request: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        canonical_json(request["messages"]).encode("utf-8")
    ).hexdigest()


def _candidate_batch_hash(candidate_records: list[dict[str, Any]]) -> str:
    return hashlib.sha256(
        canonical_json(candidate_records).encode("utf-8")
    ).hexdigest()


def _decision(
    *,
    condition: str,
    decision_index: int,
    case: PublicCase,
    current_state: SearchState,
    children: tuple[SearchState, ...],
    actions: tuple[Any, ...],
    transport: ChatCompletionsTransport,
    config: DeepSeekSearchConfig,
    decision_directory: Path,
    cumulative_tokens_before: int,
    run_header_sha256: str,
) -> _Decision:
    if not children or len(children) != len(actions):
        raise SearchContractError("LLM_DECISION_FRONTIER_INVALID")
    bounded_children = children[:LLM_BATCH_SIZE]
    bounded_actions = actions[:LLM_BATCH_SIZE]
    batch_pruned = len(children) - len(bounded_children)
    if condition == "S4":
        presented = candidate_state_items(bounded_children)
        audit_candidates = [dict(item) for item in presented]
    else:
        presented = legal_action_items(bounded_actions)
        audit_candidates = [
            {
                "action": dict(item["action"]),
                "opaque_id": item["opaque_id"],
                "resulting_state_hash": child.canonical_hash,
            }
            for item, child in zip(presented, bounded_children)
        ]
    request = build_ranking_request(
        condition=condition,
        config=config,
        case=case,
        current_state=current_state,
        candidate_items=presented,
    )
    expected_ids = tuple(item["opaque_id"] for item in presented)
    response = call_and_validate_ranking(
        transport,
        request,
        expected_ids=expected_ids,
        requested_model=config.model,
    )
    fallback_used = not response.valid
    ranking_used = response.ranking if response.valid else expected_ids
    child_by_id = {
        identifier: child
        for identifier, child in zip(expected_ids, bounded_children)
    }
    ordered_children = tuple(child_by_id[item] for item in ranking_used)
    chosen = ordered_children[0]
    total_tokens = response.usage.total_tokens or 0
    record: dict[str, Any] = {
        "candidate_batch": {
            "all_legal_child_count": len(children),
            "batch_pruned_count": batch_pruned,
            "candidate_records": audit_candidates,
            "candidate_records_sha256": _candidate_batch_hash(audit_candidates),
            "presented_count": len(audit_candidates),
        },
        "chosen_next_state_hash": chosen.canonical_hash,
        "condition": condition,
        "current_search_state": public_state_payload(current_state),
        "current_state_hash": current_state.canonical_hash,
        "decision_index": decision_index,
        "deepseek_config": config.to_dict(),
        "fallback": {
            "policy": LLM_FALLBACK_POLICY,
            "reason": response.error_code if fallback_used else None,
            "used": fallback_used,
        },
        "model": config.model,
        "private_reasoning_persisted": False,
        "protocol_version": LLM_SEARCH_PROTOCOL_VERSION,
        "provider_response": response.to_dict(),
        "public_request": request,
        "public_request_sha256": request_hash(request),
        "prompt_sha256": _prompt_hash(request),
        "ranking_schema_version": LLM_RANKING_SCHEMA_VERSION,
        "ranking_used": list(ranking_used),
        "response_ranking_accepted": response.valid,
        "run_header_sha256": run_header_sha256,
        "seed_label": config.seed_label,
        "tokens_cumulative_after_decision": cumulative_tokens_before + total_tokens,
    }
    record["decision_record_sha256"] = decision_record_hash(record)
    filename = f"decision_{decision_index:06d}.json"
    atomic_write_json(decision_directory / filename, record)
    return _Decision(
        ordered_children=ordered_children,
        record=MappingProxyType(record),
        artifact=filename,
        usage=response.usage,
        fallback_used=fallback_used,
        batch_pruned=batch_pruned,
    )


def _known(value: int | None) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _prepare_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise SearchContractError("LLM_DECISION_DIRECTORY_NOT_EMPTY")


def _run_header(
    *,
    condition: str,
    budget: int,
    case: PublicCase,
    grammar_id: str,
    pool: CandidatePool,
    policy: SearchPolicy,
    config: DeepSeekSearchConfig,
) -> dict[str, Any]:
    public_context = public_case_payload(case, grammar_id=grammar_id)
    header: dict[str, Any] = {
        "batch_policy": {
            "batch_size": LLM_BATCH_SIZE,
            "beam_width": LLM_BEAM_WIDTH,
            "cross_parent_priority": list(CROSS_PARENT_PRIORITY_FIELDS),
            "fallback_policy": LLM_FALLBACK_POLICY,
            "merge_policy_version": BATCHED_BEAM_MERGE_POLICY_VERSION,
            "policy_version": LLM_SEARCH_POLICY_VERSION,
            "presented_subset": "FIRST_32_M2_ORDERED_LEGAL_CHILDREN",
        },
        "budget_requested": budget,
        "candidate_pool": {
            "branching_incomplete": pool.branching_incomplete,
            "candidate_pool_sha256": pool.canonical_hash,
            "incompleteness_reasons": list(pool.incompleteness_reasons),
            "policy_version": pool.policy_version,
        },
        "condition": condition,
        "deepseek_config": config.to_dict(),
        "grammar_id": grammar_id,
        "ordering_uses_verifier_outcomes": False,
        "private_reasoning_persisted": False,
        "proposer_view_sha256": case.proposer_view_sha256,
        "protocol_version": LLM_SEARCH_PROTOCOL_VERSION,
        "public_case": case.public_manifest(),
        "public_context_sha256": hashlib.sha256(
            canonical_json(public_context).encode("utf-8")
        ).hexdigest(),
        "run_header_version": LLM_RUN_HEADER_VERSION,
        "llm_causal_validity_policy": {
            "fallback_is_diagnostic_only": True,
            "policy_version": LLM_CAUSAL_VALIDITY_POLICY_VERSION,
            "pre_call_status": "PENDING_FAIL_CLOSED",
            "valid_requires": [
                "AT_LEAST_ONE_ACCEPTED_LLM_DECISION",
                "ZERO_FALLBACK_DECISIONS",
                "COMPLETE_USAGE_FOR_EVERY_DECISION",
            ],
        },
        "search_policy": policy.to_dict(),
        "symbolic_comparison_requires_matched_batch_control": (
            SYMBOLIC_COMPARISON_REQUIRES_MATCHED_BATCH_CONTROL
        ),
        "symbolic_comparison_status": SYMBOLIC_COMPARISON_STATUS,
    }
    header["run_header_sha256"] = hashlib.sha256(
        canonical_json(header).encode("utf-8")
    ).hexdigest()
    return header


def llm_guided_search(
    case: PublicCase,
    *,
    condition: str,
    budget: int,
    transport: ChatCompletionsTransport,
    decision_directory: str | Path,
    config: DeepSeekSearchConfig | None = None,
    grammar_id: str = "G_FULL",
    candidate_pool: CandidatePool | None = None,
    policy: SearchPolicy | None = None,
) -> LLMGuidedSearchResult:
    """Run S4 or S5 without proof feedback or success self-evaluation."""
    if condition not in {"S4", "S5"}:
        raise SearchContractError(f"LLM_CONDITION_INVALID:{condition}")
    if budget not in BUDGET_STATES:
        raise SearchContractError(f"STATE_BUDGET_NOT_FROZEN:{budget}")
    frozen_config = config or DeepSeekSearchConfig()
    # Validate the entire proposer-visible context before creating any run
    # artifact or expanding any state.
    public_case_payload(case, grammar_id=grammar_id)
    started = time.perf_counter()
    pool = candidate_pool or extract_candidate_pool(case)
    frozen_policy = policy or SearchPolicy()
    if frozen_policy != SearchPolicy(
        latent_creation_enabled=frozen_policy.latent_creation_enabled
    ):
        raise SearchContractError("LLM_SEARCH_POLICY_NOT_FROZEN")
    output_directory = Path(decision_directory)
    _prepare_directory(output_directory)
    header = _run_header(
        condition=condition,
        budget=budget,
        case=case,
        grammar_id=grammar_id,
        pool=pool,
        policy=frozen_policy,
        config=frozen_config,
    )
    atomic_write_json(output_directory / "run_header.json", header)
    root = initial_state(case, grammar_id=grammar_id)
    layer: tuple[SearchState, ...] = (root,)
    expanded: list[SearchState] = []
    expanded_hashes: set[str] = set()
    trace: list[ExpansionRecord] = []
    decision_records: list[Mapping[str, Any]] = []
    decision_artifacts: list[str] = []
    layer_records: list[LLMSearchLayerRecord] = []
    rejection_counts: Counter[str] = Counter()
    duplicates = 0
    batch_pruned = 0
    beam_pruned = 0
    fallback_count = 0
    invalid_count = 0
    prompt_tokens = 0
    completion_tokens = 0
    reasoning_tokens = 0
    cache_hit_tokens = 0
    cache_miss_tokens = 0
    usage_complete = True
    stopped_for_budget = False

    while layer and len(expanded) < budget:
        next_candidates: dict[str, tuple[tuple[int, str, str], SearchState]] = {}
        for state in layer:
            if len(expanded) >= budget:
                stopped_for_budget = True
                break
            state_hash = state.canonical_hash
            if state_hash in expanded_hashes:
                duplicates += 1
                continue
            expansion = expand_state(state, case, pool, frozen_policy)
            expanded.append(state)
            expanded_hashes.add(state_hash)
            trace.append(ExpansionRecord(
                expansion_index=len(expanded),
                state_hash=state_hash,
                complexity=state.complexity,
                depth=state.depth,
                legal_child_hashes=tuple(
                    item.canonical_hash for item in expansion.children
                ),
            ))
            rejection_counts.update(expansion.rejected)
            if not expansion.children:
                continue
            decision = _decision(
                condition=condition,
                decision_index=len(decision_records) + 1,
                case=case,
                current_state=state,
                children=expansion.children,
                actions=expansion.actions,
                transport=transport,
                config=frozen_config,
                decision_directory=output_directory,
                cumulative_tokens_before=prompt_tokens + completion_tokens,
                run_header_sha256=header["run_header_sha256"],
            )
            decision_records.append(decision.record)
            decision_artifacts.append(decision.artifact)
            batch_pruned += decision.batch_pruned
            fallback_count += decision.fallback_used
            invalid_count += decision.fallback_used
            usage_complete = usage_complete and decision.usage.complete
            prompt_tokens += _known(decision.usage.prompt_tokens)
            completion_tokens += _known(decision.usage.completion_tokens)
            reasoning_tokens += _known(decision.usage.reasoning_tokens)
            cache_hit_tokens += _known(decision.usage.prompt_cache_hit_tokens)
            cache_miss_tokens += _known(decision.usage.prompt_cache_miss_tokens)
            for local_rank, child in enumerate(decision.ordered_children):
                child_hash = child.canonical_hash
                if child_hash in expanded_hashes:
                    duplicates += 1
                    continue
                key = cross_parent_rank_key(local_rank, state_hash, child_hash)
                prior = next_candidates.get(child_hash)
                if prior is None or key < prior[0]:
                    if prior is not None:
                        duplicates += 1
                    next_candidates[child_hash] = (key, child)
                else:
                    duplicates += 1

        if stopped_for_budget:
            break
        ranked_candidates = tuple(
            item[1]
            for item in sorted(next_candidates.values(), key=lambda item: item[0])
        )
        selected = ranked_candidates[:LLM_BEAM_WIDTH]
        pruned = max(0, len(ranked_candidates) - len(selected))
        beam_pruned += pruned
        layer_records.append(LLMSearchLayerRecord(
            depth=(selected[0].depth if selected else layer[0].depth + 1),
            candidate_state_hashes=tuple(
                item.canonical_hash for item in ranked_candidates
            ),
            selected_state_hashes=tuple(item.canonical_hash for item in selected),
            beam_pruned_state_count=pruned,
        ))
        layer = selected

    elapsed = time.perf_counter() - started
    beam_exhausted = not layer and not stopped_for_budget
    accepted_count = len(decision_records) - invalid_count
    causal_reasons = _causal_invalid_reasons(
        accepted_llm_decisions=accepted_count,
        fallback_decisions=fallback_count,
        usage_complete_for_all_decisions=usage_complete,
    )
    causal_valid = not causal_reasons
    result = LLMGuidedSearchResult(
        condition=condition,
        case_id=case.case_id,
        grammar_id=grammar_id,
        budget_requested=budget,
        states_expanded=len(expanded),
        frontier_exhausted=beam_exhausted,
        seed=frozen_config.seed,
        wall_time_seconds=elapsed,
        expanded_states=tuple(expanded),
        expansion_trace=tuple(trace),
        duplicate_states_pruned=duplicates,
        rejection_counts=MappingProxyType(dict(sorted(rejection_counts.items()))),
        candidate_pool=pool,
        policy=frozen_policy,
        public_case_manifest=public_manifest(case),
        ordering_uses_verifier_outcomes=False,
        generated_frontier_exhaustive=True,
        global_expression_enumeration_claimed=False,
        llm_tokens=prompt_tokens + completion_tokens,
        model=frozen_config.model,
        seed_label=frozen_config.seed_label,
        decision_records=tuple(decision_records),
        decision_artifacts=tuple(decision_artifacts),
        llm_layer_records=tuple(layer_records),
        llm_batch_states_pruned=batch_pruned,
        llm_beam_states_pruned=beam_pruned,
        fallback_decisions=fallback_count,
        invalid_response_decisions=invalid_count,
        accepted_llm_decisions=accepted_count,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        reasoning_tokens=reasoning_tokens,
        prompt_cache_hit_tokens=cache_hit_tokens,
        prompt_cache_miss_tokens=cache_miss_tokens,
        usage_complete_for_all_decisions=usage_complete,
        llm_causal_valid=causal_valid,
        llm_causal_validity_status=(
            LLM_CAUSAL_STATUS_VALID if causal_valid else LLM_CAUSAL_STATUS_INVALID
        ),
        llm_causal_invalid_reasons=causal_reasons,
        llm_guided_scientific_run_eligible=causal_valid,
        run_header_sha256=header["run_header_sha256"],
    )
    atomic_write_json(output_directory / result.search_result_artifact, result.to_dict())
    return result


def llm_state_ranking_search(
    case: PublicCase,
    **kwargs: Any,
) -> LLMGuidedSearchResult:
    return llm_guided_search(case, condition="S4", **kwargs)


def llm_action_proposal_search(
    case: PublicCase,
    **kwargs: Any,
) -> LLMGuidedSearchResult:
    return llm_guided_search(case, condition="S5", **kwargs)
