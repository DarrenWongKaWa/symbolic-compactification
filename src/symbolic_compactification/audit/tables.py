"""Authoritative reviewer tables. E6 implements generation from machine records.

VERIFIED TABLE IS GENERATED, NOT AUTHORED. Inclusion uses
``schema.table_bucket`` and ``schema.may_appear_in_verified_table`` only.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .evidence import AuditRun
from .schema import AuditError
from .workspace import AuditWorkspace


@dataclass(frozen=True)
class TableArtifacts:
    verified_md: Path
    structural_md: Path
    uncertified_md: Path
    nonzero_md: Path
    table_json: Path
    table_csv: Path


def generate_tables(workspace: AuditWorkspace, run: AuditRun) -> TableArtifacts:
    """E6: write TABLE_*.md plus verification_table.json/csv under reports/."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "table generation is implemented by the reviewer-table layer",
        path=str(workspace.root),
    )
