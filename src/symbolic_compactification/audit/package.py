"""Reviewer verification package export.

Builds a clean, offline-reproducible directory from an audit workspace and a
recorded run. Table inclusion is not re-derived here: existing ``reports/``
tables are copied, and ``generate_tables`` is invoked only when they are
missing.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional, Union

from ..models import ENGINE_VERSION
from ..security import redact_public_data, redact_text
from .evidence import AuditRun
from .io import (
    MAX_SOURCE_BYTES,
    assert_contained,
    contained_relpath,
    decode_utf8,
    read_bytes,
    sha256_bytes,
)
from .privacy import (
    PRIVATE_VALIDATION_DIRNAME,
    REFUSED_NETWORK_PREFIXES,
    is_private_relpath,
)
from .schema import (
    APPROVED_CAVEAT,
    APPROVED_MACHINE_CLAIM,
    AUDIT_PROTOCOL_VERSION,
    AUDIT_SCHEMA_VERSION,
    FORBIDDEN_PUBLIC_CLAIMS,
    TABLE_FILENAMES,
    AuditError,
)
from .tables import generate_tables
from .workspace import (
    CONFIG_FILE,
    EXPRESSIONS_DIRECTORY,
    AuditWorkspace,
)

PACKAGE_DIRNAME = "reviewer-verification-package"
PACKAGE_SCHEMA = "DerivationAuditReviewerPackageV1"
REPLAY_DIRNAME = "replay"
MACHINE_RESULTS_DIRNAME = "machine_results"
OBLIGATIONS_DIRNAME = "obligations"
ASSUMPTIONS_EXPORT_NAME = "assumptions.yaml"
MANIFEST_NAME = "MANIFEST.json"
README_NAME = "README.md"
REPRODUCE_NAME = "reproduce.sh"
MACHINE_RECORDS_NAME = "machine_records.json"
PROVENANCE_NAME = "provenance.json"
VERIFICATION_TABLE_JSON = "verification_table.json"
VERIFICATION_TABLE_CSV = "verification_table.csv"

_TABLE_MD_NAMES = tuple(TABLE_FILENAMES.values())
_JSON_SUFFIXES = {".json"}
_TEXT_SUFFIXES = {
    ".csv", ".md", ".rst", ".sh", ".tex", ".txt", ".yaml", ".yml",
}
_SKIP_DIR_NAMES = {
    PRIVATE_VALIDATION_DIRNAME,
    ".git",
    ".hg",
    ".svn",
    ".env",
    "__pycache__",
    PACKAGE_DIRNAME,
}


def build_reviewer_package(
    workspace: AuditWorkspace,
    run: AuditRun,
    dest: Union[str, Path, None] = None,
) -> Path:
    """Export a clean reviewer-verification-package/ with reproduce.sh."""
    dest_path = _prepare_dest(workspace, dest)
    engine_version = _engine_version(run)
    table_sources = _ensure_reviewer_tables(workspace, run)

    for name in _TABLE_MD_NAMES:
        _export_src_file(
            _require_regular_file(table_sources[name], name),
            dest_path / name,
            workspace_root=workspace.root,
            required=True,
        )

    assumptions_src = _require_contained_file(
        workspace, workspace.config.assumptions, "assumptions")
    _export_src_file(
        assumptions_src, dest_path / ASSUMPTIONS_EXPORT_NAME,
        workspace_root=workspace.root,
        required=True,
    )

    _write_obligations(workspace, run, dest_path / OBLIGATIONS_DIRNAME)
    _write_machine_results(
        workspace, run, dest_path / MACHINE_RESULTS_DIRNAME,
        engine_version=engine_version,
        table_sources=table_sources,
    )
    _export_replay(workspace, dest_path / REPLAY_DIRNAME, dest_path)
    _write_text(
        dest_path / README_NAME,
        redact_text(_readme_text(run, engine_version)),
    )
    _write_reproduce_script(dest_path / REPRODUCE_NAME)
    _assert_no_forbidden_claims((dest_path / README_NAME).read_text(encoding="utf-8"))
    _write_manifest(dest_path, run, engine_version)
    return dest_path


def _prepare_dest(
    workspace: AuditWorkspace,
    dest: Union[str, Path, None],
) -> Path:
    dest_path = (
        workspace.root / PACKAGE_DIRNAME if dest is None else Path(dest)
    )
    if dest_path.exists() and dest_path.is_symlink():
        raise AuditError(
            "PACKAGE_DEST_INVALID",
            "destination must not be a symlink",
            path=str(dest_path),
        )
    if dest_path.exists() and not dest_path.is_dir():
        raise AuditError(
            "PACKAGE_DEST_INVALID",
            "destination must be a directory",
            path=str(dest_path),
        )
    try:
        dest_path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise AuditError(
            "PACKAGE_DEST_INVALID",
            str(exc),
            path=str(dest_path),
        ) from None
    resolved = dest_path.resolve()
    if resolved == workspace.root.resolve():
        raise AuditError(
            "PACKAGE_DEST_INVALID",
            "destination must not be the audit workspace root",
            path=str(dest_path),
        )
    try:
        rel = resolved.relative_to(workspace.root.resolve()).as_posix()
    except ValueError:
        rel = None
    if rel is not None and is_private_relpath(rel):
        raise AuditError(
            "PACKAGE_DEST_INVALID",
            "destination must not be private-validation storage",
            path=str(dest_path),
        )
    return resolved


def _engine_version(run: AuditRun) -> str:
    versions = {
        record.engine_version for record in run.records if record.engine_version
    }
    if len(versions) == 1:
        return next(iter(versions))
    return ENGINE_VERSION


def _ensure_reviewer_tables(
    workspace: AuditWorkspace,
    run: AuditRun,
) -> dict[str, Path]:
    reports = workspace.root / workspace.config.output_dir
    sources = {name: reports / name for name in _TABLE_MD_NAMES}
    missing = [
        name for name, path in sources.items()
        if path.is_symlink() or not path.is_file()
    ]
    if missing:
        artifacts = generate_tables(workspace, run)
        sources = {
            "TABLE_VERIFIED.md": artifacts.verified_md,
            "TABLE_STRUCTURAL.md": artifacts.structural_md,
            "TABLE_UNCERTIFIED.md": artifacts.uncertified_md,
            "TABLE_NONZERO.md": artifacts.nonzero_md,
            VERIFICATION_TABLE_JSON: artifacts.table_json,
            VERIFICATION_TABLE_CSV: artifacts.table_csv,
        }
    else:
        for name in (VERIFICATION_TABLE_JSON, VERIFICATION_TABLE_CSV):
            candidate = reports / name
            if candidate.is_file() and not candidate.is_symlink():
                sources[name] = candidate
    for name in _TABLE_MD_NAMES:
        path = sources.get(name)
        if path is None or path.is_symlink() or not path.is_file():
            raise AuditError(
                "SOURCE_FILE_MISSING",
                f"reviewer table {name} was not generated",
                path=None if path is None else str(path),
            )
    return sources


def _require_regular_file(path: Path, field: str) -> Path:
    if path.is_symlink() or not path.is_file():
        raise AuditError(
            "SOURCE_FILE_MISSING",
            f"{field} must be a regular non-symlink file",
            path=str(path),
        )
    return path


def _require_contained_file(
    workspace: AuditWorkspace,
    rel: str,
    field: str,
) -> Path:
    path = _safe_contained_file(workspace, rel, field)
    if path is None:
        raise AuditError(
            "SOURCE_FILE_MISSING",
            f"{field} is missing or not exportable",
            path=rel,
        )
    return path


def _safe_contained_file(
    workspace: AuditWorkspace,
    rel: str,
    field: str,
) -> Optional[Path]:
    if not isinstance(rel, str) or not rel.strip():
        return None
    stripped = rel.strip()
    lowered = stripped.lower()
    if any(lowered.startswith(prefix) for prefix in REFUSED_NETWORK_PREFIXES):
        return None
    if is_private_relpath(stripped.replace("\\", "/")):
        return None
    try:
        _, abs_path = contained_relpath(workspace.root, stripped, field)
    except AuditError:
        return None
    if abs_path.is_symlink() or not abs_path.is_file():
        return None
    return abs_path


def _should_skip_path(
    root: Path,
    path: Path,
    dest: Optional[Path] = None,
) -> bool:
    if path.is_symlink():
        return True
    if path.name in _SKIP_DIR_NAMES:
        return True
    try:
        rel = path.relative_to(root).as_posix()
    except ValueError:
        return True
    if is_private_relpath(rel):
        return True
    if dest is not None:
        try:
            resolved = path.resolve()
            dest_res = dest.resolve()
            if resolved == dest_res:
                return True
            resolved.relative_to(dest_res)
            return True
        except (OSError, ValueError):
            pass
    return False


def _export_src_file(
    src: Path,
    dest: Path,
    *,
    workspace_root: Optional[Path] = None,
    required: bool = False,
) -> None:
    if src.is_symlink() or not src.is_file():
        if required:
            raise AuditError(
                "SOURCE_FILE_MISSING",
                "expected a regular non-symlink file",
                path=str(src),
            )
        return
    if workspace_root is not None:
        try:
            assert_contained(workspace_root, src, src.name)
        except AuditError:
            if required:
                raise
            return
        if _should_skip_path(workspace_root, src):
            if required:
                raise AuditError(
                    "PATH_OUTSIDE_WORKSPACE",
                    "required export source is not a contained regular file",
                    path=str(src),
                )
            return
    raw = read_bytes(src, max_bytes=MAX_SOURCE_BYTES)
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = src.suffix.lower()
    if suffix in _JSON_SUFFIXES:
        _write_text(dest, _redact_copied_json(raw, src))
        return
    if suffix in _TEXT_SUFFIXES or src.name in {CONFIG_FILE, ASSUMPTIONS_EXPORT_NAME}:
        text = decode_utf8(raw, src, "SOURCE_FILE_UNREADABLE")
        _write_text(dest, redact_text(text))
        return
    dest.write_bytes(raw)


def _redact_copied_json(raw: bytes, path: Path) -> str:
    try:
        value = json.loads(decode_utf8(raw, path, "SOURCE_FILE_UNREADABLE"))
    except (AuditError, json.JSONDecodeError):
        return redact_text(raw.decode("utf-8", errors="replace"))
    return _json_text(redact_public_data(value))


def _json_text(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_obligations(
    workspace: AuditWorkspace,
    run: AuditRun,
    dest: Path,
) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    used: dict[str, int] = {}
    for record in run.records:
        stem = _obligation_stem(record.edge_id, used)
        _write_text(
            dest / f"{stem}.json",
            _json_text(redact_public_data(record.to_dict())),
        )
        residual = record.residual_text
        if isinstance(residual, str) and residual:
            _write_text(dest / f"{stem}.residual.txt", redact_text(residual))
        artifact = record.artifact_relpath
        if isinstance(artifact, str) and artifact:
            src = _safe_contained_file(workspace, artifact, "artifact_relpath")
            if src is not None:
                suffix = src.suffix
                _export_src_file(
                    src,
                    dest / f"{stem}.artifact{suffix}",
                    workspace_root=workspace.root,
                )


def _obligation_stem(edge_id: str, used: dict[str, int]) -> str:
    safe = edge_id if edge_id else "edge"
    count = used.get(safe, 0)
    used[safe] = count + 1
    if count == 0:
        return safe
    return f"{safe}-{count}"


def _write_machine_results(
    workspace: AuditWorkspace,
    run: AuditRun,
    dest: Path,
    *,
    engine_version: str,
    table_sources: dict[str, Path],
) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    copied_records = _copy_run_sidecar(
        workspace, run, dest, MACHINE_RECORDS_NAME)
    if not copied_records:
        _write_text(dest / MACHINE_RECORDS_NAME, _json_text({
            "audit_id": run.audit_id,
            "engine_version": engine_version,
            "records": [
                redact_public_data(record.to_dict()) for record in run.records
            ],
            "run_id": run.run_id,
            "schema_version": run.schema_version,
        }))
    copied_provenance = _copy_run_sidecar(
        workspace, run, dest, PROVENANCE_NAME)
    if not copied_provenance:
        _write_text(dest / PROVENANCE_NAME, _json_text({
            "audit_id": run.audit_id,
            "engine_version": engine_version,
            "protocol_version": AUDIT_PROTOCOL_VERSION,
            "record_count": len(run.records),
            "run_id": run.run_id,
            "schema_version": run.schema_version,
        }))
    for name in (VERIFICATION_TABLE_JSON, VERIFICATION_TABLE_CSV):
        src = table_sources.get(name)
        if src is None or src.is_symlink() or not src.is_file():
            continue
        _export_src_file(src, dest / name, workspace_root=workspace.root)


def _copy_run_sidecar(
    workspace: AuditWorkspace,
    run: AuditRun,
    dest: Path,
    name: str,
) -> bool:
    directory = Path(run.directory)
    if directory.is_symlink() or not directory.is_dir():
        return False
    try:
        assert_contained(workspace.root, directory, "run.directory")
    except AuditError:
        return False
    src = directory / name
    if src.is_symlink() or not src.is_file():
        return False
    try:
        assert_contained(workspace.root, src, name)
    except AuditError:
        return False
    if _should_skip_path(workspace.root, src):
        return False
    _export_src_file(src, dest / name, workspace_root=workspace.root)
    return True


def _export_replay(
    workspace: AuditWorkspace,
    replay: Path,
    dest: Path,
) -> None:
    replay.mkdir(parents=True, exist_ok=True)
    declared = (
        CONFIG_FILE,
        workspace.config.equation_manifest,
        workspace.config.edge_manifest,
        workspace.config.assumptions,
        workspace.config.manuscript_source,
    )
    for rel in declared:
        src = _safe_contained_file(workspace, rel, rel)
        if src is None:
            continue
        _export_src_file(src, replay / Path(rel), workspace_root=workspace.root)
    for rel_dir in (
            EXPRESSIONS_DIRECTORY,
            "equations",
            "edges",
            "assumptions",
            "manuscript"):
        _export_tree(workspace, rel_dir, replay / rel_dir, dest)


def _export_tree(
    workspace: AuditWorkspace,
    rel_dir: str,
    dest_dir: Path,
    package_dest: Path,
) -> None:
    try:
        _, src_dir = contained_relpath(workspace.root, rel_dir, rel_dir)
    except AuditError:
        return
    if src_dir.is_symlink() or not src_dir.is_dir():
        return
    root = workspace.root
    for dirpath, dirnames, filenames in os.walk(src_dir, followlinks=False):
        current = Path(dirpath)
        keep: list[str] = []
        for name in dirnames:
            child = current / name
            if _should_skip_path(root, child, package_dest):
                continue
            keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            src = current / name
            if _should_skip_path(root, src, package_dest):
                continue
            if src.is_symlink() or not src.is_file():
                continue
            rel = src.relative_to(src_dir)
            _export_src_file(src, dest_dir / rel, workspace_root=root)


def _readme_text(run: AuditRun, engine_version: str) -> str:
    table_list = "\n".join(f"- `{name}`" for name in _TABLE_MD_NAMES)
    return (
        "# Derivation-audit reviewer verification package\n"
        "\n"
        "This directory is a machine-generated export of one recorded "
        "derivation-audit run. It is evidence of exact residual checks under "
        "declared symbolic semantics. Markdown text cannot create ZERO or "
        "VERIFIED status; table inclusion is generated from integrity-bound "
        "engine records.\n"
        "\n"
        f"{APPROVED_MACHINE_CLAIM}\n"
        "\n"
        f"{APPROVED_CAVEAT}\n"
        "\n"
        f"- Run id: `{run.run_id}`\n"
        f"- Audit id: `{run.audit_id}`\n"
        f"- Engine version: `{engine_version}`\n"
        f"- Schema: `{AUDIT_SCHEMA_VERSION}`\n"
        "\n"
        "## Reproduce (offline)\n"
        "\n"
        "`reproduce.sh` re-runs verification and then table generation on the "
        "bundled replay workspace in `replay/`. It does not use the network "
        "and does not install packages.\n"
        "\n"
        "```sh\n"
        "./reproduce.sh\n"
        "```\n"
        "\n"
        "Equivalent commands:\n"
        "\n"
        "```sh\n"
        "symbolic-compactification audit verify ./replay\n"
        "symbolic-compactification audit table ./replay\n"
        "```\n"
        "\n"
        "`ssc` is an alias of the same entry point. If neither console script "
        "is on `PATH`, the script falls back to "
        "`python3 -m symbolic_compactification.cli`.\n"
        "\n"
        "## Package contents\n"
        "\n"
        f"{table_list}\n"
        "- `assumptions.yaml` — declared symbols and functions\n"
        "- `obligations/` — residual texts and obligation JSON from records\n"
        "- `machine_results/` — `machine_records.json` and provenance\n"
        "- `replay/` — expressions and manifests sufficient to replay\n"
        "- `MANIFEST.json` — SHA-256 digests of packaged files\n"
        "- `reproduce.sh` — offline verify-then-table replay\n"
        "\n"
        "A NONZERO residual is a disproof of the encoded identity under the "
        "declared semantics. UNKNOWN fails closed and is not promoted.\n"
    )


def _assert_no_forbidden_claims(text: str) -> None:
    lowered = text.lower()
    for phrase in FORBIDDEN_PUBLIC_CLAIMS:
        if phrase.lower() in lowered:
            raise AuditError(
                "FORBIDDEN_PUBLIC_CLAIM",
                "reviewer package README must not contain forbidden claims",
            )


def _write_reproduce_script(path: Path) -> None:
    script = (
        "#!/bin/sh\n"
        "# Offline replay of bundled derivation-audit expressions and manifests.\n"
        "# Does not use the network.\n"
        "set -eu\n"
        "ROOT=$(CDPATH= cd -- \"$(dirname -- \"$0\")\" && pwd)\n"
        "REPLAY=\"$ROOT/replay\"\n"
        "\n"
        "die() {\n"
        "  printf '%s\\n' \"$1\" >&2\n"
        "  exit 1\n"
        "}\n"
        "\n"
        "ssc_audit() {\n"
        "  if command -v symbolic-compactification >/dev/null 2>&1; then\n"
        "    symbolic-compactification audit \"$@\"\n"
        "  elif command -v ssc >/dev/null 2>&1; then\n"
        "    ssc audit \"$@\"\n"
        "  elif command -v python3 >/dev/null 2>&1; then\n"
        "    python3 -m symbolic_compactification.cli audit \"$@\"\n"
        "  elif command -v python >/dev/null 2>&1; then\n"
        "    python -m symbolic_compactification.cli audit \"$@\"\n"
        "  else\n"
        "    die \"symbolic-compactification is not installed "
        "(offline replay requires a local install)\"\n"
        "  fi\n"
        "}\n"
        "\n"
        "ssc_audit verify \"$REPLAY\"\n"
        "ssc_audit table \"$REPLAY\"\n"
    )
    _write_text(path, script)
    mode = path.stat().st_mode
    path.chmod(mode | 0o111)


def _write_manifest(dest: Path, run: AuditRun, engine_version: str) -> None:
    files = _hash_package_files(dest)
    payload = {
        "audit_id": run.audit_id,
        "engine_version": engine_version,
        "files": files,
        "protocol_version": AUDIT_PROTOCOL_VERSION,
        "run_id": run.run_id,
        "schema": AUDIT_SCHEMA_VERSION,
        "schema_version": AUDIT_SCHEMA_VERSION,
        "package_schema": PACKAGE_SCHEMA,
    }
    _write_text(dest / MANIFEST_NAME, _json_text(payload))


def _hash_package_files(dest: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(dest, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(
            name for name in dirnames
            if not (current / name).is_symlink()
            and name not in _SKIP_DIR_NAMES
        )
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or not path.is_file():
                continue
            rel = path.relative_to(dest).as_posix()
            if rel == MANIFEST_NAME or is_private_relpath(rel):
                continue
            files[rel] = sha256_bytes(path.read_bytes())
    return files
