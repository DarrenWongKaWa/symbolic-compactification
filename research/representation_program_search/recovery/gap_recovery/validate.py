"""Fail-closed validation for the strict R2 repair and bounded R6 gap audit."""
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

from .build_package import SOURCE_EXCERPT_HASHES, VARIANTS


POLICY = "RPS_GAP_RECOVERY_VALIDATOR_V1"
COLLECTION = "research/representation_program_search/recovery/gap_recovery"
PACKAGE_ID = "rps-candidate-k9-001"
CANDIDATE = "CANDIDATE_FOR_INDEPENDENT_REVIEW"
PREDECESSOR = (
    "research/representation_program_search/packages/gap_fill/"
    "gf-cr3bp-2017-eq28"
)
PREDECESSOR_TREE_SHA256 = (
    "0943a6ae269d81af89daf96202303e183d7c75f8383a959f67c149501b04fdc0"
)
PUBLIC_FORBIDDEN_TERMS = (
    "cr3bp",
    "divided difference",
    "eq28",
    "equation (28)",
    "frechet",
    "fréchet",
    "gold",
    "hermite",
    "latent",
    "newton",
    "operator sequence",
    "representation_depth",
    "target representation",
    "three-body",
)


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(path: Path) -> tuple[str, int]:
    rows = [
        f"{item.relative_to(path).as_posix()}\t{_sha(item)}"
        for item in sorted(path.rglob("*"))
        if item.is_file()
    ]
    payload = ("\n".join(rows) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), len(rows)


def _manifest(package: Path) -> dict[str, Any]:
    payload = _json(package / "package.json")
    errors: list[str] = []
    declared: dict[str, str] = {}
    for entry in payload.get("artifact_hashes", []):
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        relative, digest = entry["path"], entry["sha256"]
        if (
            not isinstance(relative, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            or relative in declared
        ):
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        declared[relative] = digest
    actual = {
        item.relative_to(package).as_posix(): _sha(item)
        for item in package.rglob("*")
        if item.is_file()
        and item.name != "package.json"
        and "__pycache__" not in item.parts
        and not item.name.startswith(".")
    }
    if declared != actual:
        errors.append("ARTIFACT_MANIFEST_MISMATCH")
    expected = {
        "admission_status": CANDIDATE,
        "audited_depth": "R2_NEWTON_DD",
        "eligibility": CANDIDATE,
        "package_id": PACKAGE_ID,
        "package_status": "PACKAGE_READY",
        "schema_version": "RPSCasePackageV1",
        "verdict_totals": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 12},
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            errors.append(f"MANIFEST_FIELD_INVALID:{key}")
    return {
        "artifact_count": len(actual),
        "errors": sorted(set(errors)),
        "status": "VALID" if not errors else "INVALID",
    }


def _public_boundary(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    symbols_payload = _json(package / "symbols.json")["symbols"]
    assumptions = _json(package / "assumptions.json")
    expected_statuses = {
        row["predicate_id"]: row["status"] for row in assumptions["predicates"]
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
        return {"errors": [str(exc)], "loaded": False, "status": "INVALID"}
    if case.case_id != "C9H4" or not re.fullmatch(r"C[A-Z0-9]+", case.case_id):
        errors.append("PUBLIC_CASE_ID_NOT_OPAQUE")
    if tuple(symbols_payload) != case.symbols:
        errors.append("PUBLIC_SYMBOL_NAMESPACE_MISMATCH")
    if any(item.get("real") is not True for item in symbols_payload):
        errors.append("PUBLIC_SYMBOL_NOT_EXPLICITLY_REAL")
    if any(item.get("real") is False for item in symbols_payload):
        errors.append("PUBLIC_REAL_FALSE_INFERENCE")
    if dict(case.assumption_statuses) != expected_statuses:
        errors.append("PUBLIC_ASSUMPTION_STATUS_MISMATCH")
    if case.namespace_provenance != "EXACT_PROPOSER_REFERENCE":
        errors.append("PUBLIC_NAMESPACE_NOT_EXACT")
    if set(case.accessed_paths) != expected_paths:
        errors.append("PUBLIC_ACCESSED_PATH_MISMATCH")
    if any(
        {"reference", "verification", "final", "runs", "steps"}
        & set(Path(relative).parts)
        for relative in case.accessed_paths
    ):
        errors.append("PUBLIC_EVALUATOR_PATH_ACCESSED")
    catalog = _json(package / "source_catalog.json")
    if not all(
        re.fullmatch(r"M[A-Z0-9]+", row.get("member_id", ""))
        for row in catalog["members"]
    ):
        errors.append("PUBLIC_MEMBER_ID_NOT_OPAQUE")
    public_objects: list[Any] = [
        _json(package / "proposer_view.json"),
        catalog,
        assumptions,
        _json(package / "symbols.json"),
        *[member.expression for member in case.members],
    ]
    public_blob = json.dumps(public_objects, sort_keys=True, ensure_ascii=False).casefold()
    leaks = [term for term in PUBLIC_FORBIDDEN_TERMS if term in public_blob]
    if leaks:
        errors.extend(f"PUBLIC_TERM_LEAK:{term}" for term in leaks)
    return {
        "accessed_paths": list(case.accessed_paths),
        "assumption_statuses": dict(case.assumption_statuses),
        "errors": sorted(set(errors)),
        "loaded": True,
        "namespace_provenance": case.namespace_provenance,
        "proposer_view_sha256": case.proposer_view_sha256,
        "public_term_leaks": leaks,
        "status": "VALID" if not errors else "INVALID",
        "symbols": list(case.symbols),
    }


def _compile(package: Path) -> dict[str, Any]:
    loaded = load_case_package(package)
    errors: list[str] = []
    rows: dict[str, Any] = {}
    for grammar_id in VARIANTS:
        program = (
            loaded.program
            if grammar_id == "G_FULL"
            else program_from_dict(
                _json(
                    package
                    / "reference/ablations"
                    / f"{grammar_id}.program.json"
                )
            )
        )
        compiled = compile_program(
            program,
            CompileContext(
                package.resolve(),
                loaded.context.symbols,
                loaded.context.functions,
                grammar_id=grammar_id,
            ),
        )
        stored = _json(package / "reference/compilations" / f"{grammar_id}.json")
        program_id = canonical_program_hash(program)
        if stored.get("compilation") != compiled.to_dict():
            errors.append(f"COMPILATION_RECEIPT_MISMATCH:{grammar_id}")
        if stored.get("program_id") != program_id:
            errors.append(f"COMPILATION_PROGRAM_HASH_MISMATCH:{grammar_id}")
        if compiled.status != "COMPILED" or compiled.tautological is not False:
            errors.append(f"COMPILATION_INVALID:{grammar_id}")
        if len(compiled.obligations) != 4:
            errors.append(f"COMPILATION_OBLIGATION_COUNT:{grammar_id}")
        rows[grammar_id] = {
            "compilation": compiled.to_dict(),
            "program_id": program_id,
        }
    if loaded.schema_deltas:
        errors.append("M1_SCHEMA_DELTA")
    full_ops = {item.operator for item in loaded.program.operators}
    primitive = program_from_dict(
        _json(package / "reference/ablations/G_PRIMITIVE.program.json")
    )
    primitive_ops = {item.operator for item in primitive.operators}
    if full_ops != {"LINEAR_COMBINATION", "NEWTON_DD"}:
        errors.append("FULL_OPERATOR_SET_INVALID")
    if not primitive_ops <= {
        "VALUE",
        "DERIVATIVE",
        "SUBSTITUTE",
        "LINEAR_COMBINATION",
        "COMPOSE",
    } or "NEWTON_DD" in primitive_ops:
        errors.append("PRIMITIVE_OPERATOR_SET_INVALID")
    return {
        "errors": errors,
        "loader_schema_deltas": list(loaded.schema_deltas),
        "status": "VALID" if not errors else "INVALID",
        "variants": rows,
    }


def _receipts(package: Path) -> dict[str, Any]:
    index = _json(package / "verification/index.json")
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    observed: set[tuple[str, str]] = set()
    for attempt in index.get("attempts", []):
        variant = attempt.get("program_variant")
        obligation_id = attempt.get("obligation_id")
        member_id = attempt.get("member_id")
        run_id = attempt.get("run_id")
        key = (str(variant), str(obligation_id))
        if key in observed:
            errors.append(f"RECEIPT_DUPLICATE:{key}")
        observed.add(key)
        run_root = package / "verification/workspace/runs" / str(run_id)
        proposal_path = run_root / "steps/step_001.json"
        step_path = run_root / "steps/step_002.json"
        manifest_path = run_root / "manifest.json"
        candidate_path = package / str(attempt.get("candidate_path"))
        member_path = package / "members" / f"{member_id}.txt"
        if not all(
            item.is_file()
            for item in (
                proposal_path,
                step_path,
                manifest_path,
                candidate_path,
                member_path,
            )
        ):
            errors.append(f"RECEIPT_ARTIFACT_MISSING:{run_id}")
            continue
        proposal = _json(proposal_path)
        step = _json(step_path)
        manifest = _json(manifest_path)
        checks = {
            "candidate_hash_bound": step.get("candidate_hash") == _sha(candidate_path),
            "candidate_text_bound": step.get("candidate_text")
            == candidate_path.read_text(encoding="utf-8").rstrip(),
            "current_hash_bound": step.get("current_hash") == _sha(member_path),
            "hypothesis_first": (
                proposal.get("status") == "HYPOTHESIS"
                and proposal.get("proof_status") == "HYPOTHESIS"
                and proposal.get("candidate_text") == step.get("candidate_text")
            ),
            "main_proposer": manifest.get("requested_proposer_mode") == "main",
            "residual_zero": step.get("residual") == "0",
            "verdict_zero": step.get("verdict") == "ZERO" == attempt.get("verdict"),
            "proven": step.get("proof_status") == "PROVEN",
            "certified": step.get("status") == "CERTIFIED",
        }
        if not all(checks.values()):
            errors.append(f"RECEIPT_INVALID:{run_id}")
        rows.append({"attempt": attempt, "checks": checks})
    expected = {
        (grammar_id, f"Q9H{index}")
        for grammar_id in VARIANTS
        for index in range(1, 5)
    }
    if observed != expected:
        errors.append("RECEIPT_COVERAGE_INCOMPLETE")
    if index.get("required_g_full_verdicts") != {
        "NONZERO": 0,
        "UNKNOWN": 0,
        "ZERO": 4,
    }:
        errors.append("G_FULL_VERDICT_TOTAL_INVALID")
    obligations = _json(package / "reference/obligations.json")
    if obligations.get("summary") != {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 4}:
        errors.append("OBLIGATION_SUMMARY_INVALID")
    for row in obligations.get("obligations", []):
        if (
            row.get("verdict") != "ZERO"
            or row.get("proof_status") != "PROVEN"
            or _sha(package / row["current_path"]) != row.get("current_sha256")
            or _sha(package / row["candidate_path"]) != row.get("candidate_sha256")
            or not (package / row["step_path"]).is_file()
        ):
            errors.append(f"OBLIGATION_RECEIPT_INVALID:{row.get('obligation_id')}")
    return {
        "attempt_count": len(rows),
        "errors": errors,
        "rows": rows,
        "status": "VALID" if not errors else "INVALID",
    }


def _source_and_assumptions(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    dossier = _json(package / "source/dossier.json")
    source_manifest = _json(package / "source_manifest.json")
    assumptions = _json(package / "assumptions.json")
    lowering = _json(package / "source/lowering.json")
    for relative, expected in SOURCE_EXCERPT_HASHES.items():
        if _sha(package / relative) != expected:
            errors.append(f"SOURCE_EXCERPT_HASH_MISMATCH:{relative}")
    if {
        row["path"]: row["sha256"] for row in dossier.get("source_artifacts", [])
    } != SOURCE_EXCERPT_HASHES:
        errors.append("DOSSIER_SOURCE_ARTIFACT_SET_MISMATCH")
    if {
        row["path"]: row["sha256"]
        for row in source_manifest.get("source_artifacts", [])
    } != SOURCE_EXCERPT_HASHES:
        errors.append("SOURCE_MANIFEST_ARTIFACT_SET_MISMATCH")
    primary = dossier.get("primary_source", {})
    if primary.get("source_archive_sha256") != (
        "698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a"
    ) or primary.get("source_file_sha256") != (
        "59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3"
    ):
        errors.append("PRIMARY_RETRIEVAL_HASH_INVALID")
    locators = dossier.get("source_locators", {})
    for locator_id, locator in locators.items():
        if (
            not isinstance(locator, dict)
            or not isinstance(locator.get("claim"), str)
            or not isinstance(locator.get("upstream_lines"), str)
            or locator.get("path") not in SOURCE_EXCERPT_HASHES
            or locator.get("sha256") != SOURCE_EXCERPT_HASHES.get(locator.get("path"))
            or _sha(package / locator["path"]) != locator["sha256"]
        ):
            errors.append(f"SOURCE_LOCATOR_INVALID:{locator_id}")
    correction = dossier.get("numbering_correction", {})
    if (
        set(correction.get("source_locator_ids", [])) != {"S9N1", "S9N2"}
        or "unnumbered" not in str(correction.get("claim", "")).casefold()
        or "not equation (28)" not in str(correction.get("claim", "")).casefold()
    ):
        errors.append("SOURCE_NUMBERING_CORRECTION_INVALID")
    predicates = assumptions.get("predicates", [])
    if (
        assumptions.get("status") != "ASSUMPTION_COMPLETE"
        or {row.get("status") for row in predicates} - {"DECLARED", "DERIVED"}
        or {row.get("predicate_id") for row in predicates}
        != {"P9A1", "P9A2", "P9A3", "P9A4"}
    ):
        errors.append("ASSUMPTION_CONTRACT_INVALID")
    known_predicates = {row["predicate_id"] for row in predicates}
    for predicate in predicates:
        references = [part.strip() for part in predicate["source"].split(" and ")]
        if any(item not in locators and item not in known_predicates for item in references):
            errors.append(f"ASSUMPTION_LOCATOR_UNKNOWN:{predicate['predicate_id']}")
    if "positive relative masses" in json.dumps(assumptions).casefold():
        errors.append("UNSUPPORTED_MASS_POSITIVITY")
    for member_id, row in lowering.get("members", {}).items():
        if (
            row.get("source_locator_id") not in locators
            or row.get("status") != "DERIVED"
            or not isinstance(row.get("statement"), str)
            or not isinstance(row.get("notation_map"), dict)
        ):
            errors.append(f"LOWERING_LOCATOR_INVALID:{member_id}")
    if set(lowering.get("members", {})) != {f"M9H{i}" for i in range(1, 5)}:
        errors.append("LOWERING_MEMBER_SET_INVALID")
    dossier_ref = source_manifest.get("source_dossier", {})
    if _sha(package / dossier_ref.get("path", "missing")) != dossier_ref.get("sha256"):
        errors.append("SOURCE_DOSSIER_HASH_MISMATCH")
    return {
        "errors": sorted(set(errors)),
        "locator_count": len(locators),
        "source_excerpt_hashes": dict(SOURCE_EXCERPT_HASHES),
        "status": "VALID" if not errors else "INVALID",
    }


def _duplicate_and_leakage(root: Path, package: Path) -> dict[str, Any]:
    expressions = [
        item.read_text(encoding="utf-8").strip()
        for item in sorted((package / "members").glob("*.txt"))
    ]
    exact: list[str] = []
    renamed: list[str] = []
    for item in sorted(
        (root / "research/representation_program_search/packages").glob(
            "**/members/*.txt"
        )
    ):
        if package in item.parents:
            continue
        text = item.read_text(encoding="utf-8").strip()
        relative = item.relative_to(root).as_posix()
        if any(strict_normalize(text) == strict_normalize(expr) for expr in expressions):
            exact.append(relative)
        elif any(alpha_normalize(text) == alpha_normalize(expr) for expr in expressions):
            renamed.append(relative)
    expected_predecessor = {
        f"{PREDECESSOR}/members/G{index:04d}.txt" for index in range(1, 5)
    }
    references = discover_reference_corpus(root)
    payload = {
        "case_id": "C9H4",
        "expression_sketch": "\n".join(expressions),
        "proposer_view": _json(package / "proposer_view.json"),
        "source_catalog": [{"expression": expression} for expression in expressions],
        "title": "opaque repaired candidate",
    }
    corpus = audit_case(
        payload,
        references,
        historical_ids(root, references),
        top_k=12,
    )
    guo = [
        row.path
        for row in references
        if "guo" in f"{row.document_id} {row.path} {row.title}".casefold()
    ]
    errors: list[str] = []
    if set(exact) != expected_predecessor:
        errors.append("EXACT_MATCH_SET_NOT_REJECTED_PREDECESSOR_ONLY")
    if renamed:
        errors.append("UNEXPECTED_ALPHA_RENAMED_MATCH")
    if corpus.get("findings"):
        errors.append("HISTORICAL_CORPUS_FINDING")
    if not guo:
        errors.append("GUO_CORPUS_NOT_AUDITED")
    predecessor_hash, predecessor_count = _tree_hash(root / PREDECESSOR)
    if predecessor_hash != PREDECESSOR_TREE_SHA256:
        errors.append("REJECTED_PREDECESSOR_CHANGED")
    return {
        "corpus_audit": corpus,
        "corpus_partitions": sorted({row.partition for row in references}),
        "errors": errors,
        "expected_repair_predecessor_matches": exact,
        "guo_references": guo,
        "predecessor_file_count": predecessor_count,
        "predecessor_tree_sha256": predecessor_hash,
        "reference_count": len(references),
        "renamed_matches": renamed,
        "status": "VALID" if not errors else "INVALID",
    }


def _r6_mining(root: Path) -> dict[str, Any]:
    path = root / COLLECTION / "R6_MINING_NEGATIVE.json"
    if not path.is_file():
        return {"errors": ["R6_MINING_AUDIT_MISSING"], "status": "INVALID"}
    payload = _json(path)
    errors: list[str] = []
    if payload.get("schema_version") != "RPSR6MiningNegativeV1":
        errors.append("R6_SCHEMA_INVALID")
    if (
        payload.get("status") != "NO_DEFENSIBLE_R6_CANDIDATE"
        or payload.get("candidate_count") != 0
        or payload.get("package_created") is not False
        or payload.get("admission_action") != "NONE"
    ):
        errors.append("R6_DISPOSITION_INVALID")
    criteria = payload.get("criteria", {})
    if criteria != {
        "exact_executable_reconstruction": True,
        "fresh_identity": True,
        "minimum_operator_types": 2,
        "multi_member_reuse": True,
        "proposer_target_leakage": False,
        "reject_derivative_or_response_graph": True,
        "reject_directly_exposed_master": True,
        "reject_scalar_cse": True,
        "reject_short_derivative_or_recurrence_chain": True,
    }:
        errors.append("R6_CRITERIA_INVALID")
    references = discover_reference_corpus(root)
    scope = payload.get("audit_scope", {})
    actual_scope = {
        "current_case_json_documents": len(
            list((root / "research/representation_program_search/cases").glob("**/*.json"))
        ),
        "current_package_manifests": len(
            list(
                (root / "research/representation_program_search/packages").glob(
                    "**/package.json"
                )
            )
        ),
        "guo_reference_documents": sum(
            "guo" in f"{row.document_id} {row.path} {row.title}".casefold()
            for row in references
        ),
        "historical_documents": len(references),
        "historical_partitions": sorted({row.partition for row in references}),
    }
    # ``audit_scope`` is point-in-time evidence from the recovery commit.  New
    # packages or historical records added later must not rewrite that scope or
    # retroactively invalidate the preserved negative result.  A decrease is a
    # fail-closed regression; growth requires a new audit for new claims but is
    # not evidence that the earlier audit was malformed.
    for key in (
        "current_case_json_documents",
        "current_package_manifests",
        "guo_reference_documents",
        "historical_documents",
    ):
        recorded = scope.get(key)
        actual = actual_scope[key]
        if (
            not isinstance(recorded, int)
            or isinstance(recorded, bool)
            or actual < recorded
        ):
            errors.append(f"R6_AUDIT_SCOPE_REGRESSION:{key}")
    recorded_partitions = scope.get("historical_partitions")
    if (
        not isinstance(recorded_partitions, list)
        or not set(recorded_partitions) <= set(actual_scope["historical_partitions"])
    ):
        errors.append("R6_AUDIT_SCOPE_REGRESSION:historical_partitions")
    if scope.get("fresh_test_used") is not False:
        errors.append("R6_FRESH_TEST_USED")
    if scope.get("hidden_reference_programs_used") is not False:
        errors.append("R6_HIDDEN_REFERENCE_USED")
    rows = payload.get("screened_families", [])
    if not isinstance(rows, list) or len(rows) != 5:
        errors.append("R6_SCREEN_SET_INVALID")
        rows = []
    expected_identities = {
        "time-dependent Maxwell fields from Debye potentials",
        "Potts toroidal-strip transfer-matrix family",
        "Rayleigh differential generators for spherical Bessel families",
        "higher matrix-exponential derivatives from a block lift",
        "van der Waals Helmholtz response graph",
    }
    if {row.get("identity") for row in rows} != expected_identities:
        errors.append("R6_IDENTITY_SET_INVALID")
    for row in rows:
        source = row.get("source", {})
        if (
            row.get("decision") != "REJECT_NO_PACKAGE"
            or not isinstance(row.get("failure_codes"), list)
            or not row.get("failure_codes")
            or not isinstance(row.get("operator_types_required"), list)
            or len(row.get("operator_types_required", [])) < 2
            or not isinstance(row.get("equation_support"), str)
            or not isinstance(source.get("locator"), str)
            or not isinstance(source.get("source_class"), str)
            or not isinstance(source.get("title"), str)
            or not isinstance(source.get("url"), str)
        ):
            errors.append(f"R6_SCREEN_ROW_INVALID:{row.get('identity')}")
    by_identity = {row.get("identity"): row for row in rows}
    debye = by_identity.get("time-dependent Maxwell fields from Debye potentials", {})
    if (
        debye.get("source", {}).get("locator") != "pages 2-3, equations (3)-(7)"
        or "DIRECT_MASTER_EXPOSED_BY_SOURCE_EQ3" not in debye.get("failure_codes", [])
        or "FROZEN_GRAMMAR_LACKS_CURL" not in debye.get("failure_codes", [])
    ):
        errors.append("R6_DEBYE_AUDIT_INVALID")
    potts = by_identity.get("Potts toroidal-strip transfer-matrix family", {})
    if (
        potts.get("source", {}).get("arxiv") != "cond-mat/0506274"
        or "equation (5)" not in potts.get("source", {}).get("locator", "")
        or "FROZEN_GRAMMAR_LACKS_MATRIX_POWER_TRACE_DETERMINANT"
        not in potts.get("failure_codes", [])
    ):
        errors.append("R6_POTTS_AUDIT_INVALID")
    package_dirs = {
        item.name
        for item in (root / COLLECTION).iterdir()
        if item.is_dir() and (item / "package.json").is_file()
    }
    if package_dirs != {PACKAGE_ID}:
        errors.append("UNEXPECTED_R6_PACKAGE_CREATED")
    return {
        "errors": sorted(set(errors)),
        "payload": payload,
        "status": "VALID" if not errors else "INVALID",
    }


def validate(root: Path) -> dict[str, Any]:
    root = root.resolve()
    package = root / COLLECTION / PACKAGE_ID
    sections = {
        "compilation": _compile(package),
        "duplicate_and_leakage": _duplicate_and_leakage(root, package),
        "manifest": _manifest(package),
        "public_boundary": _public_boundary(package),
        "receipts": _receipts(package),
        "r6_mining": _r6_mining(root),
        "source_and_assumptions": _source_and_assumptions(package),
    }
    hard_checks = {
        name: section["status"] == "VALID" for name, section in sections.items()
    }
    return {
        "admission_decision": "NO_ADMISSION_PERFORMED",
        "admission_self_assessment": (
            CANDIDATE if all(hard_checks.values()) else "REJECTED"
        ),
        "hard_checks": hard_checks,
        "package_id": PACKAGE_ID,
        "policy": POLICY,
        "r6_mining": sections["r6_mining"]["payload"],
        "sections": sections,
        "status": "VALID" if all(hard_checks.values()) else "INVALID",
    }


def _markdown(report: dict[str, Any]) -> str:
    failed = [name for name, value in report["hard_checks"].items() if not value]
    duplicate = report["sections"]["duplicate_and_leakage"]
    return "\n".join(
        [
            "# Strict R2 Recovery and R6 Mining Audit",
            "",
            f"Status: `{report['status']}`",
            "",
            f"Admission action: `{report['admission_decision']}`",
            "",
            f"Self-assessment: `{report['admission_self_assessment']}`",
            "",
            "The R2 package is a byte-preserving scientific-identity repair of a "
            "rejected predecessor, not a new identity. Its four expected exact "
            "matches are isolated to that predecessor.",
            "",
            f"Historical/benchmark corpus documents audited: {duplicate['reference_count']}",
            "",
            f"R6 mining disposition: `{report['r6_mining'].get('status')}`",
            "",
            "Failed hard checks: " + (", ".join(failed) if failed else "none"),
            "",
            "No package or case was admitted by this audit.",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--md-out", type=Path)
    args = parser.parse_args()
    report = validate(args.root)
    text = json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(_markdown(report), encoding="utf-8")
    return 0 if report["status"] == "VALID" else 1


if __name__ == "__main__":
    raise SystemExit(main())
