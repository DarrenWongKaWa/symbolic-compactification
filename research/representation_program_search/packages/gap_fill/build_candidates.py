"""One-shot builder for the candidate-only R2/R6 gap-fill packages.

The builder contains the exact, source-audited lowering used to create the
committed artifacts.  It refuses to overwrite an existing candidate package;
normal CI uses :mod:`validate`, not this one-shot construction path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from symbolic_compactification import (
    ZERO,
    adjudicate_candidate,
    init_session,
    load_expression,
    record_proposal,
    set_current,
    validate_candidate,
)

from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
)
from research.representation_program_search.program_ir.schema import program_from_dict


ROOT = Path(__file__).resolve().parent
PACKAGE_SCHEMA = "RPSCasePackageV1"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _write_json(path: Path, value: Any) -> None:
    _atomic_bytes(path, _json_bytes(value))


def _write_text(path: Path, value: str) -> None:
    _atomic_bytes(path, (value.rstrip() + "\n").encode())


def _source_member(member_id: str, path: str, root: Path) -> dict[str, str]:
    return {"member_id": member_id, "path": path, "sha256": _sha(root / path)}


def _operator(
    operator_id: str,
    operator: str,
    output: str,
    latent_id: str,
    *,
    inputs: list[str] | None = None,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "arguments": arguments or {},
        "inputs": inputs or [],
        "latent_id": latent_id,
        "operator": operator,
        "operator_id": operator_id,
        "output": output,
    }


def _dependency_ids(operators: list[dict[str, Any]], output: str) -> list[str]:
    by_output = {item["output"]: item for item in operators}
    found: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in by_output:
            return
        seen.add(name)
        item = by_output[name]
        for dependency in item["inputs"]:
            visit(dependency)
        found.append(item["operator_id"])

    visit(output)
    return found


def _r2_spec() -> dict[str, Any]:
    xa0 = "(x1_old+alpha)**2+x2_hold**2"
    xa1 = "(x1_new+alpha)**2+x2_hold**2"
    ya0 = "(x1_hold+alpha)**2+x2_old**2"
    ya1 = "(x1_hold+alpha)**2+x2_new**2"
    xb0 = "(x1_old-beta)**2+x2_hold**2"
    xb1 = "(x1_new-beta)**2+x2_hold**2"
    yb0 = "(x1_hold-beta)**2+x2_old**2"
    yb1 = "(x1_hold-beta)**2+x2_new**2"
    members = {
        "G0001": f"-(x1_new+x1_old+2*alpha)/(sqrt({xa0})*sqrt({xa1})*(sqrt({xa0})+sqrt({xa1})))",
        "G0002": f"-(x2_new+x2_old)/(sqrt({ya0})*sqrt({ya1})*(sqrt({ya0})+sqrt({ya1})))",
        "G0003": f"-(x1_new+x1_old-2*beta)/(sqrt({xb0})*sqrt({xb1})*(sqrt({xb0})+sqrt({xb1})))",
        "G0004": f"-(x2_new+x2_old)/(sqrt({yb0})*sqrt({yb1})*(sqrt({yb0})+sqrt({yb1})))",
    }
    nodes = [("N0001", xa0, xa1), ("N0002", ya0, ya1), ("N0003", xb0, xb1), ("N0004", yb0, yb1)]
    coefficients = [
        "x1_new+x1_old+2*alpha",
        "x2_new+x2_old",
        "x1_new+x1_old-2*beta",
        "x2_new+x2_old",
    ]
    operators: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    obligations: list[dict[str, Any]] = []
    for index, ((node_id, _left, _right), coefficient) in enumerate(zip(nodes, coefficients), 1):
        dd_output = f"dd_{index}"
        output = f"component_{index}"
        operators.extend(
            [
                _operator(
                    f"O{2 * index - 1:04d}",
                    "NEWTON_DD",
                    dd_output,
                    "F0001",
                    arguments={"nodes": node_id},
                ),
                _operator(
                    f"O{2 * index:04d}",
                    "LINEAR_COMBINATION",
                    output,
                    "F0001",
                    inputs=[dd_output],
                    arguments={"coefficients": [coefficient], "constant": "0"},
                ),
            ]
        )
        member_id = f"G{index:04d}"
        obligation_id = f"Q{index:04d}"
        assignments.append(
            {
                "member_id": member_id,
                "operator_ids": _dependency_ids(operators, output),
                "output": output,
            }
        )
        obligations.append(
            {
                "member_id": member_id,
                "obligation_id": obligation_id,
                "output": output,
                "required": True,
            }
        )
    assumptions = {
        "predicates": [
            {
                "predicate_id": "P001",
                "source": "Wan, Bihlo, and Nave (2017), Section 2 and Eq. (26)",
                "statement": "All coordinates and relative masses in this lowering are real.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P002",
                "source": "Wan, Bihlo, and Nave (2017), Eqs. (26)-(28)",
                "statement": "alpha and beta are positive relative masses satisfying alpha+beta=1.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P003",
                "source": "Wan, Bihlo, and Nave (2017), Eqs. (26)-(28) and Appendix B Definition 31",
                "statement": "The four old/new coordinate pairs and their induced squared-distance nodes are distinct; no primary collision occurs.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P004",
                "source": "P001-P003",
                "statement": "Every squared-distance node is strictly positive, so the displayed real square roots and all displayed denominators are defined and nonzero.",
                "status": "DERIVED",
            },
        ],
        "schema_version": "ScientificAssumptionContractV1",
        "status": "ASSUMPTION_COMPLETE",
        "symbols_artifact": "symbols.json",
        "verifier_scope_note": "The exact verifier proves the four algebraic lowerings. Relational domain predicates are source-bound contract predicates and are not silently added to the parser namespace.",
    }
    symbols = {
        "functions": [],
        "symbols": [
            {"name": name, "real": True, "nonzero": False}
            for name in (
                "alpha",
                "beta",
                "x1_hold",
                "x1_new",
                "x1_old",
                "x2_hold",
                "x2_new",
                "x2_old",
            )
        ],
    }
    program = {
        "assumption_statuses": {f"P{index:03d}": status for index, status in enumerate(("DECLARED", "DECLARED", "DECLARED", "DERIVED"), 1)},
        "assumptions_used": ["P001", "P002", "P003", "P004"],
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {},
        "latent_objects": [
            {
                "expression": "1/sqrt(z)",
                "form": "SCALAR_KERNEL",
                "latent_id": "F0001",
                "parameters": ["z"],
            }
        ],
        "member_assignments": assignments,
        "node_structures": [
            {"node_id": node_id, "nodes": [left, right]}
            for node_id, left, right in nodes
        ],
        "obligations": obligations,
        "operators": operators,
        "representation_depth": "R2",
        "source_members": [],
        "unexplained_members": [],
    }
    sources = [
        {
            "authors": ["Andy T. S. Wan", "Alexander Bihlo", "Jean-Christophe Nave"],
            "doi": "10.1137/16M110719X",
            "equation_claim": "Four coordinate-wise divided differences of reciprocal square-root gravitational-distance terms are given in factorized operational form.",
            "equation_locator": "Section 5.3, equations displayed after Eq. (27), arXiv HTML lines 544-553; Appendix B, Definition 31 and Theorem 33",
            "retrieved": "2026-08-30",
            "source_class": "PRIMARY_PEER_REVIEWED_ARTICLE",
            "source_id": "S001",
            "title": "Conservative methods for dynamical systems",
            "url": "https://arxiv.org/html/1612.02417v1",
            "venue": "SIAM Journal on Numerical Analysis 55(5), 2255-2285 (2017)",
        }
    ]
    source_formula = "Delta_z(1/sqrt(z))=-1/(sqrt(z_old)*sqrt(z_new)*(sqrt(z_old)+sqrt(z_new)))"
    dossier = {
        "case_id": "gf-cr3bp-2017-eq28",
        "retrieval_date": "2026-08-30",
        "schema_version": "RPSGapFillSourceDossierV1",
        "source_claims": [
            {
                "claim_id": "C001",
                "locator": "S001 Section 5.3, lines 544-553",
                "normalized_formula": source_formula,
                "normalized_formula_sha256": _sha_bytes(source_formula.encode()),
                "source_id": "S001",
            }
        ],
        "sources": sources,
    }
    return {
        "case_id": "gf-cr3bp-2017-eq28",
        "candidate_status": "CANDIDATE_ONLY_NOT_ADMITTED",
        "depth_review": "R2_NEWTON_DD_CANDIDATE",
        "members": members,
        "assumptions": assumptions,
        "symbols": symbols,
        "program": program,
        "dossier": dossier,
        "sources": sources,
        "lowering": {
            member_id: {
                "derivation": "Apply S001's reciprocal-square-root divided-difference rule and its chain rule to the corresponding old/new squared-distance nodes.",
                "source_claim_ids": ["C001"],
                "status": "DERIVED",
            }
            for member_id in members
        },
    }


def _r6_spec() -> dict[str, Any]:
    q = "(V-N*b)*T**Rational(3,2)/(N*c)"
    members = {
        "G0001": f"-N*k*T*(1+log({q}))-a*N**2/V",
        "G0002": "N*k*T/(V-N*b)-a*N**2/V**2",
        "G0003": f"N*k*(Rational(5,2)+log({q}))",
        "G0004": "Rational(3,2)*N*k*T-a*N**2/V",
        "G0005": "Rational(3,2)*N*k",
        "G0006": "N*k*T*V/(V-N*b)**2-2*a*N**2/V**2",
        "G0007": "1/(N*k*T*V/(V-N*b)**2-2*a*N**2/V**2)",
        "G0008": "Rational(3,2)*N*k*T+N*k*T*V/(V-N*b)-2*a*N**2/V",
    }
    operators = [
        _operator("O0001", "VALUE", "helmholtz", "F0001", arguments={"values": {"tau": "T", "nu": "V"}}),
        _operator("O0002", "DERIVATIVE", "dF_dnu_bound", "F0001", arguments={"variable": "nu", "order": 1}),
        _operator("O0003", "SUBSTITUTE", "dF_dnu_T", "F0001", inputs=["dF_dnu_bound"], arguments={"parameter": "tau", "value": "T"}),
        _operator("O0004", "SUBSTITUTE", "dF_dV", "F0001", inputs=["dF_dnu_T"], arguments={"parameter": "nu", "value": "V"}),
        _operator("O0005", "LINEAR_COMBINATION", "pressure", "F0001", inputs=["dF_dV"], arguments={"coefficients": ["-1"], "constant": "0"}),
        _operator("O0006", "DERIVATIVE", "dF_dtau_bound", "F0001", arguments={"variable": "tau", "order": 1}),
        _operator("O0007", "SUBSTITUTE", "dF_dtau_T", "F0001", inputs=["dF_dtau_bound"], arguments={"parameter": "tau", "value": "T"}),
        _operator("O0008", "SUBSTITUTE", "dF_dT", "F0001", inputs=["dF_dtau_T"], arguments={"parameter": "nu", "value": "V"}),
        _operator("O0009", "LINEAR_COMBINATION", "entropy", "F0001", inputs=["dF_dT"], arguments={"coefficients": ["-1"], "constant": "0"}),
        _operator("O0010", "LINEAR_COMBINATION", "internal_energy", "F0001", inputs=["helmholtz", "entropy"], arguments={"coefficients": ["1", "T"], "constant": "0"}),
        _operator("O0011", "DERIVATIVE", "isochoric_heat_capacity", "F0001", inputs=["internal_energy"], arguments={"variable": "T", "order": 1}),
        _operator("O0012", "DERIVATIVE", "dp_dV", "F0001", inputs=["pressure"], arguments={"variable": "V", "order": 1}),
        _operator("O0013", "LINEAR_COMBINATION", "bulk_modulus", "F0001", inputs=["dp_dV"], arguments={"coefficients": ["-V"], "constant": "0"}),
        _operator("O0014", "COMPOSE", "isothermal_compressibility", "F0002", inputs=["bulk_modulus"]),
        _operator("O0015", "LINEAR_COMBINATION", "enthalpy", "F0001", inputs=["internal_energy", "pressure"], arguments={"coefficients": ["1", "V"], "constant": "0"}),
    ]
    outputs = [
        "helmholtz",
        "pressure",
        "entropy",
        "internal_energy",
        "isochoric_heat_capacity",
        "bulk_modulus",
        "isothermal_compressibility",
        "enthalpy",
    ]
    assignments = [
        {
            "member_id": f"G{index:04d}",
            "operator_ids": _dependency_ids(operators, output),
            "output": output,
        }
        for index, output in enumerate(outputs, 1)
    ]
    obligations = [
        {
            "member_id": f"G{index:04d}",
            "obligation_id": f"Q{index:04d}",
            "output": output,
            "required": True,
        }
        for index, output in enumerate(outputs, 1)
    ]
    assumptions = {
        "predicates": [
            {
                "predicate_id": "P001",
                "source": "Deserno (2013), Eq. (1)",
                "statement": "T, V, and N are real thermodynamic variables; a, b, c, and k are real constants independent of T and V in the fixed-N lowering.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P002",
                "source": "Deserno (2013), Eq. (1) and text below it",
                "statement": "T, N, c, and k are positive, a and b are positive model constants, and V>N*b, so the logarithm argument is positive and V is nonzero.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P003",
                "source": "NIST teqp thermodynamic-derivative definitions; fixed-N specialization",
                "statement": "All T and V derivatives are taken at fixed N and fixed model constants in one homogeneous branch.",
                "status": "DECLARED",
            },
            {
                "predicate_id": "P004",
                "source": "P001-P003",
                "statement": "The Helmholtz value, pressure, entropy, internal energy, isochoric heat capacity, and isothermal bulk modulus expressions are defined on that real domain.",
                "status": "DERIVED",
            },
            {
                "predicate_id": "P005",
                "source": "NIST teqp compressibility definition and the G0006 denominator",
                "statement": "The package is restricted away from the spinodal where the isothermal bulk modulus vanishes; this is required only for G0007.",
                "status": "DECLARED",
            },
        ],
        "schema_version": "ScientificAssumptionContractV1",
        "status": "ASSUMPTION_COMPLETE",
        "symbols_artifact": "symbols.json",
        "verifier_scope_note": "The package proves exact algebraic/differential reconstructions for the single homogeneous van der Waals branch. It makes no phase-coexistence, Maxwell-construction, or stability claim.",
    }
    symbols = {
        "functions": [],
        "symbols": [
            {"name": name, "real": True, "nonzero": name in {"N", "T", "V", "c", "k"}}
            for name in ("N", "T", "V", "a", "b", "c", "k")
        ],
    }
    program = {
        "assumption_statuses": {f"P{index:03d}": status for index, status in enumerate(("DECLARED", "DECLARED", "DECLARED", "DERIVED", "DECLARED"), 1)},
        "assumptions_used": ["P001", "P002", "P003", "P004", "P005"],
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {},
        "latent_objects": [
            {
                "expression": "-N*k*tau*(1+log((nu-N*b)*tau**Rational(3,2)/(N*c)))-a*N**2/nu",
                "form": "FUNCTION_2",
                "latent_id": "F0001",
                "parameters": ["tau", "nu"],
            },
            {
                "expression": "1/z",
                "form": "SCALAR_KERNEL",
                "latent_id": "F0002",
                "parameters": ["z"],
            },
        ],
        "member_assignments": assignments,
        "node_structures": [],
        "obligations": obligations,
        "operators": operators,
        "representation_depth": "R6",
        "source_members": [],
        "unexplained_members": [],
    }
    sources = [
        {
            "authors": ["Markus Deserno"],
            "equation_claim": "The van der Waals Helmholtz free energy F(T,V,N) is given explicitly, with a, b, and c constant in T, V, and N.",
            "equation_locator": "Eq. (1), p. 1",
            "retrieved": "2026-08-30",
            "source_class": "INSTITUTIONAL_SCIENTIFIC_NOTE",
            "source_id": "S001",
            "title": "Van der Waals equation, Maxwell construction, and Legendre transforms",
            "url": "https://www.cmu.edu/biolphys/deserno/pdf/van-der-Waals-and-Maxwell.pdf",
            "venue": "Carnegie Mellon University Department of Physics note (2013)",
        },
        {
            "authors": ["National Institute of Standards and Technology"],
            "equation_claim": "Helmholtz-energy derivatives define pressure, entropy, internal energy, enthalpy, and isochoric heat capacity.",
            "equation_locator": "Thermodynamic Derivatives, Helmholtz energy derivatives",
            "retrieved": "2026-08-30",
            "source_class": "AUTHORITATIVE_TECHNICAL_DOCUMENTATION",
            "source_id": "S002",
            "title": "Thermodynamic Derivatives — teqp documentation",
            "url": "https://pages.nist.gov/teqp-docs/en/latest/derivs/derivs.html",
            "venue": "NIST",
        },
        {
            "authors": ["Markus Deserno"],
            "equation_claim": "Differentiating the scaled Helmholtz energy with volume yields the van der Waals pressure and its first two volume derivatives.",
            "equation_locator": "Eqs. (5), (6a), and (6b), p. 1",
            "retrieved": "2026-08-30",
            "source_class": "INSTITUTIONAL_SCIENTIFIC_NOTE",
            "source_id": "S003",
            "title": "Van der Waals equation, Maxwell construction, and Legendre transforms",
            "url": "https://www.cmu.edu/biolphys/deserno/pdf/van-der-Waals-and-Maxwell.pdf",
            "venue": "Carnegie Mellon University Department of Physics note (2013)",
        },
        {
            "authors": ["Gennady Y. Gor", "Alexander V. Neimark"],
            "doi": "10.1063/1.4964683",
            "equation_claim": "Isothermal compressibility and its reciprocal isothermal modulus are defined by beta_T=-(1/V)(partial V/partial P)_T and K_T=-V(partial P/partial V)_T.",
            "equation_locator": "Section II.B, Eqs. (5) and (6)",
            "retrieved": "2026-08-30",
            "source_class": "PRIMARY_PEER_REVIEWED_ARTICLE",
            "source_id": "S004",
            "title": "Modulus-pressure equation for confined fluids",
            "url": "https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=921308",
            "venue": "Journal of Chemical Physics 145, 164505 (2016)",
        },
    ]
    f_formula = "F(T,V,N)=-N*k*T*(1+log((V-N*b)*T^(3/2)/(N*c)))-a*N^2/V"
    derivative_formula = "p=-dF/dV; s=-dF/dT; u=F+T*s; cv=du/dT"
    response_formula = "kT=-V*dp/dV; kappaT=1/kT"
    dossier = {
        "case_id": "gf-vdw-2013-eq1",
        "retrieval_date": "2026-08-30",
        "schema_version": "RPSGapFillSourceDossierV1",
        "source_claims": [
            {
                "claim_id": "C001",
                "locator": "S001 Eq. (1)",
                "normalized_formula": f_formula,
                "normalized_formula_sha256": _sha_bytes(f_formula.encode()),
                "source_id": "S001",
            },
            {
                "claim_id": "C002",
                "locator": "S002 Helmholtz energy derivatives",
                "normalized_formula": derivative_formula,
                "normalized_formula_sha256": _sha_bytes(derivative_formula.encode()),
                "source_id": "S002",
            },
            {
                "claim_id": "C003",
                "locator": "S004 Eqs. (5)-(6)",
                "normalized_formula": response_formula,
                "normalized_formula_sha256": _sha_bytes(response_formula.encode()),
                "source_id": "S004",
            },
        ],
        "sources": sources,
    }
    return {
        "case_id": "gf-vdw-2013-eq1",
        "candidate_status": "CANDIDATE_ONLY_DEPTH_REVIEW_REQUIRED",
        "depth_review": "R6_MULTI_OPERATOR_MASTER_CANDIDATE",
        "members": members,
        "assumptions": assumptions,
        "symbols": symbols,
        "program": program,
        "dossier": dossier,
        "sources": sources,
        "lowering": {
            "G0001": {"derivation": "Direct source Eq. (1), notation-normalized only.", "source_claim_ids": ["C001"], "status": "DECLARED"},
            "G0002": {"derivation": "Evaluate -partial F/partial V at fixed N and constants.", "source_claim_ids": ["C001", "C002"], "status": "DERIVED"},
            "G0003": {"derivation": "Evaluate -partial F/partial T at fixed N and constants.", "source_claim_ids": ["C001", "C002"], "status": "DERIVED"},
            "G0004": {"derivation": "Reconstruct U=F+T*S.", "source_claim_ids": ["C001", "C002"], "status": "DERIVED"},
            "G0005": {"derivation": "Evaluate C_V=partial U/partial T at fixed V and N.", "source_claim_ids": ["C001", "C002"], "status": "DERIVED"},
            "G0006": {"derivation": "Evaluate the isothermal bulk modulus -V*partial p/partial V.", "source_claim_ids": ["C001", "C002", "C003"], "status": "DERIVED"},
            "G0007": {"derivation": "Compose reciprocal with the nonzero isothermal bulk modulus.", "source_claim_ids": ["C001", "C002", "C003"], "status": "DERIVED"},
            "G0008": {"derivation": "Reconstruct H=U+p*V.", "source_claim_ids": ["C001", "C002"], "status": "DERIVED"},
        },
    }


def _artifact_paths(package: Path) -> list[Path]:
    return [
        path
        for path in sorted(package.rglob("*"))
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    ]


def _build(spec: dict[str, Any]) -> None:
    package = ROOT / spec["case_id"]
    if package.exists():
        raise FileExistsError(f"refusing to overwrite existing package: {package}")
    package.mkdir(parents=True)
    for member_id, expression in spec["members"].items():
        _write_text(package / "members" / f"{member_id}.txt", expression)
    _write_json(package / "symbols.json", spec["symbols"])
    _write_json(package / "assumptions.json", spec["assumptions"])
    _write_json(package / "sources/source_dossier.json", spec["dossier"])

    catalog = {
        "members": [
            _source_member(member_id, f"members/{member_id}.txt", package)
            for member_id in sorted(spec["members"])
        ],
        "schema_version": "RPSSourceCatalogV1",
    }
    _write_json(package / "source_catalog.json", catalog)
    spec["program"]["source_members"] = catalog["members"]
    raw_program = spec["program"]
    typed = program_from_dict(raw_program)
    raw_program["program_id"] = canonical_program_hash(typed)
    _write_json(package / "reference/program.json", raw_program)

    source_manifest = {
        "case_id": spec["case_id"],
        "lowering_provenance": spec["lowering"],
        "schema_version": "RPSSourceManifestV1",
        "source_dossier": {
            "path": "sources/source_dossier.json",
            "sha256": _sha(package / "sources/source_dossier.json"),
        },
        "sources": spec["sources"],
    }
    _write_json(package / "source_manifest.json", source_manifest)

    proposer_view = {
        "assumptions": {"path": "assumptions.json", "sha256": _sha(package / "assumptions.json")},
        "package_id": spec["case_id"],
        "schema_version": "RPSProposerViewV1",
        "source_catalog": {
            "members": catalog["members"],
            "path": "source_catalog.json",
            "sha256": _sha(package / "source_catalog.json"),
        },
    }
    _write_json(package / "proposer_view.json", proposer_view)

    typed = program_from_dict(raw_program)
    compilation = compile_program(
        typed,
        # Package artifacts already provide the exact namespace consumed by M1.
        CompileContext(
            package_root=package,
            symbols=tuple(spec["symbols"]["symbols"]),
            functions=tuple(spec["symbols"]["functions"]),
            grammar_id="G_FULL",
        ),
    )
    if compilation.status != "COMPILED" or compilation.tautological:
        raise RuntimeError(f"compile failed: {compilation.to_dict()}")

    obligation_records: list[dict[str, Any]] = []
    for compiled in compilation.obligations:
        candidate_path = package / "reference/candidates" / f"{compiled.obligation_id}.txt"
        _write_text(candidate_path, compiled.candidate_expression)
        workspace = package / "verification" / compiled.obligation_id
        session = init_session(
            str(workspace),
            meta={
                "case_id": spec["case_id"],
                "obligation_id": compiled.obligation_id,
                "purpose": "candidate_gap_fill_exact_equality_receipt",
            },
            requested_proposer_mode="main",
        )
        current = load_expression(package / compiled.current_path, spec["symbols"]["symbols"])
        candidate = load_expression(candidate_path, spec["symbols"]["symbols"])
        set_current(session, current)
        proposal = validate_candidate(
            {
                "candidate_id": f"{spec['case_id']}-{compiled.obligation_id}",
                "hypothesis": "The compiled candidate may reconstruct this exact source member under the declared contract.",
                "candidate_expression_or_rewrite": candidate.text,
                "rationale": "This is the evaluator-only expression emitted by the frozen typed constructor.",
                "expected_structural_benefit": "The shared program reuses latent objects and typed operators across multiple source members.",
                "suggested_verification_strategy": "Run the exact symbolic verifier under the unchanged member namespace.",
                "required_assumptions": ["All required predicates are DECLARED or DERIVED in assumptions.json."],
                "assumptions_status": "DECLARED",
                "confidence": "high",
                "status": "HYPOTHESIS",
            }
        )
        hypothesis = record_proposal(session, proposal)
        outcome = adjudicate_candidate(session, candidate)
        if outcome.result.verdict != ZERO or not outcome.promoted:
            raise RuntimeError(f"{compiled.obligation_id}: {outcome.result.verdict}")
        run_root = Path(session.run_root)
        obligation_records.append(
            {
                "candidate_path": candidate_path.relative_to(package).as_posix(),
                "candidate_sha256": _sha(candidate_path),
                "current_member_id": compiled.member_id,
                "current_path": compiled.current_path,
                "current_sha256": compiled.current_sha256,
                "obligation_id": compiled.obligation_id,
                "output": next(item["output"] for item in raw_program["obligations"] if item["obligation_id"] == compiled.obligation_id),
                "proposal_step": hypothesis.step,
                "proposal_step_path": (run_root / "steps/step_001.json").relative_to(package).as_posix(),
                "proposal_step_sha256": _sha(run_root / "steps/step_001.json"),
                "required": compiled.required,
                "session_path": run_root.relative_to(package).as_posix(),
                "verification_step": outcome.step.step,
                "verification_step_path": outcome.step_path.relative_to(package).as_posix(),
                "verification_step_sha256": _sha(outcome.step_path),
                "verdict": outcome.result.verdict,
            }
        )
    obligations = {
        "case_id": spec["case_id"],
        "obligations": obligation_records,
        "schema_version": "RPSObligationSetV1",
        "summary": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": len(obligation_records)},
    }
    _write_json(package / "reference/obligations.json", obligations)

    manifest = {
        "artifact_hashes": [
            {"path": path.relative_to(package).as_posix(), "sha256": _sha(path)}
            for path in _artifact_paths(package)
        ],
        "candidate_status": spec["candidate_status"],
        "lowering_scope": "SYMBOLIC_SOURCE_OBJECT",
        "manifest_exclusion": "package.json is excluded because a file cannot contain its own stable hash.",
        "package_id": spec["case_id"],
        "package_status": "PACKAGE_READY",
        "proposed_depth": spec["depth_review"],
        "schema_version": PACKAGE_SCHEMA,
        "verdict_totals": obligations["summary"],
    }
    _write_json(package / "package.json", manifest)


def build_all() -> None:
    for spec in (_r2_spec(), _r6_spec()):
        _build(spec)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="create both packages exactly once")
    args = parser.parse_args()
    if not args.build:
        parser.error("the one-shot builder requires --build")
    build_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
