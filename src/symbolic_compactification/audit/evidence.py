"""Immutable evidence store and audit verification.

LLM or agent text has no write path into these records. Only this module
may persist ``runs/<run_id>/machine_records.json`` and ``provenance.json``.

Verification is sequential: the exact SymPy backend is not treated as
thread-safe, so executable residuals are compiled and adjudicated one
edge at a time.

Changing source, residual, assumption, or engine-binding bytes produces
new hashes. A prior ZERO row cannot be reused silently for a new snapshot.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from ..models import (
    AGENT_PROTOCOL_VERSION,
    ENGINE_VERSION,
    PACKAGE_VERSION,
    AdapterError,
    VerificationResult,
    canonical_json,
    engine_git_sha,
    normalize_symbols,
    sha256_text,
)
from ..parser import normalize_functions
from ..provenance import PROVENANCE_FILE_NAME, dependency_versions
from ..security import redact_text
from ..verifier import verify_equivalent
from . import edges as edges_layer
from . import lowering as lowering_layer
from .edges import AuditEdge, GroundingResult
from .io import (
    MAX_METADATA_BYTES,
    MAX_SOURCE_BYTES,
    assert_contained,
    contained_relpath,
    decode_utf8,
    read_bytes,
    require_keys,
    safe_yaml_mapping,
    sha256_bytes,
)
from .lowering import LoweringResult
from .schema import (
    ALLOWED_DECLARED_RULES,
    ASSUMPTION_REQUIRED,
    ASYMPTOTIC_CLAIM,
    AUDIT_PROTOCOL_VERSION,
    AUDIT_SCHEMA_VERSION,
    AUDIT_STATUSES,
    BZ_IBP_CONCLUSION,
    BZ_PERIODIC_INTEGRATION_BY_PARTS,
    BZ_TORUS_PERIODICITY,
    CERTIFIED_BY_RULE,
    RuleCertificate,
    COMPILE_FAILURE,
    DEFAULT_VERIFIER_ROUTE,
    EDGE_TYPES,
    GROUNDING_FAILURE,
    INVALID_RECORD,
    NONZERO,
    NOT_LOWERED,
    PARSE_FAILURE,
    SPLIT,
    SPLIT_PARENT,
    UNKNOWN,
    ZERO,
    AuditError,
    AuditRecord,
    asymptotic_remainder_certified,
    default_status_for_edge_type,
    derive_bz_ibp_parent_status,
    derive_split_parent_status,
    integrity_issues,
    lowering_applicability,
    record_from_mapping,
)
from .workspace import (
    ASSUMPTIONS_DIRECTORY,
    EDGES_DIRECTORY,
    EQUATIONS_DIRECTORY,
    EXPRESSIONS_DIRECTORY,
    MANUSCRIPT_DIRECTORY,
    RUNS_DIRECTORY,
    AuditWorkspace,
    source_immutability_roots,
)

PathLike = Union[str, os.PathLike]

MACHINE_RECORDS_FILE = "machine_records.json"
AUDIT_PROVENANCE_SCHEMA_VERSION = "DerivationAuditRunProvenanceV1"
AUTHORITY = "symbolic_compactification.audit.evidence"

_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_TIMESTAMP_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\Z")
_ASSUMPTION_KEYS = frozenset({"symbols", "functions", "rules"})
_SNAPSHOT_DIRECTORIES = (
    MANUSCRIPT_DIRECTORY,
    EQUATIONS_DIRECTORY,
    EDGES_DIRECTORY,
    EXPRESSIONS_DIRECTORY,
    ASSUMPTIONS_DIRECTORY,
)
_MAX_RESIDUAL_TEXT = 65_536
_MAX_RUN_ARTIFACT_BYTES = MAX_METADATA_BYTES


@dataclass(frozen=True)
class AuditRun:
    run_id: str
    audit_id: str
    directory: Path
    records: tuple[AuditRecord, ...]
    schema_version: str = AUDIT_SCHEMA_VERSION


@dataclass(frozen=True)
class SourceSnapshot:
    """Read-only hash inventory of researcher-owned source files."""

    file_hashes: tuple[tuple[str, str], ...]
    source_snapshot_hash: str

    def mapping(self) -> dict[str, str]:
        return dict(self.file_hashes)


@dataclass(frozen=True)
class BoundHashes:
    """Content hashes bound into one machine record.

    ``obligation_hash`` covers lhs/rhs/residual/assumptions/snapshot/route/
    engine identity. Changing any bound byte-string yields a new digest.
    """

    lhs_hash: Optional[str]
    rhs_hash: Optional[str]
    residual_hash: Optional[str]
    assumptions_hash: str
    source_snapshot_hash: str
    obligation_hash: str
    verifier_route: str
    engine_version: str


@dataclass(frozen=True)
class DeclaredAssumptions:
    symbols: tuple[dict, ...]
    functions: tuple[str, ...]
    assumptions_hash: str
    names: tuple[str, ...]
    rules: tuple[str, ...] = ()


def verify_audit(
    workspace: AuditWorkspace,
    *,
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> AuditRun:
    """Snapshot, ground, lower, verify executable edges, persist records.

    Sibling ``load_edges`` / ``ground_edge`` / ``lower_edge`` are invoked for
    every run. Per-edge NOT_IMPLEMENTED from those layers is recorded as a
    typed non-ZERO status; a workspace-level NOT_IMPLEMENTED from
    ``load_edges`` still fails closed. Sources under manuscript/equations/
    edges/assumptions/expressions are never written.
    """
    started = time.monotonic()
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    edges = edges_layer.load_edges(workspace)
    records: list[AuditRecord] = []
    # Sequential on purpose: SymPy verification is not treated as thread-safe.
    for edge in edges:
        grounding, lowering = _ground_and_lower(edge, workspace)
        records.append(adjudicate_lowered_edge(
            edge,
            workspace,
            grounding,
            lowering,
            snapshot=snapshot,
            assumptions=assumptions,
        ))
    sealed = apply_split_parent_statuses(tuple(records))
    sealed = apply_bz_ibp_parent_statuses(sealed, assumptions.rules)
    runtime = round(max(0.0, time.monotonic() - started), 6)
    run = persist_audit_run(
        workspace,
        sealed,
        snapshot=snapshot,
        assumptions=assumptions,
        run_id=run_id,
        timestamp=timestamp,
        runtime_seconds=runtime,
    )
    _assert_sources_unchanged(workspace, snapshot)
    return run


def load_audit_run(workspace: AuditWorkspace, run_id: str) -> AuditRun:
    """Load an immutable recorded run. Do not reuse stale ZERO silently.

    Returned ZERO rows are evidence for the recorded snapshot hashes only.
    Callers must compare ``source_snapshot_hash`` / residual hashes against
    the current workspace before treating a row as current.
    """
    safe_id = _normalize_run_id(run_id)
    runs = _runs_directory(workspace)
    run_dir = runs / safe_id
    if run_dir.is_symlink():
        raise AuditError(
            "RUN_NOT_FOUND", "run must not be a symbolic link",
            path=str(run_dir),
        )
    try:
        resolved = assert_contained(workspace.root, run_dir, "run")
    except AuditError:
        raise AuditError(
            "RUN_NOT_FOUND", "run does not exist", path=str(run_dir),
        ) from None
    if not resolved.is_dir():
        raise AuditError(
            "RUN_NOT_FOUND", "run does not exist", path=str(run_dir),
        )
    records_path = resolved / MACHINE_RECORDS_FILE
    provenance_path = resolved / PROVENANCE_FILE_NAME
    records_raw = _read_run_file(records_path)
    provenance_raw = _read_run_file(provenance_path)
    payload = _strict_json(records_raw, records_path)
    provenance = _strict_json(provenance_raw, provenance_path)
    if not isinstance(payload, list):
        raise AuditError(
            "RUN_ARTIFACT_INVALID",
            "machine_records.json must be a list of records",
            path=str(records_path),
        )
    if not isinstance(provenance, dict):
        raise AuditError(
            "RUN_ARTIFACT_INVALID",
            "provenance.json must be an object",
            path=str(provenance_path),
        )
    if provenance.get("run_id") != safe_id:
        raise AuditError(
            "RUN_ARTIFACT_INVALID",
            "provenance run_id does not match the run directory",
            path=str(provenance_path),
        )
    records = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise AuditError(
                "INVALID_RECORD",
                f"machine_records[{index}] must be an object",
                path=str(records_path),
            )
        records.append(record_from_mapping(item))
    audit_id = str(provenance.get("audit_id") or _audit_id(workspace))
    return AuditRun(
        run_id=safe_id,
        audit_id=audit_id,
        directory=resolved,
        records=tuple(records),
        schema_version=str(
            provenance.get("audit_schema_version") or AUDIT_SCHEMA_VERSION),
    )


def latest_audit_run_id(workspace: AuditWorkspace) -> str:
    runs = _runs_directory(workspace)
    candidates: list[tuple[str, str]] = []
    try:
        entries = list(os.scandir(runs))
    except OSError as exc:
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE", str(exc), path=str(runs),
        ) from None
    for entry in entries:
        if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
            continue
        if not _RUN_ID_RE.fullmatch(entry.name):
            continue
        records_path = Path(entry.path) / MACHINE_RECORDS_FILE
        if not records_path.is_file() or records_path.is_symlink():
            continue
        timestamp = _provenance_timestamp(Path(entry.path))
        candidates.append((timestamp, entry.name))
    if not candidates:
        raise AuditError(
            "NO_RECORDED_RUNS",
            "run 'symbolic-compactification audit verify <dir>' first",
            path=str(runs),
        )
    candidates.sort()
    return candidates[-1][1]


def snapshot_audit_sources(workspace: AuditWorkspace) -> SourceSnapshot:
    """Hash researcher-owned sources. Never writes, never follows symlinks."""
    root = workspace.root
    hashes: dict[str, str] = {}
    config_path = root / "audit.yaml"
    _hash_source_file(root, config_path, hashes, max_bytes=MAX_METADATA_BYTES)
    for dirname in _SNAPSHOT_DIRECTORIES:
        directory = root / dirname
        if not directory.exists():
            continue
        if directory.is_symlink():
            raise AuditError(
                "PATH_OUTSIDE_WORKSPACE",
                "source must not be a symlink",
                path=str(directory),
            )
        if not directory.is_dir():
            continue
        for path in _iter_regular_files(directory):
            limit = (MAX_METADATA_BYTES
                     if path.suffix.lower() in {".yaml", ".yml", ".json"}
                     else MAX_SOURCE_BYTES)
            _hash_source_file(root, path, hashes, max_bytes=limit)
    ordered = tuple((key, hashes[key]) for key in sorted(hashes))
    digest = sha256_text(canonical_json({key: value for key, value in ordered}))
    return SourceSnapshot(file_hashes=ordered, source_snapshot_hash=digest)


def bind_hashes(
    *,
    lhs_bytes: Optional[bytes] = None,
    rhs_bytes: Optional[bytes] = None,
    residual_bytes: Optional[bytes] = None,
    assumptions_hash: str,
    source_snapshot_hash: str,
    verifier_route: str = DEFAULT_VERIFIER_ROUTE,
    engine_version: str = ENGINE_VERSION,
    edge_id: str = "",
    edge_type: str = "",
    declared_assumptions: tuple[str, ...] = (),
) -> BoundHashes:
    """Bind content hashes so a later byte change cannot reuse a ZERO row."""
    assumptions = _require_hash(assumptions_hash, "assumptions_hash")
    snapshot = _require_hash(source_snapshot_hash, "source_snapshot_hash")
    lhs_hash = _optional_bytes_hash(lhs_bytes)
    rhs_hash = _optional_bytes_hash(rhs_bytes)
    residual_hash = _optional_bytes_hash(residual_bytes)
    payload = {
        "assumptions_hash": assumptions,
        "declared_assumptions": list(declared_assumptions),
        "edge_id": edge_id,
        "edge_type": edge_type,
        "engine_version": engine_version,
        "lhs_hash": lhs_hash,
        "residual_hash": residual_hash,
        "rhs_hash": rhs_hash,
        "source_snapshot_hash": snapshot,
        "verifier_route": verifier_route,
    }
    obligation_hash = sha256_text(canonical_json(payload))
    return BoundHashes(
        lhs_hash=lhs_hash,
        rhs_hash=rhs_hash,
        residual_hash=residual_hash,
        assumptions_hash=assumptions,
        source_snapshot_hash=snapshot,
        obligation_hash=obligation_hash,
        verifier_route=verifier_route,
        engine_version=engine_version,
    )


def load_declared_assumptions(workspace: AuditWorkspace) -> DeclaredAssumptions:
    """Load ``assumptions.yaml``. ``real:false`` is rejected as in v0.1."""
    _, path = contained_relpath(
        workspace.root, workspace.config.assumptions, "assumptions")
    raw = read_bytes(path, max_bytes=MAX_METADATA_BYTES)
    mapping = safe_yaml_mapping(raw, path, "ASSUMPTIONS_PARSE_FAILURE")
    require_keys(
        mapping, allowed=_ASSUMPTION_KEYS, required=frozenset({"symbols"}),
        code="ASSUMPTIONS_SCHEMA_INVALID", path=path)
    raw_symbols = mapping["symbols"]
    if isinstance(raw_symbols, list) and any(
            isinstance(item, dict) and item.get("real") is False
            for item in raw_symbols):
        raise AuditError(
            "UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS",
            "the audit workspace rejects real:false because its complex-symbol "
            "semantics are not currently safe for certification",
            path=str(path),
        )
    try:
        symbols = tuple(normalize_symbols(raw_symbols))
        functions = tuple(normalize_functions(
            mapping.get("functions"),
            declared_symbol_names={item["name"] for item in symbols},
        ))
    except AdapterError as exc:
        raise AuditError(
            "ASSUMPTIONS_SCHEMA_INVALID", exc.code, path=str(path),
        ) from None
    rules = _parse_declared_rules(mapping.get("rules"), path)
    return DeclaredAssumptions(
        symbols=symbols,
        functions=functions,
        assumptions_hash=sha256_bytes(raw),
        names=tuple(item["name"] for item in symbols),
        rules=rules,
    )


def _parse_declared_rules(raw: Any, path: Path) -> tuple[str, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(
            isinstance(item, str) and item.strip() for item in raw):
        raise AuditError(
            "ASSUMPTIONS_SCHEMA_INVALID",
            "rules must be a list of non-empty strings",
            path=str(path),
        )
    names = tuple(item.strip() for item in raw)
    unknown = [name for name in names if name not in ALLOWED_DECLARED_RULES]
    if unknown:
        raise AuditError(
            "ASSUMPTIONS_SCHEMA_INVALID",
            "unknown declared rule: " + ", ".join(unknown),
            path=str(path),
        )
    if len(names) != len(set(names)):
        raise AuditError(
            "ASSUMPTIONS_SCHEMA_INVALID",
            "duplicate declared rule names",
            path=str(path),
        )
    return names


def assumption_gate_status(
    declared_names: tuple[str, ...] | frozenset[str],
    assumptions_used: tuple[str, ...],
) -> Optional[str]:
    """Return ASSUMPTION_REQUIRED / COMPILE_FAILURE, or None if the gate passes.

    Names in ``assumptions_used`` that are not in the workspace declaration
    are ASSUMPTION_REQUIRED. Extra declared symbols that this edge does not
    list are allowed: the workspace symbol table is shared across edges.
    An empty ``assumptions_used`` uses the declared namespace as-is.
    """
    declared = frozenset(declared_names)
    used = frozenset(assumptions_used)
    undeclared = sorted(used - declared)
    if undeclared:
        return ASSUMPTION_REQUIRED
    return None


def compile_and_verify_residual(
    *,
    residual_text: Optional[str] = None,
    left: Optional[str] = None,
    right: Optional[str] = None,
    symbols: Any,
    functions: Any = None,
) -> tuple[str, Optional[VerificationResult]]:
    """Compile one residual and adjudicate it with ``verify_equivalent``.

    A residual is parsed as an expression expected to equal ``0``. Otherwise
    lhs/rhs are parsed and checked for exact equivalence. Sequential: do not
    call this concurrently; SymPy is not treated as thread-safe.
    """
    if residual_text is not None and residual_text.strip():
        verification = verify_equivalent(
            residual_text, "0", symbols, functions=functions)
        return _engine_result(verification), verification
    if left is not None and right is not None:
        verification = verify_equivalent(
            left, right, symbols, functions=functions)
        return _engine_result(verification), verification
    return COMPILE_FAILURE, None


def adjudicate_lowered_edge(
    edge: AuditEdge,
    workspace: AuditWorkspace,
    grounding: GroundingResult,
    lowering: LoweringResult,
    *,
    snapshot: SourceSnapshot,
    assumptions: DeclaredAssumptions,
    engine_version: str = ENGINE_VERSION,
    verifier_route: str = DEFAULT_VERIFIER_ROUTE,
) -> AuditRecord:
    """Turn one grounded, lowered edge into an integrity-bound machine record."""
    source_refs = grounding.source_refs or tuple(
        item for item in (edge.source_from, edge.source_to) if item)
    lhs_text, lhs_bytes, _ = _resolve_expression(
        workspace, lowering.left if lowering.left is not None else edge.lhs)
    rhs_text, rhs_bytes, _ = _resolve_expression(
        workspace, lowering.right if lowering.right is not None else edge.rhs)
    residual_text, residual_bytes, residual_relpath = _resolve_residual(
        workspace, lowering, edge)
    if residual_bytes is None and lhs_text is not None and rhs_text is not None:
        residual_text = f"({lhs_text}) - ({rhs_text})"
        residual_bytes = residual_text.encode("utf-8")
    bound = bind_hashes(
        lhs_bytes=lhs_bytes,
        rhs_bytes=rhs_bytes,
        residual_bytes=residual_bytes,
        assumptions_hash=assumptions.assumptions_hash,
        source_snapshot_hash=snapshot.source_snapshot_hash,
        verifier_route=verifier_route,
        engine_version=engine_version,
        edge_id=edge.edge_id,
        edge_type=edge.edge_type,
        declared_assumptions=edge.assumptions_used,
    )
    stored_residual = _bounded_residual_text(residual_text)
    warnings = tuple(redact_text(item)[:2048] for item in lowering.warnings)

    if edge.edge_type not in EDGE_TYPES:
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=INVALID_RECORD, result=INVALID_RECORD,
            executable=False, warnings=(*warnings, "EDGE_TYPE_INVALID"),
            residual_text=stored_residual, artifact_relpath=residual_relpath,
        ))
    if not grounding.ok:
        status = grounding.status if grounding.status in AUDIT_STATUSES else GROUNDING_FAILURE
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=status, result=status,
            executable=False,
            warnings=(*warnings, *grounding.issues),
            residual_text=stored_residual, artifact_relpath=residual_relpath,
        ))
    if edge.edge_type == SPLIT_PARENT:
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=SPLIT, result=SPLIT, executable=False,
            warnings=warnings, residual_text=stored_residual,
            artifact_relpath=residual_relpath, children=edge.children,
        ))
    if edge.edge_type == BZ_PERIODIC_INTEGRATION_BY_PARTS:
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=NOT_LOWERED, result=NOT_LOWERED, executable=False,
            warnings=(*warnings, "BZ_IBP_NOT_LOCAL_RESIDUAL"),
            residual_text=stored_residual,
            artifact_relpath=residual_relpath, children=edge.children,
        ))

    executable = bool(lowering.executable)
    if not executable:
        status = lowering.status if lowering.status in AUDIT_STATUSES else (
            default_status_for_edge_type(edge.edge_type))
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=status, result=status, executable=False,
            warnings=warnings, residual_text=stored_residual,
            artifact_relpath=residual_relpath, children=edge.children,
        ))

    gate = assumption_gate_status(assumptions.names, edge.assumptions_used)
    if gate is not None:
        return _seal(_record(
            workspace, edge, source_refs, bound,
            status=gate, result=gate, executable=False,
            warnings=(*warnings, "DECLARED_ASSUMPTIONS_OMITTED"
                      if gate == ASSUMPTION_REQUIRED else
                      "UNDECLARED_ASSUMPTIONS_USED"),
            residual_text=stored_residual, artifact_relpath=residual_relpath,
            children=edge.children,
        ))

    result, verification = compile_and_verify_residual(
        residual_text=residual_text,
        left=lhs_text,
        right=rhs_text,
        symbols=list(assumptions.symbols),
        functions=list(assumptions.functions),
    )
    runtime = 0.0 if verification is None else float(verification.seconds)
    if result == ZERO and edge.edge_type == ASYMPTOTIC_CLAIM:
        if not asymptotic_remainder_certified(None):
            warnings = (*warnings, "ASYMPTOTIC_ZERO_WITHOUT_REMAINDER_CERTIFICATE")
            result = UNKNOWN
    if verification is None and result == COMPILE_FAILURE:
        executable_flag = False
    else:
        executable_flag = True
    return _seal(_record(
        workspace, edge, source_refs, bound,
        status=result, result=result, executable=executable_flag,
        warnings=warnings, residual_text=stored_residual,
        artifact_relpath=residual_relpath, children=edge.children,
        runtime_seconds=runtime,
        claim=edge.claim or lowering.obligation_id or "",
    ))


def apply_split_parent_statuses(
    records: tuple[AuditRecord, ...],
) -> tuple[AuditRecord, ...]:
    """Set SPLIT parent status from children. Parent is never engine ZERO."""
    by_id = {record.edge_id: record for record in records}
    updated: list[AuditRecord] = []
    for record in records:
        if record.edge_type != SPLIT_PARENT:
            updated.append(record)
            continue
        status = derive_split_parent_status(record, by_id)
        if status == ZERO:
            status = SPLIT
        updated.append(_seal(replace(
            record, status=status, result=status, executable=False,
        )))
    return tuple(updated)


def apply_bz_ibp_parent_statuses(
    records: tuple[AuditRecord, ...],
    declared_rules: tuple[str, ...] | frozenset[str],
) -> tuple[AuditRecord, ...]:
    """Seal BZ IBP parents from local children + declared torus periodicity.

    Never engine ZERO. A missing periodicity declaration is
    ASSUMPTION_REQUIRED, not a fake integral identity.
    """
    by_id = {record.edge_id: record for record in records}
    updated: list[AuditRecord] = []
    for record in records:
        if record.edge_type != BZ_PERIODIC_INTEGRATION_BY_PARTS:
            updated.append(record)
            continue
        status = derive_bz_ibp_parent_status(record, by_id, declared_rules)
        if status == ZERO:
            status = NOT_LOWERED
        extra: tuple[str, ...] = ()
        certificate = None
        if status == CERTIFIED_BY_RULE:
            extra = ("BZ_IBP_CERTIFIED_BY_LOCAL_ZERO_AND_DECLARED_TORUS",)
            children: list[tuple[str, str]] = []
            for child_id in record.children:
                child = by_id.get(child_id)
                children.append(
                    (child_id, child.status if child is not None else "MISSING"))
            certificate = RuleCertificate(
                rule_id=BZ_TORUS_PERIODICITY,
                local_children=tuple(children),
                domain=record.ibp_domain,
                conclusion=BZ_IBP_CONCLUSION,
                result=CERTIFIED_BY_RULE,
            )
        elif status == ASSUMPTION_REQUIRED:
            extra = ("BZ_TORUS_PERIODICITY_REQUIRED",)
        elif status == NOT_LOWERED:
            extra = ("BZ_IBP_NOT_CERTIFIED",)
        updated.append(_seal(replace(
            record,
            status=status,
            result=status,
            executable=False,
            warnings=tuple(dict.fromkeys((*record.warnings, *extra))),
            rule_certificate=certificate,
        )))
    return tuple(updated)


def write_exclusive_audit_run(
    runs_directory: PathLike,
    run_id: str,
    records: tuple[AuditRecord, ...],
    provenance: Mapping[str, Any],
) -> Path:
    """Create ``runs/<run_id>/`` exclusively. Never overwrite a run id."""
    safe_id = _normalize_run_id(run_id)
    runs_root = Path(runs_directory)
    try:
        if runs_root.exists() and (runs_root.is_symlink() or not runs_root.is_dir()):
            raise AuditError(
                "RUNS_DIRECTORY_UNSAFE",
                "runs must be a real directory",
                path=str(runs_root),
            )
        runs_root.mkdir(parents=True, exist_ok=True)
    except AuditError:
        raise
    except OSError as exc:
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE", str(exc), path=str(runs_root),
        ) from None
    destination = runs_root / safe_id
    if destination.exists() or destination.is_symlink():
        raise AuditError(
            "RUN_ALREADY_EXISTS",
            "never overwrite a previous audit run",
            path=str(destination),
        )
    staging = runs_root / f".{safe_id}.{secrets.token_hex(6)}.tmp"
    try:
        staging.mkdir(exist_ok=False)
    except FileExistsError:
        raise AuditError(
            "RUN_ALREADY_EXISTS",
            "never overwrite a previous audit run",
            path=str(staging),
        ) from None
    except OSError as exc:
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE", str(exc), path=str(staging),
        ) from None
    try:
        payload = [record.to_dict() for record in records]
        safe_provenance = dict(provenance)
        safe_provenance["run_id"] = safe_id
        _write_json_new(staging / PROVENANCE_FILE_NAME, safe_provenance)
        _write_json_new(staging / MACHINE_RECORDS_FILE, payload)
        os.rename(staging, destination)
    except AuditError:
        _remove_staging(staging)
        raise
    except OSError:
        _remove_staging(staging)
        if destination.exists() or destination.is_symlink():
            raise AuditError(
                "RUN_ALREADY_EXISTS",
                "never overwrite a previous audit run",
                path=str(destination),
            ) from None
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE",
            "could not persist the exclusive audit run",
            path=str(destination),
        ) from None
    except BaseException:
        _remove_staging(staging)
        raise
    return destination


def persist_audit_run(
    workspace: AuditWorkspace,
    records: tuple[AuditRecord, ...],
    *,
    snapshot: SourceSnapshot,
    assumptions: DeclaredAssumptions,
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
    runtime_seconds: float = 0.0,
    warnings: tuple[str, ...] = (),
) -> AuditRun:
    """Persist sealed records under an exclusive run directory."""
    stamp = timestamp or _now_iso()
    safe_id = _normalize_run_id(run_id or _new_run_id(stamp))
    audit_id = _audit_id(workspace)
    provenance = build_audit_provenance(
        run_id=safe_id,
        audit_id=audit_id,
        timestamp=stamp,
        snapshot=snapshot,
        assumptions_hash=assumptions.assumptions_hash,
        records=records,
        runtime_seconds=runtime_seconds,
        warnings=warnings,
        verifier_route=workspace.config.verifier_profile,
    )
    directory = write_exclusive_audit_run(
        _runs_directory(workspace), safe_id, records, provenance)
    return AuditRun(
        run_id=safe_id,
        audit_id=audit_id,
        directory=directory,
        records=records,
    )


def build_audit_provenance(
    *,
    run_id: str,
    audit_id: str,
    timestamp: str,
    snapshot: SourceSnapshot,
    assumptions_hash: str,
    records: tuple[AuditRecord, ...],
    runtime_seconds: float,
    warnings: tuple[str, ...] = (),
    verifier_route: str = DEFAULT_VERIFIER_ROUTE,
) -> dict[str, Any]:
    file_hashes = snapshot.mapping()
    expression_hashes = {
        path: digest for path, digest in file_hashes.items()
        if path.startswith(f"{EXPRESSIONS_DIRECTORY}/")
    }
    input_hashes = {
        path: digest for path, digest in file_hashes.items()
        if path not in expression_hashes
    }
    return {
        "schema_version": AUDIT_PROVENANCE_SCHEMA_VERSION,
        "audit_schema_version": AUDIT_SCHEMA_VERSION,
        "audit_protocol_version": AUDIT_PROTOCOL_VERSION,
        "run_id": run_id,
        "audit_id": audit_id,
        "timestamp": timestamp,
        "package_version": PACKAGE_VERSION,
        "engine_version": ENGINE_VERSION,
        "agent_protocol_version": AGENT_PROTOCOL_VERSION,
        "git_commit": engine_git_sha(),
        "verifier_route": verifier_route,
        "source_snapshot_hash": snapshot.source_snapshot_hash,
        "assumptions_hash": assumptions_hash,
        "input_hashes": dict(sorted(input_hashes.items())),
        "expression_hashes": dict(sorted(expression_hashes.items())),
        "runtime_seconds": float(runtime_seconds),
        "warnings": [redact_text(item)[:2048] for item in warnings],
        "record_count": len(records),
        "authority": AUTHORITY,
        "dependency_versions": dependency_versions(),
        "writer": AUTHORITY,
    }


def _ground_and_lower(
    edge: AuditEdge,
    workspace: AuditWorkspace,
) -> tuple[GroundingResult, LoweringResult]:
    try:
        grounding = edges_layer.ground_edge(edge, workspace)
    except AuditError as exc:
        status = NOT_LOWERED if exc.code == "NOT_IMPLEMENTED" else GROUNDING_FAILURE
        grounding = GroundingResult(
            edge=edge,
            ok=False,
            status=status,
            issues=(exc.code,),
            source_refs=tuple(
                item for item in (edge.source_from, edge.source_to) if item),
            source_snapshot_hash="",
        )
    try:
        lowering = lowering_layer.lower_edge(edge, workspace, grounding)
    except AuditError as exc:
        try:
            default_status = default_status_for_edge_type(edge.edge_type)
            applicability = lowering_applicability(edge.edge_type)
        except AuditError:
            default_status = INVALID_RECORD
            applicability = "NOT_APPLICABLE"
        if exc.code == "NOT_IMPLEMENTED":
            status = default_status
        else:
            status = COMPILE_FAILURE
        lowering = LoweringResult(
            edge_id=edge.edge_id,
            executable=False,
            status=status,
            residual_text=edge.residual,
            residual_path=None,
            obligation_id=None,
            left=edge.lhs,
            right=edge.rhs,
            warnings=(exc.code,),
            applicability=applicability,
        )
    return grounding, lowering


def _engine_result(verification: VerificationResult) -> str:
    if verification.verdict == ZERO:
        return ZERO
    if verification.verdict == NONZERO:
        return NONZERO
    for item in verification.evidence:
        if isinstance(item, dict) and item.get("kind") == "construction_or_parse_failed":
            return PARSE_FAILURE
    return UNKNOWN


def _record(
    workspace: AuditWorkspace,
    edge: AuditEdge,
    source_refs: tuple[str, ...],
    bound: BoundHashes,
    *,
    status: str,
    result: str,
    executable: bool,
    warnings: tuple[str, ...] = (),
    residual_text: Optional[str] = None,
    artifact_relpath: Optional[str] = None,
    children: tuple[str, ...] = (),
    runtime_seconds: float = 0.0,
    claim: str = "",
) -> AuditRecord:
    return AuditRecord(
        audit_id=_audit_id(workspace),
        edge_id=edge.edge_id,
        source_refs=source_refs,
        edge_type=edge.edge_type,
        status=status,
        result=result,
        source_snapshot_hash=bound.source_snapshot_hash,
        engine_version=bound.engine_version,
        runtime_seconds=runtime_seconds,
        lhs_hash=bound.lhs_hash,
        rhs_hash=bound.rhs_hash,
        residual_hash=bound.residual_hash,
        assumptions_hash=bound.assumptions_hash,
        obligation_hash=bound.obligation_hash,
        verifier_route=bound.verifier_route,
        warnings=warnings,
        children=children or edge.children,
        remainder_certificate_hash=None,
        declared_assumptions=edge.assumptions_used,
        executable=executable,
        claim=claim or edge.claim,
        residual_text=residual_text,
        artifact_relpath=artifact_relpath,
        required_rules=edge.required_rules,
        ibp_domain=edge.ibp_domain,
    )


def _seal(record: AuditRecord) -> AuditRecord:
    """Never persist an integrity-illegal ZERO."""
    issues = integrity_issues(record)
    if not issues:
        return record
    if record.status == ZERO or record.result == ZERO:
        return replace(
            record,
            status=INVALID_RECORD,
            result=INVALID_RECORD,
            warnings=tuple(dict.fromkeys((*record.warnings, *issues))),
        )
    return record


def _resolve_residual(
    workspace: AuditWorkspace,
    lowering: LoweringResult,
    edge: AuditEdge,
) -> tuple[Optional[str], Optional[bytes], Optional[str]]:
    if lowering.residual_path:
        return _read_workspace_expression(workspace, lowering.residual_path)
    if edge.residual and _is_workspace_file(workspace, edge.residual):
        return _read_workspace_expression(workspace, edge.residual)
    text = lowering.residual_text if lowering.residual_text is not None else edge.residual
    if text is None:
        return None, None, None
    return text, text.encode("utf-8"), None


def _resolve_expression(
    workspace: AuditWorkspace,
    value: Optional[str],
) -> tuple[Optional[str], Optional[bytes], Optional[str]]:
    if value is None:
        return None, None, None
    if _is_workspace_file(workspace, value):
        return _read_workspace_expression(workspace, value)
    return value, value.encode("utf-8"), None


def _read_workspace_expression(
    workspace: AuditWorkspace,
    relpath: str,
) -> tuple[str, bytes, str]:
    relative, absolute = contained_relpath(workspace.root, relpath, "expression")
    raw = read_bytes(absolute, max_bytes=MAX_SOURCE_BYTES)
    text = decode_utf8(raw, absolute, "EXPRESSION_PARSE_FAILURE")
    return text, raw, relative


def _is_workspace_file(workspace: AuditWorkspace, value: str) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    if "\\" in value:
        return False
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        return False
    candidate = workspace.root / relative
    return candidate.is_file() and not candidate.is_symlink()


def _bounded_residual_text(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    if len(text) > _MAX_RESIDUAL_TEXT:
        return None
    return text


def _optional_bytes_hash(raw: Optional[bytes]) -> Optional[str]:
    if raw is None:
        return None
    return sha256_bytes(raw)


def _require_hash(value: str, field: str) -> str:
    if not isinstance(value, str) or not _HASH_RE.fullmatch(value):
        raise AuditError("INVALID_RECORD", f"{field} is not a sha256 hex digest")
    return value


def _audit_id(workspace: AuditWorkspace) -> str:
    name = workspace.config.audit_name
    if isinstance(name, str) and _RUN_ID_RE.fullmatch(name):
        return name
    return "audit"


def _normalize_run_id(value: str) -> str:
    if not isinstance(value, str) or not _RUN_ID_RE.fullmatch(value):
        raise AuditError("RUN_ID_INVALID", "run id has an invalid format")
    if redact_text(value) != value:
        raise AuditError("RUN_ID_INVALID", "run id has an invalid format")
    return value


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_run_id(timestamp: str) -> str:
    stamp = timestamp.replace("-", "").replace(":", "")
    return f"{stamp}-{secrets.token_hex(4)}"


def _runs_directory(workspace: AuditWorkspace) -> Path:
    runs = workspace.root / RUNS_DIRECTORY
    if runs.is_symlink():
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE", "runs must not be a symbolic link",
            path=str(runs),
        )
    try:
        runs.mkdir(exist_ok=True)
    except OSError as exc:
        raise AuditError(
            "RUNS_DIRECTORY_UNSAFE", str(exc), path=str(runs),
        ) from None
    return assert_contained(workspace.root, runs, "runs")


def _hash_source_file(
    root: Path,
    path: Path,
    hashes: dict[str, str],
    *,
    max_bytes: int,
) -> None:
    if path.is_symlink():
        raise AuditError(
            "PATH_OUTSIDE_WORKSPACE",
            "source must not be a symlink",
            path=str(path),
        )
    if not path.is_file():
        return
    assert_contained(root, path, "source")
    relative = path.relative_to(root).as_posix()
    hashes[relative] = sha256_bytes(read_bytes(path, max_bytes=max_bytes))


def _iter_regular_files(directory: Path) -> list[Path]:
    files: list[Path] = []
    stack = [directory]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as entries:
                children = list(entries)
        except OSError as exc:
            raise AuditError(
                "SOURCE_FILE_UNREADABLE", str(exc), path=str(current),
            ) from None
        for entry in children:
            if entry.is_symlink():
                raise AuditError(
                    "PATH_OUTSIDE_WORKSPACE",
                    "source must not be a symlink",
                    path=entry.path,
                )
            if entry.is_dir(follow_symlinks=False):
                stack.append(Path(entry.path))
            elif entry.is_file(follow_symlinks=False):
                files.append(Path(entry.path))
    files.sort()
    return files


def _assert_sources_unchanged(
    workspace: AuditWorkspace,
    before: SourceSnapshot,
) -> None:
    after = snapshot_audit_sources(workspace)
    if after.source_snapshot_hash != before.source_snapshot_hash:
        raise AuditError(
            "SOURCE_MUTATED",
            "audit verification must not rewrite researcher-owned sources",
            path=str(workspace.root),
        )
    for root in source_immutability_roots(workspace):
        if root.is_symlink():
            raise AuditError(
                "PATH_OUTSIDE_WORKSPACE",
                "source must not be a symlink",
                path=str(root),
            )


def _write_json_new(path: Path, payload: Any) -> None:
    if path.exists() or path.is_symlink():
        raise AuditError(
            "RUN_ALREADY_EXISTS",
            "never overwrite a previous audit run",
            path=str(path),
        )
    encoded = json.dumps(
        payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if len(encoded.encode("utf-8")) > _MAX_RUN_ARTIFACT_BYTES:
        raise AuditError(
            "RUN_ARTIFACT_INVALID",
            "run artifact exceeds the safe size limit",
            path=str(path),
        )
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
    file_fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(file_fd)
    finally:
        os.close(file_fd)


def _remove_staging(path: Path) -> None:
    try:
        if path.is_dir() and not path.is_symlink():
            for child in path.iterdir():
                try:
                    child.unlink()
                except OSError:
                    pass
            path.rmdir()
    except OSError:
        pass


def _read_run_file(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise AuditError(
            "RUN_ARTIFACT_INVALID",
            "run artifact must be a regular file",
            path=str(path),
        )
    return read_bytes(path, max_bytes=_MAX_RUN_ARTIFACT_BYTES)


def _strict_json(raw: bytes, path: Path) -> Any:
    text = decode_utf8(raw, path, "RUN_ARTIFACT_INVALID")

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, ValueError) as exc:
        raise AuditError(
            "RUN_ARTIFACT_INVALID", str(exc), path=str(path),
        ) from None


def _provenance_timestamp(run_dir: Path) -> str:
    path = run_dir / PROVENANCE_FILE_NAME
    if not path.is_file() or path.is_symlink():
        return ""
    try:
        payload = _strict_json(read_bytes(path, max_bytes=_MAX_RUN_ARTIFACT_BYTES), path)
    except AuditError:
        return ""
    if not isinstance(payload, dict):
        return ""
    value = payload.get("timestamp")
    if isinstance(value, str) and _TIMESTAMP_RE.fullmatch(value):
        return value
    return ""


__all__ = [
    "AUDIT_PROVENANCE_SCHEMA_VERSION",
    "AUTHORITY",
    "AuditRun",
    "BoundHashes",
    "DeclaredAssumptions",
    "MACHINE_RECORDS_FILE",
    "SourceSnapshot",
    "adjudicate_lowered_edge",
    "apply_bz_ibp_parent_statuses",
    "apply_split_parent_statuses",
    "assumption_gate_status",
    "bind_hashes",
    "build_audit_provenance",
    "compile_and_verify_residual",
    "latest_audit_run_id",
    "load_audit_run",
    "load_declared_assumptions",
    "persist_audit_run",
    "snapshot_audit_sources",
    "verify_audit",
    "write_exclusive_audit_run",
]
