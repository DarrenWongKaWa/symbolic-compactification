"""Frozen legal-child generation and typed state transitions."""
from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass, replace
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.grammar_v1 import G_PRIMITIVE_OPS
from research.representation_program_search.program_ir import (
    LatentObject,
    MemberAssignment,
    NodeStructure,
    Operator,
    canonical_json,
    compile_program,
)
from research.representation_program_search.program_ir.model import thaw_json

from .candidates import CandidatePool, LatentCandidate
from .model import LegalAction, SearchContractError, SearchState
from .public_case import PublicCase
from .scoring import complexity_breakdown, score_program

SEARCH_POLICY_VERSION = "RPSSearchPolicyV1"

_ACTION_OPERATOR = {
    "SUBSTITUTE_PARAMETER": "SUBSTITUTE",
    "ADD_DERIVATIVE": "DERIVATIVE",
    "ADD_NEWTON_DD": "NEWTON_DD",
    "ADD_HERMITE_DD": "HERMITE_DD",
    "ADD_RECURRENCE": "RECURRENCE",
    "ADD_PERMUTATION": "PERMUTE",
    "ADD_LINEAR_COMBINATION": "LINEAR_COMBINATION",
    "ADD_COMPOSE": "COMPOSE",
    "RECONSTRUCT_FROM_BASIS": "BASIS_RECONSTRUCT",
}


@dataclass(frozen=True)
class SearchPolicy:
    version: str = SEARCH_POLICY_VERSION
    max_complexity: int = 24
    max_latents: int = 2
    max_operators: int = 4
    max_node_structures: int = 1
    max_member_groups: int = 1
    max_parameters_per_latent: int = 2
    latent_creation_enabled: bool = True

    def __post_init__(self) -> None:
        if self.version != SEARCH_POLICY_VERSION:
            raise SearchContractError(f"SEARCH_POLICY_UNKNOWN:{self.version}")
        for name in (
            "max_complexity", "max_latents", "max_operators",
            "max_node_structures", "max_member_groups", "max_parameters_per_latent",
        ):
            if getattr(self, name) < 0:
                raise SearchContractError(f"SEARCH_POLICY_INVALID:{name}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "latent_creation_enabled": self.latent_creation_enabled,
            "max_complexity": self.max_complexity,
            "max_latents": self.max_latents,
            "max_member_groups": self.max_member_groups,
            "max_node_structures": self.max_node_structures,
            "max_operators": self.max_operators,
            "max_parameters_per_latent": self.max_parameters_per_latent,
            "version": self.version,
        }


@dataclass(frozen=True)
class FrontierExpansion:
    children: tuple[SearchState, ...]
    actions: tuple[LegalAction, ...]
    rejected: Mapping[str, int]
    branching_incomplete: bool = True
    incompleteness_reason: str = "FROZEN_FINITE_CANDIDATE_POOL"


def initial_state(case: PublicCase, *, grammar_id: str) -> SearchState:
    state = SearchState(
        unexplained_members=tuple(sorted(item.member_id for item in case.members)),
        grammar_id=grammar_id,
        case_fingerprint=case.proposer_view_sha256,
        assumptions_used=tuple(sorted(case.assumption_statuses)),
    )
    return _finalize(state, case)


def _token(prefix: str, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _payload(action: LegalAction, *, exact: set[str]) -> dict[str, Any]:
    value = thaw_json(action.payload)
    if set(value) != exact:
        raise SearchContractError(f"ACTION_PAYLOAD_FIELDS_INVALID:{action.action}")
    return value


def _latent(state: SearchState, latent_id: Any) -> LatentObject:
    if not isinstance(latent_id, str):
        raise SearchContractError("ACTION_LATENT_ID_INVALID")
    for item in state.latent_objects:
        if item.latent_id == latent_id:
            return item
    raise SearchContractError(f"ACTION_LATENT_UNKNOWN:{latent_id}")


def _output_ids(state: SearchState) -> set[str]:
    return {item.output for item in state.operators if item.output is not None}


def _dependency_ids(state: SearchState, output: str) -> tuple[str, ...]:
    by_output = {item.output: item for item in state.operators if item.output is not None}
    result: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        operator = by_output.get(name)
        if operator is None or operator.operator_id in seen:
            return
        for child in operator.inputs:
            visit(child)
        seen.add(operator.operator_id)
        result.append(operator.operator_id)

    visit(output)
    return tuple(result)


def _append_operator(
    state: SearchState,
    *,
    operator: str,
    latent_id: str,
    inputs: tuple[str, ...] = (),
    arguments: Mapping[str, Any],
) -> tuple[Operator, ...]:
    if any(value not in _output_ids(state) for value in inputs):
        raise SearchContractError("ACTION_OPERATOR_INPUT_UNKNOWN")
    signature = {
        "arguments": arguments,
        "inputs": list(inputs),
        "latent_id": latent_id,
        "operator": operator,
    }
    operator_id = _token("OP", signature)
    output = _token("out", signature)
    if any(item.operator_id == operator_id or item.output == output for item in state.operators):
        raise SearchContractError("ACTION_DUPLICATE_OPERATOR")
    return state.operators + (Operator(
        operator_id=operator_id,
        operator=operator,
        output=output,
        latent_id=latent_id,
        inputs=inputs,
        arguments=arguments,
    ),)


def _allowed_operator(grammar_id: str, operator: str) -> bool:
    if grammar_id == "G_FULL":
        return True
    if grammar_id == "G_NO_HERMITE":
        return operator != "HERMITE_DD"
    return operator in G_PRIMITIVE_OPS


def _finalize(state: SearchState, case: PublicCase) -> SearchState:
    compiled: tuple[Mapping[str, Any], ...] = ()
    compile_status: str | None = None
    tautological = False
    program = state.to_program(
        source_members=case.source_members,
        assumption_statuses=case.assumption_statuses,
    )
    if state.member_assignments:
        result = compile_program(program, case.compile_context(state.grammar_id))
        compile_status = result.status
        tautological = result.tautological is True
        if result.status == "COMPILED":
            compiled = tuple(item.to_dict() for item in result.obligations)
        else:
            compiled = ({
                "failure_codes": list(result.failure_codes),
                "status": "COMPILE_FAILURE",
            },)
    complexity = complexity_breakdown(program).total
    score = score_program(
        program,
        state.verified_obligations,
        tautological=tautological,
        compile_status=compile_status,
    )
    return replace(
        state,
        compiled_obligations=compiled,
        complexity=complexity,
        score=score,
    )


def apply_action(state: SearchState, action: LegalAction, case: PublicCase) -> SearchState:
    """Apply one legal typed action; never repair an illegal payload."""
    base = replace(
        state,
        compiled_obligations=(),
        score=None,
        depth=state.depth + 1,
        parent_hash=state.canonical_hash,
        action_from_parent=action,
    )
    kind = action.action
    if kind in {"CREATE_LATENT", "CREATE_BASIS"}:
        values = _payload(action, exact={"candidate_id", "expression", "form", "parameters"})
        if kind == "CREATE_BASIS" and state.grammar_id == "G_PRIMITIVE":
            raise SearchContractError("ACTION_FORBIDDEN_BY_ABLATION:CREATE_BASIS")
        if not all(isinstance(values[key], str) and values[key] for key in ("candidate_id", "expression", "form")):
            raise SearchContractError("ACTION_LATENT_INVALID")
        if not isinstance(values["parameters"], list) or not all(
            isinstance(item, str) for item in values["parameters"]
        ):
            raise SearchContractError("ACTION_LATENT_PARAMETERS_INVALID")
        form = "BASIS_OBJECT" if kind == "CREATE_BASIS" else values["form"]
        latent_id = f"F_{values['candidate_id']}"
        if any(item.latent_id == latent_id for item in state.latent_objects):
            raise SearchContractError("ACTION_DUPLICATE_LATENT")
        base = replace(base, latent_objects=state.latent_objects + (LatentObject(
            latent_id=latent_id,
            form=form,
            parameters=tuple(values["parameters"]),
            expression=values["expression"],
        ),))
    elif kind == "ADD_PARAMETER":
        values = _payload(action, exact={"latent_id", "parameter"})
        latent = _latent(state, values["latent_id"])
        parameter = values["parameter"]
        if not isinstance(parameter, str) or parameter in latent.parameters:
            raise SearchContractError("ACTION_PARAMETER_INVALID")
        base = replace(base, latent_objects=tuple(
            replace(item, parameters=item.parameters + (parameter,))
            if item.latent_id == latent.latent_id else item
            for item in state.latent_objects
        ))
    elif kind == "GROUP_MEMBERS":
        values = _payload(action, exact={"member_ids"})
        if not isinstance(values["member_ids"], list) or not all(
            isinstance(item, str) for item in values["member_ids"]
        ):
            raise SearchContractError("ACTION_MEMBER_GROUP_INVALID")
        group = tuple(values["member_ids"])
        known = {item.member_id for item in case.members}
        if len(group) < 2 or len(set(group)) != len(group) or not set(group) <= known:
            raise SearchContractError("ACTION_MEMBER_GROUP_INVALID")
        group = tuple(sorted(group))
        if group in state.member_groups:
            raise SearchContractError("ACTION_DUPLICATE_MEMBER_GROUP")
        base = replace(base, member_groups=state.member_groups + (group,))
    elif kind == "ADD_REPEATED_NODE":
        values = _payload(action, exact={"nodes"})
        if state.grammar_id == "G_PRIMITIVE":
            raise SearchContractError("ACTION_FORBIDDEN_BY_ABLATION:ADD_REPEATED_NODE")
        if not isinstance(values["nodes"], list) or not all(
            isinstance(item, str) and item for item in values["nodes"]
        ):
            raise SearchContractError("ACTION_REPEATED_NODE_INVALID")
        nodes = tuple(values["nodes"])
        if len(nodes) < 2 or len(set(nodes)) == len(nodes):
            raise SearchContractError("ACTION_REPEATED_NODE_INVALID")
        node_id = _token("N", {"nodes": list(nodes)})
        if any(item.node_id == node_id for item in state.node_structures):
            raise SearchContractError("ACTION_DUPLICATE_NODE")
        base = replace(base, node_structures=state.node_structures + (NodeStructure(node_id, nodes),))
    elif kind == "ADD_MEMBER":
        values = thaw_json(action.payload)
        if set(values) == {"member_id", "output"}:
            member_id, output = values["member_id"], values["output"]
            operators = state.operators
        elif set(values) == {"latent_id", "member_id", "values"}:
            member_id = values["member_id"]
            latent = _latent(state, values["latent_id"])
            if latent.form not in {"FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION", "FUNCTION_2"}:
                raise SearchContractError("ACTION_VALUE_LATENT_INVALID")
            if not isinstance(values["values"], Mapping) or set(values["values"]) != set(latent.parameters):
                raise SearchContractError("ACTION_VALUE_ARGUMENTS_INVALID")
            arguments = (
                {"node": values["values"][latent.parameters[0]]}
                if len(latent.parameters) == 1
                else {"values": values["values"]}
            )
            operators = _append_operator(
                state,
                operator="VALUE",
                latent_id=latent.latent_id,
                arguments=arguments,
            )
            output = operators[-1].output
            instance_maps = thaw_json(state.instance_maps)
            instance_maps.setdefault(member_id, {})[latent.latent_id] = dict(values["values"])
        else:
            raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:ADD_MEMBER")
        if not isinstance(member_id, str) or not isinstance(output, str) or member_id not in state.unexplained_members or output not in {
            item.output for item in operators
        }:
            raise SearchContractError("ACTION_MEMBER_ASSIGNMENT_INVALID")
        interim = replace(state, operators=operators)
        assignment = MemberAssignment(member_id, output, _dependency_ids(interim, output))
        base = replace(
            base,
            operators=operators,
            member_assignments=state.member_assignments + (assignment,),
            unexplained_members=tuple(
                item for item in state.unexplained_members if item != member_id
            ),
            instance_maps=(
                instance_maps
                if set(values) == {"latent_id", "member_id", "values"}
                else state.instance_maps
            ),
        )
    elif kind == "ADD_NEWTON_DD":
        values = _payload(action, exact={"latent_id", "nodes"})
        if not _allowed_operator(state.grammar_id, "NEWTON_DD"):
            raise SearchContractError("ACTION_FORBIDDEN_BY_ABLATION:ADD_NEWTON_DD")
        latent = _latent(state, values["latent_id"])
        if not isinstance(values["nodes"], list) or not all(
            isinstance(item, str) and item for item in values["nodes"]
        ):
            raise SearchContractError("ACTION_NEWTON_NODES_INVALID")
        nodes = tuple(values["nodes"])
        if (
            latent.form not in {"FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION"}
            or len(nodes) < 2
            or len(set(nodes)) != len(nodes)
            or len(latent.parameters) != 1
        ):
            raise SearchContractError("ACTION_NEWTON_NODES_INVALID")
        node_id = _token("N", {"nodes": list(nodes)})
        structures = state.node_structures
        if not any(item.node_id == node_id for item in structures):
            structures += (NodeStructure(node_id, nodes),)
        state_with_node = replace(state, node_structures=structures)
        base = replace(
            base,
            node_structures=structures,
            operators=_append_operator(
                state_with_node,
                operator="NEWTON_DD",
                latent_id=latent.latent_id,
                arguments={"nodes": node_id},
            ),
        )
    elif kind == "ADD_HERMITE_DD":
        values = _payload(action, exact={"latent_id", "node_id"})
        if not _allowed_operator(state.grammar_id, "HERMITE_DD"):
            raise SearchContractError("ACTION_FORBIDDEN_BY_ABLATION:ADD_HERMITE_DD")
        latent = _latent(state, values["latent_id"])
        node = next((item for item in state.node_structures if item.node_id == values["node_id"]), None)
        grouped = True
        if node is not None:
            seen: set[str] = set()
            previous: str | None = None
            for label in node.nodes:
                if label != previous and label in seen:
                    grouped = False
                seen.add(label)
                previous = label
        if (
            latent.form not in {"FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION"}
            or node is None
            or len(set(node.nodes)) == len(node.nodes)
            or not grouped
            or len(latent.parameters) != 1
        ):
            raise SearchContractError("ACTION_HERMITE_NODE_INVALID")
        base = replace(base, operators=_append_operator(
            state,
            operator="HERMITE_DD",
            latent_id=latent.latent_id,
            arguments={"nodes": node.node_id},
        ))
    elif kind in _ACTION_OPERATOR:
        values = thaw_json(action.payload)
        operator = _ACTION_OPERATOR[kind]
        if not _allowed_operator(state.grammar_id, operator):
            raise SearchContractError(f"ACTION_FORBIDDEN_BY_ABLATION:{kind}")
        if kind == "SUBSTITUTE_PARAMETER":
            if set(values) != {"input", "latent_id", "parameter", "value"}:
                raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:SUBSTITUTE_PARAMETER")
            inputs = () if values["input"] is None else (values["input"],)
            arguments = {"parameter": values["parameter"], "value": values["value"]}
        elif kind == "ADD_DERIVATIVE":
            if set(values) != {"input", "latent_id", "order", "variable"}:
                raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:ADD_DERIVATIVE")
            inputs = () if values["input"] is None else (values["input"],)
            arguments = {"order": values["order"], "variable": values["variable"]}
        elif kind == "ADD_RECURRENCE":
            if set(values) != {"base", "form", "input", "latent_id", "parameter", "step"}:
                raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:ADD_RECURRENCE")
            inputs = () if values["input"] is None else (values["input"],)
            arguments = {key: values[key] for key in ("base", "form", "parameter", "step")}
        elif kind == "ADD_PERMUTATION":
            if set(values) != {"input", "latent_id", "mapping"}:
                raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:ADD_PERMUTATION")
            inputs = (values["input"],)
            arguments = {"mapping": values["mapping"]}
        elif kind == "ADD_COMPOSE":
            if set(values) != {"inputs", "latent_id"}:
                raise SearchContractError("ACTION_PAYLOAD_FIELDS_INVALID:ADD_COMPOSE")
            if not isinstance(values["inputs"], list) or not all(
                isinstance(item, str) for item in values["inputs"]
            ):
                raise SearchContractError("ACTION_COMPOSE_INPUTS_INVALID")
            inputs = tuple(values["inputs"])
            arguments = {}
        else:
            if set(values) != {"coefficients", "inputs", "latent_id"}:
                raise SearchContractError(f"ACTION_PAYLOAD_FIELDS_INVALID:{kind}")
            if (
                not isinstance(values["inputs"], list)
                or not isinstance(values["coefficients"], list)
                or not all(isinstance(item, str) for item in values["inputs"])
                or not all(isinstance(item, str) for item in values["coefficients"])
            ):
                raise SearchContractError(f"ACTION_ARGUMENTS_INVALID:{kind}")
            inputs = tuple(values["inputs"])
            arguments = {"coefficients": values["coefficients"]}
        _latent(state, values["latent_id"])
        base = replace(base, operators=_append_operator(
            state,
            operator=operator,
            latent_id=values["latent_id"],
            inputs=inputs,
            arguments=arguments,
        ))
    elif kind == "REMOVE_REDUNDANT_OBJECT":
        values = _payload(action, exact={"id", "object_type"})
        identifier, object_type = values["id"], values["object_type"]
        if object_type == "LATENT":
            if any(item.latent_id == identifier for item in state.operators):
                raise SearchContractError("ACTION_OBJECT_NOT_REDUNDANT")
            base = replace(base, latent_objects=tuple(
                item for item in state.latent_objects if item.latent_id != identifier
            ))
        elif object_type == "NODE":
            if any(item.arguments.get("nodes") == identifier for item in state.operators):
                raise SearchContractError("ACTION_OBJECT_NOT_REDUNDANT")
            base = replace(base, node_structures=tuple(
                item for item in state.node_structures if item.node_id != identifier
            ))
        elif object_type == "OPERATOR":
            target = next((item for item in state.operators if item.operator_id == identifier), None)
            if target is None or any(
                target.output in item.inputs for item in state.operators
            ) or any(target.output == item.output for item in state.member_assignments):
                raise SearchContractError("ACTION_OBJECT_NOT_REDUNDANT")
            base = replace(base, operators=tuple(
                item for item in state.operators if item.operator_id != identifier
            ))
        else:
            raise SearchContractError("ACTION_OBJECT_TYPE_INVALID")
    else:
        raise SearchContractError(f"ACTION_NOT_IMPLEMENTED:{kind}")
    return _finalize(base, case)


def _latent_action(candidate: LatentCandidate, action: str = "CREATE_LATENT") -> LegalAction:
    return LegalAction(action, {
        "candidate_id": candidate.candidate_id,
        "expression": candidate.expression,
        "form": candidate.form,
        "parameters": list(candidate.parameters),
    })


def _candidate_for_latent(pool: CandidatePool, latent: LatentObject) -> LatentCandidate | None:
    candidate_id = latent.latent_id.removeprefix("F_")
    return next((item for item in pool.latents if item.candidate_id == candidate_id), None)


def legal_actions(
    state: SearchState,
    case: PublicCase,
    pool: CandidatePool,
    policy: SearchPolicy,
) -> tuple[LegalAction, ...]:
    """Return every child in the frozen generated frontier for this state."""
    result: list[LegalAction] = []
    primitive = state.grammar_id == "G_PRIMITIVE"
    if policy.latent_creation_enabled and len(state.latent_objects) < policy.max_latents:
        existing = {item.latent_id for item in state.latent_objects}
        for candidate in pool.latents:
            if f"F_{candidate.candidate_id}" not in existing:
                result.append(_latent_action(candidate))
                if (
                    not primitive
                    and candidate.extraction != "SOURCE_LITERAL"
                    and candidate.form in {"FUNCTION_1", "FUNCTION_2"}
                ):
                    result.append(_latent_action(candidate, "CREATE_BASIS"))

    known_members = set(state.unexplained_members)
    outputs = tuple(item.output for item in state.operators if item.output is not None)
    output_operators = {
        item.output: item for item in state.operators if item.output is not None
    }
    composition_outputs = tuple(
        output
        for output in outputs
        if (
            (candidate := _candidate_for_latent(
                pool, _latent(state, output_operators[output].latent_id)
            )) is None
            or candidate.extraction != "SOURCE_LITERAL"
        )
    )[:3]
    for output in outputs:
        owner = output_operators[output]
        owner_latent = _latent(state, owner.latent_id)
        owner_candidate = _candidate_for_latent(pool, owner_latent)
        for member_id in sorted(known_members):
            if (
                owner_candidate is not None
                and owner_candidate.extraction == "SOURCE_LITERAL"
                and member_id not in owner_candidate.public_origins
            ):
                continue
            result.append(LegalAction("ADD_MEMBER", {"member_id": member_id, "output": output}))
    for latent in state.latent_objects:
        candidate = _candidate_for_latent(pool, latent)
        if candidate is not None and len(state.operators) < policy.max_operators:
            for member_id, values in candidate.instance_maps:
                if member_id in known_members and set(dict(values)) == set(latent.parameters):
                    result.append(LegalAction("ADD_MEMBER", {
                        "latent_id": latent.latent_id,
                        "member_id": member_id,
                        "values": dict(values),
                    }))
        control_only = candidate is not None and candidate.extraction == "SOURCE_LITERAL"
        if not control_only and len(latent.parameters) < policy.max_parameters_per_latent:
            parameter = f"rps_p{len(latent.parameters)}"
            if parameter not in latent.parameters:
                result.append(LegalAction("ADD_PARAMETER", {
                    "latent_id": latent.latent_id,
                    "parameter": parameter,
                }))

    if state.member_assignments and len(state.member_groups) < policy.max_member_groups:
        all_member_ids = sorted(item.member_id for item in case.members)
        for pair in itertools.combinations(all_member_ids, 2):
            result.append(LegalAction("GROUP_MEMBERS", {"member_ids": list(pair)}))

    if len(state.operators) < policy.max_operators:
        for latent in state.latent_objects:
            source_candidate = _candidate_for_latent(pool, latent)
            if source_candidate is not None and source_candidate.extraction == "SOURCE_LITERAL":
                continue
            unary = len(latent.parameters) == 1 and latent.form in {
                "FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION"
            }
            parameter = latent.parameters[0] if latent.parameters else None
            compatible_outputs = tuple(
                item.output for item in state.operators
                if item.latent_id == latent.latent_id and item.output is not None
            )
            for input_value in (None, *compatible_outputs[:2]):
                if parameter is not None:
                    for node in pool.node_values[:4]:
                        result.append(LegalAction("SUBSTITUTE_PARAMETER", {
                            "input": input_value,
                            "latent_id": latent.latent_id,
                            "parameter": parameter,
                            "value": node,
                        }))
                    result.append(LegalAction("ADD_DERIVATIVE", {
                        "input": input_value,
                        "latent_id": latent.latent_id,
                        "order": 1,
                        "variable": parameter,
                    }))
            if not primitive and unary:
                for left, right in itertools.combinations(pool.node_values[:4], 2):
                    node_id = _token("N", {"nodes": [left, right]})
                    if (
                        any(item.node_id == node_id for item in state.node_structures)
                        or len(state.node_structures) < policy.max_node_structures
                    ):
                        result.append(LegalAction("ADD_NEWTON_DD", {
                            "latent_id": latent.latent_id,
                            "nodes": [left, right],
                        }))
                for base in pool.node_values[:3]:
                    result.append(LegalAction("ADD_RECURRENCE", {
                        "base": base,
                        "form": "FORWARD_DIFFERENCE",
                        "input": None,
                        "latent_id": latent.latent_id,
                        "parameter": parameter,
                        "step": "1",
                    }))
                for node in state.node_structures:
                    if len(set(node.nodes)) < len(node.nodes) and state.grammar_id == "G_FULL":
                        result.append(LegalAction("ADD_HERMITE_DD", {
                            "latent_id": latent.latent_id,
                            "node_id": node.node_id,
                        }))
            for input_value in compatible_outputs[:2]:
                if not primitive and len(pool.node_values) >= 2:
                    left, right = pool.node_values[:2]
                    result.append(LegalAction("ADD_PERMUTATION", {
                        "input": input_value,
                        "latent_id": latent.latent_id,
                        "mapping": {left: right, right: left},
                    }))
            if latent.parameters and composition_outputs:
                for inputs in itertools.product(
                    composition_outputs, repeat=len(latent.parameters)
                ):
                    result.append(LegalAction("ADD_COMPOSE", {
                        "inputs": list(inputs),
                        "latent_id": latent.latent_id,
                    }))

        has_unary_latent = any(
            len(item.parameters) == 1
            and item.form in {"FUNCTION_1", "SCALAR_KERNEL", "MATRIX_FUNCTION"}
            for item in state.latent_objects
        )
        if (
            not primitive
            and has_unary_latent
            and len(state.node_structures) < policy.max_node_structures
        ):
            for node in pool.node_values[:3]:
                result.append(LegalAction("ADD_REPEATED_NODE", {"nodes": [node, node]}))
            for left, right in itertools.combinations(pool.node_values[:3], 2):
                result.append(LegalAction("ADD_REPEATED_NODE", {
                    "nodes": [left, left, right],
                }))

        synthesis_latents = tuple(
            item
            for item in state.latent_objects
            if (
                (candidate := _candidate_for_latent(pool, item)) is None
                or candidate.extraction != "SOURCE_LITERAL"
            )
        )
        synthesis_outputs = tuple(
            output
            for output in outputs
            if (
                (candidate := _candidate_for_latent(
                    pool, _latent(state, output_operators[output].latent_id)
                )) is None
                or candidate.extraction != "SOURCE_LITERAL"
            )
        )
        if len(synthesis_outputs) >= 2 and synthesis_latents:
            for first, second in itertools.combinations(synthesis_outputs[:4], 2):
                for coefficients in (("1", "1"), ("1", "-1")):
                    result.append(LegalAction("ADD_LINEAR_COMBINATION", {
                        "coefficients": list(coefficients),
                        "inputs": [first, second],
                        "latent_id": synthesis_latents[0].latent_id,
                    }))
                if not primitive and any(
                    item.form == "BASIS_OBJECT" for item in state.latent_objects
                ):
                    result.append(LegalAction("RECONSTRUCT_FROM_BASIS", {
                        "coefficients": ["1", "1"],
                        "inputs": [first, second],
                        "latent_id": synthesis_latents[0].latent_id,
                    }))

    return tuple(sorted({item.canonical_key: item for item in result}.values(), key=lambda item: item.canonical_key))


def expand_state(
    state: SearchState,
    case: PublicCase,
    pool: CandidatePool,
    policy: SearchPolicy,
) -> FrontierExpansion:
    actions = legal_actions(state, case, pool, policy)
    children: dict[str, tuple[SearchState, LegalAction]] = {}
    rejected: dict[str, int] = {}
    for action in actions:
        try:
            child = apply_action(state, action, case)
        except SearchContractError as exc:
            rejected[exc.code] = rejected.get(exc.code, 0) + 1
            continue
        if child.complexity > policy.max_complexity:
            rejected["COMPLEXITY_BOUND"] = rejected.get("COMPLEXITY_BOUND", 0) + 1
            continue
        if child.complexity < state.complexity:
            rejected["NONMONOTONE_COMPLEXITY"] = rejected.get("NONMONOTONE_COMPLEXITY", 0) + 1
            continue
        if child.canonical_hash in children:
            rejected["DUPLICATE_CANONICAL_STATE"] = rejected.get("DUPLICATE_CANONICAL_STATE", 0) + 1
            continue
        children[child.canonical_hash] = (child, action)
    ordered_pairs = tuple(sorted(
        children.values(),
        key=lambda item: (item[0].complexity, item[0].canonical_hash),
    ))
    return FrontierExpansion(
        children=tuple(item[0] for item in ordered_pairs),
        actions=tuple(item[1] for item in ordered_pairs),
        rejected=MappingProxyType(dict(sorted(rejected.items()))),
    )
