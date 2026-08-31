"""Optional static HTML report. Non-blocking for alpha.

The page is a convenience view of machine records. Inclusion in the
machine-verified section is decided only by ``schema.table_bucket`` and
``schema.may_appear_in_verified_table``. User and residual strings are
HTML-escaped. The document is self-contained: no network, no beacons.
"""
from __future__ import annotations

import html
import os
from collections import defaultdict
from pathlib import Path

from .evidence import AuditRun
from .io import assert_contained, contained_relpath
from .schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    AuditRecord,
    may_appear_in_verified_table,
    public_status_label,
    table_bucket,
)
from .workspace import REPORTS_DIRECTORY, AuditWorkspace

REPORT_FILENAME = "report.html"

_BUCKET_ORDER = (
    TABLE_VERIFIED,
    TABLE_STRUCTURAL,
    TABLE_NONZERO,
    TABLE_UNCERTIFIED,
)

_SECTION_IDS = {
    TABLE_VERIFIED: "machine-verified",
    TABLE_STRUCTURAL: "structural",
    TABLE_NONZERO: "nonzero",
    TABLE_UNCERTIFIED: "uncertified",
}

_SECTION_TITLES = {
    TABLE_VERIFIED: "Machine-verified",
    TABLE_STRUCTURAL: "Structural",
    TABLE_NONZERO: "Nonzero residuals",
    TABLE_UNCERTIFIED: "Uncertified",
}

_FILTER_JS = """
(function () {
  var input = document.getElementById("edge-filter");
  var buttons = document.querySelectorAll("[data-filter-bucket]");
  var rows = document.querySelectorAll("tr.edge-row");
  var emptyNotes = document.querySelectorAll(".empty-filter-note");
  var activeBucket = "ALL";
  function apply() {
    var q = ((input && input.value) || "").toLowerCase();
    var visible = {};
    rows.forEach(function (row) {
      var bucket = row.getAttribute("data-bucket") || "";
      var text = (row.textContent || "").toLowerCase();
      var bucketOk = activeBucket === "ALL" || bucket === activeBucket;
      var textOk = !q || text.indexOf(q) !== -1;
      var show = bucketOk && textOk;
      row.hidden = !show;
      if (show) visible[bucket] = (visible[bucket] || 0) + 1;
    });
    emptyNotes.forEach(function (note) {
      var bucket = note.getAttribute("data-empty-bucket") || "";
      var table = note.previousElementSibling;
      var hasRows = table && table.querySelectorAll("tr.edge-row").length > 0;
      note.hidden = !hasRows || (visible[bucket] || 0) > 0;
    });
  }
  if (input) input.addEventListener("input", apply);
  buttons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      activeBucket = btn.getAttribute("data-filter-bucket") || "ALL";
      buttons.forEach(function (other) {
        other.classList.toggle("active", other === btn);
      });
      apply();
    });
  });
})();
""".strip()

_CSS = """
:root { color-scheme: light; }
html { font-family: ui-sans-serif, system-ui, sans-serif; line-height: 1.4; }
body { margin: 1.5rem auto; max-width: 72rem; padding: 0 1rem 3rem; color: #111; }
header, section { margin-bottom: 1.75rem; }
h1 { font-size: 1.6rem; margin: 0 0 0.4rem; }
h2 { font-size: 1.15rem; margin: 0 0 0.6rem; }
.muted { color: #555; }
.banner { background: #f4f4f4; border: 1px solid #ddd; padding: 0.75rem 1rem; }
nav.jump a, nav.filters button { margin: 0 0.35rem 0.35rem 0; }
nav.filters button.active { font-weight: 700; }
input[type="search"] { width: min(36rem, 100%); padding: 0.35rem 0.5rem; }
table { border-collapse: collapse; width: 100%; font-size: 0.92rem; }
th, td { border: 1px solid #ccc; padding: 0.35rem 0.5rem; vertical-align: top; text-align: left; }
th { background: #fafafa; }
.table-wrap { overflow-x: auto; }
pre { white-space: pre-wrap; word-break: break-word; margin: 0.4rem 0 0; }
.hash, .cmd { font-family: ui-monospace, monospace; font-size: 0.85rem; }
dl.meta { display: grid; grid-template-columns: 12rem 1fr; gap: 0.25rem 0.75rem; }
dl.meta dt { font-weight: 600; }
ul.compact { margin: 0.25rem 0; padding-left: 1.2rem; }
@media print {
  nav.filters, #edge-filter, label[for="edge-filter"] { display: none; }
}
""".strip()


def generate_html_report(workspace: AuditWorkspace, run: AuditRun) -> Path:
    """Write ``reports/report.html``. Regenerating overwrites the previous copy."""
    _, reports_dir = contained_relpath(
        workspace.root, workspace.config.output_dir or REPORTS_DIRECTORY,
        "output_dir")
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / REPORT_FILENAME
    assert_contained(workspace.root, path, "html_report")
    document = _render_document(workspace, run)
    tmp = path.with_name(".report.html.tmp")
    tmp.write_text(document, encoding="utf-8")
    os.replace(tmp, path)
    return path


def _esc(value: object) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return html.escape(value, quote=True)


def _assign_bucket(record: AuditRecord) -> str:
    """Group by table_bucket; verified rows require may_appear_in_verified_table."""
    if may_appear_in_verified_table(record):
        return TABLE_VERIFIED
    bucket = table_bucket(record)
    if bucket == TABLE_VERIFIED:
        return TABLE_UNCERTIFIED
    return bucket


def _grouped(records: tuple[AuditRecord, ...]) -> dict[str, list[AuditRecord]]:
    grouped: dict[str, list[AuditRecord]] = defaultdict(list)
    for record in records:
        grouped[_assign_bucket(record)].append(record)
    for bucket in grouped:
        grouped[bucket].sort(key=lambda rec: rec.edge_id)
    return grouped


def _unique(values: list[str]) -> tuple[str, ...]:
    seen: dict[str, None] = {}
    for value in values:
        if value and value not in seen:
            seen[value] = None
    return tuple(seen)


def _render_document(workspace: AuditWorkspace, run: AuditRun) -> str:
    grouped = _grouped(run.records)
    title = _esc(workspace.config.audit_name or "derivation-audit")
    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="'
        "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
        "img-src 'none'; connect-src 'none'; form-action 'none'; base-uri 'none';"
        '">',
        f"<title>{title} — derivation audit</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        _render_header(workspace, run, grouped),
        _render_metadata(workspace, run),
        _render_assumptions(workspace, run),
        _render_reproduction(workspace, run),
        _render_filters(grouped),
    ]
    for bucket in _BUCKET_ORDER:
        parts.append(_render_bucket_section(bucket, grouped.get(bucket, [])))
    parts.extend([
        f"<script>{_FILTER_JS}</script>",
        "</body>",
        "</html>",
        "",
    ])
    return "\n".join(parts)


def _render_header(
    workspace: AuditWorkspace,
    run: AuditRun,
    grouped: dict[str, list[AuditRecord]],
) -> str:
    counts = ", ".join(
        f"{_esc(_SECTION_TITLES[bucket])}: {len(grouped.get(bucket, []))}"
        for bucket in _BUCKET_ORDER
    )
    jumps = " ".join(
        f'<a href="#{_SECTION_IDS[bucket]}">{_esc(_SECTION_TITLES[bucket])}</a>'
        for bucket in _BUCKET_ORDER
    )
    return (
        "<header>"
        f"<h1>{_esc(workspace.config.audit_name)} — derivation audit</h1>"
        f'<p class="muted">Run {_esc(run.run_id)} · schema '
        f"{_esc(run.schema_version)} · {len(run.records)} edge"
        f"{'' if len(run.records) == 1 else 's'} · {counts}</p>"
        f'<p class="banner">{_esc(APPROVED_MACHINE_CLAIM)} '
        f"{_esc(APPROVED_CAVEAT)} This HTML page is a non-authoritative "
        "convenience view; machine-verified inclusion is generated from "
        "integrity-bound records only.</p>"
        f'<nav class="jump">{jumps}</nav>'
        "</header>"
    )


def _render_metadata(workspace: AuditWorkspace, run: AuditRun) -> str:
    routes = _unique([
        rec.verifier_route or "" for rec in run.records
    ] + [workspace.config.verifier_profile])
    engines = _unique([rec.engine_version for rec in run.records])
    snapshots = _unique([rec.source_snapshot_hash for rec in run.records])
    runtimes = [rec.runtime_seconds for rec in run.records]
    runtime_note = (
        f"{sum(runtimes):.6g} s total"
        if runtimes else "no executable timings"
    )
    rows = [
        ("audit_id", run.audit_id),
        ("run_id", run.run_id),
        ("run_directory", str(run.directory)),
        ("workspace", str(workspace.root)),
        ("schema_version", run.schema_version),
        ("verifier_profile", workspace.config.verifier_profile),
        ("verifier_routes", ", ".join(routes) or "—"),
        ("engine_version", ", ".join(engines) or "—"),
        ("source_snapshot_hash", ", ".join(snapshots) or "—"),
        ("assumptions_sha256", workspace.assumptions_sha256),
        ("config_sha256", workspace.config_sha256),
        ("runtime", runtime_note),
    ]
    items = "".join(
        f'<dt>{_esc(key)}</dt><dd class="hash">{_esc(value)}</dd>'
        for key, value in rows
    )
    return (
        '<section id="verifier-metadata">'
        "<h2>Verifier metadata</h2>"
        f'<dl class="meta">{items}</dl>'
        "</section>"
    )


def _render_assumptions(workspace: AuditWorkspace, run: AuditRun) -> str:
    declared = _unique([
        name
        for rec in run.records
        for name in rec.declared_assumptions
    ])
    hashes = _unique([
        rec.assumptions_hash or "" for rec in run.records
    ])
    if declared:
        items = "".join(f"<li>{_esc(name)}</li>" for name in declared)
        body = f'<ul class="compact">{items}</ul>'
    else:
        body = (
            '<p class="muted">No per-edge declared assumptions in this run. '
            "Workspace assumptions file hash is recorded below.</p>"
        )
    hash_line = ", ".join(hashes) if hashes else "—"
    return (
        '<section id="assumptions">'
        "<h2>Assumptions</h2>"
        f"{body}"
        f'<p class="hash">workspace assumptions sha256: '
        f"{_esc(workspace.assumptions_sha256)}</p>"
        f'<p class="hash">record assumptions hashes: {_esc(hash_line)}</p>'
        "</section>"
    )


def _render_reproduction(workspace: AuditWorkspace, run: AuditRun) -> str:
    root = str(workspace.root)
    run_id = run.run_id
    command = (
        f"symbolic-compactification audit verify {root}\n"
        f"symbolic-compactification audit table --run {run_id} {root}\n"
        f"symbolic-compactification audit report --run {run_id} {root}\n"
    )
    return (
        '<section id="reproduction">'
        "<h2>Reproduction command</h2>"
        '<p class="muted">Re-run verification against this workspace, then '
        "regenerate reviewer tables from the recorded run id. The HTML page "
        "is an optional view of the same records.</p>"
        f'<pre class="cmd">{_esc(command)}</pre>'
        "</section>"
    )


def _render_filters(grouped: dict[str, list[AuditRecord]]) -> str:
    buttons = ['<button type="button" class="active" data-filter-bucket="ALL">All</button>']
    for bucket in _BUCKET_ORDER:
        count = len(grouped.get(bucket, []))
        buttons.append(
            f'<button type="button" data-filter-bucket="{_esc(bucket)}">'
            f"{_esc(_SECTION_TITLES[bucket])} ({count})</button>"
        )
    return (
        '<section id="filters">'
        "<h2>Edges</h2>"
        '<label for="edge-filter">Filter table</label> '
        '<input type="search" id="edge-filter" '
        'placeholder="id, status, equation ref, residual…">'
        f'<nav class="filters">{"".join(buttons)}</nav>'
        "</section>"
    )


def _render_bucket_section(bucket: str, records: list[AuditRecord]) -> str:
    section_id = _SECTION_IDS[bucket]
    title = _SECTION_TITLES[bucket]
    note = ""
    if bucket == TABLE_VERIFIED:
        note = (
            '<p class="muted">Rows appear here only when '
            "<code>may_appear_in_verified_table</code> is true "
            "(executable engine ZERO with passing integrity). "
            "A ZERO label in markdown or LLM text is not sufficient.</p>"
        )
    table = _render_table(bucket, records)
    empty_filter = (
        f'<p class="muted empty-filter-note" data-empty-bucket="{_esc(bucket)}" hidden>'
        "No rows match the current filter.</p>"
    )
    return (
        f'<section id="{section_id}" data-table="{_esc(bucket)}">'
        f"<h2>{_esc(title)} ({len(records)})</h2>"
        f"{note}{table}{empty_filter}"
        "</section>"
    )


def _render_table(bucket: str, records: list[AuditRecord]) -> str:
    if not records:
        return '<p class="muted">No records in this bucket.</p>'
    rows = "".join(_render_row(bucket, rec) for rec in records)
    return (
        '<div class="table-wrap"><table class="edges">'
        "<thead><tr>"
        "<th>Edge</th><th>Status</th><th>Result</th><th>Type</th>"
        "<th>Equation refs</th><th>Assumptions</th>"
        "<th>Verifier</th><th>Residual</th>"
        "</tr></thead>"
        f"<tbody>{rows}</tbody>"
        "</table></div>"
    )


def _render_row(bucket: str, record: AuditRecord) -> str:
    refs = ", ".join(_esc(ref) for ref in record.source_refs) or "—"
    assumptions = ", ".join(_esc(name) for name in record.declared_assumptions) or "—"
    verifier = (
        f"{_esc(record.verifier_route or '—')}<br>"
        f'<span class="muted hash">{_esc(record.engine_version)}</span>'
        f'<br><span class="muted">{_esc(f"{record.runtime_seconds:.6g} s")}</span>'
    )
    residual = _render_residual(record)
    warnings = ""
    if record.warnings:
        items = "".join(f"<li>{_esc(item)}</li>" for item in record.warnings)
        warnings = f'<ul class="compact">{items}</ul>'
    claim = f'<div class="muted">{_esc(record.claim)}</div>' if record.claim else ""
    return (
        f'<tr class="edge-row" data-bucket="{_esc(bucket)}" '
        f'data-edge-id="{_esc(record.edge_id)}" '
        f'data-status="{_esc(record.status)}">'
        f"<td>{_esc(record.edge_id)}{claim}{warnings}</td>"
        f"<td>{_esc(public_status_label(record.status))}</td>"
        f"<td>{_esc(record.result)}</td>"
        f"<td>{_esc(record.edge_type)}</td>"
        f"<td>{refs}</td>"
        f"<td>{assumptions}</td>"
        f"<td>{verifier}</td>"
        f"<td>{residual}</td>"
        "</tr>"
    )


def _render_residual(record: AuditRecord) -> str:
    text = record.residual_text
    hash_line = (
        f'<div class="muted hash">hash: {_esc(record.residual_hash)}</div>'
        if record.residual_hash else ""
    )
    if text is None or text == "":
        return f'<span class="muted">—</span>{hash_line}'
    return (
        "<details>"
        "<summary>Residual</summary>"
        f"<pre>{_esc(text)}</pre>"
        f"{hash_line}"
        "</details>"
    )
