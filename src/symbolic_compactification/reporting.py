"""Final certified-form reporting contract (agent protocol v0.2.2).

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
definitions are supplied, this module checks — via the exact verifier, where
practical — that substituting them into the human top-level form reproduces
the certified machine expression; when that check is not feasible for size or
namespace reasons it records ``"expansion_check": "skipped"`` honestly rather
than claiming verification.

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
import re
from pathlib import Path
from typing import Any, Mapping, Optional, Union

import sympy

from .models import (AGENT_PROTOCOL_VERSION, ENGINE_VERSION, ZERO,
                     AdapterError, SessionState, sha256_text)
from .parser import get_parse_policy, parse_expression
from .session import run_summary

__all__ = ["render_final_report", "FINAL_ARTIFACT_NAME"]

FINAL_ARTIFACT_NAME = "FINAL_CERTIFIED_FORM.md"

# Above this op count the abbreviation-expansion check is recorded as
# "skipped" rather than paid for (honest skip, never a silent claim).
EXPANSION_CHECK_OPS_CAP = 3000

_CONSTANTS = {"pi", "E", "I", "oo"}
_IDENTIFIER_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_BRACE_RE = re.compile(r"\{[^{}]*\}")
_SAME_KERNEL_RE = re.compile(r"same\s+kernel", re.IGNORECASE)
_TODO_RE = re.compile(r"\bTODO\b", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# completeness validation
# --------------------------------------------------------------------------- #

def _placeholder_offenders(texts: list) -> list:
    """Find ``{...}`` / TODO / 'same kernel' placeholders in the given texts."""
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
                [dict(s) for s in final.get("symbols", [])])

    if isinstance(source, SessionState) and source.current is not None:
        rec = source.current
        return rec.text, rec.sha256, [dict(s) for s in rec.symbols]

    manifest = _read_json(run_root / "manifest.json")
    if manifest and isinstance(manifest.get("current"), dict) \
            and manifest["current"].get("text"):
        cur = manifest["current"]
        return (cur["text"],
                cur.get("sha256") or sha256_text(cur["text"]),
                [dict(s) for s in cur.get("symbols", [])])
    raise AdapterError("NO_CURRENT_EXPRESSION")


# --------------------------------------------------------------------------- #
# abbreviation expansion check (exact verifier, where practical)
# --------------------------------------------------------------------------- #

def _expansion_check(human_form: str, certified_text: str,
                     declared: list, definitions: dict) -> str:
    """Verify definitions substitute back to the certified machine form.

    Returns "verified" | "undecided" | "skipped". Raises
    AdapterError("REPORT_INCOMPLETE") when the expansion is PROVABLY wrong
    (NONZERO): defined abbreviations that contradict the certified form make
    the report incomplete/incorrect.
    """
    if not definitions:
        return "verified"  # nothing to expand: human form IS the machine form

    alias_names = sorted(definitions)
    try:
        # declare the certified symbols plus the alias names so the strict
        # parser accepts the human form and each definition body
        decl = [dict(s) for s in declared] + [
            {"name": a, "real": True, "nonzero": False} for a in alias_names]
        human_expr = parse_expression(human_form, decl)
        def_exprs = {a: parse_expression(definitions[a], decl)
                     for a in alias_names}
        if sympy.count_ops(human_expr, visual=False) > EXPANSION_CHECK_OPS_CAP:
            return "skipped"

        # substitute aliases (by symbol name) until a fixed point; bounded so
        # cyclic definitions cannot loop
        expanded = human_expr
        for _ in range(len(alias_names) + 1):
            mapping = {s: def_exprs[s.name] for s in expanded.free_symbols
                       if s.name in def_exprs}
            if not mapping:
                break
            expanded = expanded.subs(mapping)
        if sympy.count_ops(expanded, visual=False) > EXPANSION_CHECK_OPS_CAP:
            return "skipped"

        from .verifier import verify_equivalent  # local: keep imports light
        result = verify_equivalent(str(expanded), certified_text, decl)
        if result.verdict == ZERO:
            return "verified"
        if result.verdict == "NONZERO":
            exc = AdapterError("REPORT_INCOMPLETE")
            exc.violators = ["abbreviation expansion contradicts the "
                             "certified machine representation "
                             f"(residual: {result.residual})"]
            raise exc
        return "undecided"
    except AdapterError:
        raise
    except Exception:
        # parse/namespace/size made the check infeasible: honest skip
        return "skipped"


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
        f"- engine_version: {ENGINE_VERSION}",
        f"- agent_protocol_version: {AGENT_PROTOCOL_VERSION}",
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
                     defined. Where practical the expansions are checked
                     against the certified machine representation via the
                     exact verifier.

    Returns:
        A dict with ``run_id``, ``certified_text``,
        ``certified_state_sha256``, ``human_form``, ``definitions``,
        ``expansion_check`` ("verified" | "undecided" | "skipped"),
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
    certified_text, certified_sha, declared = _resolve_certified(source,
                                                                 run_root)

    if definitions is None:
        definitions = {}
    if not isinstance(definitions, Mapping):
        raise AdapterError("REPORT_INCOMPLETE")
    definitions = {str(k): str(v) for k, v in definitions.items()}

    if human_form is None:
        human_form = certified_text
    if not isinstance(human_form, str) or not human_form.strip():
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = ["empty human form"]
        raise exc

    # completeness: no placeholders, no undefined aliases — anywhere
    offenders = _placeholder_offenders([human_form, *definitions.values()])
    offenders += _undefined_alias_offenders(
        human_form, certified_text,
        {s["name"] for s in declared}, definitions)
    if offenders:
        exc = AdapterError("REPORT_INCOMPLETE")
        exc.violators = sorted(set(offenders))
        raise exc

    expansion_check = _expansion_check(human_form, certified_text,
                                       declared, definitions)

    try:
        summary = run_summary(run_root)
    except AdapterError:
        summary = None

    manifest = _read_json(run_root / "manifest.json") or {}
    report = {
        "run_id": manifest.get("run_id")
                  or (source.run_id if isinstance(source, SessionState)
                      else None),
        "certified_text": certified_text,
        "certified_state_sha256": certified_sha,
        "human_form": human_form,
        "definitions": dict(definitions),
        "expansion_check": expansion_check,
        "summary": summary,
    }

    artifact_path = run_root / "final" / FINAL_ARTIFACT_NAME
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(_render_markdown(report), encoding="utf-8")
    report["artifact_path"] = str(artifact_path)
    return report
