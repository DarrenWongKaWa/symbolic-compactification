"""Hypothesis graph. Scientific state changes only on ZERO.

States: PROPOSED, CONSTRUCTABLE, ZERO_CERTIFIED, NONZERO_REFUTED,
UNKNOWN, DOMINATED. Parent/child edges recorded. AST-size is not a
discard criterion.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


STATES = (
    "PROPOSED",
    "CONSTRUCTABLE",
    "ZERO_CERTIFIED",
    "NONZERO_REFUTED",
    "UNKNOWN",
    "DOMINATED",
)


@dataclass
class Node:
    node_id: str
    parent_id: Optional[str]
    state: str
    hypothesis: dict
    construction: Optional[dict]
    verdict: Optional[str]
    d_level: str
    notes: str = ""


@dataclass
class HypothesisGraph:
    nodes: list[Node] = field(default_factory=list)

    def add(self, **kwargs) -> Node:
        node = Node(**kwargs)
        if node.state not in STATES:
            raise ValueError(node.state)
        self.nodes.append(node)
        return node

    def certified(self) -> list[Node]:
        return [n for n in self.nodes if n.state == "ZERO_CERTIFIED"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": len(self.nodes),
            "n_zero": sum(n.state == "ZERO_CERTIFIED" for n in self.nodes),
            "n_nonzero": sum(n.state == "NONZERO_REFUTED" for n in self.nodes),
            "n_unknown": sum(n.state == "UNKNOWN" for n in self.nodes),
            "nodes": [
                {
                    "node_id": n.node_id,
                    "parent_id": n.parent_id,
                    "state": n.state,
                    "hypothesis_type": (n.hypothesis or {}).get("hypothesis_type"),
                    "d_level": n.d_level,
                    "verdict": n.verdict,
                    "structured": (n.construction or {}).get("structured_text"),
                    "closed": (n.construction or {}).get("closed_text"),
                    "notes": n.notes,
                }
                for n in self.nodes
            ],
        }
