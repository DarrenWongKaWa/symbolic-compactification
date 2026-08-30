"""Build one strict candidate-only R3 package from frozen source equations.

The builder performs no network access and no benchmark admission.  It writes
one immutable RPSCasePackageV1, compiles the named and primitive reference
programs, and records every resulting obligation through the normal exact
verification session pipeline.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

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
PACKAGE_ID = "rps-case-q7v3"
CASE_ID = "Q7V3"

SOURCE_ARCHIVE_SHA256 = "e8214b47d29be06dcbd8e77f8e6d79568d6d25b67732f4ab543524b8b5a74ea7"
SOURCE_TEX_SHA256 = "fbae74b5e4422e5428404732ecbff74311077a0dce43352a0bd69e654ba5fd95"
SOURCE_EQUATIONS = r"""\begin{equation}\label{eq:integral_representation}
L_f^{(k)}(A, E_1, \dots E_k) = \frac{1}{2\pi i} \int_\Gamma \sum\limits_{\pi \in S_k} f(\zeta) M_\pi(\zeta; A, E_1,\dots, E_k) \d \zeta,
\end{equation}
where""" + " \n" + r"""\begin{equation}\label{eq:integrand_M}
M_\pi(\zeta; A, E_1,\dots, E_k) = (\zeta I - A)^{-1}E_{\pi(1)}(\zeta I - A)^{-1}E_{\pi(2)}(\zeta I - A)^{-1}\cdots E_{\pi(k)}(\zeta I - A)^{-1}.
\end{equation}
"""

MEMBERS = {
    "M01": (
        "p*q*r*(a*exp(a) + a*exp(b) - b*exp(a) - b*exp(b) "
        "- 2*exp(a) + 2*exp(b))/((a - b)**3)\n"
    ),
    "M02": (
        "p*q*r*(a**2*b*exp(a) - a**2*c*exp(a) + a**2*exp(b) "
        "- a**2*exp(c) - a*b**2*exp(a) - 2*a*b*exp(a) "
        "+ 2*a*b*exp(c) + a*c**2*exp(a) + 2*a*c*exp(a) "
        "- 2*a*c*exp(b) + b**2*c*exp(a) + b**2*exp(a) "
        "- b**2*exp(c) - b*c**2*exp(a) - c**2*exp(a) "
        "+ c**2*exp(b))/((a - b)**2*(a - c)**2*(b - c))\n"
    ),
    "M03": (
        "p*q*r*(a**2*b*exp(c) - a**2*c*exp(c) - a**2*exp(b) "
        "+ a**2*exp(c) - a*b**2*exp(c) + a*c**2*exp(c) "
        "+ 2*a*c*exp(b) - 2*a*c*exp(c) + b**2*c*exp(c) "
        "+ b**2*exp(a) - b**2*exp(c) - b*c**2*exp(c) "
        "- 2*b*c*exp(a) + 2*b*c*exp(c) + c**2*exp(a) "
        "- c**2*exp(b))/((a - b)*(a - c)**2*(b - c)**2)\n"
    ),
}

SYMBOLS = [
    {"name": name, "nonzero": False, "real": True}
    for name in ("a", "b", "c", "p", "q", "r")
]

ASSUMPTION_STATUSES = {
    "P01": "DECLARED",
    "P02": "DECLARED",
    "P03": "DERIVED",
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def _source_members(package: Path) -> list[dict[str, str]]:
    rows = []
    for member_id, text in MEMBERS.items():
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


def _closure(operators: list[dict[str, Any]], output: str) -> list[str]:
    by_output = {item["output"]: item for item in operators}
    found: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in by_output:
            return
        seen.add(name)
        operator = by_output[name]
        for child in operator.get("inputs", []):
            visit(child)
        found.append(operator["operator_id"])

    visit(output)
    return found


def _operator(
    operator_id: str,
    operator: str,
    output: str,
    *,
    inputs: Iterable[str] = (),
    arguments: dict[str, Any] | None = None,
    latent_id: str = "F01",
) -> dict[str, Any]:
    return {
        "arguments": arguments or {},
        "inputs": list(inputs),
        "latent_id": latent_id,
        "operator": operator,
        "operator_id": operator_id,
        "output": output,
    }


def _program(
    source_members: list[dict[str, str]],
    *,
    primitive: bool,
) -> dict[str, Any]:
    if primitive:
        operators = [
            _operator("OP01", "VALUE", "v_a", arguments={"node": "a"}),
            _operator("OP02", "VALUE", "v_b", arguments={"node": "b"}),
            _operator("OP03", "VALUE", "v_c", arguments={"node": "c"}),
            _operator(
                "OP04",
                "DERIVATIVE",
                "d1_z",
                arguments={"order": 1, "variable": "z"},
            ),
            _operator(
                "OP05",
                "SUBSTITUTE",
                "d1_a",
                inputs=("d1_z",),
                arguments={"parameter": "z", "value": "a"},
            ),
            _operator(
                "OP06",
                "SUBSTITUTE",
                "d1_b",
                inputs=("d1_z",),
                arguments={"parameter": "z", "value": "b"},
            ),
            _operator(
                "OP07",
                "SUBSTITUTE",
                "d1_c",
                inputs=("d1_z",),
                arguments={"parameter": "z", "value": "c"},
            ),
            _operator(
                "OP08",
                "LINEAR_COMBINATION",
                "d_ab",
                inputs=("v_b", "v_a"),
                arguments={"coefficients": ["1/(b-a)", "-1/(b-a)"]},
            ),
            _operator(
                "OP09",
                "LINEAR_COMBINATION",
                "d_bc",
                inputs=("v_c", "v_b"),
                arguments={"coefficients": ["1/(c-b)", "-1/(c-b)"]},
            ),
            _operator(
                "OP10",
                "LINEAR_COMBINATION",
                "d_aab",
                inputs=("d_ab", "d1_a"),
                arguments={"coefficients": ["1/(b-a)", "-1/(b-a)"]},
            ),
            _operator(
                "OP11",
                "LINEAR_COMBINATION",
                "d_abb",
                inputs=("d1_b", "d_ab"),
                arguments={"coefficients": ["1/(b-a)", "-1/(b-a)"]},
            ),
            _operator(
                "OP12",
                "LINEAR_COMBINATION",
                "d_aabb",
                inputs=("d_abb", "d_aab"),
                arguments={"coefficients": ["1/(b-a)", "-1/(b-a)"]},
            ),
            _operator(
                "OP13",
                "LINEAR_COMBINATION",
                "d_abc",
                inputs=("d_bc", "d_ab"),
                arguments={"coefficients": ["1/(c-a)", "-1/(c-a)"]},
            ),
            _operator(
                "OP14",
                "LINEAR_COMBINATION",
                "d_aabc",
                inputs=("d_abc", "d_aab"),
                arguments={"coefficients": ["1/(c-a)", "-1/(c-a)"]},
            ),
            _operator(
                "OP15",
                "LINEAR_COMBINATION",
                "d_bcc",
                inputs=("d1_c", "d_bc"),
                arguments={"coefficients": ["1/(c-b)", "-1/(c-b)"]},
            ),
            _operator(
                "OP16",
                "LINEAR_COMBINATION",
                "d_abcc",
                inputs=("d_bcc", "d_abc"),
                arguments={"coefficients": ["1/(c-a)", "-1/(c-a)"]},
            ),
            _operator(
                "OP17",
                "LINEAR_COMBINATION",
                "out_1",
                inputs=("d_aabb",),
                arguments={"coefficients": ["p*q*r"]},
            ),
            _operator(
                "OP18",
                "LINEAR_COMBINATION",
                "out_2",
                inputs=("d_aabc",),
                arguments={"coefficients": ["p*q*r"]},
            ),
            _operator(
                "OP19",
                "LINEAR_COMBINATION",
                "out_3",
                inputs=("d_abcc",),
                arguments={"coefficients": ["p*q*r"]},
            ),
        ]
        nodes: list[dict[str, Any]] = []
    else:
        nodes = [
            {"node_id": "N01", "nodes": ["a", "a", "b", "b"]},
            {"node_id": "N02", "nodes": ["a", "a", "b", "c"]},
            {"node_id": "N03", "nodes": ["a", "b", "c", "c"]},
        ]
        operators = [
            _operator(
                "OP01",
                "HERMITE_DD",
                "h_1",
                arguments={"nodes": "N01"},
            ),
            _operator(
                "OP02",
                "LINEAR_COMBINATION",
                "out_1",
                inputs=("h_1",),
                arguments={"coefficients": ["p*q*r"]},
            ),
            _operator(
                "OP03",
                "HERMITE_DD",
                "h_2",
                arguments={"nodes": "N02"},
            ),
            _operator(
                "OP04",
                "LINEAR_COMBINATION",
                "out_2",
                inputs=("h_2",),
                arguments={"coefficients": ["p*q*r"]},
            ),
            _operator(
                "OP05",
                "HERMITE_DD",
                "h_3",
                arguments={"nodes": "N03"},
            ),
            _operator(
                "OP06",
                "LINEAR_COMBINATION",
                "out_3",
                inputs=("h_3",),
                arguments={"coefficients": ["p*q*r"]},
            ),
        ]

    assignments = [
        {
            "member_id": member_id,
            "operator_ids": _closure(operators, output),
            "output": output,
        }
        for member_id, output in (("M01", "out_1"), ("M02", "out_2"), ("M03", "out_3"))
    ]
    raw: dict[str, Any] = {
        "assumption_statuses": ASSUMPTION_STATUSES,
        "assumptions_used": list(ASSUMPTION_STATUSES),
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {
            "M01": {"component": "c_12", "sites": ["a", "a", "b", "b"]},
            "M02": {"component": "c_13", "sites": ["a", "a", "b", "c"]},
            "M03": {"component": "c_13", "sites": ["a", "b", "c", "c"]},
        },
        "latent_objects": [
            {
                "expression": "exp(z)",
                "form": "FUNCTION_1",
                "latent_id": "F01",
                "parameters": ["z"],
            }
        ],
        "member_assignments": assignments,
        "node_structures": nodes,
        "obligations": [
            {
                "member_id": member_id,
                "obligation_id": obligation_id,
                "output": output,
                "required": True,
            }
            for member_id, obligation_id, output in (
                ("M01", "O01", "out_1"),
                ("M02", "O02", "out_2"),
                ("M03", "O03", "out_3"),
            )
        ],
        "operators": operators,
        "representation_depth": "R3_REPEATED_NODE",
        "source_members": source_members,
        "unexplained_members": [],
    }
    program = program_from_dict(raw)
    raw["program_id"] = canonical_program_hash(program)
    return raw


def _explicit_node_signatures(root: Path, excluded: Path) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    target = {(2, 2), (2, 1, 1)}
    for path in sorted((root / "research").rglob("*.json")):
        if excluded in path.parents:
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue

        def visit(item: Any) -> None:
            if isinstance(item, dict):
                for key, child in item.items():
                    if (
                        key == "nodes"
                        and isinstance(child, list)
                        and len(child) == 4
                        and all(isinstance(node, (str, int, float)) for node in child)
                    ):
                        signature = tuple(
                            sorted(Counter(map(str, child)).values(), reverse=True)
                        )
                        if signature in target:
                            matches.append(
                                {
                                    "nodes": list(map(str, child)),
                                    "path": path.relative_to(root).as_posix(),
                                    "signature": list(signature),
                                }
                            )
                    visit(child)
            elif isinstance(item, list):
                for child in item:
                    visit(child)

        visit(value)
    return matches


def _write_duplicate_audit(package: Path) -> None:
    current_member_files = [
        path
        for path in sorted(
            (ROOT / "research/representation_program_search/packages").glob(
                "**/members/*.txt"
            )
        )
        if package not in path.parents
    ]
    historical_tasks = sorted(
        (ROOT / "research/representation_invention/bench/tasks").glob("**/*.json")
    )
    candidate_hashes = {
        hashlib.sha256(value.encode("utf-8")).hexdigest() for value in MEMBERS.values()
    }
    current_hashes = {_sha256(path) for path in current_member_files}
    historical_expression_hashes: set[str] = set()
    for path in historical_tasks:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            continue
        for expression in value.get("source_expressions", []):
            if isinstance(expression, str):
                historical_expression_hashes.add(
                    hashlib.sha256((expression.rstrip("\n") + "\n").encode("utf-8")).hexdigest()
                )

    _write_json(
        package / "source/duplicate_audit.json",
        {
            "candidate_signatures": {
                "M01": {"arity": 4, "multiplicity_partition": [2, 2]},
                "M02": {"arity": 4, "multiplicity_partition": [2, 1, 1]},
                "M03": {"arity": 4, "multiplicity_partition": [2, 1, 1]},
            },
            "conclusion": "FRESH_CANDIDATE_WITH_RELATED_FAMILY_CONTROLS",
            "exact_byte_audit": {
                "candidate_vs_current_member_overlap": sorted(candidate_hashes & current_hashes),
                "candidate_vs_historical_expression_overlap": sorted(
                    candidate_hashes & historical_expression_hashes
                ),
                "current_member_files_scanned": len(current_member_files),
                "historical_task_files_scanned": len(historical_tasks),
            },
            "explicit_json_node_signature_matches": _explicit_node_signatures(
                ROOT, package
            ),
            "manual_structural_anchors": [
                {
                    "artifact_sha256": "a358ad1d9acf1f53475053a9f99101d4512d1dbe4b210e7fd1391d4c2b0e49ff",
                    "comparison": "Different arity and multiplicity partition: historical synthetic [p,p,q] has (2,1); this candidate uses arity-four (2,2) and (2,1,1) coefficients from a primary third-order matrix-function theorem.",
                    "identity": "test-a-hermite-two",
                    "path": "research/representation_invention/bench/tasks/test/test-a-hermite-two.json",
                },
                {
                    "artifact_sha256": "e80150be846e1f9fb6b0b86fc77912389bfd1fcaae0a2932d9ce89becd349bd5",
                    "comparison": "Different source, scalar function, derivative order, arity, and multiplicity partition: C3J9 is second-order log with [x,x,y] and [x,y,y]; this candidate is third-order exp with four sites.",
                    "identity": "C3J9",
                    "introduction_commit": "5da637b",
                    "path": "research/representation_program_search/packages/real_domain_recovery/rps-real-c3j9/reference/program.json",
                },
                {
                    "artifact_sha256": "dabcbdf5c0b2b3c7f6af47af734711e60dec5029190f5d14db9fa0f193f1e9dc",
                    "comparison": "Same scalar exp family but different scientific identity and multiplicity: the historical phi family contains [0^(k),z], including partition (3,1); the new coefficients use (2,2) and (2,1,1), with no fixed zero node.",
                    "identity": "sciml-phi-hermite-01",
                    "path": "research/assumption_complete_representation/cases/sciml/sciml-phi-hermite-01.json",
                },
            ],
            "mechanical_scope": "Exact source bytes plus explicit JSON node arrays across historical/current research artifacts; prose-only identities are covered by the three manual anchors and are not claimed exhaustively machine-normalized.",
            "policy_version": "RPSFreshR3DuplicateAuditV1",
        },
    )


def _compile_variant(
    package: Path,
    raw: dict[str, Any],
    grammar_id: str,
):
    program = program_from_dict(raw)
    result = compile_program(
        program,
        CompileContext(package.resolve(), tuple(SYMBOLS), (), grammar_id=grammar_id),
    )
    if result.status != "COMPILED" or result.tautological:
        raise RuntimeError(f"{grammar_id}:{result.to_dict()}")
    return result


def _verify_variants(package: Path, variants: dict[str, Any]) -> None:
    workspace = package / "verification/workspace"
    attempts: list[dict[str, Any]] = []
    full_counts = {"ZERO": 0, "NONZERO": 0, "UNKNOWN": 0}
    for variant_name, compiled in variants.items():
        suffix = variant_name.casefold().replace("g_", "")
        for obligation in compiled.obligations:
            candidate_relative = (
                f"reference/candidates/{obligation.obligation_id}.{suffix}.txt"
            )
            candidate_path = package / candidate_relative
            _write_text(candidate_path, obligation.candidate_expression + "\n")
            current = load_expression(package / obligation.current_path, SYMBOLS)
            candidate = load_expression(candidate_path, SYMBOLS)
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
                    "hypothesis": (
                        "The compiled output is exactly equivalent to the grounded member."
                    ),
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
                    f"{variant_name}:{obligation.obligation_id}:"
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
                    "verdict": outcome.result.verdict,
                    "verification_step": 2,
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
        row["obligation_id"]: row
        for row in attempts
        if row["program_variant"] == "G_FULL"
    }
    rows = []
    for obligation_id, member_id in (("O01", "M01"), ("O02", "M02"), ("O03", "M03")):
        attempt = full_attempts[obligation_id]
        current_path = f"members/{member_id}.txt"
        candidate_path = attempt["candidate_path"]
        run_id = attempt["run_id"]
        rows.append(
            {
                "candidate_path": candidate_path,
                "candidate_sha256": _sha256(package / candidate_path),
                "current_member_id": member_id,
                "current_path": current_path,
                "current_sha256": _sha256(package / current_path),
                "obligation_id": obligation_id,
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
            "obligations": rows,
            "schema_version": "RPSObligationsV1",
            "summary": full_counts,
        },
    )


def _finish_manifest(package: Path) -> None:
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
            "audited_depth": "R3_REPEATED_NODE",
            "eligibility": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE",
            "manifest_exclusion": (
                "package.json is excluded because a file cannot contain its own stable hash."
            ),
            "package_id": package.name,
            "package_status": "PACKAGE_READY",
            "schema_version": "RPSCasePackageV1",
            "source_identity": (
                "Schweitzer-2023-Theorem-2-third-order-exp-rank-one-paths"
            ),
            "verdict_totals": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 9},
        },
    )


def build() -> Path:
    package = COLLECTION / PACKAGE_ID
    if package.exists():
        raise RuntimeError(f"REFUSE_EXISTING_PACKAGE:{package}")
    package.mkdir(parents=True)

    source_members = _source_members(package)
    _write_json(package / "symbols.json", {"functions": [], "symbols": SYMBOLS})
    _write_json(
        package / "assumptions.json",
        {
            "predicates": [
                {
                    "predicate_id": "P01",
                    "source": "evaluator locator S01",
                    "statement": (
                        "a, b, and c are pairwise distinct real scalars; the displayed "
                        "quotients are used only on that stratum."
                    ),
                    "status": "DECLARED",
                },
                {
                    "predicate_id": "P02",
                    "source": "evaluator locator S02",
                    "statement": "p, q, and r are arbitrary real scalars.",
                    "status": "DECLARED",
                },
                {
                    "predicate_id": "P03",
                    "source": "evaluator locator S03",
                    "statement": "exp is entire on the complex plane.",
                    "status": "DERIVED",
                },
            ],
            "schema_version": "ScientificAssumptionContractV1",
            "status": "ASSUMPTION_COMPLETE",
            "symbols_artifact": "symbols.json",
            "verifier_scope_note": (
                "The exact namespace records real scalars. Pairwise distinctness "
                "remains an explicit relational predicate; ZERO does not silently "
                "add or discharge it."
            ),
        },
    )
    _write_json(
        package / "source_catalog.json",
        {
            "members": [
                {"locator_id": f"L0{index}", **row}
                for index, row in enumerate(source_members, start=1)
            ],
            "schema_version": "RPSMemberCatalogV1",
            "symbols_path": "symbols.json",
            "symbols_sha256": _sha256(package / "symbols.json"),
        },
    )
    _write_json(
        package / "proposer_view.json",
        {
            "assumptions": {
                "path": "assumptions.json",
                "sha256": _sha256(package / "assumptions.json"),
            },
            "case_id": CASE_ID,
            "schema_version": "RPSProposerViewV1",
            "source_catalog": {
                "path": "source_catalog.json",
                "sha256": _sha256(package / "source_catalog.json"),
            },
            "structural_observations": {
                "argument_families": ["a", "b", "c"],
                "member_count": 3,
                "shared_functions": ["exp"],
                "source_scope": "real scalar components on a declared pairwise-distinct stratum",
            },
        },
    )

    _write_text(package / "source/theorem2-equations.tex", SOURCE_EQUATIONS)
    _write_json(
        package / "source/assumption_locators.json",
        {
            "locators": [
                {
                    "locator_id": "S01",
                    "provenance": "declared fixed-instance stratum",
                    "statement": (
                        "a, b, and c are real and pairwise distinct so every "
                        "displayed rational source expression is defined."
                    ),
                },
                {
                    "locator_id": "S02",
                    "provenance": "declared fixed-instance direction scaling",
                    "statement": "p, q, and r are arbitrary real direction scalars.",
                },
                {
                    "locator_id": "S03",
                    "provenance": (
                        "derived specialization of Theorem 2's analytic-function "
                        "hypothesis to f(z)=exp(z)"
                    ),
                    "statement": (
                        "The complex exponential is entire, hence analytic on and "
                        "inside every contour admitted by Theorem 2."
                    ),
                },
            ],
            "schema_version": "RPSAssumptionLocatorSetV1",
        },
    )
    _write_json(
        package / "source/lowering.json",
        {
            "derivation_status": "DERIVED_FROM_PRIMARY_SOURCE",
            "fixed_instance": {
                "base_matrix": "diag(a,b,c)",
                "dimension": 3,
                "directions": {
                    "M01": ["p*e11", "q*e12", "r*e22"],
                    "M02": ["p*e11", "q*e12", "r*e23"],
                    "M03": ["p*e12", "q*e23", "r*e33"],
                },
                "function": "matrix exponential",
                "order": 3,
                "stratum": "a, b, c real and pairwise distinct",
            },
            "lowering_scope": "FIXED_SCIENTIFIC_INSTANCE",
            "members": {
                "M01": {
                    "component": "(1,2)",
                    "node_sequence": ["a", "a", "b", "b"],
                    "surviving_permutations": 1,
                },
                "M02": {
                    "component": "(1,3)",
                    "node_sequence": ["a", "a", "b", "c"],
                    "surviving_permutations": 1,
                },
                "M03": {
                    "component": "(1,3)",
                    "node_sequence": ["a", "b", "c", "c"],
                    "surviving_permutations": 1,
                },
            },
            "source_basis": (
                "Specialize equations (8)--(9) to k=3. With diagonal A, each "
                "listed ordered product of matrix units is the only nonzero "
                "permutation in the specified component. Its four resolvent "
                "factors have the recorded site sequence. Cauchy's residue "
                "formula gives the corresponding confluent coefficient of exp; "
                "the package certifies only the three scalar components."
            ),
        },
    )
    _write_duplicate_audit(package)
    _write_json(
        package / "source_manifest.json",
        {
            "lowering": {
                "path": "source/lowering.json",
                "sha256": _sha256(package / "source/lowering.json"),
            },
            "duplicate_audit": {
                "path": "source/duplicate_audit.json",
                "sha256": _sha256(package / "source/duplicate_audit.json"),
            },
            "assumption_contract": {
                "path": "assumptions.json",
                "sha256": _sha256(package / "assumptions.json"),
            },
            "assumption_locators": {
                "path": "source/assumption_locators.json",
                "sha256": _sha256(package / "source/assumption_locators.json"),
            },
            "symbol_namespace": {
                "path": "symbols.json",
                "sha256": _sha256(package / "symbols.json"),
            },
            "schema_version": "RPSSourceManifestV1",
            "sources": [
                {
                    "arxiv_source_archive_sha256": SOURCE_ARCHIVE_SHA256,
                    "arxiv_version": "2203.03930v2",
                    "authority": "peer-reviewed primary research article",
                    "authors": ["Marcel Schweitzer"],
                    "doi": "10.1016/j.laa.2022.10.005",
                    "journal_locator": (
                        "Linear Algebra and its Applications 656 (2023), 247--276, "
                        "Section 2.1, Theorem 2, equations (8)--(9)"
                    ),
                    "retrieved_on": "2026-08-30",
                    "source_tex_full_sha256": SOURCE_TEX_SHA256,
                    "source_tex_locator": (
                        "arXiv v2 file higher_order_frechet.tex lines 365--374; "
                        "stored bytes are the exact equation block at lines 367--373"
                    ),
                    "stored_artifact": {
                        "path": "source/theorem2-equations.tex",
                        "sha256": _sha256(package / "source/theorem2-equations.tex"),
                    },
                    "title": (
                        "Integral representations for higher-order Frechet derivatives "
                        "of matrix functions: Quadrature algorithms and new results "
                        "on the level-2 condition number"
                    ),
                    "url": "https://arxiv.org/abs/2203.03930v2",
                }
            ],
        },
    )

    full = _program(source_members, primitive=False)
    primitive = _program(source_members, primitive=True)
    _write_json(package / "reference/program.json", full)
    _write_json(package / "reference/ablations/G_NO_HERMITE.program.json", primitive)
    _write_json(package / "reference/ablations/G_PRIMITIVE.program.json", primitive)
    _write_json(
        package / "reference/obligations.json",
        {
            "obligations": [
                {
                    "current_member_id": member_id,
                    "obligation_id": obligation_id,
                    "required": True,
                }
                for obligation_id, member_id in (("O01", "M01"), ("O02", "M02"), ("O03", "M03"))
            ],
            "schema_version": "RPSObligationsV1",
        },
    )
    _write_json(
        package / "reference/review.json",
        {
            "baseline_assessment": {
                "first_order_lgg_only": False,
                "tautological": False,
                "visible_common_factor": "p*q*r",
            },
            "candidate_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "depth_assessment": "R3_REPEATED_NODE_ARITY_FOUR",
            "duplicate_assessment": (
                "No exact current/historical member match or explicit arity-four "
                "multiplicity-signature match was found. C3J9, test-a-hermite-two, "
                "and the historical exp phi family remain explicit related-family "
                "controls in source/duplicate_audit.json."
            ),
            "grammar_assessment": {
                "g_full": "COMPILED",
                "g_no_hermite": "COMPILED",
                "g_primitive": "COMPILED",
                "named_primitive_required": False,
                "scope_note": (
                    "Primitive compilation proves expressibility only. Whether the "
                    "frozen search frontier discovers that program is an empirical "
                    "question and is not claimed by this package."
                ),
            },
            "leakage_assessment": (
                "The public projection contains opaque case/member/locator ids and "
                "no target type, operator, node role, derivative order, reference "
                "program, or verification receipt. Explicit site multiplicity exists "
                "only in evaluator artifacts."
            ),
            "review_policy": "RPSFreshStrictR3CandidateV1",
        },
    )

    variants = {
        "G_FULL": _compile_variant(package, full, "G_FULL"),
        "G_NO_HERMITE": _compile_variant(package, primitive, "G_NO_HERMITE"),
        "G_PRIMITIVE": _compile_variant(package, primitive, "G_PRIMITIVE"),
    }
    _verify_variants(package, variants)
    _finish_manifest(package)
    return package


if __name__ == "__main__":
    print(build())
