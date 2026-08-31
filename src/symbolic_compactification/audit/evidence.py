"""Immutable evidence store and audit verification. E5 implements the body.

Never overwrite a previous run. Changing source, residual, or assumptions
invalidates prior ZERO rows for the new snapshot. LLM text cannot write
these records.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .schema import AUDIT_SCHEMA_VERSION, AuditError, AuditRecord
from .workspace import AuditWorkspace


@dataclass(frozen=True)
class AuditRun:
    run_id: str
    audit_id: str
    directory: Path
    records: tuple[AuditRecord, ...]
    schema_version: str = AUDIT_SCHEMA_VERSION


def verify_audit(workspace: AuditWorkspace) -> AuditRun:
    """E5: snapshot, ground, lower, verify executable edges, persist records."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "audit verification is implemented by the evidence-store layer",
        path=str(workspace.root),
    )


def load_audit_run(workspace: AuditWorkspace, run_id: str) -> AuditRun:
    """E5: load an immutable recorded run. Do not reuse stale ZERO silently."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "audit run load is implemented by the evidence-store layer",
        path=str(workspace.root),
    )


def latest_audit_run_id(workspace: AuditWorkspace) -> str:
    raise AuditError(
        "NO_RECORDED_RUNS",
        "run 'symbolic-compactification audit verify <dir>' first",
        path=str(workspace.root / "runs"),
    )
