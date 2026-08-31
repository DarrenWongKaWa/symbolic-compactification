"""Reviewer verification package export. E8 implements the body."""
from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from .evidence import AuditRun
from .schema import AuditError
from .workspace import AuditWorkspace


def build_reviewer_package(
    workspace: AuditWorkspace,
    run: AuditRun,
    dest: Union[str, Path, None] = None,
) -> Path:
    """E8: export a clean reviewer-verification-package/ with reproduce.sh."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "reviewer package export is implemented by the package layer",
        path=str(workspace.root),
    )
