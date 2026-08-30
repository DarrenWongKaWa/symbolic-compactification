"""Read-only independent audit of R6 feasibility under frozen M1.

The audit deliberately does not mine or create a package.  It binds the full
current case registry, the complete current package-manifest registry, the
historical duplicate corpus, and every historical dossier labelled R6.  The
result is a bounded repository claim: no currently mined identity clears all
R6 admission gates under the frozen parser and Program IR.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import get_parse_policy, parse_expression

from research.representation_program_search.audits.leakage.audit import (
    discover_reference_corpus,
)
from research.representation_program_search.grammar_v1 import (
    G_PRIMITIVE_OPS,
    LATENT_FORMS,
    OPERATORS,
    OPTIONAL_LATER,
)
from research.representation_program_search.program_ir import (
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.loader import PackageLoadError


AUDIT_VERSION = "RPS_INDEPENDENT_R6_FEASIBILITY_AUDIT_V1"
AUDITED_TREE = "009bd2acfab00c770bacdd71e597e9a40e2b8904"

PINNED_INPUTS = {
    "research/representation_program_search/REPRESENTATION_GRAMMAR_V1.md":
        "dc45500858006ce992b5f6d2ebb8968e16d3e2bf975e189adcc3f7eac5877b65",
    "research/representation_program_search/grammar_v1.py":
        "d0ef47c44e23cf69220c0ad9fac7801f70006f60826eb6f49729674313a7d212",
    "research/representation_program_search/program_ir/compiler.py":
        "4fa763120cc2fe8d88ca1520a8e632c97bfbe28583fceada4cf8c301ffc7ce28",
    "research/representation_program_search/program_ir/model.py":
        "8b9e77bd80c6bc1ff5e050beba3be42acf0d5c6d87a29e25d005f308aac2fe0b",
    "src/symbolic_compactification/parser.py":
        "a61b31043bd23d6a3c08210ac0c173a6c2418bd3d44017db6f15ad5d7b5f11a9",
    "research/representation_program_search/audits/admission/ADMISSION_AUDIT.json":
        "01d867ef9b0cb8a054ffd89c04830ad79510a872d11a9f02f3cd1d6cdeac1422",
    "research/representation_program_search/audits/package_admission/PACKAGE_ADMISSION_AUDIT.json":
        "6945c7301e5319bcd743bd6f59462f11c073f33a0af2d1ca3744cc36ea8dbee1",
    "research/representation_program_search/recovery/gap_recovery/R6_MINING_NEGATIVE.json":
        "a2e3ed5b9c6f394c5805dce851fd428e8b5701fa9e5f79a1614fc1264aad1102",
}

EXPECTED_REGISTRIES = {
    "current_case_json": {
        "count": 53,
        "sha256": "6a79dde9b4384ec5651671001c26a704e2d138f304542117baf15b596508f46a",
    },
    "current_science_dossiers": {
        "count": 39,
        "sha256": "6bc8b0d0eb5cc4c280c388aff87ee2bab7a5d7259623a9184c9b8aa90904bb71",
    },
    "current_package_manifests": {
        "count": 19,
        "sha256": "07bbce9e9f6e11adb0d4faaa0fb512ec28dea6f522052457646dfaf688d48034",
    },
    "historical_reference_corpus": {
        "count": 79,
        "sha256": "a2dd7c4d6f31608160c70b9b1973f26567e3fa3c39129a969aaf90ec16f34f12",
    },
    "historical_r6_dossiers": {
        "count": 14,
        "sha256": "511eebfc793f9248ba2f9d66b2f1ee471cdadcb4136e37f5a814c46f6875b4d5",
    },
}

HISTORICAL_R6 = {
    "research/assumption_complete_representation/cases/mathphys/mp-cauchy-dunford-01.json": (
        "mp-cauchy-dunford-01",
        "MATRIX_FUNCTIONAL_CALCULUS",
        ("HISTORICAL_IDENTITY", "INTEGRAL_AND_MATRIX_RESOLVENT_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
    "research/assumption_complete_representation/cases/mathphys/mp-mathias-block-01.json": (
        "mp-mathias-block-01",
        "BLOCK_EXPONENTIAL",
        ("HISTORICAL_IDENTITY", "BLOCK_MATRIX_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
    "research/assumption_complete_representation/cases/response/dossiers/ac-r05-lehmann-spectral-master.json": (
        "ac-r05-lehmann-spectral-master",
        "RESPONSE_MASTER",
        ("HISTORICAL_IDENTITY", "INTEGRAL_AND_SPECTRAL_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
    "research/assumption_complete_representation/cases/response/dossiers/ac-r07-lippmann-schwinger-iepsilon.json": (
        "ac-r07-lippmann-schwinger-iepsilon",
        "RESPONSE_MASTER",
        ("HISTORICAL_IDENTITY", "OPERATOR_RESOLVENT_AND_INTEGRAL_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
    "research/assumption_complete_representation/cases/response/dossiers/ac-r08-kubo-frequency-underspecified.json": (
        "ac-r08-kubo-frequency-underspecified",
        "RESPONSE_MASTER",
        ("HISTORICAL_IDENTITY", "PROBLEM_UNDERSPECIFIED", "INTEGRAL_AND_COMMUTATOR_SEMANTICS"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-adjoint-linear-01.json": (
        "sciml-adjoint-linear-01",
        "RESPONSE_GRAPH",
        ("HISTORICAL_IDENTITY", "DERIVATIVE_RESPONSE_GRAPH", "SCALAR_LOWERING_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-deq-ift-01.json": (
        "sciml-deq-ift-01",
        "RESPONSE_MASTER",
        ("HISTORICAL_IDENTITY", "MATRIX_INVERSE_SEMANTICS", "SCALAR_LOWERING_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-lyapunov-kronecker-01.json": (
        "sciml-lyapunov-kronecker-01",
        "MATRIX_FUNCTIONAL_CALCULUS",
        ("HISTORICAL_IDENTITY", "KRONECKER_AND_MATRIX_SEMANTICS", "SCALAR_LOWERING_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-ou-mehler-01.json": (
        "sciml-ou-mehler-01",
        "SPECIAL_FUNCTION_KERNEL",
        ("HISTORICAL_IDENTITY", "SOURCE_DISPLAYS_GENERATOR", "SCALAR_FAMILY_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-tweedie-gauss-01.json": (
        "sciml-tweedie-gauss-01",
        "RESPONSE_GRAPH",
        ("HISTORICAL_IDENTITY", "DERIVATIVE_RESPONSE_GRAPH", "SCALAR_LOWERING_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/sciml/sciml-vanloan-blockexp-01.json": (
        "sciml-vanloan-blockexp-01",
        "BLOCK_EXPONENTIAL",
        ("HISTORICAL_IDENTITY", "BLOCK_MATRIX_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
    "research/assumption_complete_representation/cases/skeptic/negative/nc-leaked-master.json": (
        "nc-leaked-master",
        "NEGATIVE_CONTROL",
        ("HISTORICAL_IDENTITY", "INTENTIONAL_TARGET_LEAKAGE"),
    ),
    "research/assumption_complete_representation/cases/thermal/thermal-03-digamma-reflection.json": (
        "thermal-03-digamma-reflection",
        "THERMAL_SPECIAL_FUNCTION",
        ("HISTORICAL_IDENTITY", "SINGLE_SPECIAL_FUNCTION_RELATION_BELOW_R6"),
    ),
    "research/assumption_complete_representation/cases/thermal/thermal-07-green-spectral-hilbert.json": (
        "thermal-07-green-spectral-hilbert",
        "THERMAL_RESPONSE_MASTER",
        ("HISTORICAL_IDENTITY", "INTEGRAL_AND_SPECTRAL_SEMANTICS", "SOURCE_DISPLAYS_MASTER"),
    ),
}

SUPPLEMENTAL_SCREEN = (
    {
        "identity": "time-dependent Maxwell fields from Debye potentials",
        "family": "VECTOR_MULTI_OPERATOR_MASTER",
        "failure_codes": [
            "FROZEN_GRAMMAR_LACKS_CURL",
            "FROZEN_PARSER_LACKS_VECTOR_BASIS_SEMANTICS",
            "PUBLIC_FULL_FIELD_MEMBER_WOULD_EXPOSE_MASTER",
            "SCALAR_COMPONENT_LOWERING_ERASES_DEPTH",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
    {
        "identity": "Potts toroidal-strip transfer-matrix family",
        "family": "MATRIX_TRANSFER_MASTER",
        "failure_codes": [
            "FROZEN_GRAMMAR_LACKS_MATRIX_POWER_TRACE_DETERMINANT",
            "PUBLIC_PARTITION_RECONSTRUCTION_WOULD_EXPOSE_MASTER",
            "FINITE_WIDTH_SCALARIZATION_ERASES_LATENT_INDUCTION",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
    {
        "identity": "Rayleigh differential generators for spherical Bessel families",
        "family": "SPECIAL_FUNCTION_DERIVATIVE_LADDER",
        "failure_codes": [
            "CURRENT_FAMILY_OVERLAP_RPS_REAL_C8Q2",
            "SHORT_DERIVATIVE_RECURRENCE_LADDER_BELOW_R6",
            "SOURCE_DISPLAYS_GENERATOR",
        ],
    },
)

R6_RELEVANT_PACKAGES = {
    "mx-abba-exp-fixed-r6": {
        "path": "research/representation_program_search/packages/matrix_diffphys/mx-abba-exp-fixed-r6",
        "expected_loader": "PACKAGE_ARTIFACT_MANIFEST_INVALID",
        "independent_depth": "R2",
        "source_member_master_exposed": True,
        "stored_source_bytes": False,
        "failure_codes": [
            "M1_LOAD_FAILURE",
            "NEWTON_DD_PLUS_LINEAR_RECONSTRUCTION_BELOW_R6",
            "PUBLIC_G0005_IS_SHARED_NEWTON_QUOTIENT",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
    "rps-r-feshbach-optical-heff": {
        "path": "research/representation_program_search/packages/response_tensor/rps-r-feshbach-optical-heff",
        "expected_loader": "PACKAGE_ARTIFACT_MANIFEST_INVALID",
        "independent_depth": "R0",
        "source_member_master_exposed": True,
        "stored_source_bytes": False,
        "failure_codes": [
            "M1_LOAD_FAILURE",
            "SHARED_DENOMINATOR_CSE_BELOW_R6",
            "PUBLIC_MEMBERS_EXPOSE_SHARED_KERNEL",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
    "gf-vdw-2013-eq1": {
        "path": "research/representation_program_search/packages/gap_fill/gf-vdw-2013-eq1",
        "expected_loader": "COMPILED_NO_SCHEMA_DELTAS",
        "independent_depth": "R1_DERIVATIVE_RESPONSE_GRAPH",
        "source_member_master_exposed": True,
        "stored_source_bytes": False,
        "failure_codes": [
            "PUBLIC_G0001_IS_EXACT_HELMHOLTZ_MASTER",
            "DERIVATIVE_RESPONSE_GRAPH_BELOW_R6",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
    "rps-candidate-j2-001": {
        "path": "research/representation_program_search/packages/dev_recovery/rps-candidate-j2-001",
        "expected_loader": "COMPILED_NO_SCHEMA_DELTAS",
        "independent_depth": "R3_REPEATED_NODE_INELIGIBLE",
        "source_member_master_exposed": False,
        "stored_source_bytes": False,
        "failure_codes": [
            "HISTORICAL_BLOCK_EXPONENTIAL_SOURCE_IDENTITY",
            "SCALAR_REPEATED_NODE_LOWERING_BELOW_R6",
            "NO_HASH_BOUND_SOURCE_BYTES_IN_PACKAGE",
        ],
    },
}

SOURCE_LOCATOR_CHECKS = (
    {
        "family": "BLOCK_EXPONENTIAL",
        "source": "Higham and Relton, Higher Order Frechet Derivatives of Matrix Functions",
        "url": "https://eprints.maths.manchester.ac.uk/2160/1/130945259.pdf",
        "locator": "equation (3.4), Theorem 3.5, and the paragraph following Theorem 3.5",
        "finding": "The source explicitly gives the block lift and upper-right-block reconstruction; the identity is historical and needs matrix/block semantics.",
    },
    {
        "family": "DEXP_BERNOULLI",
        "source": "Iserles, Munthe-Kaas, Norsett, and Zanna, Lie-group methods",
        "url": "https://www.damtp.cam.ac.uk/user/na/NA_papers/NA2000_03.pdf",
        "locator": "equations (2.40)--(2.46) and (4.3)",
        "finding": "The source explicitly gives ad, dexp, inverse dexp, the Bernoulli-adjoint series, and the Magnus equation; frozen M1 lacks noncommutative adjoint/Bernoulli operator semantics.",
    },
    {
        "family": "THERMAL_POLYGAMMA",
        "source": "NIST Digital Library of Mathematical Functions",
        "url": "https://dlmf.nist.gov/25.11.E12",
        "locator": "equation 25.11.12 in subsection 25.11(v)",
        "finding": "The source gives one Hurwitz-zeta/polygamma bridge; zeta and factorial are outside the frozen semantic whitelist and the relation is not a multi-operator R6 master.",
    },
    {
        "family": "POTTS_TRANSFER_MATRIX",
        "source": "Chang and Shrock, Transfer Matrices for the Partition Function of the Potts Model on Toroidal Lattice Strips",
        "url": "https://arxiv.org/abs/cond-mat/0506274",
        "locator": "equation (5) and trace/determinant results described in the abstract",
        "finding": "The source explicitly gives the eigenvalue-power reconstruction and trace/determinant family; frozen M1 has none of those matrix semantics.",
    },
    {
        "family": "DEBYE_MAXWELL",
        "source": "Greengard, Hagstrom, and Jiang, Extension of the Lorenz-Mie-Debye method for electromagnetic scattering to the time-domain",
        "url": "https://doi.org/10.1016/j.jcp.2015.07.009",
        "locator": "time-domain Debye representation and Theorem 2",
        "finding": "The source reconstructs vector fields using curl, curl-of-curl, time derivative, and vector spherical harmonics; frozen M1 has no such semantics.",
    },
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry(rows: Iterable[Path], root: Path) -> dict[str, Any]:
    items = [
        {
            "path": path.resolve().relative_to(root.resolve()).as_posix(),
            "sha256": _sha256(path),
        }
        for path in sorted(rows)
    ]
    encoded = (json.dumps(items, sort_keys=True, separators=(",", ":")) + "\n").encode()
    return {
        "count": len(items),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "items": items,
    }


def _parser_probe(expression: str) -> str:
    symbols = [
        {"name": name, "real": False, "nonzero": False}
        for name in ("a", "b", "n", "t")
    ]
    try:
        parse_expression(expression, symbols)
    except AdapterError as exc:
        return exc.code
    return "PARSED"


def _package_probe(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    package = root / spec["path"]
    try:
        loaded = load_case_package(package)
    except PackageLoadError as exc:
        status = exc.code
        schema_deltas: list[str] = []
        compile_status = "NOT_RUN"
        compile_failures: list[str] = []
    else:
        compiled = compile_program(loaded.program, loaded.context)
        status = "COMPILED_NO_SCHEMA_DELTAS" if not loaded.schema_deltas else "COMPILED_WITH_SCHEMA_DELTAS"
        schema_deltas = list(loaded.schema_deltas)
        compile_status = compiled.status
        compile_failures = list(compiled.failure_codes)
    return {
        "package_id": package.name,
        "path": spec["path"],
        "loader_status": status,
        "compile_status": compile_status,
        "compile_failure_codes": compile_failures,
        "schema_deltas": schema_deltas,
        "independent_depth": spec["independent_depth"],
        "source_member_master_exposed": spec["source_member_master_exposed"],
        "stored_source_bytes": spec["stored_source_bytes"],
        "failure_codes": list(spec["failure_codes"]),
        "qualifies": False,
    }


def build_audit(root: Path) -> dict[str, Any]:
    root = root.resolve()
    pinned = {path: _sha256(root / path) for path in sorted(PINNED_INPUTS)}

    admission = _json(
        root / "research/representation_program_search/audits/admission/ADMISSION_AUDIT.json"
    )
    current_cases: list[dict[str, Any]] = []
    for case in sorted(admission["cases"], key=lambda item: item["case_id"]):
        if case["audited_depth"] == "R6":
            depth_gate = "R6_CANDIDATE"
        elif case["audited_depth"] in {"R7", "R8"}:
            depth_gate = "DEEPER_DIFFERENT_TARGET_NOT_R6_SUBSTITUTE"
        else:
            depth_gate = "AUDITED_BELOW_R6"
        failure_codes = [
            case["primary_status"],
            case["parser_fit"],
            *case.get("parser_blockers", []),
        ]
        if case.get("duplicate_with"):
            failure_codes.append("CURRENT_OR_HISTORICAL_DUPLICATE")
        if case.get("frozen_source_artifact_count", 0) == 0:
            failure_codes.append("NO_HASH_BOUND_SOURCE_BYTES")
        if case.get("machine_package", {}).get("status") != "READY":
            failure_codes.append("NO_ADMISSION_PACKAGE")
        current_cases.append({
            "case_id": case["case_id"],
            "cluster": case["cluster"],
            "proposed_ladder": case["proposed_ladder"],
            "audited_depth": case["audited_depth"],
            "depth_gate": depth_gate,
            "primary_status": case["primary_status"],
            "parser_fit": case["parser_fit"],
            "duplicate_with": list(case.get("duplicate_with", [])),
            "frozen_source_artifact_count": case.get("frozen_source_artifact_count", 0),
            "machine_package_status": case.get("machine_package", {}).get("status"),
            "failure_codes": failure_codes,
            "qualifies": False,
        })

    current_case_registry = _registry(
        (root / "research/representation_program_search/cases").rglob("*.json"), root
    )
    science_registry = _registry(
        (root / case["dossier_path"] for case in admission["cases"]), root
    )
    package_registry = _registry(
        (root / "research/representation_program_search/packages").rglob("package.json"), root
    )
    references = discover_reference_corpus(root)
    historical_registry = _registry((root / item.path for item in references), root)
    historical_r6_registry = _registry((root / path for path in HISTORICAL_R6), root)

    historical_rows = []
    for path, (case_id, family, failure_codes) in sorted(HISTORICAL_R6.items()):
        payload = _json(root / path)
        historical_rows.append({
            "case_id": case_id,
            "family": family,
            "path": path,
            "dossier_sha256": _sha256(root / path),
            "declared_ladder": payload.get("proposed_ladder"),
            "failure_codes": list(failure_codes),
            "qualifies": False,
        })

    package_rows = [
        _package_probe(root, spec)
        for _package_id, spec in sorted(R6_RELEVANT_PACKAGES.items())
    ]

    registries = {
        "current_case_json": {key: current_case_registry[key] for key in ("count", "sha256")},
        "current_science_dossiers": {key: science_registry[key] for key in ("count", "sha256")},
        "current_package_manifests": {key: package_registry[key] for key in ("count", "sha256")},
        "historical_reference_corpus": {key: historical_registry[key] for key in ("count", "sha256")},
        "historical_r6_dossiers": {key: historical_r6_registry[key] for key in ("count", "sha256")},
    }
    return {
        "schema_version": AUDIT_VERSION,
        "audited_tree": AUDITED_TREE,
        "decision": "R6_MISSING",
        "failure_class": "PACKAGING_GAP",
        "candidate_count": 0,
        "package_created": False,
        "claim_boundary": (
            "No identity in the bounded, hash-bound mined registry clears every R6 "
            "admission gate under the frozen parser and Program IR. This is not a "
            "mathematical impossibility claim and does not authorize parser, verifier, "
            "grammar, method, manifest, or TEST changes."
        ),
        "qualification_gates": [
            "AUTHORITATIVE_SOURCE_LOCATOR",
            "HASH_BOUND_SOURCE_BYTES",
            "FRESH_IDENTITY",
            "ASSUMPTION_COMPLETE",
            "EXACT_M1_COMPILATION_WITHOUT_SCHEMA_DELTAS",
            "AT_LEAST_TWO_INDEPENDENT_OPERATOR_TYPES",
            "MULTI_MEMBER_REUSE",
            "NO_TARGET_OR_OPERATOR_ROLE_LEAKAGE",
            "NO_PUBLIC_SOURCE_MEMBER_MASTER_EXPOSURE",
            "NO_HISTORICAL_OR_CURRENT_STRUCTURAL_DUPLICATE",
            "NO_DEPTH_COLLAPSE_AFTER_EXECUTABLE_LOWERING",
        ],
        "pinned_inputs": pinned,
        "registries": registries,
        "frozen_language": {
            "latent_forms": list(LATENT_FORMS),
            "operators": list(OPERATORS),
            "primitive_operators": list(G_PRIMITIVE_OPS),
            "optional_later_not_active": list(OPTIONAL_LATER),
            "parser_allowed_functions": get_parse_policy()["allowed_functions"],
            "parser_probes": {
                expression: _parser_probe(expression)
                for expression in (
                    "exp(a)",
                    "polygamma(1,a)",
                    "Integral(exp(-t),(t,0,oo))",
                    "Matrix(a)",
                    "Trace(a)",
                    "Determinant(a)",
                    "Commutator(a,b)",
                    "zeta(2,a)",
                    "factorial(n)",
                    "Sum(a,(n,0,3))",
                )
            },
            "matrix_function_form_has_matrix_semantics": False,
            "note": (
                "MATRIX_FUNCTION is an accepted latent label, but M1 parses latent cores "
                "as scalar SymPy expressions. Structural Sum is admitted; matrix, trace, "
                "determinant, integral, commutator, Hurwitz-zeta, factorial, vector, and "
                "tensor algebra do not receive the required frozen semantics."
            ),
        },
        "current_case_summary": {
            "total": len(current_cases),
            "audited_depth_counts": dict(sorted(Counter(row["audited_depth"] for row in current_cases).items())),
            "r6_candidate_count": sum(row["audited_depth"] == "R6" for row in current_cases),
            "r6_status_counts": dict(sorted(Counter(
                row["primary_status"] for row in current_cases if row["audited_depth"] == "R6"
            ).items())),
            "qualifying_count": 0,
        },
        "current_cases": current_cases,
        "historical_r6": historical_rows,
        "supplemental_screen": list(SUPPLEMENTAL_SCREEN),
        "r6_relevant_packages": package_rows,
        "source_locator_checks": list(SOURCE_LOCATOR_CHECKS),
        "requested_family_conclusions": {
            "block_exponentials": "PACKAGING_GAP_AND_HISTORICAL_DUPLICATION",
            "matrix_functional_calculus": "PACKAGING_GAP_OR_R2_SCALAR_COLLAPSE",
            "dexp_bernoulli": "PACKAGING_GAP_NONCOMMUTATIVE_AND_BERNOULLI_SEMANTICS",
            "thermal_polygamma": "R5_OR_BELOW_AFTER_EXECUTABLE_LOWERING",
            "response": "PACKAGING_GAP_OR_R0_R1_DERIVATIVE_RESPONSE_COLLAPSE",
            "vector_transfer_tensor": "PACKAGING_GAP_OR_DIAGNOSTIC_ONLY",
        },
        "qualifying_candidate_ids": [],
    }


def validate_audit(root: Path, report: dict[str, Any]) -> None:
    if report["pinned_inputs"] != PINNED_INPUTS:
        raise AssertionError("PINNED_INPUT_HASH_MISMATCH")
    if report["registries"] != EXPECTED_REGISTRIES:
        raise AssertionError("REGISTRY_SCOPE_MISMATCH")
    for package_id, spec in R6_RELEVANT_PACKAGES.items():
        row = next(item for item in report["r6_relevant_packages"] if item["package_id"] == package_id)
        if row["loader_status"] != spec["expected_loader"]:
            raise AssertionError(f"PACKAGE_PROBE_MISMATCH:{package_id}")
    if report["candidate_count"] or report["qualifying_candidate_ids"]:
        raise AssertionError("R6_CANDIDATE_UNEXPECTED")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


if __name__ == "__main__":
    result = build_audit(_repo_root())
    validate_audit(_repo_root(), result)
    print(json.dumps(result, sort_keys=True, indent=2))
