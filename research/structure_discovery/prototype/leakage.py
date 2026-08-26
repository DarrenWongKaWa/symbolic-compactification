"""Gold-leakage boundary. Proposer-visible payloads must not contain hidden gold."""
from __future__ import annotations

import json
from typing import Any

HIDDEN_FIELDS = (
    "human_reference",
    "target_compact",
    "hidden_gold",
    "gold_hypothesis_type",
    "gold_types",
    "forbidden_types",
    "forbidden_reconstructions",
    "gold_reconstruction",
    "gold_auxiliaries",
    "expected_verdict",
    "ladder_id",
    "polarity",
    "notes",
    "downstream_gold",
)

PUBLIC_FIELDS = (
    "id", "tier", "family", "domain", "split", "task",
    "current", "symbols", "functions", "assumptions",
    "scientific_context", "abstraction_level_hint",
    "source_format", "provenance_public",
)


def proposer_view(item: dict) -> dict:
    view = {k: item[k] for k in PUBLIC_FIELDS if k in item}
    view["hidden_from_proposer"] = True
    return view


def assert_no_leakage(payload: Any, extra_forbidden: tuple[str, ...] = ()) -> None:
    blob = json.dumps(payload, default=str)
    for key in HIDDEN_FIELDS + extra_forbidden:
        token = f'"{key}"'
        if token in blob:
            raise RuntimeError(f"F_LEAK: hidden field {key} in proposer payload")


def context_leaks_gold_names(item: dict) -> list[str]:
    """Adversarial check: scientific_context must not contain gold names."""
    ctx = " ".join(item.get("scientific_context") or [])
    gold = item.get("hidden_gold") or {}
    names = []
    names.extend(gold.get("aux_names") or [])
    names.extend(item.get("gold_auxiliaries") or [])
    hits = []
    for n in names:
        if n and len(n) >= 3 and n in ctx:
            hits.append(n)
    return hits
