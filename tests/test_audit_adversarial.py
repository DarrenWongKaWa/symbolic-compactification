"""Anti-hallucination attacks: LLM text cannot create verified status."""
from __future__ import annotations

from symbolic_compactification.audit.schema import (
    ASYMPTOTIC_CLAIM,
    CERTIFIED_BY_CHILDREN,
    NONZERO,
    SPLIT,
    SPLIT_PARENT,
    UNKNOWN,
    ZERO,
    AuditRecord,
    derive_split_parent_status,
    integrity_ok,
    may_appear_in_verified_table,
    table_bucket,
)

_H = {
    "A": "a" * 64,
    "B": "b" * 64,
    "C": "c" * 64,
    "D": "d" * 64,
    "E": "e" * 64,
}


def _zero(**overrides) -> AuditRecord:
    data = dict(
        audit_id="audit",
        edge_id="E001",
        source_refs=("eq:a",),
        edge_type="ALGEBRAIC_EQUIVALENCE",
        status=ZERO,
        result=ZERO,
        source_snapshot_hash=_H["A"],
        engine_version="0.3.0",
        runtime_seconds=0.0,
        lhs_hash=_H["B"],
        rhs_hash=_H["C"],
        residual_hash=_H["D"],
        assumptions_hash=_H["E"],
        obligation_hash=_H["A"],
        verifier_route="python_sympy_exact_v1",
        executable=True,
        claim="lhs - rhs",
        residual_text="lhs - rhs",
    )
    data.update(overrides)
    return AuditRecord(**data)


def test_a_markdown_zero_without_machine_evidence_is_not_verified():
    """A. LLM writes ZERO into Markdown: no AuditRecord => not included."""
    records = ()
    verified_ids = [r.edge_id for r in records if may_appear_in_verified_table(r)]
    assert "LLM_FORGED" not in verified_ids
    assert verified_ids == []


def test_b_forged_zero_json_without_obligation_hash_is_invalid():
    forged = _zero(obligation_hash=None, residual_hash=None)
    assert not integrity_ok(forged)
    assert not may_appear_in_verified_table(forged)


def test_c_residual_bytes_change_breaks_record_identity():
    original = _zero()
    mutated = _zero(residual_hash="f" * 64, residual_text="lhs - rhs + 1")
    assert original.residual_hash != mutated.residual_hash
    assert original.to_dict() != mutated.to_dict()


def test_d_assumption_hash_change_breaks_record_identity():
    original = _zero()
    mutated = _zero(assumptions_hash="f" * 64)
    assert original.assumptions_hash != mutated.assumptions_hash


def test_e_source_snapshot_change_breaks_record_identity():
    original = _zero()
    mutated = _zero(source_snapshot_hash="f" * 64)
    assert original.source_snapshot_hash != mutated.source_snapshot_hash
    assert may_appear_in_verified_table(original)
    assert may_appear_in_verified_table(mutated)
    assert original.source_snapshot_hash != mutated.source_snapshot_hash


def test_f_unknown_cannot_be_relabeled_zero_without_engine_zero():
    unknown = _zero(status=ZERO, result=UNKNOWN)
    assert not integrity_ok(unknown)
    assert not may_appear_in_verified_table(unknown)


def test_g_nonzero_is_never_in_verified_table():
    record = _zero(status=NONZERO, result=NONZERO)
    assert table_bucket(record) == "TABLE_NONZERO"
    assert not may_appear_in_verified_table(record)


def test_h_split_parent_with_uncertified_child_cannot_certify():
    parent = _zero(
        edge_id="P",
        edge_type=SPLIT_PARENT,
        status=SPLIT,
        result=SPLIT,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
        children=("C1", "C2"),
    )
    child_zero = _zero(edge_id="C1")
    child_unknown = _zero(edge_id="C2", status=UNKNOWN, result=UNKNOWN)
    assert derive_split_parent_status(
        parent, {"C1": child_zero, "C2": child_unknown}) == SPLIT
    both = derive_split_parent_status(
        parent, {"C1": child_zero, "C2": _zero(edge_id="C2")})
    assert both == CERTIFIED_BY_CHILDREN
    assert both != ZERO


def test_asymptotic_unknown_stays_out_of_verified_table():
    record = _zero(
        edge_id="ASYM",
        edge_type=ASYMPTOTIC_CLAIM,
        status=UNKNOWN,
        result=UNKNOWN,
    )
    assert not may_appear_in_verified_table(record)
    assert table_bucket(record) == "TABLE_UNCERTIFIED"
