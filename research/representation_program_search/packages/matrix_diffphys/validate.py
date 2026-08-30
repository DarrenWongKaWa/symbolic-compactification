"""Fail-closed validator for matrix/diffphys RPSCasePackageV1 artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = ROOT.parents[3]
PACKAGE_SCHEMA = "RPSCasePackageV1"
CATALOG_SCHEMA = "RPSSourceCatalogV1"
PROPOSER_SCHEMA = "RPSProposerViewV1"
PROGRAM_SCHEMA = "RepresentationProgramV1"
OBLIGATION_SCHEMA = "RPSObligationSetV1"
SOURCE_SCHEMA = "RPSSourceManifestV1"
DEPTHS = {f"R{i}" for i in range(9)}
PACKAGE_STATUSES = {"PACKAGE_READY", "PACKAGE_INCOMPLETE", "PROOF_REQUIRED"}
LOWERING_SCOPE = "FIXED_SCIENTIFIC_INSTANCE"
FORBIDDEN_PROPOSER_KEYS = {
    "audited_depth",
    "gold",
    "gold_program",
    "hidden_role",
    "member_role",
    "operator_sequence",
    "reference",
    "reference_program",
    "target_representation",
}
FORBIDDEN_PROPOSER_VALUES = re.compile(
    r"\b(?:newton|hermite|recurrence|repeated[-_ ]?node|multiplicity|"
    r"confluent|coincident[-_ ]?site|target[-_ ]?(?:form|representation))\b",
    re.IGNORECASE,
)
CONTRACT_FIELDS = {
    "analytic_domains",
    "branch_conventions",
    "derived_conditions",
    "function_domains",
    "limit_domains",
    "nonzero_conditions",
    "positivity_conditions",
    "real_valued_functions",
    "source_provenance",
    "symbol_assumptions",
}


class PackageValidationError(ValueError):
    """A package violates the frozen packaging contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_program_hash(program: dict[str, Any]) -> str:
    payload = dict(program)
    payload.pop("program_id", None)
    return sha256_bytes(canonical_json_bytes(payload))


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageValidationError(f"{path}: unreadable JSON") from exc
    if not isinstance(value, dict):
        raise PackageValidationError(f"{path}: JSON root must be an object")
    return value


def _assert_canonical(path: Path, value: dict[str, Any]) -> None:
    if path.read_bytes() != canonical_json_bytes(value):
        raise PackageValidationError(f"{path}: JSON is not canonical sorted JSON")


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key).casefold())
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def _validate_contract(path: Path, contract: dict[str, Any]) -> None:
    if set(contract) != CONTRACT_FIELDS:
        raise PackageValidationError(f"{path}: not an exact ScientificAssumptionContract")
    provenance = contract["source_provenance"]
    if not isinstance(provenance, list) or not provenance:
        raise PackageValidationError(f"{path}: source_provenance is required")
    for field in (
        "analytic_domains",
        "derived_conditions",
        "limit_domains",
        "nonzero_conditions",
        "positivity_conditions",
    ):
        if not isinstance(contract[field], list):
            raise PackageValidationError(f"{path}: {field} must be a list")
        for predicate in contract[field]:
            if not isinstance(predicate, dict):
                raise PackageValidationError(f"{path}: malformed {field} predicate")
            if predicate.get("label") not in {"DECLARED", "DERIVED"}:
                raise PackageValidationError(f"{path}: fail-closed predicate label")
            if not predicate.get("statement") or not predicate.get("source"):
                raise PackageValidationError(f"{path}: unsourced {field} predicate")


def package_dirs(root: Path = ROOT) -> list[Path]:
    return sorted(path for path in root.iterdir() if path.is_dir() and (path / "package.json").is_file())


def validate_package(package_dir: Path) -> dict[str, Any]:
    manifest_path = package_dir / "package.json"
    manifest = _read_json(manifest_path)
    _assert_canonical(manifest_path, manifest)
    if manifest.get("schema_version") != PACKAGE_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong package schema")
    if manifest.get("package_id") != package_dir.name:
        raise PackageValidationError(f"{package_dir}: package_id/path mismatch")
    if manifest.get("audited_depth") not in DEPTHS:
        raise PackageValidationError(f"{package_dir}: invalid audited_depth")
    if manifest.get("package_status") not in PACKAGE_STATUSES:
        raise PackageValidationError(f"{package_dir}: invalid package_status")
    if manifest.get("lowering_scope") != LOWERING_SCOPE:
        raise PackageValidationError(f"{package_dir}: lowering_scope must use the frozen enum")

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise PackageValidationError(f"{package_dir}: artifact hashes are required")
    declared: dict[str, str] = {}
    for row in artifacts:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            raise PackageValidationError(f"{package_dir}: malformed artifact entry")
        rel = row["path"]
        path = package_dir / rel
        if Path(rel).is_absolute() or ".." in Path(rel).parts or rel == "package.json":
            raise PackageValidationError(f"{package_dir}: unsafe artifact path {rel!r}")
        if rel in declared or not path.is_file():
            raise PackageValidationError(f"{package_dir}: duplicate/missing artifact {rel!r}")
        digest = sha256_bytes(path.read_bytes())
        if digest != row["sha256"]:
            raise PackageValidationError(f"{package_dir}: hash mismatch for {rel}")
        declared[rel] = digest
    actual = {
        path.relative_to(package_dir).as_posix()
        for path in package_dir.rglob("*")
        if path.is_file() and path.name != "package.json" and "__pycache__" not in path.parts
    }
    if set(declared) != actual:
        raise PackageValidationError(f"{package_dir}: artifact inventory is not exhaustive")

    catalog_path = package_dir / "source_catalog.json"
    catalog = _read_json(catalog_path)
    _assert_canonical(catalog_path, catalog)
    if catalog.get("schema_version") != CATALOG_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong catalog schema")
    members = catalog.get("members")
    if not isinstance(members, list) or len(members) < 2:
        raise PackageValidationError(f"{package_dir}: at least two source members required")
    member_ids: set[str] = set()
    member_paths: dict[str, str] = {}
    for member in members:
        if set(member) != {"member_id", "path", "sha256"}:
            raise PackageValidationError(f"{package_dir}: source catalog leaks metadata")
        member_id = member["member_id"]
        path = package_dir / member["path"]
        if member_id in member_ids or not path.is_file():
            raise PackageValidationError(f"{package_dir}: duplicate/missing member")
        if sha256_bytes(path.read_bytes()) != member["sha256"]:
            raise PackageValidationError(f"{package_dir}: member hash mismatch")
        member_ids.add(member_id)
        member_paths[member_id] = member["path"]

    assumptions_path = package_dir / "assumptions.json"
    assumptions = _read_json(assumptions_path)
    _assert_canonical(assumptions_path, assumptions)
    _validate_contract(assumptions_path, assumptions)

    proposer_path = package_dir / "proposer_view.json"
    proposer = _read_json(proposer_path)
    _assert_canonical(proposer_path, proposer)
    if set(proposer) != {"assumptions", "case_id", "schema_version", "source_catalog"}:
        raise PackageValidationError(f"{package_dir}: proposer view exceeds source+assumption projection")
    if proposer.get("schema_version") != PROPOSER_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong proposer schema")
    if proposer.get("case_id") != catalog.get("case_id"):
        raise PackageValidationError(f"{package_dir}: proposer/catalog opaque id mismatch")
    if proposer["source_catalog"] != catalog or proposer["assumptions"] != assumptions:
        raise PackageValidationError(f"{package_dir}: proposer projection is not exact")
    leaked = _all_keys(proposer) & FORBIDDEN_PROPOSER_KEYS
    if leaked:
        raise PackageValidationError(f"{package_dir}: proposer key leakage {sorted(leaked)}")
    value_match = FORBIDDEN_PROPOSER_VALUES.search(json.dumps(proposer, sort_keys=True))
    if value_match:
        raise PackageValidationError(
            f"{package_dir}: proposer value leakage {value_match.group(0)!r}")

    program_path = package_dir / "reference" / "program.json"
    program = _read_json(program_path)
    _assert_canonical(program_path, program)
    if program.get("schema_version") != PROGRAM_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong program schema")
    if program.get("program_id") != canonical_program_hash(program):
        raise PackageValidationError(f"{package_dir}: noncanonical program_id")
    assignments = program.get("member_assignments")
    if not isinstance(assignments, dict) or set(assignments) != member_ids:
        raise PackageValidationError(f"{package_dir}: member assignment coverage mismatch")
    node_structures = program.get("node_structures")
    if not isinstance(node_structures, list):
        raise PackageValidationError(f"{package_dir}: node structures missing")
    node_ids = {
        row.get("node_id")
        for row in node_structures
        if isinstance(row, dict) and isinstance(row.get("node_id"), str)
    }
    for operator in program.get("operators", []):
        if operator.get("operator") == "HERMITE_DD":
            node_ref = operator.get("arguments", {}).get("nodes")
            if not isinstance(node_ref, str) or node_ref not in node_ids:
                raise PackageValidationError(
                    f"{package_dir}: HERMITE_DD must reference an explicit NODES object")

    obligation_path = package_dir / "reference" / "obligations.json"
    obligation_set = _read_json(obligation_path)
    _assert_canonical(obligation_path, obligation_set)
    if obligation_set.get("schema_version") != OBLIGATION_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong obligation schema")
    obligations = obligation_set.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        raise PackageValidationError(f"{package_dir}: required obligations missing")
    verdict_counts = {"ZERO": 0, "NONZERO": 0, "UNKNOWN": 0}
    obligation_by_id: dict[str, dict[str, Any]] = {}
    for obligation in obligations:
        if obligation.get("required") is not True:
            raise PackageValidationError(f"{package_dir}: optional obligation in required set")
        verdict = obligation.get("verdict")
        if verdict not in verdict_counts:
            raise PackageValidationError(f"{package_dir}: invalid obligation verdict")
        verdict_counts[verdict] += 1
        obligation_id = obligation.get("obligation_id")
        if not isinstance(obligation_id, str) or obligation_id in obligation_by_id:
            raise PackageValidationError(f"{package_dir}: duplicate/missing obligation id")
        obligation_by_id[obligation_id] = obligation
        current = package_dir / obligation["current_path"]
        candidate = package_dir / obligation["candidate_path"]
        if sha256_bytes(current.read_bytes()) != obligation["current_sha256"]:
            raise PackageValidationError(f"{package_dir}: current hash mismatch")
        if sha256_bytes(candidate.read_bytes()) != obligation["candidate_sha256"]:
            raise PackageValidationError(f"{package_dir}: candidate hash mismatch")
        run_dir = package_dir / obligation["session_path"]
        step_path = run_dir / "steps" / "step_001.json"
        step = _read_json(step_path)
        if step.get("verdict") != verdict:
            raise PackageValidationError(f"{package_dir}: obligation/session verdict mismatch")
        if step.get("current_hash") != obligation["current_sha256"]:
            raise PackageValidationError(f"{package_dir}: obligation/session current mismatch")
        if step.get("candidate_hash") != obligation["candidate_sha256"]:
            raise PackageValidationError(f"{package_dir}: obligation/session candidate mismatch")
        if verdict == "ZERO" and (step.get("status") != "CERTIFIED" or step.get("proof_status") != "PROVEN"):
            raise PackageValidationError(f"{package_dir}: ZERO lacks certified/proven status")
        if verdict == "UNKNOWN" and step.get("proof_status") != "PROOF_REQUIRED":
            raise PackageValidationError(f"{package_dir}: UNKNOWN lacks proof-required status")
    if set(program.get("obligations", [])) != set(obligation_by_id):
        raise PackageValidationError(f"{package_dir}: program/required obligation mismatch")

    for member_id, assignment in assignments.items():
        if not isinstance(assignment, dict) or not isinstance(assignment.get("reconstruction"), str):
            raise PackageValidationError(f"{package_dir}: malformed member assignment")
        member_path = member_paths[member_id]
        member_bytes = (package_dir / member_path).read_bytes()
        reconstruction_bytes = (assignment["reconstruction"] + "\n").encode("utf-8")
        if reconstruction_bytes == member_bytes:
            if assignment.get("verification") != "BYTE_IDENTICAL_EXACT":
                raise PackageValidationError(
                    f"{package_dir}: byte-identical {member_id} lacks exact tag")
            continue
        obligation_id = assignment.get("obligation_id")
        obligation = obligation_by_id.get(obligation_id)
        if obligation is None or obligation.get("current_path") != member_path:
            raise PackageValidationError(
                f"{package_dir}: non-identical {member_id} lacks required obligation")
        candidate = package_dir / obligation["candidate_path"]
        if candidate.read_bytes() != reconstruction_bytes:
            raise PackageValidationError(
                f"{package_dir}: {member_id} obligation does not verify its reconstruction")
    if verdict_counts != manifest.get("verdict_counts"):
        raise PackageValidationError(f"{package_dir}: verdict count mismatch")
    if manifest["package_status"] == "PACKAGE_READY" and (
        verdict_counts["NONZERO"] or verdict_counts["UNKNOWN"]
    ):
        raise PackageValidationError(f"{package_dir}: ready package has non-ZERO evidence")
    if manifest["package_status"] == "PROOF_REQUIRED" and (
        verdict_counts["UNKNOWN"] == 0 or verdict_counts["NONZERO"] != 0
    ):
        raise PackageValidationError(f"{package_dir}: invalid proof-required status")

    attempt_counts = dict(verdict_counts)
    non_success = obligation_set.get("non_success_evidence", [])
    if not isinstance(non_success, list):
        raise PackageValidationError(f"{package_dir}: malformed non-success evidence")
    for attempt in non_success:
        if attempt.get("required") is not False:
            raise PackageValidationError(f"{package_dir}: diagnostic attempt marked required")
        verdict = attempt.get("verdict")
        if verdict not in {"NONZERO", "UNKNOWN"}:
            raise PackageValidationError(f"{package_dir}: non-success evidence is not fail-closed")
        if not attempt.get("failure_class"):
            raise PackageValidationError(f"{package_dir}: non-success failure class missing")
        current = package_dir / attempt["current_path"]
        candidate = package_dir / attempt["candidate_path"]
        if sha256_bytes(current.read_bytes()) != attempt["current_sha256"]:
            raise PackageValidationError(f"{package_dir}: diagnostic current hash mismatch")
        if sha256_bytes(candidate.read_bytes()) != attempt["candidate_sha256"]:
            raise PackageValidationError(f"{package_dir}: diagnostic candidate hash mismatch")
        step = _read_json(package_dir / attempt["session_path"] / "steps" / "step_001.json")
        if step.get("verdict") != verdict:
            raise PackageValidationError(f"{package_dir}: diagnostic/session verdict mismatch")
        attempt_counts[verdict] += 1
    diagnostics = obligation_set.get("diagnostic_evidence", [])
    if not isinstance(diagnostics, list):
        raise PackageValidationError(f"{package_dir}: malformed diagnostic evidence")
    for attempt in diagnostics:
        verdict = attempt.get("verdict")
        if verdict not in attempt_counts:
            raise PackageValidationError(f"{package_dir}: invalid diagnostic verdict")
        if attempt.get("eligibility") != "INELIGIBLE_RESTRICTED_REPLAY":
            raise PackageValidationError(f"{package_dir}: diagnostic eligibility missing")
        if not attempt.get("restriction"):
            raise PackageValidationError(f"{package_dir}: diagnostic restriction missing")
        current = package_dir / attempt["current_path"]
        candidate = package_dir / attempt["candidate_path"]
        if sha256_bytes(current.read_bytes()) != attempt["current_sha256"]:
            raise PackageValidationError(f"{package_dir}: diagnostic current hash mismatch")
        if sha256_bytes(candidate.read_bytes()) != attempt["candidate_sha256"]:
            raise PackageValidationError(f"{package_dir}: diagnostic candidate hash mismatch")
        step = _read_json(package_dir / attempt["session_path"] / "steps" / "step_001.json")
        if step.get("verdict") != verdict:
            raise PackageValidationError(f"{package_dir}: diagnostic/session verdict mismatch")
        attempt_counts[verdict] += 1
    if attempt_counts != manifest.get("attempt_verdict_counts"):
        raise PackageValidationError(f"{package_dir}: attempt verdict count mismatch")

    source_path = package_dir / "source_manifest.json"
    source_manifest = _read_json(source_path)
    _assert_canonical(source_path, source_manifest)
    if source_manifest.get("schema_version") != SOURCE_SCHEMA:
        raise PackageValidationError(f"{package_dir}: wrong source manifest schema")
    dossier = source_manifest.get("source_dossier")
    if not isinstance(dossier, dict) or set(dossier) != {"case_id", "path", "sha256"}:
        raise PackageValidationError(f"{package_dir}: malformed source dossier binding")
    if dossier["case_id"] != manifest.get("source_dossier_id"):
        raise PackageValidationError(f"{package_dir}: source dossier id mismatch")
    dossier_path = REPOSITORY_ROOT / dossier["path"]
    if not dossier_path.is_file() or sha256_bytes(dossier_path.read_bytes()) != dossier["sha256"]:
        raise PackageValidationError(f"{package_dir}: source dossier hash mismatch")
    sources = source_manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise PackageValidationError(f"{package_dir}: primary sources required")
    for source in sources:
        if source.get("source_class") != "PRIMARY_LITERATURE" or not source.get("equation_locator"):
            raise PackageValidationError(f"{package_dir}: source lacks equation-level primary citation")

    return {
        "package_id": manifest["package_id"],
        "package_status": manifest["package_status"],
        "audited_depth": manifest["audited_depth"],
        "verdict_counts": verdict_counts,
    }


def validate_all(root: Path = ROOT) -> list[dict[str, Any]]:
    packages = package_dirs(root)
    if not 4 <= len(packages) <= 6:
        raise PackageValidationError("matrix/diffphys package count must be in [4, 6]")
    rows = [validate_package(path) for path in packages]
    depths = {row["audited_depth"] for row in rows}
    if not {"R2", "R3", "R4", "R6"}.issubset(depths):
        raise PackageValidationError("matrix/diffphys set must cover R2/R3/R4/R6")
    return rows


def main() -> int:
    rows = validate_all()
    print(json.dumps({"packages": rows, "status": "VALID"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
