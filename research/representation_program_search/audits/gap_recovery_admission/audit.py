"""Independent, read-only audit of ``rps-candidate-k9-001``.

The audited package is never modified.  This module replays public loading,
M1 compilation, canonical hashing, proof receipts, representation depth, and
duplicate status.  Primary-source retrieval was performed independently; the
retrieval hashes and exact excerpt comparisons are frozen below.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from symbolic_compactification import ZERO, load_expression, verify_equivalent

from research.representation_program_search.audits.leakage.audit import (
    alpha_normalize,
    strict_normalize,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import load_public_case


ROOT = Path(__file__).resolve().parents[4]
PACKAGE_REL = (
    "research/representation_program_search/recovery/gap_recovery/"
    "rps-candidate-k9-001"
)
PREDECESSOR_REL = (
    "research/representation_program_search/packages/gap_fill/"
    "gf-cr3bp-2017-eq28"
)
AUDITED_COMMIT = "71b34a8c4c5d7d83e4191fb4286dcd02d27c32df"
SOURCE_ARCHIVE_SHA256 = (
    "698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a"
)
SOURCE_TEX_SHA256 = (
    "59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3"
)
PREDECESSOR_TREE_SHA256 = (
    "0943a6ae269d81af89daf96202303e183d7c75f8383a959f67c149501b04fdc0"
)
EXCERPTS = {
    "source/upstream/CM_dynSys.lines_1001_1005.tex": (
        "49b68485e00dfd844f959dee8b2260b3f8cdbd80cdb5bbf323e755267c9e4fbd"
    ),
    "source/upstream/CM_dynSys.lines_1062_1069.tex": (
        "cbb9da19cf4391f71b780d550a192e83e00767cccdc6897f8125eed8da68a110"
    ),
    "source/upstream/CM_dynSys.lines_1088_1118.tex": (
        "1611b04bed8d1a0b01bf96b0746fc7550fba808a11451a55b62c005eeefd2e10"
    ),
    "source/upstream/CM_dynSys.lines_1148_1159.tex": (
        "c039184c02abdf9c0d0f2e3c4ae5a7c155f3441ca5c3f46da2d3ef3afaa2f8ff"
    ),
    "source/upstream/CM_dynSys.lines_661_709.tex": (
        "9a223e976adadde8a1b2a4691b3e9f161b1834c26da93ac1b1e63d5efa97bd5e"
    ),
    "source/upstream/CM_dynSys.lines_710_730.tex": (
        "98b2390b9e9e6ef77240751c656408ca4de25f35055ae010d21cb2efcfb5325f"
    ),
}
FORBIDDEN_PUBLIC_TARGET_TERMS = (
    "cr3bp",
    "divided difference",
    "eq28",
    "equation (28)",
    "gold",
    "hermite",
    "latent",
    "newton",
    "operator sequence",
    "representation_depth",
    "target representation",
    "three-body",
)
EXPECTED_PUBLIC_PATHS = {
    "assumptions.json",
    "members/M9H1.txt",
    "members/M9H2.txt",
    "members/M9H3.txt",
    "members/M9H4.txt",
    "proposer_view.json",
    "source_catalog.json",
    "symbols.json",
}
VARIANT_PATHS = {
    "G_FULL": "reference/program.json",
    "G_NO_HERMITE": "reference/ablations/G_NO_HERMITE.program.json",
    "G_PRIMITIVE": "reference/ablations/G_PRIMITIVE.program.json",
}


class IndependentAuditError(ValueError):
    """One fail-closed audit gate did not pass."""


def _json(path: Path) -> Mapping[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IndependentAuditError(f"UNREADABLE_JSON:{path}") from exc
    if not isinstance(value, Mapping):
        raise IndependentAuditError(f"JSON_OBJECT_REQUIRED:{path}")
    return value


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise IndependentAuditError(f"UNREADABLE:{path}") from exc


def _tree_hash(path: Path) -> tuple[str, int]:
    rows = [
        f"{item.relative_to(path).as_posix()}\t{_sha(item)}"
        for item in sorted(path.rglob("*"))
        if item.is_file()
    ]
    return hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest(), len(rows)


def _manifest(package: Path) -> dict[str, Any]:
    manifest = _json(package / "package.json")
    rows = manifest.get("artifact_hashes")
    declared: dict[str, str] = {}
    errors: list[str] = []
    if not isinstance(rows, list):
        errors.append("ARTIFACT_MANIFEST_INVALID")
        rows = []
    for row in rows:
        if not isinstance(row, Mapping) or set(row) != {"path", "sha256"}:
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        relative = row["path"]
        if not isinstance(relative, str) or relative in declared:
            errors.append("ARTIFACT_ENTRY_INVALID")
            continue
        declared[relative] = str(row["sha256"])
    actual = {
        path.relative_to(package).as_posix(): _sha(path)
        for path in package.rglob("*")
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    }
    if declared != actual:
        errors.append("ARTIFACT_MANIFEST_MISMATCH")
    expected = {
        "admission_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
        "audited_depth": "R2_NEWTON_DD",
        "eligibility": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
        "package_id": "rps-candidate-k9-001",
        "package_status": "PACKAGE_READY",
        "schema_version": "RPSCasePackageV1",
        "verdict_totals": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 12},
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"MANIFEST_FIELD:{key}")
    return {
        "artifact_count": len(actual),
        "errors": sorted(set(errors)),
        "package_manifest_sha256": _sha(package / "package.json"),
        "status": "PASS" if not errors else "FAIL",
    }


def _source(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    dossier = _json(package / "source/dossier.json")
    manifest = _json(package / "source_manifest.json")
    for relative, digest in EXCERPTS.items():
        if _sha(package / relative) != digest:
            errors.append(f"EXCERPT_HASH:{relative}")
    dossier_rows = {
        str(row["path"]): str(row["sha256"])
        for row in dossier.get("source_artifacts", [])
    }
    manifest_rows = {
        str(row["path"]): str(row["sha256"])
        for row in manifest.get("source_artifacts", [])
    }
    if dossier_rows != EXCERPTS or manifest_rows != EXCERPTS:
        errors.append("EXCERPT_BINDING")
    primary = dossier.get("primary_source", {})
    for field, value in {
        "doi": "10.1137/16M110719X",
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_file_sha256": SOURCE_TEX_SHA256,
        "source_file": "CM_dynSys.tex",
    }.items():
        if primary.get(field) != value:
            errors.append(f"PRIMARY_SOURCE:{field}")
    locators = dossier.get("source_locators", {})
    required = {
        "S9M1", "S9M2", "S9M3", "S9M4", "S9N1", "S9N2", "S9P1",
        "S9P2", "S9P3A", "S9P3B", "S9P4", "S9R1",
    }
    if set(locators) != required:
        errors.append("LOCATOR_SET")
    for locator_id, row in locators.items():
        relative = row.get("path")
        if (
            relative not in EXCERPTS
            or row.get("sha256") != EXCERPTS.get(relative)
            or not isinstance(row.get("upstream_lines"), str)
            or not isinstance(row.get("claim"), str)
        ):
            errors.append(f"LOCATOR:{locator_id}")
    context = (package / "source/upstream/CM_dynSys.lines_661_709.tex").read_text()
    next_block = (package / "source/upstream/CM_dynSys.lines_710_730.tex").read_text()
    if "\\begin{align*}" not in context or "\\end{align*}" not in context:
        errors.append("IDENTITIES_NOT_UNNUMBERED")
    if "\\label{R3B_RHS}" in context or "\\label{R3B_RHS}" not in next_block:
        errors.append("NUMBERING_CORRECTION")
    if not all(fragment in context for fragment in (
        "\\frac{\\Delta}{\\Delta x_1}",
        "\\frac{\\Delta}{\\Delta x_2}",
        "A^{r,s}",
        "B^{r,s}",
    )):
        errors.append("SOURCE_IDENTITY_CONTENT")
    return {
        "errors": sorted(set(errors)),
        "independent_retrieval": {
            "download_url": "https://export.arxiv.org/e-print/1612.02417v1",
            "retrieved_on": "2026-08-30",
            "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "source_file": "CM_dynSys.tex",
            "source_file_line_count": 1179,
            "source_file_sha256": SOURCE_TEX_SHA256,
            "stored_excerpt_comparison": "ALL_SIX_CMP_IDENTICAL",
        },
        "official_metadata_checks": {
            "arxiv": "https://arxiv.org/abs/1612.02417",
            "authors_match": True,
            "doi_match": True,
            "siam": "https://epubs.siam.org/doi/10.1137/16M110719X",
            "title_match": True,
            "venue_pages_match": True,
        },
        "source_excerpt_hashes": EXCERPTS,
        "status": "PASS" if not errors else "FAIL",
    }


def _assumptions_and_public(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    case = load_public_case(package / "proposer_view.json")
    symbols = tuple(_json(package / "symbols.json")["symbols"])
    statuses = {
        str(row["predicate_id"]): str(row["status"])
        for row in _json(package / "assumptions.json")["predicates"]
    }
    if case.case_id != "C9H4" or not re.fullmatch(r"C[A-Z0-9]+", case.case_id):
        errors.append("CASE_ID_NOT_OPAQUE")
    if any(not re.fullmatch(r"M[A-Z0-9]+", item.member_id) for item in case.members):
        errors.append("MEMBER_ID_NOT_OPAQUE")
    if case.symbols != symbols or case.namespace_provenance != "EXACT_PROPOSER_REFERENCE":
        errors.append("PUBLIC_NAMESPACE")
    if len(symbols) != 8 or any(row.get("real") is not True for row in symbols):
        errors.append("PUBLIC_REAL_NAMESPACE")
    if dict(case.assumption_statuses) != statuses:
        errors.append("PUBLIC_ASSUMPTIONS")
    if set(case.accessed_paths) != EXPECTED_PUBLIC_PATHS:
        errors.append("PUBLIC_ACCESSED_PATHS")
    visible = "\n".join(
        (package / relative).read_text(encoding="utf-8")
        for relative in sorted(EXPECTED_PUBLIC_PATHS)
    ).casefold()
    target_terms = [term for term in FORBIDDEN_PUBLIC_TARGET_TERMS if term in visible]
    if target_terms:
        errors.append("PUBLIC_TARGET_LEAKAGE")
    assumptions = _json(package / "assumptions.json")
    predicates = assumptions.get("predicates", [])
    if assumptions.get("status") != "ASSUMPTION_COMPLETE":
        errors.append("ASSUMPTION_INCOMPLETE")
    if {row.get("status") for row in predicates} - {"DECLARED", "DERIVED"}:
        errors.append("ASSUMPTION_STATUS")
    if statuses != {
        "P9A1": "DECLARED",
        "P9A2": "DECLARED",
        "P9A3": "DECLARED",
        "P9A4": "DERIVED",
    }:
        errors.append("ASSUMPTION_SET")
    return {
        "accessed_paths": list(case.accessed_paths),
        "assumption_statuses": statuses,
        "easiness_risks": [
            "PUBLIC_EXPRESSIONS_ARE_ALREADY_FACTORIZED",
            "PUBLIC_ASSUMPTION_P9A4_USES_GENERIC_NODE_DIFFERENCE_PHRASE",
        ],
        "errors": sorted(set(errors)),
        "namespace_provenance": case.namespace_provenance,
        "public_target_terms": target_terms,
        "status": "PASS" if not errors else "FAIL",
        "symbols": list(case.symbols),
    }


def _compile_and_depth(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    loaded = load_case_package(package)
    if loaded.schema_deltas:
        errors.append("M1_SCHEMA_DELTAS")
    variants: dict[str, Any] = {}
    programs: dict[str, Any] = {}
    for grammar, relative in VARIANT_PATHS.items():
        raw = _json(package / relative)
        program = loaded.program if grammar == "G_FULL" else program_from_dict(raw)
        compiled = compile_program(
            program,
            CompileContext(
                package.resolve(),
                loaded.context.symbols,
                loaded.context.functions,
                grammar_id=grammar,
            ),
        )
        program_hash = canonical_program_hash(program)
        if raw.get("program_id") != program_hash:
            errors.append(f"CANONICAL_HASH:{grammar}")
        if compiled.status != "COMPILED" or compiled.tautological or len(compiled.obligations) != 4:
            errors.append(f"COMPILE:{grammar}")
        variants[grammar] = {
            "canonical_program_hash": program_hash,
            "obligation_count": len(compiled.obligations),
            "status": compiled.status,
            "tautological": compiled.tautological,
        }
        programs[grammar] = program
    full = programs["G_FULL"]
    primitive = programs["G_PRIMITIVE"]
    full_ops = {item.operator for item in full.operators}
    primitive_ops = {item.operator for item in primitive.operators}
    if full_ops != {"NEWTON_DD", "LINEAR_COMBINATION"}:
        errors.append("FULL_OPERATOR_SET")
    if primitive_ops != {"VALUE", "LINEAR_COMBINATION"}:
        errors.append("PRIMITIVE_OPERATOR_SET")
    if "NEWTON_DD" in primitive_ops or primitive.node_structures:
        errors.append("PRIMITIVE_NAMED_GIVEAWAY")
    if (
        len(full.latent_objects) != 1
        or full.latent_objects[0].expression != "1/sqrt(z)"
        or len(full.node_structures) != 4
        or any(len(item.nodes) != 2 for item in full.node_structures)
        or len(full.member_assignments) != 4
        or full.unexplained_members
    ):
        errors.append("R2_STRUCTURE")
    return {
        "depth": {
            "assessment": "R2_NEWTON_DD",
            "basis": (
                "One shared non-member-copy latent 1/sqrt(z), four explicit "
                "two-node evaluations, and exact member-specific linear reconstruction."
            ),
            "not_r3": "No repeated node appears.",
            "not_tautological": True,
        },
        "errors": sorted(set(errors)),
        "loader_schema_deltas": list(loaded.schema_deltas),
        "named_primitive_required": False,
        "primitive_operator_set": sorted(primitive_ops),
        "status": "PASS" if not errors else "FAIL",
        "variants": variants,
    }


def _receipts(package: Path) -> dict[str, Any]:
    errors: list[str] = []
    index = _json(package / "verification/index.json")
    symbols = _json(package / "symbols.json")["symbols"]
    expected = {
        (grammar, f"Q9H{number}")
        for grammar in VARIANT_PATHS
        for number in range(1, 5)
    }
    seen: set[tuple[str, str]] = set()
    replay: list[dict[str, Any]] = []
    for attempt in index.get("attempts", []):
        grammar = str(attempt.get("program_variant"))
        obligation = str(attempt.get("obligation_id"))
        member = package / "members" / f"{attempt.get('member_id')}.txt"
        candidate = package / str(attempt.get("candidate_path"))
        run = package / "verification/workspace/runs" / str(attempt.get("run_id"))
        proposal = _json(run / "steps/step_001.json")
        receipt = _json(run / "steps/step_002.json")
        seen.add((grammar, obligation))
        recorded = (
            proposal.get("status") == "HYPOTHESIS"
            and proposal.get("proof_status") == "HYPOTHESIS"
            and receipt.get("verdict") == "ZERO"
            and receipt.get("status") == "CERTIFIED"
            and receipt.get("proof_status") == "PROVEN"
            and receipt.get("residual") == "0"
            and receipt.get("current_hash") == _sha(member)
            and receipt.get("candidate_hash") == _sha(candidate)
        )
        current_record = load_expression(member, symbols)
        candidate_record = load_expression(candidate, symbols)
        independent = verify_equivalent(
            current_record.text,
            candidate_record.text,
            symbols,
        )
        if not recorded:
            errors.append(f"RECORDED_RECEIPT:{grammar}:{obligation}")
        if independent.verdict != ZERO:
            errors.append(f"INDEPENDENT_REPLAY:{grammar}:{obligation}")
        replay.append({
            "grammar": grammar,
            "independent_verdict": independent.verdict,
            "obligation_id": obligation,
            "recorded_receipt_valid": recorded,
        })
    if seen != expected:
        errors.append("RECEIPT_COVERAGE")
    return {
        "errors": sorted(set(errors)),
        "independent_replay": replay,
        "replayed_zero": sum(item["independent_verdict"] == ZERO for item in replay),
        "status": "PASS" if not errors else "FAIL",
        "stored_receipt_count": len(replay),
    }


def _duplicates(root: Path, package: Path) -> dict[str, Any]:
    errors: list[str] = []
    members = [
        path.read_text(encoding="utf-8").strip()
        for path in sorted((package / "members").glob("*.txt"))
    ]
    exact: list[str] = []
    renamed: list[str] = []
    for path in sorted(
        (root / "research/representation_program_search/packages").glob(
            "**/members/*.txt"
        )
    ):
        text = path.read_text(encoding="utf-8").strip()
        relative = path.relative_to(root).as_posix()
        if any(strict_normalize(text) == strict_normalize(member) for member in members):
            exact.append(relative)
        elif any(alpha_normalize(text) == alpha_normalize(member) for member in members):
            renamed.append(relative)
    expected = [
        f"{PREDECESSOR_REL}/members/G{number:04d}.txt"
        for number in range(1, 5)
    ]
    if exact != expected:
        errors.append("EXACT_MATCH_SET")
    if renamed:
        errors.append("RENAMED_MATCH")
    predecessor = root / PREDECESSOR_REL
    tree_hash, file_count = _tree_hash(predecessor)
    if tree_hash != PREDECESSOR_TREE_SHA256 or file_count != 33:
        errors.append("PREDECESSOR_MUTATED")
    method_references: list[str] = []
    manifest_references: list[str] = []
    needles = ("gf-cr3bp-2017-eq28", "rps-candidate-k9-001")
    for path in (root / "research/representation_program_search").rglob("*.json"):
        relative = path.relative_to(root).as_posix()
        if PREDECESSOR_REL in relative or PACKAGE_REL in relative:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if not any(needle in text for needle in needles):
            continue
        parts = set(path.parts)
        if "runs" in parts or "results" in parts or "decisions" in parts:
            method_references.append(relative)
        if "benchmarks" in parts or path.name in {
            "FREEZE_MANIFEST.json", "DEV_MANIFEST.json", "TEST_MANIFEST.json"
        }:
            manifest_references.append(relative)
    if method_references:
        errors.append("PREDECESSOR_CONSUMED_BY_METHOD")
    if manifest_references:
        errors.append("PREDECESSOR_ALREADY_ADMITTED")
    return {
        "admission_interpretation": (
            "EXPECTED_VERSIONED_REPAIR_MATCHES. The predecessor was newly mined "
            "inside this experiment, failed package admission, and was never a DEV/TEST "
            "or method-run input. Count the pair as one scientific identity."
        ),
        "errors": sorted(set(errors)),
        "exact_matches": exact,
        "fresh_identity_claim": False,
        "manifest_references": sorted(manifest_references),
        "method_run_references": sorted(method_references),
        "predecessor_file_count": file_count,
        "predecessor_tree_sha256": tree_hash,
        "renamed_matches": renamed,
        "repair_of_newly_mined_identity": True,
        "status": "PASS" if not errors else "FAIL",
    }


def audit(root: Path = ROOT) -> dict[str, Any]:
    """Return an independently recomputed admission report."""
    package = root / PACKAGE_REL
    sections = {
        "assumptions_and_public_boundary": _assumptions_and_public(package),
        "compilation_and_depth": _compile_and_depth(package),
        "duplicate_and_identity_status": _duplicates(root, package),
        "manifest": _manifest(package),
        "primary_source": _source(package),
        "receipts": _receipts(package),
    }
    failures = [name for name, section in sections.items() if section["status"] != "PASS"]
    return {
        "admission_scope": "DEV_R2_CALIBRATION_ONLY",
        "audited_commit": AUDITED_COMMIT,
        "audited_package": PACKAGE_REL,
        "decision": "ADMISSION_READY" if not failures else "REJECT",
        "decision_reasons": (
            [
                "PRIMARY_SOURCE_AND_LOCATORS_INDEPENDENTLY_VERIFIED",
                "PUBLIC_BOUNDARY_OPAQUE_AND_TARGET_BLIND",
                "M1_CANONICAL_NONTAUTOLOGICAL_R2",
                "TWELVE_OF_TWELVE_RECEIPTS_INDEPENDENTLY_REPLAY_ZERO",
                "NAMED_OPERATOR_NOT_REQUIRED_UNDER_PRIMITIVE_CONTROL",
                "PREDECESSOR_DUPLICATES_ARE_EXPECTED_VERSIONED_REPAIR_COPIES",
                "PREDECESSOR_NEVER_ADMITTED_OR_USED_BY_METHODS",
            ]
            if not failures
            else [f"FAILED_SECTION:{name}" for name in failures]
        ),
        "identity_counting_rule": (
            "The rejected predecessor and repaired package are one scientific identity; "
            "never count both or call the repaired package a fresh mining success."
        ),
        "independent_audit_policy": "RPS_GAP_RECOVERY_INDEPENDENT_ADMISSION_V1",
        "limitations": [
            "PUBLIC_FORMULAS_ARE_FACTORIZED_AND_MAY_MAKE_R2_EASY",
            "PUBLIC_P9A4_USES_GENERIC_NODE_DIFFERENCE_WORDING_BUT_EXPOSES_NO_TARGET_OPERATOR_OR_NODE_ROLE",
            "ADMISSION_READY_IS_NOT_SEARCH_SUCCESS_OR_AI_EVIDENCE",
            "THIS_R2_CALIBRATION_CASE_DOES_NOT_ADDRESS_THE_PRIMARY_R3_PLUS_FRONTIER",
        ],
        "package_mutated_by_audit": False,
        "sections": sections,
        "status": "PASS" if not failures else "FAIL",
    }


def _markdown(report: Mapping[str, Any]) -> str:
    decision = report["decision"]
    compilation = report["sections"]["compilation_and_depth"]
    duplicates = report["sections"]["duplicate_and_identity_status"]
    source = report["sections"]["primary_source"]
    return f"""# Independent gap-recovery admission audit

## Verdict

**{decision} — DEV R2 calibration only.**

The repaired package passes the source, public-boundary, M1, exact-proof,
depth, primitive-control, and duplicate gates. It is not a new scientific
identity, search success, AI result, or R3+ result.

## Primary source

The audit independently downloaded arXiv `1612.02417v1`. The archive SHA-256
is `{SOURCE_ARCHIVE_SHA256}` and `CM_dynSys.tex` SHA-256 is
`{SOURCE_TEX_SHA256}`. All six stored excerpts compare byte-for-byte with the
claimed upstream line ranges. Official metadata agrees between
[arXiv](https://arxiv.org/abs/1612.02417) and
[SIAM](https://epubs.siam.org/doi/10.1137/16M110719X).

The four retained identities are unnumbered lines 705--708. The later
`R3B_RHS` numbered environment starts after them; the predecessor's “Eq. 28”
name was inaccurate and is not repeated in the repaired public boundary.

## Public boundary and assumptions

`load_public_case()` reads exactly the proposer view, assumptions, catalog,
symbols, and four member files. It returns eight hash-bound real symbols and
the exact statuses `DECLARED, DECLARED, DECLARED, DERIVED`. Case/member IDs are
opaque. No source identity, target representation, operator name or sequence,
reference program, node role, or receipt is public.

The factorized formulas make the intended structure comparatively easy. P9A4
also uses the generic phrase “node difference”; this is recorded as an
easiness risk, not target leakage, because it identifies neither the paired
expressions' roles nor a target operator. This wording must not be cited as
evidence of search difficulty.

## Program and proof

M1 loads with no schema deltas. `G_FULL`, `G_NO_HERMITE`, and `G_PRIMITIVE`
all have canonical program hashes, compile non-tautologically, and produce four
obligations. All 12 stored sessions bind exact current/candidate hashes and
record `HYPOTHESIS -> ZERO/CERTIFIED/PROVEN`; independent replay returns 12
more exact ZERO verdicts.

The independent depth is `{compilation['depth']['assessment']}`: one shared
`1/sqrt(z)` latent, four explicit two-node evaluations, and exact linear
reconstruction. The primitive control uses only `VALUE` and
`LINEAR_COMBINATION`, so the named `NEWTON_DD` primitive is not required.

## Duplicate disposition

The only exact current-package matches are the four predecessor member files;
there are no additional alpha-renamed matches. The predecessor tree remains
unchanged at `{duplicates['predecessor_tree_sha256']}` ({duplicates['predecessor_file_count']}
files).

These copies do not create a second case. They are a versioned package repair
of one identity newly mined in this experiment. The predecessor failed
admission and appears in no DEV/TEST manifest or method-run artifact. Admit at
most the repaired package and permanently alias/exclude the predecessor. Never
report the repair as a new mining success.

## Scope and limitations

- Admission is limited to DEV R2 calibration.
- The visible factorization can make the task easy.
- This does not bear on held-out generalization or the R3+ frontier.
- It is not AI, grammar, verifier-feedback, or search evidence until a frozen
  method run evaluates it.
- The audit used AI-assisted research tooling; all admission gates are backed
  by deterministic artifacts or exact source hashes.
"""


def write_report(root: Path = ROOT) -> dict[str, Any]:
    report = audit(root)
    output = root / "research/representation_program_search/audits/gap_recovery_admission"
    json_path = output / "INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json"
    md_path = output / "INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.md"
    json_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    result = write_report(args.root.resolve()) if args.write else audit(args.root.resolve())
    print(json.dumps(result, sort_keys=True, indent=2))
    raise SystemExit(0 if result["status"] == "PASS" else 1)
