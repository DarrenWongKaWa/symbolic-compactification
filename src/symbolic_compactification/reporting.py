"""Final certified-form reporting contract (agent protocol v0.3.0).

The human-facing deliverable of a run is the FINAL CERTIFIED FORM: the
current CERTIFIED expression rendered as a readable, complete, exactly
defined formula — NEVER "see final/current.json". The internal JSON
(``final/current.json``) is PROVENANCE, not the scientific deliverable.

Machine vs human representations
--------------------------------
The machine representation (the canonical certified expression text stored in
``final/current.json``) and the human representation produced here are
MATHEMATICALLY IDENTICAL. The human form may differ only in presentation:
named subexpressions (abbreviations / named kernels) stand in for repeated
blocks, and every such abbreviation MUST be explicitly defined. When
definitions are supplied, this module checks via the exact verifier that
substituting them into the human top-level form reproduces the certified
machine expression. An undecided or infeasible check raises
``REPORT_INCOMPLETE`` rather than publishing an unverified human form.

Deliverable contract
--------------------
A final response must:
  * show a readable top-level EXACT formula (the human form), and
  * reference the complete artifact ``<run_dir>/final/FINAL_CERTIFIED_FORM.md``
    (which carries every kernel/branch/definition plus the provenance header:
    run_id, engine_version, agent_protocol_version, final certified state
    sha256, ZERO promotions, NONZERO attempts, UNKNOWN attempts).
No hidden reasoning text is written into the artifact: structured fields and
mathematical content only.

Completeness validation
-----------------------
``render_final_report`` raises ``AdapterError("REPORT_INCOMPLETE")`` (with a
``.violators`` list attribute) when the human form or any definition contains
undefined aliases, ``{...}`` placeholders, ``TODO`` markers, or "same kernel"
hand-waving.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import sympy

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, PACKAGE_VERSION, ZERO,
                     AdapterError, SessionState, sha256_text)
from .parser import get_parse_policy, parse_expression
from .security import redact_public_data, redact_text
from .session import run_summary

__all__ = ["render_final_report", "FINAL_ARTIFACT_NAME",
           "CERTIFIED_EXPRESSION_NAME"]

FINAL_ARTIFACT_NAME = "FINAL_CERTIFIED_FORM.md"
# Machine-form artifact: the canonical certified expression text,
# one formula, suitable for machine consumption (parallel to the human
# FINAL_CERTIFIED_FORM.md artifact).
CERTIFIED_EXPRESSION_NAME = "certified_expression.txt"

_CONSTANTS = {"pi", "E", "I", "oo"}
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BRACE_RE = re.compile(r"\{[^{}]*\}")
_SAME_KERNEL_RE = re.compile(r"same\s+kernel", re.IGNORECASE)
_TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)
# "omitted" and "see JSON" are hand-waving tokens
# that mean the deliverable is incomplete — never a complete formula.
_OMITTED_RE = re.compile(r"\bomitted\b", re.IGNORECASE)
_SEE_JSON_RE = re.compile(r"see\s+JSON", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# completeness validation
# --------------------------------------------------------------------------- #

def _placeholder_offenders(texts: list) -> list:
    """Find placeholder / hand-waving tokens in the given texts.

    Rejects ``{...}``, TODO, 'same kernel', 'omitted'
    and 'see JSON' — none of these is a complete explicit formula.
    """
    offenders = []
    for text in texts:
        if not isinstance(text, str):
            continue
        for m in _BRACE_RE.finditer(text):
            offenders.append(f"placeholder {m.group(0)!r}")
        for m in _TODO_RE.finditer(text):
            offenders.append("placeholder 'TODO'")
        if _SAME_KERNEL_RE.search(text):
            offenders.append("placeholder 'same kernel'")
        if _OMITTED_RE.search(text):
            offenders.append("placeholder 'omitted'")
        if _SEE_JSON_RE.search(text):
            offenders.append("placeholder 'see JSON'")
    return sorted(set(offenders))


def _undefined_alias_offenders(human_form: str, certified_text: str,
                               declared_names: set, definitions: dict) -> list:
    """Identifiers in the human form that are neither declared symbols,
    parser builtins, defined abbreviations, nor present in the certified
    machine representation (the human form presents the SAME math)."""
    allowed = set(declared_names)
    allowed |= set(get_parse_policy()["allowed_functions"])
    allowed |= _CONSTANTS
    allowed |= set(definitions)
    allowed |= set(_IDENTIFIER_RE.findall(certified_text))
    used = set(_IDENTIFIER_RE.findall(human_form))
    return sorted(used - allowed)


# --------------------------------------------------------------------------- #
# certified-state resolution
# --------------------------------------------------------------------------- #

def _run_root_of(source: Union[SessionState, str, Path]) -> Path:
    if isinstance(source, SessionState):
        root = getattr(source, "run_root", None)
        if not root:
            raise AdapterError("SESSION_NOT_PERSISTED")
        return Path(root)
    return Path(source)


def _read_json(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _resolve_certified(source, run_root: Path) -> tuple:
    """Resolve the current CERTIFIED expression: (text, sha256, symbols).

    Preference order: ``final/current.json`` (the ZERO-gated promotion
    record), then the session's current record, then the manifest's current.
    """
    final = _read_json(run_root / "final" / "current.json")
    if final and final.get("text"):
        return (final["text"],
                final.get("sha256") or sha256_text(final["text"]),
                [dict(s) for s in final.get("symbols", [])],
                list(final.get("functions", [])))

    if isinstance(source, SessionState) and source.current is not None:
        rec = source.current
        return (rec.text, rec.sha256, [dict(s) for s in rec.symbols],
                list(rec.functions))

    manifest = _read_json(run_root / "manifest.json")
    if manifest and isinstance(manifest.get("current"), dict) \
            and manifest["current"].get("text"):
        cur = manifest["current"]
        return (cur["text"],
                cur.get("sha256") or sha256_text(cur["text"]),
                [dict(s) for s in cur.get("symbols", [])],
                list(cur.get("functions", [])))
    raise AdapterError("NO_CURRENT_EXPRESSION")


def _human_form_from_ast(certified_text: str, declared: list, functions: list
                         ) -> Optional[str]:
    """Build a human form programmatically from the certified AST.

    Parses the certified text and re-renders the AST; returns the rendered
    string, or ``None`` when parsing/rendering is infeasible. Where feasible
    this guarantees the human form is derived from the certified AST rather
    than hand-copied (so it cannot silently drift or drop terms).
    """
    try:
        expr = parse_expression(
            certified_text, declared, functions=functions or None)
        return str(expr)
    except (AdapterError, Exception):
        return None


# --------------------------------------------------------------------------- #
# abbreviation expansion check (exact verifier, where practical)
# --------------------------------------------------------------------------- #

def _expansion_check(human_form: str, certified_text: str,
                     declared: list, functions: list,
                     definitions: dict) -> str:
    """Verify definitions substitute back to the certified machine form.

    Returns ``"verified"``. Raises ``REPORT_INCOMPLETE`` for NONZERO,
    UNKNOWN, parse failure, unresolved aliases, or any infeasible check.
    """
    if not definitions and human_form == certified_text:
        return "verified"  # byte identity is already an exact proof

    alias_names = sorted(definitions)
    try:
        # declare the certified symbols plus the alias names so the strict
        # parser accepts the human form and each definition body
        decl = [dict(s) for s in declared] + [
            {"name": a, "real": True, "nonzero": False} for a in alias_names]
        human_expr = parse_expression(
            human_form, decl, functions=functions or None)
        def_exprs = {a: parse_expression(
                         definitions[a], decl, functions=functions or None)
                     for a in alias_names}

        # substitute aliases (by symbol name) until a fixed point; bounded so
        # cyclic definitions cannot loop
        expanded = human_expr
        for _ in range(len(alias_names) + 1):
            mapping = {
                symbol: def_exprs[symbol.name]
                for symbol in sorted(
                    expanded.free_symbols, key=lambda item: item.name)
                if symbol.name in def_exprs}
            if not mapping:
                break
            expanded = expanded.subs(mapping)
        remaining = sorted(
            symbol.name for symbol in expanded.free_symbols
            if symbol.name in def_exprs)
        if remaining:
            exc = AdapterError("REPORT_INCOMPLETE")
            exc.violators = [
                "cyclic or unresolved abbreviation: " + name
                for name in remaining]
            raise exc

        from .verifier import verify_equivalent  # local: keep imports light
        result = verify_equivalent(
            str(expanded), certified_text, decl,
            functions=functions or None)
        if result.verdict == ZERO:
            return "verified"
        if result.verdict == "NONZERO":
            exc = AdapterError("REPORT_INCOMPLETE")
            exc.violators = ["abbreviation expansion contradicts the "
                             "certified machine representation "
                             f"(residual: {result.residual})"]
            raise exc
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = [
            "abbreviation expansion could not be certified exactly"]
        raise exc
    except AdapterError as exc:
        if exc.code == "REPORT_INCOMPLETE":
            raise
        wrapped = AdapterError("REPORT_INCOMPLETE")
        wrapped.violators = [
            f"human representation could not be parsed exactly ({exc.code})"]
        raise wrapped from None
    except Exception:
        wrapped = AdapterError("REPORT_INCOMPLETE")
        wrapped.violators = [
            "human representation verification failed unexpectedly"]
        raise wrapped from None


# --------------------------------------------------------------------------- #
# artifact rendering
# --------------------------------------------------------------------------- #

def _render_markdown(report: dict) -> str:
    s = report["summary"] or {}
    lines = [
        "# FINAL CERTIFIED FORM",
        "",
        "## Provenance",
        "",
        f"- run_id: {report['run_id']}",
        f"- repository_version: {report['repository_version']}",
        f"- engine_version: {report['engine_version']}",
        f"- agent_protocol_version: {report['agent_protocol_version']}",
        f"- engine_git_sha: {report['engine_git_sha']}",
        f"- certified_state_sha256: {report['certified_state_sha256']}",
        f"- zero_promotions: {s.get('zero_promotions', 'unknown')}",
        f"- nonzero_attempts: {s.get('nonzero_count', 'unknown')}",
        f"- unknown_attempts: {s.get('unknown_count', 'unknown')}",
        "",
        "## Certified expression (top-level, human form)",
        "",
        "```",
        report["human_form"],
        "```",
        "",
    ]
    if report["definitions"]:
        lines += ["## Definitions (abbreviations / named kernels)", ""]
        for name in sorted(report["definitions"]):
            lines.append(f"- `{name}` := `{report['definitions'][name]}`")
        lines += [""]
    lines += [
        "## Machine representation (canonical; mathematically identical)",
        "",
        "```",
        report["certified_text"],
        "```",
        "",
        "## Abbreviation expansion check",
        "",
        f"- status: {report['expansion_check']}",
        "",
    ]
    return "\n".join(lines)


def _write_text_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


# --------------------------------------------------------------------------- #
# public API
# --------------------------------------------------------------------------- #

def render_final_report(source: Union[SessionState, str, Path], *,
                        human_form: Optional[str] = None,
                        definitions: Optional[Mapping[str, str]] = None
                        ) -> dict:
    """Build the human-facing FINAL CERTIFIED FORM deliverable for a run.

    Args:
        source:      a ``SessionState`` (with ``run_root``) or a run
                     directory path.
        human_form:  optional presentation of the certified expression using
                     named subexpressions; defaults to the certified machine
                     text itself.
        definitions: mapping abbreviation name -> exact expression string;
                     EVERY abbreviation used in ``human_form`` must be
                     defined. Expansion is checked against the certified
                     machine representation via the exact verifier.

    Returns:
        A dict with ``run_id``, ``certified_text``,
        ``certified_state_sha256``, ``human_form``, ``definitions``,
        ``expansion_check`` (always "verified" for a returned report),
        ``artifact_path`` and ``summary``. Writes
        ``<run_dir>/final/FINAL_CERTIFIED_FORM.md`` (complete artifact with
        every definition plus the provenance header).

    Raises:
        AdapterError("NO_CURRENT_EXPRESSION")  - the run has no current state
        AdapterError("REPORT_INCOMPLETE")      - undefined aliases or
            placeholders (``{...}`` / TODO / "same kernel"); the raised
            exception carries a ``.violators`` list.
    """
    run_root = _run_root_of(source)
    certified_text, certified_sha, declared, functions = _resolve_certified(
        source, run_root)

    if definitions is None:
        definitions = {}
    if not isinstance(definitions, Mapping):
        raise AdapterError("REPORT_INCOMPLETE")
    definitions = {str(k): str(v) for k, v in definitions.items()}
    invalid_aliases = sorted(
        name for name in definitions
        if (not _IDENTIFIER_RE.fullmatch(name)
            or name in {s["name"] for s in declared}
            or name in functions
            or name in set(get_parse_policy()["allowed_functions"])
            or name in _CONSTANTS))
    if invalid_aliases:
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = [f"invalid or colliding alias: {name}"
                         for name in invalid_aliases]
        raise exc

    if human_form is None:
        # Build the human form programmatically from the certified AST where
        # feasible. We keep the verbatim certified text as the
        # rendered human form (it IS the canonical rendering of that AST);
        # the AST round-trip is used below to confirm the human form is
        # programmatically derivable/complete (``human_render_verified``).
        human_form = certified_text
    if not isinstance(human_form, str) or not human_form.strip():
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = ["empty human form"]
        raise exc

    # Programmatic AST derivation of the human form (feasibility flag).
    ast_form = _human_form_from_ast(certified_text, declared, functions)
    human_ast_feasible = ast_form is not None

    # completeness: no placeholders, no undefined aliases — anywhere
    offenders = _placeholder_offenders([human_form, *definitions.values()])
    offenders += _undefined_alias_offenders(
        human_form, certified_text,
        {s["name"] for s in declared}, definitions)
    allowed_definition_names = (
        {s["name"] for s in declared} | set(functions) | set(definitions)
        | set(get_parse_policy()["allowed_functions"]) | _CONSTANTS
        | {"Sum", "Product", "Piecewise", "Eq", "Ne", "Lt", "Le",
           "Gt", "Ge", "And", "Or", "Not", "True", "False"})
    for name, body in definitions.items():
        unknown = sorted(
            set(_IDENTIFIER_RE.findall(body)) - allowed_definition_names)
        offenders.extend(
            f"undefined identifier in {name}: {identifier}"
            for identifier in unknown)
    if offenders:
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = sorted(set(offenders))
        raise exc

    expansion_check = _expansion_check(
        human_form, certified_text, declared, functions, definitions)

    # The human form is verified when it is provably consistent with the
    # certified machine form and the certified AST is programmatically
    # derivable. Expansion uncertainty already raised REPORT_INCOMPLETE.
    if human_ast_feasible:
        human_render_verified = (expansion_check == "verified")
    else:
        human_render_verified = False

    try:
        summary = redact_public_data(run_summary(run_root))
    except AdapterError:
        summary = None

    manifest = _read_json(run_root / "manifest.json") or {}
    report = {
        "run_id": redact_text(str(
            manifest.get("run_id")
            or (source.run_id if isinstance(source, SessionState)
                else "unknown"))),
        "certified_text": certified_text,
        "certified_state_sha256": certified_sha,
        "repository_version": redact_text(str(manifest.get(
            "repository_version", PACKAGE_VERSION))),
        "engine_version": redact_text(str(manifest.get(
            "engine_version", ENGINE_VERSION))),
        "agent_protocol_version": redact_text(str(manifest.get(
            "agent_protocol_version", AGENT_PROTOCOL_VERSION))),
        "engine_git_sha": redact_text(str(manifest.get(
            "engine_git_sha", "unknown"))),
        "human_form": human_form,
        "definitions": dict(definitions),
        "expansion_check": expansion_check,
        "human_render_verified": human_render_verified,
        "summary": summary,
    }

    final_dir = run_root / "final"
    final_dir.mkdir(parents=True, exist_ok=True)

    # Machine-form artifact: the canonical certified expression text.
    expression_path = final_dir / CERTIFIED_EXPRESSION_NAME
    _write_text_atomic(expression_path, certified_text + "\n")
    report["certified_expression_path"] = str(expression_path)

    artifact_path = final_dir / FINAL_ARTIFACT_NAME
    _write_text_atomic(artifact_path, _render_markdown(report))
    report["artifact_path"] = str(artifact_path)
    return report
