"""Fail-closed validation for the candidate-only fresh strict-R3 package."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from research.representation_program_search.program_ir import (
    CompileContext,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import load_public_case


ROOT = Path(__file__).resolve().parent
PACKAGE = ROOT / "rps-case-q7v3"
SOURCE_ARCHIVE_SHA256 = "e8214b47d29be06dcbd8e77f8e6d79568d6d25b67732f4ab543524b8b5a74ea7"
SOURCE_TEX_SHA256 = "fbae74b5e4422e5428404732ecbff74311077a0dce43352a0bd69e654ba5fd95"
SOURCE_EXCERPT_SHA256 = "76cbf6191983c656681daca3b3c58bf9d62688fb5f4602ba0e42005dff0222a1"
PUBLIC_PATHS = {
    "assumptions.json",
    "members/M01.txt",
    "members/M02.txt",
    "members/M03.txt",
    "proposer_view.json",
    "source_catalog.json",
    "symbols.json",
}
PUBLIC_VALUE_LEAKAGE = re.compile(
    r"\b(?:hermite|divided[ -]?difference|frech[eé]t|multiplicity|"
    r"repeated[ -]?node|node[ -]?role|operator[ -]?sequence|"
    r"target[ -]?(?:type|representation)|third[ -]?order|matrix[ -]?function)\b",
    re.IGNORECASE,
)
PRIMITIVE_OPERATORS = {
    "COMPOSE",
    "DERIVATIVE",
    "LINEAR_COMBINATION",
    "SUBSTITUTE",
    "VALUE",
}
EXPECTED_NODES = {
    "N01": ("a", "a", "b", "b"),
    "N02": ("a", "a", "b", "c"),
    "N03": ("a", "b", "c", "c"),
}


class FreshR3ValidationError(ValueError):
    """The candidate fails a strict package gate."""


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FreshR3ValidationError(f"UNREADABLE:{path}") from exc


def _json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FreshR3ValidationError(f"INVALID_JSON:{path}") from exc
    if not isinstance(value, Mapping):
        raise FreshR3ValidationError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise FreshR3ValidationError(code)


def _artifact_gate(package: Path) -> int:
    manifest = _json(package / "package.json")
    _require(manifest.get("schema_version") == "RPSCasePackageV1", "PACKAGE_SCHEMA")
    _require(manifest.get("package_id") == package.name, "PACKAGE_ID")
    _require(
        manifest.get("admission_status") == "CANDIDATE_FOR_INDEPENDENT_REVIEW",
        "PREMATURE_ADMISSION",
    )
    rows = manifest.get("artifact_hashes")
    _require(isinstance(rows, list) and bool(rows), "ARTIFACT_ROWS")
    declared: set[str] = set()
    for row in rows:
        _require(isinstance(row, Mapping), "ARTIFACT_ROW")
        relative = row.get("path")
        _require(isinstance(relative, str) and relative not in declared, "ARTIFACT_PATH")
        path = package / relative
        _require(path.is_file(), f"ARTIFACT_MISSING:{relative}")
        _require(_sha(path) == row.get("sha256"), f"ARTIFACT_HASH:{relative}")
        declared.add(relative)
    actual = {
        path.relative_to(package).as_posix()
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    }
    _require(declared == actual, "ARTIFACT_INVENTORY_INCOMPLETE")
    return len(declared)


def _source_gate(package: Path) -> None:
    manifest = _json(package / "source_manifest.json")
    source = manifest["sources"][0]
    _require(source["doi"] == "10.1016/j.laa.2022.10.005", "SOURCE_DOI")
    _require(source["arxiv_version"] == "2203.03930v2", "SOURCE_VERSION")
    _require(source["arxiv_source_archive_sha256"] == SOURCE_ARCHIVE_SHA256, "SOURCE_ARCHIVE_HASH")
    _require(source["source_tex_full_sha256"] == SOURCE_TEX_SHA256, "SOURCE_TEX_HASH")
    _require(source["stored_artifact"]["sha256"] == SOURCE_EXCERPT_SHA256, "SOURCE_EXCERPT_DECLARATION")
    _require(_sha(package / source["stored_artifact"]["path"]) == SOURCE_EXCERPT_SHA256, "SOURCE_EXCERPT_HASH")
    _require("lines 367--373" in source["source_tex_locator"], "SOURCE_LOCATOR")
    for field in ("assumption_contract", "assumption_locators", "symbol_namespace", "lowering"):
        row = manifest[field]
        _require(_sha(package / row["path"]) == row["sha256"], f"SOURCE_BINDING:{field}")
    locators = _json(package / manifest["assumption_locators"]["path"])["locators"]
    _require([item["locator_id"] for item in locators] == ["S01", "S02", "S03"], "ASSUMPTION_LOCATORS")
    assumptions = _json(package / "assumptions.json")
    statuses = {item["predicate_id"]: item["status"] for item in assumptions["predicates"]}
    _require(statuses == {"P01": "DECLARED", "P02": "DECLARED", "P03": "DERIVED"}, "ASSUMPTION_STATUS")
    _require(assumptions.get("status") == "ASSUMPTION_COMPLETE", "ASSUMPTION_INCOMPLETE")


def _public_gate(package: Path) -> dict[str, Any]:
    case = load_public_case(package / "proposer_view.json")
    _require(case.case_id == "Q7V3", "PUBLIC_CASE_ID")
    _require(set(case.accessed_paths) == PUBLIC_PATHS, "PUBLIC_PATH_FIREWALL")
    _require(case.namespace_provenance == "EXACT_PROPOSER_REFERENCE", "PUBLIC_NAMESPACE")
    _require(tuple(item.member_id for item in case.members) == ("M01", "M02", "M03"), "PUBLIC_MEMBER_IDS")
    symbols = tuple(item["name"] for item in case.symbols)
    _require(symbols == ("a", "b", "c", "p", "q", "r"), "PUBLIC_SYMBOLS")
    visible = "\n".join((package / relative).read_text(encoding="utf-8") for relative in sorted(PUBLIC_PATHS))
    match = PUBLIC_VALUE_LEAKAGE.search(visible)
    _require(match is None, f"PUBLIC_TARGET_LEAKAGE:{match.group(0) if match else ''}")
    view = _json(package / "proposer_view.json")
    _require(set(view) == {"assumptions", "case_id", "schema_version", "source_catalog", "structural_observations"}, "PUBLIC_VIEW_SHAPE")
    return case.public_manifest()


def _compile_gate(package: Path) -> dict[str, Any]:
    loaded = load_case_package(package)
    _require(loaded.schema_deltas == (), f"M1_SCHEMA_DELTAS:{loaded.schema_deltas}")
    result = compile_program(loaded.program, loaded.context)
    _require(result.status == "COMPILED", f"M1_COMPILE:{result.failure_codes}")
    _require(not result.tautological, "M1_TAUTOLOGY")
    _require(len(result.obligations) == 3, "M1_OBLIGATION_COUNT")

    variants: dict[str, Any] = {"G_FULL": result}
    for grammar_id in ("G_NO_HERMITE", "G_PRIMITIVE"):
        raw = _json(package / f"reference/ablations/{grammar_id}.program.json")
        program = program_from_dict(raw)
        operators = {item.operator for item in program.operators}
        _require(operators <= PRIMITIVE_OPERATORS, f"{grammar_id}:NONPRIMITIVE")
        _require("HERMITE_DD" not in operators, f"{grammar_id}:NAMED_HERMITE")
        compiled = compile_program(
            program,
            CompileContext(package.resolve(), tuple(loaded.context.symbols), (), grammar_id=grammar_id),
        )
        _require(compiled.status == "COMPILED", f"{grammar_id}:COMPILE:{compiled.failure_codes}")
        _require(not compiled.tautological, f"{grammar_id}:TAUTOLOGY")
        _require(len(compiled.obligations) == 3, f"{grammar_id}:OBLIGATION_COUNT")
        variants[grammar_id] = compiled

    full = _json(package / "reference/program.json")
    nodes = {item["node_id"]: tuple(item["nodes"]) for item in full["node_structures"]}
    _require(nodes == EXPECTED_NODES, "EVALUATOR_MULTIPLICITY")
    _require(all(item["operator"] == "HERMITE_DD" for item in full["operators"][::2]), "FULL_NAMED_OPERATORS")
    return {
        name: {
            "obligations": len(compiled.obligations),
            "status": compiled.status,
            "tautological": compiled.tautological,
        }
        for name, compiled in variants.items()
    }


def _receipt_gate(package: Path) -> int:
    index = _json(package / "verification/index.json")
    attempts = index.get("attempts")
    _require(isinstance(attempts, list) and len(attempts) == 9, "RECEIPT_COUNT")
    expected_pairs = {
        (grammar, obligation)
        for grammar in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
        for obligation in ("O01", "O02", "O03")
    }
    actual_pairs: set[tuple[str, str]] = set()
    for row in attempts:
        grammar = row["program_variant"]
        obligation = row["obligation_id"]
        actual_pairs.add((grammar, obligation))
        _require(row["verdict"] == "ZERO", f"INDEX_NONZERO:{grammar}:{obligation}")
        run = package / "verification/workspace/runs" / row["run_id"]
        proposal = _json(run / f"steps/step_{row['proposal_step']:03d}.json")
        receipt = _json(run / f"steps/step_{row['verification_step']:03d}.json")
        _require(proposal.get("status") == "HYPOTHESIS", f"PROPOSAL_STATUS:{grammar}:{obligation}")
        _require(receipt.get("verdict") == "ZERO", f"RECEIPT_VERDICT:{grammar}:{obligation}")
        _require(receipt.get("status") == "CERTIFIED", f"RECEIPT_STATUS:{grammar}:{obligation}")
        _require(receipt.get("proof_status") == "PROVEN", f"RECEIPT_PROOF:{grammar}:{obligation}")
        candidate = package / row["candidate_path"]
        member = package / f"members/{row['member_id']}.txt"
        _require(receipt.get("candidate_hash") == _sha(candidate), f"RECEIPT_CANDIDATE_HASH:{grammar}:{obligation}")
        _require(receipt.get("current_hash") == _sha(member), f"RECEIPT_CURRENT_HASH:{grammar}:{obligation}")
    _require(actual_pairs == expected_pairs, "RECEIPT_MATRIX")
    obligations = _json(package / "reference/obligations.json")
    _require(obligations.get("summary") == {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 3}, "REQUIRED_SUMMARY")
    return len(attempts)


def _duplicate_gate(package: Path) -> None:
    audit = _json(package / "source/duplicate_audit.json")
    exact = audit["exact_byte_audit"]
    _require(exact["candidate_vs_current_member_overlap"] == [], "CURRENT_EXACT_DUPLICATE")
    _require(exact["candidate_vs_historical_expression_overlap"] == [], "HISTORICAL_EXACT_DUPLICATE")
    _require(audit["explicit_json_node_signature_matches"] == [], "STRUCTURAL_NODE_DUPLICATE")
    anchors = {item["identity"] for item in audit["manual_structural_anchors"]}
    _require(anchors == {"C3J9", "test-a-hermite-two", "sciml-phi-hermite-01"}, "DUPLICATE_ANCHORS")
    _require(audit["candidate_signatures"] == {
        "M01": {"arity": 4, "multiplicity_partition": [2, 2]},
        "M02": {"arity": 4, "multiplicity_partition": [2, 1, 1]},
        "M03": {"arity": 4, "multiplicity_partition": [2, 1, 1]},
    }, "CANDIDATE_SIGNATURES")


def validate(package: Path = PACKAGE) -> dict[str, Any]:
    """Validate source, firewall, compilation, proof, and freshness gates."""
    artifacts = _artifact_gate(package)
    _source_gate(package)
    public = _public_gate(package)
    compiled = _compile_gate(package)
    receipts = _receipt_gate(package)
    _duplicate_gate(package)
    return {
        "admission_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
        "artifact_count": artifacts,
        "case_id": public["case_id"],
        "compiled_variants": compiled,
        "public_accessed_paths": public["accessed_paths"],
        "receipt_count": receipts,
        "status": "VALID_CANDIDATE",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True, indent=2))
