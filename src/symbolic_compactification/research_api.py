"""Stable Python API for researcher-workspace hypothesis verification.

The v0.1 API deliberately compiles one narrow obligation language: an
``equivalence`` hypothesis containing one or more ``equivalent`` relations
between declared expression members.  Every relation is adjudicated by the
existing exact verifier.  Unsupported scientific structures fail closed as
``COMPILE_FAILURE``; malformed workspaces and inputs fail as
``PARSE_FAILURE``.

Every attempt against an existing workspace directory creates an immutable
run directory containing provenance, structured result details, and a
human-readable report.  Source files are only opened for reading.
"""
from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from .models import NONZERO, UNKNOWN, ZERO, VerificationResult
from .provenance import build_run_record, sha256_file, write_run_record
from .security import REDACTED, redact_public_data, redact_text
from .verifier import verify_equivalent
from .workspace import ResearchWorkspace, WorkspaceError, load_workspace

PathLike = Union[str, os.PathLike]

RESULT_SCHEMA_VERSION = "ResearchHypothesisVerificationV1"
RESULT_FILE_NAME = "result.json"
REPORT_FILE_NAME = "REPORT.md"
VERIFIER_ROUTE = "python_sympy_exact_v1"

PARSE_FAILURE = "PARSE_FAILURE"
COMPILE_FAILURE = "COMPILE_FAILURE"
ASSUMPTION_REQUIRED = "ASSUMPTION_REQUIRED"
PUBLIC_RESULTS = frozenset({
    ZERO, NONZERO, UNKNOWN, PARSE_FAILURE, COMPILE_FAILURE,
    ASSUMPTION_REQUIRED,
})

_ASSUMPTION_GATE_CODES = frozenset({"DECLARED_ASSUMPTIONS_OMITTED"})

_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_SUMMARY_MAX_STRING = 2_048
_SUMMARY_MAX_ITEMS = 128
_SUMMARY_MAX_DEPTH = 12
_TRUNCATED = "[TRUNCATED]"
_MAX_RUN_ARTIFACT_BYTES = 1_048_576

_ARTIFACT_INVENTORY = (
    {"path": "provenance.json", "role": "immutable run provenance"},
    {"path": "result.json", "role": "structured result and bounded workspace summary"},
    {"path": "REPORT.md", "role": "human-readable verification report"},
)

_ERROR_ACTION_HINTS = {
    "PROJECT_PARSE_FAILURE": (
        "Validate project.yaml as UTF-8 YAML with only the documented fields."
    ),
    "PROJECT_SCHEMA_INVALID": (
        "Correct project.yaml to the minimal schema documented in WORKSPACE_FORMAT.md."
    ),
    "ASSUMPTIONS_PARSE_FAILURE": (
        "Validate the declared assumptions YAML and avoid aliases or anchors."
    ),
    "ASSUMPTIONS_SCHEMA_INVALID": (
        "Declare each symbol/function using the assumptions schema; do not infer it."
    ),
    "HYPOTHESIS_PARSE_FAILURE": (
        "Validate hypotheses/hypothesis.json as UTF-8 JSON with unique keys."
    ),
    "HYPOTHESIS_SCHEMA_INVALID": (
        "Correct the hypothesis members, assumptions, and obligations to schema version 1."
    ),
    "DECLARED_ASSUMPTIONS_OMITTED": (
        "List every declared symbol explicitly in hypothesis.assumptions_used."
    ),
    "EXPRESSION_PARSE_FAILURE": (
        "Correct the named expression and declare every symbol/function in the assumptions file."
    ),
    "UNSUPPORTED_HYPOTHESIS_TYPE": (
        "Set hypothesis_type to 'equivalence'; other types are not compiled in v0.1."
    ),
    "NO_PROOF_OBLIGATIONS": (
        "Add at least one explicit equivalence proof obligation."
    ),
    "UNSUPPORTED_RELATION": (
        "Set the named proof-obligation relation to 'equivalent'."
    ),
}


@dataclass(frozen=True)
class ObligationVerification:
    """One compiled equivalence obligation and its exact verifier result."""

    obligation_id: str
    relation: str
    left: str
    right: str
    result: VerificationResult

    @property
    def verdict(self) -> str:
        return self.result.verdict

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "relation": self.relation,
            "left": self.left,
            "right": self.right,
            "verdict": self.verdict,
            "verification": self.result.to_dict(),
        }


@dataclass(frozen=True)
class HypothesisVerificationResult:
    """Aggregate fail-closed result plus paths to its persisted run."""

    result: str
    run_id: str
    run_directory: Path
    provenance_path: Path
    result_path: Path
    report_path: Path
    obligations: tuple[ObligationVerification, ...]
    runtime_seconds: float
    workspace_summary: Optional[dict[str, Any]] = None
    artifact_inventory: tuple[dict[str, str], ...] = _ARTIFACT_INVENTORY
    warnings: tuple[str, ...] = ()
    error_code: Optional[str] = None
    error_source: Optional[str] = None
    action_hint: Optional[str] = None
    error_detail: Optional[str] = None

    @property
    def verdict(self) -> str:
        """Alias retained for callers that think in verifier verdicts."""
        return self.result

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-native public view, including artifact locations."""
        return {
            **self._artifact_payload(),
            "run_directory": str(self.run_directory),
            "provenance_path": str(self.provenance_path),
            "result_path": str(self.result_path),
            "report_path": str(self.report_path),
        }

    def _artifact_payload(self) -> dict[str, Any]:
        """Return the bounded payload persisted inside the run directory."""
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "run_id": self.run_id,
            "result": self.result,
            "verifier_route": VERIFIER_ROUTE,
            "runtime_seconds": self.runtime_seconds,
            "warnings": list(self.warnings),
            "error_code": self.error_code,
            "error_source": self.error_source,
            "action_hint": self.action_hint,
            "workspace_summary": self.workspace_summary,
            "artifact_inventory": [dict(item) for item in self.artifact_inventory],
            "obligations": [item.to_dict() for item in self.obligations],
        }


@dataclass(frozen=True)
class GeneratedReport:
    """A human-readable run report and the path that owns it."""

    run_id: str
    result: str
    path: Path
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "result": self.result,
            "path": str(self.path),
            "text": self.text,
        }


class HypothesisCompileError(ValueError):
    """Internal compiler boundary with a stable, non-sensitive code."""

    def __init__(self, code: str, detail: str, *, source: str):
        self.code = code
        self.detail = detail
        self.source = source
        super().__init__(f"{code}: {detail}")


def verify_hypothesis(
    workspace: PathLike | ResearchWorkspace,
    *,
    run_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> HypothesisVerificationResult:
    """Load, compile, and exactly adjudicate a workspace hypothesis.

    A supplied :class:`ResearchWorkspace` is deliberately reloaded from its
    root so verification and provenance are tied to current source bytes.
    Existing researcher files are never written; generated artifacts are
    placed only in ``workspace/runs/<run_id>/``.

    ``run_id`` and ``timestamp`` are optional reproducibility hooks.  Invalid
    or duplicate values are rejected by the provenance layer.
    """
    started = time.monotonic()
    root = _workspace_root(workspace)
    runs_directory = _safe_runs_directory(root)
    loaded: Optional[ResearchWorkspace] = None
    obligations: tuple[ObligationVerification, ...] = ()
    result = PARSE_FAILURE
    error_code: Optional[str] = None
    error_source: Optional[str] = None
    action_hint: Optional[str] = None
    error_detail: Optional[str] = None
    warnings: tuple[str, ...] = ()

    try:
        loaded = load_workspace(root)
    except WorkspaceError as exc:
        error_code = exc.code
        error_source = _safe_workspace_error_source(root, exc)
        action_hint = _action_hint_for_error(exc.code)
        error_detail = exc.detail
        if exc.code in _ASSUMPTION_GATE_CODES:
            result = ASSUMPTION_REQUIRED
            warnings = (f"assumption_required:{exc.code}",)
        else:
            warnings = (f"workspace_parse_failure:{exc.code}",)
    else:
        try:
            compiled = _compile_equivalence_obligations(loaded)
        except HypothesisCompileError as exc:
            result = COMPILE_FAILURE
            error_code = exc.code
            error_source = exc.source
            action_hint = _action_hint_for_error(exc.code)
            error_detail = exc.detail
            warnings = (f"hypothesis_compile_failure:{exc.code}",)
        else:
            expression_by_path = {
                _relative_expression_path(loaded, record.source_path): record
                for record in loaded.expressions
            }
            checked = []
            for obligation in compiled:
                left = expression_by_path[obligation.left]
                right = expression_by_path[obligation.right]
                exact = verify_equivalent(
                    left.text,
                    right.text,
                    list(loaded.symbols),
                    functions=list(loaded.functions),
                )
                checked.append(ObligationVerification(
                    obligation_id=obligation.obligation_id,
                    relation=obligation.relation,
                    left=obligation.left,
                    right=obligation.right,
                    result=exact,
                ))
            obligations = tuple(checked)
            result = _aggregate_verdicts(item.verdict for item in obligations)

    workspace_summary, summary_truncated = _workspace_summary(loaded)
    if summary_truncated:
        warnings = (*warnings, "workspace_summary_truncated")

    runtime_seconds = round(max(0.0, time.monotonic() - started), 6)
    input_hashes, expression_hashes, hypothesis_hash, assumptions_hash = (
        _loaded_hashes(loaded) if loaded is not None else _fallback_hashes(root)
    )
    provenance = build_run_record(
        input_hashes=input_hashes,
        expression_hashes=expression_hashes,
        hypothesis_hash=hypothesis_hash,
        assumptions_hash=assumptions_hash,
        verifier_route=VERIFIER_ROUTE,
        result=result,
        runtime_seconds=runtime_seconds,
        warnings=warnings,
        run_id=run_id,
        timestamp=timestamp,
    )
    provenance_path = write_run_record(runs_directory, provenance)
    run_directory = provenance_path.parent
    provisional = HypothesisVerificationResult(
        result=result,
        run_id=provenance["run_id"],
        run_directory=run_directory,
        provenance_path=provenance_path,
        result_path=run_directory / RESULT_FILE_NAME,
        report_path=run_directory / REPORT_FILE_NAME,
        obligations=obligations,
        runtime_seconds=runtime_seconds,
        workspace_summary=workspace_summary,
        warnings=tuple(provenance["warnings"]),
        error_code=error_code,
        error_source=error_source,
        action_hint=action_hint,
        error_detail=error_detail,
    )
    _write_json_atomic(provisional.result_path, provisional._artifact_payload())
    _write_text_atomic(provisional.report_path, _render_report(
        provisional._artifact_payload(), provenance))
    return provisional


def generate_report(
    workspace: PathLike | ResearchWorkspace,
    run: str | HypothesisVerificationResult,
) -> GeneratedReport:
    """Return a validated run report, regenerating it if it is absent.

    Regeneration uses only the persisted bounded ``result.json`` and
    ``provenance.json`` records.  It never rereads or modifies scientific
    source files.  An existing report is never trusted as authority: it must
    be a bounded regular file whose bytes exactly match a fresh render of the
    validated structured artifacts.
    """
    root = _workspace_root(workspace)
    runs_directory = _safe_runs_directory(root)
    selected_run_id = run.run_id if isinstance(
        run, HypothesisVerificationResult) else run
    if (not isinstance(selected_run_id, str)
            or not _RUN_ID_RE.fullmatch(selected_run_id)):
        raise WorkspaceError(
            "RUN_ID_INVALID", "run id has an invalid format", path=root)
    run_directory = runs_directory / selected_run_id
    if run_directory.is_symlink():
        raise WorkspaceError(
            "RUN_NOT_FOUND", "run must not be a symbolic link",
            path=run_directory)
    try:
        resolved_run = run_directory.resolve(strict=True)
        resolved_run.relative_to(runs_directory.resolve(strict=True))
    except (OSError, ValueError):
        raise WorkspaceError(
            "RUN_NOT_FOUND", "run does not exist", path=run_directory) from None
    if not resolved_run.is_dir():
        raise WorkspaceError(
            "RUN_NOT_FOUND", "run is not a regular directory", path=run_directory)

    result_payload = _read_json_object(
        resolved_run / RESULT_FILE_NAME,
        "RUN_RESULT_INVALID",
        runs_directory=runs_directory,
        run_directory=resolved_run,
    )
    provenance = _read_json_object(
        resolved_run / "provenance.json",
        "RUN_PROVENANCE_INVALID",
        runs_directory=runs_directory,
        run_directory=resolved_run,
    )
    _validate_persisted_run(selected_run_id, result_payload, provenance)
    text = _render_report(result_payload, provenance)
    rendered = text.encode("utf-8")
    if len(rendered) > _MAX_RUN_ARTIFACT_BYTES:
        raise WorkspaceError(
            "RUN_REPORT_INVALID",
            "freshly rendered report exceeds the safe artifact limit",
            path=resolved_run / REPORT_FILE_NAME,
        )

    report_path = resolved_run / REPORT_FILE_NAME
    if _path_entry_exists(report_path):
        existing = _read_run_artifact_bytes(
            report_path,
            "RUN_REPORT_INVALID",
            runs_directory=runs_directory,
            run_directory=resolved_run,
        )
        if existing != rendered:
            raise WorkspaceError(
                "RUN_REPORT_MISMATCH",
                "existing report does not match validated run artifacts",
                path=report_path,
            )
    else:
        _write_text_atomic(report_path, text)
        # Fail closed if another process replaced the generated artifact before
        # it could be returned to the caller.
        persisted = _read_run_artifact_bytes(
            report_path,
            "RUN_REPORT_INVALID",
            runs_directory=runs_directory,
            run_directory=resolved_run,
        )
        if persisted != rendered:
            raise WorkspaceError(
                "RUN_REPORT_MISMATCH",
                "generated report does not match validated run artifacts",
                path=report_path,
            )
    return GeneratedReport(
        run_id=selected_run_id,
        result=result_payload["result"],
        path=report_path,
        text=text,
    )


def _workspace_root(workspace: PathLike | ResearchWorkspace) -> Path:
    raw = workspace.root if isinstance(workspace, ResearchWorkspace) else workspace
    try:
        root = Path(raw).resolve(strict=True)
    except (OSError, TypeError):
        raise WorkspaceError(
            "WORKSPACE_NOT_FOUND", "workspace directory does not exist") from None
    if not root.is_dir():
        raise WorkspaceError(
            "WORKSPACE_NOT_DIRECTORY", "workspace path is not a directory",
            path=root)
    return root


def _safe_runs_directory(root: Path) -> Path:
    runs = root / "runs"
    if runs.is_symlink():
        raise WorkspaceError(
            "RUNS_DIRECTORY_UNSAFE", "runs must not be a symbolic link",
            path=runs)
    if runs.exists() and not runs.is_dir():
        raise WorkspaceError(
            "RUNS_DIRECTORY_UNSAFE", "runs must be a directory", path=runs)
    try:
        runs.mkdir(exist_ok=True)
        resolved = runs.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        raise WorkspaceError(
            "RUNS_DIRECTORY_UNSAFE", "runs is not writable inside workspace",
            path=runs) from None
    return resolved


def _compile_equivalence_obligations(workspace: ResearchWorkspace):
    hypothesis = workspace.hypothesis
    if hypothesis.hypothesis_type != "equivalence":
        raise HypothesisCompileError(
            "UNSUPPORTED_HYPOTHESIS_TYPE",
            "v0.1 supports only hypothesis_type 'equivalence'",
            source="hypotheses/hypothesis.json#/hypothesis_type",
        )
    if not hypothesis.proof_obligations:
        raise HypothesisCompileError(
            "NO_PROOF_OBLIGATIONS",
            "an equivalence hypothesis must declare at least one obligation",
            source="hypotheses/hypothesis.json#/proof_obligations",
        )
    for index, obligation in enumerate(hypothesis.proof_obligations):
        if obligation.relation != "equivalent":
            raise HypothesisCompileError(
                "UNSUPPORTED_RELATION",
                "v0.1 supports only relation 'equivalent'",
                source=("hypotheses/hypothesis.json#/proof_obligations/"
                        f"{index}/relation"),
            )
    return hypothesis.proof_obligations


def _aggregate_verdicts(verdicts) -> str:
    values = tuple(verdicts)
    if not values:
        return COMPILE_FAILURE
    if any(value == NONZERO for value in values):
        return NONZERO
    if any(value != ZERO for value in values):
        return UNKNOWN
    return ZERO


def _relative_expression_path(
    workspace: ResearchWorkspace,
    source_path: Optional[str],
) -> str:
    if source_path is None:
        raise WorkspaceError(
            "WORKSPACE_STATE_INVALID", "expression has no source path")
    try:
        return Path(source_path).relative_to(workspace.root).as_posix()
    except ValueError:
        raise WorkspaceError(
            "WORKSPACE_STATE_INVALID", "expression path is outside workspace") from None


def _loaded_hashes(workspace: ResearchWorkspace):
    inputs = {
        workspace.project_source.relative_path: workspace.project_source.sha256,
        workspace.assumptions_source.relative_path: workspace.assumptions_source.sha256,
        workspace.hypothesis_source.relative_path: workspace.hypothesis_source.sha256,
    }
    for source in (*workspace.notes, *workspace.references):
        inputs[source.relative_path] = source.sha256
    expressions = {
        _relative_expression_path(workspace, record.source_path): record.sha256
        for record in workspace.expressions
    }
    return (
        inputs,
        expressions,
        workspace.hypothesis_source.sha256,
        workspace.assumptions_source.sha256,
    )


def _fallback_hashes(root: Path):
    """Hash a fixed, non-secret file inventory after a load failure."""
    inputs: dict[str, str] = {}
    expressions: dict[str, str] = {}
    candidates = [
        (root / "project.yaml", inputs),
        (root / "hypotheses" / "hypothesis.json", inputs),
        (root / "assumptions" / "assumptions.yaml", inputs),
    ]
    expression_directory = root / "expressions"
    if expression_directory.is_dir() and not expression_directory.is_symlink():
        candidates.extend(
            (path, expressions)
            for path in sorted(expression_directory.glob("*.txt"))
        )
    for path, target in candidates:
        if path.is_symlink() or not path.is_file():
            continue
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(root)
            target[resolved.relative_to(root).as_posix()] = sha256_file(resolved)
        except (OSError, ValueError):
            continue
    hypothesis_hash = inputs.get("hypotheses/hypothesis.json")
    assumptions_hash = inputs.get("assumptions/assumptions.yaml")
    return inputs, expressions, hypothesis_hash, assumptions_hash


def _action_hint_for_error(code: str) -> Optional[str]:
    """Return one stable remediation hint without echoing user input."""
    return _ERROR_ACTION_HINTS.get(code)


def _safe_workspace_error_source(
    root: Path,
    error: WorkspaceError,
) -> Optional[str]:
    """Return a bounded workspace-relative location for a public diagnostic.

    Raw exception detail and absolute host paths never cross this boundary.
    If the reported path cannot be proven to be inside the workspace, a fixed
    schema location is used instead.
    """
    if error.path:
        try:
            relative = Path(error.path).resolve(strict=False).relative_to(
                root.resolve(strict=True)).as_posix()
        except (OSError, ValueError):
            relative = ""
        if relative and len(relative) <= 512:
            return redact_text(relative)

    if error.code.startswith("PROJECT_"):
        return "project.yaml"
    if error.code.startswith("ASSUMPTIONS_"):
        return "declared assumptions file"
    if (error.code.startswith("HYPOTHESIS_")
            or error.code == "DECLARED_ASSUMPTIONS_OMITTED"):
        return "hypotheses/hypothesis.json"
    if error.code == "EXPRESSION_PARSE_FAILURE":
        return "declared expression member"
    return None


def _bounded_public_value(value: Any) -> tuple[Any, bool]:
    """Redact and bound a JSON-like summary before it is persisted."""
    safe = redact_public_data(value)

    def bound(item: Any, depth: int) -> tuple[Any, bool]:
        if depth > _SUMMARY_MAX_DEPTH:
            return REDACTED, True
        if item is None or isinstance(item, (bool, int, float)):
            return item, False
        if isinstance(item, str):
            if len(item) <= _SUMMARY_MAX_STRING:
                return item, False
            return item[:_SUMMARY_MAX_STRING] + _TRUNCATED, True
        if isinstance(item, list):
            output = []
            truncated = len(item) > _SUMMARY_MAX_ITEMS
            for child in item[:_SUMMARY_MAX_ITEMS]:
                normalized, child_truncated = bound(child, depth + 1)
                output.append(normalized)
                truncated = truncated or child_truncated
            return output, truncated
        if isinstance(item, Mapping):
            output = {}
            keys = sorted(item, key=str)
            truncated = len(keys) > _SUMMARY_MAX_ITEMS
            for key in keys[:_SUMMARY_MAX_ITEMS]:
                normalized, child_truncated = bound(item[key], depth + 1)
                output[str(key)[:_SUMMARY_MAX_STRING]] = normalized
                truncated = truncated or child_truncated
            return output, truncated
        return REDACTED, True

    return bound(safe, 0)


def _workspace_summary(
    workspace: Optional[ResearchWorkspace],
) -> tuple[Optional[dict[str, Any]], bool]:
    """Build the bounded context needed to regenerate a grounded report.

    Notes and references contribute path/hash/size metadata only.  Their
    contents are deliberately absent, as are expression contents.
    """
    if workspace is None:
        return None, False
    raw = {
        "project": {
            "project_name": workspace.project.project_name,
            "objective": workspace.project.objective,
            "expression_entrypoint": workspace.project.expression_entrypoint,
        },
        "assumptions": {
            "symbols": list(workspace.symbols),
            "functions": list(workspace.functions),
        },
        "hypothesis": workspace.hypothesis.to_dict(),
        "grounding": {
            "notes": [
                {
                    "path": source.relative_path,
                    "sha256": source.sha256,
                    "size_bytes": source.size_bytes,
                }
                for source in workspace.notes
            ],
            "references": [
                {
                    "path": source.relative_path,
                    "sha256": source.sha256,
                    "size_bytes": source.size_bytes,
                }
                for source in workspace.references
            ],
        },
    }
    bounded, truncated = _bounded_public_value(raw)
    return bounded, truncated


def _append_json_field(lines: list[str], label: str, value: Any) -> None:
    """Append a safely redacted JSON value as an indented Markdown block."""
    lines.extend([f"**{label}**", ""])
    encoded = json.dumps(
        redact_public_data(value), sort_keys=True, indent=2, ensure_ascii=False)
    lines.extend(f"    {line}" for line in encoded.splitlines())
    lines.append("")


def _append_hashes(
    lines: list[str],
    title: str,
    values: Mapping[str, str],
) -> None:
    lines.extend([f"### {title}", ""])
    if not values:
        lines.extend(["None recorded.", ""])
        return
    for label in sorted(values):
        lines.append(f"- `{redact_text(label)}`: `{values[label]}`")
    lines.append("")


def _render_report(result: Mapping[str, Any], provenance: Mapping[str, Any]) -> str:
    status = result["result"]
    lines = [
        "# Symbolic Compactification Verification Report",
        "",
        f"- Run: `{result['run_id']}`",
        f"- Result: **{status}**",
        f"- Verifier route: `{result['verifier_route']}`",
        f"- Runtime: `{result['runtime_seconds']:.6f}` seconds",
        "",
        "## Result semantics",
        "",
        _status_explanation(status),
        "",
    ]
    error_code = result.get("error_code")
    if error_code:
        lines.extend([
            "## Action required",
            "",
            f"- Stable error code: `{error_code}`",
        ])
        if result.get("error_source"):
            lines.append(f"- Source: `{result['error_source']}`")
        if result.get("action_hint"):
            lines.append(f"- Safe hint: {result['action_hint']}")
        lines.extend([
            "",
            "Correct the researcher-owned source explicitly, then run "
            "verification again. No scientific meaning was repaired silently.",
            "",
        ])

    summary = result.get("workspace_summary")
    lines.extend(["## Workspace and grounded hypothesis", ""])
    if isinstance(summary, Mapping):
        project = summary.get("project", {})
        assumptions = summary.get("assumptions", {})
        hypothesis = summary.get("hypothesis", {})
        grounding = summary.get("grounding", {})
        _append_json_field(lines, "Project", project)
        _append_json_field(
            lines, "Declared symbols", assumptions.get("symbols", []))
        _append_json_field(
            lines, "Declared functions", assumptions.get("functions", []))
        _append_json_field(lines, "Hypothesis", hypothesis)
        _append_json_field(
            lines, "Notes/references grounding inventory", grounding)
        lines.extend([
            "Only note/reference metadata is shown; their contents are not "
            "copied into this report.",
            "",
        ])
    else:
        lines.extend([
            "A bounded workspace summary is unavailable because validation "
            "stopped before the workspace could be loaded. Available source "
            "hashes remain recorded below.",
            "",
        ])

    lines.extend([
        "### Assumption coverage in v0.1",
        "",
        "The verifier machine-applies only declared `real` and `nonzero` "
        "symbol flags and the declared function namespace. Other domain "
        "predicates, physical conditions, boundary conditions, and regularity "
        "requirements are not inferred or certified by v0.1.",
        "",
        "`ASSUMPTION_REQUIRED` has one narrow operational meaning in v0.1: "
        "a symbol already declared in the assumptions file was omitted from "
        "the hypothesis `assumptions_used` list. It does not mean the tool "
        "discovered every additional predicate needed by the science.",
        "",
    ])

    obligations = result.get("obligations", [])
    if obligations:
        lines.extend(["## Proof obligations", ""])
        for item in obligations:
            verification = item["verification"]
            lines.extend([
                f"### {item['obligation_id']}",
                "",
                f"- Relation: `{item['relation']}`",
                f"- Left member: `{item['left']}`",
                f"- Right member: `{item['right']}`",
                f"- Verdict: **{item['verdict']}**",
                f"- Residual: `{verification['residual']}`",
                f"- Simplified residual: `{verification['simplified_residual']}`",
            ])
            if verification.get("counterexample") is not None:
                lines.append(
                    "- Exact counterexample: `" + json.dumps(
                        verification["counterexample"], sort_keys=True) + "`")
            lines.append("")
    lines.extend([
        "## Provenance",
        "",
        f"- Timestamp: `{provenance['timestamp']}`",
        f"- Tool version: `{provenance['package_version']}`",
        f"- Engine version: `{provenance['engine_version']}`",
        f"- Agent protocol version: `{provenance['agent_protocol_version']}`",
        f"- Git commit: `{provenance['git_commit']}`",
        f"- Python: `{provenance['python_implementation']} "
        f"{provenance['python_version']}`",
        f"- Verifier route: `{provenance['verifier_route']}`",
        f"- Runtime: `{provenance['runtime_seconds']:.6f}` seconds",
        f"- Hypothesis SHA-256: `{provenance['hypothesis_hash']}`",
        f"- Assumptions SHA-256: `{provenance['assumptions_hash']}`",
        "",
        "### Dependency versions",
        "",
    ])
    for name, version in sorted(provenance["dependency_versions"].items()):
        lines.append(f"- `{name}`: `{version}`")
    lines.extend(["", "### Warnings", ""])
    warnings = provenance.get("warnings", [])
    if warnings:
        lines.extend(f"- `{warning}`" for warning in warnings)
    else:
        lines.append("None.")
    lines.append("")

    lines.extend(["## Source hashes", ""])
    _append_hashes(lines, "Input files", provenance["input_hashes"])
    _append_hashes(lines, "Expression members", provenance["expression_hashes"])

    lines.extend(["## Generated artifact inventory", ""])
    inventory = result.get("artifact_inventory", _ARTIFACT_INVENTORY)
    if isinstance(inventory, (list, tuple)):
        for artifact in inventory:
            if isinstance(artifact, Mapping):
                lines.append(
                    f"- `{redact_text(str(artifact.get('path', 'unknown')))}` — "
                    f"{redact_text(str(artifact.get('role', 'generated artifact')))}"
                )
    lines.extend([
        "",
        "Generated files are under this run directory. Researcher source "
        "files were not modified.",
        "",
    ])
    return "\n".join(lines)


def _status_explanation(status: str) -> str:
    return {
        ZERO: (
            "`ZERO` means every declared obligation was exactly certified "
            "under the declared engine semantics and assumptions."
        ),
        NONZERO: (
            "`NONZERO` means at least one declared obligation was refuted by "
            "the exact verification route."
        ),
        UNKNOWN: (
            "`UNKNOWN` means the system could not decide at least one "
            "obligation. It is neither likely true nor likely false, and it "
            "does not permit scientific promotion."
        ),
        PARSE_FAILURE: (
            "`PARSE_FAILURE` means workspace metadata or a declared input "
            "could not be validated and no scientific relation was checked."
        ),
        COMPILE_FAILURE: (
            "`COMPILE_FAILURE` means the declared hypothesis is outside the "
            "supported v0.1 equivalence-obligation language and no scientific "
            "relation was checked."
        ),
        ASSUMPTION_REQUIRED: (
            "`ASSUMPTION_REQUIRED` means the hypothesis omitted a declared "
            "scientific assumption. No scientific relation was checked and "
            "nothing was silently inferred; update the researcher-owned "
            "hypothesis explicitly before retrying."
        ),
    }[status]


def _path_entry_exists(path: Path) -> bool:
    """Return whether a directory entry exists without following symlinks."""
    try:
        os.lstat(path)
    except FileNotFoundError:
        return False
    except OSError:
        # An unreadable entry must flow through the fail-closed artifact reader
        # rather than being mistaken for an absent report that may be replaced.
        return True
    return True


def _read_run_artifact_bytes(
    path: Path,
    code: str,
    *,
    runs_directory: Path,
    run_directory: Path,
    max_bytes: int = _MAX_RUN_ARTIFACT_BYTES,
) -> bytes:
    """Read one bounded regular artifact without following a symlink.

    Both enclosing directories are trusted inputs established by the caller.
    This function revalidates their containment, opens the run directory and
    artifact by file descriptor, rejects every non-regular final component,
    and detects changes during the bounded read.  Artifact bytes never appear
    in an exception.
    """

    def fail(detail: str) -> WorkspaceError:
        return WorkspaceError(code, detail, path=path)

    if (isinstance(max_bytes, bool) or not isinstance(max_bytes, int)
            or max_bytes < 1):
        raise fail("run artifact size limit is invalid")

    candidate = Path(path)
    run_root = Path(run_directory)
    runs_root = Path(runs_directory)
    try:
        if runs_root.is_symlink() or run_root.is_symlink():
            raise ValueError
        resolved_runs = runs_root.resolve(strict=True)
        resolved_run = run_root.resolve(strict=True)
        resolved_run.relative_to(resolved_runs)
        if not resolved_runs.is_dir() or not resolved_run.is_dir():
            raise ValueError
        if candidate.name in ("", ".", ".."):
            raise ValueError
        if candidate.parent.resolve(strict=True) != resolved_run:
            raise ValueError
    except (OSError, ValueError):
        raise fail("run artifact path is outside the validated run") from None

    directory_flags = os.O_RDONLY
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_flags |= getattr(os, "O_DIRECTORY", 0)
    directory_flags |= getattr(os, "O_NOFOLLOW", 0)
    artifact_flags = os.O_RDONLY
    artifact_flags |= getattr(os, "O_CLOEXEC", 0)
    artifact_flags |= getattr(os, "O_NOFOLLOW", 0)

    directory_fd: Optional[int] = None
    artifact_fd: Optional[int] = None
    try:
        directory_fd = os.open(resolved_run, directory_flags)
        before_entry = os.stat(
            candidate.name, dir_fd=directory_fd, follow_symlinks=False)
        if not stat.S_ISREG(before_entry.st_mode):
            raise fail("run artifact must be a regular file")
        if before_entry.st_size > max_bytes:
            raise fail("run artifact exceeds the safe size limit")

        artifact_fd = os.open(
            candidate.name, artifact_flags, dir_fd=directory_fd)
        before_open = os.fstat(artifact_fd)
        if (not stat.S_ISREG(before_open.st_mode)
                or (before_entry.st_dev, before_entry.st_ino)
                != (before_open.st_dev, before_open.st_ino)):
            raise fail("run artifact changed before it could be read safely")
        if before_open.st_size > max_bytes:
            raise fail("run artifact exceeds the safe size limit")

        chunks: list[bytes] = []
        remaining = max_bytes + 1
        while remaining:
            block = os.read(artifact_fd, min(65_536, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        payload = b"".join(chunks)
        after_open = os.fstat(artifact_fd)
        if len(payload) > max_bytes:
            raise fail("run artifact exceeds the safe size limit")
        before_identity = (
            before_open.st_dev,
            before_open.st_ino,
            before_open.st_size,
            before_open.st_mtime_ns,
            before_open.st_ctime_ns,
        )
        after_identity = (
            after_open.st_dev,
            after_open.st_ino,
            after_open.st_size,
            after_open.st_mtime_ns,
            after_open.st_ctime_ns,
        )
        if before_identity != after_identity or len(payload) != after_open.st_size:
            raise fail("run artifact changed while it was being read")
        return payload
    except WorkspaceError:
        raise
    except OSError:
        raise fail("run artifact is missing, unsafe, or unreadable") from None
    finally:
        if artifact_fd is not None:
            try:
                os.close(artifact_fd)
            except OSError:
                pass
        if directory_fd is not None:
            try:
                os.close(directory_fd)
            except OSError:
                pass


def _read_json_object(
    path: Path,
    code: str,
    *,
    runs_directory: Path,
    run_directory: Path,
) -> dict[str, Any]:
    try:
        raw = _read_run_artifact_bytes(
            path,
            code,
            runs_directory=runs_directory,
            run_directory=run_directory,
        )
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise WorkspaceError(code, "run artifact is missing or invalid", path=path) from None
    if not isinstance(value, dict):
        raise WorkspaceError(code, "run artifact must be an object", path=path)
    return value


def _validate_persisted_run(
    run_id: str,
    result: Mapping[str, Any],
    provenance: Mapping[str, Any],
) -> None:
    if (result.get("schema_version") != RESULT_SCHEMA_VERSION
            or result.get("run_id") != run_id
            or provenance.get("run_id") != run_id
            or result.get("result") not in PUBLIC_RESULTS
            or provenance.get("result") != result.get("result")):
        raise WorkspaceError(
            "RUN_ARTIFACT_MISMATCH",
            "result and provenance do not identify the same valid run",
        )


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    _write_bytes_atomic(
        path,
        (json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)
         + "\n").encode("utf-8"),
    )


def _write_text_atomic(path: Path, text: str) -> None:
    _write_bytes_atomic(path, text.encode("utf-8"))


def _write_bytes_atomic(path: Path, payload: bytes) -> None:
    fd, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


__all__ = [
    "ASSUMPTION_REQUIRED",
    "COMPILE_FAILURE",
    "GeneratedReport",
    "HypothesisVerificationResult",
    "ObligationVerification",
    "PARSE_FAILURE",
    "REPORT_FILE_NAME",
    "RESULT_FILE_NAME",
    "RESULT_SCHEMA_VERSION",
    "generate_report",
    "verify_hypothesis",
]
