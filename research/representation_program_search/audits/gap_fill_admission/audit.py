"""Read-only, fail-closed admission audit for commit 8bab08d gap-fill packages.

The audit deliberately distinguishes exact algebraic certification from
scientific admission.  It does not repair packages, edit a manifest, select a
benchmark partition, or use a hidden target during duplicate screening.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from research.representation_program_search.audits.package_admission.audit import (
    audit_manifest,
    audit_parser,
)
from research.representation_program_search.packages.gap_fill import (
    freshness_audit,
    validate as package_validate,
)
from research.representation_program_search.program_ir import (
    compile_program,
    load_case_package,
)
from research.representation_program_search.search import load_public_case


AUDIT_POLICY = "RPS_GAP_FILL_INDEPENDENT_ADMISSION_AUDIT_V1"
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[3]
PACKAGE_ROOT = REPO_ROOT / "research/representation_program_search/packages/gap_fill"
REVIEW_PATH = HERE / "reviews.json"
OUTPUT_JSON = HERE / "INDEPENDENT_GAP_FILL_ADMISSION_AUDIT.json"
OUTPUT_MD = HERE / "INDEPENDENT_GAP_FILL_ADMISSION_AUDIT.md"
PACKAGE_IDS = ("gf-cr3bp-2017-eq28", "gf-vdw-2013-eq1")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: JSON root must be an object")
    return value


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_artifact_hash_count(package: Path) -> int:
    dossier = _json(package / "sources/source_dossier.json")
    count = 0
    for source in dossier.get("sources", []):
        if not isinstance(source, Mapping):
            continue
        artifact = source.get("artifact")
        if isinstance(artifact, Mapping) and artifact.get("bytes_sha256"):
            count += 1
        elif source.get("bytes_sha256") or source.get("content_sha256"):
            count += 1
    return count


def _ablation(package: Path, grammar_id: str) -> dict[str, Any]:
    loaded = load_case_package(package, grammar_id=grammar_id)
    compiled = compile_program(loaded.program, loaded.context)
    return {
        "failure_codes": list(compiled.failure_codes),
        "obligation_count": len(compiled.obligations),
        "program_id": compiled.program_id,
        "status": compiled.status,
        "tautological": compiled.tautological,
    }


def _public_boundary(package: Path) -> dict[str, Any]:
    public = load_public_case(package / "proposer_view.json")
    exact = _json(package / "symbols.json").get("symbols", [])
    public_symbols = public.public_manifest()["symbols"]
    return {
        "accessed_paths": list(public.accessed_paths),
        "assumption_statuses": dict(public.assumption_statuses),
        "exact_symbols": exact,
        "namespace_matches_exact_symbols": public_symbols == exact,
        "namespace_provenance": public.namespace_provenance,
        "public_symbols": public_symbols,
        "symbols_json_accessed": "symbols.json" in public.accessed_paths,
    }


def _source_binding(package: Path) -> dict[str, Any]:
    manifest = _json(package / "source_manifest.json")
    dossier_link = manifest.get("source_dossier", {})
    dossier_path = package / str(dossier_link.get("path", ""))
    dossier_hash_valid = (
        dossier_path.is_file() and _sha(dossier_path) == dossier_link.get("sha256")
    )
    dossier = _json(dossier_path)
    source_count = len(dossier.get("sources", []))
    artifact_hash_count = _source_artifact_hash_count(package)
    return {
        "dossier_hash_valid": dossier_hash_valid,
        "dossier_package_relative": dossier_path.resolve().is_relative_to(package.resolve()),
        "primary_or_authoritative_source_count": source_count,
        "retrieved_source_artifact_hash_count": artifact_hash_count,
        "strict_retrieved_source_binding": (
            dossier_hash_valid and source_count > 0 and artifact_hash_count == source_count
        ),
    }


def _receipt_summary(package: Path) -> dict[str, Any]:
    obligations = _json(package / "reference/obligations.json")
    rows = obligations.get("obligations", [])
    return {
        "all_required_exact_zero": bool(rows)
        and all(row.get("verdict") == "ZERO" for row in rows),
        "obligation_count": len(rows),
        "summary": obligations.get("summary", {}),
    }


def _program_shape(package: Path) -> dict[str, Any]:
    loaded = load_case_package(package)
    operators = loaded.program.operators
    output_use = Counter(dep for item in operators for dep in item.inputs)
    source_member_exposes_master = False
    single_use_reciprocal_wrapper = False
    if package.name == "gf-vdw-2013-eq1":
        assignments = {item.member_id: item for item in loaded.program.member_assignments}
        by_id = {item.operator_id: item for item in operators}
        first = assignments["G0001"]
        source_member_exposes_master = (
            len(first.operator_ids) == 1
            and by_id[first.operator_ids[0]].operator == "VALUE"
            and by_id[first.operator_ids[0]].latent_id == "F0001"
        )
        reciprocal_ops = [item for item in operators if item.latent_id == "F0002"]
        single_use_reciprocal_wrapper = (
            len(reciprocal_ops) == 1 and reciprocal_ops[0].operator == "COMPOSE"
        )
    return {
        "latent_count": len(loaded.program.latent_objects),
        "node_structure_count": len(loaded.program.node_structures),
        "operator_counts": dict(sorted(Counter(item.operator for item in operators).items())),
        "reused_output_count": sum(count > 1 for count in output_use.values()),
        "single_use_reciprocal_wrapper": single_use_reciprocal_wrapper,
        "source_member_exposes_master": source_member_exposes_master,
    }


def audit() -> dict[str, Any]:
    reviews_payload = _json(REVIEW_PATH)
    if reviews_payload.get("audit_policy") != AUDIT_POLICY:
        raise ValueError("review policy mismatch")
    reviews = reviews_payload.get("reviews", {})
    if set(reviews) != set(PACKAGE_IDS):
        raise ValueError("review coverage mismatch")
    retrievals = reviews_payload.get("source_retrievals", [])
    if not retrievals or any(
        not isinstance(row, Mapping)
        or not row.get("url")
        or not row.get("locator_verified")
        or not isinstance(row.get("bytes"), int)
        or not isinstance(row.get("sha256"), str)
        or len(row["sha256"]) != 64
        for row in retrievals
    ):
        raise ValueError("source retrieval review incomplete")

    freshness = freshness_audit.audit_candidates(REPO_ROOT)
    freshness_rows = {row["case_id"]: row for row in freshness["cases"]}
    cases: list[dict[str, Any]] = []
    for package_id in PACKAGE_IDS:
        package = PACKAGE_ROOT / package_id
        package_result = package_validate.validate_package(package)
        manifest = _json(package / "package.json")
        review = reviews[package_id]
        public = _public_boundary(package)
        source = _source_binding(package)
        parser = audit_parser(package)
        receipts = _receipt_summary(package)
        variants = {
            grammar_id: _ablation(package, grammar_id)
            for grammar_id in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
        }
        fresh = freshness_rows[package_id]
        blocking: list[str] = []
        if not public["namespace_matches_exact_symbols"]:
            blocking.append("PUBLIC_NAMESPACE_MISMATCH")
        if not source["strict_retrieved_source_binding"]:
            blocking.append("SOURCE_BYTES_UNBOUND")
        if review["assumption_status"] != "SOURCE_SUPPORTED":
            blocking.append("ASSUMPTION_SOURCE_GAP")
        if any(token in package_id for token in ("cr3bp", "vdw", "2013", "2017", "eq")):
            blocking.append("NONOPAQUE_PUBLIC_CASE_ID")
        if review["admission_verdict"] == "REJECT_R6_DEV_ADMISSION":
            blocking.append("DEPTH_DOWNGRADED")
        if not parser["all_machine_expressions_parse"]:
            blocking.append("PARSER_FAILURE")
        if not receipts["all_required_exact_zero"]:
            blocking.append("PROOF_GAP")
        if fresh["blocking_findings"]:
            blocking.append("DUPLICATE_OR_LEAKAGE_BLOCK")

        cases.append({
            "ablations": variants,
            "admission_ready": not blocking,
            "admission_verdict": review["admission_verdict"],
            "assumptions": {
                "findings": review["assumption_findings"],
                "status": review["assumption_status"],
            },
            "blocking_findings": blocking,
            "case_id": package_id,
            "depth": {
                "findings": review["depth_findings"],
                "independent": review["independent_depth"],
                "proposed": manifest["proposed_depth"],
            },
            "freshness": {
                "blocking_findings": fresh["blocking_findings"],
                "disposition": fresh["candidate_disposition"],
                "manual_duplicate_verdict": review["manual_duplicate_verdict"],
                "top_comparisons": fresh["top_comparisons"],
            },
            "leakage_findings": review["leakage_findings"],
            "m1": {
                "package_validator_verdict": package_result["verdict"],
                "program_id": package_result["program_id"],
                "schema_deltas": package_result["schema_deltas"],
                "tautological": package_result["tautological"],
            },
            "manifest": audit_manifest(package, manifest),
            "package_manifest_sha256": _sha(package / "package.json"),
            "parser": parser,
            "program_shape": _program_shape(package),
            "public_boundary": public,
            "receipts": receipts,
            "source": {
                **source,
                "authenticity": review["source_authenticity"],
                "findings": review["source_findings"],
            },
        })

    return {
        "admission_ready_count": sum(row["admission_ready"] for row in cases),
        "audit_date": reviews_payload["audit_date"],
        "audit_policy": AUDIT_POLICY,
        "cases": cases,
        "package_source_commit": reviews_payload["package_source_commit"],
        "scientific_packages_modified": False,
        "source_retrievals": retrievals,
        "verdict": "ZERO_ADMISSIONS" if not any(row["admission_ready"] for row in cases) else "ADMISSIONS_PRESENT",
    }


def render_markdown(report: Mapping[str, Any]) -> str:
    by_id = {row["case_id"]: row for row in report["cases"]}
    cr3bp = by_id["gf-cr3bp-2017-eq28"]
    vdw = by_id["gf-vdw-2013-eq1"]
    lines = [
        "# Independent gap-fill package admission audit",
        "",
        f"Policy: `{report['audit_policy']}`.",
        "",
        "This audit is read-only with respect to the scientific packages. Exact ZERO receipts are accepted as algebraic evidence and are not relabeled; admission remains a separate gate.",
        "",
        "## Verdict",
        "",
        f"- Admission-ready packages: **{report['admission_ready_count']}/2**.",
        f"- `gf-cr3bp-2017-eq28`: **{cr3bp['admission_verdict']}**; independent depth **{cr3bp['depth']['independent']}**.",
        f"- `gf-vdw-2013-eq1`: **{vdw['admission_verdict']}**; independent depth **{vdw['depth']['independent']}**, not R6.",
        "",
        "| package | exact receipts | M1 | parser | independent depth | admission blockers |",
        "|---|---:|---|---|---|---|",
    ]
    for row in report["cases"]:
        lines.append(
            "| `{case}` | {zero}/{total} ZERO | {m1} | {parser} | `{depth}` | {blocks} |".format(
                case=row["case_id"],
                zero=row["receipts"]["summary"].get("ZERO", 0),
                total=row["receipts"]["obligation_count"],
                m1=row["m1"]["package_validator_verdict"],
                parser="PASS" if row["parser"]["all_machine_expressions_parse"] else "FAIL",
                depth=row["depth"]["independent"],
                blocks=", ".join(f"`{item}`" for item in row["blocking_findings"]),
            )
        )
    lines += [
        "",
        "## Mechanical findings",
        "",
        "Both strict manifests are complete, both programs load through M1 with no schema deltas, every machine expression parses under the package's exact namespace, and all 12 required obligations retain exact `ZERO` evidence. `G_NO_HERMITE` compiles both programs. CR3BP fails `G_PRIMITIVE` on the named `NEWTON_DD` operator; VDW compiles under `G_PRIMITIVE`.",
        "",
        "The actual public search loader does not access either `symbols.json`: both catalogs omit `symbols_path`/`symbols_sha256`, so every public symbol is inferred with `real:false, nonzero:false`. That namespace disagrees with both packages' exact real-domain verifier namespaces and blocks admission.",
        "",
        "Each package hash-binds its normalized, package-relative dossier, but neither dossier records the bytes hash of any retrieved source. This audit independently recorded exact retrieval URLs, locators, byte counts, and SHA-256 values in `reviews.json`; that independent check does not retroactively repair package provenance.",
        "",
        "## CR3BP assessment",
        "",
        "The primary paper genuinely contains the reciprocal-square-root divided-difference rule and four coordinate-wise factorized instances. The program is a valid operational R2 representation: one shared latent, four two-node structures, and exact reconstruction. It is not primitive-grammar evidence because `NEWTON_DD` is required by name.",
        "",
        "Admission still fails: the public namespace drifts, retrieved source bytes are unbound, the proposer-visible case id is not opaque, and P002/P003 are not fully supported at their claimed locators. In particular, Eq. (28) belongs to the following damped-oscillator section; the CR3BP result is Eq. (27) and its preceding displayed identities.",
        "",
        "## Van der Waals assessment",
        "",
        "The source set is authentic and the 8/8 algebraic reconstructions are exact. It does not clear R6. G0001 already exposes the Helmholtz master, the remaining members form a familiar derivative/response graph, and the one-use reciprocal latent is a wrapper around G0006. The independent classification is `R1_DERIVATIVE_RESPONSE_GRAPH`.",
        "",
        "Admission also fails the public-namespace, source-byte, nonopaque-id, and assumption-source gates. Exact provenance is incomplete for the bulk-modulus/compressibility lowerings: G0006/G0007 omit C003, and C002's normalized formula does not contain the G0008 enthalpy relation.",
        "",
        "## Duplicate and leakage boundary",
        "",
        "The gold-free automated audit found no exact/renamed identity, sealed-Guo, trivial-CSE, first-order-LGG-only, grammar-syntax, or hidden-role blocker across the historical/current corpus. Manual review agrees that neither source identity is a renamed prior task. This does not erase the nonopaque public ids or the CR3BP named-operator giveaway.",
        "",
        "## Scope boundary",
        "",
        "No DEV or TEST manifest was created or changed. No parser, verifier, grammar, search policy, scientific package, or Guo artifact was modified.",
        "",
    ]
    return "\n".join(lines)


def write_outputs() -> dict[str, Any]:
    report = audit()
    OUTPUT_JSON.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    OUTPUT_MD.write_text(render_markdown(report), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare regenerated output with committed artifacts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = audit()
    rendered_json = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    rendered_md = render_markdown(report)
    if args.check:
        if OUTPUT_JSON.read_text(encoding="utf-8") != rendered_json:
            raise SystemExit("INDEPENDENT_GAP_FILL_ADMISSION_AUDIT.json is stale")
        if OUTPUT_MD.read_text(encoding="utf-8") != rendered_md:
            raise SystemExit("INDEPENDENT_GAP_FILL_ADMISSION_AUDIT.md is stale")
    elif args.json:
        print(rendered_json, end="")
    else:
        print(report["verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
