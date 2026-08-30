"""Deterministic fail-closed audit for the missing R4/R5 DEV slot.

The audit validates source locators and recorded diagnostic receipts, but it
has no admission path.  Because no screened identity survives freshness,
domain, leakage, and proof gates, public-case loading and M1 compilation are
explicitly not applicable rather than simulated on a rejected object.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from symbolic_compactification import get_parse_policy


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[4]
REPORT_JSON = HERE / "MINING_BOUNDARY.json"
REPORT_MD = HERE / "MINING_BOUNDARY.md"
POLICY = "RPS_R4_R5_CANDIDATE_RECOVERY_V1"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _formula_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def _validate_sources() -> dict[str, Any]:
    ledger = _json(HERE / "source_ledger.json")
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    expected_artifacts = {
        "SRC-A": (307489, "210afa1d3b8548b805c754a9757e790175405d55114fc8fd87631845b5c2b0ff"),
        "SRC-B": (301757, "6f690b01de0ce95ad450a5233ffc470ba6ca1b2b84c744a8f7fe98fd1f3f31f1"),
    }
    for source in ledger.get("sources", []):
        source_id = source.get("source_id")
        expected = expected_artifacts.get(source_id)
        if expected is None:
            errors.append(f"SOURCE_UNEXPECTED:{source_id}")
            continue
        if (source.get("artifact_bytes"), source.get("artifact_sha256")) != expected:
            errors.append(f"SOURCE_ARTIFACT_RECORD_INVALID:{source_id}")
        equations: list[dict[str, Any]] = []
        for equation in source.get("equations", []):
            formula = equation.get("formula")
            digest = equation.get("formula_sha256")
            if not isinstance(formula, str) or _formula_hash(formula) != digest:
                errors.append(f"SOURCE_FORMULA_HASH_INVALID:{source_id}")
            equations.append(
                {
                    "formula": formula,
                    "formula_sha256": digest,
                    "locator": equation.get("locator"),
                }
            )
        rows.append(
            {
                "artifact_bytes": source.get("artifact_bytes"),
                "artifact_sha256": source.get("artifact_sha256"),
                "equations": equations,
                "identifier": source.get("identifier"),
                "source_class": source.get("source_class"),
                "source_id": source_id,
                "title": source.get("title"),
                "url": source.get("url"),
            }
        )
    if {row["source_id"] for row in rows} != set(expected_artifacts):
        errors.append("SOURCE_SET_INCOMPLETE")
    return {
        "errors": sorted(set(errors)),
        "note": (
            "PDF byte counts and SHA-256 values bind the exact 2026-08-30 "
            "retrievals. The rejected-source PDFs are not copied into a case "
            "package because no candidate survived screening."
        ),
        "sources": rows,
        "status": "VALID" if not errors else "INVALID",
    }


def _historical_overlap() -> dict[str, Any]:
    task_root = REPO / "research/representation_invention/bench/tasks/test"
    required = {
        "test-a-newton-first.json": "(s(p) - s(q))/(p - q)",
        "test-a-hermite-two.json": "(ds(p) - (s(p) - s(q))/(p - q))/(p - q)",
        "test-b-piecewise-dd.json": "Piecewise(((s(p) - s(q))/(p - q), Ne(p, q)), (ds(p), True))",
    }
    errors: list[str] = []
    rows: list[dict[str, str]] = []
    for filename, expected in required.items():
        path = task_root / filename
        if not path.is_file():
            errors.append(f"HISTORICAL_TASK_MISSING:{filename}")
            continue
        payload = _json(path)
        expressions = payload.get("source_expressions", [])
        if expected not in expressions:
            errors.append(f"HISTORICAL_FORMULA_MISSING:{filename}")
        rows.append(
            {
                "formula": expected,
                "formula_sha256": _formula_hash(expected),
                "path": path.relative_to(REPO).as_posix(),
            }
        )
    return {
        "errors": errors,
        "matches": rows,
        "status": "VALID" if not errors else "INVALID",
    }


def _diagnostic_receipts() -> dict[str, Any]:
    diagnostics = HERE / "diagnostics"
    index = _json(diagnostics / "index.json")
    expected = {
        "D001": ("ZERO", "CERTIFIED", "PROVEN"),
        "D002": ("NONZERO", "UNVERIFIED", "REFUTED"),
        "D003": ("UNKNOWN", "UNVERIFIED", "PROOF_REQUIRED"),
        "D004": ("ZERO", "CERTIFIED", "PROVEN"),
    }
    errors: list[str] = []
    rows: list[dict[str, Any]] = []
    observed: set[str] = set()
    for attempt in index.get("attempts", []):
        diagnostic_id = attempt.get("diagnostic_id")
        observed.add(str(diagnostic_id))
        if diagnostic_id not in expected:
            errors.append(f"DIAGNOSTIC_UNEXPECTED:{diagnostic_id}")
            continue
        paths = {
            key: diagnostics / attempt[key]
            for key in ("candidate_path", "current_path", "symbols_path")
        }
        for key, path in paths.items():
            if not path.is_file() or _sha(path) != attempt.get(f"{key[:-5]}_sha256"):
                errors.append(f"DIAGNOSTIC_HASH_INVALID:{diagnostic_id}:{key}")
        run_root = diagnostics / "verification/workspace/runs" / attempt["run_id"]
        proposal = _json(run_root / f"steps/step_{attempt['proposal_step']:03d}.json")
        step = _json(run_root / f"steps/step_{attempt['verification_step']:03d}.json")
        manifest = _json(run_root / "manifest.json")
        verdict, lifecycle, proof = expected[diagnostic_id]
        checks = {
            "candidate_hash_bound": step.get("candidate_hash") == attempt.get("candidate_sha256"),
            "current_hash_bound": step.get("current_hash") == attempt.get("current_sha256"),
            "expected_verdict": step.get("verdict") == verdict == attempt.get("expected_verdict"),
            "lifecycle": step.get("status") == lifecycle,
            "main_proposal_recorded": (
                manifest.get("requested_proposer_mode") == "main"
                and proposal.get("status") == "HYPOTHESIS"
                and proposal.get("proof_status") == "HYPOTHESIS"
                and proposal.get("candidate_text") == step.get("candidate_text")
                and proposal.get("candidate_hash")
                == hashlib.sha256(str(proposal.get("candidate_text")).encode()).hexdigest()
                and any(
                    item.get("kind") == "proposer_candidate"
                    and item.get("invocation_mode") == "main_agent"
                    for item in proposal.get("evidence", [])
                    if isinstance(item, dict)
                )
            ),
            "proof_status": step.get("proof_status") == proof,
        }
        if diagnostic_id == "D002":
            checks["exact_counterexample"] = any(
                item.get("kind") == "exact_counterexample"
                and item.get("point") == {"x": "1/2", "y": "-2"}
                and item.get("exact_value") == "4*I*pi/25"
                for item in step.get("evidence", [])
                if isinstance(item, dict)
            )
        if diagnostic_id == "D003":
            checks["unknown_fail_closed"] = any(
                item.get("kind") == "simplification_undecided_no_exact_counterexample"
                for item in step.get("evidence", [])
                if isinstance(item, dict)
            )
        if not all(checks.values()):
            errors.append(f"DIAGNOSTIC_RECEIPT_INVALID:{diagnostic_id}")
        rows.append(
            {
                "checks": checks,
                "diagnostic_id": diagnostic_id,
                "note": attempt.get("note"),
                "run_id": attempt.get("run_id"),
                "verdict": step.get("verdict"),
            }
        )
    if observed != set(expected):
        errors.append("DIAGNOSTIC_SET_INCOMPLETE")
    return {
        "errors": sorted(set(errors)),
        "receipts": sorted(rows, key=lambda row: row["diagnostic_id"]),
        "status": "VALID" if not errors else "INVALID",
    }


def run_audit() -> dict[str, Any]:
    sources = _validate_sources()
    overlap = _historical_overlap()
    receipts = _diagnostic_receipts()
    parser_functions = sorted(get_parse_policy()["allowed_functions"])
    errors = sources["errors"] + overlap["errors"] + receipts["errors"]
    report = {
        "candidate_count": 0,
        "diagnostic_receipts": receipts,
        "historical_duplicate_audit": overlap,
        "honest_case_remaining": False,
        "m1_compile": {
            "reason": "NO_RETAINED_CANDIDATE",
            "status": "NOT_APPLICABLE"
        },
        "package_status": "NO_PACKAGE_CREATED",
        "parser_boundary": {
            "allowed_functions": parser_functions,
            "non_elementary_family_admitted": ["polygamma"],
            "polygamma_symbolic_recurrence_verdict": "UNKNOWN",
            "status": "NO_FRESH_CERTIFIABLE_R5_OBJECT_FOUND"
        },
        "policy": POLICY,
        "public_loader": {
            "reason": "NO_RETAINED_CANDIDATE",
            "status": "NOT_APPLICABLE"
        },
        "screened_leads": [
            {
                "candidate_id": "SCREEN-A",
                "disposition": "REJECTED",
                "domain": "x,y are positive real spectral values",
                "reasons": [
                    "OLD_TEST_VARIANT:test-a-newton-first",
                    "OLD_TEST_VARIANT:test-b-piecewise-dd",
                    "SOURCE_EXPOSES_DIVIDED_DIFFERENCE_TARGET",
                    "NOT_GENUINELY_FRESH"
                ],
                "scientifically_available": True,
                "source_id": "SRC-A"
            },
            {
                "candidate_id": "SCREEN-B",
                "disposition": "REJECTED",
                "domain": "positive real eigenvalues of real SPD matrices",
                "reasons": [
                    "OLD_TEST_VARIANT:test-a-hermite-two",
                    "FROZEN_NAMESPACE_CANNOT_ENFORCE_POSITIVITY",
                    "SOURCE_TO_PROGRAM_LOWERING_NONZERO_ON_FROZEN_REAL_DOMAIN",
                    "NOT_GENUINELY_FRESH"
                ],
                "scientifically_available": True,
                "source_id": "SRC-B"
            }
        ],
        "slot_disposition": {
            "R4_R5": "MISSING",
            "reason": "NO_SOURCE_BACKED_IDENTITY_SURVIVED_FRESHNESS_DOMAIN_LEAKAGE_AND_ZERO_GATES"
        },
        "source_provenance": sources,
        "status": "VALID_NEGATIVE_BOUNDARY" if not errors else "INVALID",
        "summary": (
            "Real-domain scientific formulas were found, but the parser-feasible "
            "ones are old held-out divided-difference variants. The stronger SPD "
            "lead also cannot lower soundly through the frozen namespace, and the "
            "only admitted non-elementary family remains verifier-UNKNOWN. No "
            "honest R4/R5 package remains without parser/verifier or benchmark-policy changes."
        ),
        "validation_errors": errors,
    }
    return report


def _markdown(report: dict[str, Any]) -> str:
    leads = report["screened_leads"]
    lines = [
        "# R4/R5 strict candidate-recovery boundary",
        "",
        f"Policy: `{report['policy']}`.",
        "",
        "## Verdict",
        "",
        "No strict M1 DEV candidate was created. The R4/R5 slot remains `MISSING`.",
        "This is a negative mining/package result, not evidence that the underlying",
        "scientific formulas do not exist.",
        "",
        "| lead | scientific domain | scientific formula available | package disposition |",
        "|---|---|---:|---|",
    ]
    for lead in leads:
        reasons = "; ".join(f"`{reason}`" for reason in lead["reasons"])
        lines.append(
            f"| `{lead['candidate_id']}` | {lead['domain']} | yes | rejected: {reasons} |"
        )
    lines.extend(
        [
            "",
            "## Scientific availability versus package eligibility",
            "",
            "Hiai--Petz supplies an exact positive-real logarithmic-mean kernel and",
            "explicitly defines its distinct/coalesced divided-difference form. That",
            "same explicitness makes the proposed program a direct instantiation of",
            "the already-inspected Newton/piecewise-DD held-out identities. It is not",
            "a fresh representation-search case.",
            "",
            "Bouchard et al. supplies a piecewise coefficient on real SPD spectra.",
            "After the positive-domain identity `log(x/y)=log(x)-log(y)`, its distinct",
            "coefficient is exactly the historical Hermite-two template for",
            "`F(z)=z*log(z)`, and its diagonal coefficient is the confluent stratum.",
            "The frozen symbol namespace cannot declare positivity. The exact verifier",
            "therefore correctly finds a counterexample on its broader real domain",
            "instead of certifying that source-to-program lowering.",
            "",
            "## Frozen R5 boundary",
            "",
            "The parser admits elementary functions and `polygamma`; it does not admit",
            "the broader special-function objects needed by the fresh R5 leads. The",
            "recorded symbolic polygamma recurrence remains `UNKNOWN`. A fixed value or",
            "a member that simply names `polygamma` would be a diagnostic/VALUE family,",
            "not the requested representation change.",
            "",
            "## Recorded diagnostics",
            "",
            "| id | verdict | purpose |",
            "|---|---|---|",
        ]
    )
    for row in report["diagnostic_receipts"]["receipts"]:
        lines.append(f"| `{row['diagnostic_id']}` | `{row['verdict']}` | {row['note']} |")
    lines.extend(
        [
            "",
            "All four diagnostics retain `init-session`, main-proposer hypothesis, and",
            "exact step records. ZERO is used only to establish the parser-feasible",
            "old-template mappings; it is not promoted to a case result. NONZERO and",
            "UNKNOWN remain fail-closed.",
            "",
            "## Package and method boundary",
            "",
            "`load_public_case()` and M1 compilation are `NOT_APPLICABLE`: there is no",
            "retained candidate to load or compile. No public view, package, DEV/TEST",
            "manifest, grammar change, parser change, verifier change, or ablation",
            "artifact was created. Creating dummy artifacts for a rejected identity",
            "would weaken rather than test the frozen method contract.",
            "",
            "Machine report: `MINING_BOUNDARY.json`.",
            "Source retrieval ledger: `source_ledger.json`.",
            ""
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    report = run_audit()
    payload = json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    markdown = _markdown(report)
    if args.write:
        REPORT_JSON.write_text(payload, encoding="utf-8")
        REPORT_MD.write_text(markdown, encoding="utf-8")
    if args.check:
        if not REPORT_JSON.is_file() or REPORT_JSON.read_text(encoding="utf-8") != payload:
            raise SystemExit("MINING_BOUNDARY_JSON_STALE")
        if not REPORT_MD.is_file() or REPORT_MD.read_text(encoding="utf-8") != markdown:
            raise SystemExit("MINING_BOUNDARY_MD_STALE")
    print(payload, end="")
    return 0 if report["status"] == "VALID_NEGATIVE_BOUNDARY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
