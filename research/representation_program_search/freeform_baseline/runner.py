"""Auditable runner for the frozen F0/P0 RAW free-form baseline.

The historical prompt and parser remain byte-locked.  This runner replaces
only the old transport boundary, because that boundary persisted private
provider reasoning.  It reads the final assistant ``content`` field and
explicit usage/provenance only; it never reads ``reasoning_content``.

This module does not score a response and cannot certify a representation.
Legacy operational scoring and current typed-program evaluation are separate
evaluator operations.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from research.assumption_complete_representation.eval.ac_parser import (
    extract_json_object,
    parse_model_output,
)
from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.search import PublicCase
from research.representation_program_search.search.llm_contract import (
    ChatCompletionsTransport,
    DeepSeekSearchConfig,
    LLM_RESPONSE_FORMAT,
    TokenUsage,
)

from .prompt import F0Prompt, build_f0_prompt

F0_RUN_POLICY_VERSION = "RPSF0RunPolicyV1"
F0_RUN_HEADER_VERSION = "RPSF0RunHeaderV1"
F0_RESULT_VERSION = "RPSF0ResultV1"

_PRIVATE_REASONING_KEYS = frozenset({
    "chain_of_thought",
    "cot",
    "reasoning",
    "reasoning_content",
    "reasoning_tail",
})


class F0RunContractError(ValueError):
    """Stable fail-closed error at the F0 execution boundary."""


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


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


def _hash_json(value: Mapping[str, Any] | list[Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise F0RunContractError(f"F0_RECORD_ALREADY_EXISTS:{path.name}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2, sort_keys=True, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if path.exists():
            raise F0RunContractError(f"F0_RECORD_ALREADY_EXISTS:{path.name}")
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _prepare_output(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    if any(path.iterdir()):
        raise F0RunContractError("F0_OUTPUT_DIRECTORY_NOT_EMPTY")


def _request(prompt: F0Prompt, config: DeepSeekSearchConfig) -> dict[str, Any]:
    return {
        "extra_body": {"thinking": {"type": config.thinking_type}},
        "max_tokens": config.max_tokens,
        "messages": [dict(item) for item in prompt.messages],
        "model": config.model,
        "reasoning_effort": config.reasoning_effort,
        "response_format": dict(LLM_RESPONSE_FORMAT),
        "stream": False,
    }


@dataclass(frozen=True)
class F0RunResult:
    case_id: str
    model: str
    seed: int
    seed_label: str
    prompt_sha256: str
    request_sha256: str
    run_header_sha256: str
    provider_call_valid: bool
    provider_error_code: str | None
    request_id: str | None
    response_model: str | None
    finish_reason: str | None
    usage: TokenUsage
    latency_seconds: float
    final_content: str | None
    final_content_sha256: str | None
    final_content_chars: int
    parse_status: str
    parse_error: str | None
    parsed: Mapping[str, Any]
    f0_run_available: bool
    condition: str = "F0"
    policy_version: str = F0_RUN_POLICY_VERSION
    result_version: str = F0_RESULT_VERSION
    private_reasoning_accessed: bool = False
    private_reasoning_persisted: bool = False
    legacy_evaluation: str = "EXTERNAL_FROZEN_EVALUATOR_REQUIRED"
    typed_program_evaluation: str = "EXTERNAL_NO_REPAIR_TRANSLATOR_REQUIRED"

    def __post_init__(self) -> None:
        if self.condition != "F0" or self.policy_version != F0_RUN_POLICY_VERSION:
            raise F0RunContractError("F0_RESULT_POLICY_INVALID")
        if self.private_reasoning_accessed or self.private_reasoning_persisted:
            raise F0RunContractError("F0_PRIVATE_REASONING_BOUNDARY_VIOLATED")
        if self.seed_label != f"seed-{self.seed}":
            raise F0RunContractError("F0_SEED_BINDING_INVALID")
        if self.f0_run_available != self.provider_call_valid:
            raise F0RunContractError("F0_AVAILABILITY_MISMATCH")
        if self.provider_call_valid:
            if self.provider_error_code is not None or not self.usage.complete:
                raise F0RunContractError("F0_VALID_PROVIDER_RECORD_INCONSISTENT")
            if self.final_content is None or self.final_content_sha256 is None:
                raise F0RunContractError("F0_VALID_FINAL_CONTENT_MISSING")
        elif self.final_content is not None:
            raise F0RunContractError("F0_INVALID_RESPONSE_CONTENT_PERSISTED")

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "condition": self.condition,
            "f0_run_available": self.f0_run_available,
            "final_content": self.final_content,
            "final_content_chars": self.final_content_chars,
            "final_content_sha256": self.final_content_sha256,
            "finish_reason": self.finish_reason,
            "latency_seconds": self.latency_seconds,
            "legacy_evaluation": self.legacy_evaluation,
            "model": self.model,
            "parse_error": self.parse_error,
            "parse_status": self.parse_status,
            "parsed": dict(self.parsed),
            "policy_version": self.policy_version,
            "private_reasoning_accessed": self.private_reasoning_accessed,
            "private_reasoning_persisted": self.private_reasoning_persisted,
            "prompt_sha256": self.prompt_sha256,
            "provider_call_valid": self.provider_call_valid,
            "provider_error_code": self.provider_error_code,
            "request_id": self.request_id,
            "request_sha256": self.request_sha256,
            "response_model": self.response_model,
            "result_version": self.result_version,
            "run_header_sha256": self.run_header_sha256,
            "seed": self.seed,
            "seed_label": self.seed_label,
            "typed_program_evaluation": self.typed_program_evaluation,
            "usage": self.usage.to_dict(),
        }


def run_f0(
    case: PublicCase,
    *,
    transport: ChatCompletionsTransport,
    output_directory: str | Path,
    config: DeepSeekSearchConfig | None = None,
) -> F0RunResult:
    """Execute one P0 RAW call and persist only final-output provenance.

    A syntactically malformed final answer remains an available F0 method
    outcome (a parse failure).  Provider/API/provenance failures are
    unavailable and never silently replaced by a deterministic fallback.
    """
    frozen_config = config or DeepSeekSearchConfig()
    prompt = build_f0_prompt(case)
    request = _request(prompt, frozen_config)
    output = Path(output_directory)
    _prepare_output(output)
    header: dict[str, Any] = {
        "case_id": case.case_id,
        "condition": "F0",
        "deepseek_config": frozen_config.to_dict(),
        "frozen_prompt": prompt.to_dict(),
        "policy_version": F0_RUN_POLICY_VERSION,
        "private_reasoning_accessed": False,
        "private_reasoning_persisted": False,
        "proposer_view_sha256": case.proposer_view_sha256,
        "request_sha256": _hash_json(request),
        "run_header_version": F0_RUN_HEADER_VERSION,
    }
    header["run_header_sha256"] = _hash_json(header)
    _atomic_json(output / "run_header.json", header)

    started = time.perf_counter()
    response: Any | None = None
    error_code: str | None = None
    try:
        response = transport.complete(request)
    except Exception as exc:
        error_code = f"API_FAILURE:{type(exc).__name__}"
    latency = time.perf_counter() - started

    usage = TokenUsage.empty() if response is None else TokenUsage.from_provider(response)
    request_id = _get(response, "id") if response is not None else None
    response_model = _get(response, "model") if response is not None else None
    choices = _get(response, "choices") if response is not None else None
    finish_reason: str | None = None
    content = ""
    if error_code is None:
        if not isinstance(choices, (list, tuple)) or len(choices) != 1:
            error_code = "RESPONSE_CHOICE_COUNT_INVALID"
        else:
            choice = choices[0]
            finish_reason = _get(choice, "finish_reason")
            message = _get(choice, "message")
            candidate = _get(message, "content", "")
            content = candidate if isinstance(candidate, str) else ""
            if finish_reason != "stop":
                error_code = "RESPONSE_FINISH_REASON_INVALID"
            elif response_model != frozen_config.model:
                error_code = "RESPONSE_MODEL_MISMATCH"
            elif not isinstance(request_id, str) or not request_id:
                error_code = "RESPONSE_REQUEST_ID_MISSING"
            elif not usage.complete:
                error_code = "RESPONSE_USAGE_INCOMPLETE"

    raw_final_object: Mapping[str, Any] | None = None
    if error_code is None:
        raw_final_object, _raw_error = extract_json_object(content)
        if raw_final_object is not None and _contains_private_reasoning_key(
            raw_final_object
        ):
            error_code = "RESPONSE_PRIVATE_REASONING_FIELD_FORBIDDEN"

    parsed = parse_model_output(content) if error_code is None else {
        "parse_status": "FAILED_OPERATIONAL",
        "parse_error": error_code,
        "abstain": False,
        "format_wrap": False,
        "hypotheses": [],
        "raw_obj": None,
    }
    provider_valid = error_code is None
    persisted_content = content if provider_valid else None
    safe_parsed = {key: value for key, value in parsed.items() if key != "raw_obj"}
    result = F0RunResult(
        case_id=case.case_id,
        model=frozen_config.model,
        seed=frozen_config.seed,
        seed_label=frozen_config.seed_label,
        prompt_sha256=prompt.hashes["prompt_sha256"],
        request_sha256=header["request_sha256"],
        run_header_sha256=header["run_header_sha256"],
        provider_call_valid=provider_valid,
        provider_error_code=error_code,
        request_id=request_id if isinstance(request_id, str) else None,
        response_model=response_model if isinstance(response_model, str) else None,
        finish_reason=finish_reason if isinstance(finish_reason, str) else None,
        usage=usage,
        latency_seconds=latency,
        final_content=persisted_content,
        final_content_sha256=(
            hashlib.sha256(content.encode("utf-8")).hexdigest()
            if provider_valid else None
        ),
        final_content_chars=len(content),
        parse_status=str(parsed.get("parse_status") or "PARSE_FAILURE"),
        parse_error=(
            str(parsed["parse_error"]) if parsed.get("parse_error") is not None else None
        ),
        parsed=safe_parsed,
        f0_run_available=provider_valid,
    )
    _atomic_json(output / "result.json", result.to_dict())
    return result
