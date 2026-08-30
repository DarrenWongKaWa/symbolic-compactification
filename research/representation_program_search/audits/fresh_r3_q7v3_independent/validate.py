"""Replay immutable mechanical facts and the independent Q7V3 verdict."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import load_public_case


ROOT = Path(__file__).resolve().parents[4]
AUDIT_DIR = Path(__file__).resolve().parent
AUDIT = AUDIT_DIR / "AUDIT.json"
PACKAGE = ROOT / "research/representation_program_search/packages/fresh_r3/rps-case-q7v3"
CANDIDATE_COMMIT = "56f6bdb575e96b89fa02f26fd4b23a3af6e45558"
PACKAGE_MANIFEST_SHA256 = "5c3d424fb9e89a0c2ce7d3c6e0e8f03905b4bf9915b34afce0986d0fa28eef6e"
SOURCE_EXCERPT_SHA256 = "76cbf6191983c656681daca3b3c58bf9d62688fb5f4602ba0e42005dff0222a1"
PUBLIC_PATHS = (
    "assumptions.json",
    "members/M01.txt",
    "members/M02.txt",
    "members/M03.txt",
    "proposer_view.json",
    "source_catalog.json",
    "symbols.json",
)
PROGRAM_IDS = {
    "G_FULL": "1b11b9c94276b87124d9252c9f21b65ad23868b5f24b71c6db2ae29624cdbc2b",
    "G_NO_HERMITE": "dc757e5c1005fafe603044858306cf71ac8db3cbce51f1ec86f6801b288d9afa",
    "G_PRIMITIVE": "dc757e5c1005fafe603044858306cf71ac8db3cbce51f1ec86f6801b288d9afa",
}
C3_COMMIT = "5da637b86acabd1c0b1f7840cd9f5e552b0af76f"
C3_PATH = "research/representation_program_search/packages/real_domain_recovery/rps-real-c3j9/reference/program.json"
C3_SHA256 = "e80150be846e1f9fb6b0b86fc77912389bfd1fcaae0a2932d9ce89becd349bd5"
SUFFIXES = {
    "G_FULL": "full",
    "G_NO_HERMITE": "no_hermite",
    "G_PRIMITIVE": "primitive",
}
PRIMITIVE_OPERATORS = {"VALUE", "DERIVATIVE", "SUBSTITUTE", "LINEAR_COMBINATION", "COMPOSE"}
FORBIDDEN_PUBLIC = (
    "hermite",
    "divided difference",
    "frechet",
    "fréchet",
    "multiplicity",
    "repeated node",
    "third order",
    "third-order",
    "matrix function",
    "operator sequence",
    "target representation",
    "node_structures",
    '"nodes"',
)


class IndependentAuditError(ValueError):
    """An immutable audit fact failed replay."""


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _json(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise IndependentAuditError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _require(condition: bool, code: str) -> None:
    if not condition:
        raise IndependentAuditError(code)


def _artifact_gate() -> None:
    _require(_sha(PACKAGE / "package.json") == PACKAGE_MANIFEST_SHA256, "PACKAGE_MANIFEST_DRIFT")
    manifest = _json(PACKAGE / "package.json")
    rows = manifest.get("artifact_hashes")
    _require(isinstance(rows, list) and len(rows) == 63, "PACKAGE_ARTIFACT_COUNT")
    declared = set()
    for row in rows:
        _require(isinstance(row, Mapping), "PACKAGE_ARTIFACT_ROW")
        relative = row.get("path")
        _require(isinstance(relative, str) and relative not in declared, "PACKAGE_ARTIFACT_PATH")
        _require(_sha(PACKAGE / relative) == row.get("sha256"), f"PACKAGE_ARTIFACT_HASH:{relative}")
        declared.add(relative)


def _public_gate() -> None:
    case = load_public_case(PACKAGE / "proposer_view.json")
    _require(case.case_id == "Q7V3", "PUBLIC_CASE_ID")
    _require(tuple(case.accessed_paths) == PUBLIC_PATHS, "PUBLIC_PATH_FIREWALL")
    _require(case.namespace_provenance == "EXACT_PROPOSER_REFERENCE", "PUBLIC_NAMESPACE")
    _require(tuple(item.member_id for item in case.members) == ("M01", "M02", "M03"), "PUBLIC_MEMBERS")
    expected_symbols = (
        {"name": "a", "real": True, "nonzero": False},
        {"name": "b", "real": True, "nonzero": False},
        {"name": "c", "real": True, "nonzero": False},
        {"name": "p", "real": True, "nonzero": False},
        {"name": "q", "real": True, "nonzero": False},
        {"name": "r", "real": True, "nonzero": False},
    )
    _require(case.symbols == expected_symbols and case.functions == (), "PUBLIC_EXACT_NAMESPACE")
    visible = "\n".join((PACKAGE / path).read_text(encoding="utf-8") for path in PUBLIC_PATHS).casefold()
    for forbidden in FORBIDDEN_PUBLIC:
        _require(forbidden not in visible, f"PUBLIC_LEAKAGE:{forbidden}")
    _require(case.assumption_statuses == {"P01": "DECLARED", "P02": "DECLARED", "P03": "DERIVED"}, "ASSUMPTION_STATUS")


def _source_gate() -> None:
    source = _json(PACKAGE / "source_manifest.json")["sources"][0]
    _require(source["arxiv_version"] == "2203.03930v2", "SOURCE_VERSION")
    _require(source["doi"] == "10.1016/j.laa.2022.10.005", "SOURCE_DOI")
    _require(source["arxiv_source_archive_sha256"] == "e8214b47d29be06dcbd8e77f8e6d79568d6d25b67732f4ab543524b8b5a74ea7", "SOURCE_ARCHIVE_HASH")
    _require(source["source_tex_full_sha256"] == "fbae74b5e4422e5428404732ecbff74311077a0dce43352a0bd69e654ba5fd95", "SOURCE_TEX_HASH")
    _require(_sha(PACKAGE / source["stored_artifact"]["path"]) == SOURCE_EXCERPT_SHA256, "SOURCE_EXCERPT_HASH")
    _require("lines 367--373" in source["source_tex_locator"], "SOURCE_EXCERPT_LOCATOR")


def _compile_gate() -> dict[str, str]:
    loaded = load_case_package(PACKAGE)
    _require(loaded.schema_deltas == (), f"M1_SCHEMA_DELTA:{loaded.schema_deltas}")
    programs = {"G_FULL": loaded.program}
    for grammar in ("G_NO_HERMITE", "G_PRIMITIVE"):
        programs[grammar] = program_from_dict(_json(PACKAGE / f"reference/ablations/{grammar}.program.json"))
    statuses = {}
    for grammar, program in programs.items():
        _require(canonical_program_hash(program) == PROGRAM_IDS[grammar], f"PROGRAM_ID:{grammar}")
        context = loaded.context if grammar == "G_FULL" else CompileContext(
            PACKAGE.resolve(), tuple(loaded.context.symbols), (), grammar_id=grammar
        )
        compiled = compile_program(program, context)
        _require(compiled.status == "COMPILED", f"COMPILE:{grammar}:{compiled.failure_codes}")
        _require(not compiled.tautological, f"TAUTOLOGY:{grammar}")
        _require(len(compiled.obligations) == 3, f"OBLIGATIONS:{grammar}")
        if grammar != "G_FULL":
            _require({item.operator for item in program.operators} <= PRIMITIVE_OPERATORS, f"NONPRIMITIVE:{grammar}")
            _require(program.node_structures == (), f"PRIMITIVE_NODES:{grammar}")
        for obligation in compiled.obligations:
            stored = PACKAGE / f"reference/candidates/{obligation.obligation_id}.{SUFFIXES[grammar]}.txt"
            _require(stored.read_text(encoding="utf-8") == obligation.candidate_expression + "\n", f"COMPILED_OUTPUT:{grammar}:{obligation.obligation_id}")
        statuses[grammar] = compiled.status
    full_nodes = tuple(tuple(item.nodes) for item in loaded.program.node_structures)
    _require(full_nodes == (("a", "a", "b", "b"), ("a", "a", "b", "c"), ("a", "b", "c", "c")), "R3_NODE_MULTIPLICITY")
    return statuses


def _receipt_gate() -> None:
    index = _json(PACKAGE / "verification/index.json")
    attempts = index.get("attempts")
    _require(isinstance(attempts, list) and len(attempts) == 9, "RECEIPT_COUNT")
    expected = {(grammar, obligation) for grammar in SUFFIXES for obligation in ("O01", "O02", "O03")}
    _require({(row["program_variant"], row["obligation_id"]) for row in attempts} == expected, "RECEIPT_MATRIX")
    symbols = _json(PACKAGE / "symbols.json")["symbols"]
    for row in attempts:
        run = PACKAGE / "verification/workspace/runs" / row["run_id"]
        proposal = _json(run / "steps/step_001.json")
        receipt = _json(run / "steps/step_002.json")
        manifest = _json(run / "manifest.json")
        candidate = PACKAGE / row["candidate_path"]
        member = PACKAGE / f"members/{row['member_id']}.txt"
        candidate_text = candidate.read_text(encoding="utf-8").rstrip("\n")
        _require(proposal["status"] == "HYPOTHESIS" and proposal["proof_status"] == "HYPOTHESIS", "PROPOSAL_STATUS")
        _require(proposal["candidate_text"] == candidate_text, "PROPOSAL_TEXT")
        _require(proposal["candidate_hash"] == _sha_bytes(candidate_text.encode("utf-8")), "PROPOSAL_HASH")
        _require(receipt["verdict"] == "ZERO" and receipt["residual"] == "0", "RECEIPT_ZERO")
        _require(receipt["status"] == "CERTIFIED" and receipt["proof_status"] == "PROVEN", "RECEIPT_PROVEN")
        _require(receipt["candidate_hash"] == _sha(candidate), "RECEIPT_CANDIDATE_HASH")
        _require(receipt["current_hash"] == _sha(member), "RECEIPT_MEMBER_HASH")
        _require(manifest["current"]["symbols"] == symbols, "RECEIPT_NAMESPACE")


def _freshness_gate() -> None:
    old_test_manifest = _json(ROOT / "research/assumption_complete_representation/TEST_MANIFEST.json")
    _require("mp-opitz-dd-01" in old_test_manifest["CHALLENGE"], "OPITZ_NOT_PREVIOUS_TEST")
    anchors = {
        "research/assumption_complete_representation/cases/mathphys/mp-opitz-dd-01.json": "21bb35c5c842f9dd24e72b6e360931f71b7fda185d1d0a14b17a12d2275ae849",
        "research/assumption_complete_representation/cases/mathphys/mp-hermite-fA-01.json": "187043c7ed285e97e2eb40d61d68b9a8207fdc5ab56b986f566529c8b4409691",
        "research/assumption_complete_representation/cases/sciml/sciml-phi-hermite-01.json": "dabcbdf5c0b2b3c7f6af47af734711e60dec5029190f5d14db9fa0f193f1e9dc",
        "research/representation_invention/bench/tasks/test/test-a-hermite-two.json": "a358ad1d9acf1f53475053a9f99101d4512d1dbe4b210e7fd1391d4c2b0e49ff",
    }
    for relative, expected in anchors.items():
        _require(_sha(ROOT / relative) == expected, f"DUPLICATE_ANCHOR_DRIFT:{relative}")
    opitz = _json(ROOT / "research/assumption_complete_representation/cases/mathphys/mp-opitz-dd-01.json")
    sketch = opitz["expression_sketch"].casefold()
    latent = opitz["latent_structure"].casefold()
    _require("nodes, not necessarily distinct" in sketch, "OPITZ_DISTINCTNESS_SCOPE")
    _require("repeated nodes" in latent and "hermite" in latent, "OPITZ_HERMITE_SCOPE")
    c3 = subprocess.run(
        ["git", "show", f"{C3_COMMIT}:{C3_PATH}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    _require(c3.returncode == 0, "C3_ARTIFACT_UNAVAILABLE")
    _require(_sha_bytes(c3.stdout) == C3_SHA256, "C3_ARTIFACT_DRIFT")


def validate() -> dict[str, Any]:
    """Return the immutable audit verdict after replaying all local evidence."""
    audit = _json(AUDIT)
    _require(audit["schema_version"] == "RPSIndependentAdmissionAuditV1", "AUDIT_SCHEMA")
    _require(audit["candidate_commit"] == CANDIDATE_COMMIT, "AUDIT_COMMIT")
    _require(audit["verdict"] == "REJECT" and audit["admission_ready"] is False, "AUDIT_VERDICT")
    _require(audit["methodological_finding"]["recommended_disposition"] == "DIAGNOSTIC_ONLY", "AUDIT_DISPOSITION")
    _artifact_gate()
    _public_gate()
    _source_gate()
    statuses = _compile_gate()
    _receipt_gate()
    _freshness_gate()
    return {
        "candidate_commit": CANDIDATE_COMMIT,
        "compiled_variants": statuses,
        "package_unchanged_manifest_sha256": PACKAGE_MANIFEST_SHA256,
        "recommended_disposition": "DIAGNOSTIC_ONLY",
        "status": "VALID_INDEPENDENT_AUDIT",
        "verdict": "REJECT",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
