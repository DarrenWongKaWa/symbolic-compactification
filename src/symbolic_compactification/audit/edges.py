"""Edge manifest load and source grounding. E3 implements the body."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .io import (
    MAX_METADATA_BYTES,
    MAX_SOURCE_BYTES,
    contained_relpath,
    read_bytes,
    require_keys,
    require_string,
    safe_yaml_mapping,
    sha256_bytes,
)
from .schema import (
    AUDIT_SCHEMA_VERSION,
    EDGE_TYPES,
    GROUNDING_FAILURE,
    AuditError,
    _ID_RE,
)
from .workspace import CONFIG_FILE, AuditWorkspace


@dataclass(frozen=True)
class AuditEdge:
    edge_id: str
    source_from: Optional[str]
    source_to: Optional[str]
    edge_type: str
    lhs: Optional[str] = None
    rhs: Optional[str] = None
    residual: Optional[str] = None
    children: tuple[str, ...] = ()
    assumptions_used: tuple[str, ...] = ()
    claim: str = ""
    notes: str = ""
    required_rules: tuple[str, ...] = ()
    ibp_domain: Optional[str] = None


@dataclass(frozen=True)
class GroundingResult:
    edge: AuditEdge
    ok: bool
    status: str
    issues: tuple[str, ...]
    source_refs: tuple[str, ...]
    source_snapshot_hash: str


EDGE_DOCUMENT_KEYS = frozenset({"schema_version", "edges"})
EDGE_DOCUMENT_REQUIRED = frozenset({"schema_version", "edges"})
EDGE_FIELD_KEYS = frozenset({
    "id", "edge_id", "from", "source_from", "to", "source_to",
    "type", "edge_type", "lhs", "rhs", "residual",
    "children", "assumptions_used", "claim", "notes",
    "required_rules", "ibp_domain",
})
EDGE_FIELD_REQUIRED = frozenset()
_ID_ALIASES = ("id", "edge_id")
_FROM_ALIASES = ("from", "source_from")
_TO_ALIASES = ("to", "source_to")
_TYPE_ALIASES = ("type", "edge_type")

# Bound expression files are workspace-relative; labels use the eq: prefix.
_PATH_SUFFIXES = frozenset({
    ".txt", ".yaml", ".yml", ".tex", ".md", ".json",
})


def load_edges(workspace: AuditWorkspace) -> tuple[AuditEdge, ...]:
    """Parse edges/edges.yaml. LHS/RHS/residual are optional."""
    _, path = contained_relpath(
        workspace.root, workspace.config.edge_manifest, "edge_manifest")
    raw = read_bytes(path, max_bytes=MAX_METADATA_BYTES)
    mapping = safe_yaml_mapping(raw, path, "EDGE_PARSE_FAILURE")
    require_keys(
        mapping, allowed=EDGE_DOCUMENT_KEYS, required=EDGE_DOCUMENT_REQUIRED,
        code="EDGE_SCHEMA_INVALID", path=path)
    schema_version = require_string(
        mapping["schema_version"], "schema_version",
        "EDGE_SCHEMA_INVALID", path)
    if schema_version != AUDIT_SCHEMA_VERSION:
        raise AuditError(
            "EDGE_SCHEMA_INVALID",
            f"schema_version must be {AUDIT_SCHEMA_VERSION}",
            path=str(path),
        )
    items = mapping["edges"]
    if not isinstance(items, list):
        raise AuditError(
            "EDGE_SCHEMA_INVALID", "edges must be a list", path=str(path))
    edges: list[AuditEdge] = []
    seen: set[str] = set()
    for item in items:
        edge = _parse_edge(item, path)
        if edge.edge_id in seen:
            raise AuditError(
                "DUPLICATE_EDGE_ID",
                f"duplicate edge id {edge.edge_id!r}",
                path=str(path),
            )
        seen.add(edge.edge_id)
        edges.append(edge)
    return tuple(edges)


def ground_edge(edge: AuditEdge, workspace: AuditWorkspace) -> GroundingResult:
    """Bind an edge to declared equation/expression sources. Never mutates."""
    if edge.edge_type not in EDGE_TYPES:
        raise AuditError(
            "UNKNOWN_EDGE_TYPE",
            f"unsupported edge type {edge.edge_type!r}",
            path=str(workspace.root),
        )
    issues: list[str] = []
    bound: dict[str, str] = {}
    source_refs: list[str] = []

    def _remember_ref(value: Optional[str]) -> None:
        if value and value not in source_refs:
            source_refs.append(value)

    for value in (
            edge.source_from, edge.source_to, edge.lhs, edge.rhs, edge.residual):
        _remember_ref(value)

    _bind_declared_path(
        workspace, "from", edge.source_from, bound, issues)
    _bind_declared_path(
        workspace, "to", edge.source_to, bound, issues)
    _bind_declared_path(
        workspace, "lhs", edge.lhs, bound, issues)
    _bind_declared_path(
        workspace, "rhs", edge.rhs, bound, issues)
    _bind_declared_path(
        workspace, "residual", edge.residual, bound, issues)

    snapshot = _snapshot_files(workspace, issues)
    snapshot.update(bound)
    digest = _canonical_sha256(snapshot)
    ok = not issues
    return GroundingResult(
        edge=edge,
        ok=ok,
        status="" if ok else GROUNDING_FAILURE,
        issues=tuple(issues),
        source_refs=tuple(source_refs),
        source_snapshot_hash=digest,
    )


def _parse_edge(item: Any, path: Path) -> AuditEdge:
    if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
        raise AuditError(
            "EDGE_SCHEMA_INVALID", "each edge must be a mapping", path=str(path))
    require_keys(
        item, allowed=EDGE_FIELD_KEYS, required=EDGE_FIELD_REQUIRED,
        code="EDGE_SCHEMA_INVALID", path=path)
    edge_id = _aliased_string(item, _ID_ALIASES, path, required=True)
    if not _ID_RE.fullmatch(edge_id):
        raise AuditError(
            "EDGE_ID_INVALID", f"invalid edge id {edge_id!r}", path=str(path))
    edge_type = _aliased_string(item, _TYPE_ALIASES, path, required=True)
    if edge_type not in EDGE_TYPES:
        raise AuditError(
            "UNKNOWN_EDGE_TYPE",
            f"unsupported edge type {edge_type!r}",
            path=str(path),
        )
    return AuditEdge(
        edge_id=edge_id,
        source_from=_aliased_string(item, _FROM_ALIASES, path, required=False),
        source_to=_aliased_string(item, _TO_ALIASES, path, required=False),
        edge_type=edge_type,
        lhs=_optional_string(item, "lhs", path),
        rhs=_optional_string(item, "rhs", path),
        residual=_optional_string(item, "residual", path),
        children=_optional_string_tuple(item, "children", path),
        assumptions_used=_optional_string_tuple(item, "assumptions_used", path),
        claim=_optional_text(item, "claim", path),
        notes=_optional_text(item, "notes", path),
        required_rules=_optional_string_tuple(item, "required_rules", path),
        ibp_domain=_optional_string(item, "ibp_domain", path),
    )


def _aliased_string(
    item: dict,
    aliases: tuple[str, ...],
    path: Path,
    *,
    required: bool,
) -> Optional[str]:
    present = [name for name in aliases if name in item and item[name] is not None]
    if not present:
        if required:
            raise AuditError(
                "EDGE_SCHEMA_INVALID",
                f"missing fields: {aliases[0]}",
                path=str(path),
            )
        return None
    values = []
    for name in present:
        value = item[name]
        if not isinstance(value, str) or not value.strip():
            raise AuditError(
                "EDGE_SCHEMA_INVALID",
                f"{name} must be a non-empty string",
                path=str(path),
            )
        values.append(value.strip())
    if len(set(values)) > 1:
        raise AuditError(
            "EDGE_SCHEMA_INVALID",
            f"conflicting aliases {', '.join(present)}",
            path=str(path),
        )
    return values[0]


def _optional_string(item: dict, field: str, path: Path) -> Optional[str]:
    if field not in item or item[field] is None:
        return None
    value = item[field]
    if not isinstance(value, str) or not value.strip():
        raise AuditError(
            "EDGE_SCHEMA_INVALID",
            f"{field} must be a non-empty string",
            path=str(path),
        )
    return value.strip()


def _optional_text(item: dict, field: str, path: Path) -> str:
    if field not in item or item[field] is None:
        return ""
    value = item[field]
    if not isinstance(value, str):
        raise AuditError(
            "EDGE_SCHEMA_INVALID",
            f"{field} must be a string",
            path=str(path),
        )
    return value


def _optional_string_tuple(item: dict, field: str, path: Path) -> tuple[str, ...]:
    if field not in item or item[field] is None:
        return ()
    value = item[field]
    if not isinstance(value, list) or not all(
            isinstance(entry, str) and entry.strip() for entry in value):
        raise AuditError(
            "EDGE_SCHEMA_INVALID",
            f"{field} must be a list of strings",
            path=str(path),
        )
    return tuple(entry.strip() for entry in value)


def _looks_like_workspace_path(value: str) -> bool:
    if value.startswith("eq:"):
        return False
    relative = Path(value)
    if relative.is_absolute() or "\\" in value or ".." in relative.parts:
        return True
    return "/" in value or relative.suffix.lower() in _PATH_SUFFIXES


def _bind_declared_path(
    workspace: AuditWorkspace,
    field: str,
    value: Optional[str],
    bound: dict[str, str],
    issues: list[str],
) -> None:
    if not value or not _looks_like_workspace_path(value):
        return
    try:
        rel, abs_path = contained_relpath(workspace.root, value, field)
    except AuditError as exc:
        issues.append(exc.code)
        return
    if not abs_path.is_file() or abs_path.is_symlink():
        issues.append("SOURCE_FILE_MISSING")
        return
    try:
        digest = sha256_bytes(read_bytes(abs_path, max_bytes=MAX_SOURCE_BYTES))
    except AuditError as exc:
        issues.append(exc.code)
        return
    bound[rel] = digest


def _snapshot_files(workspace: AuditWorkspace, issues: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    required = (
        (CONFIG_FILE, MAX_METADATA_BYTES),
        (workspace.config.assumptions, MAX_METADATA_BYTES),
        (workspace.config.edge_manifest, MAX_METADATA_BYTES),
        (workspace.config.equation_manifest, MAX_METADATA_BYTES),
    )
    for rel, limit in required:
        try:
            _, abs_path = contained_relpath(workspace.root, rel, rel)
        except AuditError as exc:
            issues.append(exc.code)
            continue
        if not abs_path.is_file() or abs_path.is_symlink():
            issues.append("SOURCE_FILE_MISSING")
            continue
        try:
            files[rel] = sha256_bytes(read_bytes(abs_path, max_bytes=limit))
        except AuditError as exc:
            issues.append(exc.code)
    return files


def _canonical_sha256(payload: dict[str, str]) -> str:
    text = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(text.encode("utf-8"))
