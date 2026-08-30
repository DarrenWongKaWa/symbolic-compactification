"""Strict JSON-to-dataclass construction for Program IR."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .model import (
    LatentObject,
    MemberAssignment,
    NodeStructure,
    Obligation,
    Operator,
    RepresentationProgram,
    SourceMember,
)

_ID = re.compile(r"[A-Za-z_][A-Za-z0-9_.:-]*\Z")


class SchemaError(ValueError):
    """Stable fail-closed schema error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _object(value: Any, code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SchemaError(code)
    return value


def _array(value: Any, code: str) -> list[Any]:
    if not isinstance(value, list):
        raise SchemaError(code)
    return value


def _string(value: Any, code: str, *, identifier: bool = False) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SchemaError(code)
    if identifier and not _ID.fullmatch(value):
        raise SchemaError(code)
    return value


def _strings(value: Any, code: str) -> tuple[str, ...]:
    values = _array(value, code)
    result = tuple(_string(item, code) for item in values)
    if len(set(result)) != len(result):
        raise SchemaError(code)
    return result


def program_from_dict(
    raw: Mapping[str, Any],
    *,
    injected_source_members: tuple[SourceMember, ...] = (),
    injected_assumption_statuses: Mapping[str, str] | None = None,
    injected_obligations: tuple[Obligation, ...] = (),
) -> RepresentationProgram:
    """Build a typed program without repairing missing executable links."""
    root = _object(raw, "PROGRAM_NOT_OBJECT")
    allowed_root = {
        "assumption_statuses",
        "assumptions_used",
        "depth_note",
        "grammar_version",
        "instance_maps",
        "latent_objects",
        "member_assignments",
        "node_structures",
        "obligations",
        "operators",
        "program_id",
        "representation_depth",
        "source_members",
        "unexplained_members",
    }
    unknown_root = set(root) - allowed_root
    if unknown_root:
        raise SchemaError(f"PROGRAM_FIELD_UNKNOWN:{sorted(unknown_root)[0]}")
    grammar = _string(root.get("grammar_version"), "GRAMMAR_VERSION_MISSING")

    source_raw = root.get("source_members")
    if source_raw is None:
        source_members = injected_source_members
    else:
        parsed_sources: list[SourceMember] = []
        for value in _array(source_raw, "SOURCE_MEMBERS_INVALID"):
            item = _object(value, "SOURCE_MEMBER_INVALID")
            if set(item) != {"member_id", "path", "sha256"}:
                raise SchemaError("SOURCE_MEMBER_FIELDS_INVALID")
            parsed_sources.append(SourceMember(
                member_id=_string(item.get("member_id"), "SOURCE_MEMBER_ID_INVALID", identifier=True),
                path=_string(item.get("path"), "SOURCE_MEMBER_PATH_INVALID"),
                sha256=_string(item.get("sha256"), "SOURCE_MEMBER_HASH_INVALID"),
            ))
        source_members = tuple(parsed_sources)

    latents: list[LatentObject] = []
    for item_value in _array(root.get("latent_objects"), "LATENT_OBJECTS_MISSING"):
        item = _object(item_value, "LATENT_OBJECT_INVALID")
        if set(item) != {"expression", "form", "latent_id", "parameters"}:
            raise SchemaError("LATENT_FIELDS_INVALID")
        latents.append(LatentObject(
            latent_id=_string(item.get("latent_id"), "LATENT_ID_INVALID", identifier=True),
            form=_string(item.get("form"), "LATENT_FORM_INVALID", identifier=True),
            parameters=_strings(item.get("parameters"), "LATENT_PARAMETERS_INVALID"),
            expression=_string(item.get("expression"), "LATENT_EXPRESSION_INVALID"),
        ))

    nodes: list[NodeStructure] = []
    for item_value in _array(root.get("node_structures", []), "NODE_STRUCTURES_INVALID"):
        item = _object(item_value, "NODE_STRUCTURE_INVALID")
        if set(item) != {"node_id", "nodes"}:
            raise SchemaError("NODE_FIELDS_INVALID")
        node_values = _array(item.get("nodes"), "NODE_VALUES_INVALID")
        if not node_values:
            raise SchemaError("NODE_VALUES_INVALID")
        nodes.append(NodeStructure(
            node_id=_string(item.get("node_id"), "NODE_ID_INVALID", identifier=True),
            nodes=tuple(_string(node, "NODE_VALUE_INVALID") for node in node_values),
        ))

    operators: list[Operator] = []
    for item_value in _array(root.get("operators"), "OPERATORS_MISSING"):
        item = _object(item_value, "OPERATOR_INVALID")
        if set(item) - {"arguments", "inputs", "latent_id", "operator", "operator_id", "output"}:
            raise SchemaError("OPERATOR_FIELDS_INVALID")
        output = item.get("output")
        operators.append(Operator(
            operator_id=_string(item.get("operator_id"), "OPERATOR_ID_INVALID", identifier=True),
            operator=_string(item.get("operator"), "OPERATOR_KIND_INVALID", identifier=True),
            output=None if output is None else _string(output, "OPERATOR_OUTPUT_INVALID", identifier=True),
            latent_id=None if item.get("latent_id") is None else _string(item.get("latent_id"), "OPERATOR_LATENT_INVALID", identifier=True),
            inputs=_strings(item.get("inputs", []), "OPERATOR_INPUTS_INVALID"),
            arguments=_object(item.get("arguments", {}), "OPERATOR_ARGUMENTS_INVALID"),
        ))

    assignments: list[MemberAssignment] = []
    assignment_raw = root.get("member_assignments")
    if isinstance(assignment_raw, Mapping):
        iterator = []
        for member_id, value in assignment_raw.items():
            item = dict(_object(value, "MEMBER_ASSIGNMENT_INVALID"))
            item["member_id"] = member_id
            iterator.append(item)
    else:
        iterator = _array(assignment_raw, "MEMBER_ASSIGNMENTS_MISSING")
    for item_value in iterator:
        item = _object(item_value, "MEMBER_ASSIGNMENT_INVALID")
        if set(item) - {"member_id", "operator_ids", "output", "reconstruction_path"}:
            raise SchemaError("MEMBER_ASSIGNMENT_FIELDS_INVALID")
        output = item.get("output")
        reconstruction = item.get("reconstruction_path")
        assignments.append(MemberAssignment(
            member_id=_string(item.get("member_id"), "MEMBER_ASSIGNMENT_ID_INVALID", identifier=True),
            output=None if output is None else _string(output, "MEMBER_ASSIGNMENT_OUTPUT_INVALID", identifier=True),
            operator_ids=_strings(item.get("operator_ids", []), "MEMBER_ASSIGNMENT_OPERATORS_INVALID"),
            reconstruction_path=None if reconstruction is None else _string(reconstruction, "RECONSTRUCTION_PATH_INVALID"),
        ))

    raw_obligations = root.get("obligations", [])
    obligations: tuple[Obligation, ...]
    if raw_obligations and all(isinstance(item, Mapping) for item in raw_obligations):
        parsed: list[Obligation] = []
        for item_value in raw_obligations:
            item = _object(item_value, "OBLIGATION_INVALID")
            if set(item) - {"member_id", "obligation_id", "output", "required"}:
                raise SchemaError("OBLIGATION_FIELDS_INVALID")
            member_id = item.get("member_id")
            output = item.get("output")
            required = item.get("required", True)
            if not isinstance(required, bool):
                raise SchemaError("OBLIGATION_REQUIRED_INVALID")
            parsed.append(Obligation(
                obligation_id=_string(item.get("obligation_id"), "OBLIGATION_ID_INVALID", identifier=True),
                member_id=None if member_id is None else _string(member_id, "OBLIGATION_MEMBER_INVALID", identifier=True),
                output=None if output is None else _string(output, "OBLIGATION_OUTPUT_INVALID", identifier=True),
                required=required,
            ))
        obligations = tuple(parsed)
    elif raw_obligations and all(isinstance(item, str) for item in raw_obligations):
        # Exact evaluator-side member links may be injected by the package
        # loader.  Missing output links are retained as None, never inferred
        # from operator order or reconstruction filenames.
        injected_by_id = {item.obligation_id: item for item in injected_obligations}
        obligations = tuple(
            injected_by_id.get(
                item,
                Obligation(obligation_id=item, member_id=None, output=None),
            )
            for item in raw_obligations
        )
    else:
        obligations = injected_obligations

    statuses = root.get("assumption_statuses", injected_assumption_statuses or {})
    statuses = _object(statuses, "ASSUMPTION_STATUSES_INVALID")
    representation_depth = root.get("representation_depth")
    if representation_depth is not None and not isinstance(representation_depth, str):
        raise SchemaError("REPRESENTATION_DEPTH_INVALID")
    declared_program_id = root.get("program_id")
    if declared_program_id is not None and not isinstance(declared_program_id, str):
        raise SchemaError("PROGRAM_ID_INVALID")
    return RepresentationProgram(
        grammar_version=grammar,
        source_members=tuple(source_members),
        latent_objects=tuple(latents),
        node_structures=tuple(nodes),
        operators=tuple(operators),
        member_assignments=tuple(assignments),
        assumptions_used=_strings(root.get("assumptions_used", []), "ASSUMPTIONS_USED_INVALID"),
        assumption_statuses={str(key): _string(value, "ASSUMPTION_STATUS_INVALID") for key, value in statuses.items()},
        obligations=obligations,
        instance_maps=_object(root.get("instance_maps", {}), "INSTANCE_MAPS_INVALID"),
        unexplained_members=_strings(root.get("unexplained_members", []), "UNEXPLAINED_MEMBERS_INVALID"),
        representation_depth=representation_depth,
        declared_program_id=declared_program_id,
    )
