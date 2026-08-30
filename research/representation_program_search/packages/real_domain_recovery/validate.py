"""Fail-closed validation for real-domain DEV-candidate packages.

This validator can establish package integrity and candidate-review readiness.
It cannot admit a package to DEV and deliberately has no admission code path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from research.representation_program_search.audits.leakage.audit import (
    alpha_normalize,
    audit_case,
    discover_reference_corpus,
    historical_ids,
    strict_normalize,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import SearchContractError, load_public_case


POLICY = "RPS_REAL_DOMAIN_RECOVERY_VALIDATOR_V1"
COLLECTION = "research/representation_program_search/packages/real_domain_recovery"
PACKAGE_IDS = ("rps-real-c3j9", "rps-real-c8q2")
VARIANTS = ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
CANDIDATE = "CANDIDATE_FOR_INDEPENDENT_REVIEW"
FORBIDDEN_PROPOSER_TERMS = (
    "bessel",
    "daleckii",
    "divided difference",
    "fréchet",
    "frechet",
    "gold program",
    "hermite",
    "newton",
    "operator sequence",
    "recurrence",
    "representation_depth",
    "rubensson",
    "spherical",
    "target representation",
)
EXPECTED_EXTERNAL_HASHES = {
    "rps-real-c3j9": {
        "732b25ee69191ccd32a936ad3f61bced8e97e2f77e59b79da94bea0acc2e281e"
    },
    "rps-real-c8q2": {
        "3524de6ca0ba911d6df6771fb10f9f5df0d0982024dbcb4519b792cf626e92f1",
        "218210d3de4ad84b883a27194acbc8eb6fa0d03749ec5c05c452d10f96e2a569",
        "623778bb89242d78a318a287913fd56f2e4f91932dbf8109c517e9580ede81aa",
        "fffa57fcb9a4188b0d14043f216a2fa1580833df4e35e4fba9a90c33f16d7539",
        "6c3f4818af99d4416060d886785de392d759b70ba663ebf8abbce454e0082d54",
        "419e460696027ff105fbcd0302ac0ccf774ba4c870e85d51cc93fc0f8f5f3045",
    },
}


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(package: Path) -> dict[str, Any]:
    payload = _json(package / "package.json")
    errors: list[str] = []
    declared: dict[str, str] = {}
    entries = payload.get("artifact_hashes")
    if not isinstance(entries, list):
        entries = []
        errors.append("ARTIFACT_HASHES_NOT_LIST")
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        relative, digest = entry["path"], entry["sha256"]
        if (
            not isinstance(relative, str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
            or relative in declared
        ):
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        declared[relative] = str(digest)
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
    expected_header = {
        "schema_version": "RPSCasePackageV1",
        "package_id": package.name,
        "package_status": "PACKAGE_READY",
        "admission_status": CANDIDATE,
        "eligibility": CANDIDATE,
    }
    for key, expected in expected_header.items():
        if payload.get(key) != expected:
            errors.append(f"MANIFEST_FIELD_INVALID:{key}")
    return {
        "artifact_count": len(actual),
        "errors": sorted(set(errors)),
        "status": "VALID" if not errors else "INVALID",
    }


def _compile(package: Path) -> dict[str, Any]:
    loaded = load_case_package(package)
    results: dict[str, Any] = {}
    for grammar_id in VARIANTS:
        if grammar_id == "G_FULL":
            program = loaded.program
        else:
            program = program_from_dict(
                _json(package / "reference/ablations" / f"{grammar_id}.program.json")
            )
        context = CompileContext(
            package.resolve(),
            loaded.context.symbols,
            loaded.context.functions,
            grammar_id=grammar_id,
        )
        compiled = compile_program(program, context)
        results[grammar_id] = {
            "compilation": compiled.to_dict(),
            "program_id": canonical_program_hash(program),
        }
    return {
        "loader_schema_deltas": list(loaded.schema_deltas),
        "variants": results,
    }


def _receipts(package: Path) -> dict[str, Any]:
    index = _json(package / "verification/index.json")
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    observed: set[tuple[str, str]] = set()
    for attempt in index.get("attempts", []):
        run_id = attempt.get("run_id")
        variant = attempt.get("program_variant")
        obligation = attempt.get("obligation_id")
        member_id = attempt.get("member_id")
        if not all(isinstance(item, str) for item in (run_id, variant, obligation, member_id)):
            errors.append("RECEIPT_INDEX_ROW_INVALID")
            continue
        key = (variant, obligation)
        if key in observed:
            errors.append(f"RECEIPT_DUPLICATE:{variant}:{obligation}")
        observed.add(key)
        run_root = package / "verification/workspace/runs" / run_id
        proposal_path = run_root / f"steps/step_{attempt.get('proposal_step', 0):03d}.json"
        step_path = run_root / f"steps/step_{attempt.get('verification_step', 0):03d}.json"
        run_manifest_path = run_root / "manifest.json"
        candidate_path = package / str(attempt.get("candidate_path"))
        member_path = package / "members" / f"{member_id}.txt"
        if not all(
            path.is_file()
            for path in (proposal_path, step_path, run_manifest_path, candidate_path, member_path)
        ):
            errors.append(f"RECEIPT_ARTIFACT_MISSING:{run_id}")
            continue
        proposal = _json(proposal_path)
        step = _json(step_path)
        run_manifest = _json(run_manifest_path)
        checks = {
            "candidate_hash_bound": step.get("candidate_hash") == _sha256(candidate_path),
            "current_hash_bound": step.get("current_hash") == _sha256(member_path),
            "main_proposer_recorded": (
                run_manifest.get("requested_proposer_mode") == "main"
                and proposal.get("status") == "HYPOTHESIS"
                and proposal.get("proof_status") == "HYPOTHESIS"
                and proposal.get("candidate_text") == step.get("candidate_text")
                and proposal.get("candidate_hash")
                == hashlib.sha256(str(proposal.get("candidate_text")).encode()).hexdigest()
                and any(
                    isinstance(item, dict)
                    and item.get("kind") == "proposer_candidate"
                    and item.get("invocation_mode") == "main_agent"
                    for item in proposal.get("evidence", [])
                )
            ),
            "proof_status_proven": step.get("proof_status") == "PROVEN",
            "residual_exact_zero": step.get("residual") == "0",
            "status_certified": step.get("status") == "CERTIFIED",
            "verdict_zero": step.get("verdict") == "ZERO" == attempt.get("verdict"),
        }
        if not all(checks.values()):
            errors.append(f"RECEIPT_INVALID:{run_id}")
        rows.append({"checks": checks, **attempt})
    expected = {
        (variant, obligation)
        for variant in VARIANTS
        for obligation in _json(package / "reference/obligations.json")["obligations"]
        if obligation.get("required", True)
        for obligation in [obligation["obligation_id"]]
    }
    if observed != expected:
        errors.append("RECEIPT_COVERAGE_INCOMPLETE")
    required_counts = index.get("required_g_full_verdicts")
    if required_counts != {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 3}:
        errors.append("G_FULL_VERDICT_TOTAL_INVALID")
    return {
        "all_zero": bool(rows) and not errors,
        "attempt_count": len(rows),
        "errors": errors,
        "rows": rows,
    }


def _source_and_firewall(package: Path) -> dict[str, Any]:
    source_manifest = _json(package / "source_manifest.json")
    proposer = _json(package / "proposer_view.json")
    dossier_ref = source_manifest.get("source_dossier", {})
    assumptions_ref = proposer.get("assumptions", {})
    catalog_ref = proposer.get("source_catalog", {})
    visible_objects = [proposer]
    for ref in (assumptions_ref, catalog_ref):
        if isinstance(ref, dict) and isinstance(ref.get("path"), str):
            visible_objects.append(_json(package / ref["path"]))
    visible_blob = json.dumps(visible_objects, sort_keys=True, ensure_ascii=False).casefold()
    leaks = sorted(term for term in FORBIDDEN_PROPOSER_TERMS if term in visible_blob)
    sources = source_manifest.get("sources", [])
    complete_sources = all(
        isinstance(source, dict)
        and isinstance(source.get("artifact_sha256"), str)
        and bool(re.fullmatch(r"[0-9a-f]{64}", source["artifact_sha256"]))
        and isinstance(source.get("locator"), str)
        and isinstance(source.get("retrieved_on"), str)
        and isinstance(source.get("url"), str)
        for source in sources
    )
    external_hashes = {source.get("artifact_sha256") for source in sources}
    local_source_hashes = all(
        _sha256(package / source["path"]) == source["artifact_sha256"]
        for source in sources
        if isinstance(source, dict) and "path" in source
    )
    symbols = _json(package / "symbols.json").get("symbols", [])
    predicates = _json(package / "assumptions.json").get("predicates", [])
    catalog_members = _json(package / "source_catalog.json").get("members", [])
    return {
        "all_symbols_explicitly_real": bool(symbols)
        and all(symbol.get("real") is True for symbol in symbols),
        "assumption_contract_complete": (
            _json(package / "assumptions.json").get("status")
            == "ASSUMPTION_COMPLETE"
            and bool(predicates)
            and all(item.get("status") in {"DECLARED", "DERIVED"} for item in predicates)
        ),
        "assumptions_hash_bound": (
            _sha256(package / assumptions_ref["path"]) == assumptions_ref.get("sha256")
        ),
        "catalog_hash_bound": (
            _sha256(package / catalog_ref["path"]) == catalog_ref.get("sha256")
        ),
        "dossier_hash_bound": (
            _sha256(package / dossier_ref["path"]) == dossier_ref.get("sha256")
        ),
        "expected_retrieval_hashes_present": external_hashes
        == EXPECTED_EXTERNAL_HASHES[package.name],
        "local_source_artifacts_hash_bound": local_source_hashes,
        "opaque_case_id": bool(re.fullmatch(r"C[A-Z0-9]+", proposer.get("case_id", ""))),
        "opaque_member_ids": bool(catalog_members)
        and all(re.fullmatch(r"M[A-Z0-9]+", row.get("member_id", "")) for row in catalog_members),
        "primary_locator_complete": complete_sources,
        "proposer_leaks": leaks,
    }


def _duplicate_audit(root: Path, package: Path) -> dict[str, Any]:
    expressions = [
        path.read_text(encoding="utf-8").strip()
        for path in sorted((package / "members").glob("*.txt"))
    ]
    exact: list[str] = []
    renamed: list[str] = []
    package_root = root / "research/representation_program_search/packages"
    for path in sorted(package_root.glob("**/members/*.txt")):
        if package in path.parents:
            continue
        text = path.read_text(encoding="utf-8").strip()
        if any(strict_normalize(text) == strict_normalize(expr) for expr in expressions):
            exact.append(path.relative_to(root).as_posix())
        elif any(alpha_normalize(text) == alpha_normalize(expr) for expr in expressions):
            renamed.append(path.relative_to(root).as_posix())
    payload = {
        "case_id": _json(package / "proposer_view.json")["case_id"],
        "expression_sketch": "\n".join(expressions),
        "proposer_view": _json(package / "proposer_view.json"),
        "source_catalog": [{"expression": expression} for expression in expressions],
        "title": "opaque real-domain recovery candidate",
    }
    references = discover_reference_corpus(root)
    corpus = audit_case(payload, references, historical_ids(root, references), top_k=8)
    guo_references = [
        reference.path
        for reference in references
        if "guo" in f"{reference.document_id} {reference.path} {reference.title}".casefold()
    ]
    return {
        "corpus_audit": corpus,
        "corpus_partitions": sorted({reference.partition for reference in references}),
        "exact_member_matches": exact,
        "guo_references": guo_references,
        "reference_count": len(references),
        "renamed_member_matches": renamed,
    }


def _public_loader(package: Path) -> dict[str, Any]:
    expected_symbols = tuple(_json(package / "symbols.json")["symbols"])
    expected_statuses = {
        row["predicate_id"]: row["status"]
        for row in _json(package / "assumptions.json")["predicates"]
    }
    expected_paths = {
        "assumptions.json",
        "proposer_view.json",
        "source_catalog.json",
        "symbols.json",
        *{
            row["path"]
            for row in _json(package / "source_catalog.json")["members"]
        },
    }
    try:
        case = load_public_case(package / "proposer_view.json")
    except SearchContractError as exc:
        return {
            "accessed_paths": [],
            "assumption_statuses_exact": False,
            "error": str(exc),
            "loaded": False,
            "symbols_exact": False,
        }
    return {
        "accessed_paths": list(case.accessed_paths),
        "assumption_statuses_exact": dict(case.assumption_statuses)
        == expected_statuses,
        "case_id": case.case_id,
        "error": None,
        "expected_paths_exact": set(case.accessed_paths) == expected_paths,
        "loaded": True,
        "namespace_provenance": case.namespace_provenance,
        "symbols_exact": case.symbols == expected_symbols,
    }
def _validate_package(root: Path, package: Path) -> dict[str, Any]:
    manifest = _manifest(package)
    compiled = _compile(package)
    receipts = _receipts(package)
    source = _source_and_firewall(package)
    duplicate = _duplicate_audit(root, package)
    public_loader = _public_loader(package)
    review = _json(package / "reference/review.json")
    hard_checks = {
        "all_variants_compile": all(
            row["compilation"]["status"] == "COMPILED"
            for row in compiled["variants"].values()
        ),
        "all_variants_non_tautological": all(
            row["compilation"]["tautological"] is False
            for row in compiled["variants"].values()
        ),
        "all_symbols_explicitly_real": source["all_symbols_explicitly_real"],
        "assumption_contract_complete": source["assumption_contract_complete"],
        "manifest_valid": manifest["status"] == "VALID",
        "m1_loader_has_no_schema_delta": not compiled["loader_schema_deltas"],
        "duplicate_corpus_includes_guo": bool(duplicate["guo_references"]),
        "no_exact_or_alpha_duplicate": not duplicate["exact_member_matches"]
        and not duplicate["renamed_member_matches"],
        "proposer_artifacts_hash_bound": source["assumptions_hash_bound"]
        and source["catalog_hash_bound"],
        "proposer_firewall_clean": not source["proposer_leaks"],
        "public_search_loader_contract": public_loader["loaded"]
        and public_loader["symbols_exact"]
        and public_loader["assumption_statuses_exact"]
        and public_loader["expected_paths_exact"]
        and public_loader["namespace_provenance"] == "EXACT_PROPOSER_REFERENCE",
        "receipts_exact_zero": receipts["all_zero"],
        "review_status_candidate_only": review.get("candidate_status") == CANDIDATE,
        "source_provenance_hash_bound": source["dossier_hash_bound"]
        and source["expected_retrieval_hashes_present"]
        and source["local_source_artifacts_hash_bound"]
        and source["primary_locator_complete"],
    }
    return {
        "admission_decision": "NO_ADMISSION_PERFORMED",
        "compiled_programs": compiled,
        "duplicate_and_leakage_review": duplicate,
        "hard_checks": hard_checks,
        "manifest": manifest,
        "package_id": package.name,
        "public_loader": public_loader,
        "receipts": receipts,
        "source_and_firewall": source,
        "status": CANDIDATE if all(hard_checks.values()) else "REJECTED",
    }


def validate(root: Path) -> dict[str, Any]:
    base = root / COLLECTION
    packages = [_validate_package(root, base / package_id) for package_id in PACKAGE_IDS]
    gaps = _json(base / "RECOVERY_GAPS.json")
    complete = all(package["status"] == CANDIDATE for package in packages)
    return {
        "admission_decision": "NO_ADMISSION_PERFORMED",
        "gaps": gaps,
        "packages": packages,
        "policy": POLICY,
        "status": "VALID_CANDIDATE_SET" if complete else "INVALID",
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Real-Domain DEV Candidate Recovery Audit",
        "",
        f"Status: `{report['status']}`",
        "",
        "No package was admitted. Each retained package remains "
        "`CANDIDATE_FOR_INDEPENDENT_REVIEW`.",
        "",
        "## Package checks",
        "",
    ]
    for package in report["packages"]:
        lines.extend(
            [
                f"### {package['package_id']}",
                "",
                f"Disposition: `{package['status']}`",
                "",
                f"Recorded exact-ZERO receipts: {package['receipts']['attempt_count']}",
                "",
                "Public search loader: "
                + (
                    "exact symbols and assumption statuses"
                    if package["public_loader"]["loaded"]
                    and package["public_loader"]["symbols_exact"]
                    and package["public_loader"]["assumption_statuses_exact"]
                    else f"FAILED ({package['public_loader']['error']})"
                ),
                "",
            ]
        )
        failed = [name for name, passed in package["hard_checks"].items() if not passed]
        lines.append("Failed hard checks: " + (", ".join(failed) if failed else "none"))
        lines.append("")
    lines.extend(
        [
            "## Missing slots",
            "",
            "R2 and R6 remain missing for the reasons recorded in `RECOVERY_GAPS.json`.",
            "The R3 and R4/R5 entries are review candidates, not benchmark assignments.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    report = validate(args.root.resolve())
    text = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(_render_markdown(report), encoding="utf-8")
    return 0 if report["status"] == "VALID_CANDIDATE_SET" else 1


if __name__ == "__main__":
    raise SystemExit(main())
