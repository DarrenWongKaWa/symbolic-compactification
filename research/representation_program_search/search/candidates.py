"""Gold-free, finite candidate extraction from public source expressions."""
from __future__ import annotations

import ast
import copy
import hashlib
import itertools
from dataclasses import dataclass
from typing import Any

from research.representation_program_search.program_ir import canonical_json

from .public_case import PublicCase

CANDIDATE_POLICY_VERSION = "RPSCandidatePoolV2"
MAX_PUBLIC_MEMBERS = 16
MAX_LATENT_CANDIDATES = 24
MAX_ANTI_UNIFICATION_PAIRS = 64
MAX_ANTI_UNIFICATION_PARAMETERS = 2
MAX_NODE_VALUES = 8
MAX_COEFFICIENT_CANDIDATES = 24
MAX_EXPRESSION_CHARS = 4096

_RESERVED_CONSTANTS = {"E", "I", "oo", "pi"}
_DEFAULT_COEFFICIENTS = ("-1", "0", "1", "2", "Rational(1, 2)")


@dataclass(frozen=True)
class LatentCandidate:
    candidate_id: str
    form: str
    parameters: tuple[str, ...]
    expression: str
    public_origins: tuple[str, ...]
    instance_maps: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = ()
    extraction: str = "SOURCE_LITERAL"

    @property
    def role(self) -> str:
        return (
            "TAUTOLOGY_CONTROL"
            if self.extraction == "SOURCE_LITERAL"
            else "SEARCH_CANDIDATE"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "expression": self.expression,
            "extraction": self.extraction,
            "form": self.form,
            "instance_maps": {
                member_id: dict(values) for member_id, values in self.instance_maps
            },
            "parameters": list(self.parameters),
            "public_origins": list(self.public_origins),
            "role": self.role,
        }


@dataclass(frozen=True)
class CandidatePool:
    policy_version: str
    latents: tuple[LatentCandidate, ...]
    node_values: tuple[str, ...]
    coefficients: tuple[str, ...]
    branching_incomplete: bool
    incompleteness_reasons: tuple[str, ...]
    source_member_count: int

    @property
    def canonical_hash(self) -> str:
        return hashlib.sha256(
            canonical_json(self.to_dict()).encode("utf-8")
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "branching_incomplete": self.branching_incomplete,
            "coefficients": list(self.coefficients),
            "incompleteness_reasons": list(self.incompleteness_reasons),
            "latents": [item.to_dict() for item in self.latents],
            "node_values": list(self.node_values),
            "policy_version": self.policy_version,
            "source_member_count": self.source_member_count,
        }


def _candidate(
    *,
    form: str,
    parameters: tuple[str, ...],
    expression: str,
    origins: tuple[str, ...],
    instance_maps: dict[str, dict[str, str]] | None = None,
    extraction: str,
) -> LatentCandidate:
    payload = {
        "expression": expression,
        "extraction": extraction,
        "form": form,
        "instance_maps": instance_maps or {},
        "parameters": list(parameters),
        "public_origins": list(origins),
    }
    identifier = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()[:16]
    return LatentCandidate(
        candidate_id=f"LC_{identifier}",
        form=form,
        parameters=parameters,
        expression=expression,
        public_origins=origins,
        instance_maps=tuple(
            (member_id, tuple(sorted(values.items())))
            for member_id, values in sorted((instance_maps or {}).items())
        ),
        extraction=extraction,
    )


def _anti_unify(left: ast.AST, right: ast.AST) -> tuple[ast.AST, list[tuple[ast.AST, ast.AST]]] | None:
    replacements: list[tuple[ast.AST, ast.AST]] = []
    replacement_index: dict[tuple[str, str], int] = {}

    def placeholder(a: ast.AST, b: ast.AST) -> ast.Name:
        key = (ast.dump(a, include_attributes=False), ast.dump(b, include_attributes=False))
        if key not in replacement_index:
            replacement_index[key] = len(replacements)
            replacements.append((a, b))
        return ast.Name(id=f"rps_p{replacement_index[key]}", ctx=ast.Load())

    def visit(a: Any, b: Any) -> Any:
        if isinstance(a, ast.AST) and isinstance(b, ast.AST):
            if ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False):
                return copy.deepcopy(a)
            if type(a) is not type(b):
                return placeholder(a, b)
            node = copy.copy(a)
            for field in a._fields:
                av, bv = getattr(a, field), getattr(b, field)
                if isinstance(av, ast.AST) and isinstance(bv, ast.AST):
                    setattr(node, field, visit(av, bv))
                elif isinstance(av, list) and isinstance(bv, list) and len(av) == len(bv):
                    values: list[Any] = []
                    for a_item, b_item in zip(av, bv):
                        if isinstance(a_item, ast.AST) and isinstance(b_item, ast.AST):
                            values.append(visit(a_item, b_item))
                        elif a_item == b_item:
                            values.append(copy.deepcopy(a_item))
                        else:
                            return placeholder(a, b)
                    setattr(node, field, values)
                elif av == bv:
                    setattr(node, field, copy.deepcopy(av))
                else:
                    return placeholder(a, b)
            return node
        return copy.deepcopy(a) if a == b else placeholder(left, right)

    unified = visit(left, right)
    if not replacements or len(replacements) > MAX_ANTI_UNIFICATION_PARAMETERS:
        return None
    if isinstance(unified, ast.Name) and unified.id.startswith("rps_p"):
        return None
    return ast.fix_missing_locations(unified), replacements


def _parsed(expression: str) -> ast.Expression | None:
    if len(expression) > MAX_EXPRESSION_CHARS:
        return None
    try:
        value = ast.parse(expression.strip(), mode="eval")
    except (SyntaxError, ValueError):
        return None
    return value if isinstance(value, ast.Expression) else None


def _unary_call_candidates(member_id: str, tree: ast.Expression) -> list[LatentCandidate]:
    result: list[LatentCandidate] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or len(node.args) != 1 or node.keywords:
            continue
        if not isinstance(node.func, ast.Name):
            continue
        expression = ast.unparse(ast.Call(
            func=copy.deepcopy(node.func),
            args=[ast.Name(id="rps_p0", ctx=ast.Load())],
            keywords=[],
        ))
        argument = ast.unparse(node.args[0])
        result.append(_candidate(
            form="FUNCTION_1",
            parameters=("rps_p0",),
            expression=expression,
            origins=(member_id,),
            instance_maps={member_id: {"rps_p0": argument}},
            extraction="UNARY_CALL_SCHEMA",
        ))
    return result


class _ParameterizeNames(ast.NodeTransformer):
    def __init__(self, replacements: dict[str, str]):
        self.replacements = replacements

    def visit_Name(self, node: ast.Name) -> ast.AST:
        replacement = self.replacements.get(node.id)
        if replacement is None:
            return copy.deepcopy(node)
        return ast.copy_location(ast.Name(id=replacement, ctx=ast.Load()), node)


def _expression_parameter_candidates(
    member_id: str,
    tree: ast.Expression,
) -> list[LatentCandidate]:
    """Abstract one or two free names across a complete source expression.

    This is a syntax-only latent-induction rule.  It does not inspect a
    reference program or ask whether the resulting family is useful.  A
    one-member VALUE wrapper can therefore still be generated, but the normal
    tautology/complexity gates prevent that wrapper from becoming success.
    """
    function_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    names = sorted({
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id not in function_names
        and node.id not in _RESERVED_CONSTANTS
        and not node.id.startswith("rps_p")
    })
    result: list[LatentCandidate] = []
    for width in (1, 2):
        for selected in itertools.combinations(names, width):
            parameters = tuple(f"rps_p{index}" for index in range(width))
            replacements = dict(zip(selected, parameters))
            parameterized = _ParameterizeNames(replacements).visit(
                copy.deepcopy(tree)
            )
            parameterized = ast.fix_missing_locations(parameterized)
            result.append(_candidate(
                form="FUNCTION_1" if width == 1 else "FUNCTION_2",
                parameters=parameters,
                expression=ast.unparse(parameterized),
                origins=(member_id,),
                instance_maps={
                    member_id: dict(zip(parameters, selected)),
                },
                extraction="FULL_EXPRESSION_PARAMETER_ABSTRACTION",
            ))
    return result


def _node_values(trees: list[tuple[str, ast.Expression]]) -> tuple[str, ...]:
    function_names = {
        node.func.id
        for _member_id, tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    names = sorted({
        node.id
        for _member_id, tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Name)
        and node.id not in function_names
        and node.id not in _RESERVED_CONSTANTS
        and not node.id.startswith("rps_p")
    })
    argument_values = sorted({
        ast.unparse(node.args[0])
        for _member_id, tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.func, ast.Name)
    })
    ordered = list(argument_values)
    ordered.extend(name for name in names if name not in ordered)
    return tuple(ordered[:MAX_NODE_VALUES])


def _simple_product(node: ast.AST, *, excluded_names: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id not in _RESERVED_CONSTANTS and node.id not in excluded_names
    if isinstance(node, ast.Constant):
        return isinstance(node.value, int) and not isinstance(node.value, bool)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
        return _simple_product(node.operand, excluded_names=excluded_names)
    return (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Mult)
        and _simple_product(node.left, excluded_names=excluded_names)
        and _simple_product(node.right, excluded_names=excluded_names)
    )


def _canonical_coefficient(value: str) -> str:
    try:
        return ast.unparse(ast.parse(value, mode="eval").body)
    except (SyntaxError, ValueError):
        return value


def _coefficient_candidates(
    trees: list[tuple[str, ast.Expression]],
    node_values: tuple[str, ...],
) -> tuple[str, ...]:
    """Inventory a bounded, source-derived reconstruction coefficient palette."""
    observed_integers: set[int] = {1, 2}
    observed: set[str] = {_canonical_coefficient(item) for item in _DEFAULT_COEFFICIENTS}
    reciprocals: set[str] = set()
    function_names = {
        node.func.id
        for _member_id, tree in trees
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    for _member_id, tree in trees:
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if (
                    isinstance(node.value, int)
                    and not isinstance(node.value, bool)
                    and abs(node.value) <= 16
                ):
                    observed_integers.add(abs(node.value))
                    observed.add(str(node.value))
            elif _simple_product(node, excluded_names=function_names):
                observed.add(_canonical_coefficient(ast.unparse(node)))
            elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                denominator = ast.unparse(node.right)
                reciprocal = f"1/({denominator})"
                reciprocal = _canonical_coefficient(reciprocal)
                reciprocals.add(reciprocal)
                observed.add(reciprocal)
            elif (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, ast.Pow)
                and isinstance(node.right, ast.UnaryOp)
                and isinstance(node.right.op, ast.USub)
                and isinstance(node.right.operand, ast.Constant)
                and isinstance(node.right.operand.value, int)
            ):
                observed.add(_canonical_coefficient(ast.unparse(node)))
    for left, right in itertools.combinations(node_values, 2):
        observed.add(_canonical_coefficient(f"{left}*{right}"))
    for reciprocal in reciprocals:
        for integer in sorted(observed_integers):
            if integer > 1:
                observed.add(_canonical_coefficient(f"{integer}*({reciprocal})"))

    defaults = [_canonical_coefficient(item) for item in _DEFAULT_COEFFICIENTS]
    remainder = sorted(
        observed - set(defaults),
        key=lambda value: (len(value), value),
    )
    return tuple((defaults + remainder)[:MAX_COEFFICIENT_CANDIDATES])


def extract_candidate_pool(case: PublicCase) -> CandidatePool:
    """Build the frozen finite pool without evaluator labels or programs."""
    reasons = [
        "FINITE_SOURCE_DERIVATION_IS_NOT_GLOBAL_EXPRESSION_ENUMERATION",
        f"LATENT_CANDIDATES_CAPPED_AT_{MAX_LATENT_CANDIDATES}",
        f"NODE_VALUES_CAPPED_AT_{MAX_NODE_VALUES}",
        f"ANTI_UNIFICATION_PAIRS_CAPPED_AT_{MAX_ANTI_UNIFICATION_PAIRS}",
    ]
    members = case.members[:MAX_PUBLIC_MEMBERS]
    if len(case.members) > MAX_PUBLIC_MEMBERS:
        reasons.append(f"PUBLIC_MEMBERS_TRUNCATED_AT_{MAX_PUBLIC_MEMBERS}")
    parsed = [
        (member.member_id, tree)
        for member in members
        if (tree := _parsed(member.expression)) is not None
    ]
    candidates: dict[str, LatentCandidate] = {}
    for member in members:
        if len(member.expression) <= MAX_EXPRESSION_CHARS:
            item = _candidate(
                form="FUNCTION_1",
                parameters=("rps_p0",),
                expression=member.expression.strip(),
                origins=(member.member_id,),
                instance_maps={member.member_id: {"rps_p0": "0"}},
                extraction="SOURCE_LITERAL",
            )
            candidates[item.candidate_id] = item
    for member_id, tree in parsed:
        for item in _expression_parameter_candidates(member_id, tree):
            candidates[item.candidate_id] = item
        for item in _unary_call_candidates(member_id, tree):
            candidates[item.candidate_id] = item

    pairs = list(itertools.combinations(parsed, 2))
    if len(pairs) > MAX_ANTI_UNIFICATION_PAIRS:
        reasons.append("ANTI_UNIFICATION_PAIR_LIST_TRUNCATED")
    for (left_id, left), (right_id, right) in pairs[:MAX_ANTI_UNIFICATION_PAIRS]:
        result = _anti_unify(left.body, right.body)
        if result is None:
            continue
        template, replacements = result
        parameters = tuple(f"rps_p{index}" for index in range(len(replacements)))
        form = "FUNCTION_1" if len(parameters) == 1 else "FUNCTION_2"
        item = _candidate(
            form=form,
            parameters=parameters,
            expression=ast.unparse(template),
            origins=(left_id, right_id),
            instance_maps={
                left_id: {
                    name: ast.unparse(values[0])
                    for name, values in zip(parameters, replacements)
                },
                right_id: {
                    name: ast.unparse(values[1])
                    for name, values in zip(parameters, replacements)
                },
            },
            extraction="PAIRWISE_ANTI_UNIFICATION",
        )
        candidates[item.candidate_id] = item

    extraction_priority = {
        "PAIRWISE_ANTI_UNIFICATION": 0,
        "SOURCE_LITERAL": 1,
        "UNARY_CALL_SCHEMA": 2,
        "FULL_EXPRESSION_PARAMETER_ABSTRACTION": 3,
    }
    ordered = tuple(sorted(
        candidates.values(),
        key=lambda item: (
            extraction_priority.get(item.extraction, 99),
            item.candidate_id,
        ),
    ))[:MAX_LATENT_CANDIDATES]
    if len(candidates) > MAX_LATENT_CANDIDATES:
        reasons.append("LATENT_CANDIDATE_LIST_TRUNCATED")
    nodes = _node_values(parsed)
    return CandidatePool(
        policy_version=CANDIDATE_POLICY_VERSION,
        latents=ordered,
        node_values=nodes,
        coefficients=_coefficient_candidates(parsed, nodes),
        branching_incomplete=True,
        incompleteness_reasons=tuple(sorted(set(reasons))),
        source_member_count=len(case.members),
    )
