"""Seal many-body records: Matsubara sums and asymptotic remainder claims.

Runs after the split-parent and BZ passes. Only edges that carry a
``matsubara`` or ``asymptotic`` spec are touched; the verdict comes from
``symbolic_compactification.manybody``, never from edge text. A certificate
is CERTIFIED_BY_RULE (structural table), never an engine ZERO.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any, Callable

from .edges import AuditEdge
from .io import assert_contained, contained_relpath, sha256_bytes
from .schema import (
    ASYMPTOTIC_CLAIM,
    CERTIFIED_BY_RULE,
    MATSUBARA_SUM,
    NONZERO,
    NOT_LOWERED,
    SOURCE_TIED_STEP_CARD,
    STEP_CARD,
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


def _card_paths(card: dict, card_path: Path) -> list[Path]:
    """Every file a card reads: its source document and include files."""
    includes = card.get("include") or []
    includes = [includes] if isinstance(includes, str) else list(includes)
    raw = [*includes, *([card["source_document"]] if card.get("source_document") else [])]
    return [card_path.parent / str(item) for item in raw]


def _step_card(record: AuditRecord, edge: AuditEdge, workspace) -> AuditRecord:
    """Replay one step card strictly; its decision becomes the record status."""
    import yaml

    from ..manybody.cards import CardError, load_card, run_card
    from ..models import AdapterError
    try:
        relpath, path = contained_relpath(workspace.root, edge.spec("step_card")["card"],
                                          "step_card.card")
        card = load_card(path)
        for dependency in _card_paths(card, path):       # a package must be self-contained
            assert_contained(workspace.root, dependency, "step_card dependency")
        result = run_card(path, require_source=True)
    except (AuditError, AdapterError, CardError, OSError, ValueError, yaml.YAMLError) as exc:
        code = getattr(exc, "code", "STEP_CARD_INVALID")
        return replace(record, status=UNKNOWN, result=UNKNOWN,
                       warnings=(*record.warnings, f"MANYBODY_INPUT_ERROR:{code}"))
    decision = result["decision"]
    transcription = (result.get("transcription") or {}).get("status", "ABSENT")
    checker = str(result.get("status") or result.get("verdict") or "UNKNOWN")
    fields = (result.get("transcription") or {}).get("fields") or {}
    claim_field = next((f for k, f in fields.items()
                        if k in ("claim", "rhs", "approximant") and f.get("quote")), {})
    quote, read_as = claim_field.get("quote"), claim_field.get("translated")
    where = claim_field.get("location") or {}
    source_at = None
    if where:
        doc = str(card.get("source_document") or "")
        try:
            doc = str((path.parent / doc).resolve().relative_to(workspace.root.resolve()))
        except (OSError, ValueError):
            pass
        source_at = "|".join([doc, str(where.get("line", "")), str(where.get("label", "")),
                              str(where.get("number", ""))])
    point = (result.get("counterexample") or {}).get("point")
    notes = (f"CARD_CHECK:{result.get('check')}", f"CARD_CHECKER:{checker}",
             f"TRANSCRIPTION:{transcription}",
             *(f"BLOCKED:{why}" for why in result.get("decision_blocked_by", [])),
             *(f"DIAGNOSIS:{d}" for d in (result.get("diagnosis") or [])[:3]),
             *((f"QUOTE:{quote[:_MAX_CONCLUSION]}",) if quote else ()),
             *((f"READ_AS:{read_as[:_MAX_CONCLUSION]}",) if read_as else ()),
             *((f"SOURCE_AT:{source_at}",) if source_at else ()),
             *(f"ERRATUM:{f['erratum'][:_MAX_CONCLUSION]}" for f in fields.values() if f.get("erratum")),
             *(f"ERRATUM_NOTE:{f['erratum_note'][:500]}" for f in fields.values() if f.get("erratum_note")),
             *(f"PRINTED:{f['quote'][:_MAX_CONCLUSION]}" for f in fields.values() if f.get("erratum")),
             *((f"WITH_ERRATUM:{result['decision_with_errata']}",)
               if result.get("decision_with_errata") else ()),
             *((f"DERIVED:{str(result['derived'])[:_MAX_CONCLUSION]}",) if result.get("derived") else ()),
             *((f"COUNTEREXAMPLE:{point}",) if point else ()))
    warnings = tuple(dict.fromkeys((*record.warnings, *notes)))
    if decision == "VALID":
        certificate = RuleCertificate(
            rule_id=SOURCE_TIED_STEP_CARD,
            local_children=(("card", relpath), ("card-sha256", sha256_bytes(path.read_bytes())),
                            ("checker", checker), ("transcription", transcription)),
            domain=f"check={result.get('check')}; strict source replay",
            conclusion=(f"claim as quoted: {quote or '(see card)'}")[:_MAX_CONCLUSION],
            result=CERTIFIED_BY_RULE,
            integrand_periodic="not_applicable")
        return replace(record, status=CERTIFIED_BY_RULE, result=CERTIFIED_BY_RULE,
                       executable=False, warnings=warnings, rule_certificate=certificate)
    if decision == "INVALID":
        return replace(record, status=NONZERO, result=NONZERO, warnings=warnings)
    return replace(record, status=UNKNOWN, result=UNKNOWN, warnings=warnings)


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
        if edge is not None and record.edge_type == STEP_CARD:
            if not edge.step_card:
                updated.append(seal(replace(record, status=UNKNOWN, result=UNKNOWN,
                                            warnings=(*record.warnings, "STEP_CARD_SPEC_MISSING"))))
            else:
                updated.append(seal(_step_card(record, edge, workspace)))
            continue
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
