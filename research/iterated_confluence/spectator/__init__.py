"""Exact spectator split for Track V3 one-parameter edges.

Wraps Track V factor split. Reconstruction is required before a local
kernel is returned. False decomposition acceptance = 0.
"""
from research.iterated_confluence.spectator.split import (
    MODE_ADDITIVE,
    MODE_MULTIPLICATIVE,
    MODE_NONE,
    SplitEdgeResult,
    count_ops,
    split_edge,
    split_report,
)

__all__ = [
    "MODE_ADDITIVE",
    "MODE_MULTIPLICATIVE",
    "MODE_NONE",
    "SplitEdgeResult",
    "count_ops",
    "split_edge",
    "split_report",
]
