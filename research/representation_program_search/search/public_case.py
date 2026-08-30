"""Evaluator-blind loader for the RPS public proposer boundary.

This module intentionally does not use the M1 case-package loader because
that loader is evaluator-side and reads ``reference/obligations.json`` and
``reference/program.json``.  Search receives exactly a proposer view and the
artifacts named by that view.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from research.representation_program_search.program_ir import CompileContext, SourceMember
from research.representation_program_search.program_ir.model import freeze_json, thaw_json

from .model import SearchContractError

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_IDENTIFIER = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
_FUNCTION = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_RESERVED = {
    "Abs", "And", "E", "Eq", "False", "Ge", "Gt", "I", "Le", "Lt",
    "Ne", "Not", "Or", "Piecewise", "Product", "Rational", "Sum", "True",
    "acos", "asin", "atan", "atan2", "conjugate", "cos", "cosh", "exp",
    "im", "log", "oo", "pi", "polygamma", "re", "sin", "sinh", "sqrt",
    "tan", "tanh",
}
_FORBIDDEN_KEYS = {
    "audited_depth",
    "depth",
    "gold",
    "gold_operator_sequence",
    "gold_program",
    "hidden_member_roles",
    "operator_sequence",
    "program",
    "proof_status",
    "reference",
    "representation_depth",
    "status",
    "target",
    "target_representation",
    "target_type",
    "verdict",
    "verified_obligations",
}
_FORBIDDEN_PATH_PARTS = {"reference", "verification", "final", "runs", "steps"}


@dataclass(frozen=True)
class PublicMember:
    member_id: str
    path: str
    sha256: str
    expression: str

    def source_record(self) -> SourceMember:
        return SourceMember(self.member_id, self.path, self.sha256)


@dataclass(frozen=True)
class PublicCase:
    case_id: str
    package_root: Path
    proposer_view_path: Path
    members: tuple[PublicMember, ...]
    assumptions: Any
    assumption_statuses: Mapping[str, str]
    symbols: tuple[Any, ...]
    functions: tuple[str, ...]
    namespace_provenance: str
    accessed_paths: tuple[str, ...]
    proposer_view_sha256: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "assumptions", freeze_json(self.assumptions))
        object.__setattr__(self, "assumption_statuses", freeze_json(self.assumption_statuses))

    @property
    def source_members(self) -> tuple[SourceMember, ...]:
        return tuple(item.source_record() for item in self.members)

    def compile_context(self, grammar_id: str) -> CompileContext:
        return CompileContext(
            package_root=self.package_root,
            symbols=self.symbols,
            functions=self.functions,
            grammar_id=grammar_id,
        )

    def public_manifest(self) -> dict[str, Any]:
        return {
            "accessed_paths": list(self.accessed_paths),
            "case_id": self.case_id,
            "functions": list(self.functions),
            "members": [
                {
                    "member_id": item.member_id,
                    "path": item.path,
                    "sha256": item.sha256,
                }
                for item in self.members
            ],
            "namespace_provenance": self.namespace_provenance,
            "proposer_view_sha256": self.proposer_view_sha256,
            "symbols": [thaw_json(item) for item in self.symbols],
        }


def _object(path: Path, code: str) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise SearchContractError(code) from None
    if not isinstance(value, Mapping):
        raise SearchContractError(code)
    return value


def _digest(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        raise SearchContractError("PUBLIC_ARTIFACT_MISSING") from None


def _audit_public_shape(value: Any, ancestry: tuple[str, ...] = ()) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            declared_assumption_status = (
                normalized == "status"
                and "assumptions" in ancestry
                and child in {
                    "DECLARED",
                    "DERIVED",
                    "ASSUMPTION_COMPLETE",
                    "COMPLETE",
                    "COMPLETE_AS_WRITTEN",
                }
            )
            if (
                (normalized in _FORBIDDEN_KEYS and not declared_assumption_status)
                or normalized.startswith("gold_")
            ):
                raise SearchContractError(f"PUBLIC_FIELD_FORBIDDEN:{key}")
            _audit_public_shape(child, ancestry + (normalized,))
    elif isinstance(value, list):
        for child in value:
            _audit_public_shape(child, ancestry)


def _safe_referenced_path(root: Path, relative: Any) -> Path:
    if not isinstance(relative, str) or not relative:
        raise SearchContractError("PUBLIC_PATH_INVALID")
    candidate_path = Path(relative)
    if candidate_path.is_absolute() or any(
        part.lower() in _FORBIDDEN_PATH_PARTS for part in candidate_path.parts
    ):
        raise SearchContractError(f"PUBLIC_PATH_FORBIDDEN:{relative}")
    candidate = (root / candidate_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        raise SearchContractError(f"PUBLIC_PATH_ESCAPE:{relative}") from None
    return candidate


def _checked_reference(
    root: Path,
    relative: Any,
    expected: Any,
    accessed: set[str],
) -> Path:
    if not isinstance(expected, str) or not _HASH.fullmatch(expected):
        raise SearchContractError("PUBLIC_HASH_INVALID")
    path = _safe_referenced_path(root, relative)
    if _digest(path) != expected:
        raise SearchContractError(f"PUBLIC_HASH_MISMATCH:{relative}")
    accessed.add(Path(relative).as_posix())
    return path


def _catalog_from_view(
    root: Path,
    raw: Any,
    accessed: set[str],
) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise SearchContractError("PUBLIC_SOURCE_CATALOG_INVALID")
    if "path" in raw or "sha256" in raw:
        path = _checked_reference(root, raw.get("path"), raw.get("sha256"), accessed)
        catalog = _object(path, "PUBLIC_SOURCE_CATALOG_UNREADABLE")
        # If the view repeats member facts they must agree exactly; there is
        # no merge or repair across the public boundary.
        if "members" in raw and raw["members"] != catalog.get("members"):
            raise SearchContractError("PUBLIC_SOURCE_CATALOG_DISAGREES")
        return catalog
    return raw


def _assumptions_from_view(
    root: Path,
    raw: Any,
    accessed: set[str],
) -> Any:
    if isinstance(raw, Mapping) and set(raw) == {"path", "sha256"}:
        path = _checked_reference(root, raw["path"], raw["sha256"], accessed)
        return _object(path, "PUBLIC_ASSUMPTIONS_UNREADABLE")
    if not isinstance(raw, (Mapping, list)):
        raise SearchContractError("PUBLIC_ASSUMPTIONS_INVALID")
    return raw


def _assumption_statuses(assumptions: Any) -> Mapping[str, str]:
    statuses: dict[str, str] = {}

    def visit(value: Any, path: tuple[str, ...]) -> None:
        if isinstance(value, Mapping):
            status = value.get("status", value.get("label"))
            if status in {"DECLARED", "DERIVED"}:
                explicit = value.get("predicate_id")
                identifier = (
                    explicit
                    if isinstance(explicit, str) and explicit
                    else "PUBLIC_" + "_".join(path).upper()
                )
                statuses[identifier] = status
            for key, child in sorted(value.items(), key=lambda item: str(item[0])):
                visit(child, path + (str(key),))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, path + (f"{index:03d}",))

    visit(assumptions, ("ASSUMPTION",))
    return MappingProxyType(dict(sorted(statuses.items())))


def _normalize_public_symbols(raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, list):
        raise SearchContractError("PUBLIC_SYMBOLS_INVALID")
    result: list[Any] = []
    for item in raw:
        if isinstance(item, str) and item:
            result.append(item)
        elif isinstance(item, Mapping) and isinstance(item.get("name"), str):
            allowed = {key: item[key] for key in ("name", "real", "nonzero") if key in item}
            if any(not isinstance(value, bool) for key, value in allowed.items() if key != "name"):
                raise SearchContractError("PUBLIC_SYMBOLS_INVALID")
            result.append(allowed)
        else:
            raise SearchContractError("PUBLIC_SYMBOLS_INVALID")
    return tuple(result)


def _inline_declared_symbols(assumptions: Any) -> tuple[Any, ...]:
    if not isinstance(assumptions, Mapping):
        return ()
    raw = assumptions.get("symbol_assumptions")
    if not isinstance(raw, Mapping):
        return ()
    result: list[Any] = []
    for name in sorted(raw):
        spec = raw[name]
        if not isinstance(name, str) or not isinstance(spec, Mapping):
            continue
        result.append({
            "name": name,
            "nonzero": bool(spec.get("nonzero", False)),
            "real": bool(spec.get("real", True)),
        })
    return tuple(result)


def _inferred_symbols(expressions: tuple[str, ...]) -> tuple[Any, ...]:
    calls = {match for text in expressions for match in _FUNCTION.findall(text)}
    identifiers = {
        match
        for text in expressions
        for match in _IDENTIFIER.findall(text)
        if match not in _RESERVED and match not in calls
    }
    return tuple({"name": name, "real": False, "nonzero": False} for name in sorted(identifiers))


def _public_functions(expressions: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted({
        name
        for text in expressions
        for name in _FUNCTION.findall(text)
        if name not in _RESERVED
    }))


def load_public_case(proposer_view: str | Path) -> PublicCase:
    """Load one public case without touching any evaluator-only artifact."""
    view_path = Path(proposer_view).resolve()
    if view_path.name != "proposer_view.json":
        raise SearchContractError("PUBLIC_ENTRYPOINT_NOT_PROPOSER_VIEW")
    root = view_path.parent.resolve()
    raw = _object(view_path, "PUBLIC_PROPOSER_VIEW_UNREADABLE")
    _audit_public_shape(raw)
    accessed = {"proposer_view.json"}
    catalog = _catalog_from_view(root, raw.get("source_catalog"), accessed)
    assumptions = _assumptions_from_view(root, raw.get("assumptions"), accessed)
    _audit_public_shape(catalog, ("source_catalog",))
    _audit_public_shape(assumptions, ("assumptions",))

    members_raw = catalog.get("members")
    if not isinstance(members_raw, list) or not members_raw:
        raise SearchContractError("PUBLIC_MEMBERS_INVALID")
    members: list[PublicMember] = []
    seen: set[str] = set()
    for item in members_raw:
        if not isinstance(item, Mapping):
            raise SearchContractError("PUBLIC_MEMBER_INVALID")
        member_id, relative, digest = (
            item.get("member_id"), item.get("path"), item.get("sha256")
        )
        if not isinstance(member_id, str) or not member_id or member_id in seen:
            raise SearchContractError("PUBLIC_MEMBER_ID_INVALID")
        seen.add(member_id)
        path = _checked_reference(root, relative, digest, accessed)
        if path.suffix != ".txt" or Path(relative).parts[:1] != ("members",):
            raise SearchContractError(f"PUBLIC_MEMBER_PATH_INVALID:{relative}")
        try:
            expression = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            raise SearchContractError(f"PUBLIC_MEMBER_UNREADABLE:{member_id}") from None
        if not expression.strip():
            raise SearchContractError(f"PUBLIC_MEMBER_EMPTY:{member_id}")
        members.append(PublicMember(member_id, str(relative), str(digest), expression))

    expressions = tuple(item.expression for item in members)
    symbols: tuple[Any, ...] = ()
    namespace_provenance = "INFERRED_PUBLIC_EXPRESSION_INSPECTION"
    symbols_path = catalog.get("symbols_path")
    symbols_hash = catalog.get("symbols_sha256")
    if symbols_path is not None:
        if symbols_hash is None:
            # A path without its exact digest is not a permitted search input.
            raise SearchContractError("PUBLIC_SYMBOLS_HASH_MISSING")
        path = _checked_reference(root, symbols_path, symbols_hash, accessed)
        symbols = _normalize_public_symbols(
            _object(path, "PUBLIC_SYMBOLS_UNREADABLE").get("symbols")
        )
        namespace_provenance = "EXACT_PROPOSER_REFERENCE"
    if not symbols:
        symbols = _inline_declared_symbols(assumptions)
        if symbols:
            namespace_provenance = "DECLARED_INLINE_ASSUMPTIONS"
    if not symbols:
        symbols = _inferred_symbols(expressions)

    case_id = raw.get("case_id", raw.get("package_id", root.name))
    if not isinstance(case_id, str) or not case_id:
        raise SearchContractError("PUBLIC_CASE_ID_INVALID")
    return PublicCase(
        case_id=case_id,
        package_root=root,
        proposer_view_path=view_path,
        members=tuple(members),
        assumptions=assumptions,
        assumption_statuses=_assumption_statuses(assumptions),
        symbols=symbols,
        functions=_public_functions(expressions),
        namespace_provenance=namespace_provenance,
        accessed_paths=tuple(sorted(accessed)),
        proposer_view_sha256=_digest(view_path),
    )
