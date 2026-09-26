"""Static reviewer summary generated from immutable audit records.

The summary is a reading aid for a reviewer who does not run the replay.  It
copies counts and row content from :class:`AuditRun`; it never assigns a
machine verdict.  Detailed tables, obligations, and the offline replay remain
the authoritative follow-up paths.
"""
from __future__ import annotations

import html
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .evidence import AuditRun
from .schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    TABLE_NONZERO,
    TABLE_STRUCTURAL,
    TABLE_UNCERTIFIED,
    TABLE_VERIFIED,
    AuditRecord,
    AuditError,
    integrity_issues,
    public_status_label,
)
from .tables import bucket_records, write_reports_text
from .inventory import load_equation_manifest
from .workspace import AuditWorkspace

SUMMARY_HTML_FILENAME = "REVIEWER_SUMMARY.html"
SUMMARY_MD_FILENAME = "REVIEWER_SUMMARY.md"


@dataclass(frozen=True)
class SummaryArtifacts:
    """Paths for the no-code reviewer views."""

    markdown: Path
    html: Path


def generate_reviewer_summary(
    workspace: AuditWorkspace,
    run: AuditRun,
) -> SummaryArtifacts:
    """Write an offline reviewer summary beside the generated audit tables."""
    buckets = bucket_records(run.records)
    markdown = write_reports_text(
        workspace, SUMMARY_MD_FILENAME, _render_markdown(workspace, run, buckets))
    html_path = write_reports_text(
        workspace, SUMMARY_HTML_FILENAME, _render_html(workspace, run, buckets))
    return SummaryArtifacts(markdown=markdown, html=html_path)


def _counts(
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> dict[str, int]:
    return {
        "total": len(run.records),
        "machine_exact": len(buckets[TABLE_VERIFIED]),
        "structural": len(buckets[TABLE_STRUCTURAL]),
        "nonzero": len(buckets[TABLE_NONZERO]),
        "needs_review": len(buckets[TABLE_UNCERTIFIED]),
        "integrity_fail": sum(bool(integrity_issues(record)) for record in run.records),
    }


def _provenance_rows(workspace: AuditWorkspace, run: AuditRun) -> list[tuple[str, str]]:
    source_hashes = sorted({record.source_snapshot_hash for record in run.records if record.source_snapshot_hash})
    engines = sorted({record.engine_version for record in run.records if record.engine_version})
    routes = sorted({record.verifier_route for record in run.records if record.verifier_route})
    assumptions = sorted({record.assumptions_hash for record in run.records if record.assumptions_hash})
    return [
        ("audit id", run.audit_id),
        ("run id", run.run_id),
        ("schema", run.schema_version),
        ("engine", ", ".join(engines) or "not recorded"),
        ("verifier route", ", ".join(routes) or "not recorded"),
        ("source snapshot", ", ".join(source_hashes) or "not recorded"),
        ("assumptions hash", workspace.assumptions_sha256 or "not recorded"),
        ("recorded assumptions hashes", ", ".join(assumptions) or "not recorded"),
        ("replay mode", "Not recorded in AuditRun; this summary does not establish cold replay."),
        ("freshness", "Recorded snapshot only; no comparison with later manuscript edits is claimed."),
    ]


def _equation_inventory(workspace: AuditWorkspace) -> tuple[str, str]:
    """Read the declared equation manifest without treating it as evidence."""
    try:
        inventory = load_equation_manifest(workspace)
    except AuditError as exc:
        return ("unavailable", f"manifest unavailable ({exc.code})")
    warning = ", ".join(inventory.warnings) or "none recorded"
    return (str(len(inventory.equations)), warning)


def _queue_records(buckets: Mapping[str, Sequence[AuditRecord]]) -> tuple[AuditRecord, ...]:
    return tuple(sorted(
        (*buckets[TABLE_NONZERO], *buckets[TABLE_UNCERTIFIED]),
        key=lambda record: (record.edge_id, record.edge_type, record.status),
    ))


def _display(value: object, fallback: str = "—") -> str:
    text = "" if value is None else str(value).strip()
    return text or fallback


def _md_cell(value: object, fallback: str = "—") -> str:
    return html.escape(_display(value, fallback)).replace("|", "\\|").replace("\n", " ")


def _status_sentence(counts: Mapping[str, int]) -> str:
    if not counts["total"]:
        return "No derivation obligations are recorded. No scientific verification is established."
    if counts["integrity_fail"]:
        return "Record integrity failures are present. Inspect these defects before using the affected evidence."
    if counts["nonzero"]:
        return (
            "The encoded residual table contains NONZERO rows. Those rows "
            "need scientific review before the corresponding step can be used."
        )
    if counts["needs_review"]:
        return (
            "No NONZERO row is recorded in this run, but unresolved, global, "
            "asymptotic, or unsupported obligations remain for review."
        )
    return (
        "No NONZERO or unresolved row is recorded in this run. This is still "
        "not a paper-level certificate."
    )


def _render_markdown(
    workspace: AuditWorkspace,
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> str:
    counts = _counts(run, buckets)
    statuses = Counter(record.status for record in run.records)
    types = Counter(record.edge_type for record in run.records)
    queue = _queue_records(buckets)
    equation_count, equation_warnings = _equation_inventory(workspace)
    lines = [
        "# Reviewer summary",
        "",
        "This file is a pre-generated reading aid from one recorded machine "
        "evidence run. It is not a paper-level certificate.",
        "",
        _status_sentence(counts),
        "",
        f"Declared equation inventory: `{equation_count}` entries; inventory warnings: `{equation_warnings}`. Inventory coverage is separate from derivation-edge evidence.",
        "",
        "## Read this first",
        "",
        "1. Read the evidence counts and the review queue below.",
        "2. Open `TABLE_VERIFIED.md` for exact local residuals.",
        "3. Open `TABLE_UNCERTIFIED.md` for asymptotic, global, and unsupported steps.",
        "4. In the exported package, run `./reproduce.sh` if an independent replay is needed.",
        "",
        "## Evidence counts",
        "",
        "| Category | Count | Meaning |",
        "| --- | ---: | --- |",
        f"| Total recorded obligations | {counts['total']} | All typed records in this run |",
        f"| Machine-verified local identities | {counts['machine_exact']} | Integrity-bound executable rows returning exact ZERO |",
        f"| Structural or rule records | {counts['structural']} | Definitions, bookkeeping, split parents, or declared global rules |",
        f"| NONZERO residuals | {counts['nonzero']} | Encoded identity fails under declared symbolic semantics |",
        f"| Unresolved / asymptotic / unsupported | {counts['needs_review']} | Must remain visible to the reviewer |",
        f"| Integrity failures | {counts['integrity_fail']} | Hash or record defects; must be zero for a clean package |",
        "",
        "`ZERO` is a local symbolic result. A structural or rule record is not an engine ZERO, and a finite coefficient result does not prove an enclosing remainder.",
        "These are derivation-edge counts, not numbered-equation coverage. This run does not supply a paper-claim dependency map.",
        "",
        "## Status distribution",
        "",
        "| Status | Count |",
        "| --- | ---: |",
    ]
    for status, count in sorted(statuses.items()):
        lines.append(f"| `{_md_cell(public_status_label(status))}` | {count} |")
    lines.extend([
        "",
        "## Derivation types",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ])
    for edge_type, count in sorted(types.items()):
        lines.append(f"| `{_md_cell(edge_type)}` | {count} |")
    lines.extend([
        "",
        "## Reviewer queue",
        "",
    ])
    if queue:
        lines.extend([
            "| Edge | Source | Status | Type | Claim | Assumptions |",
            "| --- | --- | --- | --- | --- | --- |",
        ])
        for record in queue:
            lines.append(
                "| " + " | ".join([
                    _md_cell(record.edge_id),
                    _md_cell(", ".join(record.source_refs)),
                    _md_cell(public_status_label(record.status)),
                    _md_cell(record.edge_type),
                    _md_cell(record.claim),
                    _md_cell(", ".join(record.declared_assumptions), "none recorded"),
                ]) + " |"
            )
    else:
        lines.append("No NONZERO or uncertified rows are listed; this does not establish complete coverage.")
    lines.extend([
        "",
        "## Provenance",
        "",
    ])
    lines.extend(f"- {key}: `{_md_cell(value)}`" for key, value in _provenance_rows(workspace, run))
    lines.extend([
        "",
        "## Scope and limitations",
        "",
        APPROVED_MACHINE_CLAIM,
        "",
        APPROVED_CAVEAT,
        "",
        "This summary does not certify a manuscript, physical model, global integral, limit, special-function identity, or numerical result. Human acceptance records reviewer judgment and does not change a machine status to Exact.",
        "",
        "## Reproduction",
        "",
        "```sh",
        "./reproduce.sh",
        "```",
        "",
        "The detailed machine records, residuals, assumptions, replay workspace, and SHA-256 manifest are included with the reviewer package.",
        "",
    ])
    return "\n".join(lines) + "\n"


def _esc(value: object, fallback: str = "—") -> str:
    return html.escape(_display(value, fallback), quote=True)


def _render_html(
    workspace: AuditWorkspace,
    run: AuditRun,
    buckets: Mapping[str, Sequence[AuditRecord]],
) -> str:
    counts = _counts(run, buckets)
    statuses = Counter(record.status for record in run.records)
    types = Counter(record.edge_type for record in run.records)
    queue = _queue_records(buckets)
    equation_count, equation_warnings = _equation_inventory(workspace)
    metric_cards = "".join(
        f'<div class="metric"><strong>{counts[key]}</strong><span>{label}</span></div>'
        for key, label in (
            ("total", "recorded"),
            ("machine_exact", "local ZERO"),
            ("structural", "structural/rule"),
            ("nonzero", "NONZERO"),
            ("needs_review", "review queue"),
        )
    )
    status_rows = "".join(
        f"<tr><th><code>{_esc(public_status_label(status))}</code></th><td>{count}</td></tr>"
        for status, count in sorted(statuses.items())
    )
    type_rows = "".join(
        f"<tr><th><code>{_esc(edge_type)}</code></th><td>{count}</td></tr>"
        for edge_type, count in sorted(types.items())
    )
    queue_html = _html_queue(queue)
    provenance_rows = "".join(
        f"<tr><th>{_esc(key)}</th><td><code>{_esc(value)}</code></td></tr>"
        for key, value in _provenance_rows(workspace, run)
    )
    return "\n".join([
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; img-src \'none\'; connect-src \'none\'; base-uri \'none\';">',
        "<title>Reviewer summary — " + _esc(workspace.config.audit_name) + "</title>",
        f"<style>{_CSS}</style>",
        "</head>",
        "<body>",
        '<main class="wrap">',
        '<p class="kicker">Pre-generated machine evidence overview</p>',
        f"<h1>{_esc(workspace.config.audit_name)} — reviewer summary</h1>",
        f'<p class="meta">Run <code>{_esc(run.run_id)}</code> · {counts["total"]} typed obligations</p>',
        f'<div class="banner">{_esc(_status_sentence(counts))}</div>',
        f'<p class="meta">Declared equation inventory: <code>{_esc(equation_count)}</code> entries · inventory warnings: <code>{_esc(equation_warnings)}</code>. Inventory coverage is separate from derivation-edge evidence.</p>',
        '<div class="metrics">' + metric_cards + '</div>',
        '<section class="notice"><strong>How to read this page.</strong> '
        'Green evidence is limited to integrity-bound local residuals returning exact ZERO. '
        'Structural, rule, asymptotic, global, numerical, and unsupported steps remain separately labelled. '
        'This page is a reading aid, not a paper-level certificate.</section>',
        '<nav class="jump"><a href="#queue">Reviewer queue</a> · '
        '<a href="#provenance">Provenance</a> · '
        '<a href="TABLE_VERIFIED.md">Exact table</a> · '
        '<a href="TABLE_UNCERTIFIED.md">Unresolved table</a></nav>',
        '<section><h2>Read this first</h2><ol>'
        '<li>Read the counts and review queue.</li>'
        '<li>Use the exact table for local residuals.</li>'
        '<li>Use the unresolved table for global, asymptotic, and unsupported steps.</li>'
        '<li>Run <code>./reproduce.sh</code> only when an independent replay is needed.</li>'
        '</ol></section>',
        '<section><h2>Status distribution</h2><table><thead><tr><th>Status</th><th>Count</th></tr></thead><tbody>'
        + status_rows + '</tbody></table></section>',
        '<section><h2>Derivation types</h2><table><thead><tr><th>Type</th><th>Count</th></tr></thead><tbody>'
        + type_rows + '</tbody></table></section>',
        '<section id="queue"><h2>Reviewer queue</h2>' + queue_html + '</section>',
        '<section id="provenance"><h2>Provenance</h2><table>' + provenance_rows + '</table></section>',
        '<section class="scope"><h2>Scope and limitations</h2>'
        f'<p>{_esc(APPROVED_MACHINE_CLAIM)}</p>'
        f'<p>{_esc(APPROVED_CAVEAT)}</p>'
        '<p>This summary does not certify a manuscript, physical model, global integral, limit, special-function identity, or numerical result. Human acceptance records reviewer judgment and does not change a machine status to Exact.</p>'
        '</section>',
        '<footer>To reproduce the evidence: <code>./reproduce.sh</code>. The package includes machine records, residuals, assumptions, replay sources, and <code>MANIFEST.json</code>.</footer>',
        '</main>',
        '</body>',
        '</html>',
        "",
    ])


def _html_queue(records: Sequence[AuditRecord]) -> str:
    if not records:
        return '<p class="ok">No NONZERO or uncertified records are present in this run.</p>'
    cards: list[str] = []
    for record in records:
        residual = _display(record.residual_text, "No executable residual recorded.")
        assumptions = _display(", ".join(record.declared_assumptions), "none recorded")
        cards.append(
            '<details class="queue-card">'
            f'<summary><strong>{_esc(record.edge_id)}</strong> · '
            f'<span class="status">{_esc(public_status_label(record.status))}</span> · '
            f'{_esc(record.edge_type)}</summary>'
            f'<p><b>Source:</b> {_esc(", ".join(record.source_refs))}</p>'
            f'<p><b>Claim:</b> {_esc(record.claim)}</p>'
            f'<p><b>Assumptions:</b> {_esc(assumptions)}</p>'
            f'<pre>{_esc(residual)}</pre>'
            '</details>'
        )
    return "\n".join(cards)


_CSS = """
:root{color-scheme:light;--ink:#20252a;--muted:#5b6670;--rule:#c5ccd2;--band:#f4f6f8;--warn:#fff5df;--warn-border:#a96b0b;--ok:#23613e;--bad:#8f2525;--max:68rem}
*{box-sizing:border-box}html{font-family:system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.45;color:var(--ink)}body{margin:0;background:#fff}.wrap{max-width:var(--max);margin:0 auto;padding:1.2rem 1.2rem 3rem}h1{font:700 1.8rem/1.2 Georgia,serif;margin:.1rem 0 .35rem}h2{font:700 1.15rem/1.25 Georgia,serif;margin:1.4rem 0 .55rem}.kicker,.meta,footer{color:var(--muted);font-size:.88rem}.kicker{text-transform:uppercase;letter-spacing:.05em}.banner,.notice{border:1px solid var(--warn-border);background:var(--warn);padding:.7rem .85rem;margin:.8rem 0}.notice{border-color:var(--rule);background:var(--band);font-size:.9rem}.metrics{display:grid;grid-template-columns:repeat(auto-fit,minmax(8.5rem,1fr));gap:.55rem;margin:1rem 0}.metric{border:1px solid var(--rule);padding:.65rem .7rem;background:#fff}.metric strong{display:block;font-size:1.35rem}.metric span{display:block;color:var(--muted);font-size:.8rem}.jump{margin:.75rem 0 1rem}.jump a{color:#1d4f80;margin-right:.55rem}table{border-collapse:collapse;width:100%;font-size:.88rem}th,td{border:1px solid var(--rule);padding:.42rem .55rem;text-align:left;vertical-align:top}th{background:var(--band)}code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85em}pre{white-space:pre-wrap;overflow:auto;background:var(--band);padding:.5rem}.queue-card{border:1px solid var(--rule);border-left:4px solid var(--warn-border);padding:.45rem .65rem;margin:.45rem 0}.queue-card summary{cursor:pointer}.status{color:var(--warn-border)}.ok{border-left:4px solid var(--ok);padding:.55rem .7rem;background:#f1f8f3;color:var(--ok)}.scope{border-top:1px solid var(--rule);margin-top:1.5rem;padding-top:.2rem}footer{border-top:1px solid var(--ink);margin-top:1.5rem;padding-top:.8rem}@media print{.jump{display:none}.queue-card{break-inside:avoid}}
""".strip()
