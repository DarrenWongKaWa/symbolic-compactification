"""Fail-closed DeepSeek ranking contract for RPS S4/S5.

This module is intentionally independent of ``research.llm_abstraction``.
In particular, it never reads, hashes, truncates, records, or reuses provider
``reasoning_content``.  Only the final JSON object and explicit usage/request
provenance cross the response boundary.

Official API references frozen for this implementation review:

* https://api-docs.deepseek.com/api/create-chat-completion/
* https://api-docs.deepseek.com/guides/thinking_mode/
* https://api-docs.deepseek.com/guides/json_mode/
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from research.representation_program_search.grammar_v1 import (
    ACTIONS,
    G_PRIMITIVE_OPS,
    GRAMMAR_ID,
    LATENT_FORMS,
    OPERATORS,
)
from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.program_ir.model import thaw_json

from .model import LegalAction, SearchContractError, SearchState
from .public_case import PublicCase

LLM_SEARCH_PROTOCOL_VERSION = "RPSLLMSearchProtocolV1"
LLM_RANKING_SCHEMA_VERSION = "RPSOpaquePermutationV1"
LLM_PRIMARY_MODEL = "deepseek-v4-pro"
LLM_ROBUSTNESS_MODEL = "deepseek-v4-flash"
LLM_ALLOWED_MODELS = (LLM_PRIMARY_MODEL, LLM_ROBUSTNESS_MODEL)
LLM_SEED_LABELS = tuple(f"seed-{index}" for index in range(5))
LLM_REASONING_EFFORT = "high"
LLM_THINKING_TYPE = "enabled"
LLM_RESPONSE_FORMAT = MappingProxyType({"type": "json_object"})
LLM_MAX_TOKENS = 4096
LLM_BASE_URL = "https://api.deepseek.com"
LLM_BATCH_SIZE = 32
LLM_BEAM_WIDTH = 32

OFFICIAL_DEEPSEEK_DOCS = (
    "https://api-docs.deepseek.com/api/create-chat-completion/",
    "https://api-docs.deepseek.com/guides/thinking_mode/",
    "https://api-docs.deepseek.com/guides/json_mode/",
)

_LLM_FORBIDDEN_PUBLIC_KEYS = {
    "audited_depth",
    "compiled_obligations",
    "counterexample",
    "gold",
    "gold_operator_sequence",
    "gold_program",
    "hidden_member_roles",
    "proof_status",
    "reference",
    "representation_depth",
    "residual",
    "target",
    "target_representation",
    "target_type",
    "verdict",
    "verification",
    "verified_obligations",
}
_LLM_FORBIDDEN_PATH_PARTS = {"final", "reference", "runs", "steps", "verification"}
_PRIVATE_REASONING_KEYS = {
    "chain_of_thought", "cot", "reasoning", "reasoning_content", "reasoning_tail"
}


@dataclass(frozen=True)
class DeepSeekSearchConfig:
    """Frozen Chat Completions configuration; only model/seed vary by arm."""

    model: str = LLM_PRIMARY_MODEL
    seed_label: str = LLM_SEED_LABELS[0]
    protocol_version: str = LLM_SEARCH_PROTOCOL_VERSION
    max_tokens: int = LLM_MAX_TOKENS
    reasoning_effort: str = LLM_REASONING_EFFORT
    thinking_type: str = LLM_THINKING_TYPE

    def __post_init__(self) -> None:
        if self.model not in LLM_ALLOWED_MODELS:
            raise SearchContractError(f"LLM_MODEL_NOT_FROZEN:{self.model}")
        if self.seed_label not in LLM_SEED_LABELS:
            raise SearchContractError(f"LLM_SEED_LABEL_NOT_FROZEN:{self.seed_label}")
        if self.protocol_version != LLM_SEARCH_PROTOCOL_VERSION:
            raise SearchContractError("LLM_PROTOCOL_NOT_FROZEN")
        if self.max_tokens != LLM_MAX_TOKENS:
            raise SearchContractError("LLM_MAX_TOKENS_NOT_FROZEN")
        if self.reasoning_effort != LLM_REASONING_EFFORT:
            raise SearchContractError("LLM_REASONING_EFFORT_NOT_FROZEN")
        if self.thinking_type != LLM_THINKING_TYPE:
            raise SearchContractError("LLM_THINKING_MODE_NOT_FROZEN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "base_url": LLM_BASE_URL,
            "max_tokens": self.max_tokens,
            "model": self.model,
            "protocol_version": self.protocol_version,
            "reasoning_effort": self.reasoning_effort,
            "response_format": dict(LLM_RESPONSE_FORMAT),
            "seed_label": self.seed_label,
            "thinking": {"type": self.thinking_type},
        }


class ChatCompletionsTransport(Protocol):
    """Minimal injectable transport; unit tests provide a mock."""

    def complete(self, request: Mapping[str, Any]) -> Any:
        ...


class OpenAIChatCompletionsTransport:
    """OpenAI-compatible DeepSeek Chat Completions transport.

    The key lives only inside the SDK client and is never exposed by the
    request/decision serialization path.
    """

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = LLM_BASE_URL,
        timeout_seconds: float = 180.0,
    ) -> None:
        if not isinstance(api_key, str) or not api_key:
            raise SearchContractError("LLM_API_KEY_MISSING")
        if base_url != LLM_BASE_URL:
            raise SearchContractError("LLM_BASE_URL_NOT_FROZEN")
        try:
            from openai import OpenAI
        except ImportError:
            raise SearchContractError("LLM_OPENAI_SDK_MISSING") from None
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )

    def complete(self, request: Mapping[str, Any]) -> Any:
        return self._client.chat.completions.create(**dict(request))


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def assert_llm_public_payload(value: Any) -> None:
    """Reject evaluator/proof fields at the S4/S5 serialization boundary."""
    def visit(child: Any) -> None:
        if isinstance(child, Mapping):
            for key, nested in child.items():
                normalized = str(key).lower()
                if (
                    normalized in _LLM_FORBIDDEN_PUBLIC_KEYS
                    or normalized.startswith("gold_")
                ):
                    raise SearchContractError(f"LLM_PUBLIC_FIELD_FORBIDDEN:{key}")
                if normalized == "path" and isinstance(nested, str):
                    if _LLM_FORBIDDEN_PATH_PARTS & {
                        item.lower() for item in Path(nested).parts
                    }:
                        raise SearchContractError(
                            f"LLM_PUBLIC_PATH_FORBIDDEN:{nested}"
                        )
                visit(nested)
        elif isinstance(child, (list, tuple)):
            for nested in child:
                visit(nested)

    visit(value)


def _contains_private_reasoning_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            str(key).lower() in _PRIVATE_REASONING_KEYS
            or _contains_private_reasoning_key(child)
            for key, child in value.items()
        )
    if isinstance(value, list):
        return any(_contains_private_reasoning_key(child) for child in value)
    return False


@dataclass(frozen=True)
class TokenUsage:
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    prompt_cache_hit_tokens: int | None
    prompt_cache_miss_tokens: int | None
    reasoning_tokens: int | None

    @property
    def complete(self) -> bool:
        values = (
            self.prompt_tokens,
            self.completion_tokens,
            self.total_tokens,
            self.prompt_cache_hit_tokens,
            self.prompt_cache_miss_tokens,
            self.reasoning_tokens,
        )
        return all(
            isinstance(item, int) and not isinstance(item, bool) and item >= 0
            for item in values
        ) and self.total_tokens == self.prompt_tokens + self.completion_tokens

    @classmethod
    def empty(cls) -> "TokenUsage":
        return cls(None, None, None, None, None, None)

    @classmethod
    def from_provider(cls, response: Any) -> "TokenUsage":
        usage = _get(response, "usage")
        details = _get(usage, "completion_tokens_details")
        return cls(
            prompt_tokens=_get(usage, "prompt_tokens"),
            completion_tokens=_get(usage, "completion_tokens"),
            total_tokens=_get(usage, "total_tokens"),
            prompt_cache_hit_tokens=_get(usage, "prompt_cache_hit_tokens"),
            prompt_cache_miss_tokens=_get(usage, "prompt_cache_miss_tokens"),
            reasoning_tokens=_get(details, "reasoning_tokens"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "completion_tokens": self.completion_tokens,
            "complete": self.complete,
            "prompt_cache_hit_tokens": self.prompt_cache_hit_tokens,
            "prompt_cache_miss_tokens": self.prompt_cache_miss_tokens,
            "prompt_tokens": self.prompt_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class RankingResponse:
    valid: bool
    ranking: tuple[str, ...]
    raw_structured_final_response: Mapping[str, Any] | None
    error_code: str | None
    usage: TokenUsage
    request_id: str | None
    response_model: str | None
    finish_reason: str | None
    latency_seconds: float
    raw_final_content_sha256: str | None
    raw_final_content_chars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "finish_reason": self.finish_reason,
            "latency_seconds": self.latency_seconds,
            "ranking": list(self.ranking),
            "raw_final_content_chars": self.raw_final_content_chars,
            "raw_final_content_sha256": self.raw_final_content_sha256,
            "raw_structured_final_response": (
                None
                if self.raw_structured_final_response is None
                else dict(self.raw_structured_final_response)
            ),
            "request_id": self.request_id,
            "response_model": self.response_model,
            "usage": self.usage.to_dict(),
            "valid": self.valid,
        }


def _invalid_response(
    *,
    code: str,
    usage: TokenUsage,
    request_id: str | None,
    response_model: str | None,
    finish_reason: str | None,
    latency_seconds: float,
    raw: Mapping[str, Any] | None = None,
    content: str = "",
) -> RankingResponse:
    return RankingResponse(
        valid=False,
        ranking=(),
        raw_structured_final_response=raw,
        error_code=code,
        usage=usage,
        request_id=request_id,
        response_model=response_model,
        finish_reason=finish_reason,
        latency_seconds=latency_seconds,
        raw_final_content_sha256=(
            hashlib.sha256(content.encode("utf-8")).hexdigest()
            if content else None
        ),
        raw_final_content_chars=len(content),
    )


def call_and_validate_ranking(
    transport: ChatCompletionsTransport,
    request: Mapping[str, Any],
    *,
    expected_ids: tuple[str, ...],
    requested_model: str,
) -> RankingResponse:
    """Call once and project only final JSON/provenance from the response.

    The provider response may contain private reasoning fields.  They are not
    accessed at all, so they cannot enter this return value or later records.
    """
    started = time.perf_counter()
    try:
        response = transport.complete(request)
    except Exception as exc:
        return _invalid_response(
            code=f"API_FAILURE:{type(exc).__name__}",
            usage=TokenUsage.empty(),
            request_id=None,
            response_model=None,
            finish_reason=None,
            latency_seconds=time.perf_counter() - started,
        )
    latency = time.perf_counter() - started
    usage = TokenUsage.from_provider(response)
    request_id = _get(response, "id")
    response_model = _get(response, "model")
    choices = _get(response, "choices")
    if not isinstance(choices, (list, tuple)) or len(choices) != 1:
        return _invalid_response(
            code="RESPONSE_CHOICE_COUNT_INVALID",
            usage=usage,
            request_id=request_id,
            response_model=response_model,
            finish_reason=None,
            latency_seconds=latency,
        )
    choice = choices[0]
    finish_reason = _get(choice, "finish_reason")
    message = _get(choice, "message")
    content = _get(message, "content", "")
    if not isinstance(content, str):
        content = ""
    common = {
        "usage": usage,
        "request_id": request_id if isinstance(request_id, str) else None,
        "response_model": response_model if isinstance(response_model, str) else None,
        "finish_reason": finish_reason if isinstance(finish_reason, str) else None,
        "latency_seconds": latency,
        "content": content,
    }
    if finish_reason != "stop":
        return _invalid_response(code="RESPONSE_FINISH_REASON_INVALID", **common)
    if response_model != requested_model:
        return _invalid_response(code="RESPONSE_MODEL_MISMATCH", **common)
    if not isinstance(request_id, str) or not request_id:
        return _invalid_response(code="RESPONSE_REQUEST_ID_MISSING", **common)
    if not usage.complete:
        return _invalid_response(code="RESPONSE_USAGE_INCOMPLETE", **common)
    try:
        parsed = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return _invalid_response(code="RESPONSE_JSON_INVALID", **common)
    if not isinstance(parsed, Mapping):
        return _invalid_response(code="RESPONSE_JSON_NOT_OBJECT", **common)
    raw = dict(parsed)
    if _contains_private_reasoning_key(raw):
        # Never persist even an accidentally copied provider reasoning field.
        # The content hash/length remain sufficient to audit the failed call.
        return _invalid_response(
            code="RESPONSE_PRIVATE_REASONING_FIELD_FORBIDDEN", **common
        )
    if set(raw) != {"ranking"}:
        return _invalid_response(
            code="RANKING_FIELDS_INVALID", raw=raw, **common
        )
    ranking = raw["ranking"]
    if not isinstance(ranking, list) or not all(
        isinstance(item, str) and item for item in ranking
    ):
        return _invalid_response(code="RANKING_NOT_STRING_LIST", raw=raw, **common)
    if len(ranking) != len(set(ranking)):
        return _invalid_response(code="RANKING_DUPLICATE_ID", raw=raw, **common)
    expected = set(expected_ids)
    actual = set(ranking)
    if actual - expected:
        return _invalid_response(code="RANKING_UNKNOWN_ID", raw=raw, **common)
    if expected - actual or len(ranking) != len(expected_ids):
        return _invalid_response(code="RANKING_MISSING_ID", raw=raw, **common)
    return RankingResponse(
        valid=True,
        ranking=tuple(ranking),
        raw_structured_final_response=raw,
        error_code=None,
        usage=usage,
        request_id=request_id,
        response_model=response_model,
        finish_reason=finish_reason,
        latency_seconds=latency,
        raw_final_content_sha256=hashlib.sha256(
            content.encode("utf-8")
        ).hexdigest(),
        raw_final_content_chars=len(content),
    )


def _allowed_operators(grammar_id: str) -> tuple[str, ...]:
    if grammar_id == "G_FULL":
        return OPERATORS
    if grammar_id == "G_NO_HERMITE":
        return tuple(item for item in OPERATORS if item != "HERMITE_DD")
    return G_PRIMITIVE_OPS


def public_case_payload(case: PublicCase, *, grammar_id: str) -> dict[str, Any]:
    """Return the exact proposer-visible scientific context."""
    payload = {
        "assumptions": thaw_json(case.assumptions),
        "case_id": case.case_id,
        "functions": list(case.functions),
        "grammar": {
            "actions": list(ACTIONS),
            "allowed_operators": list(_allowed_operators(grammar_id)),
            "grammar_id": grammar_id,
            "grammar_version": GRAMMAR_ID,
            "latent_forms": list(LATENT_FORMS),
        },
        "namespace_provenance": case.namespace_provenance,
        "source_catalog": {
            "members": [
                {
                    "expression": member.expression,
                    "member_id": member.member_id,
                    "path": member.path,
                    "sha256": member.sha256,
                }
                for member in case.members
            ],
            "symbols": [thaw_json(item) for item in case.symbols],
        },
    }
    assert_llm_public_payload(payload)
    return payload


def public_state_payload(state: SearchState) -> dict[str, Any]:
    """Strip ancestry, compile data, scores, and proof evidence from a state."""
    payload = {
        "complexity": state.complexity,
        "search_depth": state.depth,
        "state": state.scientific_payload(),
        "state_hash": state.canonical_hash,
    }
    assert_llm_public_payload(payload)
    return payload


def opaque_id(prefix: str, payload: Mapping[str, Any]) -> str:
    return f"{prefix}_{hashlib.sha256(canonical_json(payload).encode()).hexdigest()[:16]}"


def _system_prompt(condition: str) -> str:
    role = "legal child search states" if condition == "S4" else "legal typed actions"
    return (
        "You are a heuristic navigator over a formal mathematical program search. "
        f"Rank the supplied {role}. You may not invent, alter, explain, or omit "
        "candidates. Return one JSON object with exactly one key named ranking. "
        "The ranking value must be a complete permutation of the supplied opaque "
        "IDs, best first. Output JSON only. Example JSON: {\"ranking\":[\"ID_A\",\"ID_B\"]}."
    )


def build_ranking_request(
    *,
    condition: str,
    config: DeepSeekSearchConfig,
    case: PublicCase,
    current_state: SearchState,
    candidate_items: tuple[Mapping[str, Any], ...],
) -> dict[str, Any]:
    if condition not in {"S4", "S5"}:
        raise SearchContractError(f"LLM_CONDITION_INVALID:{condition}")
    if not candidate_items or len(candidate_items) > LLM_BATCH_SIZE:
        raise SearchContractError("LLM_CANDIDATE_BATCH_INVALID")
    user_payload = {
        "candidate_kind": "CHILD_STATE" if condition == "S4" else "LEGAL_ACTION",
        "candidates": [dict(item) for item in candidate_items],
        "condition": condition,
        "current_search_state": public_state_payload(current_state),
        "public_case": public_case_payload(case, grammar_id=current_state.grammar_id),
        "response_contract": {
            "schema_version": LLM_RANKING_SCHEMA_VERSION,
            "shape": {"ranking": ["OPAQUE_ID_1", "OPAQUE_ID_2"]},
            "strict_complete_permutation": True,
        },
        "seed_label": config.seed_label,
    }
    assert_llm_public_payload(user_payload)
    return {
        "extra_body": {"thinking": {"type": config.thinking_type}},
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": _system_prompt(condition)},
            {"role": "user", "content": canonical_json(user_payload)},
        ],
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "response_format": dict(LLM_RESPONSE_FORMAT),
        "stream": False,
    }


def candidate_state_items(
    states: tuple[SearchState, ...],
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for state in states:
        payload = public_state_payload(state)
        identifier = opaque_id("C", payload)
        if identifier in seen:
            raise SearchContractError("LLM_OPAQUE_ID_COLLISION")
        seen.add(identifier)
        result.append({"opaque_id": identifier, "state": payload})
    return tuple(result)


def legal_action_items(
    actions: tuple[LegalAction, ...],
) -> tuple[dict[str, Any], ...]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for action in actions:
        payload = action.to_dict()
        identifier = opaque_id("A", payload)
        if identifier in seen:
            raise SearchContractError("LLM_OPAQUE_ID_COLLISION")
        seen.add(identifier)
        result.append({"action": payload, "opaque_id": identifier})
    return tuple(result)


def atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Create a JSON record atomically without overwriting prior evidence."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SearchContractError(f"LLM_RECORD_ALREADY_EXISTS:{path.name}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            raise SearchContractError(f"LLM_RECORD_ALREADY_EXISTS:{path.name}")
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def decision_record_hash(payload: Mapping[str, Any]) -> str:
    content = dict(payload)
    content.pop("decision_record_sha256", None)
    return hashlib.sha256(canonical_json(content).encode("utf-8")).hexdigest()


def request_hash(request: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(request).encode("utf-8")).hexdigest()
