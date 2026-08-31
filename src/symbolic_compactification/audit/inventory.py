"""LaTeX/Markdown equation inventory. E2 implements the body.

Inventory extracts labels, environments, order, and source ranges. It does
not interpret LaTeX as symbolic algebra.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .schema import AuditError
from .workspace import AuditWorkspace


@dataclass(frozen=True)
class InventoriedEquation:
    equation_id: str
    label: Optional[str]
    environment: str
    source_file: str
    start_line: int
    end_line: int
    source_hash: str
    body: str
    curated: bool = False


@dataclass(frozen=True)
class EquationInventory:
    equations: tuple[InventoriedEquation, ...]
    duplicate_labels: tuple[str, ...]
    source_hash: str
    warnings: tuple[str, ...]


def inventory_equations(
    workspace: AuditWorkspace,
    *,
    write: bool = False,
) -> EquationInventory:
    """E2: extract equation references. ``write`` updates only tool-owned
    inventory sidecars under reports/, never curated equation mappings.
    """
    raise AuditError(
        "NOT_IMPLEMENTED",
        "equation inventory is implemented by the derivation-audit inventory layer",
        path=str(workspace.root),
    )


def load_equation_manifest(workspace: AuditWorkspace) -> EquationInventory:
    """E2: load equations/equations.yaml including curated mappings."""
    raise AuditError(
        "NOT_IMPLEMENTED",
        "equation manifest load is implemented by the inventory layer",
        path=str(workspace.root),
    )
