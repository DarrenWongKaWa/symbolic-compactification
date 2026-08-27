"""Guo DEV source catalog.

Wraps `research.grounded_proposer.catalog` and Track B `build_index`.
The standard Guo DEV expression is expected to contain 4 Sum blocks and
14 Piecewise branches. Those are structural counts, not a representation
choice. Catalog member ids are G####. Extra gold fields are not added.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from research.grounded_proposer.catalog import (
    catalog_entries,
    catalog_ids,
    render_catalog,
)
from research.obligation_ir.source_index import SourceIndex, build_index
from research.representation_invention.schema import is_catalog_id
from symbolic_compactification import parse_expression
from symbolic_compactification.structure import structure_summary

ROOT = Path(__file__).resolve().parents[3]
# Existing scientific input. Do not substitute a shortened expression.
GUO_SOURCE = ROOT / "examples" / "long" / "Guo_Sigma_abc_dc_exact.txt"

EXPECTED_N_SUMS = 4
EXPECTED_N_PIECEWISE = 4
EXPECTED_N_PIECEWISE_BRANCHES = 14

CATALOG_ENTRY_KEYS = (
    "source_node_id",
    "sol_node_id",
    "kind",
    "parent_gid",
    "ops",
    "fingerprint",
    "text",
)


@dataclass
class GuoDevCatalog:
    """Catalog + structural counts for the standard Guo DEV source."""

    item: dict[str, Any]
    index: SourceIndex
    entries: list[dict[str, Any]]
    n_sums: int
    n_piecewise: int
    n_piecewise_branches: int

    @property
    def ids(self) -> set[str]:
        return catalog_ids(self.entries)


def count_catalog_kinds(entries: list[dict[str, Any]]) -> dict[str, int]:
    n_sums = sum(1 for e in entries if e.get("kind") == "sum")
    n_branches = sum(1 for e in entries if e.get("kind") == "piecewise_branch")
    return {"n_sums": n_sums, "n_piecewise_branches": n_branches}


def _load_item() -> dict[str, Any]:
    if not GUO_SOURCE.is_file():
        raise FileNotFoundError(f"Guo DEV source missing: {GUO_SOURCE}")
    from research.llm_abstraction.tasks import load_guo_item, public_item

    try:
        raw = load_guo_item()
    except Exception as exc:
        raise RuntimeError(f"Guo DEV expression failed to load: {GUO_SOURCE}") from exc
    if not str(raw.get("current") or "").strip():
        raise RuntimeError(f"Guo DEV expression loaded empty: {GUO_SOURCE}")
    return public_item(raw)


@lru_cache(maxsize=1)
def load_guo_catalog() -> GuoDevCatalog:
    """Load the real Guo DEV expression, index it, and wrap the P1 catalog.

    Load/parse failure raises. Callers must not skip.
    """
    item = _load_item()
    symbols = item.get("symbols") or []
    functions = item.get("functions") or []
    current = item["current"]
    try:
        expr = parse_expression(current, symbols, functions=functions or None)
        summary = structure_summary(expr)
        index = build_index(current, symbols, functions)
    except Exception as exc:
        raise RuntimeError(f"Guo DEV expression failed to parse: {GUO_SOURCE}") from exc
    entries = catalog_entries(index)
    return GuoDevCatalog(
        item=item,
        index=index,
        entries=entries,
        n_sums=int(summary["sums"]),
        n_piecewise=int(summary["piecewise"]),
        n_piecewise_branches=int(summary["piecewise_branches"]),
    )


def assert_catalog_ids(entries: list[dict[str, Any]]) -> None:
    for e in entries:
        gid = e.get("source_node_id") or ""
        if not is_catalog_id(gid):
            raise AssertionError(f"catalog id is not G####: {gid!r}")


__all__ = [
    "CATALOG_ENTRY_KEYS",
    "EXPECTED_N_PIECEWISE",
    "EXPECTED_N_PIECEWISE_BRANCHES",
    "EXPECTED_N_SUMS",
    "GUO_SOURCE",
    "GuoDevCatalog",
    "assert_catalog_ids",
    "build_index",
    "catalog_entries",
    "catalog_ids",
    "count_catalog_kinds",
    "load_guo_catalog",
    "render_catalog",
]
