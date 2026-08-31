"""Targeted tests for derivation-audit edge lowering."""
from __future__ import annotations

import pytest

from symbolic_compactification.audit.edges import AuditEdge, GroundingResult
from symbolic_compactification.audit.lowering import lower_edge
from symbolic_compactification.audit.schema import (
    ALGEBRAIC_EQUIVALENCE,
    ASYMPTOTIC_CLAIM,
    BOOKKEEPING,
    COMPLETENESS_RECONSTRUCTION,
    DEFINITION,
    DEFINITION_INSERTION,
    EDGE_TYPE_SPECS,
    GLOBAL_SYMMETRY_PAIRING,
    GROUNDING_FAILURE,
    INTEGRAL_ARGUMENT,
    LIMIT_CLAIM,
    LOWERING_NOT_APPLICABLE,
    LOWERING_PARTIAL,
    LOWERING_SUPPORTED,
    NOT_LOWERED,
    PAIRWISE_REDUCTION,
    RECORDED,
    SPECIAL_FUNCTION_IDENTITY,
    SPLIT,
    SPLIT_PARENT,
    UNKNOWN,
    ZERO,
)
from symbolic_compactification.audit.workspace import initialize_audit_workspace

_HASH = "a" * 64


@pytest.fixture
def workspace(tmp_path):
    return initialize_audit_workspace(tmp_path / "paper-audit")


def _edge(**overrides) -> AuditEdge:
    payload = dict(
        edge_id="E001",
        source_from="eq:a",
        source_to="eq:b",
        edge_type=ALGEBRAIC_EQUIVALENCE,
    )
    payload.update(overrides)
    return AuditEdge(**payload)


def _ground(edge: AuditEdge, *, ok: bool = True, issues=()) -> GroundingResult:
    return GroundingResult(
        edge=edge,
        ok=ok,
        status=GROUNDING_FAILURE if not ok else "GROUNDED",
        issues=tuple(issues),
        source_refs=tuple(
            ref for ref in (edge.source_from, edge.source_to) if ref),
        source_snapshot_hash=_HASH,
    )


def _write_expr(workspace, name: str, text: str) -> str:
    rel = f"expressions/{name}"
    (workspace.root / rel).write_text(text, encoding="utf-8")
    return rel


def test_grounding_failure_is_not_executable(workspace):
    edge = _edge(residual="x - y")
    result = lower_edge(
        edge, workspace, _ground(edge, ok=False, issues=("MISSING_SOURCE",)))
    assert result.executable is False
    assert result.status == GROUNDING_FAILURE
    assert result.residual_text is None
    assert result.warnings == ("MISSING_SOURCE",)
    assert result.status != ZERO


@pytest.mark.parametrize(
    "edge_type,spec",
    sorted(EDGE_TYPE_SPECS.items()),
    ids=sorted(EDGE_TYPE_SPECS),
)
def test_default_status_without_residual_or_members(workspace, edge_type, spec):
    edge = _edge(edge_id=f"T-{edge_type}", edge_type=edge_type)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == spec.default_status
    assert result.applicability == spec.lowering
    assert result.residual_text is None
    assert result.status != ZERO


def test_definition_insertion_is_definition_not_executable(workspace):
    edge = _edge(
        edge_type=DEFINITION_INSERTION,
        residual="x - y",
        lhs="expressions/lhs.txt",
        rhs="expressions/rhs.txt",
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == DEFINITION
    assert result.residual_text is None


def test_bookkeeping_without_residual_is_recorded(workspace):
    edge = _edge(edge_type=BOOKKEEPING)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == RECORDED


def test_completeness_reconstruction_without_residual_is_recorded(workspace):
    edge = _edge(edge_type=COMPLETENESS_RECONSTRUCTION)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == RECORDED
    assert result.applicability == LOWERING_PARTIAL


def test_split_parent_is_split_not_executable(workspace):
    edge = _edge(
        edge_type=SPLIT_PARENT,
        children=("C12", "C13"),
        residual="x - y",
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == SPLIT
    assert result.residual_text is None
    assert result.applicability == LOWERING_NOT_APPLICABLE


def test_asymptotic_claim_is_unknown_and_never_rewritten(workspace):
    lhs = _write_expr(workspace, "F.txt", "F")
    rhs = _write_expr(workspace, "approx.txt", "A/gamma")
    edge = _edge(
        edge_type=ASYMPTOTIC_CLAIM,
        lhs=lhs,
        rhs=rhs,
        residual="F - A/gamma",
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == UNKNOWN
    assert result.residual_text is None
    assert "ASYMPTOTIC_REMAINDER_NOT_CERTIFIED" in result.warnings
    assert result.residual_text != "F - A/gamma"
    assert result.residual_text != "(F) - (A/gamma)"


def test_integral_argument_is_not_lowered_as_a_whole(workspace):
    edge = _edge(
        edge_type=INTEGRAL_ARGUMENT,
        lhs=_write_expr(workspace, "int_lhs.txt", "Integral(f(x), x)"),
        rhs=_write_expr(workspace, "int_rhs.txt", "0"),
        residual="Integral(f(x), x) - 0",
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == NOT_LOWERED
    assert result.residual_text is None
    assert "INTEGRAL_ARGUMENT_NOT_LOCAL_RESIDUAL" in result.warnings


def test_limit_claim_without_residual_is_unknown(workspace):
    edge = _edge(
        edge_type=LIMIT_CLAIM,
        lhs=_write_expr(workspace, "lim_lhs.txt", "Limit(f(x), x, 0)"),
        rhs=_write_expr(workspace, "lim_rhs.txt", "1"),
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == UNKNOWN
    assert result.residual_text is None
    assert "NAKED_LIMIT_DIFFERENCE_NOT_IDENTITY" in result.warnings


def test_limit_claim_with_explicit_residual_is_executable(workspace):
    rel = _write_expr(workspace, "limit_residual.txt", "a - b")
    edge = _edge(edge_type=LIMIT_CLAIM, residual=rel)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.status == UNKNOWN
    assert result.residual_text == "a - b"
    assert result.residual_path == rel
    assert result.status != ZERO


def test_supported_type_without_residual_or_members_is_not_lowered(workspace):
    edge = _edge(edge_type=ALGEBRAIC_EQUIVALENCE)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == NOT_LOWERED
    assert result.applicability == LOWERING_SUPPORTED


def test_algebraic_residual_file_is_executable(workspace):
    rel = _write_expr(workspace, "residual.txt", "x - y\n")
    edge = _edge(residual=rel)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.status == NOT_LOWERED
    assert result.residual_text == "x - y"
    assert result.residual_path == rel
    assert result.obligation_id == edge.edge_id
    assert result.status != ZERO


def test_algebraic_lhs_rhs_files_form_native_difference(workspace):
    lhs = _write_expr(workspace, "lhs.txt", "x + 1")
    rhs = _write_expr(workspace, "rhs.txt", "y")
    edge = _edge(lhs=lhs, rhs=rhs)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.status == NOT_LOWERED
    assert result.residual_text == "(x + 1) - (y)"
    assert result.residual_path is None
    assert result.left == "x + 1"
    assert result.right == "y"
    assert result.status != ZERO


def test_inline_residual_text_is_executable(workspace):
    edge = _edge(residual="x**2 - y**2")
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.residual_text == "x**2 - y**2"
    assert result.residual_path is None
    assert result.status != ZERO


def test_residual_file_preferred_over_lhs_rhs(workspace):
    residual = _write_expr(workspace, "pair.txt", "a - b")
    lhs = _write_expr(workspace, "left.txt", "a + c")
    rhs = _write_expr(workspace, "right.txt", "b + c")
    edge = _edge(residual=residual, lhs=lhs, rhs=rhs)
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.residual_text == "a - b"
    assert result.residual_path == residual


def test_pairwise_reduction_requires_local_pair_residual(workspace):
    lhs = _write_expr(workspace, "sum_lhs.txt", "Sum(a(i) + a(j), (i, 1, n))")
    rhs = _write_expr(workspace, "sum_rhs.txt", "0")
    without = _edge(edge_type=PAIRWISE_REDUCTION, lhs=lhs, rhs=rhs)
    blocked = lower_edge(without, workspace, _ground(without))
    assert blocked.executable is False
    assert blocked.status == NOT_LOWERED
    assert blocked.residual_text is None
    assert "PAIRWISE_GLOBAL_SUM_NOT_LOCAL_RESIDUAL" in blocked.warnings

    residual = _write_expr(workspace, "pair_ij.txt", "a(i) + a(j)")
    with_pair = _edge(edge_type=PAIRWISE_REDUCTION, residual=residual)
    lowered = lower_edge(with_pair, workspace, _ground(with_pair))
    assert lowered.executable is True
    assert lowered.status == NOT_LOWERED
    assert lowered.residual_text == "a(i) + a(j)"
    assert lowered.status != ZERO


def test_completeness_reconstruction_with_residual_is_executable(workspace):
    residual = _write_expr(workspace, "complete.txt", "P - I")
    edge = _edge(
        edge_type=COMPLETENESS_RECONSTRUCTION,
        residual=residual,
        assumptions_used=("completeness",),
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.status == RECORDED
    assert result.residual_text == "P - I"
    assert result.status != ZERO


def test_special_function_identity_partial_needs_members(workspace):
    empty = _edge(edge_type=SPECIAL_FUNCTION_IDENTITY)
    blocked = lower_edge(empty, workspace, _ground(empty))
    assert blocked.executable is False
    assert blocked.status == NOT_LOWERED

    edge = _edge(
        edge_type=SPECIAL_FUNCTION_IDENTITY,
        lhs=_write_expr(workspace, "sf_lhs.txt", "sin(x)**2 + cos(x)**2"),
        rhs=_write_expr(workspace, "sf_rhs.txt", "1"),
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is True
    assert result.residual_text == "(sin(x)**2 + cos(x)**2) - (1)"
    assert result.status != ZERO


def test_global_symmetry_pairing_does_not_swallow_domain_sum(workspace):
    edge = _edge(
        edge_type=GLOBAL_SYMMETRY_PAIRING,
        lhs=_write_expr(workspace, "pair_sum_l.txt", "Sum(K(i, j), (i, 1, n))"),
        rhs=_write_expr(workspace, "pair_sum_r.txt", "0"),
    )
    result = lower_edge(edge, workspace, _ground(edge))
    assert result.executable is False
    assert result.status == NOT_LOWERED
    assert "GLOBAL_PAIRING_NOT_LOCAL_RESIDUAL" in result.warnings
