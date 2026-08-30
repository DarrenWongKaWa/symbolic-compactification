"""Frozen RPS complexity and score implementation.

No coefficient is configurable per task.  Evaluation may attach proof
evidence, but S0/S1 never use verifier outcomes to order their frontiers.
"""
from __future__ import annotations

import math
import sympy
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterable

from research.representation_program_search.program_ir import RepresentationProgram
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import infer_namespace, parse_expression

from .model import ObligationEvidence, SearchContractError


@dataclass(frozen=True)
class ComplexityBreakdown:
    n_latents: int
    n_operators: int
    max_operator_depth: int
    n_parameters: int
    n_member_exceptions: int
    latent_expression_units: int
    n_reconstruction_ops: int

    @property
    def total(self) -> int:
        return (
            self.n_latents
            + self.n_operators
            + self.max_operator_depth
            + self.n_parameters
            + self.n_member_exceptions
            + self.latent_expression_units
            + self.n_reconstruction_ops
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "latent_expression_units": self.latent_expression_units,
            "max_operator_depth": self.max_operator_depth,
            "n_latents": self.n_latents,
            "n_member_exceptions": self.n_member_exceptions,
            "n_operators": self.n_operators,
            "n_parameters": self.n_parameters,
            "n_reconstruction_ops": self.n_reconstruction_ops,
            "total": self.total,
        }


def _count_ops(expression: str) -> int:
    """Use the engine's inspection namespace and exact SymPy ``count_ops``.

    Namespace inference is explicitly inspection-only; it never supplies a
    verification assumption.  Candidate compilation and later evaluation
    still use the case's declared namespace and fail closed independently.
    """
    try:
        symbols, functions = infer_namespace(expression)
        parsed = parse_expression(expression, symbols, functions=functions)
        return int(sympy.count_ops(parsed, visual=False))
    except (AdapterError, TypeError, ValueError):
        raise SearchContractError("LATENT_COUNT_OPS_UNAVAILABLE") from None


def _operator_depth(program: RepresentationProgram) -> int:
    by_output = {
        item.output: item for item in program.operators if item.output is not None
    }
    memo: dict[str, int] = {}

    def depth(output: str, visiting: frozenset[str] = frozenset()) -> int:
        if output in memo:
            return memo[output]
        if output in visiting:
            return len(program.operators) + 1
        operator = by_output.get(output)
        if operator is None:
            return 0
        value = 1 + max(
            (depth(item, visiting | {output}) for item in operator.inputs),
            default=0,
        )
        memo[output] = value
        return value

    return max((depth(output) for output in by_output), default=0)


def _assignment_latents(program: RepresentationProgram) -> dict[str, frozenset[str]]:
    by_id = {item.operator_id: item for item in program.operators}
    return {
        assignment.member_id: frozenset(
            by_id[operator_id].latent_id
            for operator_id in assignment.operator_ids
            if operator_id in by_id and by_id[operator_id].latent_id is not None
        )
        for assignment in program.member_assignments
    }


def _member_exceptions(program: RepresentationProgram) -> int:
    uses = _assignment_latents(program)
    counts: dict[str, int] = {}
    for latent_ids in uses.values():
        for latent_id in latent_ids:
            counts[latent_id] = counts.get(latent_id, 0) + 1
    return sum(
        1
        for latent_ids in uses.values()
        if not latent_ids or not any(counts[item] > 1 for item in latent_ids)
    )


def complexity_breakdown(program: RepresentationProgram) -> ComplexityBreakdown:
    expression_ops = sum(_count_ops(item.expression) for item in program.latent_objects)
    exceptions = _member_exceptions(program)
    return ComplexityBreakdown(
        n_latents=len(program.latent_objects),
        n_operators=len(program.operators),
        max_operator_depth=_operator_depth(program),
        n_parameters=sum(len(item.parameters) for item in program.latent_objects),
        n_member_exceptions=exceptions,
        latent_expression_units=math.ceil(expression_ops / 8),
        n_reconstruction_ops=sum(
            len(item.operator_ids) for item in program.member_assignments
        ),
    )


def _fraction_payload(value: Fraction) -> dict[str, int]:
    return {"denominator": value.denominator, "numerator": value.numerator}


def score_program(
    program: RepresentationProgram,
    evidence: Iterable[ObligationEvidence] = (),
    *,
    tautological: bool = False,
    compile_status: str | None = None,
) -> dict[str, object]:
    """Apply the exact frozen coefficients λ1=1, λ2=1, λ3=1, λ4=2."""
    proof = tuple(evidence)
    evidence_by_id: dict[str, ObligationEvidence] = {}
    for item in proof:
        if item.obligation_id in evidence_by_id:
            raise ValueError(f"DUPLICATE_OBLIGATION_EVIDENCE:{item.obligation_id}")
        evidence_by_id[item.obligation_id] = item
    obligations_by_id = {item.obligation_id: item for item in program.obligations}
    required_nonzero = any(
        obligations_by_id[identifier].required and item.verdict == "NONZERO"
        for identifier, item in evidence_by_id.items()
        if identifier in obligations_by_id
    )
    coverage = Fraction(
        len(program.member_assignments),
        len(program.source_members),
    ) if program.source_members else Fraction(0)
    verified = 0 if tautological else sum(
        item.verdict == "ZERO"
        for identifier, item in evidence_by_id.items()
        if identifier in obligations_by_id
    )
    assignment_latents = _assignment_latents(program)
    counts: dict[str, int] = {}
    for latent_ids in assignment_latents.values():
        for latent_id in latent_ids:
            counts[latent_id] = counts.get(latent_id, 0) + 1
    shared_members = sum(
        any(counts[item] >= 2 for item in latent_ids)
        for latent_ids in assignment_latents.values()
    )
    reuse = (
        Fraction(shared_members, len(program.latent_objects))
        if program.latent_objects
        else Fraction(0)
    )
    breakdown = complexity_breakdown(program)
    exceptions = breakdown.n_member_exceptions
    score = coverage + verified + reuse - breakdown.total - 2 * exceptions
    ineligibility: list[str] = []
    if required_nonzero:
        ineligibility.append("REQUIRED_NONZERO")
    if compile_status == "COMPILE_FAILURE":
        ineligibility.append("COMPILE_FAILURE")
    if tautological:
        ineligibility.append("TAUTOLOGICAL")
    return {
        "coefficients": {"lambda1": 1, "lambda2": 1, "lambda3": 1, "lambda4": 2},
        "complexity": breakdown.to_dict(),
        "coverage": _fraction_payload(coverage),
        "exceptions": exceptions,
        "ineligible": bool(ineligibility),
        "ineligibility_reasons": ineligibility,
        "reuse": _fraction_payload(reuse),
        "score": _fraction_payload(score),
        "verified_relations": verified,
    }
