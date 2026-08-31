"""Bounded, fail-closed IO helpers for derivation-audit workspaces."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Optional

import yaml
from yaml.tokens import AliasToken, AnchorToken

from .schema import AuditError

MAX_METADATA_BYTES = 1_048_576
MAX_SOURCE_BYTES = 8_388_608


def decode_utf8(raw: bytes, path: Path, code: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise AuditError(code, "file must be UTF-8", path=str(path)) from None


def read_bytes(path: Path, *, max_bytes: int) -> bytes:
    try:
        if not path.is_file() or path.is_symlink():
            raise AuditError(
                "SOURCE_FILE_MISSING", "expected a regular non-symlink file",
                path=str(path))
        size = path.stat().st_size
        if size > max_bytes:
            raise AuditError(
                "SOURCE_TOO_LARGE",
                f"file exceeds {max_bytes} bytes",
                path=str(path),
            )
        return path.read_bytes()
    except AuditError:
        raise
    except OSError as exc:
        raise AuditError("SOURCE_FILE_UNREADABLE", str(exc), path=str(path)) from None


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(read_bytes(path, max_bytes=MAX_SOURCE_BYTES))


def assert_contained(root: Path, candidate: Path, field: str) -> Path:
    try:
        resolved_root = root.resolve()
        resolved = candidate.resolve()
        resolved.relative_to(resolved_root)
    except (OSError, ValueError):
        raise AuditError(
            "PATH_OUTSIDE_WORKSPACE",
            f"{field} resolves outside the audit workspace",
            path=str(candidate),
        ) from None
    if candidate.is_symlink() or resolved.is_symlink():
        raise AuditError(
            "PATH_OUTSIDE_WORKSPACE",
            f"{field} must not be a symlink",
            path=str(candidate),
        )
    return resolved


def contained_relpath(root: Path, raw: str, field: str) -> tuple[str, Path]:
    if not isinstance(raw, str) or not raw.strip():
        raise AuditError("WORKSPACE_PATH_INVALID", f"{field} must be a path string")
    if "\\" in raw:
        raise AuditError(
            "WORKSPACE_PATH_INVALID",
            f"{field} must use portable '/' separators",
        )
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise AuditError(
            "PATH_OUTSIDE_WORKSPACE",
            f"{field} must be a normalized workspace-relative path",
        )
    candidate = root / relative
    resolved = assert_contained(root, candidate, field)
    return relative.as_posix(), resolved


def write_new(path: Path, text: str) -> None:
    """Create a file. Never overwrite."""
    if path.exists() or path.is_symlink():
        raise AuditError(
            "SOURCE_ALREADY_EXISTS",
            "audit init never overwrites existing files",
            path=str(path),
        )
    path.write_text(text, encoding="utf-8")
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def safe_yaml_mapping(raw: bytes, path: Path, code: str) -> dict:
    text = decode_utf8(raw, path, code)
    try:
        tokens = yaml.scan(text)
        if any(isinstance(token, (AliasToken, AnchorToken)) for token in tokens):
            raise AuditError(
                code, "YAML anchors and aliases are not permitted", path=str(path))
        value = yaml.safe_load(text)
    except AuditError:
        raise
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None) or "invalid YAML"
        raise AuditError(code, problem, path=str(path)) from None
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise AuditError(code, "top-level YAML value must be a mapping", path=str(path))
    return value


def strict_json_mapping(raw: bytes, path: Path, code: str) -> dict:
    text = decode_utf8(raw, path, code)

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuditError(code, str(exc), path=str(path)) from None
    if not isinstance(value, dict):
        raise AuditError(code, "top-level JSON value must be an object", path=str(path))
    return value


def require_keys(value: dict, *, allowed: frozenset, required: frozenset,
                 code: str, path: Path) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise AuditError(code, f"unknown fields: {', '.join(unknown)}", path=str(path))
    if missing:
        raise AuditError(code, f"missing fields: {', '.join(missing)}", path=str(path))


def require_string(value: Any, field: str, code: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditError(code, f"{field} must be a non-empty string", path=str(path))
    return value.strip()
