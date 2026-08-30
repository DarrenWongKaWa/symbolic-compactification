"""Read-only loader for RPSCasePackageV1 evaluator programs."""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_program_hash
from .model import CompileContext, Obligation, RepresentationProgram, SourceMember
from .schema import SchemaError, program_from_dict


class PackageLoadError(ValueError):
    """Stable package-ingestion failure."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class LoadedCasePackage:
    package_id: str
    program: RepresentationProgram
    context: CompileContext
    schema_deltas: tuple[str, ...]


def _load_object(path: Path, code: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise PackageLoadError(code) from None
    if not isinstance(value, Mapping):
        raise PackageLoadError(code)
    return value


def _safe_path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative:
        raise PackageLoadError("PACKAGE_ARTIFACT_PATH_INVALID")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        raise PackageLoadError("PACKAGE_ARTIFACT_PATH_ESCAPE") from None
    return path


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise PackageLoadError("PACKAGE_ARTIFACT_MISSING") from None


def load_case_package(package_root: str | Path, *, grammar_id: str = "G_FULL") -> LoadedCasePackage:
    """Load exact package artifacts and expose, but never repair, schema gaps."""
    root = Path(package_root).resolve()
    manifest = _load_object(root / "package.json", "PACKAGE_MANIFEST_UNREADABLE")
    if manifest.get("schema_version") != "RPSCasePackageV1":
        raise PackageLoadError("PACKAGE_SCHEMA_UNKNOWN")
    package_id = manifest.get("package_id")
    if not isinstance(package_id, str) or package_id != root.name:
        raise PackageLoadError("PACKAGE_ID_MISMATCH")
    artifacts = manifest.get("artifact_hashes")
    if not isinstance(artifacts, list):
        raise PackageLoadError("PACKAGE_ARTIFACT_MANIFEST_INVALID")
    seen: set[str] = set()
    for entry in artifacts:
        if not isinstance(entry, Mapping):
            raise PackageLoadError("PACKAGE_ARTIFACT_MANIFEST_INVALID")
        relative = entry.get("path")
        expected = entry.get("sha256")
        if not isinstance(relative, str) or relative in seen:
            raise PackageLoadError("PACKAGE_ARTIFACT_MANIFEST_INVALID")
        seen.add(relative)
        if _sha256(_safe_path(root, relative)) != expected:
            raise PackageLoadError("PACKAGE_ARTIFACT_HASH_MISMATCH")
    actual = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    }
    if actual != seen:
        raise PackageLoadError("PACKAGE_ARTIFACT_MANIFEST_INCOMPLETE")

    catalog = _load_object(root / "source_catalog.json", "SOURCE_CATALOG_UNREADABLE")
    raw_members = catalog.get("members")
    if not isinstance(raw_members, list):
        raise PackageLoadError("SOURCE_CATALOG_INVALID")
    source_members: list[SourceMember] = []
    for item in raw_members:
        if not isinstance(item, Mapping):
            raise PackageLoadError("SOURCE_CATALOG_INVALID")
        try:
            member_id = item["member_id"]
            path = item["path"]
            digest = item["sha256"]
        except KeyError:
            raise PackageLoadError("SOURCE_CATALOG_INVALID") from None
        if not all(isinstance(value, str) for value in (member_id, path, digest)):
            raise PackageLoadError("SOURCE_CATALOG_INVALID")
        member = SourceMember(member_id=member_id, path=path, sha256=digest)
        if _sha256(_safe_path(root, member.path)) != member.sha256:
            raise PackageLoadError("SOURCE_MEMBER_HASH_MISMATCH")
        source_members.append(member)

    assumptions = _load_object(root / "assumptions.json", "ASSUMPTIONS_UNREADABLE")
    raw_predicates = assumptions.get("predicates")
    if not isinstance(raw_predicates, list):
        raise PackageLoadError("ASSUMPTIONS_INVALID")
    assumption_statuses: dict[str, str] = {}
    for item in raw_predicates:
        if not isinstance(item, Mapping):
            raise PackageLoadError("ASSUMPTIONS_INVALID")
        identifier = item.get("predicate_id")
        status = item.get("status")
        if not isinstance(identifier, str) or not isinstance(status, str):
            raise PackageLoadError("ASSUMPTIONS_INVALID")
        if identifier in assumption_statuses:
            raise PackageLoadError("ASSUMPTION_ID_DUPLICATE")
        assumption_statuses[identifier] = status

    raw_obligations = _load_object(
        root / "reference/obligations.json", "OBLIGATIONS_UNREADABLE"
    ).get("obligations")
    if not isinstance(raw_obligations, list):
        raise PackageLoadError("OBLIGATIONS_INVALID")
    obligation_links: list[Obligation] = []
    for item in raw_obligations:
        if not isinstance(item, Mapping):
            raise PackageLoadError("OBLIGATIONS_INVALID")
        identifier = item.get("obligation_id")
        member_id = item.get("current_member_id")
        required = item.get("required", True)
        if not isinstance(identifier, str) or not isinstance(member_id, str) or not isinstance(required, bool):
            raise PackageLoadError("OBLIGATIONS_INVALID")
        obligation_links.append(Obligation(
            obligation_id=identifier,
            member_id=member_id,
            output=None,
            required=required,
        ))

    namespace = _load_object(root / "symbols.json", "SYMBOLS_UNREADABLE")
    symbols = namespace.get("symbols")
    functions = namespace.get("functions", [])
    if (
        not isinstance(symbols, list)
        or not isinstance(functions, list)
        or not all(isinstance(item, str) for item in functions)
    ):
        raise PackageLoadError("SYMBOLS_INVALID")

    raw_program = _load_object(
        root / "reference/program.json", "PROGRAM_UNREADABLE"
    )
    legacy_declared_program_id = raw_program.get("program_id")
    program_for_m1 = dict(raw_program)
    # RPSCasePackageV1 predates M1 alpha-normalized hashing.  Preserve the
    # exact legacy id for the delta report, but do not mislabel it as an M1 id.
    program_for_m1.pop("program_id", None)
    try:
        program = program_from_dict(
            program_for_m1,
            injected_source_members=tuple(source_members),
            injected_assumption_statuses=assumption_statuses,
            injected_obligations=tuple(obligation_links),
        )
    except (SchemaError, TypeError) as exc:
        code = getattr(exc, "code", "PROGRAM_SCHEMA_INVALID")
        raise PackageLoadError(code) from None

    deltas: list[str] = []
    if "source_members" not in raw_program:
        deltas.append("SOURCE_MEMBERS_INJECTED_FROM_EXACT_CATALOG")
    if "assumption_statuses" not in raw_program:
        deltas.append("ASSUMPTION_STATUSES_INJECTED_FROM_EXACT_CONTRACT")
    if any(item.output is None for item in program.operators):
        deltas.append("EXECUTABLE_OPERATOR_OUTPUTS_MISSING")
    if any(item.output is None for item in program.member_assignments):
        deltas.append("EXECUTABLE_ASSIGNMENT_OUTPUTS_MISSING")
    if any(item.output is None for item in program.obligations):
        deltas.append("EXECUTABLE_OBLIGATION_OUTPUT_LINKS_MISSING")
    if legacy_declared_program_id != canonical_program_hash(program):
        deltas.append("LEGACY_PROGRAM_ID_IS_NOT_M1_ALPHA_NORMALIZED_HASH")

    return LoadedCasePackage(
        package_id=package_id,
        program=program,
        context=CompileContext(
            package_root=root,
            symbols=tuple(symbols),
            functions=tuple(functions),
            grammar_id=grammar_id,
        ),
        schema_deltas=tuple(deltas),
    )
