"""Deterministic validation for fail-closed J2 recovery artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from research.representation_program_search.audits.leakage.audit import (
    alpha_normalize,
    discover_reference_corpus,
    historical_ids,
    audit_case,
    strict_normalize,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict


POLICY = "RPS_DEV_RECOVERY_VALIDATOR_V1"
PACKAGE_ID = "rps-candidate-j2-001"
FORBIDDEN_PROPOSER_TERMS = (
    "hermite",
    "newton_dd",
    "hermite_dd",
    "frechet",
    "fréchet",
    "repeated node",
    "repeated-node",
    "representation_depth",
    "target representation",
    "gold program",
    "operator sequence",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def _manifest(package: Path) -> dict[str, Any]:
    payload = _json(package / "package.json")
    entries = payload.get("artifact_hashes")
    errors: list[str] = []
    declared: dict[str, str] = {}
    if not isinstance(entries, list):
        errors.append("ARTIFACT_HASHES_NOT_LIST")
        entries = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        relative, expected = item["path"], item["sha256"]
        if not isinstance(relative, str) or not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        if relative in declared:
            errors.append("ARTIFACT_ENTRY_DUPLICATE")
        declared[relative] = str(expected)
    actual = {
        path.relative_to(package).as_posix(): _sha256(path)
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    }
    if declared != actual:
        errors.append("ARTIFACT_MANIFEST_MISMATCH")
    if payload.get("package_status") != "PACKAGING_GAP":
        errors.append("CONTRACT_DEFECT_MUST_NOT_BE_PACKAGE_READY")
    return {
        "artifact_count": len(actual),
        "errors": sorted(set(errors)),
        "status": "VALID" if not errors else "INVALID",
    }


def _compile(package: Path) -> dict[str, Any]:
    loaded = load_case_package(package)
    full = compile_program(loaded.program, loaded.context)
    raw = _json(package / "reference/ablations/G_PRIMITIVE.program.json")
    primitive = program_from_dict(raw)
    primitive_context = CompileContext(
        package.resolve(),
        loaded.context.symbols,
        loaded.context.functions,
        grammar_id="G_PRIMITIVE",
    )
    no_hermite_context = CompileContext(
        package.resolve(),
        loaded.context.symbols,
        loaded.context.functions,
        grammar_id="G_NO_HERMITE",
    )
    primitive_result = compile_program(primitive, primitive_context)
    no_hermite_result = compile_program(primitive, no_hermite_context)
    full_node_shapes = [list(item.nodes) for item in loaded.program.node_structures]
    return {
        "full": full.to_dict(),
        "full_program_id": canonical_program_hash(loaded.program),
        "full_repeated_node_shapes": full_node_shapes,
        "loader_schema_deltas": list(loaded.schema_deltas),
        "no_hermite_compositional": no_hermite_result.to_dict(),
        "primitive": primitive_result.to_dict(),
        "primitive_program_id": canonical_program_hash(primitive),
    }


def _receipts(package: Path) -> dict[str, Any]:
    index = _json(package / "verification/index.json")
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for attempt in index.get("attempts", []):
        run_id = attempt["run_id"]
        step_path = package / "verification/workspace/runs" / run_id / "steps/step_001.json"
        step = _json(step_path)
        variant = attempt["program_variant"].casefold().replace("g_", "")
        candidate_path = package / "reference/candidates" / f'{attempt["obligation_id"]}.{variant}.txt'
        member_path = package / "members" / f'{attempt["member_id"]}.txt'
        checks = {
            "candidate_hash_bound": step.get("candidate_hash") == _sha256(candidate_path),
            "current_hash_bound": step.get("current_hash") == _sha256(member_path),
            "proof_status_proven": step.get("proof_status") == "PROVEN",
            "residual_exact_zero": step.get("residual") == "0",
            "status_certified": step.get("status") == "CERTIFIED",
            "verdict_zero": step.get("verdict") == "ZERO",
        }
        if not all(checks.values()):
            errors.append(f"RECEIPT_INVALID:{run_id}")
        rows.append({"checks": checks, **attempt})
    return {
        "all_zero": bool(rows) and not errors,
        "attempt_count": len(rows),
        "domain_eligibility": "INELIGIBLE_REAL_FALSE_CONTRACT_DEFECT",
        "errors": errors,
        "rows": rows,
    }


def _source_and_firewall(root: Path, package: Path) -> dict[str, Any]:
    manifest = _json(package / "source_manifest.json")
    dossier = manifest["source_dossier"]
    dossier_path = package / dossier["path"]
    proposer = _json(package / "proposer_view.json")
    assumptions = proposer["assumptions"]
    catalog = proposer["source_catalog"]
    blob = json.dumps(proposer, sort_keys=True).casefold()
    leaks = sorted(term for term in FORBIDDEN_PROPOSER_TERMS if term in blob)
    opaque_case = bool(re.fullmatch(r"C[A-Z0-9]+", proposer.get("case_id", "")))
    opaque_members = all(
        re.fullmatch(r"[A-Z][A-Z0-9]+", item.get("member_id", ""))
        for item in catalog.get("members", [])
    )
    return {
        "assumptions_hash_bound": _sha256(package / assumptions["path"]) == assumptions["sha256"],
        "catalog_hash_bound": _sha256(package / catalog["path"]) == catalog["sha256"],
        "dossier_exact_copy": _sha256(dossier_path) == dossier["sha256"] == _sha256(
            root / "research/representation_program_search/cases/diffphys/rps-dp-relton-second-frechet.json"
        ),
        "opaque_case_id": opaque_case,
        "opaque_member_ids": opaque_members,
        "primary_locator_complete": all(
            isinstance(source.get("retrieved_on"), str)
            and isinstance(source.get("locator"), str)
            and isinstance(source.get("url"), str)
            and isinstance(source.get("artifact_sha256"), str)
            for source in manifest.get("sources", [])
        ),
        "proposer_leaks": leaks,
    }


def _duplicate_audit(root: Path, package: Path) -> dict[str, Any]:
    expressions = [path.read_text(encoding="utf-8").strip() for path in sorted((package / "members").glob("*.txt"))]
    exact: list[str] = []
    renamed: list[str] = []
    package_base = root / "research/representation_program_search/packages"
    for path in sorted(package_base.glob("**/members/*.txt")):
        if package in path.parents:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if any(strict_normalize(text) == strict_normalize(expr) for expr in expressions):
            exact.append(path.relative_to(root).as_posix())
        elif any(alpha_normalize(text) == alpha_normalize(expr) for expr in expressions):
            renamed.append(path.relative_to(root).as_posix())
    payload = {
        "case_id": "C7X4",
        "expression_sketch": "\n".join(expressions),
        "proposer_view": _json(package / "proposer_view.json"),
        "source_catalog": [{"expression": item} for item in expressions],
        "title": "opaque source family C7X4",
    }
    references = discover_reference_corpus(root)
    corpus = audit_case(payload, references, historical_ids(root, references), top_k=8)
    review_notes = [
        "Thematic overlap with historical first-Frechet/Daleckii-Krein and exp phi/Hermite cases requires independent review.",
        "The two second-order members are distinct mixed-direction components with node multisets [x,x,y] and [x,y,y], not renamings of the historical zero-node phi family.",
        "Visible common subexpressions create a CSE-baseline risk even though the IR-level program is non-tautological.",
    ]
    return {
        "corpus_audit": corpus,
        "exact_member_matches": exact,
        "manual_review_notes": review_notes,
        "renamed_member_matches": renamed,
    }


def validate(root: Path) -> dict[str, Any]:
    package = root / "research/representation_program_search/packages/dev_recovery" / PACKAGE_ID
    manifest = _manifest(package)
    compiled = _compile(package)
    receipts = _receipts(package)
    source = _source_and_firewall(root, package)
    duplicate = _duplicate_audit(root, package)
    hard_checks = {
        "full_compiles": compiled["full"]["status"] == "COMPILED",
        "manifest_valid": manifest["status"] == "VALID",
        "m1_loader_has_no_schema_delta": not compiled["loader_schema_deltas"],
        "no_hermite_program_compiles": compiled["no_hermite_compositional"]["status"] == "COMPILED",
        "primitive_program_compiles": compiled["primitive"]["status"] == "COMPILED",
        "proposer_artifacts_hash_bound": source["assumptions_hash_bound"] and source["catalog_hash_bound"],
        "proposer_firewall_clean": not source["proposer_leaks"],
        "receipts_exact_zero": receipts["all_zero"],
        "source_hash_bound": source["dossier_exact_copy"],
        "zero_receipts_ineligible": receipts["domain_eligibility"] == "INELIGIBLE_REAL_FALSE_CONTRACT_DEFECT",
    }
    return {
        "admission_decision": "PACKAGING_GAP",
        "compiled_programs": compiled,
        "duplicate_and_baseline_review": duplicate,
        "hard_checks": hard_checks,
        "manifest": manifest,
        "package_id": PACKAGE_ID,
        "policy": POLICY,
        "receipts": receipts,
        "source_and_firewall": source,
        "status": "VALID_PACKAGING_GAP_EVIDENCE" if all(hard_checks.values()) else "INVALID",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()
    report = validate(args.root.resolve())
    text = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["status"] == "VALID_PACKAGING_GAP_EVIDENCE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
