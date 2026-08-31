"""Minimal external researcher workspace for the v0.1 research preview.

The workspace layer is deliberately small.  It validates and loads user-owned
source files without mutating them; run creation and verification live in the
session/API layers.  All paths declared by metadata are relative to, and
contained by, the workspace root (including after symlink resolution).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml
from yaml.tokens import AliasToken, AnchorToken

from .models import AdapterError, ExpressionRecord, normalize_symbols
from .parser import load_expression, normalize_functions

PROJECT_FILE = "project.yaml"
ASSUMPTIONS_DIRECTORY = "assumptions"
EXPRESSIONS_DIRECTORY = "expressions"
HYPOTHESES_DIRECTORY = "hypotheses"
NOTES_DIRECTORY = "notes"
REFERENCES_DIRECTORY = "references"
RUNS_DIRECTORY = "runs"

_PROJECT_KEYS = frozenset({
    "project_name",
    "objective",
    "expression_entrypoint",
    "assumptions_file",
    "optional_notes",
    "optional_references",
})
_PROJECT_REQUIRED = frozenset({
    "project_name", "objective", "expression_entrypoint", "assumptions_file",
})
_ASSUMPTION_KEYS = frozenset({"symbols", "functions"})
_HYPOTHESIS_KEYS = frozenset({
    "schema_version",
    "hypothesis_type",
    "members",
    "latent_object",
    "operators",
    "instance_maps",
    "reconstruction_rule",
    "assumptions_used",
    "proof_obligations",
})
_HYPOTHESIS_REQUIRED = frozenset({
    "hypothesis_type", "members", "assumptions_used",
})
_OBLIGATION_KEYS = frozenset({"obligation_id", "relation", "left", "right"})
_OBLIGATION_REQUIRED = _OBLIGATION_KEYS
_MAX_METADATA_BYTES = 1_048_576


class WorkspaceError(ValueError):
    """User-facing workspace failure with a stable machine-readable code."""

    def __init__(self, code: str, detail: str, *, path: Optional[Path] = None):
        self.code = code
        self.detail = detail
        self.path = None if path is None else str(path)
        location = "" if path is None else f" ({path})"
        super().__init__(f"{code}{location}: {detail}")


@dataclass(frozen=True)
class WorkspaceSource:
    """An immutable snapshot of one loaded, user-owned source file."""

    kind: str
    relative_path: str
    absolute_path: Path
    sha256: str
    size_bytes: int
    text: Optional[str] = None


@dataclass(frozen=True)
class WorkspaceProject:
    project_name: str
    objective: str
    expression_entrypoint: str
    assumptions_file: str
    optional_notes: tuple[str, ...]
    optional_references: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "project_name": self.project_name,
            "objective": self.objective,
            "expression_entrypoint": self.expression_entrypoint,
            "assumptions_file": self.assumptions_file,
            "optional_notes": list(self.optional_notes),
            "optional_references": list(self.optional_references),
        }


@dataclass(frozen=True)
class HypothesisObligation:
    obligation_id: str
    relation: str
    left: str
    right: str

    def to_dict(self) -> dict:
        return {
            "obligation_id": self.obligation_id,
            "relation": self.relation,
            "left": self.left,
            "right": self.right,
        }


@dataclass(frozen=True)
class WorkspaceHypothesis:
    schema_version: int
    hypothesis_type: str
    members: tuple[str, ...]
    latent_object: Optional[str]
    operators: tuple[str, ...]
    instance_maps: dict
    reconstruction_rule: Optional[str]
    assumptions_used: tuple[str, ...]
    proof_obligations: tuple[HypothesisObligation, ...]
    normalized_simple_form: bool = False

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "hypothesis_type": self.hypothesis_type,
            "members": list(self.members),
            "latent_object": self.latent_object,
            "operators": list(self.operators),
            "instance_maps": dict(self.instance_maps),
            "reconstruction_rule": self.reconstruction_rule,
            "assumptions_used": list(self.assumptions_used),
            "proof_obligations": [o.to_dict() for o in self.proof_obligations],
        }


@dataclass(frozen=True)
class ResearchWorkspace:
    """Validated read-only snapshot of an external researcher workspace."""

    root: Path
    project: WorkspaceProject
    symbols: tuple[dict, ...]
    functions: tuple[str, ...]
    hypothesis: WorkspaceHypothesis
    expressions: tuple[ExpressionRecord, ...]
    notes: tuple[WorkspaceSource, ...]
    references: tuple[WorkspaceSource, ...]
    project_source: WorkspaceSource
    assumptions_source: WorkspaceSource
    hypothesis_source: WorkspaceSource

    @property
    def current_expression(self) -> ExpressionRecord:
        for record in self.expressions:
            relative = Path(record.source_path or "").relative_to(self.root)
            if relative.as_posix() == self.project.expression_entrypoint:
                return record
        raise WorkspaceError(
            "WORKSPACE_STATE_INVALID",
            "the expression entrypoint is absent from the loaded members",
            path=self.root,
        )


def _read_bytes(path: Path, *, metadata: bool = False) -> bytes:
    try:
        if not path.is_file():
            raise WorkspaceError(
                "SOURCE_FILE_MISSING", "expected a regular file", path=path)
        raw = path.read_bytes()
        if metadata and len(raw) > _MAX_METADATA_BYTES:
            raise WorkspaceError(
                "METADATA_TOO_LARGE",
                f"metadata exceeds {_MAX_METADATA_BYTES} bytes",
                path=path,
            )
        return raw
    except WorkspaceError:
        raise
    except OSError as exc:
        raise WorkspaceError(
            "SOURCE_FILE_UNREADABLE", str(exc), path=path) from None


def _decode_text(raw: bytes, path: Path, code: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        raise WorkspaceError(code, "file must be UTF-8", path=path) from None


def _source_from_bytes(
    path: Path,
    root: Path,
    kind: str,
    raw: bytes,
    *,
    text: bool,
) -> WorkspaceSource:
    """Build provenance from the exact immutable bytes used by the parser."""
    content = _decode_text(raw, path, "SOURCE_FILE_NOT_UTF8") if text else None
    return WorkspaceSource(
        kind=kind,
        relative_path=path.relative_to(root).as_posix(),
        absolute_path=path,
        sha256=hashlib.sha256(raw).hexdigest(),
        size_bytes=len(raw),
        text=content,
    )


def _source(path: Path, root: Path, kind: str, *, text: bool) -> WorkspaceSource:
    return _source_from_bytes(
        path, root, kind, _read_bytes(path), text=text)


def _safe_yaml_mapping(raw: bytes, path: Path, code: str) -> dict:
    text = _decode_text(raw, path, code)
    try:
        tokens = yaml.scan(text)
        if any(isinstance(token, (AliasToken, AnchorToken)) for token in tokens):
            raise WorkspaceError(
                code, "YAML anchors and aliases are not permitted", path=path)
        value = yaml.safe_load(text)
    except WorkspaceError:
        raise
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None) or "invalid YAML"
        raise WorkspaceError(code, problem, path=path) from None
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise WorkspaceError(code, "top-level YAML value must be a mapping", path=path)
    return value


def _strict_json_mapping(raw: bytes, path: Path, code: str) -> dict:
    text = _decode_text(raw, path, code)

    def no_duplicates(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=no_duplicates)
    except (json.JSONDecodeError, ValueError) as exc:
        raise WorkspaceError(code, str(exc), path=path) from None
    if not isinstance(value, dict):
        raise WorkspaceError(code, "top-level JSON value must be an object", path=path)
    return value


def _keys(value: dict, *, allowed: frozenset, required: frozenset,
          code: str, path: Path) -> None:
    unknown = sorted(set(value) - allowed)
    missing = sorted(required - set(value))
    if unknown:
        raise WorkspaceError(code, f"unknown fields: {', '.join(unknown)}", path=path)
    if missing:
        raise WorkspaceError(code, f"missing fields: {', '.join(missing)}", path=path)


def _string(value: Any, field: str, code: str, path: Path,
            *, optional: bool = False) -> Optional[str]:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise WorkspaceError(code, f"{field} must be a non-empty string", path=path)
    return value.strip()


def _string_list(value: Any, field: str, code: str, path: Path,
                 *, allow_scalar: bool = False) -> tuple[str, ...]:
    if value is None:
        return ()
    if allow_scalar and isinstance(value, str):
        value = [value]
    if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value):
        raise WorkspaceError(code, f"{field} must be a list of non-empty strings", path=path)
    normalized = tuple(item.strip() for item in value)
    if len(normalized) != len(set(normalized)):
        raise WorkspaceError(code, f"{field} contains duplicates", path=path)
    return normalized


def _contained_path(root: Path, raw: str, field: str, category: str) -> tuple[str, Path]:
    if not isinstance(raw, str) or not raw.strip():
        raise WorkspaceError("WORKSPACE_PATH_INVALID", f"{field} must be a path string")
    if "\\" in raw:
        raise WorkspaceError(
            "WORKSPACE_PATH_INVALID",
            f"{field} must use portable '/' separators",
        )
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise WorkspaceError(
            "PATH_OUTSIDE_WORKSPACE",
            f"{field} must be a normalized workspace-relative path",
        )
    if not relative.parts or relative.parts[0] != category:
        raise WorkspaceError(
            "WORKSPACE_PATH_INVALID",
            f"{field} must be under {category}/",
        )
    candidate = root / relative
    _assert_contained(root, candidate, field)
    if not candidate.is_file():
        raise WorkspaceError(
            "SOURCE_FILE_MISSING", f"{field} does not name a regular file", path=candidate)
    return relative.as_posix(), candidate


def _assert_contained(root: Path, candidate: Path, field: str) -> None:
    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, ValueError):
        raise WorkspaceError(
            "PATH_OUTSIDE_WORKSPACE",
            f"{field} resolves outside the workspace",
            path=candidate,
        ) from None


def _load_project(root: Path) -> tuple[WorkspaceProject, WorkspaceSource]:
    path = root / PROJECT_FILE
    _assert_contained(root, path, PROJECT_FILE)
    source_bytes = _read_bytes(path, metadata=True)
    raw = _safe_yaml_mapping(source_bytes, path, "PROJECT_PARSE_FAILURE")
    _keys(raw, allowed=_PROJECT_KEYS, required=_PROJECT_REQUIRED,
          code="PROJECT_SCHEMA_INVALID", path=path)
    notes = _string_list(raw.get("optional_notes"), "optional_notes",
                         "PROJECT_SCHEMA_INVALID", path, allow_scalar=True)
    references = _string_list(raw.get("optional_references"),
                              "optional_references", "PROJECT_SCHEMA_INVALID",
                              path, allow_scalar=True)
    project = WorkspaceProject(
        project_name=_string(raw["project_name"], "project_name",
                             "PROJECT_SCHEMA_INVALID", path) or "",
        objective=_string(raw["objective"], "objective",
                          "PROJECT_SCHEMA_INVALID", path) or "",
        expression_entrypoint=_string(
            raw["expression_entrypoint"], "expression_entrypoint",
            "PROJECT_SCHEMA_INVALID", path) or "",
        assumptions_file=_string(
            raw["assumptions_file"], "assumptions_file",
            "PROJECT_SCHEMA_INVALID", path) or "",
        optional_notes=notes,
        optional_references=references,
    )
    return project, _source_from_bytes(
        path, root, "project", source_bytes, text=True)


def _load_assumptions(root: Path, relative: str) -> tuple[
        tuple[dict, ...], tuple[str, ...], WorkspaceSource]:
    normalized, path = _contained_path(
        root, relative, "assumptions_file", ASSUMPTIONS_DIRECTORY)
    source_bytes = _read_bytes(path, metadata=True)
    raw = _safe_yaml_mapping(
        source_bytes, path, "ASSUMPTIONS_PARSE_FAILURE")
    _keys(raw, allowed=_ASSUMPTION_KEYS, required=frozenset({"symbols"}),
          code="ASSUMPTIONS_SCHEMA_INVALID", path=path)
    raw_symbols = raw["symbols"]
    if isinstance(raw_symbols, list) and any(
            isinstance(item, dict) and item.get("real") is False
            for item in raw_symbols):
        raise WorkspaceError(
            "UNSUPPORTED_COMPLEX_SYMBOL_SEMANTICS",
            "the v0.1 workspace rejects real:false because its complex-symbol "
            "semantics are not currently safe for certification",
            path=path,
        )
    try:
        symbols = normalize_symbols(raw_symbols)
        functions = normalize_functions(
            raw.get("functions"),
            declared_symbol_names={item["name"] for item in symbols},
        )
    except AdapterError as exc:
        raise WorkspaceError(
            "ASSUMPTIONS_SCHEMA_INVALID", exc.code, path=path) from None
    return tuple(symbols), tuple(functions), _source_from_bytes(
        path, root, "assumptions", source_bytes, text=True)


def _load_hypothesis(root: Path, symbol_names: set[str]) -> tuple[
        WorkspaceHypothesis, WorkspaceSource]:
    path = root / HYPOTHESES_DIRECTORY / "hypothesis.json"
    _assert_contained(root, path, "hypothesis")
    source_bytes = _read_bytes(path, metadata=True)
    raw = _strict_json_mapping(
        source_bytes, path, "HYPOTHESIS_PARSE_FAILURE")
    if "assumptions_used" not in raw:
        raise WorkspaceError(
            "DECLARED_ASSUMPTIONS_OMITTED",
            "assumptions_used is required and must list every declared "
            "symbol; omitted: " + ", ".join(sorted(symbol_names)),
            path=path,
        )
    _keys(raw, allowed=_HYPOTHESIS_KEYS, required=_HYPOTHESIS_REQUIRED,
          code="HYPOTHESIS_SCHEMA_INVALID", path=path)
    schema_version = raw.get("schema_version", 1)
    if schema_version != 1:
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID", "schema_version must be 1", path=path)
    htype = _string(raw["hypothesis_type"], "hypothesis_type",
                    "HYPOTHESIS_SCHEMA_INVALID", path) or ""
    members = _string_list(raw["members"], "members",
                           "HYPOTHESIS_SCHEMA_INVALID", path)
    if not members:
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID", "members must not be empty", path=path)
    checked_members = tuple(
        _contained_path(root, member, "members", EXPRESSIONS_DIRECTORY)[0]
        for member in members
    )
    assumptions_used = _string_list(
        raw["assumptions_used"], "assumptions_used",
        "HYPOTHESIS_SCHEMA_INVALID", path)
    undeclared = sorted(set(assumptions_used) - symbol_names)
    if undeclared:
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID",
            f"assumptions_used names are undeclared: {', '.join(undeclared)}",
            path=path,
        )
    omitted = sorted(symbol_names - set(assumptions_used))
    if omitted:
        raise WorkspaceError(
            "DECLARED_ASSUMPTIONS_OMITTED",
            "assumptions_used must list every declared symbol; omitted: "
            + ", ".join(omitted),
            path=path,
        )
    operators = _string_list(raw.get("operators"), "operators",
                             "HYPOTHESIS_SCHEMA_INVALID", path)
    instance_maps = raw.get("instance_maps", {})
    if not isinstance(instance_maps, dict) or not all(
            isinstance(key, str) and key for key in instance_maps):
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID", "instance_maps must be an object",
            path=path)
    latent = _string(raw.get("latent_object"), "latent_object",
                     "HYPOTHESIS_SCHEMA_INVALID", path, optional=True)
    reconstruction = _string(
        raw.get("reconstruction_rule"), "reconstruction_rule",
        "HYPOTHESIS_SCHEMA_INVALID", path, optional=True)

    simple = "proof_obligations" not in raw
    obligation_values = raw.get("proof_obligations")
    if obligation_values is None and htype == "equivalence" and len(checked_members) == 2:
        obligation_values = [{
            "obligation_id": "equivalence-1",
            "relation": "equivalent",
            "left": checked_members[0],
            "right": checked_members[1],
        }]
    elif obligation_values is None:
        obligation_values = []
    if not isinstance(obligation_values, list):
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID", "proof_obligations must be a list",
            path=path)
    obligations = []
    for index, value in enumerate(obligation_values):
        if not isinstance(value, dict):
            raise WorkspaceError(
                "HYPOTHESIS_SCHEMA_INVALID",
                f"proof_obligations[{index}] must be an object", path=path)
        _keys(value, allowed=_OBLIGATION_KEYS, required=_OBLIGATION_REQUIRED,
              code="HYPOTHESIS_SCHEMA_INVALID", path=path)
        fields = {
            key: _string(value[key], f"proof_obligations[{index}].{key}",
                         "HYPOTHESIS_SCHEMA_INVALID", path) or ""
            for key in _OBLIGATION_KEYS
        }
        if fields["left"] not in checked_members or fields["right"] not in checked_members:
            raise WorkspaceError(
                "HYPOTHESIS_SCHEMA_INVALID",
                f"proof_obligations[{index}] must reference declared members",
                path=path,
            )
        obligations.append(HypothesisObligation(**fields))
    ids = [item.obligation_id for item in obligations]
    if len(ids) != len(set(ids)):
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID", "obligation_id values must be unique",
            path=path)

    hypothesis = WorkspaceHypothesis(
        schema_version=1,
        hypothesis_type=htype,
        members=checked_members,
        latent_object=latent,
        operators=operators,
        instance_maps=dict(instance_maps),
        reconstruction_rule=reconstruction,
        assumptions_used=assumptions_used,
        proof_obligations=tuple(obligations),
        normalized_simple_form=simple,
    )
    return hypothesis, _source_from_bytes(
        path, root, "hypothesis", source_bytes, text=True)


def load_workspace(path: str | Path) -> ResearchWorkspace:
    """Validate and load a researcher workspace without writing any file.

    Expressions are read and parsed through the engine's existing strict
    parser.  A malformed expression is surfaced as ``EXPRESSION_PARSE_FAILURE``
    with the underlying parser code in ``WorkspaceError.detail``.
    """
    root_input = Path(path)
    try:
        root = root_input.resolve(strict=True)
    except OSError:
        raise WorkspaceError(
            "WORKSPACE_NOT_FOUND", "workspace directory does not exist",
            path=root_input) from None
    if not root.is_dir():
        raise WorkspaceError(
            "WORKSPACE_NOT_DIRECTORY", "workspace path is not a directory",
            path=root)

    project, project_source = _load_project(root)
    entrypoint, _ = _contained_path(
        root, project.expression_entrypoint, "expression_entrypoint",
        EXPRESSIONS_DIRECTORY)
    symbols, functions, assumptions_source = _load_assumptions(
        root, project.assumptions_file)
    hypothesis, hypothesis_source = _load_hypothesis(
        root, {item["name"] for item in symbols})
    if entrypoint not in hypothesis.members:
        raise WorkspaceError(
            "HYPOTHESIS_SCHEMA_INVALID",
            "members must include project.expression_entrypoint",
            path=root / HYPOTHESES_DIRECTORY / "hypothesis.json",
        )

    expressions = []
    for member in hypothesis.members:
        _, member_path = _contained_path(
            root, member, "members", EXPRESSIONS_DIRECTORY)
        try:
            expressions.append(load_expression(
                member_path, list(symbols), functions=list(functions)))
        except AdapterError as exc:
            raise WorkspaceError(
                "EXPRESSION_PARSE_FAILURE", exc.code, path=member_path) from None

    notes = tuple(
        _source(_contained_path(root, note, "optional_notes", NOTES_DIRECTORY)[1],
                root, "note", text=True)
        for note in project.optional_notes
    )
    references = tuple(
        _source(_contained_path(root, reference, "optional_references",
                                REFERENCES_DIRECTORY)[1],
                root, "reference", text=False)
        for reference in project.optional_references
    )
    return ResearchWorkspace(
        root=root,
        project=project,
        symbols=symbols,
        functions=functions,
        hypothesis=hypothesis,
        expressions=tuple(expressions),
        notes=notes,
        references=references,
        project_source=project_source,
        assumptions_source=assumptions_source,
        hypothesis_source=hypothesis_source,
    )


def _write_new(path: Path, content: str) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def initialize_workspace(path: str | Path) -> ResearchWorkspace:
    """Create the minimal v0.1 workspace and return its validated snapshot.

    The target must not already exist.  This is an intentional no-overwrite
    policy: initialization can never replace a researcher's files.
    """
    requested = Path(path)
    if requested.exists() or requested.is_symlink():
        raise WorkspaceError(
            "WORKSPACE_ALREADY_EXISTS",
            "choose a new path; initialization never overwrites existing data",
            path=requested,
        )
    try:
        requested.parent.mkdir(parents=True, exist_ok=True)
        requested.mkdir(exist_ok=False)
        for name in (
                EXPRESSIONS_DIRECTORY, NOTES_DIRECTORY, ASSUMPTIONS_DIRECTORY,
                REFERENCES_DIRECTORY, HYPOTHESES_DIRECTORY, RUNS_DIRECTORY):
            (requested / name).mkdir()
        project_name = requested.name or "symbolic-research-project"
        _write_new(requested / PROJECT_FILE, (
            f"project_name: {json.dumps(project_name)}\n"
            "objective: \"Test an exact symbolic hypothesis without modifying source files.\"\n"
            "expression_entrypoint: expressions/current.txt\n"
            "assumptions_file: assumptions/assumptions.yaml\n"
            "optional_notes:\n"
            "  - notes/research_notes.md\n"
            "optional_references:\n"
            "  - references/README.md\n"
        ))
        _write_new(requested / EXPRESSIONS_DIRECTORY / "current.txt",
                   "x**2 + 2*x + 1\n")
        _write_new(requested / EXPRESSIONS_DIRECTORY / "candidate.txt",
                   "(x + 1)**2\n")
        _write_new(requested / NOTES_DIRECTORY / "research_notes.md", (
            "# Research notes\n\n"
            "Replace the example expressions and hypothesis with your own inputs.\n"
            "The tool reads these source files but writes results only under `runs/`.\n"
        ))
        _write_new(requested / ASSUMPTIONS_DIRECTORY / "assumptions.yaml", (
            "symbols:\n"
            "  - name: x\n"
            "    real: true\n"
            "    nonzero: false\n"
            "functions: []\n"
        ))
        _write_new(requested / REFERENCES_DIRECTORY / "README.md", (
            "# References\n\n"
            "List source paths, citations, or manually curated excerpts here.\n"
            "Reference ingestion is currently lightweight.\n"
        ))
        hypothesis = {
            "schema_version": 1,
            "hypothesis_type": "equivalence",
            "members": [
                "expressions/current.txt", "expressions/candidate.txt"],
            "latent_object": None,
            "operators": [],
            "instance_maps": {},
            "reconstruction_rule": "current is exactly equivalent to candidate",
            "assumptions_used": ["x"],
            "proof_obligations": [{
                "obligation_id": "equivalence-1",
                "relation": "equivalent",
                "left": "expressions/current.txt",
                "right": "expressions/candidate.txt",
            }],
        }
        _write_new(
            requested / HYPOTHESES_DIRECTORY / "hypothesis.json",
            json.dumps(hypothesis, indent=2, sort_keys=True) + "\n",
        )
    except WorkspaceError:
        raise
    except OSError as exc:
        raise WorkspaceError(
            "WORKSPACE_INITIALIZATION_FAILED", str(exc), path=requested) from None
    return load_workspace(requested)


__all__ = [
    "HypothesisObligation",
    "ResearchWorkspace",
    "WorkspaceError",
    "WorkspaceHypothesis",
    "WorkspaceProject",
    "WorkspaceSource",
    "initialize_workspace",
    "load_workspace",
]
