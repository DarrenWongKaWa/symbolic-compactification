"""Atomic one-condition jobs for the frozen RPS calibration and evaluation matrix.

The runner intentionally executes one condition at a time.  A coordinator may
parallelize jobs because every job consumes immutable, hash-bound inputs and
publishes to a distinct directory by atomic rename.  It owns no search policy,
candidate generation, verifier rule, or LLM prompt.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from research.representation_program_search.freeform_baseline import (
    evaluate_f0,
    run_f0,
)
from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.search import (
    ChatCompletionsTransport,
    DeepSeekSearchConfig,
    SearchPolicy,
    enumerative_search,
    llm_action_proposal_search,
    llm_state_ranking_search,
    load_public_case,
    random_search,
    symbolic_beam_search,
    symbolic_matched_batch32_search,
)
from research.representation_program_search.sol_search import sol_conditioned_search
from research.representation_program_search.verifier_search import (
    FIXED_STATE_BUDGETS,
    M2VerifierFrontierAdapter,
    llm_verifier_search,
    verifier_matched_batch32_search,
    verifier_search,
    verify_search_result_posthoc,
)

RUNNER_VERSION = "RPSExperimentJobRunnerV1"
CLEARANCE_SCHEMA = "RPSCaseClearanceV1"
JOB_CONDITIONS = frozenset({
    "S0",
    "S1",
    "S2",
    "S2_MATCHED_BATCH32",
    "S3",
    "S4",
    "S5",
    "S6",
    "S6_MATCHED_BATCH32",
    "S7",
    "F0",
})
LLM_CONDITIONS = frozenset({"S4", "S5", "S7", "F0"})
GRAMMAR_IDS = frozenset({"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"})


class ExperimentJobError(ValueError):
    """Stable fail-closed execution contract error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _validate_sha256(value: str | None, field: str, *, required: bool) -> None:
    if value is None and not required:
        return
    if not isinstance(value, str) or len(value) != 64 or any(
        character not in "0123456789abcdef" for character in value
    ):
        raise ExperimentJobError(f"{field.upper()}_INVALID")


def _read_hash_bound_json(
    path: str | Path,
    expected_sha256: str,
    *,
    label: str,
) -> tuple[dict[str, Any], str]:
    _validate_sha256(expected_sha256, f"{label}_sha256", required=True)
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise ExperimentJobError(f"{label.upper()}_MISSING") from exc
    actual = _sha256_bytes(raw)
    if actual != expected_sha256:
        raise ExperimentJobError(f"{label.upper()}_HASH_MISMATCH")
    try:
        value = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ExperimentJobError(f"{label.upper()}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise ExperimentJobError(f"{label.upper()}_NOT_OBJECT")
    return value, actual


def _atomic_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise ExperimentJobError(f"JOB_RECORD_ALREADY_EXISTS:{path.name}")
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _file_sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


@dataclass(frozen=True)
class ExperimentJobSpec:
    """Immutable inputs for one independently replayable method job."""

    job_id: str
    condition: str
    case_id: str
    proposer_view_sha256: str
    clearance_receipt_sha256: str
    grammar_id: str = "G_FULL"
    budget: int | None = None
    random_seed: int | None = None
    model: str | None = None
    seed_label: str | None = None
    latent_creation_allowed: bool = True
    sol_artifact_sha256: str | None = None
    f0_hidden_sha256: str | None = None
    version: str = RUNNER_VERSION

    def __post_init__(self) -> None:
        if self.version != RUNNER_VERSION:
            raise ExperimentJobError("RUNNER_VERSION_UNKNOWN")
        if not self.job_id or not self.case_id:
            raise ExperimentJobError("JOB_IDENTITY_EMPTY")
        if self.condition not in JOB_CONDITIONS:
            raise ExperimentJobError("JOB_CONDITION_UNKNOWN")
        if self.grammar_id not in GRAMMAR_IDS:
            raise ExperimentJobError("JOB_GRAMMAR_UNKNOWN")
        _validate_sha256(
            self.proposer_view_sha256, "proposer_view_sha256", required=True
        )
        _validate_sha256(
            self.clearance_receipt_sha256,
            "clearance_receipt_sha256",
            required=True,
        )
        _validate_sha256(
            self.sol_artifact_sha256,
            "sol_artifact_sha256",
            required=self.condition == "S3",
        )
        _validate_sha256(
            self.f0_hidden_sha256,
            "f0_hidden_sha256",
            required=self.condition == "F0",
        )
        if self.condition == "F0":
            if self.budget is not None:
                raise ExperimentJobError("F0_STATE_BUDGET_FORBIDDEN")
        elif self.budget not in FIXED_STATE_BUDGETS:
            raise ExperimentJobError("JOB_STATE_BUDGET_NOT_FROZEN")
        if self.condition == "S0":
            if not isinstance(self.random_seed, int) or isinstance(
                self.random_seed, bool
            ) or self.random_seed < 0:
                raise ExperimentJobError("S0_RANDOM_SEED_INVALID")
        elif self.random_seed is not None:
            raise ExperimentJobError("NONRANDOM_CONDITION_HAS_RANDOM_SEED")
        if self.condition in LLM_CONDITIONS:
            if self.model is None or self.seed_label is None:
                raise ExperimentJobError("LLM_CONFIGURATION_MISSING")
            # The shared config performs the frozen model/seed validation.
            DeepSeekSearchConfig(model=self.model, seed_label=self.seed_label)
        elif self.model is not None or self.seed_label is not None:
            raise ExperimentJobError("NONLLM_CONDITION_HAS_LLM_CONFIGURATION")
        if self.condition != "S3" and self.sol_artifact_sha256 is not None:
            raise ExperimentJobError("NONSOL_CONDITION_HAS_SOL_ARTIFACT")
        if self.condition != "F0" and self.f0_hidden_sha256 is not None:
            raise ExperimentJobError("NONF0_CONDITION_HAS_F0_HIDDEN")

    def to_dict(self) -> dict[str, Any]:
        return {
            "budget": self.budget,
            "case_id": self.case_id,
            "clearance_receipt_sha256": self.clearance_receipt_sha256,
            "condition": self.condition,
            "f0_hidden_sha256": self.f0_hidden_sha256,
            "grammar_id": self.grammar_id,
            "job_id": self.job_id,
            "latent_creation_allowed": self.latent_creation_allowed,
            "model": self.model,
            "proposer_view_sha256": self.proposer_view_sha256,
            "random_seed": self.random_seed,
            "seed_label": self.seed_label,
            "sol_artifact_sha256": self.sol_artifact_sha256,
            "version": self.version,
        }

    @property
    def canonical_hash(self) -> str:
        return _sha256_json(self.to_dict())


def load_clearance_receipt(
    path: str | Path,
    expected_sha256: str,
    *,
    case_id: str,
    proposer_view_sha256: str,
) -> dict[str, Any]:
    """Load the independent admission/assumption/leakage gate for one case."""
    receipt, _actual = _read_hash_bound_json(
        path, expected_sha256, label="clearance_receipt"
    )
    required = {
        "admission_audit_sha256",
        "admission_status",
        "assumption_audit_sha256",
        "assumption_clearance",
        "case_id",
        "leakage_audit_sha256",
        "leakage_status",
        "proposer_view_sha256",
        "schema_version",
    }
    if set(receipt) != required:
        raise ExperimentJobError("CLEARANCE_RECEIPT_SCHEMA_MISMATCH")
    if receipt["schema_version"] != CLEARANCE_SCHEMA:
        raise ExperimentJobError("CLEARANCE_RECEIPT_VERSION_UNKNOWN")
    if receipt["case_id"] != case_id:
        raise ExperimentJobError("CLEARANCE_RECEIPT_CASE_MISMATCH")
    if receipt["proposer_view_sha256"] != proposer_view_sha256:
        raise ExperimentJobError("CLEARANCE_RECEIPT_PUBLIC_CASE_MISMATCH")
    for field in (
        "admission_audit_sha256",
        "assumption_audit_sha256",
        "leakage_audit_sha256",
    ):
        _validate_sha256(receipt.get(field), field, required=True)
    if receipt["admission_status"] != "ADMISSION_READY":
        raise ExperimentJobError("CASE_NOT_ADMISSION_READY")
    if receipt["assumption_clearance"] != "CLEARED":
        raise ExperimentJobError("CASE_ASSUMPTIONS_NOT_CLEARED")
    if receipt["leakage_status"] != "CLEARED":
        raise ExperimentJobError("CASE_LEAKAGE_NOT_CLEARED")
    return receipt


def _search_summary(search_result: Any, verifier_result: Any) -> dict[str, Any]:
    return {
        "first_success_index": verifier_result.first_success_index,
        "llm_tokens_used": verifier_result.llm_tokens_used,
        "method_available": True,
        "program_success": verifier_result.first_success_index is not None,
        "search_states_expanded": search_result.states_expanded,
        "verifier_states_expanded": verifier_result.states_expanded,
        "wall_time_seconds": (
            search_result.wall_time_seconds + verifier_result.wall_time_seconds
        ),
    }


def _run_search_then_posthoc(
    search_result: Any,
    case: Any,
    staging: Path,
) -> dict[str, Any]:
    search_path = staging / "search" / "result.json"
    if not search_path.exists():
        _atomic_json(search_path, search_result.to_dict(include_states=True))
    verifier_result = verify_search_result_posthoc(
        search_result,
        case,
        output_root=staging / "verification",
        leakage_status="CLEARED",
        assumption_clearance="CLEARED",
    )
    summary = _search_summary(search_result, verifier_result)
    summary.update({
        "search_result_sha256": _file_sha256(search_path),
        "verification_result_sha256": _file_sha256(
            staging / "verification" / "result.json"
        ),
    })
    return summary


def _safe_error_code(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    if isinstance(code, str) and code:
        return code
    text = str(exc)
    if text and len(text) <= 160 and all(ord(character) >= 32 for character in text):
        return f"{type(exc).__name__}:{text}"
    return type(exc).__name__


def run_experiment_job(
    spec: ExperimentJobSpec,
    *,
    proposer_view_path: str | Path,
    clearance_receipt_path: str | Path,
    output_directory: str | Path,
    transport: ChatCompletionsTransport | None = None,
    sol_artifact_path: str | Path | None = None,
    f0_hidden_path: str | Path | None = None,
) -> dict[str, Any]:
    """Execute and atomically publish one method job.

    Method failures are preserved as ``METHOD_ERROR`` artifacts and returned;
    they are never rewritten as search failures or PROGRAM_SUCCESS.
    """
    output = Path(output_directory)
    if output.exists():
        raise ExperimentJobError("JOB_OUTPUT_ALREADY_EXISTS")
    case = load_public_case(proposer_view_path)
    if case.case_id != spec.case_id:
        raise ExperimentJobError("JOB_CASE_MISMATCH")
    if case.proposer_view_sha256 != spec.proposer_view_sha256:
        raise ExperimentJobError("JOB_PUBLIC_CASE_HASH_MISMATCH")
    clearance = load_clearance_receipt(
        clearance_receipt_path,
        spec.clearance_receipt_sha256,
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
    )
    if spec.condition in LLM_CONDITIONS and transport is None:
        raise ExperimentJobError("LLM_TRANSPORT_REQUIRED")
    if spec.condition == "S3" and sol_artifact_path is None:
        raise ExperimentJobError("SOL_ARTIFACT_REQUIRED")
    hidden: dict[str, Any] | None = None
    if spec.condition == "F0":
        if f0_hidden_path is None or spec.f0_hidden_sha256 is None:
            raise ExperimentJobError("F0_HIDDEN_REQUIRED")
        hidden, _actual = _read_hash_bound_json(
            f0_hidden_path, spec.f0_hidden_sha256, label="f0_hidden"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.", dir=output.parent))
    published = False
    try:
        manifest = {
            "case_public_manifest": case.public_manifest(),
            "clearance": clearance,
            "private_f0_authority_exposed_to_search": False,
            "spec": spec.to_dict(),
            "spec_sha256": spec.canonical_hash,
        }
        _atomic_json(staging / "JOB_MANIFEST.json", manifest)
        policy = SearchPolicy(
            latent_creation_enabled=spec.latent_creation_allowed
        )
        config = (
            DeepSeekSearchConfig(model=spec.model, seed_label=spec.seed_label)
            if spec.condition in LLM_CONDITIONS
            else None
        )
        try:
            if spec.condition == "S0":
                search = random_search(
                    case,
                    budget=spec.budget,
                    seed=spec.random_seed,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                method = _run_search_then_posthoc(search, case, staging)
            elif spec.condition == "S1":
                search = enumerative_search(
                    case,
                    budget=spec.budget,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                method = _run_search_then_posthoc(search, case, staging)
            elif spec.condition == "S2":
                search = symbolic_beam_search(
                    case,
                    budget=spec.budget,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                method = _run_search_then_posthoc(search, case, staging)
            elif spec.condition == "S2_MATCHED_BATCH32":
                search = symbolic_matched_batch32_search(
                    case,
                    budget=spec.budget,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                method = _run_search_then_posthoc(search, case, staging)
            elif spec.condition == "S3":
                sol = sol_conditioned_search(
                    case,
                    budget=spec.budget,
                    artifact_path=sol_artifact_path,
                    artifact_sha256=spec.sol_artifact_sha256,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                sol_path = staging / "search" / "result.json"
                _atomic_json(sol_path, sol.to_dict(include_states=True))
                if sol.search_result is None:
                    method = {
                        "exclusion_reason": sol.projection.reason,
                        "first_success_index": None,
                        "llm_tokens_used": 0,
                        "method_available": False,
                        "program_success": False,
                        "search_result_sha256": _file_sha256(sol_path),
                        "search_states_expanded": None,
                        "verifier_states_expanded": None,
                        "wall_time_seconds": None,
                    }
                else:
                    method = _run_search_then_posthoc(
                        sol.search_result, case, staging
                    )
                    method["sol_result_sha256"] = _file_sha256(sol_path)
            elif spec.condition in {"S4", "S5"}:
                search_function = (
                    llm_state_ranking_search
                    if spec.condition == "S4"
                    else llm_action_proposal_search
                )
                search = search_function(
                    case,
                    budget=spec.budget,
                    transport=transport,
                    decision_directory=staging / "search",
                    config=config,
                    grammar_id=spec.grammar_id,
                    policy=policy,
                )
                method = _run_search_then_posthoc(search, case, staging)
                method["llm_guided_scientific_run_eligible"] = (
                    search.llm_guided_scientific_run_eligible
                )
            elif spec.condition in {"S6", "S6_MATCHED_BATCH32", "S7"}:
                adapter = M2VerifierFrontierAdapter(
                    case,
                    grammar_id=spec.grammar_id,
                    search_policy=policy,
                    leakage_status="CLEARED",
                    assumption_clearance="CLEARED",
                )
                if spec.condition == "S6":
                    result = verifier_search(
                        (adapter.initial_node(),),
                        output_root=staging / "verification",
                        budget=spec.budget,
                        condition="S6",
                        expander=adapter.expand,
                    )
                elif spec.condition == "S6_MATCHED_BATCH32":
                    result = verifier_matched_batch32_search(
                        adapter,
                        output_root=staging / "verification",
                        budget=spec.budget,
                    )
                else:
                    result = llm_verifier_search(
                        adapter,
                        output_root=staging / "verification",
                        budget=spec.budget,
                        transport=transport,
                        config=config,
                    )
                method = {
                    "first_success_index": result.first_success_index,
                    "llm_tokens_used": result.llm_tokens_used,
                    "method_available": True,
                    "program_success": result.first_success_index is not None,
                    "search_states_expanded": result.states_expanded,
                    "verification_result_sha256": _file_sha256(
                        staging / "verification" / "result.json"
                    ),
                    "verifier_states_expanded": result.states_expanded,
                    "wall_time_seconds": result.wall_time_seconds,
                }
                if spec.condition == "S7":
                    method["llm_guided_scientific_run_eligible"] = (
                        result.llm_guided_scientific_run_eligible
                    )
            else:
                f0 = run_f0(
                    case,
                    transport=transport,
                    output_directory=staging / "freeform",
                    config=config,
                )
                evaluation = evaluate_f0(
                    f0,
                    case,
                    legacy_hidden=hidden,
                    output_directory=staging / "verification",
                    leakage_status="CLEARED",
                    assumption_clearance="CLEARED",
                )
                typed = evaluation.get("program") or {}
                method = {
                    "evaluation_result_sha256": _file_sha256(
                        staging / "verification" / "evaluation.json"
                    ),
                    "first_success_index": (
                        1 if typed.get("any_program_success") else None
                    ),
                    "llm_tokens_used": f0.usage.total_tokens,
                    "method_available": f0.f0_run_available,
                    "program_success": bool(typed.get("any_program_success")),
                    "search_states_expanded": None,
                    "verifier_states_expanded": None,
                    "wall_time_seconds": f0.latency_seconds,
                }
            result_payload = {
                "condition": spec.condition,
                "job_id": spec.job_id,
                "method": method,
                "runner_status": "COMPLETE",
                "runner_version": RUNNER_VERSION,
                "spec_sha256": spec.canonical_hash,
            }
        except Exception as exc:  # preserve failed attempts as evidence
            result_payload = {
                "condition": spec.condition,
                "error_code": _safe_error_code(exc),
                "job_id": spec.job_id,
                "method": None,
                "runner_status": "METHOD_ERROR",
                "runner_version": RUNNER_VERSION,
                "spec_sha256": spec.canonical_hash,
            }
        result_payload["result_sha256"] = _sha256_json(result_payload)
        _atomic_json(staging / "JOB_RESULT.json", result_payload)
        os.replace(staging, output)
        published = True
        return result_payload
    finally:
        if not published and staging.exists():
            shutil.rmtree(staging)
