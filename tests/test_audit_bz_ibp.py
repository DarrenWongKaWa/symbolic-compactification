"""BZ-torus IBP adapter: local Leibniz ZERO + declared periodicity."""
from __future__ import annotations

from pathlib import Path

from symbolic_compactification.audit.evidence import (
    apply_bz_ibp_parent_statuses,
    load_declared_assumptions,
    verify_audit,
)
from symbolic_compactification.audit.schema import (
    ASSUMPTION_REQUIRED,
    BZ_PERIODIC_INTEGRATION_BY_PARTS,
    CERTIFIED_BY_RULE,
    NOT_LOWERED,
    TABLE_STRUCTURAL,
    TABLE_VERIFIED,
    ZERO,
    may_appear_in_verified_table,
    public_status_label,
    table_bucket,
)
from symbolic_compactification.audit.workspace import (
    initialize_audit_workspace,
    load_audit_workspace,
)
from symbolic_compactification.verifier import verify_equivalent


_LEIBNIZ = (
    "diff(u(k)*v(k), k) - (diff(u(k), k)*v(k) + u(k)*diff(v(k), k))"
)


def _write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_leibniz_product_rule_is_engine_zero():
    symbols = [{"name": "k", "real": True, "nonzero": False}]
    result = verify_equivalent(_LEIBNIZ, "0", symbols, functions=["u", "v"])
    assert result.verdict == "ZERO"


def test_certified_by_rule_never_enters_verified_table():
    from tests.test_audit_schema import _record
    record = _record(
        edge_id="ibp1",
        edge_type=BZ_PERIODIC_INTEGRATION_BY_PARTS,
        status=CERTIFIED_BY_RULE,
        result=CERTIFIED_BY_RULE,
        executable=False,
        residual_hash=None,
        obligation_hash=None,
        verifier_route=None,
        children=("local1",),
        required_rules=("BZ_TORUS_PERIODICITY",),
        ibp_domain="BRILLOUIN_ZONE_TORUS",
    )
    assert not may_appear_in_verified_table(record)
    assert table_bucket(record) == TABLE_STRUCTURAL
    assert public_status_label(record.status) != ZERO
    assert not public_status_label(record.status).startswith("ZERO")
    assert table_bucket(record) != TABLE_VERIFIED


def test_bz_ibp_requires_declared_periodicity(tmp_path: Path):
    root = initialize_audit_workspace(tmp_path / "ws").root
    _write(root, "assumptions/assumptions.yaml", (
        "symbols:\n"
        "  - name: k\n"
        "    real: true\n"
        "    nonzero: false\n"
        "functions:\n"
        "  - u\n"
        "  - v\n"
    ))
    _write(root, "expressions/leibniz.txt", _LEIBNIZ + "\n")
    _write(root, "edges/edges.yaml", f"""\
schema_version: DerivationAuditV1
edges:
  - edge_id: local.leibniz
    source_from: eq:placeholder
    source_to: eq:placeholder
    edge_type: ALGEBRAIC_EQUIVALENCE
    residual: expressions/leibniz.txt
    assumptions_used: [k]
    claim: "Leibniz product rule"
  - edge_id: parent.ibp
    source_from: eq:placeholder
    source_to: eq:placeholder
    edge_type: BZ_PERIODIC_INTEGRATION_BY_PARTS
    children: [local.leibniz]
    ibp_domain: BRILLOUIN_ZONE_TORUS
    required_rules: [BZ_TORUS_PERIODICITY]
    assumptions_used: []
    claim: "BZ IBP without declared periodicity"
""")
    run = verify_audit(load_audit_workspace(root))
    by_id = {record.edge_id: record for record in run.records}
    assert by_id["local.leibniz"].status == ZERO
    assert by_id["parent.ibp"].status == ASSUMPTION_REQUIRED
    assert not may_appear_in_verified_table(by_id["parent.ibp"])


def test_bz_ibp_certified_by_rule_when_periodicity_declared(tmp_path: Path):
    root = initialize_audit_workspace(tmp_path / "ws2").root
    _write(root, "assumptions/assumptions.yaml", (
        "symbols:\n"
        "  - name: k\n"
        "    real: true\n"
        "    nonzero: false\n"
        "functions:\n"
        "  - u\n"
        "  - v\n"
        "rules:\n"
        "  - BZ_TORUS_PERIODICITY\n"
    ))
    _write(root, "expressions/leibniz.txt", _LEIBNIZ + "\n")
    _write(root, "edges/edges.yaml", f"""\
schema_version: DerivationAuditV1
edges:
  - edge_id: local.leibniz
    source_from: eq:placeholder
    source_to: eq:placeholder
    edge_type: ALGEBRAIC_EQUIVALENCE
    residual: expressions/leibniz.txt
    assumptions_used: [k]
    claim: "Leibniz product rule"
  - edge_id: parent.ibp
    source_from: eq:placeholder
    source_to: eq:placeholder
    edge_type: BZ_PERIODIC_INTEGRATION_BY_PARTS
    children: [local.leibniz]
    ibp_domain: BRILLOUIN_ZONE_TORUS
    required_rules: [BZ_TORUS_PERIODICITY]
    assumptions_used: []
    claim: "BZ IBP with declared torus periodicity"
""")
    run = verify_audit(load_audit_workspace(root))
    by_id = {record.edge_id: record for record in run.records}
    assert by_id["local.leibniz"].result == ZERO
    parent = by_id["parent.ibp"]
    assert parent.status == CERTIFIED_BY_RULE
    assert parent.result == CERTIFIED_BY_RULE
    assert parent.executable is False
    assert not may_appear_in_verified_table(parent)
    assert table_bucket(parent) == TABLE_STRUCTURAL
    assert parent.rule_certificate is not None
    cert = parent.rule_certificate.to_dict()
    assert cert["rule_id"] == "BZ_TORUS_PERIODICITY"
    assert cert["requirements"]["domain"] == "BRILLOUIN_ZONE_TORUS"
    assert cert["conclusion"] == "integral_of_total_derivative = 0"
    assert cert["result"] == CERTIFIED_BY_RULE
    assert cert["local_children"] == [
        {"edge_id": "local.leibniz", "status": ZERO},
    ]


def test_bz_ibp_not_lowered_without_local_child(tmp_path: Path):
    root = initialize_audit_workspace(tmp_path / "ws3").root
    _write(root, "assumptions/assumptions.yaml", (
        "symbols:\n"
        "  - name: k\n"
        "    real: true\n"
        "    nonzero: false\n"
        "functions: []\n"
        "rules:\n"
        "  - BZ_TORUS_PERIODICITY\n"
    ))
    _write(root, "edges/edges.yaml", """\
schema_version: DerivationAuditV1
edges:
  - edge_id: parent.ibp
    source_from: eq:placeholder
    source_to: eq:placeholder
    edge_type: BZ_PERIODIC_INTEGRATION_BY_PARTS
    children: []
    ibp_domain: BRILLOUIN_ZONE_TORUS
    required_rules: [BZ_TORUS_PERIODICITY]
    assumptions_used: []
    claim: "IBP with no local child"
""")
    run = verify_audit(load_audit_workspace(root))
    parent = run.records[0]
    assert parent.status == NOT_LOWERED
    assert not may_appear_in_verified_table(parent)
