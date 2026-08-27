"""Proposer-visible Guo DEV packet: catalog render + historical context.

Does not import evaluation queries. Hidden notes (COUNTS.md, eval/queries.py)
are listed here so tests can assert they are omitted from the packet.
No new gold hints. Scientific context is the historical Guo DEV wording.
"""
from __future__ import annotations

from typing import Any, Optional

from research.representation_invention.guo.catalog import (
    GuoDevCatalog,
    load_guo_catalog,
    render_catalog,
)
from research.structure_discovery.prototype.leakage import (
    assert_no_leakage,
    proposer_view as strip_item,
)

# Relpaths under this package that must not appear in the proposer packet.
HIDDEN_FROM_PROPOSER = (
    "COUNTS.md",
    "eval/queries.py",
)

# Historical Guo DEV scientific_context (research.llm_abstraction.tasks.load_guo_item).
SCIENTIFIC_CONTEXT = [
    "Identify a small number of latent mathematical objects or representation changes that could explain multiple non-identical structural families.",
    "Do not simplify the full expression.",
    "Do not invent physical names. For each hypothesis: identify members; define latent object; specify operators/maps; provide a construction plan; list proof obligations.",
]

_EXTRA_FORBIDDEN = (
    "gold_types",
    "gold_members",
    "gold_latent",
    "gold_operator",
    "forbidden_types",
    "hidden_gold",
    "gold_auxiliaries",
    "human_reference",
    "target_compact",
    "notes",
)


def proposer_view(catalog: Optional[GuoDevCatalog] = None) -> dict[str, Any]:
    """Public packet: stripped item + catalog render + historical context."""
    cat = catalog or load_guo_catalog()
    view = strip_item(cat.item)
    ctx = list(view.get("scientific_context") or SCIENTIFIC_CONTEXT)
    if not ctx:
        ctx = list(SCIENTIFIC_CONTEXT)
    view["scientific_context"] = ctx
    view["catalog_text"] = render_catalog(cat.entries)
    view["catalog_ids"] = sorted(cat.ids)
    for rel in HIDDEN_FROM_PROPOSER:
        view.pop(rel, None)
    assert_no_leakage(view, extra_forbidden=_EXTRA_FORBIDDEN)
    return view


def render_proposer_view(catalog: Optional[GuoDevCatalog] = None) -> str:
    """String form historically given to a proposer (catalog + context)."""
    view = proposer_view(catalog)
    ctx = "\n".join(f"- {c}" for c in view.get("scientific_context") or [])
    symbols = view.get("symbols") or []
    names = [s.get("name") if isinstance(s, dict) else s for s in symbols]
    parts = [
        "TASK: Propose grounded representation hypotheses for non-identical families.",
        "Do not simplify the full expression.",
        "",
        "DECLARED SYMBOLS:",
        repr(names),
        "DECLARED FUNCTIONS:",
        repr(list(view.get("functions") or [])),
        "SCIENTIFIC CONTEXT:",
        ctx or "(none)",
        "",
        view["catalog_text"],
        "",
        "RAW EXPRESSION:",
        str(view.get("current") or ""),
        "",
        "Respond with JSON only. Every source_node_id must be in the catalog.",
    ]
    return "\n".join(parts)


__all__ = [
    "HIDDEN_FROM_PROPOSER",
    "SCIENTIFIC_CONTEXT",
    "proposer_view",
    "render_proposer_view",
]
