"""Gold-free duplicate/leakage audit for the two gap-fill candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research.representation_program_search.audits.leakage.audit import (
    POLICY_VERSION,
    CorpusDocument,
    audit_case,
    discover_new_dossiers,
    discover_reference_corpus,
    historical_ids,
    source_formulas,
    source_identifiers,
)

from .validate import ROOT as GAP_ROOT
from .validate import package_dirs


REPO_ROOT = Path(__file__).resolve().parents[4]


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root is not an object")
    return value


def _current_case_documents(root: Path) -> list[CorpusDocument]:
    documents: list[CorpusDocument] = []
    for path, payload in discover_new_dossiers(root):
        formulas = source_formulas(payload)
        documents.append(
            CorpusDocument(
                document_id=str(payload["case_id"]),
                path=str(path.relative_to(root)),
                partition="CURRENT_MINED_CASE",
                title=str(payload.get("title", "")),
                formulas=formulas,
                identity_text="\n".join((str(payload.get("title", "")), *formulas)),
                source_ids=source_identifiers(payload),
            )
        )
    return documents


def _existing_package_documents(root: Path) -> list[CorpusDocument]:
    packages_root = root / "research/representation_program_search/packages"
    documents: list[CorpusDocument] = []
    for manifest_path in sorted(packages_root.glob("**/package.json")):
        package = manifest_path.parent
        if package.parent == GAP_ROOT:
            continue
        try:
            manifest = _json(manifest_path)
            catalog = _json(package / "source_catalog.json")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            continue
        formulas: list[str] = []
        for row in catalog.get("members", []):
            if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                continue
            member_path = package / row["path"]
            try:
                formulas.append(member_path.read_text(encoding="utf-8").strip())
            except (OSError, UnicodeError):
                continue
        if not formulas:
            continue
        try:
            source_manifest = _json(package / "source_manifest.json")
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError):
            source_manifest = {}
        payload = {
            "sources": source_manifest.get("sources", []),
            "source_provenance": source_manifest.get("source_provenance", []),
        }
        package_id = str(manifest.get("package_id", package.name))
        documents.append(
            CorpusDocument(
                document_id=package_id,
                path=str(manifest_path.relative_to(root)),
                partition="CURRENT_PACKAGE",
                title=package_id,
                formulas=tuple(formulas),
                identity_text="\n".join((package_id, *formulas)),
                source_ids=source_identifiers(payload),
            )
        )
    return documents


def audit_candidates(root: Path = REPO_ROOT) -> dict[str, Any]:
    references = discover_reference_corpus(root)
    references.extend(_current_case_documents(root))
    references.extend(_existing_package_documents(root))
    forbidden = historical_ids(root, references)
    rows: list[dict[str, Any]] = []
    for package in package_dirs(GAP_ROOT):
        manifest = _json(package / "package.json")
        catalog = _json(package / "source_catalog.json")
        formulas = [
            (package / row["path"]).read_text(encoding="utf-8").strip()
            for row in catalog["members"]
        ]
        source_manifest = _json(package / "source_manifest.json")
        payload = {
            "case_id": package.name,
            "source_expressions": formulas,
            "sources": source_manifest.get("sources", []),
            "proposer_view": _json(package / "proposer_view.json"),
            "_audit_path": str(package.relative_to(root)),
        }
        result = audit_case(payload, references, forbidden, top_k=8)
        blocking = [
            item
            for item in result["findings"]
            if item["code"] in {
                "EXACT_DUPLICATE_IDENTITY_RISK",
                "RENAMED_IDENTITY_RISK",
                "GRAMMAR_SYNTAX_LEAKAGE",
                "HIDDEN_MEMBER_ROLE_LEAKAGE",
                "SEALED_GUO_REFERENCE",
                "TRIVIAL_CSE",
                "FIRST_ORDER_LGG_ONLY",
            }
        ]
        result["blocking_findings"] = blocking
        result["candidate_disposition"] = (
            "FAIL_CLOSED" if blocking else "PASS_TO_INDEPENDENT_MANUAL_REVIEW"
        )
        result["package_status"] = manifest["package_status"]
        rows.append(result)
    return {
        "audit_scope": {
            "current_mined_cases": sum(item.partition == "CURRENT_MINED_CASE" for item in references),
            "current_packages": sum(item.partition == "CURRENT_PACKAGE" for item in references),
            "historical_documents": sum(item.partition not in {"CURRENT_MINED_CASE", "CURRENT_PACKAGE"} for item in references),
            "reference_total": len(references),
        },
        "cases": rows,
        "gold_fields_used": False,
        "policy": POLICY_VERSION,
        "schema_version": "RPSGapFillFreshnessAuditV1",
        "verdict": "PASS_TO_MANUAL_REVIEW" if all(not row["blocking_findings"] for row in rows) else "FAIL_CLOSED",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit_candidates()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report["verdict"])
        for row in report["cases"]:
            print(f"{row['case_id']}: {row['candidate_disposition']} ({len(row['findings'])} review findings)")
    return 0 if report["verdict"] != "FAIL_CLOSED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
