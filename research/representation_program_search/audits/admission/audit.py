"""Deterministic, fail-closed admission audit for newly mined RPS dossiers.

This tool does not admit tasks to a benchmark or modify dossiers.  It checks
the evidence currently present in the miner tree and combines those checks
with the bounded scientific/depth reviews in ``reviews.json``.  In
particular, ``expression_sketch`` is never treated as verifier input.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from symbolic_compactification import load_expression


AUDIT_VERSION = "rps-admission-audit-v1"
CLUSTERS = ("matrix", "thermal", "response", "tensor", "diffphys")
PRIMARY_STATUSES = (
    "ADMISSION_CANDIDATE",
    "PACKAGING_GAP",
    "PROBLEM_UNDERSPECIFIED",
    "DUPLICATE_REVIEW",
    "REJECT",
)
DEPTH_ASSESSMENTS = (
    "PLAUSIBLE",
    "NEEDS_DOWNGRADE",
    "NOT_OPERATIONAL_AT_PROPOSED_DEPTH",
)
PARSER_FITS = (
    "REPRESENTABLE_AFTER_PACKAGING",
    "REPRESENTABLE_ONLY_AFTER_FIXED_INSTANCE_LOWERING",
    "NOT_REPRESENTABLE_UNDER_FROZEN_PARSER",
)
ASSUMPTION_FIELDS = (
    "symbol_assumptions",
    "function_domains",
    "nonzero_conditions",
    "positivity_conditions",
    "real_valued_functions",
    "analytic_domains",
    "branch_conventions",
    "limit_domains",
    "source_provenance",
    "derived_conditions",
)
PREDICATE_FIELDS = (
    "nonzero_conditions",
    "positivity_conditions",
    "analytic_domains",
    "limit_domains",
    "derived_conditions",
)
ALLOWED_PREDICATE_LABELS = {"DECLARED", "DERIVED", "NOT_DECLARED"}

HERE = Path(__file__).resolve().parent
RESEARCH_ROOT = HERE.parents[1]
CASES_ROOT = RESEARCH_ROOT / "cases"
REVIEWS_PATH = HERE / "reviews.json"
JSON_OUTPUT = HERE / "ADMISSION_AUDIT.json"
MARKDOWN_OUTPUT = HERE / "ADMISSION_AUDIT.md"


class AuditError(RuntimeError):
    """A deterministic audit contract failure."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"UNREADABLE_JSON:{path}:{type(exc).__name__}") from None
    if not isinstance(value, dict):
        raise AuditError(f"JSON_NOT_OBJECT:{path}")
    return value


def discover_dossiers(cases_root: Path = CASES_ROOT) -> list[tuple[str, Path, dict[str, Any]]]:
    """Load exactly the non-skeptic dossiers listed by each miner index."""
    rows: list[tuple[str, Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for cluster in CLUSTERS:
        cluster_dir = cases_root / cluster
        index = _load_object(cluster_dir / "index.json")
        entries = index.get("dossiers")
        if not isinstance(entries, list):
            raise AuditError(f"INDEX_DOSSIERS_MALFORMED:{cluster}")
        if index.get("count") != len(entries):
            raise AuditError(f"INDEX_COUNT_MISMATCH:{cluster}")
        listed_files: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict) or not isinstance(entry.get("json"), str):
                raise AuditError(f"INDEX_ENTRY_MALFORMED:{cluster}")
            listed_files.add(entry["json"])
            path = cluster_dir / entry["json"]
            dossier = _load_object(path)
            case_id = dossier.get("case_id")
            if not isinstance(case_id, str) or not case_id:
                raise AuditError(f"CASE_ID_MISSING:{path}")
            if entry.get("case_id") != case_id:
                raise AuditError(f"INDEX_CASE_ID_MISMATCH:{case_id}")
            if case_id in seen:
                raise AuditError(f"DUPLICATE_CASE_ID:{case_id}")
            seen.add(case_id)
            rows.append((cluster, path, dossier))
        actual_files = {p.name for p in cluster_dir.glob("*.json") if p.name != "index.json"}
        if listed_files != actual_files:
            raise AuditError(f"INDEX_FILE_SET_MISMATCH:{cluster}")
    return sorted(rows, key=lambda row: row[2]["case_id"])


def load_reviews(path: Path = REVIEWS_PATH) -> tuple[dict[str, Any], str]:
    payload = _load_object(path)
    cases = payload.get("cases")
    if not isinstance(cases, dict):
        raise AuditError("REVIEWS_CASES_MALFORMED")
    for case_id, review in cases.items():
        if not isinstance(review, dict):
            raise AuditError(f"REVIEW_MALFORMED:{case_id}")
        if review.get("depth_assessment") not in DEPTH_ASSESSMENTS:
            raise AuditError(f"REVIEW_DEPTH_INVALID:{case_id}")
        if review.get("parser_fit") not in PARSER_FITS:
            raise AuditError(f"REVIEW_PARSER_FIT_INVALID:{case_id}")
        if not isinstance(review.get("parser_blockers"), list):
            raise AuditError(f"REVIEW_PARSER_BLOCKERS_MALFORMED:{case_id}")
        if not isinstance(review.get("duplicate_with"), list):
            raise AuditError(f"REVIEW_DUPLICATES_MALFORMED:{case_id}")
        for key in ("audited_depth", "assumption_gap", "hard_reject", "note"):
            if not isinstance(review.get(key), str):
                raise AuditError(f"REVIEW_FIELD_MALFORMED:{case_id}:{key}")
    return cases, _sha256(path)


def _assumption_contract_status(dossier: dict[str, Any]) -> tuple[str, list[str]]:
    contract = dossier.get("assumption_contract")
    if not isinstance(contract, dict):
        return "MALFORMED", ["ASSUMPTION_CONTRACT_MISSING"]
    issues: list[str] = []
    for field in ASSUMPTION_FIELDS:
        if field not in contract:
            issues.append(f"ASSUMPTION_FIELD_MISSING:{field}")
    for field in PREDICATE_FIELDS:
        values = contract.get(field, [])
        if not isinstance(values, list):
            issues.append(f"PREDICATE_LIST_MALFORMED:{field}")
            continue
        for offset, pred in enumerate(values):
            if not isinstance(pred, dict):
                issues.append(f"PREDICATE_MALFORMED:{field}:{offset}")
                continue
            label = pred.get("label")
            if label not in ALLOWED_PREDICATE_LABELS:
                issues.append(f"PREDICATE_LABEL_INVALID:{field}:{offset}")
            if label == "NOT_DECLARED":
                issues.append(f"NOT_DECLARED:{field}:{offset}")
            if not str(pred.get("source", "")).strip():
                issues.append(f"PREDICATE_SOURCE_MISSING:{field}:{offset}")
    return ("COMPLETE_AS_WRITTEN" if not issues else "INCOMPLETE", issues)


def _scoped_path(base: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise AuditError("ARTIFACT_PATH_INVALID")
    target = (base / relative).resolve()
    try:
        target.relative_to(base.resolve())
    except ValueError:
        raise AuditError("ARTIFACT_PATH_ESCAPES_CASE_DIRECTORY") from None
    return target


def _provenance_status(
    dossier: dict[str, Any], dossier_path: Path
) -> tuple[str, int, int, list[str]]:
    contract = dossier.get("assumption_contract")
    sources = contract.get("source_provenance", []) if isinstance(contract, dict) else []
    nonempty = [s for s in sources if isinstance(s, str) and s.strip()]
    if not nonempty or not str(dossier.get("public_source", "")).strip():
        return "MISSING", len(nonempty), 0, ["SOURCE_CITATION_MISSING"]
    artifacts = dossier.get("source_artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        return "CITATIONS_PRESENT_SOURCE_NOT_FROZEN", len(nonempty), 0, []
    issues: list[str] = []
    verified = 0
    for offset, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            issues.append(f"SOURCE_ARTIFACT_MALFORMED:{offset}")
            continue
        relative = artifact.get("path")
        digest = artifact.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            issues.append(f"SOURCE_ARTIFACT_SHA256_INVALID:{offset}")
            continue
        try:
            path = _scoped_path(dossier_path.parent, relative)
        except AuditError as exc:
            issues.append(f"SOURCE_ARTIFACT_PATH_INVALID:{offset}:{exc}")
            continue
        if not path.is_file():
            issues.append(f"SOURCE_ARTIFACT_MISSING:{offset}")
            continue
        if _sha256(path) != digest:
            issues.append(f"SOURCE_ARTIFACT_HASH_MISMATCH:{offset}")
            continue
        verified += 1
    if issues or verified == 0:
        return "SOURCE_ARTIFACT_REFERENCES_INVALID", len(nonempty), verified, issues
    return "FROZEN_ARTIFACT_REFERENCES_PRESENT", len(nonempty), verified, []


def _machine_package(dossier: dict[str, Any], dossier_path: Path) -> dict[str, Any]:
    """Inspect an explicit package if present; never parse expression_sketch."""
    package = dossier.get("admission_package")
    if not isinstance(package, dict):
        return {
            "status": "ABSENT",
            "member_count": 0,
            "obligation_count": 0,
            "parse_failures": [],
            "reason": "NO_ADMISSION_PACKAGE; expression_sketch is context, not verifier input",
        }
    member_files = package.get("member_files")
    obligation_files = package.get("obligation_files")
    symbols_file = package.get("symbols_file")
    if not isinstance(member_files, list) or len(member_files) < 2:
        return {
            "status": "MALFORMED",
            "member_count": len(member_files) if isinstance(member_files, list) else 0,
            "obligation_count": len(obligation_files) if isinstance(obligation_files, list) else 0,
            "parse_failures": [],
            "reason": "AT_LEAST_TWO_MEMBER_FILES_REQUIRED",
        }
    if not isinstance(obligation_files, list) or not obligation_files:
        return {
            "status": "MALFORMED",
            "member_count": len(member_files),
            "obligation_count": 0,
            "parse_failures": [],
            "reason": "OBLIGATION_FILES_REQUIRED",
        }
    if not isinstance(symbols_file, str):
        return {
            "status": "MALFORMED",
            "member_count": len(member_files),
            "obligation_count": len(obligation_files),
            "parse_failures": [],
            "reason": "SYMBOLS_FILE_REQUIRED",
        }
    base = dossier_path.parent
    try:
        namespace = _load_object(_scoped_path(base, symbols_file))
    except AuditError as exc:
        return {
            "status": "UNPARSEABLE",
            "member_count": len(member_files),
            "obligation_count": len(obligation_files),
            "parse_failures": [str(exc)],
            "reason": "SYMBOL_NAMESPACE_UNREADABLE",
        }
    symbols = namespace.get("symbols", namespace)
    functions = namespace.get("functions") if isinstance(namespace, dict) else None
    failures: list[str] = []
    for rel in member_files + obligation_files:
        if not isinstance(rel, str):
            failures.append("NON_STRING_EXPRESSION_PATH")
            continue
        try:
            path = _scoped_path(base, rel)
        except AuditError as exc:
            failures.append(f"{rel}:{exc}")
            continue
        try:
            load_expression(path, symbols, functions=functions)
        except Exception as exc:  # AdapterError is intentionally rendered as evidence.
            failures.append(f"{rel}:{exc}")
    return {
        "status": "PARSEABLE" if not failures else "UNPARSEABLE",
        "member_count": len(member_files),
        "obligation_count": len(obligation_files),
        "parse_failures": failures,
        "reason": "" if not failures else "FROZEN_PARSER_REJECTED_PACKAGE",
    }


def _nonfabricated_status(dossier: dict[str, Any], provenance_status: str) -> str:
    blob = " ".join(
        str(dossier.get(key, "")) for key in ("domain", "title", "notes")
    ).lower()
    if dossier.get("synthetic") is True or any(word in blob for word in (
        "author-constructed toy", "fabricated toy", "no scientific source"
    )):
        return "FABRICATION_SIGNAL"
    if provenance_status == "MISSING":
        return "UNCONFIRMED_NO_PROVENANCE"
    return "NO_FABRICATION_SIGNAL_CITATIONS_NOT_SOURCE_AUTHENTICATED"


def _primary_status(
    review: dict[str, Any],
    assumption_status: str,
    assumption_issues: list[str],
    provenance_status: str,
    nonfabricated_status: str,
    package: dict[str, Any],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if review["hard_reject"]:
        return "REJECT", ["HARD_REJECT:" + review["hard_reject"]]
    if nonfabricated_status.startswith("FABRICATION"):
        return "REJECT", ["FABRICATION_SIGNAL"]
    if review["assumption_gap"]:
        return "PROBLEM_UNDERSPECIFIED", ["MANUAL_ASSUMPTION_GAP:" + review["assumption_gap"]]
    if assumption_status != "COMPLETE_AS_WRITTEN":
        return "PROBLEM_UNDERSPECIFIED", assumption_issues
    if review["duplicate_with"]:
        return "DUPLICATE_REVIEW", ["DUPLICATE_WITH:" + ref for ref in review["duplicate_with"]]
    if provenance_status != "FROZEN_ARTIFACT_REFERENCES_PRESENT":
        reasons.append("SCIENTIFIC_SOURCE_NOT_FROZEN")
    if package["status"] != "PARSEABLE":
        reasons.append("MACHINE_PACKAGE_" + package["status"])
    if review["parser_fit"] != "REPRESENTABLE_AFTER_PACKAGING":
        reasons.append(review["parser_fit"])
    if reasons:
        return "PACKAGING_GAP", reasons
    return "ADMISSION_CANDIDATE", []


def build_audit(
    cases_root: Path = CASES_ROOT,
    reviews_path: Path = REVIEWS_PATH,
) -> dict[str, Any]:
    dossiers = discover_dossiers(cases_root)
    reviews, reviews_sha = load_reviews(reviews_path)
    dossier_ids = {dossier["case_id"] for _, _, dossier in dossiers}
    if set(reviews) != dossier_ids:
        missing = sorted(dossier_ids - set(reviews))
        extra = sorted(set(reviews) - dossier_ids)
        raise AuditError(f"REVIEW_COVERAGE_MISMATCH:missing={missing}:extra={extra}")

    rows: list[dict[str, Any]] = []
    for cluster, path, dossier in dossiers:
        case_id = dossier["case_id"]
        review = reviews[case_id]
        assumption_status, assumption_issues = _assumption_contract_status(dossier)
        provenance_status, source_count, source_artifact_count, provenance_issues = (
            _provenance_status(dossier, path)
        )
        nonfabricated = _nonfabricated_status(dossier, provenance_status)
        package = _machine_package(dossier, path)
        status, reasons = _primary_status(
            review,
            assumption_status,
            assumption_issues,
            provenance_status,
            nonfabricated,
            package,
        )
        if status not in PRIMARY_STATUSES:
            raise AuditError(f"PRIMARY_STATUS_INVALID:{case_id}:{status}")
        rows.append({
            "case_id": case_id,
            "cluster": cluster,
            "dossier_path": path.relative_to(RESEARCH_ROOT.parent.parent).as_posix(),
            "dossier_sha256": _sha256(path),
            "primary_status": status,
            "status_reasons": reasons,
            "proposed_ladder": dossier.get("proposed_ladder", ""),
            "depth_assessment": review["depth_assessment"],
            "audited_depth": review["audited_depth"],
            "depth_note": review["note"],
            "machine_package": package,
            "parser_fit": review["parser_fit"],
            "parser_blockers": review["parser_blockers"],
            "assumption_contract_status": assumption_status,
            "assumption_issues": assumption_issues,
            "manual_assumption_gap": review["assumption_gap"],
            "provenance_status": provenance_status,
            "source_citation_count": source_count,
            "frozen_source_artifact_count": source_artifact_count,
            "provenance_issues": provenance_issues,
            "nonfabricated_status": nonfabricated,
            "duplicate_with": review["duplicate_with"],
            "hard_reject": review["hard_reject"],
        })

    status_counts = Counter(row["primary_status"] for row in rows)
    depth_counts = Counter(row["depth_assessment"] for row in rows)
    parser_counts = Counter(row["parser_fit"] for row in rows)
    cluster_counts = Counter(row["cluster"] for row in rows)
    input_hash = hashlib.sha256(
        "\n".join(f"{row['case_id']}:{row['dossier_sha256']}" for row in rows).encode("utf-8")
    ).hexdigest()
    return {
        "audit_version": AUDIT_VERSION,
        "scope": "all non-skeptic Representation Program Search miner dossiers",
        "input_tree_sha256": input_hash,
        "reviews_sha256": reviews_sha,
        "policy": {
            "expression_sketch_is_verifier_input": False,
            "source_citations_are_source_authentication": False,
            "admission_requires_parseable_machine_package": True,
            "unknown_or_missing_evidence_fails_closed": True,
            "primary_status_precedence": [
                "REJECT", "PROBLEM_UNDERSPECIFIED", "DUPLICATE_REVIEW",
                "PACKAGING_GAP", "ADMISSION_CANDIDATE"
            ],
        },
        "summary": {
            "total": len(rows),
            "by_status": {key: status_counts.get(key, 0) for key in PRIMARY_STATUSES},
            "by_depth_assessment": {
                key: depth_counts.get(key, 0) for key in DEPTH_ASSESSMENTS
            },
            "by_parser_fit": {key: parser_counts.get(key, 0) for key in PARSER_FITS},
            "by_cluster": {key: cluster_counts.get(key, 0) for key in CLUSTERS},
            "machine_packages_parseable": sum(
                row["machine_package"]["status"] == "PARSEABLE" for row in rows
            ),
            "frozen_source_artifact_references": sum(
                row["provenance_status"] == "FROZEN_ARTIFACT_REFERENCES_PRESENT"
                for row in rows
            ),
        },
        "cases": rows,
    }


def render_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# Representation-search admission audit",
        "",
        f"Audit version: `{audit['audit_version']}`",
        "",
        f"Input tree SHA-256: `{audit['input_tree_sha256']}`",
        "",
        f"Review policy SHA-256: `{audit['reviews_sha256']}`",
        "",
        "This is an admission audit, not a benchmark split or scientific result. "
        "It does not edit dossiers, change the grammar/parser/verifier, or admit any case.",
        "",
        "## Outcome",
        "",
        f"Audited {summary['total']} non-skeptic dossiers. `expression_sketch` is context only; "
        "it is never accepted as a machine expression. No dossier supplies an explicit "
        "admission package of parseable member and obligation files, and no cited source is "
        "frozen as a repository artifact with a source reference.",
        "",
        "| status | count |",
        "|---|---:|",
    ]
    for status in PRIMARY_STATUSES:
        lines.append(f"| `{status}` | {summary['by_status'][status]} |")
    lines += [
        "",
        "`DUPLICATE_REVIEW` and `REJECT` have precedence over packaging so those problems "
        "remain visible even though the corresponding dossiers also lack machine packages. "
        "`PROBLEM_UNDERSPECIFIED` is reserved for verifier-domain assumptions, not proof gaps.",
        "",
        "## Depth audit",
        "",
        "| assessment | count |",
        "|---|---:|",
    ]
    for status in DEPTH_ASSESSMENTS:
        lines.append(f"| `{status}` | {summary['by_depth_assessment'][status]} |")
    lines += [
        "",
        "Depth is an admission plausibility judgment, never a certified representation result. "
        "A `PLAUSIBLE` R-level still requires a complete program and ZERO obligations.",
        "",
        "## Per-case decisions",
        "",
        "| case | cluster | primary status | proposed -> audited | parser fit | key issue |",
        "|---|---|---|---|---|---|",
    ]
    for row in audit["cases"]:
        issue = row["status_reasons"][0] if row["status_reasons"] else "none"
        issue = issue.replace("|", "\\|").replace("\n", " ")
        if len(issue) > 150:
            issue = issue[:147] + "..."
        lines.append(
            f"| `{row['case_id']}` | {row['cluster']} | `{row['primary_status']}` | "
            f"{row['proposed_ladder']} -> {row['audited_depth']} "
            f"({row['depth_assessment']}) | `{row['parser_fit']}` | {issue} |"
        )
    lines += [
        "",
        "## Interpretation boundaries",
        "",
        "- A citation present in a dossier is not treated as a frozen or content-authenticated source.",
        "- Absence of a fabrication signal is not proof that a source transcription is correct.",
        "- Fixed-instance lowering may support a fixed-dimensional task; it must be labeled as such "
        "and cannot prove a symbolic-dimension identity.",
        "- Declaring an unsupported special function as an undefined function can make text parse, "
        "but does not give the verifier the semantics needed to certify its identity.",
        "- No case in this artifact is selected for DEV, TEST, or CHALLENGE.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(audit: dict[str, Any]) -> None:
    JSON_OUTPUT.write_text(
        json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    MARKDOWN_OUTPUT.write_text(render_markdown(audit), encoding="utf-8")


def check_outputs(audit: dict[str, Any]) -> None:
    expected_json = json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    expected_md = render_markdown(audit)
    if not JSON_OUTPUT.is_file() or JSON_OUTPUT.read_text(encoding="utf-8") != expected_json:
        raise AuditError("ADMISSION_AUDIT_JSON_STALE")
    if not MARKDOWN_OUTPUT.is_file() or MARKDOWN_OUTPUT.read_text(encoding="utf-8") != expected_md:
        raise AuditError("ADMISSION_AUDIT_MARKDOWN_STALE")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write deterministic JSON/Markdown")
    mode.add_argument("--check", action="store_true", help="check committed outputs are current")
    args = parser.parse_args(argv)
    audit = build_audit()
    if args.write:
        write_outputs(audit)
    elif args.check:
        check_outputs(audit)
    else:
        print(json.dumps(audit["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
