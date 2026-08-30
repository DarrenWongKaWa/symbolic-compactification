"""Build the two fail-closed real-domain recovery candidate packages.

The builder is deterministic except for engine run identifiers/timestamps in the
mandatory verification receipts.  It never downloads a source: exact retrieval
hashes and the small DLMF TeX artifacts are frozen below from the documented
2026-08-30 retrieval.  Re-running against an existing package fails closed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from symbolic_compactification import (
    ZERO,
    adjudicate_candidate,
    init_session,
    load_expression,
    record_proposal,
    set_current,
)

from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
)
from research.representation_program_search.program_ir.schema import program_from_dict


ROOT = Path(__file__).resolve().parents[4]
COLLECTION = Path(__file__).resolve().parent


def _bytes_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _bytes_sha256(path.read_bytes())


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def _write_json(path: Path, value: Any) -> None:
    _write_text(
        path,
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
    )


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_members(package: Path, members: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for member_id, text in members.items():
        relative = f"members/{member_id}.txt"
        _write_text(package / relative, text)
        rows.append(
            {
                "member_id": member_id,
                "path": relative,
                "sha256": _sha256(package / relative),
            }
        )
    return rows


def _program_with_id(raw: dict[str, Any]) -> dict[str, Any]:
    program = program_from_dict(raw)
    result = dict(raw)
    result["program_id"] = canonical_program_hash(program)
    return result


def _compile_variant(
    package: Path,
    raw: dict[str, Any],
    symbols: list[dict[str, Any]],
    grammar_id: str,
) -> tuple[dict[str, Any], Any]:
    program = program_from_dict(raw)
    result = compile_program(
        program,
        CompileContext(package.resolve(), tuple(symbols), (), grammar_id=grammar_id),
    )
    if result.status != "COMPILED" or result.tautological:
        raise RuntimeError(f"{package.name}:{grammar_id}:{result.to_dict()}")
    return result.to_dict(), result


def _verify_variants(
    package: Path,
    symbols: list[dict[str, Any]],
    variants: dict[str, tuple[dict[str, Any], Any]],
) -> None:
    workspace = package / "verification/workspace"
    attempts: list[dict[str, Any]] = []
    full_counts = {"ZERO": 0, "NONZERO": 0, "UNKNOWN": 0}
    for variant_name, (_compiled_payload, compiled) in variants.items():
        suffix = variant_name.casefold().replace("g_", "")
        for obligation in compiled.obligations:
            candidate_relative = (
                f"reference/candidates/{obligation.obligation_id}.{suffix}.txt"
            )
            candidate_path = package / candidate_relative
            _write_text(candidate_path, obligation.candidate_expression + "\n")
            member_path = package / obligation.current_path
            current = load_expression(member_path, symbols)
            candidate = load_expression(candidate_path, symbols)
            session = init_session(
                str(workspace),
                meta={
                    "case_package": package.name,
                    "grammar_variant": variant_name,
                    "obligation_id": obligation.obligation_id,
                },
                requested_proposer_mode="main",
            )
            set_current(session, current)
            record_proposal(
                session,
                {
                    "assumptions_status": "DECLARED",
                    "candidate_expression_or_rewrite": candidate.text,
                    "candidate_id": (
                        f"{package.name}-{variant_name}-{obligation.obligation_id}"
                    ),
                    "confidence": "high",
                    "expected_structural_benefit": (
                        "A legal compiled program output reconstructs one grounded member."
                    ),
                    "hypothesis": "The compiled output is exactly equivalent to the member.",
                    "rationale": "The transformation is the selected executable M1 output.",
                    "required_assumptions": ["package ScientificAssumptionContract"],
                    "status": "HYPOTHESIS",
                    "suggested_verification_strategy": (
                        "Run the exact verifier on the hash-bound member and candidate files."
                    ),
                },
            )
            outcome = adjudicate_candidate(
                session,
                candidate,
                meta={
                    "case_package": package.name,
                    "grammar_variant": variant_name,
                    "obligation_id": obligation.obligation_id,
                },
            )
            if outcome.result.verdict != ZERO:
                raise RuntimeError(
                    f"{package.name}:{variant_name}:{obligation.obligation_id}:"
                    f"{outcome.result.to_dict()}"
                )
            attempts.append(
                {
                    "candidate_path": candidate_relative,
                    "member_id": obligation.member_id,
                    "obligation_id": obligation.obligation_id,
                    "program_variant": variant_name,
                    "proposal_step": 1,
                    "run_id": session.run_id,
                    "verification_step": 2,
                    "verdict": outcome.result.verdict,
                }
            )
            if variant_name == "G_FULL":
                full_counts[outcome.result.verdict] += 1
    _write_json(
        package / "verification/index.json",
        {
            "attempts": attempts,
            "required_g_full_verdicts": full_counts,
            "schema_version": "RPSVerificationIndexV1",
        },
    )
    full_attempts = {
        attempt["obligation_id"]: attempt
        for attempt in attempts
        if attempt["program_variant"] == "G_FULL"
    }
    obligation_rows: list[dict[str, Any]] = []
    for obligation in _read_json(package / "reference/obligations.json")["obligations"]:
        attempt = full_attempts[obligation["obligation_id"]]
        current_path = f"members/{attempt['member_id']}.txt"
        candidate_path = attempt["candidate_path"]
        run_id = attempt["run_id"]
        obligation_rows.append(
            {
                "candidate_path": candidate_path,
                "candidate_sha256": _sha256(package / candidate_path),
                "current_member_id": attempt["member_id"],
                "current_path": current_path,
                "current_sha256": _sha256(package / current_path),
                "obligation_id": attempt["obligation_id"],
                "proof_status": "PROVEN",
                "required": True,
                "run_id": run_id,
                "session_path": f"verification/workspace/runs/{run_id}",
                "step_path": (
                    f"verification/workspace/runs/{run_id}/steps/step_002.json"
                ),
                "verdict": "ZERO",
            }
        )
    _write_json(
        package / "reference/obligations.json",
        {
            "obligations": obligation_rows,
            "schema_version": "RPSObligationsV1",
            "summary": full_counts,
        },
    )


def _finish_manifest(
    package: Path,
    *,
    depth: str,
    source_identity: str,
    receipt_count: int,
) -> None:
    artifacts = [
        {"path": path.relative_to(package).as_posix(), "sha256": _sha256(path)}
        for path in sorted(package.rglob("*"))
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    ]
    _write_json(
        package / "package.json",
        {
            "admission_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "artifact_hashes": artifacts,
            "audited_depth": depth,
            "eligibility": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE",
            "manifest_exclusion": (
                "package.json is excluded because a file cannot contain its own stable hash."
            ),
            "package_id": package.name,
            "package_status": "PACKAGE_READY",
            "schema_version": "RPSCasePackageV1",
            "source_identity": source_identity,
            "verdict_totals": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": receipt_count},
        },
    )


def _build_r3() -> None:
    package = COLLECTION / "rps-real-c3j9"
    if package.exists():
        raise RuntimeError(f"REFUSE_EXISTING_PACKAGE:{package}")
    package.mkdir(parents=True)
    members = {
        "M3A1": "p*(log(y)-log(x))/(y-x)\n",
        "M3A2": "p*q*(((log(y)-log(x))/(y-x))-1/x)/(y-x)\n",
        "M3A3": "p*q*(1/y-(log(y)-log(x))/(y-x))/(y-x)\n",
    }
    source_members = _source_members(package, members)
    symbols = [
        {"name": "x", "nonzero": True, "real": True},
        {"name": "y", "nonzero": True, "real": True},
        {"name": "p", "nonzero": False, "real": True},
        {"name": "q", "nonzero": False, "real": True},
    ]
    _write_json(package / "symbols.json", {"functions": [], "symbols": symbols})
    assumptions = {
        "predicates": [
            {
                "predicate_id": "P3A1",
                "source": "evaluator source locator S3P1",
                "statement": (
                    "x and y are distinct positive real eigenvalues; the displayed "
                    "quotients are used only on x != y."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P3A2",
                "source": "evaluator source locator S3P2",
                "statement": (
                    "p and q are arbitrary real coefficients of real-symmetric "
                    "direction matrices."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P3A3",
                "source": "evaluator source locator S3P3",
                "statement": (
                    "log is smooth on the open positive-real spectral interval, so "
                    "the first and second derivative formulas used here exist."
                ),
                "status": "DERIVED",
            },
            {
                "predicate_id": "P3A4",
                "source": "evaluator source locator S3P4",
                "statement": (
                    "Each retained matrix response uses an affine real-symmetric "
                    "perturbation family, so its mixed base-matrix derivative is zero."
                ),
                "status": "DECLARED",
            },
        ],
        "schema_version": "ScientificAssumptionContractV1",
        "status": "COMPLETE",
        "symbols_artifact": "symbols.json",
        "verifier_scope_note": (
            "The symbol namespace exactly records real and nonzero scalar symbols. "
            "The relational predicates x>0, y>0, and x!=y remain explicit in this "
            "contract; exact ZERO does not silently add or discharge them."
        ),
    }
    _write_json(package / "assumptions.json", assumptions)
    catalog = {
        "members": [
            {"locator_id": f"S3L{i}", **row}
            for i, row in enumerate(source_members, start=1)
        ],
        "schema_version": "RPSMemberCatalogV1",
    }
    _write_json(package / "source_catalog.json", catalog)
    _write_json(
        package / "proposer_view.json",
        {
            "assumptions": {
                "path": "assumptions.json",
                "sha256": _sha256(package / "assumptions.json"),
            },
            "case_id": "C3J9",
            "schema_version": "RPSProposerViewV1",
            "source_catalog": {
                "members": [
                    {key: row[key] for key in ("member_id", "path", "sha256")}
                    for row in source_members
                ],
                "path": "source_catalog.json",
                "sha256": _sha256(package / "source_catalog.json"),
            },
            "structural_observations": {
                "argument_families": ["x", "y"],
                "member_count": 3,
                "shared_functions": ["log"],
                "source_scope": (
                    "real scalar components on a declared positive, distinct-parameter stratum"
                ),
            },
        },
    )
    dossier = {
        "domain": "real-symmetric matrix-function response",
        "identity": "C3J9",
        "primary_source": {
            "artifact_sha256": (
                "732b25ee69191ccd32a936ad3f61bced8e97e2f77e59b79da94bea0acc2e281e"
            ),
            "doi": "10.1137/23M1580589",
            "retrieved_on": "2026-08-30",
            "title": "A Unifying Framework for Higher Order Derivatives of Matrix Functions",
            "url": "https://arxiv.org/pdf/2306.15814",
        },
        "predicate_locators": {
            "S3P1": "pages 9--10, equations (4.3)--(4.5), positive-spectrum log specialization declared in source/lowering.json",
            "S3P2": "pages 9--10, Hermitian hypothesis above (4.3) and explicit real A,E statement below (5.2)",
            "S3P3": "Theorem 3.3 smoothness hypothesis and scalar log domain recorded in source/lowering.json",
            "S3P4": "equation (4.5) U^(alpha) term plus the affine scientific-instance declaration in source/lowering.json",
        },
        "source_locator": (
            "arXiv v1 pages 9--10, equations (4.3)--(4.5); published as SIAM "
            "J. Matrix Anal. Appl. 45(1), 504--528 (2024)"
        ),
        "source_scope": (
            "Equation (4.5) gives the second-order formula when A at the base "
            "point is Hermitian. The paper explicitly also treats real A and E."
        ),
        "visual_formula_check": (
            "PDF pages 9--10 rendered with Poppler at 150 dpi; equations (4.3)--"
            "(4.5) and the real A,E statement below (5.2) were visually inspected."
        ),
    }
    _write_json(package / "source/dossier.json", dossier)
    lowering = {
        "derivation_status": "DERIVED_FROM_PRIMARY_SOURCE",
        "fixed_instance": {
            "base_matrix": "diag(x,y)",
            "dimension": 2,
            "function": "log on the positive-real spectral interval",
            "perturbation_family": "A(s,t)=diag(x,y)+s*E_beta+t*E_gamma",
            "stratum": "x>0, y>0, x!=y",
        },
        "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE",
        "members": {
            "M3A1": (
                "Equation (4.4), component (1,2), with the real-symmetric direction "
                "p*(e12+e21)."
            ),
            "M3A2": (
                "Equation (4.5), component (1,2), with beta-direction p*e11 and "
                "gamma-direction q*(e12+e21), isolating the node multiset (x,x,y)."
            ),
            "M3A3": (
                "Equation (4.5), component (1,2), with beta-direction "
                "q*(e12+e21) and gamma-direction p*e22, isolating (x,y,y)."
            ),
        },
        "notation_expansion": {
            "log[x,y]": "(log(y)-log(x))/(y-x)",
            "log[x,x,y]": "(log[x,y]-1/x)/(y-x)",
            "log[x,y,y]": "(1/y-log[x,y])/(y-x)",
        },
        "source_basis": (
            "The fixed directions leave exactly one path term in the relevant sum "
            "of equation (4.5); affine dependence makes its U^(alpha) term zero. "
            "The package certifies only these scalar components, not the general "
            "matrix theorem."
        ),
    }
    _write_json(package / "source/lowering.json", lowering)
    _write_json(
        package / "source_manifest.json",
        {
            "member_lowering": {
                member_id: f"source/lowering.json#{member_id}"
                for member_id in members
            },
            "schema_version": "RPSSourceManifestV1",
            "source_dossier": {
                "path": "source/dossier.json",
                "sha256": _sha256(package / "source/dossier.json"),
            },
            "sources": [dossier["primary_source"] | {"locator": dossier["source_locator"]}],
        },
    )
    obligations = [
        {
            "current_member_id": row["member_id"],
            "obligation_id": f"O3R{i}",
            "required": True,
        }
        for i, row in enumerate(source_members, start=1)
    ]
    _write_json(
        package / "reference/obligations.json",
        {"obligations": obligations, "schema_version": "RPSObligationCatalogV1"},
    )
    common = {
        "assumption_statuses": {
            "P3A1": "DECLARED",
            "P3A2": "DECLARED",
            "P3A3": "DERIVED",
            "P3A4": "DECLARED",
        },
        "assumptions_used": ["P3A1", "P3A2", "P3A3", "P3A4"],
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {
            "M3A1": {"component": "first_12", "nodes": ["x", "y"]},
            "M3A2": {"component": "second_12", "nodes": ["x", "x", "y"]},
            "M3A3": {"component": "second_12", "nodes": ["x", "y", "y"]},
        },
        "latent_objects": [
            {
                "expression": "log(u)",
                "form": "FUNCTION_1",
                "latent_id": "F3L1",
                "parameters": ["u"],
            }
        ],
        "source_members": source_members,
        "unexplained_members": [],
    }
    full = _program_with_id(
        common
        | {
            "member_assignments": [
                {"member_id": "M3A1", "operator_ids": ["OP3N", "OP3L1"], "output": "c3_1"},
                {"member_id": "M3A2", "operator_ids": ["OP3H1", "OP3L2"], "output": "c3_2"},
                {"member_id": "M3A3", "operator_ids": ["OP3H2", "OP3L3"], "output": "c3_3"},
            ],
            "node_structures": [
                {"node_id": "N3D1", "nodes": ["x", "y"]},
                {"node_id": "N3D2", "nodes": ["x", "x", "y"]},
                {"node_id": "N3D3", "nodes": ["x", "y", "y"]},
            ],
            "obligations": [
                {"member_id": "M3A1", "obligation_id": "O3R1", "output": "c3_1", "required": True},
                {"member_id": "M3A2", "obligation_id": "O3R2", "output": "c3_2", "required": True},
                {"member_id": "M3A3", "obligation_id": "O3R3", "output": "c3_3", "required": True},
            ],
            "operators": [
                {"arguments": {"nodes": "N3D1"}, "inputs": [], "latent_id": "F3L1", "operator": "NEWTON_DD", "operator_id": "OP3N", "output": "d3_xy"},
                {"arguments": {"coefficients": ["p"]}, "inputs": ["d3_xy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "OP3L1", "output": "c3_1"},
                {"arguments": {"nodes": "N3D2"}, "inputs": [], "latent_id": "F3L1", "operator": "HERMITE_DD", "operator_id": "OP3H1", "output": "d3_xxy"},
                {"arguments": {"coefficients": ["p*q"]}, "inputs": ["d3_xxy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "OP3L2", "output": "c3_2"},
                {"arguments": {"nodes": "N3D3"}, "inputs": [], "latent_id": "F3L1", "operator": "HERMITE_DD", "operator_id": "OP3H2", "output": "d3_xyy"},
                {"arguments": {"coefficients": ["p*q"]}, "inputs": ["d3_xyy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "OP3L3", "output": "c3_3"},
            ],
            "representation_depth": "R3_REPEATED_NODE",
        }
    )
    primitive = _program_with_id(
        common
        | {
            "member_assignments": [
                {"member_id": "M3A1", "operator_ids": ["P3X", "P3Y", "P3DD", "P3L1"], "output": "pc3_1"},
                {"member_id": "M3A2", "operator_ids": ["P3X", "P3Y", "P3DD", "P3D", "P3DX", "P3XXY", "P3L2"], "output": "pc3_2"},
                {"member_id": "M3A3", "operator_ids": ["P3D", "P3DY", "P3X", "P3Y", "P3DD", "P3XYY", "P3L3"], "output": "pc3_3"},
            ],
            "node_structures": [],
            "obligations": [
                {"member_id": "M3A1", "obligation_id": "O3R1", "output": "pc3_1", "required": True},
                {"member_id": "M3A2", "obligation_id": "O3R2", "output": "pc3_2", "required": True},
                {"member_id": "M3A3", "obligation_id": "O3R3", "output": "pc3_3", "required": True},
            ],
            "operators": [
                {"arguments": {"node": "x"}, "inputs": [], "latent_id": "F3L1", "operator": "VALUE", "operator_id": "P3X", "output": "p3_fx"},
                {"arguments": {"node": "y"}, "inputs": [], "latent_id": "F3L1", "operator": "VALUE", "operator_id": "P3Y", "output": "p3_fy"},
                {"arguments": {"coefficients": ["-1/(y-x)", "1/(y-x)"]}, "inputs": ["p3_fx", "p3_fy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3DD", "output": "p3_dxy"},
                {"arguments": {"variable": "u"}, "inputs": [], "latent_id": "F3L1", "operator": "DERIVATIVE", "operator_id": "P3D", "output": "p3_df"},
                {"arguments": {"parameter": "u", "value": "x"}, "inputs": ["p3_df"], "latent_id": "F3L1", "operator": "SUBSTITUTE", "operator_id": "P3DX", "output": "p3_dfx"},
                {"arguments": {"parameter": "u", "value": "y"}, "inputs": ["p3_df"], "latent_id": "F3L1", "operator": "SUBSTITUTE", "operator_id": "P3DY", "output": "p3_dfy"},
                {"arguments": {"coefficients": ["1/(y-x)", "-1/(y-x)"]}, "inputs": ["p3_dxy", "p3_dfx"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3XXY", "output": "p3_xxy"},
                {"arguments": {"coefficients": ["1/(y-x)", "-1/(y-x)"]}, "inputs": ["p3_dfy", "p3_dxy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3XYY", "output": "p3_xyy"},
                {"arguments": {"coefficients": ["p"]}, "inputs": ["p3_dxy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3L1", "output": "pc3_1"},
                {"arguments": {"coefficients": ["p*q"]}, "inputs": ["p3_xxy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3L2", "output": "pc3_2"},
                {"arguments": {"coefficients": ["p*q"]}, "inputs": ["p3_xyy"], "latent_id": "F3L1", "operator": "LINEAR_COMBINATION", "operator_id": "P3L3", "output": "pc3_3"},
            ],
            "representation_depth": "R3_COMPOSITIONAL_REPEATED_NODE",
        }
    )
    _write_json(package / "reference/program.json", full)
    _write_json(package / "reference/ablations/G_NO_HERMITE.program.json", primitive)
    _write_json(package / "reference/ablations/G_PRIMITIVE.program.json", primitive)
    variants = {
        "G_FULL": _compile_variant(package, full, symbols, "G_FULL"),
        "G_NO_HERMITE": _compile_variant(package, primitive, symbols, "G_NO_HERMITE"),
        "G_PRIMITIVE": _compile_variant(package, primitive, symbols, "G_PRIMITIVE"),
    }
    _write_json(
        package / "reference/review.json",
        {
            "baseline_assessment": {
                "cse": "MODERATE_VISIBLE_LOG_KERNEL_REUSE_BUT_NO_REPEATED_NODE_CONSTRUCTOR",
                "first_order_lgg_only": False,
                "tautological": False,
            },
            "candidate_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "depth_assessment": "R3_REPEATED_NODE",
            "duplicate_assessment": (
                "No exact or alpha-renamed member match in the current package pool. "
                "Thematic overlap with historical first-order matrix-function response "
                "is retained as a manual-review risk; this source identity is second-order "
                "log response, not a renamed historical member."
            ),
            "grammar_assessment": {
                "g_full": variants["G_FULL"][0]["status"],
                "g_no_hermite": variants["G_NO_HERMITE"][0]["status"],
                "g_primitive": variants["G_PRIMITIVE"][0]["status"],
                "named_primitive_required": False,
            },
            "leakage_assessment": "OPAQUE_PROPOSER_VIEW_WITHOUT_SOURCE_OR_TARGET_NAMES",
            "review_policy": "RPS_REAL_DOMAIN_RECOVERY_REVIEW_V1",
        },
    )
    _verify_variants(package, symbols, variants)
    _finish_manifest(
        package,
        depth="R3_REPEATED_NODE",
        source_identity="Rubensson-2024-equations-4.3--4.5-real-SPD-log",
        receipt_count=9,
    )


def _build_r5() -> None:
    package = COLLECTION / "rps-real-c8q2"
    if package.exists():
        raise RuntimeError(f"REFUSE_EXISTING_PACKAGE:{package}")
    package.mkdir(parents=True)
    members = {
        "M8B1": "sin(x)/x\n",
        "M8B2": "sin(x)/x**2 - cos(x)/x\n",
        "M8B3": "(-1/x + 3/x**3)*sin(x) - 3*cos(x)/x**2\n",
    }
    source_members = _source_members(package, members)
    symbols = [{"name": "x", "nonzero": True, "real": True}]
    _write_json(package / "symbols.json", {"functions": [], "symbols": symbols})
    assumptions = {
        "predicates": [
            {
                "predicate_id": "P8A1",
                "source": "evaluator source locator S8P1",
                "statement": (
                    "x is a real nonzero argument. This is an explicit restriction of "
                    "identities stated for complex z, whose domain contains the retained "
                    "real subdomain."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P8A2",
                "source": "evaluator source locator S8P2",
                "statement": "The retained orders 0, 1, and 2 are nonnegative integers.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P8A3",
                "source": "P8A1 and evaluator source locator S8P3",
                "statement": "Every displayed denominator is nonzero because x != 0.",
                "status": "DERIVED",
            },
        ],
        "schema_version": "ScientificAssumptionContractV1",
        "status": "COMPLETE",
        "symbols_artifact": "symbols.json",
        "verifier_scope_note": (
            "The frozen namespace exactly records the retained real, nonzero argument. "
            "No zero-limit continuation, complex-domain receipt, or unstated positivity "
            "claim is used."
        ),
    }
    _write_json(package / "assumptions.json", assumptions)
    catalog = {
        "members": [
            {"locator_id": f"S8L{i}", **row}
            for i, row in enumerate(source_members, start=1)
        ],
        "schema_version": "RPSMemberCatalogV1",
    }
    _write_json(package / "source_catalog.json", catalog)
    _write_json(
        package / "proposer_view.json",
        {
            "assumptions": {
                "path": "assumptions.json",
                "sha256": _sha256(package / "assumptions.json"),
            },
            "case_id": "C8Q2",
            "schema_version": "RPSProposerViewV1",
            "source_catalog": {
                "members": [
                    {key: row[key] for key in ("member_id", "path", "sha256")}
                    for row in source_members
                ],
                "path": "source_catalog.json",
                "sha256": _sha256(package / "source_catalog.json"),
            },
            "structural_observations": {
                "argument_families": ["x"],
                "member_count": 3,
                "shared_functions": ["sin", "cos"],
                "source_scope": "real nonzero scalar argument",
            },
        },
    )
    upstream = {
        "10.49.E3a.tex": "$\\mathsf{j}_{0}\\left(z\\right)=\\frac{\\sin z}{z},$",
        "10.49.E3b.tex": "$\\mathsf{j}_{1}\\left(z\\right)=\\frac{\\sin z}{z^{2}}-\\frac{\\cos z}{z},$",
        "10.49.E3c.tex": "$\\mathsf{j}_{2}\\left(z\\right)=\\left(-\\frac{1}{z}+\\frac{3}{z^{3}}\\right)\\sin z-%\n\\frac{3}{z^{2}}\\cos z.$",
        "10.49.E14a.tex": "\\[\\mathsf{j}_{n}\\left(z\\right)=z^{n}\\left(-\\frac{1}{z}\\frac{\\mathrm{d}}{\\mathrm{%\nd}z}\\right)^{n}\\frac{\\sin z}{z},\\]",
        "10.51.E1a.tex": "\\[f_{n-1}(z)+f_{n+1}(z)=((2n+1)/z)f_{n}(z),\\]",
    }
    for name, text in upstream.items():
        _write_text(package / "source/upstream" / name, text)
    upstream_rows = [
        {
            "artifact_sha256": _sha256(package / "source/upstream" / name),
            "locator": name.removesuffix(".tex"),
            "path": f"source/upstream/{name}",
            "retrieved_on": "2026-08-30",
            "url": f"https://dlmf.nist.gov/{name}",
        }
        for name in upstream
    ]
    external_rows = [
        {
            "artifact_sha256": (
                "419e460696027ff105fbcd0302ac0ccf774ba4c870e85d51cc93fc0f8f5f3045"
            ),
            "locator": "DLMF 10.73(ii), spherical waves",
            "retrieved_on": "2026-08-30",
            "url": "https://dlmf.nist.gov/10.73.ii",
        }
    ]
    dossier = {
        "authority": "NIST Digital Library of Mathematical Functions",
        "domain": "real radial Helmholtz special-function kernels",
        "identity": "C8Q2",
        "retrieved_on": "2026-08-30",
        "predicate_locators": {
            "S8P1": "10.49.3 identities restricted to real x!=0; 10.73(ii) records the real spherical-wave use",
            "S8P2": "sections 10.47--10.60 standing nonnegative-integer order convention",
            "S8P3": "10.49.E3a--E3c displayed quotient forms",
        },
        "source_locators": [
            "DLMF 10.49.3 (three explicit orders)",
            "DLMF 10.49.14 (differential generator)",
            "DLMF 10.51.1 (order recurrence)",
            "DLMF 10.73(ii) (spherical Helmholtz application with real argument)",
        ],
        "source_urls": [
            "https://dlmf.nist.gov/10.49",
            "https://dlmf.nist.gov/10.51",
            "https://dlmf.nist.gov/10.73.ii",
        ],
    }
    _write_json(package / "source/dossier.json", dossier)
    lowering = {
        "derivation_status": "DIRECT_TRANSLATION_OF_AUTHORITATIVE_SOURCE",
        "fixed_instance": {
            "argument": "real x != 0",
            "orders": [0, 1, 2],
        },
        "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE",
        "members": {
            "M8B1": "DLMF 10.49.E3a with z replaced by the retained real x.",
            "M8B2": "DLMF 10.49.E3b with z replaced by x.",
            "M8B3": "DLMF 10.49.E3c with z replaced by x.",
        },
        "program_basis": (
            "DLMF 10.49.E14a supplies the differential generator and "
            "10.51.E1a supplies the three-term recurrence."
        ),
    }
    _write_json(package / "source/lowering.json", lowering)
    _write_json(
        package / "source_manifest.json",
        {
            "member_lowering": {
                member_id: f"source/lowering.json#{member_id}"
                for member_id in members
            },
            "schema_version": "RPSSourceManifestV1",
            "source_dossier": {
                "path": "source/dossier.json",
                "sha256": _sha256(package / "source/dossier.json"),
            },
            "sources": upstream_rows + external_rows,
        },
    )
    obligations = [
        {
            "current_member_id": row["member_id"],
            "obligation_id": f"O8R{i}",
            "required": True,
        }
        for i, row in enumerate(source_members, start=1)
    ]
    _write_json(
        package / "reference/obligations.json",
        {"obligations": obligations, "schema_version": "RPSObligationCatalogV1"},
    )
    raw = {
        "assumption_statuses": {"P8A1": "DECLARED", "P8A2": "DECLARED", "P8A3": "DERIVED"},
        "assumptions_used": ["P8A1", "P8A2", "P8A3"],
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {
            "M8B1": {"order": 0},
            "M8B2": {"order": 1},
            "M8B3": {"order": 2},
        },
        "latent_objects": [
            {
                "expression": "sin(u)/u",
                "form": "SCALAR_KERNEL",
                "latent_id": "F8S1",
                "parameters": ["u"],
            }
        ],
        "member_assignments": [
            {"member_id": "M8B1", "operator_ids": ["OP8V"], "output": "c8_0"},
            {"member_id": "M8B2", "operator_ids": ["OP8D", "OP8S", "OP8L1"], "output": "c8_1"},
            {"member_id": "M8B3", "operator_ids": ["OP8D", "OP8S", "OP8L1", "OP8V", "OP8L2"], "output": "c8_2"},
        ],
        "node_structures": [],
        "obligations": [
            {"member_id": "M8B1", "obligation_id": "O8R1", "output": "c8_0", "required": True},
            {"member_id": "M8B2", "obligation_id": "O8R2", "output": "c8_1", "required": True},
            {"member_id": "M8B3", "obligation_id": "O8R3", "output": "c8_2", "required": True},
        ],
        "operators": [
            {"arguments": {"node": "x"}, "inputs": [], "latent_id": "F8S1", "operator": "VALUE", "operator_id": "OP8V", "output": "c8_0"},
            {"arguments": {"variable": "u"}, "inputs": [], "latent_id": "F8S1", "operator": "DERIVATIVE", "operator_id": "OP8D", "output": "d8_f"},
            {"arguments": {"parameter": "u", "value": "x"}, "inputs": ["d8_f"], "latent_id": "F8S1", "operator": "SUBSTITUTE", "operator_id": "OP8S", "output": "d8_x"},
            {"arguments": {"coefficients": ["-1"]}, "inputs": ["d8_x"], "latent_id": "F8S1", "operator": "LINEAR_COMBINATION", "operator_id": "OP8L1", "output": "c8_1"},
            {"arguments": {"coefficients": ["3/x", "-1"]}, "inputs": ["c8_1", "c8_0"], "latent_id": "F8S1", "operator": "LINEAR_COMBINATION", "operator_id": "OP8L2", "output": "c8_2"},
        ],
        "representation_depth": "R5_SPECIAL_FUNCTION_FAMILY",
        "source_members": source_members,
        "unexplained_members": [],
    }
    program = _program_with_id(raw)
    _write_json(package / "reference/program.json", program)
    _write_json(package / "reference/ablations/G_NO_HERMITE.program.json", program)
    _write_json(package / "reference/ablations/G_PRIMITIVE.program.json", program)
    variants = {
        "G_FULL": _compile_variant(package, program, symbols, "G_FULL"),
        "G_NO_HERMITE": _compile_variant(package, program, symbols, "G_NO_HERMITE"),
        "G_PRIMITIVE": _compile_variant(package, program, symbols, "G_PRIMITIVE"),
    }
    _write_json(
        package / "reference/review.json",
        {
            "baseline_assessment": {
                "cse": (
                    "VISIBLE_TRIGONOMETRIC_ATOMS_BUT_CSE_DOES_NOT_SUPPLY_THE_"
                    "DIFFERENTIAL_GENERATOR_OR_ORDER_RECURRENCE"
                ),
                "first_order_lgg_only": False,
                "tautological": False,
            },
            "candidate_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "depth_assessment": "R5_SPECIAL_FUNCTION_FAMILY",
            "depth_downgrade_risk": (
                "A reviewer may downgrade the fixed three-order slice if semantic family "
                "coverage is judged insufficient; no R5 claim is admitted here."
            ),
            "duplicate_assessment": (
                "No exact or alpha-renamed member match in the current package pool or "
                "historical benchmark scan. The identity is not a phi, resolvent, thermal, "
                "or matrix-function divided-difference variant."
            ),
            "grammar_assessment": {
                "g_full": variants["G_FULL"][0]["status"],
                "g_no_hermite": variants["G_NO_HERMITE"][0]["status"],
                "g_primitive": variants["G_PRIMITIVE"][0]["status"],
                "named_primitive_required": False,
            },
            "leakage_assessment": "OPAQUE_PROPOSER_VIEW_WITHOUT_SPECIAL_FUNCTION_OR_RECURRENCE_NAMES",
            "review_policy": "RPS_REAL_DOMAIN_RECOVERY_REVIEW_V1",
        },
    )
    _verify_variants(package, symbols, variants)
    _finish_manifest(
        package,
        depth="R5_SPECIAL_FUNCTION_FAMILY",
        source_identity="NIST-DLMF-10.49-real-radial-orders-0--2",
        receipt_count=9,
    )


def main() -> int:
    COLLECTION.mkdir(parents=True, exist_ok=True)
    _build_r3()
    _build_r5()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
