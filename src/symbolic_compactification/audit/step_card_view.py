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

_DETAIL_PREFIXES = ("QUOTE:", "READ_AS:", "DERIVED:", "COUNTEREXAMPLE:", "SOURCE_AT:", "REASON:",
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
            'translated by fixed rules. A step whose card does not match its quote is never decided. '
            'VALID means the claim holds identically for generic values of the parameters (away '
            'from coincident poles and vanishing denominators), under the conventions below.</p>'
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


# Why a step was not decided, in words a reviewer can act on. First match wins.
_REASONS = (
    ("DISPLAYS_DISAGREE", "Two displays give the same quantity different values",
     "The paper writes the quantity twice and the two right-hand sides differ. Unless the "
     "displays hold under different conditions (a limit, a special case), one of them is wrong."),
    ("FUNCTION_OR_PRODUCT", "The verdict depends on whether a name before “(” is a function or a product",
     "The card was checked both ways and the readings disagree. List the name under multiply: or "
     "functions: in conventions.yaml once you know which the paper means."),
    ("INTEGRAND_NOT_ENTIRE", "An integral with limits whose integrand may have a singularity",
     "Only integrands built from polynomials, exp, sin and cos are checked; this one stays with the reviewer."),
    ("ANTIDERIVATIVE_", "No verified antiderivative for an integral with limits",
     "The integral may still be right; it is outside what this check proves."),
    ("INFINITE_LIMIT_DECAY_UNDECIDED", "An infinite limit whose convergence depends on unstated signs",
     "State the damping symbol positive (e.g. $\\eta > 0$) and the frequencies real."),
    ("INFINITE_LIMIT_TERM_NOT_DECAYING", "An infinite limit where the integrand does not decay",
     "Check the convergence factor of the integral."),
    ("INTEGRATION_VARIABLE_MISMATCH", "The integration variable does not match the card",
     "Re-draft the card from the source."),
    ("INTEGRAL_NOT_UNDERSTOOD", "An integral whose limits or measure could not be read",
     "Integrals with both limits and one measure (dx before or after the integrand) are read."),
    ("LANGRETH_ORDER_ONLY", "A Langreth rule that differs from the exact one only in the order of factors",
     "Right if the functions commute (scalars of one frequency), wrong for matrices and time convolutions."),
    ("PERIODIC_IN_AN_INDEX", "A refutation that may fail for an integer index",
     "e^{2πin} = 1 for integer n: the counterexample used a generic value. Declare the index under "
     "integers: if the paper does not say so."),
    ("NONCOMMUTING_STATED", "The paper says its quantities are matrices or do not commute",
     "The checks treat products as commuting. Remove noncommuting: from conventions.yaml only if "
     "this step involves scalars alone."),
    ("BRANCH_DEPENDS_ON_SIGN", "A refutation that needs a negative value under a square root or a log",
     "State the symbols positive if the paper means them so (rates, widths)."),
    ("REORDERING_ONLY", "A claim that only reorders factors",
     "A B = ±B A is about operators, Grassmann numbers or generators; it is not checked as numbers."),
    ("SUBSCRIPT_COLLISION", "Two subscripts that read as the same name",
     "ε_+ and ε_p are both read as epsilon_p; rename one in notation."),
    ("DERIVATIVE_HOLDS_FIXED", "A derivative of an expression with other symbols in it",
     "d(ωt)/dt holds ω fixed; if the paper lets it depend on t, the result differs."),
    ("LOG_BASE_STATED", "The text uses logarithms to another base", "log here is not the natural logarithm."),
    ("BUILTIN_REDEFINED", "The paper defines its own function with a built-in name",
     "Its erf, sin or exp is not the standard one; quote the paper's definition instead."),
    ("ARBITRARY_FUNCTION", "A refutation that treats a declared function as arbitrary",
     "The paper's function may be a specific one (ζ(4) = π⁴/90 fails for an arbitrary ζ). Map a "
     "special function by notation (zeta: zeta_fn, Gamma: gamma_fn) or quote its definition."),
    ("TRACE_OF_MATRICES", "A trace or determinant", "Its arguments are matrices; the checks here are commutative."),
    ("VECTOR_OR_MATRIX", "Bold symbols in the claim", "Vectors or matrices: dot and matrix products are not products of numbers."),
    ("SOURCE_SLASH_PRECEDENCE", "A slash whose reach is ambiguous",
     "ω/2T means ω/(2T) to a physicist and (ω/2)T to a parser; write \\frac or brackets."),
    ("HOLDS_AT_SPECIAL_PHASES", "A refutation of a claim that holds when a phase factor is ±1",
     "e^{iπN} = 1 for even N, e^{iqL} = 1 on a periodic lattice: the claim may be about such values."),
    ("FERMI_SHIFT_NOT_REAL", "A Fermi function shifted by a complex amount",
     "n_F(ω + iΩ) moves the poles of n_F; the closed-form route needs a real shift."),
    ("CONSTRAINED_IN_TEXT", "A refutation using names the text constrains",
     "The text imposes a relation on them ($e^{iqL}=1$, $t>s$, $\\eta<0$); with them free, the "
     "counterexample may violate it."),
    ("APPROXIMATION_STATED", "The text says this holds to some order only",
     "'To first order', 'linear response': an exact equality is not what the paper claims."),
    ("DISTRIBUTION_IN_TEXT", "The paper writes its own occupation function",
     "The built-in n_F(x) = 1/(e^{βx}+1) may differ from the paper's (a chemical potential, say)."),
    ("OPERATORS", "Uses names the text calls operators, spin components or matrices",
     "Their products need not commute; the checks here are commutative."),
    ("DISTRIBUTION_NOT_THERMAL", "The text says n_F is not the thermal Fermi function",
     "n_F is expanded as 1/(e^{βx}+1) by the checks, which the paper does not mean here."),
    ("CONDITION_IN_DISPLAY", "The display holds a condition, a second relation or words next to this one",
     "\\qquad Ωt = π, (μ = 0), \\text{at} …: the extra piece may restrict the claim, so it is not decided."),
    ("EQUIV_RELATION", "A definition written with ≡ or :=", "It defines a quantity; it is not a claim to check."),
    ("ONE_SIDED_SYMBOL", "A refutation of a relation in which some symbol appears on one side only",
     "Such a relation may fix that symbol (a definition such as Γ = 2πρV², or a condition such as "
     "e^{iqL} = 1) rather than claim an identity, so it is not reported as wrong."),
    ("APPROXIMATE_NUMBER", "A refutation of a claim with a rounded decimal",
     "0.7468 means ≈; compare the value numerically by hand."),
    ("SINGULAR_AT_STATED_VALUE", "The claim is undefined at a value the text sets",
     "The identity holds for generic values, but the text fixes a name ($a = 0$) where a "
     "denominator vanishes. Check which value the step is about."),
    ("VALUED_IN_TEXT", "A refutation that treats a name as free although the text gives it a value",
     "The text sets this name ($x = …$) without a definition the tool could use. Quote it as a "
     "definition in conventions.yaml if it holds for this step."),
    ("SOURCE_PRODUCT_WITH_COMMA", "A name listed under multiply: is applied to several arguments",
     "G(t, t') cannot be a product: move the name to functions: or define it."),
    ("SOURCE_APPLICATION_AMBIGUOUS", "A name before “(” could be a product or a function",
     "List the name under multiply: in conventions.yaml if it multiplies, or define it as a function."),
    ("SOURCE_BRACKETS_UNBALANCED", "Brackets do not pair up as printed",
     "If the fix is obvious, add a bracket-only erratum to the card."),
    ("NOT_IN_DOCUMENT", "A quote is not in the manuscript",
     "Re-draft the card; quotes must be copied from the source."),
    ("SOURCE_CHARACTER_UNSUPPORTED", "Notation outside the supported forms",
     "Indefinite integrals, sums over indices, ⟨…⟩, traces, derivatives, matrices and similar "
     "stay with the reviewer."),
    ("SOURCE_FUNCTION_WITHOUT_ARGUMENTS", "A function name without its arguments",
     "Map the token in notation, or rename the definition."),
    ("RE_IM_WITHOUT_ARGUMENT", "Re or Im without an argument", "Check the quote boundaries."),
    ("UNDECLARED_OR_DISALLOWED_NAME", "Uses a name the conventions do not declare",
     "Declare the symbol, map it in notation, or define it."),
    ("UNQUOTED_CARD_DEFINITION", "A card definition is not quoted from the paper",
     "Quote it as define:NAME(args), or move it to conventions.yaml."),
    ("CONVENTION_CONFLICT", "The card redefines a shared convention", "Remove the card's override."),
    ("SOURCE_REQUIRED", "An expression is not quoted from the paper", "Quote it verbatim."),
    ("MANYBODY_INPUT_ERROR", "The card could not be read", "Open the card and fix its fields."),
    ("REALNESS_UNSTATED", "The claim takes Re, Im, a conjugate or |…| of a symbol the paper never calls real",
     "State the symbol real or complex in conventions.yaml (real: true / real: false)."),
    ("LIMIT_POINT_UNSTATED", "The limit point of an O(…) claim is not stated",
     "The verdict differs between x → 0 and x → ∞; set point: 0 or oo on the card."),
    ("NAMED_QUANTITY_UNDEFINED", "Uses a quantity the paper gives a value elsewhere, without its definition",
     "Quote that quantity's definition in conventions.yaml (define:NAME(args)) so it is not a free symbol."),
    ("LHS_IS_A_NAMED_QUANTITY", "States the value of a named quantity",
     "Without that quantity's own definition the relation cannot be checked; quote its "
     "definition in conventions.yaml if the paper gives one."),
    ("CARD_LHS_BARE", "States or defines a named quantity",
     "If the equation defines the name, move it to conventions.yaml as a quoted definition so "
     "other steps can use it; if it is defined elsewhere, quote that definition."),
)
_UNDECIDED_BY_CHECK = ("The check could not decide the claim",
                       "The quote was read; the claim is outside what this check can prove.")


def explain(record: AuditRecord) -> tuple[str, str]:
    text = " ".join(record.warnings)
    for code, title, hint in _REASONS:
        if code in text:
            return title, hint
    return _UNDECIDED_BY_CHECK


def is_undecided_card(record: AuditRecord) -> bool:
    return (record.edge_type == STEP_CARD and record.status not in ("CERTIFIED_BY_RULE", "NONZERO")
            and not any(w.startswith("WITH_ERRATUM:") for w in record.warnings))


def html_undecided_groups(records: Sequence[AuditRecord], macros: dict | None = None) -> str:
    """Undecided step cards, grouped by why, each group collapsed."""
    if not records:
        return ""
    groups: dict[tuple[str, str], list[AuditRecord]] = {}
    for r in records:
        groups.setdefault(explain(r), []).append(r)
    parts = [f'<h3 class="undecided">Not decided by the tool ({len(records)} steps)</h3>',
             '<p class="meta">These steps are not claimed right or wrong. Each group says why and '
             'what would let the tool decide them.</p>']
    for (title, hint), rows in sorted(groups.items(), key=lambda kv: (kv[0][0] != _REASONS[0][1], -len(kv[1]))):
        names: dict[str, int] = {}
        for r in rows:
            for w in r.warnings:
                if "SOURCE_APPLICATION_AMBIGUOUS:" in w:
                    name = w.rsplit("SOURCE_APPLICATION_AMBIGUOUS:", 1)[1]
                    names[name] = names.get(name, 0) + 1
        if names:
            hint += " Names: " + ", ".join(f"{n} ({k})" for n, k in sorted(names.items(), key=lambda x: -x[1])) + "."
        body = []
        for r in rows:
            meta = card_meta(r)
            quote = " ".join(meta.get("QUOTE", []))
            claim = render_tex(quote, macros or {}, display=False, source=False) if quote else "—"
            body.append(f"<tr><td><code>{_esc(r.edge_id)}</code></td>"
                        f"<td>{_short_source(meta, r)}</td><td>{claim}</td></tr>")
        flagged = " open" if title == _REASONS[0][1] else ""      # disagreements are shown open
        parts.append(f'<details class="group"{flagged}><summary><b>{_esc(title)}</b> — {len(rows)}</summary>'
                     f'<p class="meta">{_esc(hint)}</p><div class="scroll"><table><thead><tr>'
                     '<th>Step</th><th>Source</th><th>Claim as quoted</th></tr></thead><tbody>'
                     + "".join(body) + "</tbody></table></div></details>")
    return "".join(parts)
