"""Guo DEV catalog — proposer-visible API.

Evaluation queries live under `eval/` and are not imported here.
The `proposer_view` submodule is not re-exported (name would shadow).
"""

from research.representation_invention.guo.catalog import (
    EXPECTED_N_PIECEWISE_BRANCHES,
    EXPECTED_N_SUMS,
    GUO_SOURCE,
    GuoDevCatalog,
    catalog_entries,
    catalog_ids,
    load_guo_catalog,
    render_catalog,
)

__all__ = [
    "EXPECTED_N_PIECEWISE_BRANCHES",
    "EXPECTED_N_SUMS",
    "GUO_SOURCE",
    "GuoDevCatalog",
    "catalog_entries",
    "catalog_ids",
    "load_guo_catalog",
    "render_catalog",
]
