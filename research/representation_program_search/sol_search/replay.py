"""Atomic read-only replay builder for the byte-frozen SOL v1 authority."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import sympy

from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.search import PublicCase
from symbolic_compactification.observations.discovery import version_of
from symbolic_compactification.parser import parse_expression

from .authority import authority_manifest, validate_local_authority
from .model import (
    SOL_ARTIFACT_SCHEMA,
    SOL_AUTHORITY_COMMIT,
    SOL_LAYER,
    SOLProjection,
)
from .projection import load_sol_projection
from .replay_contract import (
    SOL_REPLAY_BACKENDS,
    SOL_REPLAY_BACKEND_PRESET,
    SOL_REPLAY_POLICY_VERSION,
    SOL_REPLAY_TIMEOUT_SECONDS,
    replay_policy_payload,
    replay_wrapper_functions,
    structural_container_metadata,
    structural_container_text,
)

_FORBIDDEN_PATH_PARTS = frozenset({
    "evaluator", "evaluation", "final", "reference", "runs", "steps", "verification",
})


class SOLReplayError(ValueError):
    """Stable fail-closed replay-builder error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class SOLReplayPolicy:
    """Version lock; backend preset and timeout are not caller-configurable."""

    version: str = SOL_REPLAY_POLICY_VERSION

    def __post_init__(self) -> None:
        if self.version != SOL_REPLAY_POLICY_VERSION:
            raise SOLReplayError("SOL_REPLAY_POLICY_UNKNOWN")

    def to_dict(self) -> dict[str, Any]:
        return replay_policy_payload()


@dataclass(frozen=True)
class SOLReplayResult:
    artifact_path: str
    artifact_sha256: str
    container_sha256: str
    projection: SOLProjection
    replay_policy: SOLReplayPolicy
    environment_versions: dict[str, str | None]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "audit_semantics": "HASH_AND_REPLAY_NOT_PROOF_OF_EXECUTION",
            "container_sha256": self.container_sha256,
            "environment_versions": dict(sorted(self.environment_versions.items())),
            "projection": self.projection.to_dict(),
            "replay_policy": self.replay_policy.to_dict(),
        }


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _case_binding(case: PublicCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "proposer_view_sha256": case.proposer_view_sha256,
        "source_members": [
            {"member_id": item.member_id, "sha256": item.sha256}
            for item in sorted(case.members, key=lambda item: item.member_id)
        ],
    }


def _environment_versions() -> dict[str, str | None]:
    return {
        "egglog": version_of("egglog"),
        "lgg": version_of("lgg"),
        "machine": platform.machine(),
        "matchpy": version_of("matchpy"),
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "sympy": sympy.__version__,
        "system": platform.system(),
        "system_release": platform.release(),
    }


def _validate_public_case(case: PublicCase) -> None:
    if not isinstance(case, PublicCase):
        raise SOLReplayError("SOL_REPLAY_PUBLIC_CASE_REQUIRED")
    if any(
        part.lower() in _FORBIDDEN_PATH_PARTS
        for relative in case.accessed_paths
        for part in Path(relative).parts
    ):
        raise SOLReplayError("SOL_REPLAY_PUBLIC_BOUNDARY_VIOLATION")
    wrappers = set(replay_wrapper_functions(case).values())
    if wrappers & set(case.functions):
        raise SOLReplayError("SOL_REPLAY_WRAPPER_COLLISION")
    symbol_names = {
        item if isinstance(item, str) else item.get("name")
        for item in case.symbols
    }
    if wrappers & symbol_names:
        raise SOLReplayError("SOL_REPLAY_WRAPPER_COLLISION")
    for member in case.members:
        if _sha256(member.expression.encode("utf-8")) != member.sha256:
            raise SOLReplayError(f"SOL_REPLAY_MEMBER_HASH_MISMATCH:{member.member_id}")
        try:
            parse_expression(
                member.expression,
                list(case.symbols),
                functions=list(case.functions) or None,
            )
        except Exception as exc:
            raise SOLReplayError(
                f"SOL_REPLAY_MEMBER_PARSE_FAILURE:{member.member_id}:{type(exc).__name__}"
            ) from None


def _validate_output_path(case: PublicCase, output_path: str | Path) -> Path:
    path = Path(output_path).resolve()
    if path.suffix != ".json":
        raise SOLReplayError("SOL_REPLAY_OUTPUT_SUFFIX_INVALID")
    if path.exists():
        raise SOLReplayError("SOL_REPLAY_OUTPUT_EXISTS")
    if any(part.lower() in _FORBIDDEN_PATH_PARTS for part in path.parts):
        raise SOLReplayError("SOL_REPLAY_OUTPUT_PATH_FORBIDDEN")
    try:
        relative = path.relative_to(case.package_root.resolve())
    except ValueError:
        relative = None
    if relative is not None:
        if any(part.lower() in _FORBIDDEN_PATH_PARTS for part in relative.parts):
            raise SOLReplayError("SOL_REPLAY_OUTPUT_PATH_FORBIDDEN")
        if relative.parts and relative.parts[0].lower() == "members":
            raise SOLReplayError("SOL_REPLAY_OUTPUT_PATH_FORBIDDEN")
        if path == case.proposer_view_path.resolve():
            raise SOLReplayError("SOL_REPLAY_OUTPUT_PATH_FORBIDDEN")
    return path


def _backend_provenance(bundle: dict[str, Any]) -> dict[str, Any]:
    provenance = bundle.get("provenance") or {}
    return {
        "backend_status": bundle.get("backend_status") or {},
        "backend_versions": {
            name: version_of(name) for name in SOL_REPLAY_BACKENDS
        },
        "backends_run": list(provenance.get("backends_run") or []),
    }


def _artifact_payload(
    case: PublicCase,
    bundle: dict[str, Any],
    environment: dict[str, str | None],
) -> dict[str, Any]:
    bundle_sha256 = _sha256(canonical_json(bundle).encode("utf-8"))
    return {
        "bundle": bundle,
        "case_binding": _case_binding(case),
        "replay_attestation": {
            "authority_manifest_sha256": authority_manifest()["manifest_sha256"],
            "backend_provenance": _backend_provenance(bundle),
            "bundle_sha256": bundle_sha256,
            "environment_versions": environment,
            "mode": "READ_ONLY_FROZEN_SOL_REPLAY",
            "public_case_sha256": case.proposer_view_sha256,
            "replay_policy": replay_policy_payload(),
            "structural_container": structural_container_metadata(case),
        },
        "schema_version": SOL_ARTIFACT_SCHEMA,
        "sol_authority": {
            "commit": SOL_AUTHORITY_COMMIT,
            "layer": SOL_LAYER,
            **authority_manifest(),
        },
    }


def _artifact_bytes(payload: dict[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(str(path), flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def build_sol_replay_artifact(
    case: PublicCase,
    output_path: str | Path,
    *,
    policy: SOLReplayPolicy | None = None,
) -> SOLReplayResult:
    """Replay frozen SOL on public members and atomically publish its artifact."""
    frozen_policy = policy or SOLReplayPolicy()
    authority_failures = validate_local_authority(Path(__file__).resolve().parents[3])
    if authority_failures:
        raise SOLReplayError(authority_failures[0])
    _validate_public_case(case)
    destination = _validate_output_path(case, output_path)
    container = structural_container_text(case)
    wrapper_functions = tuple(replay_wrapper_functions(case).values())
    # Import only after the exact local replay authority has passed its byte
    # manifest. Importing is not evidence of execution; the output remains
    # auditable only by hashes and deterministic replay.
    from symbolic_compactification.observations.api import observe

    try:
        observed = observe(
            container,
            list(case.symbols),
            list(case.functions) + list(wrapper_functions),
            context={"rps_replay_policy": frozen_policy.version},
            backends=SOL_REPLAY_BACKEND_PRESET,
            timeout_s=SOL_REPLAY_TIMEOUT_SECONDS,
        )
    except Exception as exc:
        raise SOLReplayError(f"SOL_REPLAY_EXECUTION_FAILURE:{type(exc).__name__}") from None
    bundle = observed.to_dict()
    environment = _environment_versions()
    payload = _artifact_payload(case, bundle, environment)
    encoded = _artifact_bytes(payload)
    artifact_sha256 = _sha256(encoded)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=str(destination.parent),
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        projection = load_sol_projection(
            case,
            temporary,
            expected_sha256=artifact_sha256,
        )
        if projection.status == "UNAVAILABLE":
            raise SOLReplayError(
                "SOL_REPLAY_SELF_VALIDATION_FAILED:" + ",".join(projection.reason_codes)
            )
        # Same-directory hard-link publication is atomic and refuses to
        # overwrite evidence created concurrently after the preflight check.
        linked = False
        try:
            os.link(temporary, destination)
            linked = True
        except FileExistsError:
            raise SOLReplayError("SOL_REPLAY_OUTPUT_EXISTS") from None
        _fsync_directory(destination.parent)
        temporary.unlink()
        _fsync_directory(destination.parent)
    except BaseException:
        if "linked" in locals() and linked:
            try:
                destination.unlink()
                _fsync_directory(destination.parent)
            except OSError:
                pass
        try:
            temporary.unlink()
        except OSError:
            pass
        raise
    return SOLReplayResult(
        artifact_path=str(destination),
        artifact_sha256=artifact_sha256,
        container_sha256=structural_container_metadata(case)["expression_sha256"],
        projection=projection,
        replay_policy=frozen_policy,
        environment_versions=environment,
    )
