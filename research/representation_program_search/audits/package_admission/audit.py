"""Fail-closed post-package admission, depth, and leakage audit.

This module is read-only with respect to case packages.  It binds every input
by SHA-256, runs the frozen parser and M1 loader/compiler, checks retained
verifier receipts, and combines those mechanical facts with the separately
frozen bounded review policy in ``reviews.json``.  It never repairs a package,
selects TEST, or assigns a method result.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from symbolic_compactification import load_expression
from symbolic_compactification.models import AdapterError

from research.representation_program_search.audits.leakage.audit import (
    EXACT_DUPLICATE,
    HISTORICAL_ID,
    NEAR_DUPLICATE,
    RENAMED_DUPLICATE,
    SEALED_GUO,
    _leakage_findings,
    alpha_normalize,
    audit_case,
    discover_reference_corpus,
    historical_ids,
    strict_normalize,
)
from research.representation_program_search.program_ir import (
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.loader import PackageLoadError


AUDIT_VERSION = "RPS_PACKAGE_ADMISSION_AUDIT_V1"
PACKAGE_FAMILIES = ("thermal", "matrix_diffphys", "response_tensor")
LOWERING_SCOPES = {
    "SYMBOLIC_SOURCE_OBJECT",
    "FIXED_SCIENTIFIC_INSTANCE",
    "FINITE_INDEX_DIAGNOSTIC",
}
DUPLICATE_CODES = {
    EXACT_DUPLICATE,
    RENAMED_DUPLICATE,
    NEAR_DUPLICATE,
    HISTORICAL_ID,
    SEALED_GUO,
}
DISPOSITION_ORDER = (
    "HUMAN_REQUIRED",
    "DIAGNOSTIC_ONLY",
    "PROOF_REQUIRED",
    "SCHEMA_GAP",
    "LEAKAGE_REVIEW",
    "DUPLICATE_REVIEW",
    "DEPTH_DOWNGRADED",
    "REJECT_TAUTOLOGY",
    "ADMISSION_READY",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()


def _relative(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def discover_packages(root: Path) -> list[Path]:
    base = root / "research" / "representation_program_search" / "packages"
    packages: list[Path] = []
    for family in PACKAGE_FAMILIES:
        packages.extend(
            path.parent
            for path in sorted((base / family).glob("*/package.json"))
        )
    return sorted(packages, key=lambda path: (path.parent.name, path.name))


def _safe_package_path(package: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    candidate = (package / relative).resolve()
    try:
        candidate.relative_to(package.resolve())
    except ValueError:
        return None
    return candidate


def audit_manifest(package: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    strict_entries = manifest.get("artifact_hashes")
    legacy_entries = manifest.get("artifacts")
    declared: list[tuple[str, str]] = []
    source_key = "NONE"
    if isinstance(strict_entries, list):
        source_key = "artifact_hashes"
        for entry in strict_entries:
            if isinstance(entry, Mapping):
                declared.append((str(entry.get("path", "")), str(entry.get("sha256", ""))))
            else:
                declared.append(("", ""))
    elif isinstance(legacy_entries, list):
        source_key = "artifacts"
        for entry in legacy_entries:
            if isinstance(entry, Mapping):
                declared.append((str(entry.get("path", "")), str(entry.get("sha256", ""))))
            else:
                declared.append(("", ""))
    elif isinstance(legacy_entries, Mapping):
        source_key = "artifacts"
        declared.extend((str(path), str(digest)) for path, digest in legacy_entries.items())

    seen: set[str] = set()
    invalid: list[str] = []
    mismatches: list[str] = []
    for relative, expected in declared:
        target = _safe_package_path(package, relative)
        if (
            not relative
            or relative in seen
            or target is None
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
        ):
            invalid.append(relative or "<empty>")
            continue
        seen.add(relative)
        if not target.is_file() or _sha256(target) != expected:
            mismatches.append(relative)
    actual = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    }
    missing_from_manifest = sorted(actual - seen)
    nonexistent_declared = sorted(seen - actual)
    strict_contract = (
        manifest.get("schema_version") == "RPSCasePackageV1"
        and manifest.get("package_id") == package.name
        and source_key == "artifact_hashes"
        and isinstance(strict_entries, list)
        and not invalid
        and not mismatches
        and not missing_from_manifest
        and not nonexistent_declared
    )
    errors: list[str] = []
    if source_key != "artifact_hashes":
        errors.append("PACKAGE_CONTRACT_REQUIRES_ARTIFACT_HASHES_LIST")
    if invalid:
        errors.append("ARTIFACT_MANIFEST_ENTRY_INVALID")
    if mismatches:
        errors.append("ARTIFACT_HASH_MISMATCH")
    if missing_from_manifest or nonexistent_declared:
        errors.append("ARTIFACT_MANIFEST_INCOMPLETE")
    return {
        "artifact_field": source_key,
        "declared_artifact_count": len(declared),
        "errors": errors,
        "hash_integrity": not invalid and not mismatches,
        "manifest_coverage_complete": not missing_from_manifest and not nonexistent_declared,
        "missing_from_manifest": missing_from_manifest,
        "nonexistent_declared": nonexistent_declared,
        "strict_rps_case_package_v1": strict_contract,
    }


def audit_parser(package: Path) -> dict[str, Any]:
    namespace = _json(package / "symbols.json")
    symbols = namespace.get("symbols") if isinstance(namespace, Mapping) else None
    functions = namespace.get("functions", []) if isinstance(namespace, Mapping) else []
    paths = sorted((package / "members").glob("*.txt"))
    paths += sorted((package / "reference").rglob("*.txt"))
    rows: list[dict[str, Any]] = []
    for path in sorted(set(paths)):
        try:
            record = load_expression(path, symbols, functions=functions or None)
            rows.append({
                "path": path.relative_to(package).as_posix(),
                "sha256": record.sha256,
                "status": "PARSED",
            })
        except (AdapterError, TypeError, ValueError, OSError) as exc:
            rows.append({
                "error": getattr(exc, "code", type(exc).__name__),
                "path": path.relative_to(package).as_posix(),
                "status": "PARSE_FAILURE",
            })
    return {
        "all_machine_expressions_parse": bool(rows) and all(row["status"] == "PARSED" for row in rows),
        "expression_count": len(rows),
        "expressions": rows,
    }


def audit_source(package: Path, root: Path) -> dict[str, Any]:
    payload = _json(package / "source_manifest.json")
    dossier = payload.get("source_dossier") if isinstance(payload, Mapping) else None
    dossier_path = dossier.get("path") if isinstance(dossier, Mapping) else None
    dossier_hash = dossier.get("sha256") if isinstance(dossier, Mapping) else None
    binding = "ABSENT"
    binding_valid = False
    if isinstance(dossier_path, str) and isinstance(dossier_hash, str):
        package_target = (package / dossier_path).resolve() if not Path(dossier_path).is_absolute() else None
        repo_target = (root / dossier_path).resolve()
        if (
            package_target is not None
            and package_target.is_file()
            and package_target.is_relative_to(root)
        ):
            binding = "PACKAGE_RELATIVE"
            binding_valid = _sha256(package_target) == dossier_hash
        elif repo_target.is_file():
            binding = "REPO_RELATIVE_CONTRACT_VIOLATION"
            binding_valid = _sha256(repo_target) == dossier_hash
        else:
            binding = "MISSING"

    sources = payload.get("sources", []) if isinstance(payload, Mapping) else []
    source_rows: list[dict[str, Any]] = []
    retrieval_missing = 0
    embedded_hash_failures = 0
    for source in sources if isinstance(sources, list) else []:
        if not isinstance(source, Mapping):
            source_rows.append({"status": "INVALID_SOURCE_ENTRY"})
            continue
        artifact = source.get("artifact") if isinstance(source.get("artifact"), Mapping) else {}
        online = bool(source.get("url") or source.get("formula_url") or artifact.get("url"))
        retrieval = source.get("retrieved_on") or artifact.get("retrieved_on")
        if online and not retrieval:
            retrieval_missing += 1
        tex = source.get("tex")
        tex_hash = source.get("tex_sha256")
        embedded_ok: bool | None = None
        if isinstance(tex, str) and isinstance(tex_hash, str):
            embedded_ok = hashlib.sha256(tex.encode()).hexdigest() == tex_hash
            if not embedded_ok:
                embedded_hash_failures += 1
        locator = (
            source.get("equation_locator")
            or source.get("locator")
            or source.get("equation_id")
            or source.get("formula_url")
        )
        source_rows.append({
            "content_hash_recorded": bool(tex_hash or artifact.get("bytes_sha256")),
            "embedded_text_hash_valid": embedded_ok,
            "has_equation_locator": bool(locator),
            "online": online,
            "retrieval_date_recorded": bool(retrieval),
        })
    exact_lowering = isinstance(payload.get("lowering_provenance"), Mapping) or isinstance(
        payload.get("package_derivation"), Mapping
    )
    if not exact_lowering:
        # Thermal manifests bind exact source equations to exact catalog rows.
        catalog = _json(package / "source_catalog.json")
        members = catalog.get("members", []) if isinstance(catalog, Mapping) else []
        exact_lowering = bool(members) and all(
            isinstance(member, Mapping) and member.get("source_equation_id")
            for member in members
        )
    strict = (
        binding == "PACKAGE_RELATIVE"
        and binding_valid
        and bool(source_rows)
        and all(row.get("has_equation_locator") for row in source_rows)
        and retrieval_missing == 0
        and embedded_hash_failures == 0
        and exact_lowering
    )
    errors: list[str] = []
    if binding != "PACKAGE_RELATIVE" or not binding_valid:
        errors.append("SOURCE_DOSSIER_NOT_PACKAGE_RELATIVE_AND_HASH_BOUND")
    if retrieval_missing:
        errors.append("ONLINE_SOURCE_RETRIEVAL_DATE_MISSING")
    if embedded_hash_failures:
        errors.append("EMBEDDED_SOURCE_HASH_MISMATCH")
    if not exact_lowering:
        errors.append("MEMBER_LOWERING_MAP_MISSING")
    return {
        "dossier_binding": binding,
        "dossier_hash_valid": binding_valid,
        "errors": errors,
        "exact_member_lowering_recorded": exact_lowering,
        "source_count": len(source_rows),
        "sources": source_rows,
        "strict_source_provenance": strict,
    }


def _walk_statuses(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in {"label", "status"} and isinstance(child, str):
                yield child
            yield from _walk_statuses(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_statuses(child)


def audit_assumptions(package: Path, review: Mapping[str, Any]) -> dict[str, Any]:
    payload = _json(package / "assumptions.json")
    statuses = sorted(set(_walk_statuses(payload)))
    mechanical_gap = any(status in {"NOT_DECLARED", "HUMAN_REQUIRED"} for status in statuses)
    review_status = str(review["assumption_status"])
    return {
        "contract_statuses_observed": statuses,
        "domain_change_note": review["domain_note"],
        "has_mechanical_not_declared_or_human_required": mechanical_gap,
        "independent_assumption_status": review_status,
        "passes_admission": not mechanical_gap and review_status != "HUMAN_REQUIRED",
    }


def _expanded_proposer_view(package: Path) -> dict[str, Any]:
    view = _json(package / "proposer_view.json")
    expanded = dict(view)
    assumptions = view.get("assumptions") if isinstance(view, Mapping) else None
    if isinstance(assumptions, Mapping) and isinstance(assumptions.get("path"), str):
        target = _safe_package_path(package, assumptions["path"])
        if target is not None and target.is_file():
            expanded["referenced_assumptions"] = _json(target)
    return expanded


def audit_projection(package: Path) -> dict[str, Any]:
    expanded = _expanded_proposer_view(package)
    findings = [finding.__dict__ for finding in _leakage_findings({"proposer_view": expanded})]
    package_id = expanded.get("package_id")
    if isinstance(package_id, str):
        leaked = sorted(
            token for token in ("newton", "hermite", "recurrence", "basis")
            if re.search(rf"(?:^|[-_]){token}(?:$|[-_])", package_id, re.I)
        )
        if leaked:
            findings.append({
                "auto_reject": False,
                "code": "PACKAGE_ID_OPERATOR_LEAKAGE",
                "evidence": {
                    "matches": leaked,
                    "path": "proposer_view.package_id",
                },
                "recommendation": "MANUAL_REVIEW",
                "severity": "HIGH",
            })
    findings.sort(key=lambda row: (row["code"], json.dumps(row["evidence"], sort_keys=True)))
    return {
        "expanded_referenced_files": "assumptions.json" in {
            str(value.get("path"))
            for value in expanded.values()
            if isinstance(value, Mapping) and value.get("path")
        },
        "findings": findings,
        "passes_leakage_gate": not findings,
        "projection_sha256": hashlib.sha256(_canonical_bytes(expanded)).hexdigest(),
    }


def _source_texts(package: Path) -> list[str]:
    return [path.read_text(encoding="utf-8").strip() for path in sorted((package / "members").glob("*.txt"))]


def audit_historical_duplicates(
    package: Path,
    references: Sequence[Any],
    forbidden: Sequence[str],
) -> dict[str, Any]:
    manifest = _json(package / "source_manifest.json")
    payload = {
        "case_id": package.name,
        "proposer_view": _expanded_proposer_view(package),
        "public_source": manifest.get("sources", []),
        "source_expressions": _source_texts(package),
        "title": package.name,
    }
    result = audit_case(payload, references, forbidden, top_k=5)
    findings = [finding for finding in result["findings"] if finding["code"] in DUPLICATE_CODES]
    return {
        "findings": findings,
        "passes_historical_duplicate_gate": not findings,
        "top_comparisons": result["top_comparisons"],
    }


def _current_pool_duplicates(package: Path, packages: Sequence[Path]) -> dict[str, Any]:
    mine = [(path.name, path.read_text(encoding="utf-8").strip()) for path in sorted((package / "members").glob("*.txt"))]
    my_manifest = _json(package / "package.json")
    exact: list[dict[str, str]] = []
    renamed: list[dict[str, str]] = []
    source_siblings: list[str] = []
    for other in packages:
        if other == package:
            continue
        other_manifest = _json(other / "package.json")
        if other_manifest.get("source_dossier_id") == my_manifest.get("source_dossier_id"):
            source_siblings.append(other.name)
        for my_name, my_text in mine:
            for other_path in sorted((other / "members").glob("*.txt")):
                other_text = other_path.read_text(encoding="utf-8").strip()
                evidence = {
                    "member": my_name,
                    "other_member": other_path.name,
                    "other_package": other.name,
                }
                if len(strict_normalize(my_text)) >= 16 and strict_normalize(my_text) == strict_normalize(other_text):
                    exact.append(evidence)
                elif (
                    len(alpha_normalize(my_text)) >= 8
                    and alpha_normalize(my_text) == alpha_normalize(other_text)
                ):
                    renamed.append(evidence)
    # Pairs are encountered twice globally but only once within a package row.
    def unique(rows: list[dict[str, str]]) -> list[dict[str, str]]:
        return [dict(items) for items in sorted({tuple(sorted(row.items())) for row in rows})]
    exact = unique(exact)
    renamed = unique(renamed)
    source_siblings = sorted(set(source_siblings))
    return {
        "exact_member_overlaps": exact,
        "renamed_member_overlaps": renamed,
        "same_source_dossier_packages": source_siblings,
        "requires_current_pool_review": bool(exact or renamed or source_siblings),
    }


def _static_m1_observations(package: Path) -> list[str]:
    raw = _json(package / "reference" / "program.json")
    observations: set[str] = set()
    unsupported_root = sorted(set(raw) - {
        "assumption_statuses", "assumptions_used", "depth_note", "grammar_version",
        "instance_maps", "latent_objects", "member_assignments", "node_structures",
        "obligations", "operators", "program_id", "representation_depth",
        "source_members", "unexplained_members",
    })
    if unsupported_root:
        observations.add("PROGRAM_ROOT_FIELDS_UNSUPPORTED:" + ",".join(unsupported_root))
    for latent in raw.get("latent_objects", []):
        if isinstance(latent, Mapping) and "expression" not in latent:
            observations.add("LATENT_EXPRESSION_FIELD_MISSING")
    for operator in raw.get("operators", []):
        if not isinstance(operator, Mapping):
            observations.add("OPERATOR_NOT_OBJECT")
            continue
        if "latent" in operator and "latent_id" not in operator:
            observations.add("OPERATOR_USES_UNSUPPORTED_LATENT_ALIAS")
        if "output" not in operator:
            observations.add("EXECUTABLE_OPERATOR_OUTPUTS_MISSING")
        if not isinstance(operator.get("arguments", {}), Mapping):
            observations.add("OPERATOR_ARGUMENTS_NOT_OBJECT")
    assignments = raw.get("member_assignments")
    if isinstance(assignments, Mapping):
        for value in assignments.values():
            if isinstance(value, str):
                observations.add("MEMBER_ASSIGNMENT_STRING_SHORTHAND_UNSUPPORTED")
            elif isinstance(value, Mapping):
                if "output" not in value:
                    observations.add("EXECUTABLE_ASSIGNMENT_OUTPUTS_MISSING")
                if set(value) - {"operator_ids", "output", "reconstruction_path"}:
                    observations.add("MEMBER_ASSIGNMENT_FIELDS_UNSUPPORTED")
    obligations = raw.get("obligations", [])
    if obligations and all(isinstance(item, str) for item in obligations):
        observations.add("EXECUTABLE_OBLIGATION_OUTPUT_LINKS_MISSING")
    return sorted(observations)


def audit_m1(package: Path) -> dict[str, Any]:
    static = _static_m1_observations(package)
    try:
        loaded = load_case_package(package)
    except PackageLoadError as exc:
        return {
            "compile_failure_codes": [],
            "compile_status": "NOT_RUN",
            "loader_error": exc.code,
            "loader_status": "LOAD_FAILURE",
            "schema_deltas": [],
            "static_schema_observations": static,
        }
    result = compile_program(loaded.program, loaded.context)
    return {
        "compile_failure_codes": list(result.failure_codes),
        "compile_status": result.status,
        "compiled_obligation_count": len(result.obligations),
        "loader_error": None,
        "loader_status": "LOADED",
        "schema_deltas": list(loaded.schema_deltas),
        "static_schema_observations": static,
        "tautological": result.tautological,
    }


def _obligation_session_path(package: Path, item: Mapping[str, Any]) -> Path | None:
    relative = item.get("session_path") or item.get("run_path")
    if isinstance(relative, str):
        return _safe_package_path(package, relative)
    step_path = item.get("step_path")
    if isinstance(step_path, str):
        target = _safe_package_path(package, step_path)
        return target.parents[1] if target is not None else None
    return None


def audit_obligations(package: Path) -> dict[str, Any]:
    payload = _json(package / "reference" / "obligations.json")
    obligations = payload.get("obligations", []) if isinstance(payload, Mapping) else []
    catalog = _json(package / "source_catalog.json")
    member_rows = catalog.get("members", []) if isinstance(catalog, Mapping) else []
    member_hashes: dict[str, set[str]] = {}
    for member in member_rows:
        if isinstance(member, Mapping):
            member_hashes.setdefault(str(member.get("sha256")), set()).add(str(member.get("member_id")))
    expected_members = {
        str(member.get("member_id")) for member in member_rows if isinstance(member, Mapping)
    }
    covered: set[str] = set()
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    receipt_errors: list[str] = []
    for item in obligations if isinstance(obligations, list) else []:
        if not isinstance(item, Mapping):
            receipt_errors.append("OBLIGATION_ENTRY_INVALID")
            continue
        verdict = str(item.get("verdict", "MISSING"))
        counts[verdict] += 1
        current_member = item.get("current_member_id")
        if isinstance(current_member, str):
            covered.add(current_member)
        for hash_key in ("current_sha256", "candidate_sha256"):
            digest = item.get(hash_key)
            if isinstance(digest, str) and digest in member_hashes:
                covered.update(member_hashes[digest])
        tags = item.get("component_tags")
        if isinstance(tags, Mapping):
            covered.update(str(value) for value in tags.values() if str(value) in expected_members)

        session = _obligation_session_path(package, item)
        step_verdicts: list[str] = []
        if session is None or not session.is_dir():
            receipt_errors.append(f"SESSION_MISSING:{item.get('obligation_id')}")
        else:
            for step_path in sorted((session / "steps").glob("step_*.json")):
                step = _json(step_path)
                if isinstance(step, Mapping) and step.get("verdict"):
                    step_verdicts.append(str(step["verdict"]))
            if verdict not in step_verdicts:
                receipt_errors.append(f"SESSION_VERDICT_MISMATCH:{item.get('obligation_id')}")
        for path_key, hash_key in (("current_path", "current_sha256"), ("candidate_path", "candidate_sha256")):
            relative = item.get(path_key)
            expected = item.get(hash_key)
            if isinstance(relative, str) and isinstance(expected, str):
                target = _safe_package_path(package, relative)
                if target is None or not target.is_file() or _sha256(target) != expected:
                    receipt_errors.append(f"OBLIGATION_ARTIFACT_HASH_MISMATCH:{item.get('obligation_id')}:{path_key}")
            elif isinstance(relative, str):
                target = _safe_package_path(package, relative)
                if target is not None and target.is_file():
                    covered.update(member_hashes.get(_sha256(target), set()))
        rows.append({
            "obligation_id": item.get("obligation_id"),
            "required": item.get("required", True),
            "session_verdicts": step_verdicts,
            "verdict": verdict,
        })

    # Explicit byte-identical reconstruction paths cover assignments that do
    # not need a transformation receipt of their own.
    program = _json(package / "reference" / "program.json")
    assignments = program.get("member_assignments", {}) if isinstance(program, Mapping) else {}
    if isinstance(assignments, Mapping):
        for member_id, assignment in assignments.items():
            if not isinstance(assignment, Mapping) or assignment.get("verification") != "BYTE_IDENTICAL_EXACT":
                continue
            source = next((m for m in member_rows if isinstance(m, Mapping) and m.get("member_id") == member_id), None)
            reconstruction = assignment.get("reconstruction")
            if isinstance(source, Mapping) and isinstance(reconstruction, str):
                source_path = _safe_package_path(package, source.get("path"))
                if source_path is not None and source_path.read_text(encoding="utf-8").strip() == reconstruction.strip():
                    covered.add(str(member_id))

    required = [row for row in rows if row["required"]]
    diagnostic_evidence = payload.get("diagnostic_evidence", []) if isinstance(payload, Mapping) else []
    restricted_replays = [
        item for item in diagnostic_evidence
        if isinstance(item, Mapping) and item.get("eligibility") == "INELIGIBLE_RESTRICTED_REPLAY"
    ]
    return {
        "all_required_zero": bool(required) and all(row["verdict"] == "ZERO" for row in required),
        "covered_members": sorted(covered),
        "member_coverage_complete": covered == expected_members,
        "missing_members": sorted(expected_members - covered),
        "receipt_errors": sorted(set(receipt_errors)),
        "required_obligation_count": len(required),
        "required_verdict_counts": dict(sorted(Counter(row["verdict"] for row in required).items())),
        "restricted_replays": restricted_replays,
        "rows": rows,
    }


def _depth_review(review: Mapping[str, Any], claimed: Any) -> dict[str, Any]:
    return {
        "claimed_depth": claimed,
        "depth_assessment": review["depth_assessment"],
        "independent_depth": review["independent_depth"],
        "named_primitive_giveaway": review["named_primitive_giveaway"],
        "non_tautology": review["non_tautology"],
        "review_flags": review["review_flags"],
    }


def _dispositions(row: Mapping[str, Any]) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    values: set[str] = set()
    if not row["assumptions"]["passes_admission"]:
        values.add("HUMAN_REQUIRED")
        reasons.append("ASSUMPTION_GATE_NOT_AUTHORIZED")
    if row["lowering_scope"] == "FINITE_INDEX_DIAGNOSTIC":
        values.add("DIAGNOSTIC_ONLY")
        reasons.append("FINITE_INDEX_REPLAY_CANNOT_ENTER_FAIR_COMPARISON")
    if not row["obligations"]["all_required_zero"]:
        values.add("PROOF_REQUIRED")
        reasons.append("NOT_ALL_REQUIRED_OBLIGATIONS_ZERO")
    if (
        not row["manifest"]["strict_rps_case_package_v1"]
        or not row["source_provenance"]["strict_source_provenance"]
        or row["m1"]["compile_status"] != "COMPILED"
        or not row["obligations"]["member_coverage_complete"]
        or row["obligations"]["receipt_errors"]
    ):
        values.add("SCHEMA_GAP")
        reasons.append("PACKAGE_OR_M1_OR_RECEIPT_GATE_FAILED")
    if not row["projection"]["passes_leakage_gate"]:
        values.add("LEAKAGE_REVIEW")
        reasons.append("PROPOSER_PROJECTION_LEAKAGE_FINDING")
    if (
        not row["historical_duplicates"]["passes_historical_duplicate_gate"]
        or row["current_pool_duplicates"]["requires_current_pool_review"]
    ):
        values.add("DUPLICATE_REVIEW")
        reasons.append("HISTORICAL_OR_CURRENT_POOL_DUPLICATE_REVIEW")
    depth_assessment = row["depth"]["depth_assessment"]
    if depth_assessment in {"DEPTH_DOWNGRADED", "NOT_ADMISSIBLE_AS_R8"}:
        values.add("DEPTH_DOWNGRADED")
        reasons.append("INDEPENDENT_DEPTH_DOES_NOT_SUPPORT_PACKAGE_LABEL")
    if str(row["depth"]["non_tautology"]).startswith("FAIL"):
        values.add("REJECT_TAUTOLOGY")
        reasons.append("NON_TAUTOLOGY_GATE_FAILED")

    hard_gate = not values.intersection({
        "HUMAN_REQUIRED", "DIAGNOSTIC_ONLY", "PROOF_REQUIRED", "SCHEMA_GAP",
        "LEAKAGE_REVIEW", "DUPLICATE_REVIEW", "REJECT_TAUTOLOGY",
    })
    if hard_gate and row["parser"]["all_machine_expressions_parse"]:
        values.add("ADMISSION_READY")
    if not row["parser"]["all_machine_expressions_parse"]:
        values.add("SCHEMA_GAP")
        reasons.append("FROZEN_PARSER_FAILURE")
    return [value for value in DISPOSITION_ORDER if value in values], sorted(set(reasons))


def audit_repository(root: Path | str | None = None) -> dict[str, Any]:
    root = Path(root or _repo_root()).resolve()
    review_path = root / "research" / "representation_program_search" / "audits" / "package_admission" / "reviews.json"
    review_payload = _json(review_path)
    reviews = review_payload["reviews"]
    packages = discover_packages(root)
    if set(reviews) != {package.name for package in packages}:
        raise ValueError("REVIEW_COVERAGE_MISMATCH")
    references = discover_reference_corpus(root)
    forbidden = historical_ids(root, references)
    rows: list[dict[str, Any]] = []
    for package in packages:
        manifest = _json(package / "package.json")
        review = reviews[package.name]
        row: dict[str, Any] = {
            "assumptions": audit_assumptions(package, review),
            "audited_input_sha256": _sha256(package / "package.json"),
            "current_pool_duplicates": _current_pool_duplicates(package, packages),
            "depth": _depth_review(review, manifest.get("audited_depth")),
            "family": package.parent.name,
            "historical_duplicates": audit_historical_duplicates(package, references, forbidden),
            "lowering_scope": manifest.get("lowering_scope"),
            "m1": audit_m1(package),
            "manifest": audit_manifest(package, manifest),
            "obligations": audit_obligations(package),
            "package_id": package.name,
            "package_status": manifest.get("package_status"),
            "parser": audit_parser(package),
            "path": _relative(root, package),
            "projection": audit_projection(package),
            "source_dossier_id": manifest.get("source_dossier_id"),
            "source_provenance": audit_source(package, root),
        }
        row["dispositions"], row["ineligibility_reasons"] = _dispositions(row)
        row["fair_comparison_eligible"] = row["dispositions"] == ["ADMISSION_READY"]
        rows.append(row)

    ready = [row["package_id"] for row in rows if row["fair_comparison_eligible"]]
    slots: dict[str, dict[str, Any]] = {}
    slot_depths = {
        "R2": {"R2"},
        "R3": {"R3"},
        "R4_R5": {"R4", "R5", "R5_FIXED_INSTANCE"},
        "R6": {"R6"},
    }
    for slot, depths in slot_depths.items():
        candidates = [row["package_id"] for row in rows if row["depth"]["independent_depth"] in depths]
        admitted = [package_id for package_id in candidates if package_id in ready]
        slots[slot] = {
            "admission_ready": admitted,
            "candidate_packages": candidates,
            "status": "AVAILABLE" if admitted else "MISSING",
            "missing_gate": None if admitted else (
                "NO_INDEPENDENT_DEPTH_CANDIDATE" if not candidates else "ALL_CANDIDATES_FAIL_ADMISSION_GATES"
            ),
        }
    disposition_counts = Counter(value for row in rows for value in row["dispositions"])
    return {
        "admission_ready_count": len(ready),
        "admission_ready_packages": ready,
        "audit_version": AUDIT_VERSION,
        "dev_calibration_recommendation": {
            "negative_trap": {
                "status": "EVALUATOR_ONLY_SEPARATE",
                "missing_gate": None,
                "note": "The M10 adversarial falsifier is an evaluator-only control, not an admissible benchmark candidate.",
            },
            "selected_packages": ready,
            "slots": slots,
        },
        "disposition_counts": dict(sorted(disposition_counts.items())),
        "fair_comparison_package_count": len(ready),
        "frozen_parser_modified": False,
        "gold_programs_modified": False,
        "package_count": len(rows),
        "packages": rows,
        "reference_document_count": len(references),
        "review_policy_path": _relative(root, review_path),
        "review_policy_sha256": _sha256(review_path),
        "schema_repair_sufficient_for_admission": False,
        "schema_repair_limit": (
            "Repairing package/M1 schemas alone cannot cure required UNKNOWN verdicts, "
            "unauthorized assumptions, depth downgrades, duplicate review, proposer leakage, "
            "or finite-index diagnostic scope."
        ),
        "selects_test": False,
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    lines = [
        "# Post-package admission, depth, and leakage audit",
        "",
        f"Policy: `{report['audit_version']}`.",
        "",
        "This is a fail-closed admission audit, not a benchmark split or method result. "
        "`PACKAGE_READY` remains necessary but is not treated as `ADMISSION_READY`.",
        "",
        "## Outcome",
        "",
        f"- Packages audited: {report['package_count']}",
        f"- `ADMISSION_READY`: {report['admission_ready_count']}",
        f"- Fair-comparison eligible: {report['fair_comparison_package_count']}",
        f"- Frozen reference documents checked: {report['reference_document_count']}",
        "",
        "| package | package status | claimed | independent | scope | dispositions | fair? |",
        "|---|---|---:|---:|---|---|---:|",
    ]
    for row in report["packages"]:
        lines.append(
            f"| `{row['package_id']}` | `{row['package_status']}` | "
            f"{row['depth']['claimed_depth']} | {row['depth']['independent_depth']} | "
            f"`{row['lowering_scope']}` | {', '.join(f'`{d}`' for d in row['dispositions'])} | "
            f"{'yes' if row['fair_comparison_eligible'] else 'no'} |"
        )
    lines.extend((
        "",
        "## Decisive findings",
        "",
        "- All six thermal packages load through M1 but fail compilation at the first missing executable output; the audit records every loader schema delta and never repairs links.",
        "- All four matrix/differentiable-physics packages and all three response/tensor packages fail the M1 loader with `PACKAGE_ARTIFACT_MANIFEST_INVALID` because they use `artifacts`, not the contract's `artifact_hashes` list.",
        "- The oscillator's required complex-domain Piecewise obligation is `UNKNOWN`; its real-domain ZERO replay remains explicitly ineligible.",
        "- Both tensor packages are `FINITE_INDEX_DIAGNOSTIC` and cannot enter R8 fair comparison.",
        "- The fixed AB/BA package is independently R2 (one Newton divided difference plus linear reconstruction), not R6.",
        "- The scalar Feshbach package is independently R0/CSE-baseline class (one exposed denominator kernel plus linear combinations), not R6.",
        "- Thermal-10 is `HUMAN_REQUIRED`: it repairs a previously rejected domain contract without a recorded human decision.",
        "- Schema repair alone cannot admit the pool: proof, assumption, depth, duplicate, leakage, and diagnostic-scope gates remain independent.",
        "",
        "## DEV calibration recommendation",
        "",
        "No package is recommended. Missing slots are reported rather than filled from ineligible artifacts:",
        "",
        "| slot | status | candidate packages | missing gate |",
        "|---|---|---|---|",
    ))
    for slot, detail in report["dev_calibration_recommendation"]["slots"].items():
        candidates = ", ".join(f"`{item}`" for item in detail["candidate_packages"]) or "none"
        lines.append(f"| {slot} | `{detail['status']}` | {candidates} | `{detail['missing_gate']}` |")
    lines.extend((
        "",
        "The M10 adversarial negative trap remains an evaluator-only falsifier, separate from benchmark admission; it is not a benchmark candidate. No TEST task was selected.",
        "",
        "## Interpretation boundary",
        "",
        "Depth review is independent of package labels. Duplicate similarity is a review gate, not an automatic scientific rejection. ZERO receipts certify only their exact current/candidate texts and declared lowering scope; they do not repair Program IR, source-provenance, leakage, or depth defects.",
        "",
    ))
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=_repo_root())
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    report = audit_repository(args.root)
    base = args.root / "research" / "representation_program_search" / "audits" / "package_admission"
    json_path = base / "PACKAGE_ADMISSION_AUDIT.json"
    md_path = base / "PACKAGE_ADMISSION_AUDIT.md"
    json_bytes = _canonical_bytes(report)
    md_bytes = render_markdown(report).encode()
    if args.check:
        return 0 if json_path.read_bytes() == json_bytes and md_path.read_bytes() == md_bytes else 1
    if args.write:
        json_path.write_bytes(json_bytes)
        md_path.write_bytes(md_bytes)
    else:
        print(json_bytes.decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
