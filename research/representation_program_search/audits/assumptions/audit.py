"""Deterministic, fail-closed ScientificAssumptionContract audit.

The implementation does not edit candidate dossiers.  It inventories every
contract declaration, applies the source-backed classifications frozen in
``REQUIRED_PREDICATES.json``, and emits a canonical JSON audit artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


AUDIT_DIR = Path(__file__).resolve().parent
RESEARCH_DIR = AUDIT_DIR.parents[1]
CASE_ROOT = RESEARCH_DIR / "cases"
SPEC_PATH = AUDIT_DIR / "REQUIRED_PREDICATES.json"
ARTIFACT_PATH = AUDIT_DIR / "AUDIT.json"

CASE_CLUSTERS = ("matrix", "thermal", "response", "tensor", "diffphys")
PREDICATE_FIELDS = (
    "nonzero_conditions",
    "positivity_conditions",
    "analytic_domains",
    "limit_domains",
    "derived_conditions",
)
PREDICATE_STATUSES = ("DECLARED", "DERIVED", "NOT_DECLARED")


class AuditInputError(ValueError):
    """Raised when the audit inputs violate the frozen input schema."""


def _canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AuditInputError(f"{path}: top-level JSON must be an object")
    return value


def case_paths(case_root: Path = CASE_ROOT) -> list[Path]:
    """Return every non-index JSON dossier in the five in-scope clusters."""

    paths: list[Path] = []
    for cluster in CASE_CLUSTERS:
        cluster_dir = case_root / cluster
        if not cluster_dir.is_dir():
            raise AuditInputError(f"missing case cluster: {cluster_dir}")
        paths.extend(
            path
            for path in sorted(cluster_dir.glob("*.json"))
            if path.name != "index.json"
        )
    return paths


def _explicit_contract_records(
    case_id: str,
    contract: dict[str, Any],
    reclassifications: dict[tuple[str, str, int], dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    symbols = contract.get("symbol_assumptions")
    if not isinstance(symbols, dict):
        raise AuditInputError(f"{case_id}: symbol_assumptions must be an object")
    for symbol, assumptions in sorted(symbols.items()):
        records.append(
            {
                "predicate_id": f"symbol_assumptions:{symbol}",
                "category": "symbol_assumptions",
                "statement": f"{symbol}: {json.dumps(assumptions, sort_keys=True)}",
                "dossier_status": "DECLARED",
                "audit_status": "DECLARED",
                "origin": "CONTRACT_EXPLICIT",
                "source": "ScientificAssumptionContract.symbol_assumptions",
            }
        )

    function_domains = contract.get("function_domains")
    if not isinstance(function_domains, dict):
        raise AuditInputError(f"{case_id}: function_domains must be an object")
    for function_name, statement in sorted(function_domains.items()):
        records.append(
            {
                "predicate_id": f"function_domains:{function_name}",
                "category": "function_domains",
                "statement": statement,
                "dossier_status": "DECLARED",
                "audit_status": "DECLARED",
                "origin": "CONTRACT_EXPLICIT",
                "source": "ScientificAssumptionContract.function_domains",
            }
        )

    for index, function_name in enumerate(contract.get("real_valued_functions") or []):
        records.append(
            {
                "predicate_id": f"real_valued_functions:{index}",
                "category": "real_valued_functions",
                "statement": f"{function_name} is real-valued on its declared domain.",
                "dossier_status": "DECLARED",
                "audit_status": "DECLARED",
                "origin": "CONTRACT_EXPLICIT",
                "source": "ScientificAssumptionContract.real_valued_functions",
            }
        )

    for index, statement in enumerate(contract.get("branch_conventions") or []):
        records.append(
            {
                "predicate_id": f"branch_conventions:{index}",
                "category": "branch_conventions",
                "statement": statement,
                "dossier_status": "DECLARED",
                "audit_status": "DECLARED",
                "origin": "CONTRACT_EXPLICIT",
                "source": "ScientificAssumptionContract.branch_conventions",
            }
        )

    for field in PREDICATE_FIELDS:
        values = contract.get(field) or []
        if not isinstance(values, list):
            raise AuditInputError(f"{case_id}: {field} must be a list")
        for index, predicate in enumerate(values):
            if not isinstance(predicate, dict):
                raise AuditInputError(f"{case_id}: {field}[{index}] must be an object")
            dossier_status = predicate.get("label", "NOT_DECLARED")
            if dossier_status not in PREDICATE_STATUSES:
                raise AuditInputError(
                    f"{case_id}: {field}[{index}] has invalid label {dossier_status!r}"
                )
            statement = predicate.get("statement")
            source = predicate.get("source")
            if not isinstance(statement, str) or not statement.strip():
                raise AuditInputError(f"{case_id}: {field}[{index}] lacks a statement")
            if not isinstance(source, str) or not source.strip():
                raise AuditInputError(f"{case_id}: {field}[{index}] lacks a source")

            override = reclassifications.get((case_id, field, index))
            audit_status = override["audit_status"] if override else dossier_status
            record = {
                "predicate_id": f"{field}:{index}",
                "category": field,
                "statement": statement,
                "dossier_status": dossier_status,
                "audit_status": audit_status,
                "origin": "CONTRACT_EXPLICIT",
                "source": source,
            }
            if override:
                record["audit_reason"] = override["reason"]
                record["source_basis"] = override["source_basis"]
            records.append(record)

    return records


def _load_spec(spec_path: Path) -> dict[str, Any]:
    spec = _load_json(spec_path)
    if spec.get("audit_version") != "rps-assumption-audit-v1":
        raise AuditInputError("unexpected audit_version")
    return spec


def _reclassification_map(spec: dict[str, Any]) -> dict[tuple[str, str, int], dict[str, Any]]:
    result: dict[tuple[str, str, int], dict[str, Any]] = {}
    for item in spec.get("reclassifications") or []:
        status = item.get("audit_status")
        if status not in PREDICATE_STATUSES:
            raise AuditInputError(f"invalid reclassification status: {status!r}")
        key = (item["case_id"], item["field"], item["index"])
        if key in result:
            raise AuditInputError(f"duplicate reclassification: {key}")
        result[key] = item
    return result


def _additional_records(case_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    by_case = spec.get("required_predicates") or {}
    for finding in by_case.get(case_id, []):
        finding_id = finding.get("finding_id")
        if not isinstance(finding_id, str) or not finding_id:
            raise AuditInputError(f"{case_id}: additional predicate lacks finding_id")
        if finding_id in seen:
            raise AuditInputError(f"{case_id}: duplicate finding_id {finding_id}")
        seen.add(finding_id)
        status = finding.get("audit_status")
        if status not in PREDICATE_STATUSES:
            raise AuditInputError(f"{case_id}/{finding_id}: invalid audit_status")
        result.append(
            {
                "predicate_id": f"auditor_required:{finding_id}",
                "category": finding["category"],
                "statement": finding["statement"],
                "dossier_status": "ABSENT",
                "audit_status": status,
                "origin": "AUDITOR_REQUIRED_GAP",
                "audit_reason": finding["reason"],
                "source_basis": finding["source_basis"],
            }
        )
    return result


def _validate_spec_case_ids(spec: dict[str, Any], case_ids: set[str]) -> None:
    referenced = set((spec.get("required_predicates") or {}).keys())
    referenced.update(item["case_id"] for item in spec.get("reclassifications") or [])
    unknown = sorted(referenced - case_ids)
    if unknown:
        raise AuditInputError(f"audit spec references unknown cases: {unknown}")


def _status_counts(records: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts = {status: 0 for status in PREDICATE_STATUSES}
    for record in records:
        counts[record["audit_status"]] += 1
    return counts


def build_audit(
    case_root: Path = CASE_ROOT,
    spec_path: Path = SPEC_PATH,
) -> dict[str, Any]:
    """Build the canonical assumption audit from immutable dossier inputs."""

    spec = _load_spec(spec_path)
    paths = case_paths(case_root)
    raw_cases = [(path, _load_json(path)) for path in paths]
    case_ids = {data.get("case_id") for _, data in raw_cases}
    if None in case_ids or len(case_ids) != len(raw_cases):
        raise AuditInputError("case_id values must be present and unique")
    _validate_spec_case_ids(spec, case_ids)
    reclassifications = _reclassification_map(spec)

    relative_base = case_root.parents[2]
    cases: list[dict[str, Any]] = []
    consumed_reclassifications: set[tuple[str, str, int]] = set()
    input_hashes: dict[str, str] = {}
    for path, data in raw_cases:
        case_id = data["case_id"]
        if path.stem != case_id:
            raise AuditInputError(f"{path}: filename does not match case_id {case_id}")
        contract = data.get("assumption_contract")
        if not isinstance(contract, dict):
            raise AuditInputError(f"{case_id}: missing ScientificAssumptionContract")
        provenance = contract.get("source_provenance")
        if not isinstance(provenance, list) or not provenance:
            raise AuditInputError(f"{case_id}: missing source_provenance")

        records = _explicit_contract_records(case_id, contract, reclassifications)
        records.extend(_additional_records(case_id, spec))
        for key in reclassifications:
            if key[0] == case_id and any(
                record["predicate_id"] == f"{key[1]}:{key[2]}" for record in records
            ):
                consumed_reclassifications.add(key)

        counts = _status_counts(records)
        outcome = (
            "PROBLEM_UNDERSPECIFIED" if counts["NOT_DECLARED"] else "ASSUMPTION_COMPLETE"
        )
        path_bytes = path.read_bytes()
        relative_path = path.relative_to(relative_base).as_posix()
        input_hashes[relative_path] = _sha256_bytes(path_bytes)
        cases.append(
            {
                "case_id": case_id,
                "cluster": path.parent.name,
                "dossier_path": relative_path,
                "dossier_sha256": input_hashes[relative_path],
                "dossier_rejected": bool(data.get("rejected", False)),
                "audit_outcome": outcome,
                "downstream_gate": (
                    "EXCLUDE_UNTIL_ASSUMPTIONS_DECLARED"
                    if outcome == "PROBLEM_UNDERSPECIFIED"
                    else "ELIGIBLE_FOR_SEPARATE_ADMISSION_AUDIT"
                ),
                "predicate_counts": counts,
                "predicates": records,
                "source_provenance": provenance,
            }
        )

    unused = sorted(set(reclassifications) - consumed_reclassifications)
    if unused:
        raise AuditInputError(f"unused reclassifications: {unused}")

    cases.sort(key=lambda item: (CASE_CLUSTERS.index(item["cluster"]), item["case_id"]))
    underspecified = [
        case["case_id"]
        for case in cases
        if case["audit_outcome"] == "PROBLEM_UNDERSPECIFIED"
    ]
    total_counts = _status_counts(
        record for case in cases for record in case["predicates"]
    )
    cluster_counts = {
        cluster: sum(case["cluster"] == cluster for case in cases)
        for cluster in CASE_CLUSTERS
    }
    manifest_sha256 = _sha256_bytes(_canonical_json_bytes(input_hashes))
    return {
        "schema": "ScientificAssumptionContractAuditV1",
        "audit_version": spec["audit_version"],
        "scope": {
            "clusters": list(CASE_CLUSTERS),
            "skeptic_cases_included": False,
            "case_count": len(cases),
            "cluster_counts": cluster_counts,
        },
        "semantics": {
            "statuses": list(PREDICATE_STATUSES),
            "admission_complete": spec["policy"]["admission_complete"],
            "fail_closed": spec["policy"]["fail_closed"],
            "no_repair": spec["policy"]["no_repair"],
            "packaging_gap_is_not_assumption_success": True,
        },
        "input_manifest_sha256": manifest_sha256,
        "summary": {
            "case_count": len(cases),
            "assumption_complete_count": len(cases) - len(underspecified),
            "problem_underspecified_count": len(underspecified),
            "problem_underspecified_case_ids": underspecified,
            "predicate_counts": total_counts,
        },
        "cases": cases,
    }


def render_artifact(audit: dict[str, Any]) -> bytes:
    return _canonical_json_bytes(audit)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write canonical AUDIT.json")
    mode.add_argument("--check", action="store_true", help="verify committed AUDIT.json")
    args = parser.parse_args(argv)

    rendered = render_artifact(build_audit())
    if args.write:
        ARTIFACT_PATH.write_bytes(rendered)
        return 0
    if not ARTIFACT_PATH.is_file() or ARTIFACT_PATH.read_bytes() != rendered:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
