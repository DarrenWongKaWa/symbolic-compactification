"""Task-invariant symbolic priority for the S2 beam-search control.

The heuristic sees only the already-loaded public case, the frozen candidate
pool, and a partial search state.  It does not read evaluator artifacts and it
does not inspect compiled or verified obligations.  Its observations are
syntactic evidence for search ordering, never mathematical proof.
"""
from __future__ import annotations

import ast
import hashlib
import itertools
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from research.representation_program_search.program_ir import canonical_json

from .candidates import CandidatePool, LatentCandidate
from .model import SearchState
from .public_case import PublicCase

SYMBOLIC_HEURISTIC_VERSION = "RPSSymbolicHeuristicV1"

# Frozen globally before any scientific DEV search.  These integer
# coefficients are task-invariant and deliberately small enough to audit by
# eye.  Changing one creates a new heuristic version.
SYMBOLIC_HEURISTIC_WEIGHTS = MappingProxyType({
    "coverage_member": 16,
    "reuse_member": 8,
    "relation_support": 4,
    "repeated_node_match": 6,
    "derivative_edge_match": 5,
    "family_match": 4,
    "symmetry_match": 4,
    "cross_latent_compose": 3,
    "complexity": -2,
    "tautology_control_latent": -12,
})

_FUNCTION_NAMES = {
    "Abs", "And", "Eq", "Ge", "Gt", "Le", "Lt", "Ne", "Not", "Or",
    "Piecewise", "Product", "Rational", "Sum", "acos", "asin", "atan",
    "atan2", "conjugate", "cos", "cosh", "exp", "im", "log",
    "polygamma", "re", "sin", "sinh", "sqrt", "tan", "tanh",
}


def _pairs(values: Iterable[str]) -> set[tuple[str, str]]:
    return {
        tuple(sorted(pair))
        for pair in itertools.combinations(sorted(set(values)), 2)
    }


def _tree(expression: str) -> ast.Expression | None:
    try:
        value = ast.parse(expression.strip(), mode="eval")
    except (SyntaxError, ValueError):
        return None
    return value if isinstance(value, ast.Expression) else None


class _AlphaNames(ast.NodeTransformer):
    """Normalize variables by first occurrence while preserving call names."""

    def __init__(self) -> None:
        self.names: dict[str, str] = {}

    def visit_Call(self, node: ast.Call) -> ast.AST:  # noqa: N802 - ast API
        function = node.func
        if isinstance(function, ast.Name):
            normalized_function: ast.expr = ast.Name(function.id, ast.Load())
        else:
            normalized_function = self.visit(function)  # type: ignore[assignment]
        return ast.copy_location(ast.Call(
            func=normalized_function,
            args=[self.visit(item) for item in node.args],
            keywords=[self.visit(item) for item in node.keywords],
        ), node)

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: N802 - ast API
        if node.id in _FUNCTION_NAMES:
            return ast.copy_location(ast.Name(node.id, ast.Load()), node)
        if node.id not in self.names:
            self.names[node.id] = f"rps_v{len(self.names)}"
        return ast.copy_location(ast.Name(self.names[node.id], ast.Load()), node)


class _ShapeAtoms(ast.NodeTransformer):
    """Replace scalar leaves by atoms to expose denominator/power families."""

    def visit_Name(self, node: ast.Name) -> ast.AST:  # noqa: N802 - ast API
        return ast.copy_location(ast.Name("rps_atom", ast.Load()), node)

    def visit_Constant(self, node: ast.Constant) -> ast.AST:  # noqa: N802 - ast API
        return ast.copy_location(ast.Name("rps_atom", ast.Load()), node)


def _dump(node: ast.AST) -> str:
    return ast.dump(ast.fix_missing_locations(node), include_attributes=False)


def _alpha_signature(tree: ast.Expression) -> str:
    return _dump(_AlphaNames().visit(ast.fix_missing_locations(ast.parse(
        ast.unparse(tree), mode="eval"
    ))))


def _shape_signature(node: ast.AST) -> str:
    return _dump(_ShapeAtoms().visit(ast.fix_missing_locations(ast.parse(
        ast.unparse(node), mode="eval"
    ))))


def _call_families(tree: ast.Expression) -> set[tuple[str, int]]:
    return {
        (node.func.id, len(node.args))
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and not node.keywords
    }


def _call_arguments(tree: ast.Expression) -> list[str]:
    return [
        ast.unparse(argument)
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        for argument in node.args
    ]


def _denominator_families(tree: ast.Expression) -> set[str]:
    return {
        _shape_signature(node.right)
        for node in ast.walk(tree)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
    }


def _power_profile(tree: ast.Expression) -> set[tuple[str, int]]:
    result: set[tuple[str, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Pow):
            continue
        exponent = node.right
        if isinstance(exponent, ast.Constant) and isinstance(exponent.value, int):
            result.add((_shape_signature(node.left), exponent.value))
        elif (
            isinstance(exponent, ast.UnaryOp)
            and isinstance(exponent.op, ast.USub)
            and isinstance(exponent.operand, ast.Constant)
            and isinstance(exponent.operand.value, int)
        ):
            result.add((_shape_signature(node.left), -exponent.operand.value))
    return result


@dataclass(frozen=True)
class SymbolicObservations:
    """Canonical proposer-visible relation inventory used only for ranking."""

    relation_edges: tuple[tuple[str, str], ...]
    argument_family_edges: tuple[tuple[str, str], ...]
    denominator_family_edges: tuple[tuple[str, str], ...]
    derivative_edges: tuple[tuple[str, str], ...]
    symmetry_edges: tuple[tuple[str, str], ...]
    repeated_node_values: tuple[str, ...]
    policy_version: str = SYMBOLIC_HEURISTIC_VERSION

    @property
    def canonical_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(self.to_dict()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "argument_family_edges": [list(item) for item in self.argument_family_edges],
            "denominator_family_edges": [list(item) for item in self.denominator_family_edges],
            "derivative_edges": [list(item) for item in self.derivative_edges],
            "policy_version": self.policy_version,
            "relation_edges": [list(item) for item in self.relation_edges],
            "repeated_node_values": list(self.repeated_node_values),
            "symmetry_edges": [list(item) for item in self.symmetry_edges],
        }


def extract_symbolic_observations(
    case: PublicCase,
    pool: CandidatePool,
) -> SymbolicObservations:
    """Extract bounded syntactic relations from public expressions only."""
    parsed = {
        member.member_id: tree
        for member in case.members
        if (tree := _tree(member.expression)) is not None
    }
    relation_edges: set[tuple[str, str]] = set()
    for candidate in pool.latents:
        if candidate.extraction != "SOURCE_LITERAL":
            relation_edges.update(_pairs(candidate.public_origins))

    call_families = {
        member_id: _call_families(tree) for member_id, tree in parsed.items()
    }
    denominator_families = {
        member_id: _denominator_families(tree) for member_id, tree in parsed.items()
    }
    power_profiles = {
        member_id: _power_profile(tree) for member_id, tree in parsed.items()
    }
    alpha_signatures = {
        member_id: _alpha_signature(tree) for member_id, tree in parsed.items()
    }
    argument_edges: set[tuple[str, str]] = set()
    denominator_edges: set[tuple[str, str]] = set()
    derivative_edges: set[tuple[str, str]] = set()
    symmetry_edges: set[tuple[str, str]] = set()
    for left, right in itertools.combinations(sorted(parsed), 2):
        pair = (left, right)
        if call_families[left] & call_families[right]:
            argument_edges.add(pair)
        if denominator_families[left] & denominator_families[right]:
            denominator_edges.add(pair)
        if alpha_signatures[left] == alpha_signatures[right]:
            symmetry_edges.add(pair)
        if any(
            left_shape == right_shape and abs(left_power - right_power) == 1
            for left_shape, left_power in power_profiles[left]
            for right_shape, right_power in power_profiles[right]
        ):
            derivative_edges.add(pair)

    argument_counts: dict[str, int] = {}
    for tree in parsed.values():
        for argument in _call_arguments(tree):
            argument_counts[argument] = argument_counts.get(argument, 0) + 1
    repeated_values = {
        value for value, count in argument_counts.items() if count >= 2
    }
    # Repeated denominator powers are weak confluence evidence.  Preserve
    # exact public node spellings where available; no equality is inferred.
    for member_id, profiles in power_profiles.items():
        if any(abs(power) >= 2 for _shape, power in profiles):
            repeated_values.update(_call_arguments(parsed[member_id]))

    all_relations = (
        relation_edges | argument_edges | denominator_edges
        | derivative_edges | symmetry_edges
    )
    return SymbolicObservations(
        relation_edges=tuple(sorted(all_relations)),
        argument_family_edges=tuple(sorted(argument_edges)),
        denominator_family_edges=tuple(sorted(denominator_edges)),
        derivative_edges=tuple(sorted(derivative_edges)),
        symmetry_edges=tuple(sorted(symmetry_edges)),
        repeated_node_values=tuple(sorted(repeated_values)),
    )


@dataclass(frozen=True)
class SymbolicPriority:
    """Auditable integer priority; higher ``total`` is explored first."""

    total: int
    features: Mapping[str, int]
    policy_version: str = SYMBOLIC_HEURISTIC_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "features", MappingProxyType(dict(sorted(self.features.items())))
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "features": dict(self.features),
            "policy_version": self.policy_version,
            "total": self.total,
            "weights": dict(SYMBOLIC_HEURISTIC_WEIGHTS),
        }


def _candidate_map(pool: CandidatePool) -> dict[str, LatentCandidate]:
    return {f"F_{item.candidate_id}": item for item in pool.latents}


def _candidate_edges(candidate: LatentCandidate | None) -> set[tuple[str, str]]:
    return set() if candidate is None else _pairs(candidate.public_origins)


def symbolic_priority(
    state: SearchState,
    case: PublicCase,
    pool: CandidatePool,
    observations: SymbolicObservations | None = None,
) -> SymbolicPriority:
    """Score a state without consulting proof, compile, or evaluator fields."""
    observed = observations or extract_symbolic_observations(case, pool)
    relation_edges = set(observed.relation_edges)
    argument_edges = set(observed.argument_family_edges)
    denominator_edges = set(observed.denominator_family_edges)
    derivative_edges = set(observed.derivative_edges)
    symmetry_edges = set(observed.symmetry_edges)
    candidates = _candidate_map(pool)
    operators_by_id = {item.operator_id: item for item in state.operators}
    operators_by_output = {
        item.output: item for item in state.operators if item.output is not None
    }

    assignment_latents: dict[str, set[str]] = {}
    latent_assignment_counts: dict[str, int] = {}
    for assignment in state.member_assignments:
        latent_ids = {
            operators_by_id[operator_id].latent_id
            for operator_id in assignment.operator_ids
            if operator_id in operators_by_id
            and operators_by_id[operator_id].latent_id is not None
        }
        assignment_latents[assignment.member_id] = latent_ids
        for latent_id in latent_ids:
            latent_assignment_counts[latent_id] = (
                latent_assignment_counts.get(latent_id, 0) + 1
            )

    reuse_members = sum(
        any(latent_assignment_counts.get(latent_id, 0) >= 2 for latent_id in latent_ids)
        for latent_ids in assignment_latents.values()
    )
    relation_support = 0
    for latent in state.latent_objects:
        if _candidate_edges(candidates.get(latent.latent_id)) & relation_edges:
            relation_support += 1
    relation_support += sum(
        tuple(sorted(group)) in relation_edges for group in state.member_groups
    )

    repeated_values = set(observed.repeated_node_values)
    repeated_matches = sum(
        any(node.nodes.count(value) >= 2 for value in repeated_values)
        for node in state.node_structures
    )
    node_by_id = {item.node_id: item for item in state.node_structures}
    repeated_matches += sum(
        operator.operator == "HERMITE_DD"
        and (node := node_by_id.get(operator.arguments.get("nodes"))) is not None
        and any(node.nodes.count(value) >= 2 for value in repeated_values)
        for operator in state.operators
    )

    derivative_matches = 0
    family_matches = 0
    symmetry_matches = 0
    cross_latent_compose = 0
    for operator in state.operators:
        candidate_edges = _candidate_edges(candidates.get(operator.latent_id or ""))
        if operator.operator == "DERIVATIVE" and candidate_edges & derivative_edges:
            derivative_matches += 1
        if (
            operator.operator in {
                "VALUE", "SUBSTITUTE", "NEWTON_DD", "HERMITE_DD",
                "RECURRENCE", "COMPOSE",
            }
            and candidate_edges & (argument_edges | denominator_edges)
        ):
            family_matches += 1
        if (
            operator.operator in {"PERMUTE", "BASIS_PROJECT", "BASIS_RECONSTRUCT"}
            and candidate_edges & symmetry_edges
        ):
            symmetry_matches += 1
        if operator.operator == "COMPOSE":
            input_latents = {
                operators_by_output[item].latent_id
                for item in operator.inputs
                if item in operators_by_output
            }
            if any(item != operator.latent_id for item in input_latents):
                cross_latent_compose += 1

    tautology_controls = sum(
        candidates.get(latent.latent_id) is not None
        and candidates[latent.latent_id].role == "TAUTOLOGY_CONTROL"
        for latent in state.latent_objects
    )
    features = {
        "complexity": state.complexity,
        "coverage_member": len(state.member_assignments),
        "cross_latent_compose": cross_latent_compose,
        "derivative_edge_match": derivative_matches,
        "family_match": family_matches,
        "relation_support": relation_support,
        "repeated_node_match": repeated_matches,
        "reuse_member": reuse_members,
        "symmetry_match": symmetry_matches,
        "tautology_control_latent": tautology_controls,
    }
    total = sum(
        features[name] * SYMBOLIC_HEURISTIC_WEIGHTS[name]
        for name in SYMBOLIC_HEURISTIC_WEIGHTS
    )
    return SymbolicPriority(total=total, features=features)


def symbolic_priority_key(
    state: SearchState,
    case: PublicCase,
    pool: CandidatePool,
    observations: SymbolicObservations,
) -> tuple[int, int, str]:
    """Ascending deterministic key: priority desc, complexity, state hash."""
    value = symbolic_priority(state, case, pool, observations)
    return (-value.total, state.complexity, state.canonical_hash)
