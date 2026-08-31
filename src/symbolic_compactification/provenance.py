"""Safe, deterministic provenance records for researcher-workspace runs.

This module is deliberately independent of the session database used by the
historical research harness.  It records one bounded, public schema and never
inspects the process environment, ``.env`` files, request objects, or logging
state.  User files are opened read-only and only their SHA-256 digests are
persisted.

The convenience :func:`record_research_run` API writes::

    <runs_directory>/<run_id>/provenance.json

The run directory is created exclusively and the JSON file is written through
an fsynced temporary file followed by an atomic rename.  Existing runs are
never overwritten.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import re
import secrets
import tempfile
import time
from dataclasses import dataclass
from importlib import metadata
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Optional, Union

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, PACKAGE_VERSION,
                     engine_git_sha)

PathLike = Union[str, os.PathLike]

PROVENANCE_SCHEMA_VERSION = "ResearchRunProvenanceV1"
PROVENANCE_FILE_NAME = "provenance.json"
PROVENANCE_RESULTS = frozenset({
    "ZERO",
    "NONZERO",
    "UNKNOWN",
    "PARSE_FAILURE",
    "COMPILE_FAILURE",
    "ASSUMPTION_REQUIRED",
})

_RECORD_FIELDS = frozenset({
    "schema_version",
    "run_id",
    "timestamp",
    "package_version",
    "engine_version",
    "agent_protocol_version",
    "git_commit",
    "python_version",
    "python_implementation",
    "dependency_versions",
    "input_hashes",
    "expression_hashes",
    "hypothesis_hash",
    "assumptions_hash",
    "verifier_route",
    "result",
    "runtime_seconds",
    "warnings",
})
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_ROUTE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}\Z")
_DIST_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP_RE = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_GIT_RE = re.compile(r"(?:[0-9a-f]{7,64}(?:-dirty)?|unknown)\Z")

# A small production-local redaction boundary.  The repository's older,
# broader sanitizer lives under ``research/`` and importing it would couple a
# release API to frozen experiment code.  These patterns cover the credential
# forms that may plausibly occur in verifier warnings.  Crucially, this module
# never reads environment/config/request data in the first place.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{8,}"),
    re.compile(r"(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,})",
               re.IGNORECASE),
    re.compile(r"(?:xox[baprs]-[A-Za-z0-9-]{8,}|AKIA[A-Z0-9]{12,})"),
    re.compile(r"AIza[A-Za-z0-9_-]{16,}"),
)
_AUTH_RE = re.compile(
    r"(?i)(\bauthorization\s*[:=]\s*)(?:(?:bearer|basic)\s+)?[^\s,;]+")
_BEARER_RE = re.compile(r"(?i)(\bbearer\s+)[^\s,;]+")
_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b(?:api[_-]?key|apikey|access[_-]?token|refresh[_-]?token|"
    r"auth[_-]?token|password|passwd|secret|client[_-]?secret|"
    r"x-api-key|[A-Z0-9_]*API_KEY)\s*[:=]\s*)"
    r"(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)")


class ProvenanceError(ValueError):
    """Stable error raised before an unsafe or ambiguous record is written."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class RecordedRun:
    """A persisted record and the exact path that owns it."""

    record: dict
    path: Path


def sha256_file(path: PathLike) -> str:
    """Return the SHA-256 digest of a file read without modifying it."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as stream:
            before = os.fstat(stream.fileno())
            while True:
                block = stream.read(1024 * 1024)
                if not block:
                    break
                digest.update(block)
            after = os.fstat(stream.fileno())
    except OSError:
        raise ProvenanceError("PROVENANCE_INPUT_UNREADABLE") from None
    if (before.st_size, before.st_mtime_ns) != (after.st_size,
                                                after.st_mtime_ns):
        raise ProvenanceError("PROVENANCE_INPUT_CHANGED_DURING_HASH")
    return digest.hexdigest()


def hash_named_files(files: Optional[Mapping[str, PathLike]]) -> dict[str, str]:
    """Hash explicitly named files, returning a key-sorted mapping.

    Names are logical, workspace-relative labels only.  Absolute host paths
    are intentionally excluded from provenance records.
    """
    if files is None:
        return {}
    if not isinstance(files, Mapping):
        raise ProvenanceError("PROVENANCE_FILE_MAP_INVALID")
    normalized: dict[str, PathLike] = {}
    for label, path in files.items():
        safe_label = _normalize_label(label)
        if safe_label in normalized:
            raise ProvenanceError("PROVENANCE_FILE_LABEL_DUPLICATE")
        normalized[safe_label] = path
    return {label: sha256_file(normalized[label]) for label in sorted(normalized)}


def dependency_versions(
        distributions: Iterable[str] = ("sympy",)) -> dict[str, str]:
    """Capture installed versions for an explicit dependency allow-list.

    No package inventory or environment state is collected.  Missing optional
    distributions are represented as ``"not-installed"``.
    """
    result: dict[str, str] = {}
    for raw_name in distributions:
        if not isinstance(raw_name, str) or not _DIST_RE.fullmatch(raw_name):
            raise ProvenanceError("PROVENANCE_DEPENDENCY_NAME_INVALID")
        name = raw_name.lower()
        try:
            version = metadata.version(raw_name)
        except metadata.PackageNotFoundError:
            version = "not-installed"
        result[name] = _redact_text(str(version))
    return {name: result[name] for name in sorted(result)}


def build_run_record(
    *,
    input_hashes: Mapping[str, str],
    expression_hashes: Mapping[str, str],
    hypothesis_hash: Optional[str],
    assumptions_hash: Optional[str],
    verifier_route: str,
    result: str,
    runtime_seconds: float,
    warnings: Iterable[str] = (),
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    git_commit: Optional[str] = None,
    installed_dependencies: Optional[Mapping[str, str]] = None,
) -> dict:
    """Build one JSON-native provenance record.

    Timestamp, run id, git commit, and dependency versions may be injected for
    deterministic replay tests.  The production defaults capture them at the
    call boundary.  Only the fixed schema is returned; arbitrary metadata is
    not accepted.
    """
    normalized_timestamp = _normalize_timestamp(timestamp or _now_iso())
    normalized_run_id = _normalize_run_id(
        run_id or _new_run_id(normalized_timestamp))
    normalized_route = _normalize_route(verifier_route)
    normalized_result = _normalize_result(result)
    normalized_runtime = _normalize_runtime(runtime_seconds)
    normalized_git = git_commit if git_commit is not None else engine_git_sha()
    if not isinstance(normalized_git, str) or not _GIT_RE.fullmatch(normalized_git):
        raise ProvenanceError("PROVENANCE_GIT_COMMIT_INVALID")

    if installed_dependencies is None:
        normalized_dependencies = dependency_versions()
    else:
        normalized_dependencies = _normalize_dependencies(
            installed_dependencies)

    record = {
        "schema_version": PROVENANCE_SCHEMA_VERSION,
        "run_id": normalized_run_id,
        "timestamp": normalized_timestamp,
        "package_version": PACKAGE_VERSION,
        "engine_version": ENGINE_VERSION,
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "git_commit": normalized_git,
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "dependency_versions": normalized_dependencies,
        "input_hashes": _normalize_hash_map(input_hashes),
        "expression_hashes": _normalize_hash_map(expression_hashes),
        "hypothesis_hash": _normalize_optional_hash(hypothesis_hash),
        "assumptions_hash": _normalize_optional_hash(assumptions_hash),
        "verifier_route": normalized_route,
        "result": normalized_result,
        "runtime_seconds": normalized_runtime,
        "warnings": _normalize_warnings(warnings),
    }
    _validate_record(record)
    return record


def write_run_record(runs_directory: PathLike, record: Mapping) -> Path:
    """Atomically create one immutable ``provenance.json`` run record.

    The caller supplies the ``runs/`` directory.  A run directory is created
    with exclusive semantics; an existing run id raises
    ``PROVENANCE_RUN_ALREADY_EXISTS`` and is never overwritten.
    """
    safe_record = _record_for_write(record)
    runs_root = Path(runs_directory)
    try:
        runs_root.mkdir(parents=True, exist_ok=True)
    except OSError:
        raise ProvenanceError("PROVENANCE_RUNS_DIRECTORY_UNWRITABLE") from None
    run_root = runs_root / safe_record["run_id"]
    try:
        run_root.mkdir(exist_ok=False)
    except FileExistsError:
        raise ProvenanceError("PROVENANCE_RUN_ALREADY_EXISTS") from None
    except OSError:
        raise ProvenanceError("PROVENANCE_RUNS_DIRECTORY_UNWRITABLE") from None

    destination = run_root / PROVENANCE_FILE_NAME
    try:
        _write_json_atomic(destination, safe_record)
    except BaseException:
        try:
            run_root.rmdir()
        except OSError:
            pass
        raise
    return destination


def record_research_run(
    runs_directory: PathLike,
    *,
    input_files: Optional[Mapping[str, PathLike]] = None,
    expression_files: Optional[Mapping[str, PathLike]] = None,
    hypothesis_file: Optional[PathLike] = None,
    assumptions_file: Optional[PathLike] = None,
    verifier_route: str,
    result: str,
    runtime_seconds: float,
    warnings: Iterable[str] = (),
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> RecordedRun:
    """Hash read-only user artifacts, build a record, and persist it."""
    record = build_run_record(
        input_hashes=hash_named_files(input_files),
        expression_hashes=hash_named_files(expression_files),
        hypothesis_hash=(None if hypothesis_file is None
                         else sha256_file(hypothesis_file)),
        assumptions_hash=(None if assumptions_file is None
                          else sha256_file(assumptions_file)),
        verifier_route=verifier_route,
        result=result,
        runtime_seconds=runtime_seconds,
        warnings=warnings,
        run_id=run_id,
        timestamp=timestamp,
    )
    path = write_run_record(runs_directory, record)
    return RecordedRun(record=record, path=path)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_run_id(timestamp: str) -> str:
    stamp = timestamp.replace("-", "").replace(":", "")
    return f"{stamp}-{secrets.token_hex(4)}"


def _normalize_timestamp(value: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        raise ProvenanceError("PROVENANCE_TIMESTAMP_INVALID")
    try:
        time.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ProvenanceError("PROVENANCE_TIMESTAMP_INVALID") from None
    return value


def _normalize_run_id(value: str) -> str:
    if not isinstance(value, str) or not _RUN_ID_RE.fullmatch(value):
        raise ProvenanceError("PROVENANCE_RUN_ID_INVALID")
    if _redact_text(value) != value:
        raise ProvenanceError("PROVENANCE_UNSAFE_VALUE")
    return value


def _normalize_route(value: str) -> str:
    if not isinstance(value, str) or not _ROUTE_RE.fullmatch(value):
        raise ProvenanceError("PROVENANCE_VERIFIER_ROUTE_INVALID")
    if _redact_text(value) != value:
        raise ProvenanceError("PROVENANCE_UNSAFE_VALUE")
    return value


def _normalize_result(value: str) -> str:
    if value not in PROVENANCE_RESULTS:
        raise ProvenanceError("PROVENANCE_RESULT_INVALID")
    return value


def _normalize_runtime(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProvenanceError("PROVENANCE_RUNTIME_INVALID")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ProvenanceError("PROVENANCE_RUNTIME_INVALID")
    return normalized


def _normalize_label(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 512:
        raise ProvenanceError("PROVENANCE_FILE_LABEL_INVALID")
    if value != value.strip() or "\\" in value:
        raise ProvenanceError("PROVENANCE_FILE_LABEL_INVALID")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ProvenanceError("PROVENANCE_FILE_LABEL_INVALID")
    if "\x00" in value or "\n" in value or "\r" in value:
        raise ProvenanceError("PROVENANCE_FILE_LABEL_INVALID")
    return value


def _normalize_hash_map(value: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ProvenanceError("PROVENANCE_HASH_MAP_INVALID")
    normalized = {}
    for label, digest in value.items():
        safe_label = _normalize_label(label)
        if not isinstance(digest, str) or not _HASH_RE.fullmatch(digest):
            raise ProvenanceError("PROVENANCE_HASH_INVALID")
        normalized[safe_label] = digest
    return {label: normalized[label] for label in sorted(normalized)}


def _normalize_optional_hash(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise ProvenanceError("PROVENANCE_HASH_INVALID")
    return value


def _normalize_dependencies(value: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ProvenanceError("PROVENANCE_DEPENDENCIES_INVALID")
    normalized = {}
    for raw_name, raw_version in value.items():
        if not isinstance(raw_name, str) or not _DIST_RE.fullmatch(raw_name):
            raise ProvenanceError("PROVENANCE_DEPENDENCY_NAME_INVALID")
        if not isinstance(raw_version, str) or len(raw_version) > 256:
            raise ProvenanceError("PROVENANCE_DEPENDENCY_VERSION_INVALID")
        normalized[raw_name.lower()] = _redact_text(raw_version)
    return {name: normalized[name] for name in sorted(normalized)}


def _normalize_warnings(values: Iterable[str]) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise ProvenanceError("PROVENANCE_WARNINGS_INVALID")
    try:
        warnings = list(values)
    except TypeError:
        raise ProvenanceError("PROVENANCE_WARNINGS_INVALID") from None
    normalized = []
    for warning in warnings:
        if not isinstance(warning, str):
            raise ProvenanceError("PROVENANCE_WARNINGS_INVALID")
        # Bounded warning text prevents accidental persistence of entire crash
        # dumps or configuration files.  Redaction happens before truncation.
        normalized.append(_redact_text(warning)[:2048])
    return normalized


def _redact_text(value: str) -> str:
    redacted = _AUTH_RE.sub(r"\1[REDACTED]", value)
    redacted = _BEARER_RE.sub(r"\1[REDACTED]", redacted)
    redacted = _ASSIGNMENT_RE.sub(r"\1[REDACTED]", redacted)
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _record_for_write(record: Mapping) -> dict:
    if not isinstance(record, Mapping) or set(record) != _RECORD_FIELDS:
        raise ProvenanceError("PROVENANCE_RECORD_SCHEMA_INVALID")
    safe = dict(record)
    safe["warnings"] = _normalize_warnings(record["warnings"])
    safe["dependency_versions"] = _normalize_dependencies(
        record["dependency_versions"])
    safe["input_hashes"] = _normalize_hash_map(record["input_hashes"])
    safe["expression_hashes"] = _normalize_hash_map(
        record["expression_hashes"])
    _validate_record(safe)
    return safe


def _validate_record(record: Mapping) -> None:
    if set(record) != _RECORD_FIELDS:
        raise ProvenanceError("PROVENANCE_RECORD_SCHEMA_INVALID")
    if record["schema_version"] != PROVENANCE_SCHEMA_VERSION:
        raise ProvenanceError("PROVENANCE_RECORD_SCHEMA_INVALID")
    _normalize_run_id(record["run_id"])
    _normalize_timestamp(record["timestamp"])
    if record["package_version"] != PACKAGE_VERSION:
        raise ProvenanceError("PROVENANCE_RECORD_VERSION_INVALID")
    if record["engine_version"] != ENGINE_VERSION:
        raise ProvenanceError("PROVENANCE_RECORD_VERSION_INVALID")
    if record["agent_protocol_version"] != AGENT_PROTOCOL_VERSION:
        raise ProvenanceError("PROVENANCE_RECORD_VERSION_INVALID")
    if not isinstance(record["git_commit"], str) or not _GIT_RE.fullmatch(
            record["git_commit"]):
        raise ProvenanceError("PROVENANCE_GIT_COMMIT_INVALID")
    if record["python_version"] != platform.python_version():
        raise ProvenanceError("PROVENANCE_RECORD_VERSION_INVALID")
    if record["python_implementation"] != platform.python_implementation():
        raise ProvenanceError("PROVENANCE_RECORD_VERSION_INVALID")
    _normalize_dependencies(record["dependency_versions"])
    _normalize_hash_map(record["input_hashes"])
    _normalize_hash_map(record["expression_hashes"])
    _normalize_optional_hash(record["hypothesis_hash"])
    _normalize_optional_hash(record["assumptions_hash"])
    _normalize_route(record["verifier_route"])
    _normalize_result(record["result"])
    _normalize_runtime(record["runtime_seconds"])
    _normalize_warnings(record["warnings"])


def _write_json_atomic(path: Path, payload: Mapping) -> None:
    encoded = json.dumps(payload, sort_keys=True, indent=2,
                         ensure_ascii=False) + "\n"
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        # The enclosing run directory was created exclusively, so replace is
        # atomic without any possibility of clobbering a prior run record.
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


__all__ = [
    "PROVENANCE_FILE_NAME",
    "PROVENANCE_RESULTS",
    "PROVENANCE_SCHEMA_VERSION",
    "ProvenanceError",
    "RecordedRun",
    "build_run_record",
    "dependency_versions",
    "hash_named_files",
    "record_research_run",
    "sha256_file",
    "write_run_record",
]
