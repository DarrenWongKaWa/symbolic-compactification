"""Reviewer views for STEP_CARD records (many-body step cards).

A step card's record carries its details as prefixed warnings written by
manybody_pass (CARD_CHECK:, TRANSCRIPTION:, QUOTE:, DERIVED:, ...). These
helpers only display them; they never change a status. The conventions
table shows the one agent- or author-authored bridge of a card audit (the
notation map and the shared definitions), so a reviewer can check it once.
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

from .schema import STEP_CARD, AuditError, AuditRecord, public_status_label

__all__ = ["STEP_CARD", "card_meta", "chip_warnings", "conventions", "html_conventions",
           "html_step_card_body", "html_step_cards", "manuscript_macros", "manuscript_title",
           "md_step_cards",
           "render_expression", "render_tex", "step_card_records"]
from .workspace import AuditWorkspace

_DETAIL_PREFIXES = ("QUOTE:", "READ_AS:", "DERIVED:", "COUNTEREXAMPLE:", "SOURCE_AT:",
                    "ERRATUM:", "ERRATUM_NOTE:", "PRINTED:", "WITH_ERRATUM:")
_META_PREFIXES = ("CARD_CHECK:", "CARD_CHECKER:", "TRANSCRIPTION:", "BLOCKED:", "DIAGNOSIS:")


def card_meta(record: AuditRecord) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for warning in record.warnings:
        for prefix in (*_META_PREFIXES, *_DETAIL_PREFIXES):
            if warning.startswith(prefix):
                out.setdefault(prefix[:-1], []).append(warning[len(prefix):])
    return out


def chip_warnings(record: AuditRecord) -> tuple[str, ...]:
    """Warnings shown as chips: the long details are shown in the body."""
    if record.edge_type != STEP_CARD:
        return record.warnings
    return tuple(w for w in record.warnings if not w.startswith(_DETAIL_PREFIXES))


def step_card_records(records: Iterable[AuditRecord]) -> list[AuditRecord]:
    return [r for r in records if r.edge_type == STEP_CARD]


def _esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def conventions(workspace: AuditWorkspace) -> list[tuple[str, str, str, str]]:
    """(file, kind, key, value) for every conventions.yaml beside a card."""
    from .edges import load_edges
    try:
        edges = load_edges(workspace)
    except AuditError:
        return []
    files: list[Path] = []
    for edge in edges:
        card = edge.spec("step_card").get("card") if edge.step_card else None
        if card:
            candidate = (workspace.root / card).parent / "conventions.yaml"
            if candidate.is_file() and candidate not in files:
                files.append(candidate)
    rows = []
    for path in files:
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        rel = str(path.relative_to(workspace.root))
        for s in data.get("symbols") or []:
            if isinstance(s, dict) and s.get("positive"):
                rows.append((rel, "assumption", str(s["name"]), "positive"))
        for k, v in (data.get("notation") or {}).items():
            rows.append((rel, "notation", str(k), str(v)))
        for name in data.get("multiply") or []:
            rows.append((rel, "product before (", str(name), f"{name}(x) is read as {name}*x"))
        for k, v in (data.get("define") or {}).items():
            rows.append((rel, "definition (typed)", str(k), str(v)))
        for k, v in (data.get("source") or {}).items():
            quote = v.get("quote") if isinstance(v, dict) else v
            branch = f"  [branch {v['branch']}]" if isinstance(v, dict) and v.get("branch") else ""
            rows.append((rel, "definition (quoted)", str(k).split(":", 1)[-1], f"{quote}{branch}"))
    return rows


def manuscript_macros(workspace: AuditWorkspace) -> dict:
    from ..manybody.latex import read_macros
    try:
        return read_macros((workspace.root / workspace.config.manuscript_source)
                           .read_text(encoding="utf-8"))
    except (OSError, AttributeError, ValueError):
        return {}


def render_tex(tex: str, macros: dict, *, display: bool = True, source: bool = True) -> str:
    """Rendered MathML with the verbatim LaTeX one click away."""
    from ..manybody.mathml import latex_to_mathml
    rendered = latex_to_mathml(tex, macros, display=display)
    if rendered is None:
        return f"<pre>{_esc(tex)}</pre>"
    if not source:
        return f'<span class="math">{rendered}</span>'
    return (f'<div class="math">{rendered}</div>'
            f'<details class="tex"><summary>LaTeX source</summary><pre>{_esc(tex)}</pre></details>')


def render_expression(text: str) -> str:
    from ..manybody.mathml import expression_to_mathml
    rendered = expression_to_mathml(text)
    if rendered is None:
        return f"<pre>{_esc(text)}</pre>"
    return (f'<div class="math">{rendered}</div>'
            f'<details class="tex"><summary>as text</summary><pre>{_esc(text)}</pre></details>')


def manuscript_title(workspace: AuditWorkspace) -> str | None:
    from ..manybody.latex import document_title
    try:
        return document_title((workspace.root / workspace.config.manuscript_source)
                              .read_text(encoding="utf-8"))
    except (OSError, AttributeError, ValueError):
        return None


def citation(value: str, title: str | None = None) -> str:
    """'file|line|label|number' -> 'Title — file, line 32, eq. (5) [eq:x]'."""
    doc, line, label, number = (value.split("|") + ["", "", "", ""])[:4]
    parts = [f"<code>{_esc(doc)}</code>" if doc else "", f"line {_esc(line)}" if line else "",
             f"eq. ({_esc(number)})" if number else "", f"<code>\\label{{{_esc(label)}}}</code>" if label else ""]
    where = ", ".join(p for p in parts if p)
    head = f"<i>{_esc(title)}</i> — " if title else ""
    return f'<p class="cite">From the manuscript: {head}{where}</p>'


def html_step_card_body(record: AuditRecord, macros: dict | None = None,
                        title: str | None = None) -> str:
    meta = card_meta(record)
    macros = macros or {}
    parts = []
    for value in meta.get("QUOTE", []):
        parts.append("<p><b>Claim, as written in the manuscript:</b></p>" + render_tex(value, macros))
        for at in meta.get("SOURCE_AT", []):
            parts.append(citation(at, title))
    for printed, fixed in zip(meta.get("PRINTED", []), meta.get("ERRATUM", [])):
        verdict = (meta.get("WITH_ERRATUM") or ["not decided"])[0]
        note = " ".join(meta.get("ERRATUM_NOTE", []))
        parts.append(
            '<div class="erratum"><p><b>Typesetting defect in the manuscript.</b> '
            + (_esc(note) + ". " if note else "")
            + "The printed formula cannot be read as written, so the step is not decided. "
            f"With the bracket-only correction below the claim is <b>{_esc(verdict)}</b>.</p>"
            "<p><b>Printed:</b></p>" + render_tex(printed, macros)
            + "<p><b>Corrected (brackets only):</b></p>" + render_tex(fixed, macros) + "</div>")
    for value in meta.get("READ_AS", []):
        parts.append("<p><b>Claim, as the tool read it:</b></p>" + render_expression(value))
    for value in meta.get("DERIVED", []):
        parts.append("<p><b>What the tool computed:</b></p>" + render_expression(value))
    for label, key in (("Counterexample point", "COUNTEREXAMPLE"), ("Diagnosis", "DIAGNOSIS"),
                       ("Not decided because", "BLOCKED")):
        for value in meta.get(key, []):
            parts.append(f"<p><b>{label}:</b> <code>{_esc(value)}</code></p>")
    return "".join(parts) or "<p>No step-card details recorded.</p>"


def html_step_cards(records: Sequence[AuditRecord], tone_of: Mapping[int, str],
                    macros: dict | None = None) -> str:
    macros = macros or {}
    rows = []
    for r in records:
        meta = card_meta(r)
        rows.append(
            "<tr>"
            f"<td><code>{_esc(r.edge_id)}</code></td>"
            f"<td>{_short_source(meta, r)}</td>"
            f"<td>{_esc(', '.join(meta.get('CARD_CHECK', ['—'])))}</td>"
            f"<td><span class=\"chip {tone_of.get(id(r), 'tone-review')}\">"
            f"{_esc(public_status_label(r.status))}</span>"
            + (f"<br><span class=\"meta\">{_esc(meta['WITH_ERRATUM'][0])} after bracket erratum</span>"
               if meta.get("WITH_ERRATUM") else "") + "</td>"
            f"<td>{_esc(', '.join(meta.get('TRANSCRIPTION', ['—'])))}</td>"
            f"<td>{render_tex(' '.join(meta['QUOTE']), macros, display=False, source=False) if meta.get('QUOTE') else '—'}</td>"
            "</tr>")
    return ('<section id="cards"><h2>Step cards</h2>'
            '<p class="meta">Each row is one derivation step replayed with '
            '<code>--require-source</code>: the claim is a verbatim quote of the manuscript, '
            'translated by fixed rules. A step whose card does not match its quote is never decided.</p>'
            '<div class="scroll"><table><thead><tr><th>Step</th><th>Source</th><th>Check</th>'
            '<th>Status</th><th>Transcription</th><th>Claim as quoted</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div></section>")


def _short_source(meta: dict, record: AuditRecord) -> str:
    at = (meta.get("SOURCE_AT") or [""])[0]
    if at:
        doc, line, label, number = (at.split("|") + ["", "", "", ""])[:4]
        bits = [f"eq. ({_esc(number)})" if number else "", f"line {_esc(line)}" if line else ""]
        return _esc(Path(doc).name) + ("<br>" + " · ".join(b for b in bits if b) if any(bits) else "")
    return _esc(", ".join(record.source_refs) or "—")


def html_conventions(rows: Sequence[tuple[str, str, str, str]], macros: dict | None = None) -> str:
    if not rows:
        return ""

    def meaning(kind: str, value: str) -> str:
        if kind == "definition (quoted)":
            tex, _, branch = value.partition("  [branch ")
            return render_tex(tex, macros or {}, display=False, source=False) + (
                f" <span class=\"meta\">branch {_esc(branch.rstrip(']'))}</span>" if branch else "")
        return f"<code>{_esc(value)}</code>"

    body = "".join(
        f"<tr><td>{_esc(kind)}</td><td><code>{_esc(key)}</code></td><td>{meaning(kind, value)}</td></tr>"
        for _, kind, key, value in rows)
    files = ", ".join(sorted({f for f, *_ in rows}))
    return ('<section id="conventions"><h2>Conventions to review once</h2>'
            f'<p class="meta">From <code>{_esc(files)}</code>. The notation map and typed '
            'definitions are the only hand-written link between the manuscript and the checks; '
            'quoted definitions were matched against the manuscript.</p>'
            '<div class="scroll"><table><thead><tr><th>Kind</th><th>Name</th><th>Meaning</th></tr></thead>'
            f"<tbody>{body}</tbody></table></div></section>")


def md_step_cards(records: Sequence[AuditRecord], rows: Sequence[tuple[str, str, str, str]],
                  cell) -> list[str]:
    if not records:
        return []
    lines = ["", "## Step cards", "",
             "| Step | Source | Check | Status | Transcription | Claim as quoted |",
             "| --- | --- | --- | --- | --- | --- |"]
    for r in records:
        meta = card_meta(r)
        lines.append("| " + " | ".join([
            cell(r.edge_id), cell(", ".join(r.source_refs)),
            cell(", ".join(meta.get("CARD_CHECK", []))), cell(public_status_label(r.status)),
            cell(", ".join(meta.get("TRANSCRIPTION", []))), cell(" ".join(meta.get("QUOTE", []))),
        ]) + " |")
    if rows:
        lines += ["", "## Conventions to review once", "", "| Kind | Name | Meaning |",
                  "| --- | --- | --- |"]
        lines += [f"| {cell(kind)} | `{cell(key)}` | `{cell(value)}` |" for _, kind, key, value in rows]
    return lines
