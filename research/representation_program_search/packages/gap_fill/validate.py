"""Fail-closed validation for the candidate-only gap-fill packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research.representation_program_search.program_ir import (
    compile_program,
    load_case_package,
)


ROOT = Path(__file__).resolve().parent
PACKAGE_POLICY = {
    "gf-cr3bp-2017-eq28": {
        "candidate_status": "CANDIDATE_ONLY_NOT_ADMITTED",
        "proposed_depth": "R2_NEWTON_DD_CANDIDATE",
        "members": 4,
        "operators": {"LINEAR_COMBINATION": 4, "NEWTON_DD": 4},
    },
    "gf-vdw-2013-eq1": {
        "candidate_status": "CANDIDATE_ONLY_DEPTH_REVIEW_REQUIRED",
        "proposed_depth": "R6_MULTI_OPERATOR_MASTER_CANDIDATE",
        "members": 8,
        "operators": {
            "COMPOSE": 1,
            "DERIVATIVE": 4,
            "LINEAR_COMBINATION": 5,
            "SUBSTITUTE": 4,
            "VALUE": 1,
        },
    },
}
PROPOSER_FORBIDDEN_KEYS = {
    "audited_depth",
    "candidate_status",
    "gold",
    "hidden_role",
    "operator",
    "operator_sequence",
    "program",
    "proposed_depth",
    "reference",
    "representation_type",
    "target",
    "verdict",
}
PROPOSER_FORBIDDEN_VALUES = {
    "newton_dd",
    "hermite_dd",
    "create_latent",
    "add_derivative",
    "master_member",
    "gold_member",
}


class GapFillValidationError(ValueError):
    """Stable fail-closed package error."""


def package_dirs(root: Path = ROOT) -> list[Path]:
    return [root / name for name in sorted(PACKAGE_POLICY)]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GapFillValidationError(f"{path}: unreadable JSON") from exc
    if not isinstance(value, dict):
        raise GapFillValidationError(f"{path}: JSON root is not an object")
    return value


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_canonical(path: Path, value: dict[str, Any]) -> None:
    if path.read_bytes() != _canonical_bytes(value):
        raise GapFillValidationError(f"{path}: noncanonical JSON")


def _artifact_paths(package: Path) -> list[Path]:
    return [
        path
        for path in sorted(package.rglob("*"))
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    ]


def _walk_public(value: Any, location: str = "proposer_view") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            folded = str(key).casefold()
            if folded in PROPOSER_FORBIDDEN_KEYS:
                raise GapFillValidationError(f"{location}: forbidden public key {key}")
            _walk_public(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_public(child, f"{location}[{index}]")
    elif isinstance(value, str):
        folded = value.casefold()
        for forbidden in PROPOSER_FORBIDDEN_VALUES:
            if forbidden in folded:
                raise GapFillValidationError(f"{location}: forbidden public target hint")


def _validate_assumptions(package: Path, program: Any) -> None:
    contract = _read_json(package / "assumptions.json")
    _assert_canonical(package / "assumptions.json", contract)
    if contract.get("schema_version") != "ScientificAssumptionContractV1":
        raise GapFillValidationError(f"{package.name}: wrong assumption schema")
    if contract.get("status") != "ASSUMPTION_COMPLETE":
        raise GapFillValidationError(f"{package.name}: assumptions not complete")
    predicates = contract.get("predicates")
    if not isinstance(predicates, list) or not predicates:
        raise GapFillValidationError(f"{package.name}: predicates missing")
    expected: dict[str, str] = {}
    for predicate in predicates:
        if not isinstance(predicate, dict) or set(predicate) != {
            "predicate_id",
            "source",
            "statement",
            "status",
        }:
            raise GapFillValidationError(f"{package.name}: malformed predicate")
        identifier = predicate["predicate_id"]
        status = predicate["status"]
        if not isinstance(identifier, str) or status not in {"DECLARED", "DERIVED"}:
            raise GapFillValidationError(f"{package.name}: inadmissible predicate status")
        if not predicate["source"] or not predicate["statement"] or identifier in expected:
            raise GapFillValidationError(f"{package.name}: incomplete predicate")
        expected[identifier] = status
    if dict(program.assumption_statuses) != expected:
        raise GapFillValidationError(f"{package.name}: program/contract assumption mismatch")
    if set(program.assumptions_used) != set(expected):
        raise GapFillValidationError(f"{package.name}: unused or unbound assumption")


def _validate_sources(package: Path, source_ids: set[str]) -> None:
    manifest_path = package / "source_manifest.json"
    manifest = _read_json(manifest_path)
    _assert_canonical(manifest_path, manifest)
    dossier_link = manifest.get("source_dossier")
    if not isinstance(dossier_link, dict) or set(dossier_link) != {"path", "sha256"}:
        raise GapFillValidationError(f"{package.name}: source dossier link malformed")
    dossier_path = package / str(dossier_link["path"])
    if dossier_path.resolve().parent != (package / "sources").resolve():
        raise GapFillValidationError(f"{package.name}: source dossier path escaped")
    if _sha(dossier_path) != dossier_link["sha256"]:
        raise GapFillValidationError(f"{package.name}: source dossier hash mismatch")
    dossier = _read_json(dossier_path)
    _assert_canonical(dossier_path, dossier)
    if dossier.get("case_id") != package.name or dossier.get("retrieval_date") != "2026-08-30":
        raise GapFillValidationError(f"{package.name}: source dossier identity mismatch")
    sources = dossier.get("sources")
    if not isinstance(sources, list) or not sources:
        raise GapFillValidationError(f"{package.name}: sources missing")
    got_source_ids = {source.get("source_id") for source in sources if isinstance(source, dict)}
    if got_source_ids != source_ids:
        raise GapFillValidationError(f"{package.name}: source id mismatch")
    for source in sources:
        if not all(source.get(key) for key in ("source_id", "source_class", "title", "url", "equation_locator", "equation_claim")):
            raise GapFillValidationError(f"{package.name}: incomplete source provenance")
    claims = dossier.get("source_claims")
    if not isinstance(claims, list) or not claims:
        raise GapFillValidationError(f"{package.name}: source claims missing")
    claim_ids: set[str] = set()
    for claim in claims:
        formula = claim.get("normalized_formula") if isinstance(claim, dict) else None
        if not isinstance(formula, str) or not formula:
            raise GapFillValidationError(f"{package.name}: source formula missing")
        if hashlib.sha256(formula.encode()).hexdigest() != claim.get("normalized_formula_sha256"):
            raise GapFillValidationError(f"{package.name}: source formula hash mismatch")
        if claim.get("source_id") not in source_ids or claim.get("claim_id") in claim_ids:
            raise GapFillValidationError(f"{package.name}: bad source claim link")
        claim_ids.add(claim["claim_id"])
    lowerings = manifest.get("lowering_provenance")
    if not isinstance(lowerings, dict):
        raise GapFillValidationError(f"{package.name}: lowering provenance missing")
    for member_id, lowering in lowerings.items():
        if not isinstance(lowering, dict) or lowering.get("status") not in {"DECLARED", "DERIVED"}:
            raise GapFillValidationError(f"{package.name}: malformed lowering {member_id}")
        linked = lowering.get("source_claim_ids")
        if not isinstance(linked, list) or not linked or not set(linked) <= claim_ids:
            raise GapFillValidationError(f"{package.name}: unbound lowering {member_id}")


def _validate_receipts(package: Path, compilation: Any) -> None:
    obligations_path = package / "reference/obligations.json"
    obligations = _read_json(obligations_path)
    _assert_canonical(obligations_path, obligations)
    rows = obligations.get("obligations")
    if not isinstance(rows, list) or len(rows) != len(compilation.obligations):
        raise GapFillValidationError(f"{package.name}: obligation count mismatch")
    by_id = {item.obligation_id: item for item in compilation.obligations}
    if obligations.get("summary") != {"NONZERO": 0, "UNKNOWN": 0, "ZERO": len(rows)}:
        raise GapFillValidationError(f"{package.name}: verdict summary mismatch")
    for row in rows:
        identifier = row.get("obligation_id")
        if identifier not in by_id or row.get("verdict") != "ZERO":
            raise GapFillValidationError(f"{package.name}: required ZERO absent")
        compiled = by_id[identifier]
        candidate_path = package / row["candidate_path"]
        if _sha(candidate_path) != row["candidate_sha256"]:
            raise GapFillValidationError(f"{package.name}: candidate hash mismatch")
        if candidate_path.read_text(encoding="utf-8").strip() != compiled.candidate_expression:
            raise GapFillValidationError(f"{package.name}: candidate/compiler mismatch")
        if row.get("current_member_id") != compiled.member_id or row.get("current_sha256") != compiled.current_sha256:
            raise GapFillValidationError(f"{package.name}: current/compiler mismatch")
        proposal_path = package / row["proposal_step_path"]
        verification_path = package / row["verification_step_path"]
        if _sha(proposal_path) != row["proposal_step_sha256"] or _sha(verification_path) != row["verification_step_sha256"]:
            raise GapFillValidationError(f"{package.name}: receipt hash mismatch")
        proposal = _read_json(proposal_path)
        verification = _read_json(verification_path)
        if not (
            proposal.get("step") == 1
            and proposal.get("status") == "HYPOTHESIS"
            and proposal.get("proof_status") == "HYPOTHESIS"
            and proposal.get("verdict") == "UNKNOWN"
        ):
            raise GapFillValidationError(f"{package.name}: proposal receipt invalid")
        if not (
            verification.get("step") == 2
            and verification.get("status") == "CERTIFIED"
            and verification.get("proof_status") == "PROVEN"
            and verification.get("verdict") == "ZERO"
            and verification.get("residual") == "0"
        ):
            raise GapFillValidationError(f"{package.name}: verification receipt invalid")
        if proposal.get("candidate_text") != compiled.candidate_expression or verification.get("candidate_text") != compiled.candidate_expression:
            raise GapFillValidationError(f"{package.name}: receipt candidate mismatch")
        if proposal.get("current_hash") != compiled.current_sha256 or verification.get("current_hash") != compiled.current_sha256:
            raise GapFillValidationError(f"{package.name}: receipt current mismatch")
        evidence = verification.get("evidence")
        if not isinstance(evidence, list) or not any(item.get("kind") == "exact_symbolic_zero" for item in evidence if isinstance(item, dict)):
            raise GapFillValidationError(f"{package.name}: exact ZERO evidence absent")


def validate_package(package: Path) -> dict[str, Any]:
    if package.name not in PACKAGE_POLICY:
        raise GapFillValidationError(f"unexpected package {package.name}")
    policy = PACKAGE_POLICY[package.name]
    manifest_path = package / "package.json"
    manifest = _read_json(manifest_path)
    _assert_canonical(manifest_path, manifest)
    for key, expected in {
        "schema_version": "RPSCasePackageV1",
        "package_id": package.name,
        "package_status": "PACKAGE_READY",
        "lowering_scope": "SYMBOLIC_SOURCE_OBJECT",
        "candidate_status": policy["candidate_status"],
        "proposed_depth": policy["proposed_depth"],
    }.items():
        if manifest.get(key) != expected:
            raise GapFillValidationError(f"{package.name}: manifest {key} mismatch")
    recorded = manifest.get("artifact_hashes")
    if not isinstance(recorded, list):
        raise GapFillValidationError(f"{package.name}: artifact hashes missing")
    expected_hashes = {
        path.relative_to(package).as_posix(): _sha(path)
        for path in _artifact_paths(package)
    }
    got_hashes = {row.get("path"): row.get("sha256") for row in recorded if isinstance(row, dict)}
    if got_hashes != expected_hashes or len(got_hashes) != len(recorded):
        raise GapFillValidationError(f"{package.name}: artifact manifest mismatch")
    for path in _artifact_paths(package):
        # Engine-owned session JSON preserves the authoritative field order
        # emitted by v0.3.0; do not rewrite evidence to fit package formatting.
        if path.suffix == ".json" and "verification" not in path.parts:
            _assert_canonical(path, _read_json(path))

    proposer = _read_json(package / "proposer_view.json")
    _walk_public(proposer)
    if set(proposer) != {"assumptions", "package_id", "schema_version", "source_catalog"}:
        raise GapFillValidationError(f"{package.name}: proposer projection widened")

    loaded = load_case_package(package)
    if loaded.schema_deltas:
        raise GapFillValidationError(f"{package.name}: M1 schema deltas {loaded.schema_deltas}")
    compilation = compile_program(loaded.program, loaded.context)
    if compilation.status != "COMPILED" or compilation.failure_codes or compilation.tautological:
        raise GapFillValidationError(f"{package.name}: M1 compile/non-tautology gate failed")
    if loaded.program.declared_program_id is not None:
        raise GapFillValidationError(f"{package.name}: loader unexpectedly retained legacy id")
    raw_program = _read_json(package / "reference/program.json")
    if raw_program.get("program_id") != compilation.program_id:
        raise GapFillValidationError(f"{package.name}: program id mismatch")
    if len(loaded.program.source_members) != policy["members"] or len(compilation.obligations) != policy["members"]:
        raise GapFillValidationError(f"{package.name}: member coverage mismatch")
    operator_counts = dict(sorted(Counter(item.operator for item in loaded.program.operators).items()))
    if operator_counts != policy["operators"]:
        raise GapFillValidationError(f"{package.name}: operator profile mismatch")
    _validate_assumptions(package, loaded.program)
    source_manifest = _read_json(package / "source_manifest.json")
    sources = source_manifest.get("sources", [])
    source_ids = {item.get("source_id") for item in sources if isinstance(item, dict)}
    _validate_sources(package, source_ids)
    if set(source_manifest.get("lowering_provenance", {})) != {item.member_id for item in loaded.program.source_members}:
        raise GapFillValidationError(f"{package.name}: source-member lowering coverage mismatch")
    _validate_receipts(package, compilation)

    if package.name == "gf-cr3bp-2017-eq28":
        if len(loaded.program.latent_objects) != 1 or len(loaded.program.node_structures) != 4:
            raise GapFillValidationError("R2 candidate lost shared latent/node family")
        if any(len(node.nodes) != 2 or len(set(node.nodes)) != 2 for node in loaded.program.node_structures):
            raise GapFillValidationError("R2 candidate contains invalid Newton nodes")
        primitive_loaded = load_case_package(package, grammar_id="G_PRIMITIVE")
        primitive = compile_program(primitive_loaded.program, primitive_loaded.context)
        if primitive.status != "COMPILE_FAILURE" or not any(
            code.startswith("OPERATOR_FORBIDDEN_BY_ABLATION")
            for code in primitive.failure_codes
        ):
            raise GapFillValidationError("R2 named-operator ablation boundary changed")
    else:
        output_use = Counter(dependency for item in loaded.program.operators for dependency in item.inputs)
        if len(loaded.program.latent_objects) != 2 or max(output_use.values(), default=0) < 2:
            raise GapFillValidationError("R6 candidate lacks a branching/reused master graph")
        if len({item.operator for item in loaded.program.operators}) < 5:
            raise GapFillValidationError("R6 candidate lacks multi-operator structure")
        primitive_loaded = load_case_package(package, grammar_id="G_PRIMITIVE")
        primitive = compile_program(primitive_loaded.program, primitive_loaded.context)
        if primitive.status != "COMPILED" or primitive.failure_codes:
            raise GapFillValidationError("R6 candidate no longer compiles compositionally under G_PRIMITIVE")

    return {
        "case_id": package.name,
        "candidate_status": policy["candidate_status"],
        "compiled_obligations": len(compilation.obligations),
        "operator_counts": operator_counts,
        "program_id": compilation.program_id,
        "schema_deltas": [],
        "tautological": False,
        "verdict": "VALID_CANDIDATE_PACKAGE",
    }


def validate_all(root: Path = ROOT) -> dict[str, Any]:
    rows = [validate_package(package) for package in package_dirs(root)]
    return {
        "candidate_count": len(rows),
        "cases": rows,
        "schema_version": "RPSGapFillValidationV1",
        "verdict": "VALID" if len(rows) == len(PACKAGE_POLICY) else "INVALID",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = validate_all()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for row in report["cases"]:
            print(f"{row['case_id']}: {row['verdict']} ({row['compiled_obligations']} ZERO obligations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
