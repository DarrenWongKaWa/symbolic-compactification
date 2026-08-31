"""Frozen v0.2 derivation-audit contracts.

This module is the interface freeze for Derivation Audit alpha.  Implementation
modules must import these names rather than inventing parallel enumerations.
LLM or agent text has no authority to assign ZERO, VERIFIED, or CERTIFIED;
only an integrity-bound executable record with engine result ZERO may enter
the machine-verified table.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional

AUDIT_SCHEMA_VERSION = "DerivationAuditV1"
AUDIT_PROTOCOL_VERSION = "0.2.0"
DEFAULT_VERIFIER_ROUTE = "python_sympy_exact_v1"

# --------------------------------------------------------------------------- #
# Status taxonomy
# --------------------------------------------------------------------------- #

ZERO = "ZERO"
NONZERO = "NONZERO"
UNKNOWN = "UNKNOWN"
ASSUMPTION_REQUIRED = "ASSUMPTION_REQUIRED"
DEFINITION = "DEFINITION"
RECORDED = "RECORDED"
SPLIT = "SPLIT"
NOT_LOWERED = "NOT_LOWERED"
PARSE_FAILURE = "PARSE_FAILURE"
GROUNDING_FAILURE = "GROUNDING_FAILURE"
COMPILE_FAILURE = "COMPILE_FAILURE"
INVALID_RECORD = "INVALID_RECORD"
CERTIFIED_BY_CHILDREN = "CERTIFIED_BY_CHILDREN"
CERTIFIED_BY_RULE = "CERTIFIED_BY_RULE"

ENGINE_RESULTS = frozenset({
    ZERO, NONZERO, UNKNOWN, ASSUMPTION_REQUIRED,
    PARSE_FAILURE, COMPILE_FAILURE, GROUNDING_FAILURE, INVALID_RECORD,
})

AUDIT_STATUSES = frozenset({
    ZERO, NONZERO, UNKNOWN, ASSUMPTION_REQUIRED,
    DEFINITION, RECORDED, SPLIT, NOT_LOWERED,
    PARSE_FAILURE, GROUNDING_FAILURE, COMPILE_FAILURE, INVALID_RECORD,
    CERTIFIED_BY_CHILDREN,
    CERTIFIED_BY_RULE,
})

STRUCTURAL_STATUSES = frozenset({
    DEFINITION, RECORDED, SPLIT, CERTIFIED_BY_CHILDREN, CERTIFIED_BY_RULE,
})

UNCERTIFIED_STATUSES = frozenset({
    UNKNOWN, ASSUMPTION_REQUIRED, NOT_LOWERED,
    PARSE_FAILURE, GROUNDING_FAILURE, COMPILE_FAILURE, INVALID_RECORD,
})

# --------------------------------------------------------------------------- #
# Edge types and lowering applicability
# --------------------------------------------------------------------------- #

LOWERING_SUPPORTED = "SUPPORTED"
LOWERING_PARTIAL = "PARTIAL"
LOWERING_NOT_APPLICABLE = "NOT_APPLICABLE"

ALGEBRAIC_EQUIVALENCE = "ALGEBRAIC_EQUIVALENCE"
DEFINITION_INSERTION = "DEFINITION_INSERTION"
INDEX_RELABELING = "INDEX_RELABELING"
PERMUTATION_IDENTITY = "PERMUTATION_IDENTITY"
COEFFICIENT_IDENTITY = "COEFFICIENT_IDENTITY"
LAURENT_COEFFICIENT = "LAURENT_COEFFICIENT"
SERIES_COEFFICIENT = "SERIES_COEFFICIENT"
SYMMETRY_LOCAL = "SYMMETRY_LOCAL"
PROJECTOR_IDENTITY = "PROJECTOR_IDENTITY"
COMPLETENESS_RECONSTRUCTION = "COMPLETENESS_RECONSTRUCTION"
PAIRWISE_REDUCTION = "PAIRWISE_REDUCTION"
DIVIDED_DIFFERENCE = "DIVIDED_DIFFERENCE"
SPECIAL_FUNCTION_IDENTITY = "SPECIAL_FUNCTION_IDENTITY"
SPLIT_PARENT = "SPLIT_PARENT"
ASYMPTOTIC_CLAIM = "ASYMPTOTIC_CLAIM"
LIMIT_CLAIM = "LIMIT_CLAIM"
INTEGRAL_ARGUMENT = "INTEGRAL_ARGUMENT"
GLOBAL_SYMMETRY_PAIRING = "GLOBAL_SYMMETRY_PAIRING"
BOOKKEEPING = "BOOKKEEPING"
CUSTOM_EXACT = "CUSTOM_EXACT"
BZ_PERIODIC_INTEGRATION_BY_PARTS = "BZ_PERIODIC_INTEGRATION_BY_PARTS"

# Named global theorems that may be declared in assumptions.yaml ``rules``.
# The engine never treats these as a local residual.
BZ_TORUS_PERIODICITY = "BZ_TORUS_PERIODICITY"
BRILLOUIN_ZONE_TORUS = "BRILLOUIN_ZONE_TORUS"
ALLOWED_DECLARED_RULES = frozenset({BZ_TORUS_PERIODICITY})
ALLOWED_IBP_DOMAINS = frozenset({BRILLOUIN_ZONE_TORUS})

EDGE_TYPES = frozenset({
    ALGEBRAIC_EQUIVALENCE, DEFINITION_INSERTION, INDEX_RELABELING,
    PERMUTATION_IDENTITY, COEFFICIENT_IDENTITY, LAURENT_COEFFICIENT,
    SERIES_COEFFICIENT, SYMMETRY_LOCAL, PROJECTOR_IDENTITY,
    COMPLETENESS_RECONSTRUCTION, PAIRWISE_REDUCTION, DIVIDED_DIFFERENCE,
    SPECIAL_FUNCTION_IDENTITY, SPLIT_PARENT, ASYMPTOTIC_CLAIM, LIMIT_CLAIM,
    INTEGRAL_ARGUMENT, GLOBAL_SYMMETRY_PAIRING, BOOKKEEPING, CUSTOM_EXACT,
    BZ_PERIODIC_INTEGRATION_BY_PARTS,
})

NON_RESIDUAL_CLAIM_TYPES = frozenset({
    ASYMPTOTIC_CLAIM, LIMIT_CLAIM, INTEGRAL_ARGUMENT,
})

# Finite coefficient identities are independently certifiable.  They never
# certify an enclosing asymptotic remainder claim.
COEFFICIENT_EDGE_TYPES = frozenset({
    COEFFICIENT_IDENTITY, LAURENT_COEFFICIENT, SERIES_COEFFICIENT,
})


@dataclass(frozen=True)
class EdgeTypeSpec:
    name: str
    lowering: str
    default_status: str
    notes: str


EDGE_TYPE_SPECS: dict[str, EdgeTypeSpec] = {
    ALGEBRAIC_EQUIVALENCE: EdgeTypeSpec(
        ALGEBRAIC_EQUIVALENCE, LOWERING_SUPPORTED, NOT_LOWERED,
        "Scalar or expression equality residual lhs - rhs."),
    DEFINITION_INSERTION: EdgeTypeSpec(
        DEFINITION_INSERTION, LOWERING_NOT_APPLICABLE, DEFINITION,
        "Name or definition introduction; not a proof claim."),
    INDEX_RELABELING: EdgeTypeSpec(
        INDEX_RELABELING, LOWERING_SUPPORTED, NOT_LOWERED,
        "Dummy-index or dummy-variable relabeling of an identity."),
    PERMUTATION_IDENTITY: EdgeTypeSpec(
        PERMUTATION_IDENTITY, LOWERING_SUPPORTED, NOT_LOWERED,
        "Finite permutation symmetry of a local kernel."),
    COEFFICIENT_IDENTITY: EdgeTypeSpec(
        COEFFICIENT_IDENTITY, LOWERING_SUPPORTED, NOT_LOWERED,
        "Exact coefficient comparison; not a remainder proof."),
    LAURENT_COEFFICIENT: EdgeTypeSpec(
        LAURENT_COEFFICIENT, LOWERING_SUPPORTED, NOT_LOWERED,
        "Exact Laurent coefficient identity. Finite coefficients do not "
        "prove an asymptotic remainder."),
    SERIES_COEFFICIENT: EdgeTypeSpec(
        SERIES_COEFFICIENT, LOWERING_SUPPORTED, NOT_LOWERED,
        "Exact series coefficient identity, not a remainder certificate."),
    SYMMETRY_LOCAL: EdgeTypeSpec(
        SYMMETRY_LOCAL, LOWERING_SUPPORTED, NOT_LOWERED,
        "Local algebraic symmetry of a kernel or matrix element."),
    PROJECTOR_IDENTITY: EdgeTypeSpec(
        PROJECTOR_IDENTITY, LOWERING_SUPPORTED, NOT_LOWERED,
        "Projector algebra such as P^2 - P = 0 under declared relations."),
    COMPLETENESS_RECONSTRUCTION: EdgeTypeSpec(
        COMPLETENESS_RECONSTRUCTION, LOWERING_PARTIAL, RECORDED,
        "Reconstruction via a declared completeness relation. Executable "
        "only when the completeness rule is an explicit assumption and a "
        "residual is supplied."),
    PAIRWISE_REDUCTION: EdgeTypeSpec(
        PAIRWISE_REDUCTION, LOWERING_PARTIAL, NOT_LOWERED,
        "Local pair identity is lowerable; a global sum is not swallowed "
        "as one residual."),
    DIVIDED_DIFFERENCE: EdgeTypeSpec(
        DIVIDED_DIFFERENCE, LOWERING_SUPPORTED, NOT_LOWERED,
        "Exact divided-difference algebraic identity."),
    SPECIAL_FUNCTION_IDENTITY: EdgeTypeSpec(
        SPECIAL_FUNCTION_IDENTITY, LOWERING_PARTIAL, NOT_LOWERED,
        "Only identities inside the declared verifier catalogue."),
    SPLIT_PARENT: EdgeTypeSpec(
        SPLIT_PARENT, LOWERING_NOT_APPLICABLE, SPLIT,
        "Parent delegated to child obligations. Never itself ZERO."),
    ASYMPTOTIC_CLAIM: EdgeTypeSpec(
        ASYMPTOTIC_CLAIM, LOWERING_NOT_APPLICABLE, UNKNOWN,
        "Global remainder claim. Coefficient children may be ZERO; the "
        "claim is not ZERO without a remainder certificate."),
    LIMIT_CLAIM: EdgeTypeSpec(
        LIMIT_CLAIM, LOWERING_PARTIAL, UNKNOWN,
        "Naked limit differences are not identities. Coefficient or "
        "residue children may be lowered separately."),
    INTEGRAL_ARGUMENT: EdgeTypeSpec(
        INTEGRAL_ARGUMENT, LOWERING_NOT_APPLICABLE, NOT_LOWERED,
        "Integral-level pairing or contour argument is not a local residual."),
    GLOBAL_SYMMETRY_PAIRING: EdgeTypeSpec(
        GLOBAL_SYMMETRY_PAIRING, LOWERING_PARTIAL, NOT_LOWERED,
        "Global pairing over a domain. Local pair kernels may be lowered."),
    BOOKKEEPING: EdgeTypeSpec(
        BOOKKEEPING, LOWERING_NOT_APPLICABLE, RECORDED,
        "Assembly or reconstruction bookkeeping, not an exact residual."),
    CUSTOM_EXACT: EdgeTypeSpec(
        CUSTOM_EXACT, LOWERING_SUPPORTED, NOT_LOWERED,
        "Explicit user-supplied residual with declared semantics."),
    BZ_PERIODIC_INTEGRATION_BY_PARTS: EdgeTypeSpec(
        BZ_PERIODIC_INTEGRATION_BY_PARTS, LOWERING_PARTIAL, NOT_LOWERED,
        "Global BZ-torus integration by parts. Local Leibniz children may "
        "be ZERO; the parent is CERTIFIED_BY_RULE only with declared "
        "BZ_TORUS_PERIODICITY on domain BRILLOUIN_ZONE_TORUS. Never engine "
        "ZERO: SymPy does not evaluate the integral."),
}

# --------------------------------------------------------------------------- #
# Reviewer tables
# --------------------------------------------------------------------------- #

TABLE_VERIFIED = "TABLE_VERIFIED"
TABLE_STRUCTURAL = "TABLE_STRUCTURAL"
TABLE_NONZERO = "TABLE_NONZERO"
TABLE_UNCERTIFIED = "TABLE_UNCERTIFIED"

TABLE_FILENAMES = {
    TABLE_VERIFIED: "TABLE_VERIFIED.md",
    TABLE_STRUCTURAL: "TABLE_STRUCTURAL.md",
    TABLE_NONZERO: "TABLE_NONZERO.md",
    TABLE_UNCERTIFIED: "TABLE_UNCERTIFIED.md",
}

NONZERO_REVIEWER_TEXT = (
    "The encoded residual is NONZERO under the declared symbolic semantics. "
    "Check transcription, assumptions, conventions, and the derivation step."
)

APPROVED_MACHINE_CLAIM = (
    "Exact algebraic and local structural identities that were lowered to "
    "executable residuals were evaluated under the declared symbolic semantics. "
    "Only obligations returning exact ZERO are listed as machine-verified."
)

APPROVED_CAVEAT = (
    "Definitions, integral-level arguments, asymptotic remainder claims, and "
    "unsupported transformations are tracked separately rather than being "
    "misreported as exact algebraic identities."
)

FORBIDDEN_PUBLIC_CLAIMS = (
    "AI proves your paper",
    "AI guarantees the derivation is correct",
    "autonomous theoretical physicist",
    "discovers hidden physics",
    "formal proof assistant",
    "universal CAS proof system",
    "every manuscript step can be certified",
)

CLI_AUDIT_COMMANDS = (
    "init", "inventory", "inspect", "verify", "table", "report", "package",
)

WORKSPACE_LAYOUT = (
    "audit.yaml",
    "manuscript/",
    "equations/equations.yaml",
    "edges/edges.yaml",
    "expressions/",
    "assumptions/assumptions.yaml",
    "runs/",
    "reports/",
)

AUDIT_YAML_KEYS = frozenset({
    "schema_version",
    "audit_name",
    "manuscript_source",
    "equation_manifest",
    "edge_manifest",
    "assumptions",
    "output_dir",
    "verifier_profile",
})
AUDIT_YAML_REQUIRED = frozenset({
    "schema_version",
    "audit_name",
    "manuscript_source",
    "equation_manifest",
    "edge_manifest",
    "assumptions",
    "output_dir",
    "verifier_profile",
})

MACHINE_RECORD_FIELDS = (
    "audit_id",
    "edge_id",
    "source_refs",
    "edge_type",
    "lhs_hash",
    "rhs_hash",
    "residual_hash",
    "assumptions_hash",
    "source_snapshot_hash",
    "obligation_hash",
    "verifier_route",
    "engine_version",
    "result",
    "runtime_seconds",
    "warnings",
)

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_HASH_RE = re.compile(r"[0-9a-f]{64}\Z")
_ROUTE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/-]{0,127}\Z")


class AuditError(ValueError):
    """Stable audit failure with a machine-readable code."""

    def __init__(self, code: str, detail: str, *, path: Optional[str] = None):
        self.code = code
        self.detail = detail
        self.path = path
        location = "" if path is None else f" ({path})"
        super().__init__(f"{code}{location}: {detail}")


def public_status_label(status: str) -> str:
    """Reviewer-facing label. SPLIT certification is never displayed as ZERO."""
    if status == CERTIFIED_BY_CHILDREN:
        return "SPLIT — all children certified"
    if status == CERTIFIED_BY_RULE:
        return "CERTIFIED_BY_RULE — local ZERO + declared BZ-torus IBP"
    return status


def default_status_for_edge_type(edge_type: str) -> str:
    spec = EDGE_TYPE_SPECS.get(edge_type)
    if spec is None:
        raise AuditError("UNKNOWN_EDGE_TYPE", f"unsupported edge type {edge_type!r}")
    return spec.default_status


def lowering_applicability(edge_type: str) -> str:
    spec = EDGE_TYPE_SPECS.get(edge_type)
    if spec is None:
        raise AuditError("UNKNOWN_EDGE_TYPE", f"unsupported edge type {edge_type!r}")
    return spec.lowering


def asymptotic_remainder_certified(remainder_certificate_hash: Optional[str]) -> bool:
    """Finite coefficient agreement is not a remainder proof."""
    return bool(remainder_certificate_hash) and bool(
        _HASH_RE.fullmatch(remainder_certificate_hash))


@dataclass(frozen=True)
class AuditRecord:
    """Immutable machine evidence for one derivation edge.

    ``result`` is the engine/adjudication outcome. ``status`` is the typed
    derivation-audit status. Only ``status == result == ZERO`` with passing
    integrity may appear in TABLE_VERIFIED. LLM text cannot populate this
    record with authority.
    """

    audit_id: str
    edge_id: str
    source_refs: tuple[str, ...]
    edge_type: str
    status: str
    result: str
    source_snapshot_hash: str
    engine_version: str
    runtime_seconds: float = 0.0
    lhs_hash: Optional[str] = None
    rhs_hash: Optional[str] = None
    residual_hash: Optional[str] = None
    assumptions_hash: Optional[str] = None
    obligation_hash: Optional[str] = None
    verifier_route: Optional[str] = None
    warnings: tuple[str, ...] = ()
    children: tuple[str, ...] = ()
    remainder_certificate_hash: Optional[str] = None
    declared_assumptions: tuple[str, ...] = ()
    executable: bool = False
    claim: str = ""
    residual_text: Optional[str] = None
    artifact_relpath: Optional[str] = None
    schema_version: str = AUDIT_SCHEMA_VERSION
    required_rules: tuple[str, ...] = ()
    ibp_domain: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "audit_id": self.audit_id,
            "edge_id": self.edge_id,
            "source_refs": list(self.source_refs),
            "edge_type": self.edge_type,
            "status": self.status,
            "result": self.result,
            "lhs_hash": self.lhs_hash,
            "rhs_hash": self.rhs_hash,
            "residual_hash": self.residual_hash,
            "assumptions_hash": self.assumptions_hash,
            "source_snapshot_hash": self.source_snapshot_hash,
            "obligation_hash": self.obligation_hash,
            "verifier_route": self.verifier_route,
            "engine_version": self.engine_version,
            "runtime_seconds": self.runtime_seconds,
            "warnings": list(self.warnings),
            "children": list(self.children),
            "remainder_certificate_hash": self.remainder_certificate_hash,
            "declared_assumptions": list(self.declared_assumptions),
            "executable": self.executable,
            "claim": self.claim,
            "residual_text": self.residual_text,
            "artifact_relpath": self.artifact_relpath,
            "required_rules": list(self.required_rules),
            "ibp_domain": self.ibp_domain,
        }


def _valid_id(value: str) -> bool:
    return isinstance(value, str) and bool(_ID_RE.fullmatch(value))


def _valid_hash(value: Optional[str], *, required: bool) -> bool:
    if value is None:
        return not required
    return isinstance(value, str) and bool(_HASH_RE.fullmatch(value))


def integrity_issues(record: AuditRecord) -> tuple[str, ...]:
    """Return machine-integrity defects. An empty tuple means PASS."""
    issues: list[str] = []
    if record.schema_version != AUDIT_SCHEMA_VERSION:
        issues.append("SCHEMA_VERSION_MISMATCH")
    if not _valid_id(record.audit_id):
        issues.append("AUDIT_ID_INVALID")
    if not _valid_id(record.edge_id):
        issues.append("EDGE_ID_INVALID")
    if record.edge_type not in EDGE_TYPES:
        issues.append("EDGE_TYPE_INVALID")
    if record.status not in AUDIT_STATUSES:
        issues.append("STATUS_INVALID")
    if record.result not in ENGINE_RESULTS and record.result not in AUDIT_STATUSES:
        issues.append("RESULT_INVALID")
    if not _valid_hash(record.source_snapshot_hash, required=True):
        issues.append("SOURCE_SNAPSHOT_HASH_INVALID")
    if not isinstance(record.engine_version, str) or not record.engine_version:
        issues.append("ENGINE_VERSION_INVALID")
    if not isinstance(record.runtime_seconds, (int, float)) or record.runtime_seconds < 0:
        issues.append("RUNTIME_INVALID")
    if record.executable:
        if not _valid_hash(record.residual_hash, required=True):
            issues.append("RESIDUAL_HASH_REQUIRED")
        if not _valid_hash(record.obligation_hash, required=True):
            issues.append("OBLIGATION_HASH_REQUIRED")
        if not _valid_hash(record.assumptions_hash, required=True):
            issues.append("ASSUMPTIONS_HASH_REQUIRED")
        if not (isinstance(record.verifier_route, str)
                and _ROUTE_RE.fullmatch(record.verifier_route)):
            issues.append("VERIFIER_ROUTE_REQUIRED")
    else:
        if not _valid_hash(record.residual_hash, required=False):
            issues.append("RESIDUAL_HASH_INVALID")
        if not _valid_hash(record.obligation_hash, required=False):
            issues.append("OBLIGATION_HASH_INVALID")
        if not _valid_hash(record.assumptions_hash, required=False):
            issues.append("ASSUMPTIONS_HASH_INVALID")
    if not _valid_hash(record.lhs_hash, required=False):
        issues.append("LHS_HASH_INVALID")
    if not _valid_hash(record.rhs_hash, required=False):
        issues.append("RHS_HASH_INVALID")
    if not _valid_hash(record.remainder_certificate_hash, required=False):
        issues.append("REMAINDER_CERTIFICATE_HASH_INVALID")
    if record.status == ZERO and record.result != ZERO:
        issues.append("STATUS_ZERO_REQUIRES_ENGINE_ZERO")
    if record.status == ZERO and not record.executable:
        issues.append("STATUS_ZERO_REQUIRES_EXECUTABLE")
    if record.edge_type == ASYMPTOTIC_CLAIM and record.result == ZERO:
        if not asymptotic_remainder_certified(record.remainder_certificate_hash):
            issues.append("ASYMPTOTIC_ZERO_WITHOUT_REMAINDER_CERTIFICATE")
    if record.edge_type == SPLIT_PARENT and record.status == ZERO:
        issues.append("SPLIT_PARENT_CANNOT_BE_ENGINE_ZERO")
    if record.edge_type == BZ_PERIODIC_INTEGRATION_BY_PARTS and record.status == ZERO:
        issues.append("BZ_IBP_PARENT_CANNOT_BE_ENGINE_ZERO")
    if record.status == CERTIFIED_BY_CHILDREN and record.edge_type != SPLIT_PARENT:
        issues.append("CERTIFIED_BY_CHILDREN_REQUIRES_SPLIT_PARENT")
    if (
            record.status == CERTIFIED_BY_RULE
            and record.edge_type != BZ_PERIODIC_INTEGRATION_BY_PARTS):
        issues.append("CERTIFIED_BY_RULE_REQUIRES_BZ_IBP")
    return tuple(issues)


def integrity_ok(record: AuditRecord) -> bool:
    return not integrity_issues(record)


def may_appear_in_verified_table(record: AuditRecord) -> bool:
    """Authoritative inclusion rule. Markdown cannot create a verified row."""
    if not integrity_ok(record):
        return False
    if record.result != ZERO or record.status != ZERO:
        return False
    if not record.executable:
        return False
    if record.edge_type == SPLIT_PARENT:
        return False
    if record.edge_type == ASYMPTOTIC_CLAIM:
        return False
    if record.edge_type == BZ_PERIODIC_INTEGRATION_BY_PARTS:
        return False
    if record.status == CERTIFIED_BY_RULE:
        return False
    return True


def table_bucket(record: AuditRecord) -> str:
    """Assign a record to exactly one reviewer table."""
    if not integrity_ok(record):
        return TABLE_UNCERTIFIED
    if record.result == NONZERO or record.status == NONZERO:
        return TABLE_NONZERO
    if may_appear_in_verified_table(record):
        return TABLE_VERIFIED
    if record.status in STRUCTURAL_STATUSES:
        return TABLE_STRUCTURAL
    return TABLE_UNCERTIFIED


def derive_split_parent_status(
    parent: AuditRecord,
    children: Mapping[str, AuditRecord],
) -> str:
    """Return SPLIT or CERTIFIED_BY_CHILDREN. Never ZERO.

    Required children are ``parent.children``. Every required child must be
    present, integrity-ok, and status/result ZERO. A missing, UNKNOWN, or
    NONZERO child blocks parent certification.
    """
    if parent.edge_type != SPLIT_PARENT:
        raise AuditError(
            "NOT_SPLIT_PARENT",
            f"edge {parent.edge_id} is not a SPLIT_PARENT",
        )
    if not parent.children:
        return SPLIT
    for child_id in parent.children:
        child = children.get(child_id)
        if child is None:
            return SPLIT
        if not integrity_ok(child):
            return SPLIT
        if child.result != ZERO or child.status != ZERO:
            return SPLIT
    return CERTIFIED_BY_CHILDREN


def derive_bz_ibp_parent_status(
    parent: AuditRecord,
    children: Mapping[str, AuditRecord],
    declared_rules: tuple[str, ...] | frozenset[str],
) -> str:
    """Return CERTIFIED_BY_RULE, ASSUMPTION_REQUIRED, or NOT_LOWERED. Never ZERO.

    Certificate is local child ZERO plus a declared BZ-torus periodicity
    theorem. The engine does not evaluate the Brillouin-zone integral.
    """
    if parent.edge_type != BZ_PERIODIC_INTEGRATION_BY_PARTS:
        raise AuditError(
            "NOT_BZ_IBP_PARENT",
            f"edge {parent.edge_id} is not BZ_PERIODIC_INTEGRATION_BY_PARTS",
        )
    domain = parent.ibp_domain
    if domain is None or domain not in ALLOWED_IBP_DOMAINS:
        return NOT_LOWERED
    required = tuple(parent.required_rules)
    if not required or BZ_TORUS_PERIODICITY not in required:
        return ASSUMPTION_REQUIRED
    if any(name not in ALLOWED_DECLARED_RULES for name in required):
        return NOT_LOWERED
    declared = frozenset(declared_rules)
    if any(name not in declared for name in required):
        return ASSUMPTION_REQUIRED
    if not parent.children:
        return NOT_LOWERED
    for child_id in parent.children:
        child = children.get(child_id)
        if child is None:
            return NOT_LOWERED
        if not integrity_ok(child):
            return NOT_LOWERED
        if child.result != ZERO or child.status != ZERO:
            return NOT_LOWERED
    return CERTIFIED_BY_RULE


def record_from_mapping(data: Mapping[str, Any]) -> AuditRecord:
    """Load a record from JSON. Does not trust caller status labels."""
    def _tuple(name: str) -> tuple[str, ...]:
        value = data.get(name, ())
        if value is None:
            return ()
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise AuditError("INVALID_RECORD", f"{name} must be a list of strings")
        return tuple(value)

    def _opt_str(name: str) -> Optional[str]:
        value = data.get(name)
        if value is None:
            return None
        if not isinstance(value, str):
            raise AuditError("INVALID_RECORD", f"{name} must be a string or null")
        return value

    try:
        runtime = data.get("runtime_seconds", 0.0)
        executable = bool(data.get("executable", False))
        return AuditRecord(
            audit_id=str(data["audit_id"]),
            edge_id=str(data["edge_id"]),
            source_refs=_tuple("source_refs"),
            edge_type=str(data["edge_type"]),
            status=str(data["status"]),
            result=str(data["result"]),
            source_snapshot_hash=str(data["source_snapshot_hash"]),
            engine_version=str(data["engine_version"]),
            runtime_seconds=float(runtime),
            lhs_hash=_opt_str("lhs_hash"),
            rhs_hash=_opt_str("rhs_hash"),
            residual_hash=_opt_str("residual_hash"),
            assumptions_hash=_opt_str("assumptions_hash"),
            obligation_hash=_opt_str("obligation_hash"),
            verifier_route=_opt_str("verifier_route"),
            warnings=_tuple("warnings"),
            children=_tuple("children"),
            remainder_certificate_hash=_opt_str("remainder_certificate_hash"),
            declared_assumptions=_tuple("declared_assumptions"),
            executable=executable,
            claim=str(data.get("claim") or ""),
            residual_text=_opt_str("residual_text"),
            artifact_relpath=_opt_str("artifact_relpath"),
            schema_version=str(data.get("schema_version") or AUDIT_SCHEMA_VERSION),
            required_rules=_tuple("required_rules"),
            ibp_domain=_opt_str("ibp_domain"),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise AuditError("INVALID_RECORD", str(exc)) from None
