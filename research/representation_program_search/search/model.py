"""Typed search-state and legal-action records for RPS S0/S1.

The ancestry and diagnostic fields are deliberately excluded from state
identity.  Canonical state hashes therefore identify a partial mathematical
program, not the route by which a search method reached it.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.grammar_v1 import ACTIONS, GRAMMAR_ID
from research.representation_program_search.program_ir import (
    LatentObject,
    MemberAssignment,
    NodeStructure,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
    canonical_json,
    canonical_program_hash,
)
from research.representation_program_search.program_ir.model import freeze_json, thaw_json


class SearchContractError(ValueError):
    """Stable fail-closed search-contract error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LegalAction:
    """One action from the frozen action vocabulary with a typed JSON payload."""

    action: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.action not in ACTIONS:
            raise SearchContractError(f"ACTION_UNKNOWN:{self.action}")
        try:
            frozen = freeze_json(self.payload)
        except TypeError as exc:
            raise SearchContractError("ACTION_PAYLOAD_NOT_JSON") from exc
        if not isinstance(frozen, Mapping):
            raise SearchContractError("ACTION_PAYLOAD_NOT_OBJECT")
        object.__setattr__(self, "payload", frozen)

    def to_dict(self) -> dict[str, Any]:
        return {"action": self.action, "payload": thaw_json(self.payload)}

    @property
    def canonical_key(self) -> str:
        return canonical_json(self.to_dict())


@dataclass(frozen=True)
class ObligationEvidence:
    obligation_id: str
    verdict: str
    required: bool = True

    def __post_init__(self) -> None:
        if self.verdict not in {"ZERO", "NONZERO", "UNKNOWN", "COMPILE_FAILURE"}:
            raise SearchContractError(f"VERDICT_UNKNOWN:{self.verdict}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "required": self.required,
            "verdict": self.verdict,
        }


@dataclass(frozen=True)
class SearchState:
    """Immutable partial program plus method-neutral search metadata."""

    latent_objects: tuple[LatentObject, ...] = ()
    member_assignments: tuple[MemberAssignment, ...] = ()
    operators: tuple[Operator, ...] = ()
    node_structures: tuple[NodeStructure, ...] = ()
    unexplained_members: tuple[str, ...] = ()
    compiled_obligations: tuple[Mapping[str, Any], ...] = ()
    verified_obligations: tuple[ObligationEvidence, ...] = ()
    complexity: int = 0
    score: Mapping[str, Any] | None = None
    depth: int = 0
    grammar_id: str = "G_FULL"
    parent_hash: str | None = None
    action_from_parent: LegalAction | None = None
    member_groups: tuple[tuple[str, ...], ...] = ()
    instance_maps: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    assumptions_used: tuple[str, ...] = ()
    case_fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.grammar_id not in {"G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"}:
            raise SearchContractError(f"GRAMMAR_ABLATION_UNKNOWN:{self.grammar_id}")
        if self.depth < 0 or self.complexity < 0:
            raise SearchContractError("STATE_METRIC_NEGATIVE")
        object.__setattr__(self, "instance_maps", freeze_json(self.instance_maps))
        object.__setattr__(
            self,
            "compiled_obligations",
            tuple(freeze_json(item) for item in self.compiled_obligations),
        )
        if self.score is not None:
            object.__setattr__(self, "score", freeze_json(self.score))

    def to_program(
        self,
        *,
        source_members: tuple[SourceMember, ...],
        assumption_statuses: Mapping[str, str],
    ) -> RepresentationProgram:
        obligations = tuple(
            Obligation(
                obligation_id=f"OBL_{assignment.member_id}",
                member_id=assignment.member_id,
                output=assignment.output,
                required=True,
            )
            for assignment in self.member_assignments
        )
        return RepresentationProgram(
            grammar_version=GRAMMAR_ID,
            source_members=source_members,
            latent_objects=self.latent_objects,
            node_structures=self.node_structures,
            operators=self.operators,
            member_assignments=self.member_assignments,
            assumptions_used=self.assumptions_used,
            assumption_statuses=assumption_statuses,
            obligations=obligations,
            instance_maps=self.instance_maps,
            unexplained_members=self.unexplained_members,
        )

    def scientific_payload(self) -> dict[str, Any]:
        """Return the ancestry-free payload used for duplicate identity."""
        return {
            "assumptions_used": sorted(self.assumptions_used),
            "case_fingerprint": self.case_fingerprint,
            "grammar_id": self.grammar_id,
            "instance_maps": thaw_json(self.instance_maps),
            "latent_objects": [
                item.to_dict() for item in sorted(self.latent_objects, key=lambda item: item.latent_id)
            ],
            "member_assignments": [
                item.to_dict()
                for item in sorted(self.member_assignments, key=lambda item: item.member_id)
            ],
            "member_groups": [list(sorted(item)) for item in sorted(self.member_groups)],
            "node_structures": [
                item.to_dict()
                for item in sorted(self.node_structures, key=lambda item: item.node_id)
            ],
            "operators": [
                item.to_dict() for item in sorted(self.operators, key=lambda item: item.operator_id)
            ],
            "unexplained_members": sorted(self.unexplained_members),
        }

    @property
    def canonical_hash(self) -> str:
        normalized_program = RepresentationProgram(
            grammar_version=GRAMMAR_ID,
            source_members=(),
            latent_objects=tuple(sorted(self.latent_objects, key=lambda item: item.latent_id)),
            node_structures=tuple(sorted(self.node_structures, key=lambda item: item.node_id)),
            operators=tuple(sorted(self.operators, key=lambda item: item.operator_id)),
            member_assignments=tuple(sorted(self.member_assignments, key=lambda item: item.member_id)),
            assumptions_used=tuple(sorted(self.assumptions_used)),
            assumption_statuses={item: "DECLARED" for item in self.assumptions_used},
            obligations=tuple(
                Obligation(
                    obligation_id=f"OBL_{item.member_id}",
                    member_id=item.member_id,
                    output=item.output,
                )
                for item in sorted(self.member_assignments, key=lambda item: item.member_id)
            ),
            instance_maps=self.instance_maps,
            unexplained_members=tuple(sorted(self.unexplained_members)),
        )
        identity = {
            "case_fingerprint": self.case_fingerprint,
            "grammar_id": self.grammar_id,
            "member_groups": [list(sorted(item)) for item in sorted(self.member_groups)],
            "program_hash": canonical_program_hash(normalized_program),
        }
        encoded = canonical_json(identity).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def with_metrics(self, *, complexity: int, score: Mapping[str, Any]) -> "SearchState":
        return replace(self, complexity=complexity, score=score)

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.scientific_payload(),
            "action_from_parent": (
                None if self.action_from_parent is None else self.action_from_parent.to_dict()
            ),
            "canonical_hash": self.canonical_hash,
            "compiled_obligations": [
                thaw_json(item) for item in self.compiled_obligations
            ],
            "complexity": self.complexity,
            "depth": self.depth,
            "parent_hash": self.parent_hash,
            "score": None if self.score is None else thaw_json(self.score),
            "verified_obligations": [item.to_dict() for item in self.verified_obligations],
        }
