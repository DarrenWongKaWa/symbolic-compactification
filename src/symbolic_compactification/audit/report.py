"""Human-readable audit REPORT.md. E6 implements generation.

Machine claims in the report must be copied from the evidence store. Narrative
explanations are non-authoritative.
"""
from __future__ import annotations

from pathlib import Path

from .evidence import AuditRun
from .schema import AuditError
from .workspace import AuditWorkspace


def generate_audit_report(workspace: AuditWorkspace, run: AuditRun) -> Path:
    """E6: write reports/REPORT.md from machine evidence only."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "audit report generation is implemented by the reviewer-table layer",
        path=str(workspace.root),
    )
