"""Gold / interpretation leakage checks for packets and prompts."""
from __future__ import annotations

import json
from typing import Any, Iterable

from symbolic_compactification.observations.ir import FORBIDDEN_INTERPRETATION

PACKET_FORBIDDEN = FORBIDDEN_INTERPRETATION + (
    "master function",
    "divided difference",
    "confluence",
    "nine generator",
    "physical generator",
    "thermal master",
    "therefore define",
    "Hermite",
    "Phi_Gamma",
    "PhiGamma",
    "this suggests",
    "this is a hermite",
    "PRB closed",
)


def blob_of(payload: Any) -> str:
    return json.dumps(payload, default=str)


def leak_hits(payload: Any, extra: Iterable[str] = ()) -> list[str]:
    low = blob_of(payload).lower()
    hits = []
    for tok in list(PACKET_FORBIDDEN) + list(extra):
        if tok and len(tok) >= 3 and tok.lower() in low:
            hits.append(tok)
    return hits


def assert_no_packet_interpretation(payload: Any, extra: Iterable[str] = ()) -> None:
    hits = leak_hits(payload, extra)
    if hits:
        raise RuntimeError(f"SOL packet interpretation leak: {hits}")


def gold_name_hits(payload: Any, item: dict) -> list[str]:
    names = []
    gold = item.get("hidden_gold") or {}
    names.extend(gold.get("aux_names") or [])
    names.extend(item.get("gold_auxiliaries") or [])
    names.extend(item.get("gold_names") or [])
    return leak_hits(payload, names)
