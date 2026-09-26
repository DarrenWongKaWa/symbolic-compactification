"""Seal many-body records: Matsubara sums and asymptotic remainder claims.

Runs after the split-parent and BZ passes. Only edges that carry a
``matsubara`` or ``asymptotic`` spec are touched; the verdict comes from
``symbolic_compactification.manybody``, never from edge text. A certificate
is CERTIFIED_BY_RULE (structural table), never an engine ZERO.
"""
from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable

from .edges import AuditEdge
from .schema import (
    ASYMPTOTIC_CLAIM,
    CERTIFIED_BY_RULE,
    MATSUBARA_SUM,
    NONZERO,
    NOT_LOWERED,
    UNKNOWN,
    AuditError,
    AuditRecord,
    RuleCertificate,
)

_PLACEHOLDER_WARNINGS = frozenset({
    "MATSUBARA_SUM_NOT_LOCAL_RESIDUAL", "ASYMPTOTIC_REMAINDER_NOT_CERTIFIED",
})
_MAX_CONCLUSION = 2000


def _read(read_expression: Callable, workspace, relpath: str) -> str:
    text, _, _ = read_expression(workspace, relpath)
    return text.strip()


def _run(edge: AuditEdge, workspace, assumptions, read_expression):
    symbols, functions = list(assumptions.symbols), list(assumptions.functions)
    if edge.edge_type == MATSUBARA_SUM:
        from ..manybody import verify_matsubara_sum
        spec = edge.spec("matsubara")
        if not edge.rhs:
            raise AuditError("MATSUBARA_CLAIM_MISSING", "MATSUBARA_SUM needs rhs")
        return verify_matsubara_sum(
            _read(read_expression, workspace, spec["summand"]),
            _read(read_expression, workspace, edge.rhs),
            variable=spec["variable"], beta=spec["beta"],
            statistics=spec["statistics"],
            convergence=spec.get("convergence", "none"),
            positive=tuple(spec.get("positive", ())),
            symbols=symbols, functions=functions,
            declared_rules=tuple(assumptions.rules))
    from ..manybody import certify_remainder
    spec = edge.spec("asymptotic")
    return certify_remainder(
        _read(read_expression, workspace, spec["function"]),
        _read(read_expression, workspace, spec["approximant"]),
        variable=spec["variable"], point=spec["point"], order=int(spec["order"]),
        direction=spec.get("direction", "+-"),
        positive=tuple(spec.get("positive", ())),
        symbols=symbols, functions=functions)


def _certificate(record: AuditRecord, edge: AuditEdge, outcome,
                 by_id: dict[str, AuditRecord]) -> RuleCertificate:
    children = [(child, by_id[child].status if child in by_id else "MISSING")
                for child in record.children]
    children += [("symbolic-check", outcome.symbolic_verdict),
                 ("numeric-crosscheck", str(outcome.numeric.get("status", "NOT_RUN")))]
    if edge.edge_type == MATSUBARA_SUM:
        spec = edge.spec("matsubara")
        domain = f"{spec['statistics']}; convergence={spec.get('convergence', 'none')}"
        conclusion = f"T*sum_n F(i*w_n) = {outcome.derived}"
    else:
        spec = edge.spec("asymptotic")
        domain = f"{spec['variable']} -> {spec['point']} ({spec.get('direction', '+-')})"
        conclusion = (f"(f - P)/{spec['variable']}**({spec['order']}) -> "
                      f"{outcome.derived}; remainder certificate "
                      f"{outcome.certificate_hash}")
    return RuleCertificate(
        rule_id=outcome.rule_id,
        local_children=tuple(children),
        domain=domain,
        conclusion=conclusion[:_MAX_CONCLUSION],
        result=CERTIFIED_BY_RULE,
        integrand_periodic="not_applicable",
    )


def apply_manybody_certificates(
    records: tuple[AuditRecord, ...],
    edges: list[AuditEdge] | tuple[AuditEdge, ...],
    workspace: Any,
    assumptions: Any,
    *,
    read_expression: Callable,
    seal: Callable[[AuditRecord], AuditRecord],
) -> tuple[AuditRecord, ...]:
    edges_by_id = {edge.edge_id: edge for edge in edges}
    by_id = {record.edge_id: record for record in records}
    updated: list[AuditRecord] = []
    for record in records:
        edge = edges_by_id.get(record.edge_id)
        wants = edge is not None and (
            record.edge_type == MATSUBARA_SUM
            or (record.edge_type == ASYMPTOTIC_CLAIM and edge.asymptotic))
        if not wants or record.status not in (NOT_LOWERED, UNKNOWN):
            updated.append(record)
            continue
        if record.edge_type == MATSUBARA_SUM and not edge.matsubara:
            updated.append(seal(replace(record, warnings=tuple(dict.fromkeys(
                (*record.warnings, "MATSUBARA_SPEC_MISSING"))))))
            continue
        kept = tuple(w for w in record.warnings if w not in _PLACEHOLDER_WARNINGS)
        try:
            outcome = _run(edge, workspace, assumptions, read_expression)
        except AuditError as exc:
            updated.append(seal(replace(record, warnings=tuple(dict.fromkeys(
                (*kept, f"MANYBODY_INPUT_ERROR:{exc.code}"))))))
            continue
        numeric = outcome.numeric.get("status")
        notes = (f"NUMERIC_CROSSCHECK_{numeric}",) if numeric in ("AGREES", "DISAGREES") else ()
        warnings = tuple(dict.fromkeys((*kept, *outcome.reasons, *notes)))
        if outcome.status == CERTIFIED_BY_RULE:
            new = replace(
                record, status=CERTIFIED_BY_RULE, result=CERTIFIED_BY_RULE,
                executable=False, warnings=warnings,
                rule_certificate=_certificate(record, edge, outcome, by_id),
                remainder_certificate_hash=(
                    outcome.certificate_hash if record.edge_type == ASYMPTOTIC_CLAIM
                    else None))
        elif outcome.status == NONZERO:
            new = replace(record, status=NONZERO, result=NONZERO, warnings=warnings)
        else:
            new = replace(record, status=outcome.status, result=outcome.status,
                          warnings=warnings)
        updated.append(seal(new))
    return tuple(updated)
