"""Build and validate source-backed thermal RPS case packages.

The builder performs only canonical bookkeeping: program-id hashing,
proposer-view projection, and the package artifact manifest. Scientific
members, assumptions, reference programs, and verifier records are inputs and
are never invented or repaired here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any

from symbolic_compactification import load_expression

from research.representation_program_search.grammar_v1 import (
    GRAMMAR_ID,
    LATENT_FORMS,
    OPERATORS,
)


ROOT = Path(__file__).resolve().parent
PACKAGE_SCHEMA = "RPSCasePackageV1"
PACKAGE_CONFIG = {
    "thermal-09-digamma-newton": {
        "audited_depth": "R2_NEWTON_DD",
        "lowering_scope": "NONE_SYMBOLIC_SOURCE_IDENTITY",
        "package_status": "PROOF_REQUIRED",
        "source_dossier_id": "thermal-09-digamma-recurrence",
    },
    "thermal-09-digamma-newton-z1": {
        "audited_depth": "R0_REPEATED_STRUCTURE",
        "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE_Z_EQ_1",
        "package_status": "PACKAGE_READY",
        "source_dossier_id": "thermal-09-digamma-recurrence",
    },
    "thermal-10-polygamma-order2-recurrence": {
        "audited_depth": "R1_PARAMETER_FAMILY",
        "lowering_scope": "FIXED_ORDER_N_EQ_2_SYMBOLIC_Z",
        "package_status": "PROOF_REQUIRED",
        "source_dossier_id": "thermal-10-polygamma-recurrence",
    },
    "thermal-11-digamma-duplication": {
        "audited_depth": "R1_PARAMETER_FAMILY",
        "lowering_scope": "FIXED_MULTIPLICATION_N_EQ_2_SYMBOLIC_Z",
        "package_status": "PROOF_REQUIRED",
        "source_dossier_id": "thermal-11-gauss-multiplication-psi",
    },
    "thermal-13-alternating-digamma": {
        "audited_depth": "R5_SPECIAL_FUNCTION_REPRESENTATION",
        "lowering_scope": "NONE_SYMBOLIC_SOURCE_IDENTITY",
        "package_status": "PROOF_REQUIRED",
        "source_dossier_id": "thermal-13-alternating-fermi-series",
    },
    "thermal-13-alternating-digamma-z1": {
        "audited_depth": "R5_SPECIAL_FUNCTION_FIXED_INSTANCE",
        "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE_Z_EQ_1",
        "package_status": "PACKAGE_READY",
        "source_dossier_id": "thermal-13-alternating-fermi-series",
    },
}

_PROPOSER_FORBIDDEN = {
    "audited_depth",
    "gold",
    "operator",
    "operator_sequence",
    "package_status",
    "program",
    "reference",
    "role",
    "source_dossier_id",
    "target",
    "verdict",
}


class PackageValidationError(ValueError):
    """Raised when a package violates the fail-closed package contract."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PackageValidationError(f"{path}: unreadable JSON") from exc
    if not isinstance(value, dict):
        raise PackageValidationError(f"{path}: top-level JSON must be an object")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    data = _canonical_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def package_dirs(root: Path = ROOT) -> list[Path]:
    return [root / name for name in sorted(PACKAGE_CONFIG)]


def _artifact_paths(package: Path) -> list[Path]:
    return [
        path
        for path in sorted(package.rglob("*"))
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    ]


def materialize_package(package: Path) -> None:
    config = PACKAGE_CONFIG[package.name]
    program_path = package / "reference/program.json"
    program = _load(program_path)
    unhashed_program = dict(program)
    unhashed_program.pop("program_id", None)
    program["program_id"] = _canonical_hash(unhashed_program)
    _atomic_json(program_path, program)

    catalog_path = package / "source_catalog.json"
    assumptions_path = package / "assumptions.json"
    proposer_view = {
        "assumptions": {
            "path": "assumptions.json",
            "sha256": _file_hash(assumptions_path),
        },
        "package_id": package.name,
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": _load(catalog_path)["members"],
            "path": "source_catalog.json",
            "sha256": _file_hash(catalog_path),
        },
    }
    _atomic_json(package / "proposer_view.json", proposer_view)

    obligations = _load(package / "reference/obligations.json")
    package_manifest = {
        "artifact_hashes": [
            {
                "path": path.relative_to(package).as_posix(),
                "sha256": _file_hash(path),
            }
            for path in _artifact_paths(package)
        ],
        "audited_depth": config["audited_depth"],
        "lowering_scope": config["lowering_scope"],
        "manifest_exclusion": "package.json is excluded because a file cannot contain its own stable hash.",
        "package_id": package.name,
        "package_status": config["package_status"],
        "schema_version": PACKAGE_SCHEMA,
        "source_dossier_id": config["source_dossier_id"],
        "verdict_totals": obligations["summary"],
    }
    _atomic_json(package / "package.json", package_manifest)


def materialize_all(root: Path = ROOT) -> None:
    for package in package_dirs(root):
        materialize_package(package)


def _check_proposer_projection(value: Any, location: str = "proposer_view") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = key.lower()
            if lowered in _PROPOSER_FORBIDDEN:
                raise PackageValidationError(f"{location}: forbidden key {key}")
            _check_proposer_projection(child, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_proposer_projection(child, f"{location}[{index}]")


def validate_package(package: Path) -> dict[str, int]:
    if package.name not in PACKAGE_CONFIG:
        raise PackageValidationError(f"unexpected package directory: {package.name}")
    config = PACKAGE_CONFIG[package.name]
    manifest = _load(package / "package.json")
    for key, expected in {
        "schema_version": PACKAGE_SCHEMA,
        "package_id": package.name,
        **config,
    }.items():
        if manifest.get(key) != expected:
            raise PackageValidationError(f"{package.name}: package.json {key} mismatch")

    recorded = manifest.get("artifact_hashes")
    if not isinstance(recorded, list):
        raise PackageValidationError(f"{package.name}: artifact_hashes must be a list")
    expected_hashes = {
        path.relative_to(package).as_posix(): _file_hash(path)
        for path in _artifact_paths(package)
    }
    got_hashes = {entry.get("path"): entry.get("sha256") for entry in recorded}
    if got_hashes != expected_hashes or len(got_hashes) != len(recorded):
        raise PackageValidationError(f"{package.name}: artifact manifest mismatch")

    namespace = _load(package / "symbols.json")
    symbols = namespace.get("symbols")
    functions = namespace.get("functions") or None
    if not isinstance(symbols, list):
        raise PackageValidationError(f"{package.name}: symbols.json lacks symbols")

    catalog = _load(package / "source_catalog.json")
    members = catalog.get("members")
    if not isinstance(members, list) or len(members) < 2:
        raise PackageValidationError(f"{package.name}: at least two source members required")
    member_by_id: dict[str, dict[str, Any]] = {}
    for member in members:
        member_id = member.get("member_id")
        if not isinstance(member_id, str) or member_id in member_by_id:
            raise PackageValidationError(f"{package.name}: duplicate/invalid member id")
        path = package / str(member.get("path"))
        if path.parent != package / "members" or path.suffix != ".txt":
            raise PackageValidationError(f"{package.name}: member path escapes members/")
        if _file_hash(path) != member.get("sha256"):
            raise PackageValidationError(f"{package.name}/{member_id}: member hash mismatch")
        load_expression(str(path), symbols, functions=functions)
        member_by_id[member_id] = member

    assumptions = _load(package / "assumptions.json")
    if assumptions.get("status") != "ASSUMPTION_COMPLETE":
        raise PackageValidationError(f"{package.name}: assumptions are not complete")
    predicates = assumptions.get("predicates")
    if not isinstance(predicates, list) or not predicates:
        raise PackageValidationError(f"{package.name}: assumptions lack predicates")
    if any(predicate.get("status") not in {"DECLARED", "DERIVED"} for predicate in predicates):
        raise PackageValidationError(f"{package.name}: undeclared assumption predicate")

    source_manifest = _load(package / "source_manifest.json")
    dossier = source_manifest.get("source_dossier", {})
    dossier_path = (package / str(dossier.get("path"))).resolve()
    if _file_hash(dossier_path) != dossier.get("sha256"):
        raise PackageValidationError(f"{package.name}: dossier hash mismatch")
    if config["source_dossier_id"] not in dossier_path.name:
        raise PackageValidationError(f"{package.name}: wrong source dossier")
    for source in source_manifest.get("sources", []):
        if not str(source.get("formula_url", "")).startswith("https://dlmf.nist.gov/"):
            raise PackageValidationError(f"{package.name}: non-authoritative source")
        tex = source.get("tex")
        if not isinstance(tex, str) or hashlib.sha256(tex.encode()).hexdigest() != source.get("tex_sha256"):
            raise PackageValidationError(f"{package.name}: source TeX hash mismatch")

    proposer_view = _load(package / "proposer_view.json")
    if set(proposer_view) != {"assumptions", "package_id", "schema_version", "source_catalog"}:
        raise PackageValidationError(f"{package.name}: proposer projection has extra fields")
    _check_proposer_projection(proposer_view)
    if proposer_view["assumptions"]["sha256"] != _file_hash(package / "assumptions.json"):
        raise PackageValidationError(f"{package.name}: proposer assumptions hash mismatch")
    if proposer_view["source_catalog"]["sha256"] != _file_hash(package / "source_catalog.json"):
        raise PackageValidationError(f"{package.name}: proposer catalog hash mismatch")

    program = _load(package / "reference/program.json")
    unhashed_program = dict(program)
    program_id = unhashed_program.pop("program_id", None)
    if program_id != _canonical_hash(unhashed_program):
        raise PackageValidationError(f"{package.name}: program_id mismatch")
    if program.get("grammar_version") != GRAMMAR_ID:
        raise PackageValidationError(f"{package.name}: wrong grammar")
    latents = program.get("latent_objects")
    if not isinstance(latents, list) or not latents:
        raise PackageValidationError(f"{package.name}: no latent object")
    if any(latent.get("form") not in LATENT_FORMS for latent in latents):
        raise PackageValidationError(f"{package.name}: invalid latent form")
    operators = program.get("operators")
    if not isinstance(operators, list) or not operators:
        raise PackageValidationError(f"{package.name}: no operators")
    if any(operator.get("operator") not in OPERATORS for operator in operators):
        raise PackageValidationError(f"{package.name}: illegal operator")
    assignments = program.get("member_assignments")
    if not isinstance(assignments, dict) or set(assignments) != set(member_by_id):
        raise PackageValidationError(f"{package.name}: incomplete member assignments")
    if program.get("unexplained_members") != []:
        raise PackageValidationError(f"{package.name}: unexplained members remain")
    if program.get("representation_depth") != config["audited_depth"]:
        raise PackageValidationError(f"{package.name}: audited depth mismatch")
    if package.name.startswith("thermal-10-"):
        if any(operator.get("operator") == "HERMITE_DD" for operator in operators):
            raise PackageValidationError(f"{package.name}: recurrence mislabeled Hermite")
        if program.get("node_structures"):
            raise PackageValidationError(f"{package.name}: recurrence invented repeated nodes")

    obligations_doc = _load(package / "reference/obligations.json")
    obligations = obligations_doc.get("obligations")
    if not isinstance(obligations, list) or not obligations:
        raise PackageValidationError(f"{package.name}: no obligations")
    verdicts: Counter[str] = Counter()
    obligation_ids: set[str] = set()
    for obligation in obligations:
        obligation_id = obligation.get("obligation_id")
        if not isinstance(obligation_id, str) or obligation_id in obligation_ids:
            raise PackageValidationError(f"{package.name}: duplicate obligation")
        obligation_ids.add(obligation_id)
        member = member_by_id.get(obligation.get("current_member_id"))
        if member is None:
            raise PackageValidationError(f"{package.name}/{obligation_id}: unknown source member")
        candidate = package / str(obligation.get("candidate_path"))
        load_expression(str(candidate), symbols, functions=functions)
        step_path = package / str(obligation.get("step_path"))
        step = _load(step_path)
        if step.get("current_hash") != member["sha256"]:
            raise PackageValidationError(f"{package.name}/{obligation_id}: current hash mismatch")
        if step.get("candidate_hash") != _file_hash(candidate):
            raise PackageValidationError(f"{package.name}/{obligation_id}: candidate hash mismatch")
        if step.get("verdict") != obligation.get("verdict"):
            raise PackageValidationError(f"{package.name}/{obligation_id}: verdict mismatch")
        if step.get("proof_status") != obligation.get("proof_status"):
            raise PackageValidationError(f"{package.name}/{obligation_id}: proof status mismatch")
        if obligation.get("run_id") not in obligation.get("step_path", ""):
            raise PackageValidationError(f"{package.name}/{obligation_id}: run provenance mismatch")
        verdicts[step["verdict"]] += 1
    expected_summary = {name: verdicts.get(name, 0) for name in ("NONZERO", "UNKNOWN", "ZERO")}
    if obligations_doc.get("summary") != expected_summary or manifest.get("verdict_totals") != expected_summary:
        raise PackageValidationError(f"{package.name}: verdict totals mismatch")
    if set(program.get("obligations", [])) != obligation_ids:
        raise PackageValidationError(f"{package.name}: program obligations mismatch")
    all_required_zero = all(
        not obligation.get("required") or obligation.get("verdict") == "ZERO"
        for obligation in obligations
    )
    if (manifest["package_status"] == "PACKAGE_READY") != all_required_zero:
        raise PackageValidationError(f"{package.name}: readiness does not match ZERO gate")
    if manifest["package_status"] == "PROOF_REQUIRED" and not verdicts.get("UNKNOWN"):
        raise PackageValidationError(f"{package.name}: PROOF_REQUIRED lacks UNKNOWN evidence")
    return expected_summary


def validate_all(root: Path = ROOT) -> dict[str, Any]:
    packages = package_dirs(root)
    if not 4 <= len(packages) <= 6:
        raise PackageValidationError("thermal package count must be between 4 and 6")
    missing = [path.name for path in packages if not path.is_dir()]
    if missing:
        raise PackageValidationError(f"missing package directories: {missing}")
    totals: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for package in packages:
        totals.update(validate_package(package))
        statuses[_load(package / "package.json")["package_status"]] += 1
    return {
        "package_count": len(packages),
        "package_statuses": dict(sorted(statuses.items())),
        "verdict_totals": {name: totals.get(name, 0) for name in ("NONZERO", "UNKNOWN", "ZERO")},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if not args.write and not args.check:
        parser.error("choose --write and/or --check")
    if args.write:
        materialize_all()
    result = validate_all()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
