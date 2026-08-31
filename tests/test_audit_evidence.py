"""Evidence-store tests for derivation-audit v0.2.

Helpers are tested even when edge/lowering siblings are still stubs.
Full ``verify_audit`` orchestration is exercised through local fakes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import symbolic_compactification.audit.edges as edges_mod
import symbolic_compactification.audit.lowering as lowering_mod
from symbolic_compactification.audit.edges import AuditEdge, GroundingResult
from symbolic_compactification.audit.evidence import (
    AUDIT_PROVENANCE_SCHEMA_VERSION,
    MACHINE_RECORDS_FILE,
    apply_split_parent_statuses,
    assumption_gate_status,
    adjudicate_lowered_edge,
    bind_hashes,
    compile_and_verify_residual,
    latest_audit_run_id,
    load_audit_run,
    load_declared_assumptions,
    persist_audit_run,
    snapshot_audit_sources,
    verify_audit,
    write_exclusive_audit_run,
)
from symbolic_compactification.audit.lowering import LoweringResult
from symbolic_compactification.audit.schema import (
    ALGEBRAIC_EQUIVALENCE,
    ASSUMPTION_REQUIRED,
    ASYMPTOTIC_CLAIM,
    CERTIFIED_BY_CHILDREN,
    COMPILE_FAILURE,
    LOWERING_SUPPORTED,
    NONZERO,
    NOT_LOWERED,
    PARSE_FAILURE,
    SPLIT,
    SPLIT_PARENT,
    UNKNOWN,
    ZERO,
    AuditError,
    AuditRecord,
    integrity_ok,
    may_appear_in_verified_table,
    record_from_mapping,
)
from symbolic_compactification.audit.workspace import (
    initialize_audit_workspace,
    load_audit_workspace,
)
from symbolic_compactification.models import ENGINE_VERSION
from symbolic_compactification.provenance import PROVENANCE_FILE_NAME

_HASH_A = "a" * 64
_HASH_B = "b" * 64
_HASH_C = "c" * 64


def _source_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
        and "runs" not in path.relative_to(root).parts
        and "reports" not in path.relative_to(root).parts
    }


def _edge(**overrides) -> AuditEdge:
    base = dict(
        edge_id="E001",
        source_from="eq:a",
        source_to="eq:b",
        edge_type=ALGEBRAIC_EQUIVALENCE,
        assumptions_used=("x",),
        claim="eq:a equals eq:b",
    )
    base.update(overrides)
    return AuditEdge(**base)


def _ground(edge: AuditEdge, *, ok: bool = True, status: str = "GROUNDED") -> GroundingResult:
    return GroundingResult(
        edge=edge,
        ok=ok,
        status=status if ok else "GROUNDING_FAILURE",
        issues=() if ok else ("UNGROUNDED",),
        source_refs=tuple(item for item in (edge.source_from, edge.source_to) if item),
        source_snapshot_hash=_HASH_A,
    )


def _lower(edge: AuditEdge, **overrides) -> LoweringResult:
    base = dict(
        edge_id=edge.edge_id,
        executable=True,
        status=NOT_LOWERED,
        residual_text="x - x",
        residual_path=None,
        obligation_id="obl-1",
        left=None,
        right=None,
        warnings=(),
        applicability=LOWERING_SUPPORTED,
    )
    base.update(overrides)
    return LoweringResult(**base)


def _record(**overrides) -> AuditRecord:
    base = dict(
        audit_id="audit1",
        edge_id="E001",
        source_refs=("eq:a", "eq:b"),
        edge_type=ALGEBRAIC_EQUIVALENCE,
        status=ZERO,
        result=ZERO,
        source_snapshot_hash=_HASH_A,
        engine_version=ENGINE_VERSION,
        runtime_seconds=0.01,
        lhs_hash=_HASH_B,
        rhs_hash=_HASH_C,
        residual_hash=_HASH_A,
        assumptions_hash=_HASH_B,
        obligation_hash=_HASH_C,
        verifier_route="python_sympy_exact_v1",
        executable=True,
        claim="a - b",
        residual_text="a - b",
    )
    base.update(overrides)
    return AuditRecord(**base)


def _install_fakes(monkeypatch, loaded_edges):
    by_id = {edge.edge_id: edge for edge in loaded_edges}

    def fake_load(_workspace):
        return tuple(loaded_edges)

    def fake_ground(edge, _workspace):
        return _ground(by_id[edge.edge_id])

    def fake_lower(edge, _workspace, _grounding):
        residual = edge.residual or "x - x"
        path = residual if residual.startswith("expressions/") else None
        text = None if path else residual
        executable = edge.edge_type not in {SPLIT_PARENT, ASYMPTOTIC_CLAIM}
        if edge.edge_type == ASYMPTOTIC_CLAIM:
            executable = True
            text = edge.residual or "x - x"
            path = None
        if edge.edge_type == SPLIT_PARENT:
            executable = False
            text = None
        return _lower(
            edge,
            executable=executable,
            residual_text=text,
            residual_path=path,
            left=edge.lhs,
            right=edge.rhs,
            status=SPLIT if edge.edge_type == SPLIT_PARENT else NOT_LOWERED,
        )

    monkeypatch.setattr(edges_mod, "load_edges", fake_load)
    monkeypatch.setattr(edges_mod, "ground_edge", fake_ground)
    monkeypatch.setattr(lowering_mod, "lower_edge", fake_lower)


def test_bind_hashes_change_when_residual_bytes_change():
    first = bind_hashes(
        residual_bytes=b"x - x\n",
        assumptions_hash=_HASH_A,
        source_snapshot_hash=_HASH_B,
        edge_id="E001",
        edge_type=ALGEBRAIC_EQUIVALENCE,
        declared_assumptions=("x",),
    )
    second = bind_hashes(
        residual_bytes=b"x-x\n",
        assumptions_hash=_HASH_A,
        source_snapshot_hash=_HASH_B,
        edge_id="E001",
        edge_type=ALGEBRAIC_EQUIVALENCE,
        declared_assumptions=("x",),
    )
    assert first.residual_hash != second.residual_hash
    assert first.obligation_hash != second.obligation_hash
    assert first.assumptions_hash == second.assumptions_hash
    assert len(first.obligation_hash) == 64


def test_bind_hashes_change_when_assumptions_or_snapshot_or_engine_change():
    base = dict(
        residual_bytes=b"x - x\n",
        assumptions_hash=_HASH_A,
        source_snapshot_hash=_HASH_B,
        edge_id="E001",
        edge_type=ALGEBRAIC_EQUIVALENCE,
    )
    original = bind_hashes(**base)
    assumptions = bind_hashes(**{**base, "assumptions_hash": _HASH_C})
    snapshot = bind_hashes(**{**base, "source_snapshot_hash": _HASH_C})
    engine = bind_hashes(**{**base, "engine_version": "not-the-same-engine"})
    assert original.obligation_hash != assumptions.obligation_hash
    assert original.obligation_hash != snapshot.obligation_hash
    assert original.obligation_hash != engine.obligation_hash


def test_exclusive_run_write_never_overwrites(tmp_path):
    runs = tmp_path / "runs"
    record = _record()
    provenance = {
        "schema_version": AUDIT_PROVENANCE_SCHEMA_VERSION,
        "run_id": "run-1",
        "audit_id": "audit1",
        "writer": "symbolic_compactification.audit.evidence",
    }
    first = write_exclusive_audit_run(runs, "run-1", (record,), provenance)
    payload = (first / MACHINE_RECORDS_FILE).read_bytes()
    provenance_bytes = (first / PROVENANCE_FILE_NAME).read_bytes()
    with pytest.raises(AuditError) as exc:
        write_exclusive_audit_run(runs, "run-1", (record,), provenance)
    assert exc.value.code == "RUN_ALREADY_EXISTS"
    assert (first / MACHINE_RECORDS_FILE).read_bytes() == payload
    assert (first / PROVENANCE_FILE_NAME).read_bytes() == provenance_bytes
    loaded = json.loads(payload.decode("utf-8"))
    assert isinstance(loaded, list)
    assert loaded[0]["edge_id"] == "E001"


def test_residual_file_byte_change_invalidates_snapshot_and_obligation(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "paper")
    residual = workspace.root / "expressions" / "residual.txt"
    residual.write_bytes(b"x - x\n")
    before = snapshot_audit_sources(workspace)
    bound_before = bind_hashes(
        residual_bytes=residual.read_bytes(),
        assumptions_hash=before.mapping()["assumptions/assumptions.yaml"],
        source_snapshot_hash=before.source_snapshot_hash,
        edge_id="E001",
        edge_type=ALGEBRAIC_EQUIVALENCE,
    )
    residual.write_bytes(b"x-x\n")
    after = snapshot_audit_sources(workspace)
    bound_after = bind_hashes(
        residual_bytes=residual.read_bytes(),
        assumptions_hash=after.mapping()["assumptions/assumptions.yaml"],
        source_snapshot_hash=after.source_snapshot_hash,
        edge_id="E001",
        edge_type=ALGEBRAIC_EQUIVALENCE,
    )
    assert before.source_snapshot_hash != after.source_snapshot_hash
    assert bound_before.residual_hash != bound_after.residual_hash
    assert bound_before.obligation_hash != bound_after.obligation_hash
    assert bound_before.source_snapshot_hash != bound_after.source_snapshot_hash


def test_forged_zero_dict_missing_hashes_fails_integrity():
    forged = _record(
        residual_hash=None,
        obligation_hash=None,
        assumptions_hash=None,
        verifier_route=None,
    ).to_dict()
    loaded = record_from_mapping(forged)
    assert not integrity_ok(loaded)
    assert not may_appear_in_verified_table(loaded)


def test_assumption_gate_missing_declared_names():
    assert assumption_gate_status(("x",), ()) is None
    assert assumption_gate_status(("x", "y"), ("x",)) is None
    assert assumption_gate_status(("x",), ("x",)) is None
    assert assumption_gate_status(("x",), ("y",)) == ASSUMPTION_REQUIRED


def test_real_false_assumptions_are_rejected(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "complex")
    path = workspace.root / "assumptions" / "assumptions.yaml"
    path.write_text(
        "symbols:\n"
        "  - name: z\n"
        "    real: false\n"
        "    nonzero: false\n"
        "functions: []\n",
        encoding="utf-8",
    )
    loaded = load_audit_workspace(workspace.root)
    with pytest.raises(AuditError) as exc:
        load_declared_assumptions(loaded)
    assert exc.value.code == "UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS"


def test_compile_and_verify_residual_zero_nonzero_and_parse_failure():
    zero_status, zero = compile_and_verify_residual(
        residual_text="x - x", symbols=["x"])
    assert zero_status == ZERO
    assert zero is not None and zero.verdict == ZERO
    lhs_status, _ = compile_and_verify_residual(
        left="(x + 1)**2", right="x**2 + 2*x + 1", symbols=["x"])
    assert lhs_status == ZERO
    nonzero_status, nonzero = compile_and_verify_residual(
        residual_text="x + 1", symbols=["x"])
    assert nonzero_status == NONZERO
    assert nonzero is not None and nonzero.counterexample is not None
    parse_status, _ = compile_and_verify_residual(
        residual_text="y", symbols=["x"])
    assert parse_status == PARSE_FAILURE
    missing_status, missing = compile_and_verify_residual(symbols=["x"])
    assert missing_status == COMPILE_FAILURE
    assert missing is None


def test_fake_lowering_path_certifies_zero_and_refutes_nonzero(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "fake")
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    zero_edge = _edge(residual="x - x")
    zero = adjudicate_lowered_edge(
        zero_edge, workspace, _ground(zero_edge), _lower(zero_edge),
        snapshot=snapshot, assumptions=assumptions)
    assert zero.status == ZERO
    assert zero.result == ZERO
    assert zero.executable
    assert integrity_ok(zero)
    assert may_appear_in_verified_table(zero)
    nonzero_edge = _edge(edge_id="E002", residual="x + 1")
    nonzero = adjudicate_lowered_edge(
        nonzero_edge, workspace, _ground(nonzero_edge),
        _lower(nonzero_edge, residual_text="x + 1"),
        snapshot=snapshot, assumptions=assumptions)
    assert nonzero.status == NONZERO
    assert not may_appear_in_verified_table(nonzero)


def test_undeclared_assumption_name_is_assumption_required(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "gate")
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    edge = _edge(assumptions_used=("y",))
    record = adjudicate_lowered_edge(
        edge, workspace, _ground(edge), _lower(edge),
        snapshot=snapshot, assumptions=assumptions)
    assert record.status == ASSUMPTION_REQUIRED
    assert record.result == ASSUMPTION_REQUIRED
    assert not record.executable
    assert not may_appear_in_verified_table(record)


def test_asymptotic_claim_never_engine_zero_without_remainder_certificate(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "asym")
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    edge = _edge(edge_id="A001", edge_type=ASYMPTOTIC_CLAIM, residual="x - x")
    record = adjudicate_lowered_edge(
        edge, workspace, _ground(edge),
        _lower(edge, residual_text="x - x", executable=True),
        snapshot=snapshot, assumptions=assumptions)
    assert record.status != ZERO
    assert record.result != ZERO
    assert record.status == UNKNOWN
    assert not may_appear_in_verified_table(record)


def test_split_parent_status_follows_children_and_is_never_engine_zero(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "split")
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    child_a = _edge(edge_id="C1", residual="x - x")
    child_b = _edge(edge_id="C2", residual="x - x")
    parent = _edge(
        edge_id="P1", edge_type=SPLIT_PARENT, children=("C1", "C2"),
        residual=None, assumptions_used=())
    rec_a = adjudicate_lowered_edge(
        child_a, workspace, _ground(child_a), _lower(child_a),
        snapshot=snapshot, assumptions=assumptions)
    rec_b = adjudicate_lowered_edge(
        child_b, workspace, _ground(child_b), _lower(child_b),
        snapshot=snapshot, assumptions=assumptions)
    rec_p = adjudicate_lowered_edge(
        parent, workspace, _ground(parent),
        _lower(parent, executable=False, residual_text=None, status=SPLIT),
        snapshot=snapshot, assumptions=assumptions)
    assert rec_p.status == SPLIT
    certified = apply_split_parent_statuses((rec_p, rec_a, rec_b))
    parent_rec = next(item for item in certified if item.edge_id == "P1")
    assert parent_rec.status == CERTIFIED_BY_CHILDREN
    assert parent_rec.result == CERTIFIED_BY_CHILDREN
    assert parent_rec.result != ZERO
    assert parent_rec.status != ZERO
    rec_b_bad = adjudicate_lowered_edge(
        child_b, workspace, _ground(child_b),
        _lower(child_b, residual_text="x + 1"),
        snapshot=snapshot, assumptions=assumptions)
    blocked = apply_split_parent_statuses((rec_p, rec_a, rec_b_bad))
    blocked_parent = next(item for item in blocked if item.edge_id == "P1")
    assert blocked_parent.status == SPLIT


def test_verify_audit_with_fake_layers_persists_exclusive_run(tmp_path, monkeypatch):
    workspace = initialize_audit_workspace(tmp_path / "orch")
    residual = workspace.root / "expressions" / "residual.txt"
    residual.write_text("x - x\n", encoding="utf-8")
    before = _source_bytes(workspace.root)
    edges = (
        _edge(residual="expressions/residual.txt"),
        _edge(edge_id="E002", residual="x + 1"),
        _edge(
            edge_id="A001", edge_type=ASYMPTOTIC_CLAIM, residual="x - x",
            children=("E001",),
        ),
        _edge(
            edge_id="P1", edge_type=SPLIT_PARENT, children=("E001",),
            residual=None, assumptions_used=(),
        ),
    )
    _install_fakes(monkeypatch, edges)
    run = verify_audit(
        workspace, run_id="orch-run", timestamp="2026-09-01T00:00:00Z")
    assert run.run_id == "orch-run"
    assert (run.directory / MACHINE_RECORDS_FILE).is_file()
    assert (run.directory / PROVENANCE_FILE_NAME).is_file()
    by_id = {record.edge_id: record for record in run.records}
    assert by_id["E001"].status == ZERO
    assert integrity_ok(by_id["E001"])
    assert may_appear_in_verified_table(by_id["E001"])
    assert by_id["E002"].status == NONZERO
    assert by_id["A001"].status == UNKNOWN
    assert by_id["P1"].status == CERTIFIED_BY_CHILDREN
    assert by_id["P1"].result != ZERO
    loaded = load_audit_run(workspace, "orch-run")
    assert loaded.run_id == run.run_id
    assert [item.edge_id for item in loaded.records] == [
        item.edge_id for item in run.records]
    assert latest_audit_run_id(workspace) == "orch-run"
    assert _source_bytes(workspace.root) == before
    with pytest.raises(AuditError) as exc:
        verify_audit(workspace, run_id="orch-run")
    assert exc.value.code == "RUN_ALREADY_EXISTS"
    assert _source_bytes(workspace.root) == before


def test_persist_and_latest_run_order(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "order")
    snapshot = snapshot_audit_sources(workspace)
    assumptions = load_declared_assumptions(workspace)
    edge = _edge()
    record = adjudicate_lowered_edge(
        edge, workspace, _ground(edge), _lower(edge),
        snapshot=snapshot, assumptions=assumptions)
    first = persist_audit_run(
        workspace, (record,), snapshot=snapshot, assumptions=assumptions,
        run_id="20260901T000000Z-aaaa", timestamp="2026-09-01T00:00:00Z")
    second = persist_audit_run(
        workspace, (record,), snapshot=snapshot, assumptions=assumptions,
        run_id="20260901T000001Z-bbbb", timestamp="2026-09-01T00:00:01Z")
    assert latest_audit_run_id(workspace) == second.run_id
    assert load_audit_run(workspace, first.run_id).records[0].status == ZERO


def test_latest_audit_run_id_without_runs(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "empty")
    with pytest.raises(AuditError) as exc:
        latest_audit_run_id(workspace)
    assert exc.value.code == "NO_RECORDED_RUNS"


def test_verify_audit_calls_sibling_layers_or_is_stubbed(tmp_path):
    workspace = initialize_audit_workspace(tmp_path / "stub")
    before = _source_bytes(workspace.root)
    try:
        run = verify_audit(workspace)
    except AuditError as exc:
        if exc.code == "NOT_IMPLEMENTED":
            assert _source_bytes(workspace.root) == before
            return
        raise
    assert run.directory.is_dir()
    assert (run.directory / MACHINE_RECORDS_FILE).is_file()
    assert _source_bytes(workspace.root) == before
