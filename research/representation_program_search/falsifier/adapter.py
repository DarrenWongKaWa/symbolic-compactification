"""Small validator seam for evaluator fixtures, independent of M1.

This module checks only grammar membership and the frozen Hermite multiplicity
invariant. It does not compile symbolic programs and cannot certify equality.
Fixture failure classes are mapped to the already implemented M1 compiler's
stable failure-code prefix; they are not required to be identical strings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from research.representation_program_search.grammar_v1 import (
    ACTIONS,
    GRAMMAR_ID,
    LATENT_FORMS,
    OPERATORS,
)

M1_FAILURE_PREFIX_BY_ADAPTER_CLASS = {
    "HERMITE_NODE_MULTIPLICITY": "HERMITE_REPEATED_NODE_REQUIRED",
}


@dataclass(frozen=True)
class AdapterResult:
    valid: bool
    failure_class: str | None = None


def validate_adapter_program(program: dict[str, Any]) -> AdapterResult:
    """Validate the fixture-facing subset of RepresentationGrammarV1."""
    if program.get("grammar_version") != GRAMMAR_ID:
        return AdapterResult(False, "GRAMMAR_VERSION")

    latents = program.get("latent_objects")
    nodes = program.get("node_structures")
    operators = program.get("operators")
    if not isinstance(latents, list) or not isinstance(nodes, list):
        return AdapterResult(False, "PROGRAM_SHAPE")
    if not isinstance(operators, list):
        return AdapterResult(False, "PROGRAM_SHAPE")

    latent_ids: set[str] = set()
    for latent in latents:
        if not isinstance(latent, dict) or latent.get("form") not in LATENT_FORMS:
            return AdapterResult(False, "LATENT_FORM")
        latent_id = latent.get("latent_id")
        if not isinstance(latent_id, str) or not latent_id or latent_id in latent_ids:
            return AdapterResult(False, "LATENT_ID")
        latent_ids.add(latent_id)

    node_map: dict[str, list[str]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            return AdapterResult(False, "NODE_SHAPE")
        node_id = node.get("node_id")
        labels = node.get("nodes")
        if not isinstance(node_id, str) or not isinstance(labels, list):
            return AdapterResult(False, "NODE_SHAPE")
        if not labels or not all(isinstance(label, str) and label for label in labels):
            return AdapterResult(False, "NODE_SHAPE")
        node_map[node_id] = labels

    for operator in operators:
        if not isinstance(operator, dict) or operator.get("operator") not in OPERATORS:
            return AdapterResult(False, "OPERATOR")
        latent_id = operator.get("latent")
        if latent_id is not None and latent_id not in latent_ids:
            return AdapterResult(False, "UNKNOWN_LATENT")
        if operator.get("operator") == "HERMITE_DD":
            labels = node_map.get(operator.get("node_structure"), [])
            if len(labels) == len(set(labels)):
                return AdapterResult(False, "HERMITE_NODE_MULTIPLICITY")
        if operator.get("operator") == "NEWTON_DD":
            labels = node_map.get(operator.get("node_structure"), [])
            if len(labels) != len(set(labels)):
                return AdapterResult(False, "NEWTON_REPEATED_NODE")

    return AdapterResult(True)


def validate_action_sequence(actions: dict[str, Any]) -> AdapterResult:
    """Check action vocabulary; payload typing remains the M1 compiler's job."""
    sequence = actions.get("actions")
    if not isinstance(sequence, list):
        return AdapterResult(False, "ACTION_SEQUENCE")
    for entry in sequence:
        if not isinstance(entry, dict) or entry.get("action") not in ACTIONS:
            return AdapterResult(False, "ILLEGAL_ACTION")
        if not isinstance(entry.get("payload"), dict):
            return AdapterResult(False, "ACTION_PAYLOAD")
    return AdapterResult(True)


def m1_failure_prefix(adapter_failure_class: str) -> str | None:
    """Return the M1 compiler prefix corresponding to a fixture-side class."""
    return M1_FAILURE_PREFIX_BY_ADAPTER_CLASS.get(adapter_failure_class)
