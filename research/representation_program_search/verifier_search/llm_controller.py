"""S7 LLM-plus-verifier search and its matched non-LLM S6 control.

Both conditions use the exact M2 legal frontier and S6 evaluation machinery.
The LLM can only permute a bounded set of already-legal child states; it never
sees verifier residuals, counterexamples, obligation receipts, or evaluator
targets.
"""
from __future__ import annotations

import hashlib
import time
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import thaw_json
from research.representation_program_search.search.beam_policy import (
    BANDED_BATCHED_BEAM_MERGE_POLICY_VERSION,
    BANDED_CROSS_PARENT_PRIORITY_FIELDS,
    MATCHED_LAYER_BEAM_WIDTH,
    MATCHED_PER_PARENT_BATCH_SIZE,
    banded_cross_parent_rank_key,
)
from research.representation_program_search.search.actions import SearchPolicy
from research.representation_program_search.search.llm_contract import (
    LLM_RANKING_SCHEMA_VERSION,
    LLM_RESPONSE_FORMAT,
    LLM_SEARCH_PROTOCOL_VERSION,
    LLM_SEED_LABELS,
    ChatCompletionsTransport,
    DeepSeekSearchConfig,
    TokenUsage,
    assert_llm_public_payload,
    call_and_validate_ranking,
    public_case_payload,
    request_hash,
)
from research.representation_program_search.search.llm_guided import (
    LLM_CAUSAL_STATUS_INVALID,
    LLM_CAUSAL_STATUS_VALID,
    LLM_CAUSAL_VALIDITY_POLICY_VERSION,
    LLM_FALLBACK_POLICY,
    llm_causal_invalid_reasons,
)

from .controller import (
    VerifierSearchController,
    _DominanceIndex,
    _atomic_json,
    _file_sha256,
    _safe_exception_code,
    _sha256_json,
)
from .m2_adapter import M2VerifierFrontierAdapter
from .model import (
    FEEDBACK_VALUES,
    FIXED_STATE_BUDGETS,
    FrontierContractError,
    VerifierFrontierNode,
    VerifierSearchPolicy,
    VerifierSearchResult,
)

S7_CONDITION = "S7"
S6_MATCHED_BATCH32_CONDITION = "S6_MATCHED_BATCH32"
VERIFIER_BATCHED_SEARCH_POLICY_VERSION = "RPSVerifierBatchedBeamPolicyV1"
S7_PROTOCOL_VERSION = "RPSS7LLMVerifierSearchV1"
S7_DECISION_SCHEMA_VERSION = "RPSS7VerifierStateDecisionV1"
S7_RUN_HEADER_VERSION = "RPSS7RunHeaderV1"
S7_COMPARISON_STATUS = "S6_MATCHED_BATCH32_CONTROL_REQUIRED"
S6_MATCHED_COMPARISON_STATUS = "MATCHED_BATCH32_DIAGNOSTIC_CONTROL"


def _known(value: int | None) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _canonical_local_order(
    children: tuple[VerifierFrontierNode, ...],
) -> tuple[VerifierFrontierNode, ...]:
    return tuple(sorted(children, key=lambda item: (item.complexity, item.canonical_hash)))


def _node_for_llm(node: VerifierFrontierNode) -> dict[str, Any]:
    public_state = thaw_json(node.public_state)
    search_state = public_state.get("search_state", public_state)
    payload = {
        "action_from_parent": (
            None
            if node.action_from_parent is None
            else thaw_json(node.action_from_parent)
        ),
        "complexity": node.complexity,
        "depth": node.depth,
        "grammar_id": node.context.grammar_id,
        "search_state": search_state,
        "search_state_hash": public_state.get("search_state_hash"),
        "state_hash": node.canonical_hash,
    }
    assert_llm_public_payload(payload)
    return payload


def _candidate_items(
    children: tuple[VerifierFrontierNode, ...],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for child in children:
        state = _node_for_llm(child)
        identity = {
            "action": state["action_from_parent"],
            "state_hash": child.canonical_hash,
        }
        opaque_id = "C_" + hashlib.sha256(
            canonical_json(identity).encode("utf-8")
        ).hexdigest()[:16]
        if opaque_id in seen:
            raise FrontierContractError("S7_OPAQUE_ID_COLLISION")
        seen.add(opaque_id)
        rows.append({
            "action": state["action_from_parent"],
            "opaque_id": opaque_id,
            "state": state,
        })
    return tuple(rows)


def _s7_request(
    *,
    config: DeepSeekSearchConfig,
    adapter: M2VerifierFrontierAdapter,
    current: VerifierFrontierNode,
    feedback: str | None,
    candidates: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    if feedback is not None and feedback not in FEEDBACK_VALUES:
        raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")
    user_payload = {
        "aggregate_feedback_class": feedback,
        "candidate_kind": "LEGAL_CHILD_STATE_WITH_TYPED_ACTION",
        "candidates": [dict(item) for item in candidates],
        "condition": S7_CONDITION,
        "current_search_state": _node_for_llm(current),
        "feedback_contract": sorted(FEEDBACK_VALUES),
        "public_case": public_case_payload(
            adapter.case, grammar_id=adapter.grammar_id
        ),
        "response_contract": {
            "schema_version": LLM_RANKING_SCHEMA_VERSION,
            "shape": {"ranking": ["OPAQUE_ID_1", "OPAQUE_ID_2"]},
            "strict_complete_permutation": True,
        },
        "seed_label": config.seed_label,
    }
    assert_llm_public_payload(user_payload)
    request = {
        "extra_body": {"thinking": {"type": config.thinking_type}},
        "max_tokens": config.max_tokens,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You rank already-legal child states in a formal mathematical "
                    "program search. Use only the supplied public state, typed "
                    "actions, and aggregate feedback class. Do not invent, alter, "
                    "explain, or omit candidates. Return JSON only, with exactly "
                    "one key named ranking whose value is a complete best-first "
                    "permutation of the opaque IDs. Example JSON: "
                    "{\"ranking\":[\"ID_A\",\"ID_B\"]}."
                ),
            },
            {"role": "user", "content": canonical_json(user_payload)},
        ],
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "response_format": dict(LLM_RESPONSE_FORMAT),
        "stream": False,
    }
    assert_llm_public_payload(request)
    return request


@dataclass(frozen=True)
class VerifierParentBatchRecord:
    parent_state_hash: str
    feedback_class: str | None
    feedback_priority_band: int
    all_legal_child_count: int
    presented_child_hashes: tuple[str, ...]
    ordered_child_hashes: tuple[str, ...]
    batch_pruned_state_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "all_legal_child_count": self.all_legal_child_count,
            "batch_pruned_state_count": self.batch_pruned_state_count,
            "feedback_class": self.feedback_class,
            "feedback_priority_band": self.feedback_priority_band,
            "ordered_child_hashes": list(self.ordered_child_hashes),
            "parent_state_hash": self.parent_state_hash,
            "presented_child_hashes": list(self.presented_child_hashes),
        }


@dataclass(frozen=True)
class VerifierBeamLayerRecord:
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
class BatchedVerifierSearchResult(VerifierSearchResult):
    batched_search_policy_version: str = VERIFIER_BATCHED_SEARCH_POLICY_VERSION
    merge_policy_version: str = BANDED_BATCHED_BEAM_MERGE_POLICY_VERSION
    batch_size: int = MATCHED_PER_PARENT_BATCH_SIZE
    beam_width: int = MATCHED_LAYER_BEAM_WIDTH
    batch_states_pruned: int = 0
    beam_states_pruned: int = 0
    parent_batches: tuple[VerifierParentBatchRecord, ...] = ()
    beam_layers: tuple[VerifierBeamLayerRecord, ...] = ()
    controller_header_sha256: str = ""
    batched_search_complete: bool = False
    frontier_matched_to_s7: bool = True
    strongest_full_frontier_s6: bool = False
    replaces_full_frontier_s6: bool = False
    verifier_comparison_status: str = S6_MATCHED_COMPARISON_STATUS

    def __post_init__(self) -> None:
        if self.condition not in {S6_MATCHED_BATCH32_CONDITION, S7_CONDITION}:
            raise ValueError("BATCHED_VERIFIER_CONDITION_INVALID")
        if (
            self.batch_size != MATCHED_PER_PARENT_BATCH_SIZE
            or self.beam_width != MATCHED_LAYER_BEAM_WIDTH
        ):
            raise ValueError("BATCHED_VERIFIER_POLICY_NOT_FROZEN")
        if self.merge_policy_version != BANDED_BATCHED_BEAM_MERGE_POLICY_VERSION:
            raise ValueError("BATCHED_VERIFIER_MERGE_POLICY_NOT_FROZEN")
        if self.strongest_full_frontier_s6 or self.replaces_full_frontier_s6:
            raise ValueError("BATCHED_VERIFIER_CANNOT_REPLACE_FULL_S6")
        if self.batched_search_complete or not self.frontier_matched_to_s7:
            raise ValueError("BATCHED_VERIFIER_COMPLETENESS_FLAG_INVALID")

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update({
            "batch_size": self.batch_size,
            "batch_states_pruned": self.batch_states_pruned,
            "batched_search_policy_version": self.batched_search_policy_version,
            "batched_search_complete": self.batched_search_complete,
            "beam_layers": [item.to_dict() for item in self.beam_layers],
            "beam_states_pruned": self.beam_states_pruned,
            "beam_width": self.beam_width,
            "condition": self.condition,
            "controller_header_sha256": self.controller_header_sha256,
            "cross_parent_priority": list(BANDED_CROSS_PARENT_PRIORITY_FIELDS),
            "frontier_matched_to_s7": self.frontier_matched_to_s7,
            "merge_policy_version": self.merge_policy_version,
            "parent_batches": [item.to_dict() for item in self.parent_batches],
            "replaces_full_frontier_s6": self.replaces_full_frontier_s6,
            "strongest_full_frontier_s6": self.strongest_full_frontier_s6,
            "verifier_comparison_status": self.verifier_comparison_status,
        })
        return payload


@dataclass(frozen=True)
class S7VerifierSearchResult(BatchedVerifierSearchResult):
    protocol_version: str = S7_PROTOCOL_VERSION
    model: str = ""
    seed: int = 0
    seed_label: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    prompt_cache_hit_tokens: int = 0
    prompt_cache_miss_tokens: int = 0
    tokens_to_first_success: int | None = None
    llm_decision_count: int = 0
    accepted_llm_decisions: int = 0
    fallback_decisions: int = 0
    invalid_response_decisions: int = 0
    usage_complete_for_all_decisions: bool = True
    llm_causal_validity_policy_version: str = LLM_CAUSAL_VALIDITY_POLICY_VERSION
    llm_causal_valid: bool = False
    llm_causal_validity_status: str = LLM_CAUSAL_STATUS_INVALID
    llm_causal_invalid_reasons: tuple[str, ...] = ()
    llm_guided_scientific_run_eligible: bool = False
    verifier_comparison_requires_matched_batch_control: bool = True
    required_verifier_control_condition: str = S6_MATCHED_BATCH32_CONDITION
    strongest_verifier_baseline_condition: str = "S6"
    verifier_comparison_status: str = S7_COMPARISON_STATUS

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.seed_label not in LLM_SEED_LABELS:
            raise ValueError("S7_SEED_LABEL_INVALID")
        if self.protocol_version != S7_PROTOCOL_VERSION:
            raise ValueError("S7_PROTOCOL_NOT_FROZEN")
        if self.seed != LLM_SEED_LABELS.index(self.seed_label):
            raise ValueError("S7_SEED_BINDING_INVALID")
        if self.llm_causal_validity_policy_version != (
            LLM_CAUSAL_VALIDITY_POLICY_VERSION
        ):
            raise ValueError("S7_CAUSAL_POLICY_NOT_FROZEN")
        if self.llm_tokens_used != self.prompt_tokens + self.completion_tokens:
            raise ValueError("S7_TOKEN_TOTAL_MISMATCH")
        if self.fallback_decisions != self.invalid_response_decisions:
            raise ValueError("S7_INVALID_FALLBACK_COUNT_MISMATCH")
        if self.accepted_llm_decisions != (
            self.llm_decision_count - self.invalid_response_decisions
        ):
            raise ValueError("S7_ACCEPTED_DECISION_COUNT_MISMATCH")
        reasons = llm_causal_invalid_reasons(
            accepted_llm_decisions=self.accepted_llm_decisions,
            fallback_decisions=self.fallback_decisions,
            usage_complete_for_all_decisions=self.usage_complete_for_all_decisions,
        )
        if self.llm_causal_invalid_reasons != reasons:
            raise ValueError("S7_CAUSAL_REASON_MISMATCH")
        valid = not reasons
        if self.llm_causal_valid != valid:
            raise ValueError("S7_CAUSAL_VALIDITY_MISMATCH")
        expected_status = LLM_CAUSAL_STATUS_VALID if valid else LLM_CAUSAL_STATUS_INVALID
        if self.llm_causal_validity_status != expected_status:
            raise ValueError("S7_CAUSAL_STATUS_MISMATCH")
        if self.llm_guided_scientific_run_eligible != valid:
            raise ValueError("S7_SCIENTIFIC_ELIGIBILITY_MISMATCH")
        if not self.verifier_comparison_requires_matched_batch_control:
            raise ValueError("S7_MATCHED_CONTROL_GATE_MISSING")
        if self.required_verifier_control_condition != S6_MATCHED_BATCH32_CONDITION:
            raise ValueError("S7_MATCHED_CONTROL_INVALID")

    def to_dict(self) -> dict[str, Any]:
        payload = super().to_dict()
        payload.update({
            "accepted_llm_decisions": self.accepted_llm_decisions,
            "completion_tokens": self.completion_tokens,
            "fallback_decisions": self.fallback_decisions,
            "invalid_response_decisions": self.invalid_response_decisions,
            "llm_causal_invalid_reasons": list(self.llm_causal_invalid_reasons),
            "llm_causal_valid": self.llm_causal_valid,
            "llm_causal_validity_policy_version": (
                self.llm_causal_validity_policy_version
            ),
            "llm_causal_validity_status": self.llm_causal_validity_status,
            "llm_decision_count": self.llm_decision_count,
            "llm_guided_scientific_run_eligible": (
                self.llm_guided_scientific_run_eligible
            ),
            "model": self.model,
            "prompt_cache_hit_tokens": self.prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": self.prompt_cache_miss_tokens,
            "prompt_tokens": self.prompt_tokens,
            "protocol_version": self.protocol_version,
            "reasoning_tokens": self.reasoning_tokens,
            "required_verifier_control_condition": (
                self.required_verifier_control_condition
            ),
            "seed": self.seed,
            "seed_label": self.seed_label,
            "strongest_verifier_baseline_condition": (
                self.strongest_verifier_baseline_condition
            ),
            "tokens_to_first_success": self.tokens_to_first_success,
            "usage_complete_for_all_decisions": (
                self.usage_complete_for_all_decisions
            ),
            "verifier_comparison_requires_matched_batch_control": (
                self.verifier_comparison_requires_matched_batch_control
            ),
        })
        return payload


@dataclass
class _LLMCounters:
    decisions: int = 0
    accepted: int = 0
    fallback: int = 0
    invalid: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    usage_complete: bool = True

    def add(self, usage: TokenUsage, *, valid: bool) -> None:
        self.decisions += 1
        self.accepted += int(valid)
        self.fallback += int(not valid)
        self.invalid += int(not valid)
        self.usage_complete = self.usage_complete and usage.complete
        self.prompt_tokens += _known(usage.prompt_tokens)
        self.completion_tokens += _known(usage.completion_tokens)
        self.reasoning_tokens += _known(usage.reasoning_tokens)
        self.cache_hit_tokens += _known(usage.prompt_cache_hit_tokens)
        self.cache_miss_tokens += _known(usage.prompt_cache_miss_tokens)


class _BatchedVerifierController(VerifierSearchController):
    """Shared execution path for S7 and S6_MATCHED_BATCH32."""

    def __init__(
        self,
        *,
        adapter: M2VerifierFrontierAdapter,
        output_root: str | Path,
        budget: int,
        condition: str,
        transport: ChatCompletionsTransport | None = None,
        config: DeepSeekSearchConfig | None = None,
        policy: VerifierSearchPolicy | None = None,
    ) -> None:
        if not isinstance(adapter, M2VerifierFrontierAdapter):
            raise FrontierContractError("BATCHED_VERIFIER_M2_ADAPTER_REQUIRED")
        if condition not in {S7_CONDITION, S6_MATCHED_BATCH32_CONDITION}:
            raise FrontierContractError("BATCHED_VERIFIER_CONDITION_INVALID")
        if adapter.search_policy != SearchPolicy(
            latent_creation_enabled=adapter.search_policy.latent_creation_enabled
        ):
            raise FrontierContractError("BATCHED_VERIFIER_SEARCH_POLICY_NOT_FROZEN")
        if condition == S7_CONDITION and transport is None:
            raise FrontierContractError("S7_TRANSPORT_REQUIRED")
        if condition != S7_CONDITION and (transport is not None or config is not None):
            raise FrontierContractError("S6_MATCHED_LLM_FORBIDDEN")
        self.adapter = adapter
        self.condition = condition
        self.transport = transport
        self.config = config or (DeepSeekSearchConfig() if condition == S7_CONDITION else None)
        super().__init__(
            output_root=output_root,
            budget=budget,
            condition=condition,
            policy=policy,
            expander=adapter.expand,
        )

    def _header(self) -> dict[str, Any]:
        public_context = public_case_payload(
            self.adapter.case, grammar_id=self.adapter.grammar_id
        )
        header: dict[str, Any] = {
            "adapter": self.adapter.public_contract(),
            "batch_policy": {
                "batch_size": MATCHED_PER_PARENT_BATCH_SIZE,
                "beam_width": MATCHED_LAYER_BEAM_WIDTH,
                "cross_parent_priority": list(BANDED_CROSS_PARENT_PRIORITY_FIELDS),
                "fallback_policy": (
                    LLM_FALLBACK_POLICY if self.condition == S7_CONDITION else None
                ),
                "merge_policy_version": BANDED_BATCHED_BEAM_MERGE_POLICY_VERSION,
                "policy_version": VERIFIER_BATCHED_SEARCH_POLICY_VERSION,
                "presented_subset": "FIRST_32_M2_ORDERED_LEGAL_CHILDREN",
            },
            "budget_requested": self.budget,
            "condition": self.condition,
            "feedback_values": sorted(FEEDBACK_VALUES),
            "private_reasoning_persisted": False,
            "protocol_version": S7_PROTOCOL_VERSION,
            "public_context_sha256": hashlib.sha256(
                canonical_json(public_context).encode("utf-8")
            ).hexdigest(),
            "run_header_version": S7_RUN_HEADER_VERSION,
            "state_budget_unit": "STATES_EXPANDED",
            "verifier_policy": self.policy.to_dict(),
            "verifier_success_gate": {
                "assumptions_complete": True,
                "compile_success": True,
                "leakage_cleared": True,
                "non_tautological": True,
                "required_obligations_all_zero": True,
                "receipts_required": True,
            },
            "verifier_comparison": {
                "required_matched_control": S6_MATCHED_BATCH32_CONDITION,
                "strongest_full_frontier_baseline": "S6",
            },
        }
        if self.config is not None:
            header["deepseek_config"] = self.config.to_dict()
            header["llm_ranking_protocol_version"] = LLM_SEARCH_PROTOCOL_VERSION
            header["llm_causal_validity_policy"] = {
                "fallback_is_diagnostic_only": True,
                "policy_version": LLM_CAUSAL_VALIDITY_POLICY_VERSION,
                "pre_call_status": "PENDING_FAIL_CLOSED",
                "valid_requires": [
                    "AT_LEAST_ONE_ACCEPTED_LLM_DECISION",
                    "ZERO_FALLBACK_DECISIONS",
                    "COMPLETE_USAGE_FOR_EVERY_DECISION",
                ],
            }
        header["controller_header_sha256"] = _sha256_json(header)
        return header

    def _initialize_batched_output(self) -> dict[str, Any]:
        # Validate all initial proposer-visible material before creating files.
        public_case_payload(self.adapter.case, grammar_id=self.adapter.grammar_id)
        root = self.adapter.initial_node()
        _node_for_llm(root)
        if self.output_root.exists():
            if any(self.output_root.iterdir()):
                raise FrontierContractError("OUTPUT_ROOT_NOT_EMPTY")
        else:
            self.output_root.mkdir(parents=True)
        (self.output_root / "decisions").mkdir(exist_ok=True)
        (self.output_root / "states").mkdir(exist_ok=True)
        header = self._header()
        _atomic_json(self.output_root / "controller.json", header)
        return header

    def run_batched(self) -> BatchedVerifierSearchResult:
        header = self._initialize_batched_output()
        started = time.perf_counter()
        root = self.adapter.initial_node()
        layer: tuple[VerifierFrontierNode, ...] = (root,)
        expanded_hashes: set[str] = set()
        public_contracts: dict[str, str] = {}
        decisions: list[dict[str, Any]] = []
        parent_batches: list[VerifierParentBatchRecord] = []
        beam_layers: list[VerifierBeamLayerRecord] = []
        successes: list[str] = []
        retained_unknown: list[str] = []
        disposition_counts: Counter[str] = Counter()
        feedback_counts: Counter[str] = Counter()
        obligation_verdict_counts: Counter[str] = Counter()
        dominance = _DominanceIndex()
        llm = _LLMCounters()
        duplicate_count = 0
        batch_pruned = 0
        beam_pruned = 0
        first_success: int | None = None
        time_to_first_success: float | None = None
        tokens_to_first_success: int | None = None
        stopped_for_budget = False

        while layer and len(decisions) < self.budget:
            next_candidates: dict[
                str, tuple[tuple[int, int, str, str], VerifierFrontierNode]
            ] = {}
            for node in layer:
                if len(decisions) >= self.budget:
                    stopped_for_budget = True
                    break
                state_hash = node.canonical_hash
                if state_hash in expanded_hashes:
                    duplicate_count += 1
                    continue
                public_contract = node.to_public_dict()
                public_contract.pop("action_from_parent", None)
                public_contract.pop("parent_hash", None)
                public_contract.pop("depth", None)
                contract_hash = _sha256_json(public_contract)
                previous = public_contracts.get(state_hash)
                if previous is not None and previous != contract_hash:
                    raise FrontierContractError("DUPLICATE_STATE_METADATA_CONFLICT")
                public_contracts[state_hash] = contract_hash
                expanded_hashes.add(state_hash)
                index = len(decisions) + 1
                decision_started = time.perf_counter()
                state_root = self.output_root / "states" / f"state_{index:05d}"
                state_root.mkdir(parents=True, exist_ok=False)

                if node.complete:
                    evaluation = self._evaluate_complete(node, state_root, dominance)
                else:
                    evaluation = {
                        "compiled_obligations": (),
                        "disposition": "PARTIAL_EXPANDED",
                        "feedback": None,
                        "reason": "INCOMPLETE_PROGRAM",
                    }
                feedback = evaluation["feedback"]
                if feedback is not None and feedback not in FEEDBACK_VALUES:
                    raise FrontierContractError(f"FEEDBACK_UNKNOWN:{feedback}")
                if (
                    evaluation["disposition"] == "PROGRAM_SUCCESS"
                    and first_success is None
                ):
                    first_success = index
                    time_to_first_success = time.perf_counter() - started
                    tokens_to_first_success = (
                        llm.prompt_tokens + llm.completion_tokens
                    )
                should_expand = (
                    evaluation["disposition"] != "PRE_VERIFICATION_INELIGIBLE"
                    and (feedback != "ZERO" or self.policy.continue_after_success)
                )
                expander_failure: str | None = None
                try:
                    children = self._expand(node, feedback) if should_expand else ()
                except Exception as exc:
                    children = ()
                    expander_failure = _safe_exception_code(exc)
                child_band = (
                    self.policy.initial_priority_band
                    if feedback is None
                    else self.policy.band_for_feedback(feedback)
                )
                presented = _canonical_local_order(
                    children[:MATCHED_PER_PARENT_BATCH_SIZE]
                )
                batch_pruned_for_parent = len(children) - len(presented)
                batch_pruned += batch_pruned_for_parent
                candidate_records = _candidate_items(presented) if presented else ()
                expected_ids = tuple(item["opaque_id"] for item in candidate_records)
                request: Mapping[str, Any] | None = None
                provider_response: Mapping[str, Any] | None = None
                fallback = {"policy": None, "reason": None, "used": False}
                if presented and self.condition == S7_CONDITION:
                    if self.config is None or self.transport is None:
                        raise FrontierContractError("S7_CLIENT_CONFIG_MISSING")
                    request = _s7_request(
                        config=self.config,
                        adapter=self.adapter,
                        current=node,
                        feedback=feedback,
                        candidates=candidate_records,
                    )
                    response = call_and_validate_ranking(
                        self.transport,
                        request,
                        expected_ids=expected_ids,
                        requested_model=self.config.model,
                    )
                    llm.add(response.usage, valid=response.valid)
                    ranking = response.ranking if response.valid else expected_ids
                    provider_response = response.to_dict()
                    fallback = {
                        "policy": LLM_FALLBACK_POLICY,
                        "reason": response.error_code if not response.valid else None,
                        "used": not response.valid,
                    }
                else:
                    ranking = expected_ids
                child_by_id = {
                    item["opaque_id"]: child
                    for item, child in zip(candidate_records, presented)
                }
                ordered = tuple(child_by_id[item] for item in ranking)
                parent_batches.append(VerifierParentBatchRecord(
                    parent_state_hash=state_hash,
                    feedback_class=feedback,
                    feedback_priority_band=child_band,
                    all_legal_child_count=len(children),
                    presented_child_hashes=tuple(
                        child.canonical_hash for child in presented
                    ),
                    ordered_child_hashes=tuple(child.canonical_hash for child in ordered),
                    batch_pruned_state_count=batch_pruned_for_parent,
                ))
                for local_rank, child in enumerate(ordered):
                    child_hash = child.canonical_hash
                    if child_hash in expanded_hashes:
                        duplicate_count += 1
                        continue
                    key = banded_cross_parent_rank_key(
                        child_band, local_rank, state_hash, child_hash
                    )
                    prior = next_candidates.get(child_hash)
                    if prior is None or key < prior[0]:
                        if prior is not None:
                            duplicate_count += 1
                        next_candidates[child_hash] = (key, child)
                    else:
                        duplicate_count += 1

                if feedback is not None:
                    feedback_counts[feedback] += 1
                disposition = evaluation["disposition"]
                disposition_counts[disposition] += 1
                if disposition == "PROGRAM_SUCCESS":
                    successes.append(state_hash)
                if disposition == "RETAINED_LOWER_PRIORITY":
                    retained_unknown.append(state_hash)

                obligation_rows = tuple(evaluation.pop("compiled_obligations", ()))
                for row in obligation_rows:
                    obligation_verdict_counts[row["verdict"]] += 1
                evaluation_payload = {
                    "disposition": disposition,
                    "evaluation": evaluation,
                    "feedback_class": feedback,
                    "obligations": list(obligation_rows),
                    "schema_version": "RPSBatchedVerifierEvaluationV1",
                    "state_hash": state_hash,
                }
                semantic_evaluation_inputs = {
                    "disposition": disposition,
                    "evaluation": evaluation,
                    "feedback_class": feedback,
                    "obligations": [
                        {
                            "member_id": row["member_id"],
                            "obligation_hash": row["obligation_hash"],
                            "obligation_id": row["obligation_id"],
                            "required": row["required"],
                            "semantic_evidence_hash": row["semantic_evidence_hash"],
                            "verdict": row["verdict"],
                        }
                        for row in obligation_rows
                    ],
                    "state_hash": state_hash,
                }
                evaluation_payload["semantic_evaluation_sha256"] = _sha256_json(
                    semantic_evaluation_inputs
                )
                evaluation_path = state_root / "evaluation.json"
                _atomic_json(evaluation_path, evaluation_payload)
                evaluation_sha256 = _file_sha256(evaluation_path)

                decision_payload: dict[str, Any] = {
                    "candidate_batch": {
                        "all_legal_child_count": len(children),
                        "batch_pruned_count": batch_pruned_for_parent,
                        "candidate_records": list(candidate_records),
                        "candidate_records_sha256": _sha256_json(
                            list(candidate_records)
                        ),
                        "presented_count": len(candidate_records),
                    },
                    "chosen_next_state_hash": (
                        ordered[0].canonical_hash if ordered else None
                    ),
                    "condition": self.condition,
                    "current_search_state": _node_for_llm(node),
                    "current_state_hash": state_hash,
                    "decision_index": index,
                    "disposition": disposition,
                    "expander_failure": expander_failure,
                    "fallback": fallback,
                    "feedback_class": feedback,
                    "feedback_priority_band": child_band,
                    "ordered_next_state_hashes": [
                        child.canonical_hash for child in ordered
                    ],
                    "private_reasoning_persisted": False,
                    "protocol_version": S7_PROTOCOL_VERSION,
                    "provider_response": provider_response,
                    "public_request": request,
                    "public_request_sha256": (
                        request_hash(request) if request is not None else None
                    ),
                    "ranking_used": list(ranking),
                    "run_header_sha256": header["controller_header_sha256"],
                    "schema_version": S7_DECISION_SCHEMA_VERSION,
                    "state_evaluation_artifact": evaluation_path.relative_to(
                        self.output_root
                    ).as_posix(),
                    "state_evaluation_sha256": evaluation_sha256,
                    "state_evaluation_semantic_sha256": evaluation_payload[
                        "semantic_evaluation_sha256"
                    ],
                    "token_usage_cumulative": {
                        "completion_tokens": llm.completion_tokens,
                        "prompt_tokens": llm.prompt_tokens,
                        "reasoning_tokens": llm.reasoning_tokens,
                        "total_tokens": llm.prompt_tokens + llm.completion_tokens,
                    },
                    "wall_time_seconds": time.perf_counter() - decision_started,
                }
                semantic_decision_inputs = {
                    "candidate_state_hashes": [
                        child.canonical_hash for child in presented
                    ],
                    "condition": self.condition,
                    "decision_index": index,
                    "disposition": disposition,
                    "feedback_class": feedback,
                    "feedback_priority_band": child_band,
                    "ordered_next_state_hashes": decision_payload[
                        "ordered_next_state_hashes"
                    ],
                    "public_request_sha256": decision_payload[
                        "public_request_sha256"
                    ],
                    "ranking_used": list(ranking),
                    "state_evaluation_semantic_sha256": decision_payload[
                        "state_evaluation_semantic_sha256"
                    ],
                    "state_hash": state_hash,
                }
                decision_payload["semantic_decision_hash"] = _sha256_json(
                    semantic_decision_inputs
                )
                decision_payload["decision_hash"] = _sha256_json(decision_payload)
                decision_path = (
                    self.output_root / "decisions" / f"decision_{index:05d}.json"
                )
                _atomic_json(decision_path, decision_payload)
                decisions.append(decision_payload)
                if expander_failure is not None:
                    raise FrontierContractError(
                        f"EXPANDER_FAILURE:{expander_failure}"
                    )

            if stopped_for_budget:
                break
            ranked_candidates = tuple(
                item[1]
                for item in sorted(next_candidates.values(), key=lambda item: item[0])
            )
            selected = ranked_candidates[:MATCHED_LAYER_BEAM_WIDTH]
            pruned = max(0, len(ranked_candidates) - len(selected))
            beam_pruned += pruned
            beam_layers.append(VerifierBeamLayerRecord(
                depth=(selected[0].depth if selected else layer[0].depth + 1),
                candidate_state_hashes=tuple(
                    item.canonical_hash for item in ranked_candidates
                ),
                selected_state_hashes=tuple(item.canonical_hash for item in selected),
                beam_pruned_state_count=pruned,
            ))
            layer = selected

        success_at: dict[str, bool | None] = {}
        for checkpoint in FIXED_STATE_BUDGETS:
            success_at[f"SUCCESS@{checkpoint}"] = (
                None
                if checkpoint > self.budget
                else first_success is not None and first_success <= checkpoint
            )
        decision_hashes = tuple(item["decision_hash"] for item in decisions)
        semantic_decision_hashes = tuple(
            item["semantic_decision_hash"] for item in decisions
        )
        common = {
            "condition": self.condition,
            "budget_requested": self.budget,
            "states_expanded": len(decisions),
            "frontier_exhausted": not layer and not stopped_for_budget,
            "first_success_index": first_success,
            "successful_state_hashes": tuple(successes),
            "retained_unknown_state_hashes": tuple(retained_unknown),
            "duplicate_states_pruned": duplicate_count,
            "disposition_counts": dict(sorted(disposition_counts.items())),
            "feedback_counts": {
                value: feedback_counts.get(value, 0)
                for value in sorted(FEEDBACK_VALUES)
            },
            "obligation_verdict_counts": {
                value: obligation_verdict_counts.get(value, 0)
                for value in sorted(FEEDBACK_VALUES)
            },
            "success_at": success_at,
            "decision_hashes": decision_hashes,
            "trace_hash": _sha256_json(list(decision_hashes)),
            "semantic_decision_hashes": semantic_decision_hashes,
            "semantic_trace_hash": _sha256_json(list(semantic_decision_hashes)),
            "wall_time_seconds": time.perf_counter() - started,
            "time_to_first_success_seconds": time_to_first_success,
            "output_root": str(self.output_root),
            "policy": self.policy,
            "batch_states_pruned": batch_pruned,
            "beam_states_pruned": beam_pruned,
            "parent_batches": tuple(parent_batches),
            "beam_layers": tuple(beam_layers),
            "controller_header_sha256": header["controller_header_sha256"],
        }
        if self.condition == S7_CONDITION:
            if self.config is None:
                raise FrontierContractError("S7_CLIENT_CONFIG_MISSING")
            reasons = llm_causal_invalid_reasons(
                accepted_llm_decisions=llm.accepted,
                fallback_decisions=llm.fallback,
                usage_complete_for_all_decisions=llm.usage_complete,
            )
            causal_valid = not reasons
            result: BatchedVerifierSearchResult = S7VerifierSearchResult(
                **common,
                llm_tokens_used=llm.prompt_tokens + llm.completion_tokens,
                model=self.config.model,
                seed=self.config.seed,
                seed_label=self.config.seed_label,
                prompt_tokens=llm.prompt_tokens,
                completion_tokens=llm.completion_tokens,
                reasoning_tokens=llm.reasoning_tokens,
                prompt_cache_hit_tokens=llm.cache_hit_tokens,
                prompt_cache_miss_tokens=llm.cache_miss_tokens,
                llm_decision_count=llm.decisions,
                accepted_llm_decisions=llm.accepted,
                fallback_decisions=llm.fallback,
                invalid_response_decisions=llm.invalid,
                usage_complete_for_all_decisions=llm.usage_complete,
                llm_causal_valid=causal_valid,
                llm_causal_validity_status=(
                    LLM_CAUSAL_STATUS_VALID
                    if causal_valid
                    else LLM_CAUSAL_STATUS_INVALID
                ),
                llm_causal_invalid_reasons=reasons,
                llm_guided_scientific_run_eligible=causal_valid,
                tokens_to_first_success=tokens_to_first_success,
            )
        else:
            result = BatchedVerifierSearchResult(
                **common,
                llm_tokens_used=0,
            )
        _atomic_json(self.output_root / "result.json", result.to_dict())
        return result


def llm_verifier_search(
    adapter: M2VerifierFrontierAdapter,
    *,
    output_root: str | Path,
    budget: int,
    transport: ChatCompletionsTransport,
    config: DeepSeekSearchConfig | None = None,
    policy: VerifierSearchPolicy | None = None,
) -> S7VerifierSearchResult:
    """Run S7 over an exact M2 adapter; success remains exact S6 success."""
    result = _BatchedVerifierController(
        adapter=adapter,
        output_root=output_root,
        budget=budget,
        condition=S7_CONDITION,
        transport=transport,
        config=config,
        policy=policy,
    ).run_batched()
    if not isinstance(result, S7VerifierSearchResult):
        raise FrontierContractError("S7_RESULT_TYPE_INVALID")
    return result


def verifier_matched_batch32_search(
    adapter: M2VerifierFrontierAdapter,
    *,
    output_root: str | Path,
    budget: int,
    policy: VerifierSearchPolicy | None = None,
) -> BatchedVerifierSearchResult:
    """Run the non-LLM matched diagnostic; full-frontier S6 remains strongest."""
    return _BatchedVerifierController(
        adapter=adapter,
        output_root=output_root,
        budget=budget,
        condition=S6_MATCHED_BATCH32_CONDITION,
        policy=policy,
    ).run_batched()
