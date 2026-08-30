"""Immutable data model for executable representation programs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


def freeze_json(value: Any) -> Any:
    """Recursively freeze a JSON-native value.

    Mapping keys are ordered so construction from differently ordered JSON
    produces the same in-memory representation and canonical serialization.
    """
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): freeze_json(value[key]) for key in sorted(value)}
        )
    if isinstance(value, (list, tuple)):
        return tuple(freeze_json(item) for item in value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"NON_JSON_VALUE:{type(value).__name__}")


def thaw_json(value: Any) -> Any:
    """Return a JSON-native copy of a recursively frozen value."""
    if isinstance(value, Mapping):
        return {key: thaw_json(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(child) for child in value]
    return value


@dataclass(frozen=True)
class SourceMember:
    member_id: str
    path: str
    sha256: str

    def to_dict(self) -> dict[str, str]:
        return {
            "member_id": self.member_id,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class LatentObject:
    latent_id: str
    form: str
    parameters: tuple[str, ...]
    expression: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "expression": self.expression,
            "form": self.form,
            "latent_id": self.latent_id,
            "parameters": list(self.parameters),
        }


@dataclass(frozen=True)
class NodeStructure:
    node_id: str
    nodes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "nodes": list(self.nodes)}


@dataclass(frozen=True)
class Operator:
    operator_id: str
    operator: str
    output: str | None
    latent_id: str | None = None
    inputs: tuple[str, ...] = ()
    arguments: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", freeze_json(self.arguments))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "arguments": thaw_json(self.arguments),
            "inputs": list(self.inputs),
            "operator": self.operator,
            "operator_id": self.operator_id,
            "output": self.output,
        }
        if self.latent_id is not None:
            payload["latent_id"] = self.latent_id
        return payload


@dataclass(frozen=True)
class MemberAssignment:
    member_id: str
    output: str | None
    operator_ids: tuple[str, ...] = ()
    reconstruction_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "member_id": self.member_id,
            "operator_ids": list(self.operator_ids),
            "output": self.output,
        }
        if self.reconstruction_path is not None:
            payload["reconstruction_path"] = self.reconstruction_path
        return payload


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    member_id: str | None
    output: str | None
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "member_id": self.member_id,
            "obligation_id": self.obligation_id,
            "output": self.output,
            "required": self.required,
        }


@dataclass(frozen=True)
class RepresentationProgram:
    grammar_version: str
    source_members: tuple[SourceMember, ...]
    latent_objects: tuple[LatentObject, ...]
    node_structures: tuple[NodeStructure, ...]
    operators: tuple[Operator, ...]
    member_assignments: tuple[MemberAssignment, ...]
    assumptions_used: tuple[str, ...]
    assumption_statuses: Mapping[str, str]
    obligations: tuple[Obligation, ...]
    instance_maps: Mapping[str, Any] = field(
        default_factory=lambda: MappingProxyType({})
    )
    unexplained_members: tuple[str, ...] = ()
    representation_depth: str | None = None
    declared_program_id: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumption_statuses", freeze_json(
            self.assumption_statuses
        ))
        object.__setattr__(self, "instance_maps", freeze_json(self.instance_maps))

    def to_dict(self, *, include_program_id: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "assumption_statuses": thaw_json(self.assumption_statuses),
            "assumptions_used": list(self.assumptions_used),
            "grammar_version": self.grammar_version,
            "instance_maps": thaw_json(self.instance_maps),
            "latent_objects": [item.to_dict() for item in self.latent_objects],
            "member_assignments": [
                item.to_dict() for item in self.member_assignments
            ],
            "node_structures": [item.to_dict() for item in self.node_structures],
            "obligations": [item.to_dict() for item in self.obligations],
            "operators": [item.to_dict() for item in self.operators],
            "source_members": [item.to_dict() for item in self.source_members],
            "unexplained_members": list(self.unexplained_members),
        }
        if self.representation_depth is not None:
            payload["representation_depth"] = self.representation_depth
        if include_program_id:
            from .canonical import canonical_program_hash

            payload["program_id"] = canonical_program_hash(self)
        return payload


@dataclass(frozen=True)
class CompileContext:
    package_root: Path
    symbols: tuple[Any, ...]
    functions: tuple[str, ...] = ()
    grammar_id: str = "G_FULL"


@dataclass(frozen=True)
class CompiledObligation:
    obligation_id: str
    member_id: str
    current_path: str
    current_sha256: str
    current_expression: str
    candidate_expression: str
    required: bool
    status: str = "COMPILED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_expression": self.candidate_expression,
            "current_expression": self.current_expression,
            "current_path": self.current_path,
            "current_sha256": self.current_sha256,
            "member_id": self.member_id,
            "obligation_id": self.obligation_id,
            "required": self.required,
            "status": self.status,
        }


@dataclass(frozen=True)
class CompilationResult:
    status: str
    program_id: str
    obligations: tuple[CompiledObligation, ...] = ()
    failure_codes: tuple[str, ...] = ()
    tautological: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "failure_codes": list(self.failure_codes),
            "obligations": [item.to_dict() for item in self.obligations],
            "program_id": self.program_id,
            "status": self.status,
            "tautological": self.tautological,
        }
