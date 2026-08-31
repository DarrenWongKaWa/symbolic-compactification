"""Typed-edge lowering to executable residuals. E4 implements the body.

Do not pretend every derivation is a scalar subtraction. Asymptotic remainder
claims must not be rewritten as F - A/gamma = 0.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .edges import AuditEdge, GroundingResult
from .io import MAX_SOURCE_BYTES, contained_relpath, decode_utf8, read_bytes
from .schema import (
    ASYMPTOTIC_CLAIM,
    BOOKKEEPING,
    BZ_PERIODIC_INTEGRATION_BY_PARTS,
    COMPLETENESS_RECONSTRUCTION,
    DEFINITION_INSERTION,
    GLOBAL_SYMMETRY_PAIRING,
    GROUNDING_FAILURE,
    INTEGRAL_ARGUMENT,
    LIMIT_CLAIM,
    LOWERING_PARTIAL,
    LOWERING_SUPPORTED,
    PAIRWISE_REDUCTION,
    SPLIT_PARENT,
    AuditError,
    default_status_for_edge_type,
    lowering_applicability,
)
from .workspace import AuditWorkspace

# These types never become a local residual, even when lhs/rhs/residual
# fields are populated. Asymptotic claims in particular must not be rewritten
# as F - A/gamma = 0.
_NEVER_EXECUTABLE_TYPES = frozenset({
    DEFINITION_INSERTION,
    BOOKKEEPING,
    SPLIT_PARENT,
    ASYMPTOTIC_CLAIM,
    INTEGRAL_ARGUMENT,
    BZ_PERIODIC_INTEGRATION_BY_PARTS,
})

# PARTIAL types that may execute a supplied residual, but must not treat a
# global or naked lhs/rhs difference as an identity.
_RESIDUAL_ONLY_TYPES = frozenset({
    COMPLETENESS_RECONSTRUCTION,
    PAIRWISE_REDUCTION,
    LIMIT_CLAIM,
    GLOBAL_SYMMETRY_PAIRING,
})


@dataclass(frozen=True)
class LoweringResult:
    edge_id: str
    executable: bool
    status: str
    residual_text: Optional[str]
    residual_path: Optional[str]
    obligation_id: Optional[str]
    left: Optional[str]
    right: Optional[str]
    warnings: tuple[str, ...]
    applicability: str


def _load_expression(
    workspace: AuditWorkspace,
    value: Optional[str],
    field: str,
) -> tuple[Optional[str], Optional[str], tuple[str, ...]]:
    """Return ``(native_text, relpath_or_none, warnings)``.

    An existing workspace-relative file wins over inline text. A string that
    is not an existing contained file is treated as native residual text.
    Path traversal is fail-closed and never becomes inline math.
    """
    if value is None:
        return None, None, ()
    if not isinstance(value, str):
        return None, None, ("INVALID_RECORD",)
    text = value.strip()
    if not text:
        return None, None, ()
    try:
        rel, abs_path = contained_relpath(workspace.root, text, field)
    except AuditError as exc:
        if exc.code == "PATH_OUTSIDE_WORKSPACE":
            return None, None, (exc.code,)
        return text, None, ()
    try:
        if abs_path.is_file() and not abs_path.is_symlink():
            raw = read_bytes(abs_path, max_bytes=MAX_SOURCE_BYTES)
            decoded = decode_utf8(raw, abs_path, "SOURCE_DECODE_FAILURE").strip()
            if not decoded:
                return None, None, ("EMPTY_EXPRESSION_FILE",)
            return decoded, rel, ()
    except AuditError as exc:
        return None, None, (exc.code,)
    if rel.startswith("expressions/") or rel.startswith("equations/"):
        return None, None, ("SOURCE_FILE_MISSING",)
    return text, None, ()


def _native_difference(left: str, right: str) -> str:
    return f"({left}) - ({right})"


def lower_edge(
    edge: AuditEdge,
    workspace: AuditWorkspace,
    grounding: GroundingResult,
) -> LoweringResult:
    """Produce an explicit residual or a typed non-executable status.

    Does not call the verifier and never assigns ZERO. Engine adjudication
    of an executable residual is left to the evidence layer.
    """
    applicability = lowering_applicability(edge.edge_type)
    default_status = default_status_for_edge_type(edge.edge_type)

    def finish(
        *,
        executable: bool,
        status: str,
        residual_text: Optional[str] = None,
        residual_path: Optional[str] = None,
        obligation_id: Optional[str] = None,
        left: Optional[str] = None,
        right: Optional[str] = None,
        warnings: tuple[str, ...] = (),
    ) -> LoweringResult:
        return LoweringResult(
            edge_id=edge.edge_id,
            executable=executable,
            status=status,
            residual_text=residual_text,
            residual_path=residual_path,
            obligation_id=obligation_id,
            left=left,
            right=right,
            warnings=warnings,
            applicability=applicability,
        )

    if not grounding.ok:
        return finish(
            executable=False,
            status=GROUNDING_FAILURE,
            warnings=grounding.issues,
        )

    if edge.edge_type in _NEVER_EXECUTABLE_TYPES:
        typed: tuple[str, ...] = ()
        if edge.edge_type == ASYMPTOTIC_CLAIM:
            typed = ("ASYMPTOTIC_REMAINDER_NOT_CERTIFIED",)
        elif edge.edge_type == INTEGRAL_ARGUMENT:
            typed = ("INTEGRAL_ARGUMENT_NOT_LOCAL_RESIDUAL",)
        elif edge.edge_type == BZ_PERIODIC_INTEGRATION_BY_PARTS:
            typed = ("BZ_IBP_NOT_LOCAL_RESIDUAL",)
        return finish(executable=False, status=default_status, warnings=typed)

    residual_text, residual_path, residual_warnings = _load_expression(
        workspace, edge.residual, "residual")
    left_text, left_path, left_warnings = _load_expression(
        workspace, edge.lhs, "lhs")
    right_text, right_path, right_warnings = _load_expression(
        workspace, edge.rhs, "rhs")
    warnings = residual_warnings + left_warnings + right_warnings

    if "PATH_OUTSIDE_WORKSPACE" in warnings:
        return finish(
            executable=False,
            status=GROUNDING_FAILURE,
            left=left_text,
            right=right_text,
            warnings=warnings,
        )

    has_residual = residual_text is not None
    has_lhs_rhs_files = left_path is not None and right_path is not None
    has_both_sides = left_text is not None and right_text is not None

    if edge.edge_type in _RESIDUAL_ONLY_TYPES and not has_residual:
        extra: tuple[str, ...] = ()
        if edge.edge_type == LIMIT_CLAIM:
            extra = ("NAKED_LIMIT_DIFFERENCE_NOT_IDENTITY",)
        elif edge.edge_type == PAIRWISE_REDUCTION and has_both_sides:
            extra = ("PAIRWISE_GLOBAL_SUM_NOT_LOCAL_RESIDUAL",)
        elif edge.edge_type == GLOBAL_SYMMETRY_PAIRING and has_both_sides:
            extra = ("GLOBAL_PAIRING_NOT_LOCAL_RESIDUAL",)
        return finish(
            executable=False,
            status=default_status,
            left=left_text,
            right=right_text,
            warnings=warnings + extra,
        )

    built_text: Optional[str] = None
    built_path: Optional[str] = None
    if has_residual:
        built_text = residual_text
        built_path = residual_path
    elif (has_lhs_rhs_files
          and edge.edge_type not in _RESIDUAL_ONLY_TYPES
          and applicability in {LOWERING_SUPPORTED, LOWERING_PARTIAL}):
        assert left_text is not None and right_text is not None
        built_text = _native_difference(left_text, right_text)
        built_path = None

    if built_text is not None and applicability in {
            LOWERING_SUPPORTED, LOWERING_PARTIAL}:
        return finish(
            executable=True,
            status=default_status,
            residual_text=built_text,
            residual_path=built_path,
            obligation_id=edge.edge_id,
            left=left_text,
            right=right_text,
            warnings=warnings,
        )

    return finish(
        executable=False,
        status=default_status,
        left=left_text,
        right=right_text,
        warnings=warnings,
    )
