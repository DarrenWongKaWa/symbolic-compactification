"""Derivation audit layer (v0.2). Additive to the v0.1 workspace API.

Verified table rows are generated from machine records only. LLM text cannot
create ZERO / VERIFIED / CERTIFIED status.
"""
from .schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    ASYMPTOTIC_CLAIM,
    AUDIT_SCHEMA_VERSION,
    AuditError,
    AuditRecord,
    CERTIFIED_BY_CHILDREN,
    DEFINITION,
    EDGE_TYPES,
    NONZERO,
    NOT_LOWERED,
    RECORDED,
    SPLIT,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    UNKNOWN,
    ZERO,
    derive_split_parent_status,
    integrity_ok,
    may_appear_in_verified_table,
    table_bucket,
)
from .workspace import (
    AuditWorkspace,
    initialize_audit_workspace,
    load_audit_workspace,
)

__all__ = [
    "APPROVED_CAVEAT",
    "APPROVED_MACHINE_CLAIM",
    "ASYMPTOTIC_CLAIM",
    "AUDIT_SCHEMA_VERSION",
    "AuditError",
    "AuditRecord",
    "AuditWorkspace",
    "CERTIFIED_BY_CHILDREN",
    "DEFINITION",
    "EDGE_TYPES",
    "NONZERO",
    "NOT_LOWERED",
    "RECORDED",
    "SPLIT",
    "TABLE_NONZERO",
    "TABLE_STRUCTURAL",
    "TABLE_UNCERTIFIED",
    "TABLE_VERIFIED",
    "UNKNOWN",
    "ZERO",
    "derive_split_parent_status",
    "initialize_audit_workspace",
    "integrity_ok",
    "load_audit_workspace",
    "may_appear_in_verified_table",
    "table_bucket",
]
