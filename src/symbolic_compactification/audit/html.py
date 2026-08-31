"""Optional static HTML report. E9 implements if cost is small. Non-blocking."""
from __future__ import annotations

from pathlib import Path

from .evidence import AuditRun
from .schema import AuditError
from .workspace import AuditWorkspace


def generate_html_report(workspace: AuditWorkspace, run: AuditRun) -> Path:
    """E9: optional static HTML. Must not be required for alpha."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "HTML report is optional and unimplemented in the interface freeze",
        path=str(workspace.root),
    )
