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
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from .models import NONZERO, UNKNOWN, ZERO, VerificationResult
from .provenance import build_run_record, sha256_file, write_run_record
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
    warnings: tuple[str, ...] = ()
    error_code: Optional[str] = None
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

    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
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
    error_detail: Optional[str] = None
    warnings: tuple[str, ...] = ()

    try:
        loaded = load_workspace(root)
    except WorkspaceError as exc:
        error_code = exc.code
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
        warnings=tuple(provenance["warnings"]),
        error_code=error_code,
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
    """Return an existing run report, regenerating it if it is absent.

    Regeneration uses only the persisted bounded ``result.json`` and
    ``provenance.json`` records.  It never rereads or modifies scientific
    source files.
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
        resolved_run / RESULT_FILE_NAME, "RUN_RESULT_INVALID")
    provenance = _read_json_object(
        resolved_run / "provenance.json", "RUN_PROVENANCE_INVALID")
    _validate_persisted_run(selected_run_id, result_payload, provenance)
    report_path = resolved_run / REPORT_FILE_NAME
    if report_path.exists():
        try:
            text = report_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise WorkspaceError(
                "RUN_REPORT_UNREADABLE", "report is not readable UTF-8",
                path=report_path) from None
    else:
        text = _render_report(result_payload, provenance)
        _write_text_atomic(report_path, text)
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
        )
    if not hypothesis.proof_obligations:
        raise HypothesisCompileError(
            "NO_PROOF_OBLIGATIONS",
            "an equivalence hypothesis must declare at least one obligation",
        )
    for obligation in hypothesis.proof_obligations:
        if obligation.relation != "equivalent":
            raise HypothesisCompileError(
                "UNSUPPORTED_RELATION",
                "v0.1 supports only relation 'equivalent'",
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
            f"The run stopped with `{error_code}`. Correct the declared "
            "workspace or hypothesis and run verification again.",
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
        f"- Git commit: `{provenance['git_commit']}`",
        f"- Python: `{provenance['python_version']}`",
        f"- Hypothesis SHA-256: `{provenance['hypothesis_hash']}`",
        f"- Assumptions SHA-256: `{provenance['assumptions_hash']}`",
        "- Complete input and expression hashes: `provenance.json`",
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


def _read_json_object(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
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
