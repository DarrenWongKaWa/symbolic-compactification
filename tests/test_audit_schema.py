"""Interface-freeze tests for derivation-audit status and table rules."""
from __future__ import annotations

from symbolic_compactification.audit.schema import (
    ASYMPTOTIC_CLAIM,
    AUDIT_STATUSES,
    CERTIFIED_BY_CHILDREN,
    DEFINITION,
    EDGE_TYPES,
    NONZERO,
    NOT_LOWERED,
    RECORDED,
    SPLIT,
    SPLIT_PARENT,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    UNKNOWN,
    ZERO,
    AuditRecord,
    derive_split_parent_status,
    integrity_issues,
    may_appear_in_verified_table,
    public_status_label,
    table_bucket,
)

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64
_HASH_D = "d" * 64
_HASH_E = "e" * 64


def _record(**overrides) -> AuditRecord:
    base = dict(
        audit_id="audit1",
        edge_id="E001",
        source_refs=("eq:a", "eq:b"),
        edge_type="ALGEBRAIC_EQUIVALENCE",
        status=ZERO,
        result=ZERO,
        source_snapshot_hash=_HASH_A,
        engine_version="0.3.0",
        runtime_seconds=0.01,
        lhs_hash=_HASH_B,
        rhs_hash=_HASH_C,
        residual_hash=_HASH_D,
        assumptions_hash=_HASH_E,
        obligation_hash=_HASH_A,
        verifier_route="python_sympy_exact_v1",
        executable=True,
        claim="a - b",
        residual_text="a - b",
    )
    base.update(overrides)
    return AuditRecord(**base)


def test_required_statuses_and_edge_types_are_frozen():
    for name in (
            "ZERO", "NONZERO", "UNKNOWN", "ASSUMPTION_REQUIRED",
            "DEFINITION", "RECORDED", "SPLIT", "NOT_LOWERED",
            "PARSE_FAILURE", "GROUNDING_FAILURE", "COMPILE_FAILURE",
            "INVALID_RECORD"):
        assert name in AUDIT_STATUSES
    assert CERTIFIED_BY_CHILDREN in AUDIT_STATUSES
    assert "CERTIFIED_BY_RULE" in AUDIT_STATUSES
    assert "ALGEBRAIC_EQUIVALENCE" in EDGE_TYPES
    assert "ASYMPTOTIC_CLAIM" in EDGE_TYPES
    assert "BZ_PERIODIC_INTEGRATION_BY_PARTS" in EDGE_TYPES
    assert "PAIRWISE_REDUCTION" in EDGE_TYPES
    assert "COMPLETENESS_RECONSTRUCTION" in EDGE_TYPES


def test_zero_executable_record_enters_verified_table_only():
    record = _record()
    assert integrity_issues(record) == ()
    assert may_appear_in_verified_table(record)
    assert table_bucket(record) == TABLE_VERIFIED


def test_forged_zero_without_hashes_is_rejected():
    forged = _record(
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
    )
    assert "RESIDUAL_HASH_REQUIRED" in integrity_issues(forged)
    assert not may_appear_in_verified_table(forged)
    assert table_bucket(forged) == TABLE_UNCERTIFIED


def test_nonzero_never_enters_verified_table():
    record = _record(status=NONZERO, result=NONZERO)
    assert table_bucket(record) == TABLE_NONZERO
    assert not may_appear_in_verified_table(record)


def test_definition_and_recorded_are_structural_not_failures():
    definition = _record(
        edge_id="D001",
        edge_type="DEFINITION_INSERTION",
        status=DEFINITION,
        result=DEFINITION,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
        lhs_hash=None,
        rhs_hash=None,
    )
    recorded = _record(
        edge_id="R001",
        edge_type="BOOKKEEPING",
        status=RECORDED,
        result=RECORDED,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
    )
    assert table_bucket(definition) == TABLE_STRUCTURAL
    assert table_bucket(recorded) == TABLE_STRUCTURAL
    assert not may_appear_in_verified_table(definition)


def test_asymptotic_claim_cannot_be_zero_without_remainder_certificate():
    claim = _record(
        edge_id="A001",
        edge_type=ASYMPTOTIC_CLAIM,
        status=ZERO,
        result=ZERO,
        remainder_certificate_hash=None,
    )
    issues = integrity_issues(claim)
    assert "ASYMPTOTIC_ZERO_WITHOUT_REMAINDER_CERTIFICATE" in issues
    assert not may_appear_in_verified_table(claim)
    unknown = _record(
        edge_id="A001",
        edge_type=ASYMPTOTIC_CLAIM,
        status=UNKNOWN,
        result=UNKNOWN,
        executable=True,
    )
    assert table_bucket(unknown) == TABLE_UNCERTIFIED


def test_coefficient_zero_does_not_certify_enclosing_asymptotic():
    coefficient = _record(edge_id="C0", edge_type="LAURENT_COEFFICIENT")
    parent = _record(
        edge_id="ASYM",
        edge_type=ASYMPTOTIC_CLAIM,
        status=UNKNOWN,
        result=UNKNOWN,
        executable=True,
        children=("C0",),
    )
    assert may_appear_in_verified_table(coefficient)
    assert table_bucket(parent) == TABLE_UNCERTIFIED


def test_split_parent_cannot_be_engine_zero_and_needs_all_children():
    child = _record(edge_id="C12")
    parent = _record(
        edge_id="E008",
        edge_type=SPLIT_PARENT,
        status=SPLIT,
        result=SPLIT,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
        children=("C12", "C13"),
    )
    assert "SPLIT_PARENT_CANNOT_BE_ENGINE_ZERO" in integrity_issues(
        _record(edge_id="E008", edge_type=SPLIT_PARENT, status=ZERO, result=ZERO)
    )
    assert derive_split_parent_status(parent, {"C12": child}) == SPLIT
    certified = derive_split_parent_status(
        parent, {"C12": child, "C13": _record(edge_id="C13")})
    assert certified == CERTIFIED_BY_CHILDREN
    unknown_child = _record(edge_id="C13", status=UNKNOWN, result=UNKNOWN)
    assert derive_split_parent_status(
        parent, {"C12": child, "C13": unknown_child}) == SPLIT
    display = public_status_label(CERTIFIED_BY_CHILDREN)
    assert display.startswith("SPLIT")
    assert "ZERO" not in display


def test_not_lowered_is_uncertified_not_unknown_overload():
    record = _record(
        edge_id="N1",
        status=NOT_LOWERED,
        result=NOT_LOWERED,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
    )
    assert table_bucket(record) == TABLE_UNCERTIFIED
    assert record.status != UNKNOWN
