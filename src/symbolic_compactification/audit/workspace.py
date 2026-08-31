"""Audit workspace init and read-only load. Never mutates researcher sources."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from .io import (
    MAX_METADATA_BYTES,
    MAX_SOURCE_BYTES,
    assert_contained,
    contained_relpath,
    read_bytes,
    require_keys,
    require_string,
    safe_yaml_mapping,
    sha256_bytes,
    write_new,
)
from .schema import (
    AUDIT_SCHEMA_VERSION,
    AUDIT_YAML_KEYS,
    AUDIT_YAML_REQUIRED,
    DEFAULT_VERIFIER_ROUTE,
    AuditError,
)

PathLike = Union[str, os.PathLike]

CONFIG_FILE = "audit.yaml"
MANUSCRIPT_DIRECTORY = "manuscript"
EQUATIONS_DIRECTORY = "equations"
EDGES_DIRECTORY = "edges"
EXPRESSIONS_DIRECTORY = "expressions"
ASSUMPTIONS_DIRECTORY = "assumptions"
RUNS_DIRECTORY = "runs"
REPORTS_DIRECTORY = "reports"
EQUATION_MANIFEST = "equations/equations.yaml"
EDGE_MANIFEST = "edges/edges.yaml"
ASSUMPTIONS_FILE = "assumptions/assumptions.yaml"
MANUSCRIPT_SOURCE = "manuscript/source.tex"


@dataclass(frozen=True)
class AuditConfig:
    audit_name: str
    manuscript_source: str
    equation_manifest: str
    edge_manifest: str
    assumptions: str
    output_dir: str
    verifier_profile: str
    schema_version: str = AUDIT_SCHEMA_VERSION

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "audit_name": self.audit_name,
            "manuscript_source": self.manuscript_source,
            "equation_manifest": self.equation_manifest,
            "edge_manifest": self.edge_manifest,
            "assumptions": self.assumptions,
            "output_dir": self.output_dir,
            "verifier_profile": self.verifier_profile,
        }


@dataclass(frozen=True)
class AuditWorkspace:
    """Validated read-only snapshot of an audit workspace."""

    root: Path
    config: AuditConfig
    config_sha256: str
    manuscript_sha256: Optional[str]
    equation_manifest_sha256: str
    edge_manifest_sha256: str
    assumptions_sha256: str


def _audit_yaml_text(name: str) -> str:
    return (
        f"schema_version: {AUDIT_SCHEMA_VERSION}\n"
        f"audit_name: {name!r}\n"
        f"manuscript_source: {MANUSCRIPT_SOURCE}\n"
        f"equation_manifest: {EQUATION_MANIFEST}\n"
        f"edge_manifest: {EDGE_MANIFEST}\n"
        f"assumptions: {ASSUMPTIONS_FILE}\n"
        f"output_dir: {REPORTS_DIRECTORY}\n"
        f"verifier_profile: {DEFAULT_VERIFIER_ROUTE}\n"
    )


def initialize_audit_workspace(path: PathLike) -> AuditWorkspace:
    """Create a new audit workspace. The target path must not already exist."""
    requested = Path(path)
    if requested.exists() or requested.is_symlink():
        raise AuditError(
            "WORKSPACE_ALREADY_EXISTS",
            "choose a new path; initialization never overwrites existing data",
            path=str(requested),
        )
    try:
        requested.parent.mkdir(parents=True, exist_ok=True)
        requested.mkdir(exist_ok=False)
        for name in (
                MANUSCRIPT_DIRECTORY, EQUATIONS_DIRECTORY, EDGES_DIRECTORY,
                EXPRESSIONS_DIRECTORY, ASSUMPTIONS_DIRECTORY, RUNS_DIRECTORY,
                REPORTS_DIRECTORY):
            (requested / name).mkdir()
        audit_name = requested.name or "untitled-audit"
        write_new(requested / CONFIG_FILE, _audit_yaml_text(audit_name))
        write_new(requested / MANUSCRIPT_SOURCE, (
            "% Derivation-audit manuscript source (LaTeX or Markdown).\n"
            "% Replace this placeholder. Inventory extracts labels only;\n"
            "% it does not interpret mathematics.\n"
            "\\documentclass{article}\n"
            "\\begin{document}\n"
            "\\begin{equation}\n"
            "\\label{eq:placeholder}\n"
            "1 = 1\n"
            "\\end{equation}\n"
            "\\end{document}\n"
        ))
        write_new(requested / EQUATION_MANIFEST, (
            f"schema_version: {AUDIT_SCHEMA_VERSION}\n"
            "equations: []\n"
        ))
        write_new(requested / EDGE_MANIFEST, (
            f"schema_version: {AUDIT_SCHEMA_VERSION}\n"
            "# Edge ids may use letters, digits, '.', '_', '-', and ':' "
            "(for example eq:12).\n"
            "# Required fields: id (or edge_id) and type (or edge_type).\n"
            "# Example:\n"
            "# edges:\n"
            "#   - id: eq:placeholder\n"
            "#     from: eq:placeholder\n"
            "#     to: eq:placeholder\n"
            "#     type: ALGEBRAIC_EQUIVALENCE\n"
            "#     lhs: expressions/left.txt\n"
            "#     rhs: expressions/right.txt\n"
            "edges: []\n"
        ))
        write_new(requested / ASSUMPTIONS_FILE, (
            "symbols:\n"
            "  - name: x\n"
            "    real: true\n"
            "    nonzero: false\n"
            "functions: []\n"
        ))
        write_new(requested / EXPRESSIONS_DIRECTORY / "README.md", (
            "# Symbolic expressions\n\n"
            "Place explicit native-text residuals and members here.\n"
            "Equation inventory does not auto-translate LaTeX into algebra.\n"
        ))
        write_new(requested / REPORTS_DIRECTORY / ".gitkeep", "")
        write_new(requested / RUNS_DIRECTORY / ".gitkeep", "")
    except AuditError:
        raise
    except OSError as exc:
        raise AuditError(
            "WORKSPACE_INITIALIZATION_FAILED", str(exc), path=str(requested),
        ) from None
    return load_audit_workspace(requested)


def load_audit_workspace(path: PathLike) -> AuditWorkspace:
    requested = Path(path)
    try:
        root = requested.resolve(strict=True)
    except OSError:
        raise AuditError(
            "WORKSPACE_NOT_FOUND",
            "audit workspace directory does not exist",
            path=str(requested),
        ) from None
    if not root.is_dir() or root.is_symlink():
        raise AuditError(
            "WORKSPACE_NOT_DIRECTORY",
            "audit workspace path is not a real directory",
            path=str(root),
        )
    config_path = root / CONFIG_FILE
    assert_contained(root, config_path, CONFIG_FILE)
    raw = read_bytes(config_path, max_bytes=MAX_METADATA_BYTES)
    mapping = safe_yaml_mapping(raw, config_path, "AUDIT_PARSE_FAILURE")
    require_keys(
        mapping, allowed=AUDIT_YAML_KEYS, required=AUDIT_YAML_REQUIRED,
        code="AUDIT_SCHEMA_INVALID", path=config_path)
    schema_version = require_string(
        mapping["schema_version"], "schema_version",
        "AUDIT_SCHEMA_INVALID", config_path)
    if schema_version != AUDIT_SCHEMA_VERSION:
        raise AuditError(
            "AUDIT_SCHEMA_INVALID",
            f"schema_version must be {AUDIT_SCHEMA_VERSION}",
            path=str(config_path),
        )
    config = AuditConfig(
        audit_name=require_string(
            mapping["audit_name"], "audit_name",
            "AUDIT_SCHEMA_INVALID", config_path),
        manuscript_source=require_string(
            mapping["manuscript_source"], "manuscript_source",
            "AUDIT_SCHEMA_INVALID", config_path),
        equation_manifest=require_string(
            mapping["equation_manifest"], "equation_manifest",
            "AUDIT_SCHEMA_INVALID", config_path),
        edge_manifest=require_string(
            mapping["edge_manifest"], "edge_manifest",
            "AUDIT_SCHEMA_INVALID", config_path),
        assumptions=require_string(
            mapping["assumptions"], "assumptions",
            "AUDIT_SCHEMA_INVALID", config_path),
        output_dir=require_string(
            mapping["output_dir"], "output_dir",
            "AUDIT_SCHEMA_INVALID", config_path),
        verifier_profile=require_string(
            mapping["verifier_profile"], "verifier_profile",
            "AUDIT_SCHEMA_INVALID", config_path),
        schema_version=schema_version,
    )
    if config.verifier_profile != DEFAULT_VERIFIER_ROUTE:
        raise AuditError(
            "UNSUPPORTED_VERIFIER_PROFILE",
            f"alpha supports only {DEFAULT_VERIFIER_ROUTE}",
            path=str(config_path),
        )

    def _hash_declared(rel: str, field: str, required: bool) -> Optional[str]:
        _, abs_path = contained_relpath(root, rel, field)
        if not abs_path.is_file():
            if required:
                raise AuditError(
                    "SOURCE_FILE_MISSING",
                    f"{field} is missing",
                    path=str(abs_path),
                )
            return None
        limit = (MAX_SOURCE_BYTES if field == "manuscript_source"
                 else MAX_METADATA_BYTES)
        return sha256_bytes(read_bytes(abs_path, max_bytes=limit))

    return AuditWorkspace(
        root=root,
        config=config,
        config_sha256=sha256_bytes(raw),
        manuscript_sha256=_hash_declared(
            config.manuscript_source, "manuscript_source", required=False),
        equation_manifest_sha256=_hash_declared(
            config.equation_manifest, "equation_manifest", required=True) or "",
        edge_manifest_sha256=_hash_declared(
            config.edge_manifest, "edge_manifest", required=True) or "",
        assumptions_sha256=_hash_declared(
            config.assumptions, "assumptions", required=True) or "",
    )


def source_immutability_roots(workspace: AuditWorkspace) -> tuple[Path, ...]:
    """Researcher-owned paths that audit commands must never rewrite."""
    root = workspace.root
    return (
        root / CONFIG_FILE,
        root / workspace.config.manuscript_source,
        root / workspace.config.equation_manifest,
        root / workspace.config.edge_manifest,
        root / workspace.config.assumptions,
        root / EXPRESSIONS_DIRECTORY,
        root / MANUSCRIPT_DIRECTORY,
        root / EQUATIONS_DIRECTORY,
        root / EDGES_DIRECTORY,
        root / ASSUMPTIONS_DIRECTORY,
    )
