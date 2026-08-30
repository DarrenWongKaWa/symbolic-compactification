"""Read-only, hash-bound projection of frozen SOL relation artifacts."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

import sympy

from research.representation_program_search.program_ir import canonical_json
from research.representation_program_search.search import PublicCase
from symbolic_compactification.observations.ir import (
    DESCRIPTIVE_ONLY,
    EXACTNESS_CLASSES,
    RELATION_TYPES,
)
from symbolic_compactification.observations.leak import assert_no_interpretation
from symbolic_compactification.parser import parse_expression

from .authority import authority_manifest, validate_local_authority
from .model import (
    SOL_ARTIFACT_SCHEMA,
    SOL_AUTHORITY_COMMIT,
    SOL_LAYER,
    ProjectedSOLRelation,
    SOLProjection,
)
from .replay_contract import (
    SOL_REPLAY_BACKENDS,
    SOL_REPLAY_STATUS_BACKENDS,
    replay_policy_payload,
    structural_container_metadata,
)

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_FORBIDDEN_KEYS = frozenset({
    "answer",
    "audited_depth",
    "evaluator",
    "expected_success",
    "expected_verdict",
    "gold",
    "gold_operator_sequence",
    "gold_program",
    "hidden_member_roles",
    "operator_sequence",
    "proof_status",
    "reference_program",
    "representation_depth",
    "success",
    "target",
    "target_representation",
    "target_representation_type",
    "target_type",
    "verdict",
    "verified_obligations",
})
_ELIGIBLE_RELATION_TYPES = frozenset({
    "AC_EQUIVALENT",
    "CANONICALLY_EQUIVALENT",
    "CSE_SHARED",
    "DERIVATIVE_RELATED",
    "EGRAPH_EQUIVALENT",
    "IDENTICAL",
    "INDEX_RENAMING_RELATED",
    "KNOWN_REWRITE_EQUIVALENT",
    "LGG_FAMILY",
    "PATTERN_MATCH",
    "PERMUTATION_RELATED",
    "RECURRENCE_CANDIDATE",
    "SAME_DENOMINATOR_FAMILY",
    "SAME_FUNCTION_FAMILY",
    "SAME_INDEX_ORBIT",
    "SAME_POLE_SIGNATURE",
    "SUBSTITUTION_INSTANCE",
    "TENSOR_SYMMETRY_RELATED",
})
_BUNDLE_FIELDS = frozenset({
    "backend_status",
    "canonical_variants",
    "expression_summary",
    "families",
    "nodes",
    "packets",
    "provenance",
    "relations",
})
_NODE_FIELDS = frozenset({
    "free_symbols",
    "functions",
    "indexed_symbols",
    "node_id",
    "ops",
    "provenance",
    "source_span",
    "srepr",
    "structural_hash",
    "text",
})
_RELATION_FIELDS = frozenset({
    "assumptions",
    "backend",
    "backend_version",
    "confidence_class",
    "evidence",
    "exactness_class",
    "relation_type",
    "source_ids",
    "theory",
    "witness",
})


class _ProjectionFailure(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _fail(
    case: PublicCase,
    code: str,
    *,
    expected: str | None,
    actual: str | None,
) -> SOLProjection:
    return SOLProjection(
        status="UNAVAILABLE",
        reason_codes=(code,),
        source_artifact_sha256=actual,
        expected_artifact_sha256=expected,
        public_case_sha256=case.proposer_view_sha256,
    )


def _scan_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).lower()
            if normalized in _FORBIDDEN_KEYS or normalized.startswith("gold_"):
                raise _ProjectionFailure(f"SOL_FORBIDDEN_FIELD:{key}")
            _scan_forbidden_keys(child)
    elif isinstance(value, list):
        for child in value:
            _scan_forbidden_keys(child)


def _case_binding(case: PublicCase) -> dict[str, Any]:
    return {
        "case_id": case.case_id,
        "proposer_view_sha256": case.proposer_view_sha256,
        "source_members": [
            {"member_id": item.member_id, "sha256": item.sha256}
            for item in sorted(case.members, key=lambda item: item.member_id)
        ],
    }


def _bundle_sha256(bundle: Mapping[str, Any]) -> str:
    return _digest(canonical_json(dict(bundle)).encode("utf-8"))


def _validate_replay_attestation(
    case: PublicCase,
    bundle: Mapping[str, Any],
    attestation: Any,
) -> None:
    if not isinstance(attestation, Mapping) or set(attestation) != {
        "authority_manifest_sha256",
        "backend_provenance",
        "bundle_sha256",
        "environment_versions",
        "mode",
        "public_case_sha256",
        "replay_policy",
        "structural_container",
    }:
        raise _ProjectionFailure("SOL_REPLAY_ATTESTATION_INVALID")
    expected_scalars = {
        "authority_manifest_sha256": authority_manifest()["manifest_sha256"],
        "bundle_sha256": _bundle_sha256(bundle),
        "mode": "READ_ONLY_FROZEN_SOL_REPLAY",
        "public_case_sha256": case.proposer_view_sha256,
        "replay_policy": replay_policy_payload(),
        "structural_container": structural_container_metadata(case),
    }
    if any(attestation.get(key) != value for key, value in expected_scalars.items()):
        raise _ProjectionFailure("SOL_REPLAY_ATTESTATION_INVALID")
    summary = bundle.get("expression_summary")
    if not isinstance(summary, Mapping) or summary.get("raw_sha256") != (
        expected_scalars["structural_container"]["expression_sha256"]
    ):
        raise _ProjectionFailure("SOL_CONTAINER_HASH_MISMATCH")
    provenance = bundle.get("provenance")
    backend_provenance = attestation.get("backend_provenance")
    if not isinstance(provenance, Mapping) or not isinstance(backend_provenance, Mapping):
        raise _ProjectionFailure("SOL_BACKEND_PROVENANCE_INVALID")
    if set(backend_provenance) != {
        "backend_status", "backend_versions", "backends_run",
    }:
        raise _ProjectionFailure("SOL_BACKEND_PROVENANCE_INVALID")
    backends_run = provenance.get("backends_run")
    if (
        backend_provenance.get("backend_status") != bundle.get("backend_status")
        or backend_provenance.get("backends_run") != backends_run
        or not isinstance(backends_run, list)
        or any(item not in SOL_REPLAY_BACKENDS for item in backends_run)
        or backends_run != [item for item in SOL_REPLAY_BACKENDS if item in backends_run]
    ):
        raise _ProjectionFailure("SOL_BACKEND_PROVENANCE_INVALID")
    backend_versions = backend_provenance.get("backend_versions")
    if (
        not isinstance(backend_versions, Mapping)
        or set(backend_versions) != set(SOL_REPLAY_BACKENDS)
        or any(value is not None and not isinstance(value, str) for value in backend_versions.values())
    ):
        raise _ProjectionFailure("SOL_BACKEND_VERSIONS_INVALID")
    environment = attestation.get("environment_versions")
    if (
        not isinstance(environment, Mapping)
        or set(environment) != {
            "egglog",
            "lgg",
            "machine",
            "matchpy",
            "python_implementation",
            "python_version",
            "sympy",
            "system",
            "system_release",
        }
        or any(value is not None and not isinstance(value, str) for value in environment.values())
    ):
        raise _ProjectionFailure("SOL_ENVIRONMENT_VERSIONS_INVALID")
    if any(
        environment[name] != backend_versions[name]
        for name in SOL_REPLAY_BACKENDS
    ):
        raise _ProjectionFailure("SOL_ENVIRONMENT_VERSIONS_INVALID")


def _member_subexpressions(case: PublicCase) -> dict[str, set[str]]:
    owners: dict[str, set[str]] = {}
    for member in case.members:
        try:
            expression = parse_expression(
                member.expression,
                list(case.symbols),
                functions=list(case.functions) or None,
            )
        except Exception as exc:
            raise _ProjectionFailure(
                f"SOL_PUBLIC_MEMBER_PARSE_FAILURE:{member.member_id}:{type(exc).__name__}"
            ) from None
        for item in sympy.preorder_traversal(expression):
            owners.setdefault(sympy.srepr(item), set()).add(member.member_id)
    return owners


def _validated_nodes(bundle: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    raw = bundle.get("nodes")
    if not isinstance(raw, list):
        raise _ProjectionFailure("SOL_NODES_INVALID")
    nodes: dict[str, Mapping[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping):
            raise _ProjectionFailure("SOL_NODE_INVALID")
        if set(item) != _NODE_FIELDS:
            raise _ProjectionFailure("SOL_NODE_FIELDS_INVALID")
        node_id = item.get("node_id")
        srepr = item.get("srepr")
        structural_hash = item.get("structural_hash")
        if not isinstance(node_id, str) or not node_id or node_id in nodes:
            raise _ProjectionFailure("SOL_NODE_ID_INVALID")
        if not isinstance(srepr, str) or not isinstance(structural_hash, str):
            raise _ProjectionFailure(f"SOL_NODE_CONTENT_INVALID:{node_id}")
        if _digest(srepr.encode("utf-8")) != structural_hash:
            raise _ProjectionFailure(f"SOL_NODE_HASH_MISMATCH:{node_id}")
        free_symbols = item.get("free_symbols", [])
        if not isinstance(free_symbols, list) or not all(
            isinstance(symbol, str) for symbol in free_symbols
        ):
            raise _ProjectionFailure(f"SOL_NODE_SYMBOLS_INVALID:{node_id}")
        nodes[node_id] = item
    return nodes


def _relation_identifier(raw: Mapping[str, Any]) -> str:
    return "SOLR_" + _digest(canonical_json(dict(raw)).encode("utf-8"))


def _project_relations(
    case: PublicCase,
    bundle: Mapping[str, Any],
    artifact_sha256: str,
) -> tuple[ProjectedSOLRelation, ...]:
    nodes = _validated_nodes(bundle)
    owners_by_srepr = _member_subexpressions(case)
    raw_relations = bundle.get("relations")
    if not isinstance(raw_relations, list):
        raise _ProjectionFailure("SOL_RELATIONS_INVALID")
    projected: dict[str, ProjectedSOLRelation] = {}
    for raw in raw_relations:
        if not isinstance(raw, Mapping):
            raise _ProjectionFailure("SOL_RELATION_INVALID")
        if set(raw) != _RELATION_FIELDS:
            raise _ProjectionFailure("SOL_RELATION_FIELDS_INVALID")
        relation_type = raw.get("relation_type")
        exactness = raw.get("exactness_class")
        backend = raw.get("backend")
        source_ids = raw.get("source_ids")
        if relation_type not in RELATION_TYPES:
            raise _ProjectionFailure("SOL_RELATION_TYPE_INVALID")
        if exactness not in EXACTNESS_CLASSES:
            raise _ProjectionFailure("SOL_RELATION_EXACTNESS_INVALID")
        if relation_type in DESCRIPTIVE_ONLY and exactness == "EXACT_FACT":
            raise _ProjectionFailure("SOL_RELATION_EXACTNESS_ESCALATION")
        if not isinstance(backend, str) or not backend:
            raise _ProjectionFailure("SOL_RELATION_BACKEND_INVALID")
        for field in ("evidence", "confidence_class"):
            if not isinstance(raw.get(field), str):
                raise _ProjectionFailure(f"SOL_RELATION_{field.upper()}_INVALID")
        assumptions = raw.get("assumptions")
        if not isinstance(assumptions, list) or not all(
            isinstance(item, str) for item in assumptions
        ):
            raise _ProjectionFailure("SOL_RELATION_ASSUMPTIONS_INVALID")
        for field in ("witness", "theory", "backend_version"):
            if raw.get(field) is not None and not isinstance(raw.get(field), str):
                raise _ProjectionFailure(f"SOL_RELATION_{field.upper()}_INVALID")
        if relation_type not in _ELIGIBLE_RELATION_TYPES:
            continue
        if not isinstance(source_ids, list) or not source_ids or not all(
            isinstance(node_id, str) for node_id in source_ids
        ):
            # Orphan/aggregate relations cannot be routed to a public action.
            continue
        if len(source_ids) != len(set(source_ids)):
            raise _ProjectionFailure("SOL_RELATION_NODES_DUPLICATED")
        if any(node_id not in nodes for node_id in source_ids):
            raise _ProjectionFailure("SOL_RELATION_NODE_UNKNOWN")
        affected: set[str] = set()
        symbols: set[str] = set()
        all_nodes_public = True
        for node_id in source_ids:
            node = nodes[node_id]
            owners = owners_by_srepr.get(str(node["srepr"]), set())
            if not owners:
                all_nodes_public = False
                break
            affected.update(owners)
            symbols.update(node.get("free_symbols") or [])
        if not all_nodes_public or not affected:
            continue
        relation_id = _relation_identifier(raw)
        projected[relation_id] = ProjectedSOLRelation(
            relation_id=relation_id,
            relation_type=str(relation_type),
            exactness_class=str(exactness),
            backend=backend,
            source_node_ids=tuple(source_ids),
            affected_member_ids=tuple(sorted(affected)),
            node_symbols=tuple(sorted(symbols)),
            source_artifact_sha256=artifact_sha256,
        )
    return tuple(projected[key] for key in sorted(projected))


def load_sol_projection(
    case: PublicCase,
    artifact_path: str | Path,
    *,
    expected_sha256: str,
) -> SOLProjection:
    """Load one immutable SOL artifact; never run or retune SOL here."""
    expected = expected_sha256 if isinstance(expected_sha256, str) else None
    if expected is None or not _HASH.fullmatch(expected):
        return _fail(case, "SOL_EXPECTED_HASH_INVALID", expected=expected, actual=None)
    path = Path(artifact_path)
    try:
        relative = path.resolve().relative_to(case.package_root.resolve())
    except ValueError:
        relative = None
    if relative is not None and any(
        part.lower() in {"evaluator", "evaluation", "reference", "verification", "runs", "steps", "final"}
        for part in relative.parts
    ):
        return _fail(case, "SOL_ARTIFACT_PATH_FORBIDDEN", expected=expected, actual=None)
    try:
        raw_bytes = path.read_bytes()
    except OSError:
        return _fail(case, "SOL_ARTIFACT_MISSING", expected=expected, actual=None)
    actual = _digest(raw_bytes)
    if actual != expected:
        return _fail(case, "SOL_ARTIFACT_HASH_MISMATCH", expected=expected, actual=actual)
    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _fail(case, "SOL_ARTIFACT_UNREADABLE", expected=expected, actual=actual)
    try:
        if not isinstance(data, Mapping):
            raise _ProjectionFailure("SOL_ARTIFACT_NOT_OBJECT")
        _scan_forbidden_keys(data)
        if set(data) != {
            "bundle",
            "case_binding",
            "replay_attestation",
            "schema_version",
            "sol_authority",
        }:
            raise _ProjectionFailure("SOL_ARTIFACT_FIELDS_INVALID")
        if data.get("schema_version") != SOL_ARTIFACT_SCHEMA:
            raise _ProjectionFailure("SOL_ARTIFACT_SCHEMA_INVALID")
        if data.get("sol_authority") != {
            "commit": SOL_AUTHORITY_COMMIT,
            "layer": SOL_LAYER,
            **authority_manifest(),
        }:
            raise _ProjectionFailure("SOL_AUTHORITY_INVALID")
        local_authority_failures = validate_local_authority(
            Path(__file__).resolve().parents[3]
        )
        if local_authority_failures:
            raise _ProjectionFailure(local_authority_failures[0])
        if data.get("case_binding") != _case_binding(case):
            raise _ProjectionFailure("SOL_CASE_BINDING_MISMATCH")
        bundle = data.get("bundle")
        if not isinstance(bundle, Mapping):
            raise _ProjectionFailure("SOL_BUNDLE_INVALID")
        if set(bundle) != _BUNDLE_FIELDS:
            raise _ProjectionFailure("SOL_BUNDLE_FIELDS_INVALID")
        _validate_replay_attestation(case, bundle, data.get("replay_attestation"))
        provenance = bundle.get("provenance")
        if not isinstance(provenance, Mapping) or provenance.get("layer") != SOL_LAYER:
            raise _ProjectionFailure("SOL_BUNDLE_PROVENANCE_INVALID")
        if provenance.get("context_keys") != ["rps_replay_policy"]:
            raise _ProjectionFailure("SOL_BUNDLE_CONTEXT_INVALID")
        backends_run = provenance.get("backends_run")
        if not isinstance(backends_run, list) or not all(
            isinstance(item, str) for item in backends_run
        ):
            raise _ProjectionFailure("SOL_BUNDLE_BACKENDS_INVALID")
        if any(
            isinstance(item, Mapping) and item.get("backend") not in backends_run
            for item in bundle.get("relations", [])
        ):
            raise _ProjectionFailure("SOL_RELATION_BACKEND_NOT_ATTESTED")
        backend_status = bundle.get("backend_status")
        if not isinstance(backend_status, Mapping) or any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in backend_status.items()
        ):
            raise _ProjectionFailure("SOL_BUNDLE_BACKEND_STATUS_INVALID")
        if set(backend_status) != set(SOL_REPLAY_STATUS_BACKENDS):
            raise _ProjectionFailure("SOL_BUNDLE_BACKEND_STATUS_INVALID")
        assert_no_interpretation(bundle)
        relations = _project_relations(case, bundle, actual)
    except _ProjectionFailure as exc:
        return _fail(case, exc.code, expected=expected, actual=actual)
    except RuntimeError:
        return _fail(case, "SOL_INTERPRETATION_LEAK", expected=expected, actual=actual)
    if not relations:
        return SOLProjection(
            status="NO_ELIGIBLE_SOL",
            reason_codes=("NO_PUBLIC_SOURCE_BOUND_RELATIONS",),
            source_artifact_sha256=actual,
            expected_artifact_sha256=expected,
            public_case_sha256=case.proposer_view_sha256,
        )
    return SOLProjection(
        status="AVAILABLE",
        reason_codes=(),
        source_artifact_sha256=actual,
        expected_artifact_sha256=expected,
        public_case_sha256=case.proposer_view_sha256,
        relations=relations,
    )
