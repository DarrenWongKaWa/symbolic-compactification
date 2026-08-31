"""Human-readable audit REPORT.md. E6 implements generation.

Machine claims in the report must be copied from the evidence store. Narrative
explanations are non-authoritative.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .evidence import AuditRun
from .schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    ASYMPTOTIC_CLAIM,
    AUDIT_PROTOCOL_VERSION,
    AUDIT_SCHEMA_VERSION,
    CERTIFIED_BY_CHILDREN,
    INTEGRAL_ARGUMENT,
    LIMIT_CLAIM,
    NONZERO_REVIEWER_TEXT,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    AuditRecord,
    integrity_issues,
    public_status_label,
)
from .tables import (
    NONZERO_TABLE_TITLE,
    TABLE_ORDER,
    bucket_records,
    render_markdown_table,
    write_reports_text,
)
from .workspace import AuditWorkspace

REPORT_FILENAME = "REPORT.md"

_SPECIAL_UNVERIFIED_TYPES = frozenset({
    ASYMPTOTIC_CLAIM, INTEGRAL_ARGUMENT, LIMIT_CLAIM,
})


def generate_audit_report(workspace: AuditWorkspace, run: AuditRun) -> Path:
    """Write reports/REPORT.md from machine evidence only."""
    buckets = bucket_records(run.records)
    text = _render_report(workspace, run, buckets)
    return write_reports_text(workspace, REPORT_FILENAME, text)


def _render_report(
    workspace: AuditWorkspace,
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> str:
    lines: list[str] = [
        "# Derivation Audit Report",
        "",
        "Narrative is non-authoritative; machine numbers come from records.",
        "Markdown cannot create ZERO, VERIFIED, or CERTIFIED status.",
        "",
        "## Scope",
        "",
        f"- Schema version: `{AUDIT_SCHEMA_VERSION}`",
        f"- Protocol version: `{AUDIT_PROTOCOL_VERSION}`",
        f"- Audit name: `{workspace.config.audit_name}`",
        f"- Audit id: `{run.audit_id}`",
        f"- Run id: `{run.run_id}`",
        f"- Record count: `{len(run.records)}`",
        f"- Verifier profile: `{workspace.config.verifier_profile}`",
        "",
        "## Declared semantics",
        "",
        APPROVED_MACHINE_CLAIM,
        "",
        "- ZERO is exact symbolic simplification of an executable residual "
        "to 0 under the declared namespace.",
        "- NONZERO is an exact probe proving the residual is not 0.",
        "- UNKNOWN and other non-ZERO statuses are not machine-verified.",
        "- Split parents are never engine ZERO; CERTIFIED_BY_CHILDREN is "
        "displayed as "
        f"`{public_status_label(CERTIFIED_BY_CHILDREN)}` "
        "and is never displayed as ZERO.",
        "- Verified-table inclusion uses `schema.may_appear_in_verified_table` "
        "only. Other tables use `schema.table_bucket`.",
        "- VERIFIED TABLE IS GENERATED, NOT AUTHORED.",
        "",
        "## Source snapshot",
        "",
        _kv("config_sha256", workspace.config_sha256),
        _kv("manuscript_sha256", workspace.manuscript_sha256),
        _kv("equation_manifest_sha256", workspace.equation_manifest_sha256),
        _kv("edge_manifest_sha256", workspace.edge_manifest_sha256),
        _kv("assumptions_sha256", workspace.assumptions_sha256),
    ]
    snapshot_hashes = sorted({
        record.source_snapshot_hash for record in run.records
    })
    if snapshot_hashes:
        lines.append(
            "- record source_snapshot_hash values: "
            + ", ".join(f"`{item}`" for item in snapshot_hashes)
        )
    engines = sorted({record.engine_version for record in run.records})
    if engines:
        lines.append(
            "- record engine_version values: "
            + ", ".join(f"`{item}`" for item in engines)
        )
    lines.extend([
        "",
        "## Verification summary",
        "",
        "| Table | Rows |",
        "| --- | --- |",
    ])
    for name in TABLE_ORDER:
        lines.append(f"| `{name}` | {len(buckets[name])} |")
    lines.extend(["", "| Status | Public label | Count |", "| --- | --- | --- |"])
    status_counts = Counter(record.status for record in run.records)
    for status in sorted(status_counts):
        lines.append(
            f"| `{status}` | {public_status_label(status)} | "
            f"{status_counts[status]} |"
        )
    n_fail = sum(1 for record in run.records if integrity_issues(record))
    lines.extend([
        "",
        f"- integrity FAIL records: `{n_fail}`",
        "",
        "## Machine-verified identities",
        "",
        APPROVED_MACHINE_CLAIM,
        "",
    ])
    verified = buckets[TABLE_VERIFIED]
    if verified:
        lines.append(render_markdown_table(verified).rstrip("\n"))
    else:
        lines.append(
            "No rows passed `schema.may_appear_in_verified_table`."
        )
    lines.extend([
        "",
        "## Structural steps",
        "",
        "DEFINITION, RECORDED, SPLIT, and CERTIFIED_BY_CHILDREN records. "
        "CERTIFIED_BY_CHILDREN is never displayed as ZERO.",
        "",
    ])
    structural = buckets[TABLE_STRUCTURAL]
    if structural:
        lines.append(render_markdown_table(structural).rstrip("\n"))
    else:
        lines.append("No structural records in this run.")
    lines.extend([
        "",
        "## Nonzero residuals",
        "",
        f"### {NONZERO_TABLE_TITLE}",
        "",
        NONZERO_REVIEWER_TEXT,
        "",
    ])
    nonzero = buckets[TABLE_NONZERO]
    if nonzero:
        lines.append(render_markdown_table(nonzero).rstrip("\n"))
    else:
        lines.append("No NONZERO records in this run.")
    lines.extend([
        "",
        "## Uncertified / asymptotic / integral",
        "",
        APPROVED_CAVEAT,
        "",
    ])
    uncertified = buckets[TABLE_UNCERTIFIED]
    if uncertified:
        lines.append(render_markdown_table(uncertified).rstrip("\n"))
    else:
        lines.append("No uncertified records in this run.")
    special = tuple(
        record for record in run.records
        if record.edge_type in _SPECIAL_UNVERIFIED_TYPES
    )
    lines.extend([
        "",
        "- asymptotic/limit/integral records: "
        f"`{len(special)}`",
        "",
        "## Assumptions",
        "",
        _kv("workspace assumptions_sha256", workspace.assumptions_sha256),
    ])
    assumed = []
    for record in run.records:
        if record.declared_assumptions:
            assumed.append(
                f"- `{record.edge_id}`: "
                + ", ".join(f"`{item}`" for item in record.declared_assumptions)
            )
    if assumed:
        lines.append("- Declared assumptions on records:")
        lines.extend(assumed)
    else:
        lines.append("- Declared assumptions on records: none.")
    lines.extend([
        "",
        "Assumptions are those declared on the workspace and records. "
        "None were inferred.",
        "",
        "## Reproduction",
        "",
        "Tables and this report are regenerated from immutable machine "
        "records. Existing markdown is not evidence and is overwritten.",
        "",
        "```",
        f"symbolic-compactification audit table <workspace> --run {run.run_id}",
        f"symbolic-compactification audit report <workspace> --run {run.run_id}",
        "```",
        "",
        "## Limitations",
        "",
        APPROVED_CAVEAT,
        "",
        "Finite coefficient identities do not certify an enclosing "
        "asymptotic remainder. Integral-level arguments are not local "
        "executable residuals. Split parents are never engine ZERO.",
        "This report does not certify a manuscript as a whole.",
        "",
    ])
    return "\n".join(lines) + "\n"


def _kv(label: str, value: Optional[str]) -> str:
    shown = "absent" if not value else value
    return f"- {label}: `{shown}`"
