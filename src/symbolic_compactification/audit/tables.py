"""Authoritative reviewer tables. E6 implements generation from machine records.

VERIFIED TABLE IS GENERATED, NOT AUTHORED. Inclusion uses
``schema.table_bucket`` and ``schema.may_appear_in_verified_table`` only.
"""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence

from .evidence import AuditRun
from .io import contained_relpath
from .schema import (
    AUDIT_PROTOCOL_VERSION,
    AUDIT_SCHEMA_VERSION,
    CERTIFIED_BY_CHILDREN,
    CERTIFIED_BY_RULE,
    FORBIDDEN_PUBLIC_CLAIMS,
    NONZERO_REVIEWER_TEXT,
    TABLE_FILENAMES,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    AuditError,
    AuditRecord,
    integrity_issues,
    may_appear_in_verified_table,
    public_status_label,
    table_bucket,
)
from .workspace import REPORTS_DIRECTORY, AuditWorkspace

VERIFIED_COLUMNS = (
    "Edge ID",
    "Manuscript equation reference(s)",
    "Claim / transformation",
    "Executable residual",
    "Derivation type",
    "Declared assumptions",
    "Verifier",
    "Result",
    "Artifact link",
)

NONZERO_TABLE_TITLE = "POTENTIAL DERIVATION MISMATCHES"
JSON_FILENAME = "verification_table.json"
CSV_FILENAME = "verification_table.csv"

TABLE_ORDER = (
    TABLE_VERIFIED,
    TABLE_STRUCTURAL,
    TABLE_NONZERO,
    TABLE_UNCERTIFIED,
)

CSV_FIELDNAMES = (
    "run_id",
    "audit_id",
    "table",
    "edge_id",
    "source_refs",
    "claim",
    "residual_text",
    "edge_type",
    "declared_assumptions",
    "verifier_route",
    "status",
    "result",
    "public_status",
    "integrity",
    "executable",
    "artifact_relpath",
)

_BANNED_REVIEWER_PHRASES = ("the paper is wrong",)


@dataclass(frozen=True)
class TableArtifacts:
    verified_md: Path
    structural_md: Path
    uncertified_md: Path
    nonzero_md: Path
    table_json: Path
    table_csv: Path


def reports_directory(workspace: AuditWorkspace) -> Path:
    """Return the tool-owned reports/ directory, creating it if needed."""
    raw = workspace.root / REPORTS_DIRECTORY
    if raw.is_symlink():
        raise AuditError(
            "PATH_OUTSIDE_WORKSPACE",
            "reports must not be a symlink",
            path=str(raw),
        )
    _, path = contained_relpath(
        workspace.root, REPORTS_DIRECTORY, "output_dir")
    try:
        if path.exists() and not path.is_dir():
            raise AuditError(
                "REPORTS_DIRECTORY_INVALID",
                "reports must be a directory",
                path=str(path),
            )
        path.mkdir(parents=True, exist_ok=True)
    except AuditError:
        raise
    except OSError as exc:
        raise AuditError(
            "REPORTS_WRITE_FAILED", str(exc), path=str(path),
        ) from None
    if path.is_symlink() or not path.is_dir():
        raise AuditError(
            "REPORTS_DIRECTORY_INVALID",
            "reports must be a real directory",
            path=str(path),
        )
    return path


def write_reports_text(
    workspace: AuditWorkspace, filename: str, text: str,
) -> Path:
    """Atomically write a bare filename under reports/. Overwrite is allowed."""
    if (
        not isinstance(filename, str)
        or not filename
        or Path(filename).name != filename
        or "/" in filename
        or "\\" in filename
    ):
        raise AuditError(
            "REPORTS_PATH_INVALID",
            "reports filename must be a bare file name",
        )
    path = reports_directory(workspace) / filename
    payload = text if text.endswith("\n") else text + "\n"
    _guard_public_text(payload, path)
    _atomic_write(path, payload.encode("utf-8"))
    return path


def bucket_records(
    records: Iterable[AuditRecord],
) -> dict[str, tuple[AuditRecord, ...]]:
    """Assign each record to exactly one reviewer table via schema rules."""
    grouped: dict[str, list[AuditRecord]] = {
        name: [] for name in TABLE_ORDER
    }
    for record in records:
        verified = may_appear_in_verified_table(record)
        bucket = table_bucket(record)
        if verified:
            grouped[TABLE_VERIFIED].append(record)
            continue
        if bucket == TABLE_VERIFIED or bucket not in grouped:
            grouped[TABLE_UNCERTIFIED].append(record)
            continue
        grouped[bucket].append(record)
    return {
        name: tuple(_sorted_records(grouped[name])) for name in TABLE_ORDER
    }


def render_markdown_table(records: Sequence[AuditRecord]) -> str:
    """Render the shared reviewer-column markdown table (header always present)."""
    header = "| " + " | ".join(VERIFIED_COLUMNS) + " |"
    divider = "| " + " | ".join("---" for _ in VERIFIED_COLUMNS) + " |"
    lines = [header, divider]
    for record in records:
        lines.append("| " + " | ".join(_display_cells(record)) + " |")
    return "\n".join(lines) + "\n"


def generate_tables(workspace: AuditWorkspace, run: AuditRun) -> TableArtifacts:
    """Write TABLE_*.md plus verification_table.json/csv under reports/."""
    buckets = bucket_records(run.records)
    payloads = {
        TABLE_FILENAMES[TABLE_VERIFIED]: _render_verified_markdown(
            buckets[TABLE_VERIFIED]),
        TABLE_FILENAMES[TABLE_STRUCTURAL]: _render_structural_markdown(
            buckets[TABLE_STRUCTURAL]),
        TABLE_FILENAMES[TABLE_UNCERTIFIED]: _render_uncertified_markdown(
            buckets[TABLE_UNCERTIFIED]),
        TABLE_FILENAMES[TABLE_NONZERO]: _render_nonzero_markdown(
            buckets[TABLE_NONZERO]),
        JSON_FILENAME: _render_json(workspace, run, buckets),
        CSV_FILENAME: _render_csv(run, buckets),
    }
    paths: dict[str, Path] = {}
    for filename, text in payloads.items():
        paths[filename] = write_reports_text(workspace, filename, text)
    return TableArtifacts(
        verified_md=paths[TABLE_FILENAMES[TABLE_VERIFIED]],
        structural_md=paths[TABLE_FILENAMES[TABLE_STRUCTURAL]],
        uncertified_md=paths[TABLE_FILENAMES[TABLE_UNCERTIFIED]],
        nonzero_md=paths[TABLE_FILENAMES[TABLE_NONZERO]],
        table_json=paths[JSON_FILENAME],
        table_csv=paths[CSV_FILENAME],
    )


def _sorted_records(records: Iterable[AuditRecord]) -> list[AuditRecord]:
    return sorted(
        records,
        key=lambda record: (record.edge_id, record.edge_type, record.status),
    )


def _join(parts: tuple[str, ...]) -> str:
    return ", ".join(parts)


def _cell(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = " ".join(line.strip() for line in text.split("\n"))
    return text.replace("|", "\\|")


def _display_cells(record: AuditRecord) -> tuple[str, ...]:
    return (
        _cell(record.edge_id),
        _cell(_join(record.source_refs)),
        _cell(record.claim),
        _cell(record.residual_text or ""),
        _cell(record.edge_type),
        _cell(_join(record.declared_assumptions)),
        _cell(record.verifier_route or ""),
        _cell(public_status_label(record.status)),
        _cell(record.artifact_relpath or ""),
    )


def _integrity_label(record: AuditRecord) -> str:
    return "PASS" if not integrity_issues(record) else "FAIL"


def _guard_public_text(text: str, path: Path) -> None:
    lowered = text.lower()
    for phrase in FORBIDDEN_PUBLIC_CLAIMS:
        if phrase.lower() in lowered:
            raise AuditError(
                "FORBIDDEN_PUBLIC_CLAIM",
                "generated reviewer text contains a forbidden public claim",
                path=str(path),
            )
    for phrase in _BANNED_REVIEWER_PHRASES:
        if phrase in lowered:
            raise AuditError(
                "FORBIDDEN_PUBLIC_CLAIM",
                "generated reviewer text contains a forbidden reviewer phrase",
                path=str(path),
            )


def _atomic_write(path: Path, payload: bytes) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise AuditError(
            "REPORTS_PATH_INVALID",
            "refusing to overwrite a non-regular reports file",
            path=str(path),
        )
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except AuditError:
        raise
    except OSError as exc:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise AuditError(
            "REPORTS_WRITE_FAILED", str(exc), path=str(path),
        ) from None
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _preamble(title: str, paragraphs: Sequence[str]) -> list[str]:
    lines = [f"# {title}", ""]
    for paragraph in paragraphs:
        lines.extend([paragraph, ""])
    return lines


def _render_verified_markdown(records: Sequence[AuditRecord]) -> str:
    lines = _preamble("TABLE_VERIFIED", (
        "Generated from machine records. Markdown cannot create ZERO or "
        "VERIFIED status.",
        "Every row below has integrity PASS and engine result ZERO. "
        "Inclusion uses `schema.may_appear_in_verified_table` and "
        "`schema.table_bucket` only.",
    ))
    lines.append(render_markdown_table(records).rstrip("\n"))
    lines.append("")
    return "\n".join(lines) + "\n"


def _render_structural_markdown(records: Sequence[AuditRecord]) -> str:
    lines = _preamble("TABLE_STRUCTURAL", (
        "Definitions, recorded bookkeeping, split parents, split parents "
        "whose children are all certified, and BZ-torus IBP parents "
        "certified by local ZERO plus a declared periodicity theorem.",
        "CERTIFIED_BY_CHILDREN is displayed as "
        f"`{public_status_label(CERTIFIED_BY_CHILDREN)}`. "
        "CERTIFIED_BY_RULE is displayed as "
        f"`{public_status_label(CERTIFIED_BY_RULE)}`. "
        "Neither is displayed as ZERO; SymPy did not evaluate the integral.",
    ))
    lines.append(render_markdown_table(records).rstrip("\n"))
    lines.append("")
    return "\n".join(lines) + "\n"


def _render_uncertified_markdown(records: Sequence[AuditRecord]) -> str:
    lines = _preamble("TABLE_UNCERTIFIED", (
        "Unknown, assumption-required, not-lowered, parse/compile/grounding "
        "failures, invalid records, and other non-verified obligations.",
        "Asymptotic remainder claims and integral arguments appear here. "
        "A remainder certificate does not place an enclosing ASYMPTOTIC_CLAIM "
        "in TABLE_VERIFIED.",
    ))
    lines.append(render_markdown_table(records).rstrip("\n"))
    lines.append("")
    return "\n".join(lines) + "\n"


def _render_nonzero_markdown(records: Sequence[AuditRecord]) -> str:
    lines = _preamble(NONZERO_TABLE_TITLE, (
        "Machine table: TABLE_NONZERO.",
        NONZERO_REVIEWER_TEXT,
    ))
    lines.append(render_markdown_table(records).rstrip("\n"))
    lines.append("")
    return "\n".join(lines) + "\n"


def _json_row(record: AuditRecord, table_name: str) -> dict[str, Any]:
    issues = list(integrity_issues(record))
    return {
        "table": table_name,
        "edge_id": record.edge_id,
        "source_refs": list(record.source_refs),
        "claim": record.claim,
        "residual_text": record.residual_text,
        "edge_type": record.edge_type,
        "declared_assumptions": list(record.declared_assumptions),
        "verifier_route": record.verifier_route,
        "status": record.status,
        "result": record.result,
        "public_status": public_status_label(record.status),
        "integrity": _integrity_label(record),
        "integrity_issues": issues,
        "executable": record.executable,
        "artifact_relpath": record.artifact_relpath,
        "residual_hash": record.residual_hash,
        "obligation_hash": record.obligation_hash,
        "assumptions_hash": record.assumptions_hash,
        "source_snapshot_hash": record.source_snapshot_hash,
        "engine_version": record.engine_version,
        "runtime_seconds": record.runtime_seconds,
        "warnings": list(record.warnings),
        "children": list(record.children),
        "remainder_certificate_hash": record.remainder_certificate_hash,
        "may_appear_in_verified_table": may_appear_in_verified_table(record),
        "table_bucket": table_bucket(record),
    }


def _csv_row(
    run: AuditRun, record: AuditRecord, table_name: str,
) -> dict[str, str]:
    return {
        "run_id": run.run_id,
        "audit_id": run.audit_id,
        "table": table_name,
        "edge_id": record.edge_id,
        "source_refs": _join(record.source_refs),
        "claim": record.claim,
        "residual_text": record.residual_text or "",
        "edge_type": record.edge_type,
        "declared_assumptions": _join(record.declared_assumptions),
        "verifier_route": record.verifier_route or "",
        "status": record.status,
        "result": record.result,
        "public_status": public_status_label(record.status),
        "integrity": _integrity_label(record),
        "executable": "true" if record.executable else "false",
        "artifact_relpath": record.artifact_relpath or "",
    }


def _iter_bucket_rows(
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> Iterable[tuple[str, AuditRecord]]:
    for table_name in TABLE_ORDER:
        for record in buckets[table_name]:
            yield table_name, record


def _render_json(
    workspace: AuditWorkspace,
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> str:
    payload = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "protocol_version": AUDIT_PROTOCOL_VERSION,
        "run_id": run.run_id,
        "audit_id": run.audit_id,
        "audit_name": workspace.config.audit_name,
        "authority": "machine_records",
        "note": (
            "VERIFIED TABLE IS GENERATED, NOT AUTHORED. "
            "Markdown cannot create ZERO or VERIFIED status."
        ),
        "inclusion": {
            "verified": "schema.may_appear_in_verified_table",
            "buckets": "schema.table_bucket",
        },
        "counts": {name: len(buckets[name]) for name in TABLE_ORDER},
        "rows": [
            _json_row(record, table_name)
            for table_name, record in _iter_bucket_rows(buckets)
        ],
    }
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)


def _render_csv(
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=list(CSV_FIELDNAMES),
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    for table_name, record in _iter_bucket_rows(buckets):
        writer.writerow(_csv_row(run, record, table_name))
    return buffer.getvalue()
