"""LaTeX/Markdown equation inventory. E2 implements the body.

Inventory extracts labels, environments, order, and source ranges. It does
not interpret LaTeX as symbolic algebra.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml

from .io import (
    MAX_METADATA_BYTES,
    MAX_SOURCE_BYTES,
    contained_relpath,
    decode_utf8,
    read_bytes,
    require_string,
    safe_yaml_mapping,
    sha256_bytes,
    write_new,
)
from .schema import AUDIT_SCHEMA_VERSION, AuditError
from .workspace import REPORTS_DIRECTORY, AuditWorkspace

INVENTORY_SIDECAR = f"{REPORTS_DIRECTORY}/inventory.json"
DUPLICATE_LABEL_NOTE = "duplicate labels are not scientific evidence"

_ENV_PATTERN = r"equation\*?|align\*?|aligned\*?|eqnarray\*?"
_BEGIN_RE = re.compile(r"\\begin\{(" + _ENV_PATTERN + r")\}")
_END_RE = re.compile(r"\\end\{(" + _ENV_PATTERN + r")\}")
_LABEL_RE = re.compile(r"\\label\s*\{([^}]+)\}")
_DOLLAR_RE = re.compile(r"(?<!\\)\$\$")
_BRACKET_OPEN_RE = re.compile(r"(?<!\\)\\\[")
_BRACKET_CLOSE_RE = re.compile(r"(?<!\\)\\\]")

_ROW_FIELDS = (
    "id",
    "label",
    "environment",
    "source_file",
    "start_line",
    "end_line",
    "source_hash",
    "body",
    "curated",
)


@dataclass(frozen=True)
class InventoriedEquation:
    equation_id: str
    label: Optional[str]
    environment: str
    source_file: str
    start_line: int
    end_line: int
    source_hash: str
    body: str
    curated: bool = False


@dataclass(frozen=True)
class EquationInventory:
    equations: tuple[InventoriedEquation, ...]
    duplicate_labels: tuple[str, ...]
    source_hash: str
    warnings: tuple[str, ...]


class _NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True


@dataclass(frozen=True)
class _Block:
    environment: str
    start: int
    end: int
    inner_start: int
    inner_end: int


def inventory_equations(
    workspace: AuditWorkspace,
    *,
    write: bool = False,
    update_manifest: bool = False,
) -> EquationInventory:
    """Extract equation references from the manuscript.

    ``write=True`` writes the tool-owned sidecar ``reports/inventory.json``.
    Researcher-owned ``equations/equations.yaml`` is updated only when
    ``update_manifest=True``. Manuscript sources are never rewritten.
    """
    manifest_path, document, existing_rows = _load_manifest_document(workspace)
    source_rel, _source_path, source_text, source_hash, source_warnings = (
        _read_manuscript(workspace)
    )
    scan_warnings: list[str] = list(source_warnings)
    scanned: list[InventoriedEquation] = []
    if source_text is not None and source_rel is not None:
        scanned, extract_warnings = _extract_from_text(source_text, source_rel)
        scan_warnings.extend(extract_warnings)

    if source_text is None:
        merged_rows = [dict(row) for row in existing_rows]
    else:
        merged_rows = _merge_rows(existing_rows, scanned)

    equations = tuple(
        _equation_from_row(row, manifest_path) for row in merged_rows
    )
    duplicate_labels = _duplicate_labels(equations)
    warnings = tuple(
        list(scan_warnings) + list(_duplicate_warnings(duplicate_labels))
    )
    inventory = EquationInventory(
        equations=equations,
        duplicate_labels=duplicate_labels,
        source_hash=source_hash,
        warnings=warnings,
    )
    if write:
        _write_sidecar(workspace, inventory, source_rel)
        if update_manifest:
            _write_manifest(manifest_path, document, merged_rows)
    return inventory


def load_equation_manifest(workspace: AuditWorkspace) -> EquationInventory:
    """Load equations/equations.yaml including curated mappings."""
    manifest_path, _document, rows = _load_manifest_document(workspace)
    equations = tuple(_equation_from_row(row, manifest_path) for row in rows)
    duplicate_labels = _duplicate_labels(equations)
    _source_rel, _source_path, _text, source_hash, source_warnings = (
        _read_manuscript(workspace)
    )
    warnings = tuple(list(source_warnings) + list(_duplicate_warnings(duplicate_labels)))
    return EquationInventory(
        equations=equations,
        duplicate_labels=duplicate_labels,
        source_hash=source_hash,
        warnings=warnings,
    )


def _read_manuscript(
    workspace: AuditWorkspace,
) -> tuple[Optional[str], Optional[Path], Optional[str], str, tuple[str, ...]]:
    rel, path = contained_relpath(
        workspace.root, workspace.config.manuscript_source, "manuscript_source")
    if not path.is_file() or path.is_symlink():
        return rel, path, None, "", ("manuscript source is missing",)
    raw = read_bytes(path, max_bytes=MAX_SOURCE_BYTES)
    text = decode_utf8(raw, path, "SOURCE_FILE_UNREADABLE")
    return rel, path, text, sha256_bytes(raw), ()


def _load_manifest_document(
    workspace: AuditWorkspace,
) -> tuple[Path, dict, list[dict]]:
    _rel, path = contained_relpath(
        workspace.root, workspace.config.equation_manifest, "equation_manifest")
    raw = read_bytes(path, max_bytes=MAX_METADATA_BYTES)
    mapping = safe_yaml_mapping(raw, path, "AUDIT_SCHEMA_INVALID")
    schema_version = require_string(
        mapping.get("schema_version"), "schema_version",
        "AUDIT_SCHEMA_INVALID", path)
    if schema_version != AUDIT_SCHEMA_VERSION:
        raise AuditError(
            "AUDIT_SCHEMA_INVALID",
            f"schema_version must be {AUDIT_SCHEMA_VERSION}",
            path=str(path),
        )
    equations = mapping.get("equations")
    if not isinstance(equations, list):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID",
            "equations must be a list",
            path=str(path),
        )
    rows: list[dict] = []
    for index, item in enumerate(equations):
        if not isinstance(item, dict) or not all(isinstance(key, str) for key in item):
            raise AuditError(
                "AUDIT_SCHEMA_INVALID",
                f"equations[{index}] must be a mapping",
                path=str(path),
            )
        rows.append(item)
    return path, mapping, rows


def _equation_from_row(row: dict, path: Path) -> InventoriedEquation:
    raw_id = row.get("id", row.get("label"))
    if isinstance(raw_id, int) and not isinstance(raw_id, bool):
        raw_id = str(raw_id)
    equation_id = require_string(raw_id, "id", "AUDIT_SCHEMA_INVALID", path)
    label = _optional_string(row.get("label"), "label", path)
    environment = row.get("environment", "")
    if environment is None:
        environment = ""
    if not isinstance(environment, str):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID", "environment must be a string", path=str(path))
    source_file = row.get("source_file", "")
    if source_file is None:
        source_file = ""
    if not isinstance(source_file, str):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID", "source_file must be a string", path=str(path))
    body = row.get("body", "")
    if body is None:
        body = ""
    if not isinstance(body, str):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID", "body must be a string", path=str(path))
    source_hash = row.get("source_hash")
    if source_hash is None or source_hash == "":
        source_hash = sha256_bytes(body.encode("utf-8"))
    elif not isinstance(source_hash, str):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID", "source_hash must be a string", path=str(path))
    curated = row.get("curated", False)
    if not isinstance(curated, bool):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID", "curated must be a boolean", path=str(path))
    return InventoriedEquation(
        equation_id=equation_id,
        label=label,
        environment=environment,
        source_file=source_file,
        start_line=_int_field(row.get("start_line"), "start_line", path),
        end_line=_int_field(row.get("end_line"), "end_line", path),
        source_hash=source_hash,
        body=body,
        curated=curated,
    )


def _optional_string(value: object, field: str, path: Path) -> Optional[str]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID",
            f"{field} must be a string or null",
            path=str(path),
        )
    stripped = value.strip()
    return stripped or None


def _int_field(value: object, field: str, path: Path) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int):
        raise AuditError(
            "AUDIT_SCHEMA_INVALID",
            f"{field} must be an integer",
            path=str(path),
        )
    return value


def _extract_from_text(
    text: str,
    source_file: str,
) -> tuple[list[InventoriedEquation], tuple[str, ...]]:
    masked = _mask_latex_comments(text)
    warnings: list[str] = []
    blocks = _top_level_environments(masked, warnings)
    occupied = [(block.start, block.end) for block in blocks]
    blocks.extend(_display_blocks(masked, occupied, warnings))
    blocks.sort(key=lambda block: (block.start, block.end))

    extracted: list[InventoriedEquation] = []
    used_anonymous: set[str] = set()
    for block in blocks:
        body = _slice_body(text, block.inner_start, block.inner_end)
        labels = [
            match.group(1).strip()
            for match in _LABEL_RE.finditer(masked[block.inner_start:block.inner_end])
            if match.group(1).strip()
        ]
        start_line = _line_at(text, block.start)
        end_line = _line_at(text, max(block.start, block.end - 1))
        source_hash = sha256_bytes(body.encode("utf-8"))
        if not labels:
            equation_id = _anonymous_id(source_file, start_line, used_anonymous)
            extracted.append(InventoriedEquation(
                equation_id=equation_id,
                label=None,
                environment=block.environment,
                source_file=source_file,
                start_line=start_line,
                end_line=end_line,
                source_hash=source_hash,
                body=body,
            ))
            continue
        for label in labels:
            extracted.append(InventoriedEquation(
                equation_id=label,
                label=label,
                environment=block.environment,
                source_file=source_file,
                start_line=start_line,
                end_line=end_line,
                source_hash=source_hash,
                body=body,
            ))
    return extracted, tuple(warnings)


def _mask_latex_comments(text: str) -> str:
    out: list[str] = []
    in_comment = False
    index = 0
    length = len(text)
    while index < length:
        char = text[index]
        if in_comment:
            if char == "\n":
                in_comment = False
                out.append("\n")
            else:
                out.append(" ")
            index += 1
            continue
        if char == "\\" and index + 1 < length:
            out.append(char)
            out.append(text[index + 1])
            index += 2
            continue
        if char == "%":
            in_comment = True
            out.append(" ")
            index += 1
            continue
        out.append(char)
        index += 1
    return "".join(out)


def _top_level_environments(masked: str, warnings: list[str]) -> list[_Block]:
    tokens: list[tuple[int, str, str, int]] = []
    for match in _BEGIN_RE.finditer(masked):
        tokens.append((match.start(), "begin", match.group(1), match.end()))
    for match in _END_RE.finditer(masked):
        tokens.append((match.start(), "end", match.group(1), match.end()))
    tokens.sort(key=lambda item: (item[0], 0 if item[1] == "begin" else 1))

    stack: list[tuple[str, int, int]] = []
    blocks: list[_Block] = []
    for start, kind, name, token_end in tokens:
        if kind == "begin":
            stack.append((name, start, token_end))
            continue
        if not stack or stack[-1][0] != name:
            warnings.append(
                f"unmatched \\end{{{name}}} at line {_line_at(masked, start)}"
            )
            continue
        env, begin_at, inner_start = stack.pop()
        if not stack:
            blocks.append(_Block(
                environment=env,
                start=begin_at,
                end=token_end,
                inner_start=inner_start,
                inner_end=start,
            ))
    for env, begin_at, _inner_start in stack:
        warnings.append(
            f"unclosed \\begin{{{env}}} at line {_line_at(masked, begin_at)}"
        )
    return blocks


def _display_blocks(
    masked: str,
    occupied: list[tuple[int, int]],
    warnings: list[str],
) -> list[_Block]:
    blocks: list[_Block] = []
    taken = list(occupied)
    for match in _BRACKET_OPEN_RE.finditer(masked):
        if _position_inside(match.start(), taken):
            continue
        close = _BRACKET_CLOSE_RE.search(masked, match.end())
        if close is None:
            warnings.append(
                f"unclosed \\[ at line {_line_at(masked, match.start())}"
            )
            continue
        span = (match.start(), close.end())
        if _overlaps_any(span, taken) or _position_inside(close.start(), taken):
            continue
        taken.append(span)
        blocks.append(_Block(
            environment=r"\[",
            start=match.start(),
            end=close.end(),
            inner_start=match.end(),
            inner_end=close.start(),
        ))
    dollars = [
        (match.start(), match.end())
        for match in _DOLLAR_RE.finditer(masked)
        if not _position_inside(match.start(), taken)
    ]
    index = 0
    while index + 1 < len(dollars):
        open_at, inner_start = dollars[index]
        close_at, close_end = dollars[index + 1]
        span = (open_at, close_end)
        if not _overlaps_any(span, taken):
            taken.append(span)
            blocks.append(_Block(
                environment="$$",
                start=open_at,
                end=close_end,
                inner_start=inner_start,
                inner_end=close_at,
            ))
        index += 2
    if index < len(dollars):
        warnings.append(
            f"unclosed $$ at line {_line_at(masked, dollars[index][0])}"
        )
    return blocks


def _overlaps_any(span: tuple[int, int], occupied: list[tuple[int, int]]) -> bool:
    start, end = span
    for other_start, other_end in occupied:
        if start < other_end and other_start < end:
            return True
    return False


def _position_inside(position: int, occupied: list[tuple[int, int]]) -> bool:
    for start, end in occupied:
        if start <= position < end:
            return True
    return False


def _slice_body(text: str, inner_start: int, inner_end: int) -> str:
    body = text[inner_start:inner_end]
    if body.startswith("\n"):
        body = body[1:]
    if body.endswith("\n"):
        body = body[:-1]
    return body


def _line_at(text: str, position: int) -> int:
    if position < 0:
        return 1
    if position > len(text):
        position = len(text)
    return text.count("\n", 0, position) + 1


def _anonymous_id(source_file: str, start_line: int, used: set[str]) -> str:
    stem = Path(source_file).stem or "eq"
    candidate = f"{stem}-L{start_line}"
    if candidate not in used:
        used.add(candidate)
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in used:
        suffix += 1
    candidate = f"{candidate}-{suffix}"
    used.add(candidate)
    return candidate


def _merge_rows(
    existing_rows: list[dict],
    scanned: list[InventoriedEquation],
) -> list[dict]:
    used: set[int] = set()
    merged: list[dict] = []
    for item in scanned:
        match_index = _match_existing(item, existing_rows, used)
        if match_index is None:
            merged.append(_row_from_equation(item))
            continue
        used.add(match_index)
        merged.append(_overlay_scanned(existing_rows[match_index], item))
    for index, row in enumerate(existing_rows):
        if index in used:
            continue
        if bool(row.get("curated", False)):
            merged.append(dict(row))
    return merged


def _match_existing(
    scanned: InventoriedEquation,
    existing_rows: list[dict],
    used: set[int],
) -> Optional[int]:
    if scanned.label:
        for index, row in enumerate(existing_rows):
            if index in used:
                continue
            row_label = row.get("label")
            if isinstance(row_label, str) and row_label.strip() == scanned.label:
                return index
    for index, row in enumerate(existing_rows):
        if index in used:
            continue
        raw_id = row.get("id")
        if isinstance(raw_id, int) and not isinstance(raw_id, bool):
            raw_id = str(raw_id)
        if isinstance(raw_id, str) and raw_id.strip() == scanned.equation_id:
            return index
    if scanned.label is None:
        for index, row in enumerate(existing_rows):
            if index in used:
                continue
            row_label = row.get("label")
            if isinstance(row_label, str) and row_label.strip():
                continue
            if (row.get("source_file") == scanned.source_file
                    and row.get("start_line") == scanned.start_line):
                return index
    return None


def _row_from_equation(equation: InventoriedEquation) -> dict:
    return {
        "id": equation.equation_id,
        "label": equation.label,
        "environment": equation.environment,
        "source_file": equation.source_file,
        "start_line": equation.start_line,
        "end_line": equation.end_line,
        "source_hash": equation.source_hash,
        "body": equation.body,
        "curated": equation.curated,
    }


def _overlay_scanned(existing: dict, scanned: InventoriedEquation) -> dict:
    row = dict(existing)
    existing_id = existing.get("id")
    if isinstance(existing_id, int) and not isinstance(existing_id, bool):
        existing_id = str(existing_id)
    if isinstance(existing_id, str) and existing_id.strip():
        row["id"] = existing_id.strip()
    else:
        row["id"] = scanned.equation_id
    existing_label = existing.get("label")
    if isinstance(existing_label, str) and existing_label.strip():
        row["label"] = existing_label.strip()
    else:
        row["label"] = scanned.label
    row["curated"] = bool(existing.get("curated", False))
    row["environment"] = scanned.environment
    row["source_file"] = scanned.source_file
    row["start_line"] = scanned.start_line
    row["end_line"] = scanned.end_line
    row["source_hash"] = scanned.source_hash
    row["body"] = scanned.body
    return row


def _duplicate_labels(equations: tuple[InventoriedEquation, ...]) -> tuple[str, ...]:
    counts: dict[str, int] = {}
    duplicates: list[str] = []
    for equation in equations:
        if not equation.label:
            continue
        counts[equation.label] = counts.get(equation.label, 0) + 1
        if counts[equation.label] == 2:
            duplicates.append(equation.label)
    return tuple(duplicates)


def _duplicate_warnings(duplicate_labels: tuple[str, ...]) -> tuple[str, ...]:
    if not duplicate_labels:
        return ()
    listed = ", ".join(duplicate_labels)
    return (f"{DUPLICATE_LABEL_NOTE}: {listed}",)


def _ordered_row(row: dict) -> dict:
    ordered: dict = {}
    for field in _ROW_FIELDS:
        if field in row:
            ordered[field] = row[field]
    for key, value in row.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def _dump_yaml(document: dict) -> str:
    dumped = yaml.dump(
        document,
        Dumper=_NoAliasDumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )
    if not dumped.endswith("\n"):
        dumped += "\n"
    return dumped


def _write_manifest(path: Path, document: dict, rows: list[dict]) -> None:
    output: dict = {"schema_version": AUDIT_SCHEMA_VERSION}
    for key, value in document.items():
        if key in {"schema_version", "equations"}:
            continue
        output[key] = value
    output["equations"] = [_ordered_row(row) for row in rows]
    _replace_text(path, _dump_yaml(output))


def _write_sidecar(
    workspace: AuditWorkspace,
    inventory: EquationInventory,
    source_rel: Optional[str],
) -> None:
    _rel, path = contained_relpath(
        workspace.root, INVENTORY_SIDECAR, "inventory sidecar")
    payload = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "source_file": source_rel,
        "source_hash": inventory.source_hash,
        "equations": [_row_from_equation(item) for item in inventory.equations],
        "duplicate_labels": list(inventory.duplicate_labels),
        "warnings": list(inventory.warnings),
        "note": "inventory counts are workspace inventory, not scientific evidence",
    }
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        _replace_text(path, text)
    else:
        write_new(path, text)


def _replace_text(path: Path, text: str) -> None:
    """Replace an existing file in place. Does not create a new path identity."""
    tmp = path.with_name(path.name + ".tmp")
    try:
        if tmp.exists() or tmp.is_symlink():
            tmp.unlink()
        tmp.write_text(text, encoding="utf-8")
        fd = os.open(tmp, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(tmp, path)
        fd = os.open(path, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except Exception:
        if tmp.exists() and tmp.resolve() != path.resolve():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise
