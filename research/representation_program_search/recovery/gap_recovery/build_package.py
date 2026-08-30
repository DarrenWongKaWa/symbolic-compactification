"""One-shot builder for the strict opaque R2 recovery package.

The primary-source TeX excerpts are staged as exact bytes in the package tree.
This builder verifies their frozen hashes before creating any other artifact and
refuses to overwrite a completed package.  It does not download sources, alter
the verifier/parser/grammar, admit a benchmark case, or touch shared manifests.
"""
from __future__ import annotations

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
)

from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
)
from research.representation_program_search.program_ir.schema import program_from_dict


COLLECTION = Path(__file__).resolve().parent
PACKAGE = COLLECTION / "rps-candidate-k9-001"
VARIANTS = ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE")
SOURCE_EXCERPT_HASHES = {
    "source/upstream/CM_dynSys.lines_661_709.tex": (
        "9a223e976adadde8a1b2a4691b3e9f161b1834c26da93ac1b1e63d5efa97bd5e"
    ),
    "source/upstream/CM_dynSys.lines_710_730.tex": (
        "98b2390b9e9e6ef77240751c656408ca4de25f35055ae010d21cb2efcfb5325f"
    ),
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
}


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _atomic_bytes(path: Path, value: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _write_json(path: Path, value: Any) -> None:
    _atomic_bytes(path, _json_bytes(value))


def _write_text(path: Path, value: str) -> None:
    _atomic_bytes(path, (value.rstrip() + "\n").encode("utf-8"))


def _verify_staged_sources() -> None:
    if (PACKAGE / "package.json").exists():
        raise FileExistsError(f"refusing to overwrite completed evidence: {PACKAGE}")
    actual_files = {
        path.relative_to(PACKAGE).as_posix()
        for path in PACKAGE.rglob("*")
        if path.is_file()
    }
    if actual_files != set(SOURCE_EXCERPT_HASHES):
        raise RuntimeError(f"STAGED_SOURCE_SET_INVALID:{sorted(actual_files)}")
    for relative, expected in SOURCE_EXCERPT_HASHES.items():
        if _sha(PACKAGE / relative) != expected:
            raise RuntimeError(f"STAGED_SOURCE_HASH_MISMATCH:{relative}")


def _source_members(members: dict[str, str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for member_id, expression in members.items():
        relative = f"members/{member_id}.txt"
        _write_text(PACKAGE / relative, expression)
        rows.append(
            {
                "member_id": member_id,
                "path": relative,
                "sha256": _sha(PACKAGE / relative),
            }
        )
    return rows


def _operator(
    operator_id: str,
    kind: str,
    output: str,
    *,
    inputs: list[str] | None = None,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "arguments": arguments or {},
        "inputs": inputs or [],
        "latent_id": "L9K1",
        "operator": kind,
        "operator_id": operator_id,
        "output": output,
    }


def _dependency_ids(operators: list[dict[str, Any]], output: str) -> list[str]:
    by_output = {item["output"]: item for item in operators}
    result: list[str] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in by_output:
            return
        seen.add(name)
        item = by_output[name]
        for dependency in item["inputs"]:
            visit(dependency)
        result.append(item["operator_id"])

    visit(output)
    return result


def _with_program_id(raw: dict[str, Any]) -> dict[str, Any]:
    program = program_from_dict(raw)
    return raw | {"program_id": canonical_program_hash(program)}


def _programs(
    source_members: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    nodes = (
        (
            "N9K1",
            "(x1_old+alpha)**2+x2_hold**2",
            "(x1_new+alpha)**2+x2_hold**2",
            "x1_new+x1_old+2*alpha",
        ),
        (
            "N9K2",
            "(x1_hold+alpha)**2+x2_old**2",
            "(x1_hold+alpha)**2+x2_new**2",
            "x2_new+x2_old",
        ),
        (
            "N9K3",
            "(x1_old-beta)**2+x2_hold**2",
            "(x1_new-beta)**2+x2_hold**2",
            "x1_new+x1_old-2*beta",
        ),
        (
            "N9K4",
            "(x1_hold-beta)**2+x2_old**2",
            "(x1_hold-beta)**2+x2_new**2",
            "x2_new+x2_old",
        ),
    )
    common = {
        "assumption_statuses": {
            "P9A1": "DECLARED",
            "P9A2": "DECLARED",
            "P9A3": "DECLARED",
            "P9A4": "DERIVED",
        },
        "assumptions_used": ["P9A1", "P9A2", "P9A3", "P9A4"],
        "grammar_version": "RepresentationGrammarV1",
        "instance_maps": {
            f"M9H{index}": {
                "left_node": left,
                "right_node": right,
            }
            for index, (_node_id, left, right, _coefficient) in enumerate(nodes, 1)
        },
        "latent_objects": [
            {
                "expression": "1/sqrt(z)",
                "form": "SCALAR_KERNEL",
                "latent_id": "L9K1",
                "parameters": ["z"],
            }
        ],
        "source_members": source_members,
        "unexplained_members": [],
    }
    full_operators: list[dict[str, Any]] = []
    full_assignments: list[dict[str, Any]] = []
    full_obligations: list[dict[str, Any]] = []
    for index, (node_id, _left, _right, coefficient) in enumerate(nodes, 1):
        dd_output = f"d9_{index}"
        output = f"c9_{index}"
        full_operators.extend(
            [
                _operator(
                    f"OP9N{index}",
                    "NEWTON_DD",
                    dd_output,
                    arguments={"nodes": node_id},
                ),
                _operator(
                    f"OP9L{index}",
                    "LINEAR_COMBINATION",
                    output,
                    inputs=[dd_output],
                    arguments={"coefficients": [coefficient], "constant": "0"},
                ),
            ]
        )
        member_id = f"M9H{index}"
        obligation_id = f"Q9H{index}"
        full_assignments.append(
            {
                "member_id": member_id,
                "operator_ids": _dependency_ids(full_operators, output),
                "output": output,
            }
        )
        full_obligations.append(
            {
                "member_id": member_id,
                "obligation_id": obligation_id,
                "output": output,
                "required": True,
            }
        )
    full = _with_program_id(
        common
        | {
            "member_assignments": full_assignments,
            "node_structures": [
                {"node_id": node_id, "nodes": [left, right]}
                for node_id, left, right, _coefficient in nodes
            ],
            "obligations": full_obligations,
            "operators": full_operators,
            "representation_depth": "R2_NEWTON_DD",
        }
    )

    primitive_operators: list[dict[str, Any]] = []
    primitive_assignments: list[dict[str, Any]] = []
    primitive_obligations: list[dict[str, Any]] = []
    for index, (_node_id, left, right, coefficient) in enumerate(nodes, 1):
        left_output = f"p9_left_{index}"
        right_output = f"p9_right_{index}"
        dd_output = f"p9_dd_{index}"
        output = f"p9_component_{index}"
        primitive_operators.extend(
            [
                _operator(
                    f"P9V{index}A",
                    "VALUE",
                    left_output,
                    arguments={"node": left},
                ),
                _operator(
                    f"P9V{index}B",
                    "VALUE",
                    right_output,
                    arguments={"node": right},
                ),
                _operator(
                    f"P9D{index}",
                    "LINEAR_COMBINATION",
                    dd_output,
                    inputs=[left_output, right_output],
                    arguments={
                        "coefficients": [f"-1/(({right})-({left}))", f"1/(({right})-({left}))"],
                        "constant": "0",
                    },
                ),
                _operator(
                    f"P9L{index}",
                    "LINEAR_COMBINATION",
                    output,
                    inputs=[dd_output],
                    arguments={"coefficients": [coefficient], "constant": "0"},
                ),
            ]
        )
        primitive_assignments.append(
            {
                "member_id": f"M9H{index}",
                "operator_ids": _dependency_ids(primitive_operators, output),
                "output": output,
            }
        )
        primitive_obligations.append(
            {
                "member_id": f"M9H{index}",
                "obligation_id": f"Q9H{index}",
                "output": output,
                "required": True,
            }
        )
    primitive = _with_program_id(
        common
        | {
            "member_assignments": primitive_assignments,
            "node_structures": [],
            "obligations": primitive_obligations,
            "operators": primitive_operators,
            "representation_depth": "R2_COMPOSITIONAL_DIVIDED_DIFFERENCE",
        }
    )
    return full, primitive


def _compile(
    program_payload: dict[str, Any],
    symbols: list[dict[str, Any]],
    grammar_id: str,
) -> tuple[dict[str, Any], Any]:
    program = program_from_dict(program_payload)
    result = compile_program(
        program,
        CompileContext(PACKAGE.resolve(), tuple(symbols), (), grammar_id=grammar_id),
    )
    if result.status != "COMPILED" or result.tautological:
        raise RuntimeError(f"COMPILE_FAILED:{grammar_id}:{result.to_dict()}")
    return result.to_dict(), result


def _verify(
    symbols: list[dict[str, Any]],
    variants: dict[str, tuple[dict[str, Any], Any]],
) -> None:
    workspace = PACKAGE / "verification/workspace"
    attempts: list[dict[str, Any]] = []
    counts = {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 0}
    for variant_name, (_compile_payload, compiled) in variants.items():
        suffix = variant_name.casefold().replace("g_", "")
        for obligation in compiled.obligations:
            candidate_relative = (
                f"reference/candidates/{obligation.obligation_id}.{suffix}.txt"
            )
            candidate_path = PACKAGE / candidate_relative
            _write_text(candidate_path, obligation.candidate_expression)
            member_path = PACKAGE / obligation.current_path
            current = load_expression(member_path, symbols)
            candidate = load_expression(candidate_path, symbols)
            session = init_session(
                str(workspace),
                meta={
                    "case_package": PACKAGE.name,
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
                        f"{PACKAGE.name}-{variant_name}-{obligation.obligation_id}"
                    ),
                    "confidence": "high",
                    "expected_structural_benefit": (
                        "The executable M1 program reconstructs one hash-bound member."
                    ),
                    "hypothesis": (
                        "The compiled program output is exactly equivalent to the member."
                    ),
                    "rationale": "This is the selected typed constructor output.",
                    "required_assumptions": ["package ScientificAssumptionContract"],
                    "status": "HYPOTHESIS",
                    "suggested_verification_strategy": (
                        "Run the exact verifier on the hash-bound member and candidate."
                    ),
                },
            )
            outcome = adjudicate_candidate(
                session,
                candidate,
                meta={
                    "case_package": PACKAGE.name,
                    "grammar_variant": variant_name,
                    "obligation_id": obligation.obligation_id,
                },
            )
            if outcome.result.verdict != ZERO:
                raise RuntimeError(
                    f"VERIFY_FAILED:{variant_name}:{obligation.obligation_id}:"
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
                    "verdict": "ZERO",
                }
            )
            if variant_name == "G_FULL":
                counts["ZERO"] += 1
    _write_json(
        PACKAGE / "verification/index.json",
        {
            "attempts": attempts,
            "required_g_full_verdicts": counts,
            "schema_version": "RPSVerificationIndexV1",
        },
    )
    full_attempts = {
        row["obligation_id"]: row
        for row in attempts
        if row["program_variant"] == "G_FULL"
    }
    rows: list[dict[str, Any]] = []
    for index in range(1, 5):
        obligation_id = f"Q9H{index}"
        attempt = full_attempts[obligation_id]
        current_path = f"members/M9H{index}.txt"
        candidate_path = attempt["candidate_path"]
        run_id = attempt["run_id"]
        rows.append(
            {
                "candidate_path": candidate_path,
                "candidate_sha256": _sha(PACKAGE / candidate_path),
                "current_member_id": f"M9H{index}",
                "current_path": current_path,
                "current_sha256": _sha(PACKAGE / current_path),
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
        PACKAGE / "reference/obligations.json",
        {
            "obligations": rows,
            "schema_version": "RPSObligationsV1",
            "summary": counts,
        },
    )


def _finish_manifest() -> None:
    artifacts = [
        {"path": path.relative_to(PACKAGE).as_posix(), "sha256": _sha(path)}
        for path in sorted(PACKAGE.rglob("*"))
        if path.is_file()
        and path.name != "package.json"
        and "__pycache__" not in path.parts
        and not path.name.startswith(".")
    ]
    _write_json(
        PACKAGE / "package.json",
        {
            "admission_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "artifact_hashes": artifacts,
            "audited_depth": "R2_NEWTON_DD",
            "eligibility": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "lowering_scope": "SOURCE_EQUATION_INSTANCE",
            "manifest_exclusion": (
                "package.json is excluded because a file cannot contain its own stable hash."
            ),
            "package_id": PACKAGE.name,
            "package_status": "PACKAGE_READY",
            "schema_version": "RPSCasePackageV1",
            "source_identity": (
                "Wan-Bihlo-Nave-2017-Section-5.3-unnumbered-coordinate-identities"
            ),
            "verdict_totals": {"NONZERO": 0, "UNKNOWN": 0, "ZERO": 12},
        },
    )


def build() -> Path:
    _verify_staged_sources()
    members = {
        "M9H1": (
            "-(x1_new+x1_old+2*alpha)/(sqrt((x1_old+alpha)**2+x2_hold**2)*"
            "sqrt((x1_new+alpha)**2+x2_hold**2)*(sqrt((x1_old+alpha)**2+"
            "x2_hold**2)+sqrt((x1_new+alpha)**2+x2_hold**2)))"
        ),
        "M9H2": (
            "-(x2_new+x2_old)/(sqrt((x1_hold+alpha)**2+x2_old**2)*"
            "sqrt((x1_hold+alpha)**2+x2_new**2)*(sqrt((x1_hold+alpha)**2+"
            "x2_old**2)+sqrt((x1_hold+alpha)**2+x2_new**2)))"
        ),
        "M9H3": (
            "-(x1_new+x1_old-2*beta)/(sqrt((x1_old-beta)**2+x2_hold**2)*"
            "sqrt((x1_new-beta)**2+x2_hold**2)*(sqrt((x1_old-beta)**2+"
            "x2_hold**2)+sqrt((x1_new-beta)**2+x2_hold**2)))"
        ),
        "M9H4": (
            "-(x2_new+x2_old)/(sqrt((x1_hold-beta)**2+x2_old**2)*"
            "sqrt((x1_hold-beta)**2+x2_new**2)*(sqrt((x1_hold-beta)**2+"
            "x2_old**2)+sqrt((x1_hold-beta)**2+x2_new**2)))"
        ),
    }
    source_members = _source_members(members)
    symbols = [
        {"name": name, "nonzero": False, "real": True}
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
    ]
    _write_json(PACKAGE / "symbols.json", {"functions": [], "symbols": symbols})
    assumptions = {
        "predicates": [
            {
                "predicate_id": "P9A1",
                "source": "S9P1",
                "statement": (
                    "All retained coordinate and mass variables are real; no complex "
                    "branch is used."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P9A2",
                "source": "S9P2",
                "statement": (
                    "alpha and beta are relative masses satisfying alpha+beta=1; "
                    "the source does not state positivity here and this package does "
                    "not add it."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P9A3",
                "source": "S9P3A and S9P3B",
                "statement": (
                    "For each retained expression, both old/new squared-distance "
                    "radicands are positive and unequal. This is an explicitly "
                    "retained nondegenerate stratum, not a claim about every physical "
                    "trajectory."
                ),
                "status": "DECLARED",
            },
            {
                "predicate_id": "P9A4",
                "source": "P9A3 and S9P4",
                "statement": (
                    "The real square roots and every displayed reciprocal, node "
                    "difference, and square-root-sum denominator are nonzero on the "
                    "retained stratum."
                ),
                "status": "DERIVED",
            },
        ],
        "schema_version": "ScientificAssumptionContractV1",
        "status": "ASSUMPTION_COMPLETE",
        "symbols_artifact": "symbols.json",
        "verifier_scope_note": (
            "The exact namespace records every symbol as real without inferring "
            "real:false. Relational positivity, inequality, and alpha+beta=1 remain "
            "explicit contract predicates; exact ZERO does not silently prove them."
        ),
    }
    _write_json(PACKAGE / "assumptions.json", assumptions)
    catalog = {
        "members": [
            {"locator_id": f"L9H{index}", **row}
            for index, row in enumerate(source_members, 1)
        ],
        "schema_version": "RPSMemberCatalogV1",
        "symbols_path": "symbols.json",
        "symbols_sha256": _sha(PACKAGE / "symbols.json"),
    }
    _write_json(PACKAGE / "source_catalog.json", catalog)
    _write_json(
        PACKAGE / "proposer_view.json",
        {
            "assumptions": {
                "path": "assumptions.json",
                "sha256": _sha(PACKAGE / "assumptions.json"),
            },
            "case_id": "C9H4",
            "schema_version": "RPSProposerViewV1",
            "source_catalog": {
                "path": "source_catalog.json",
                "sha256": _sha(PACKAGE / "source_catalog.json"),
            },
            "structural_observations": {
                "member_count": 4,
                "shared_visible_calls": ["sqrt"],
                "source_scope": "four real scalar expressions on one declared stratum",
            },
        },
    )

    excerpt_rows = [
        {"path": relative, "sha256": digest}
        for relative, digest in sorted(SOURCE_EXCERPT_HASHES.items())
    ]
    dossier = {
        "case_id": "C9H4",
        "numbering_correction": {
            "claim": (
                "The four retained coordinate identities are unnumbered align* lines "
                "in Section 5.3. They follow the source label 3bodySys and precede "
                "the later source label R3B_RHS; they are not equation (28)."
            ),
            "source_locator_ids": ["S9N1", "S9N2"],
        },
        "primary_source": {
            "authors": [
                "Andy T. S. Wan",
                "Alexander Bihlo",
                "Jean-Christophe Nave",
            ],
            "doi": "10.1137/16M110719X",
            "retrieved_on": "2026-08-30",
            "source_archive_sha256": (
                "698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a"
            ),
            "source_file": "CM_dynSys.tex",
            "source_file_sha256": (
                "59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3"
            ),
            "title": "Conservative methods for dynamical systems",
            "url": "https://arxiv.org/e-print/1612.02417v1",
            "venue": "SIAM Journal on Numerical Analysis 55(5), 2255-2285 (2017)",
        },
        "source_artifacts": excerpt_rows,
        "source_locators": {
            "S9N1": {
                "claim": (
                    "The retained formulas occur in an unnumbered align* block after "
                    "the source label 3bodySys."
                ),
                "path": "source/upstream/CM_dynSys.lines_661_709.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_661_709.tex"
                ],
                "upstream_lines": "661-709 (labels/formulas at 663-709)",
            },
            "S9N2": {
                "claim": (
                    "The next numbered source environment begins later with label "
                    "R3B_RHS."
                ),
                "path": "source/upstream/CM_dynSys.lines_710_730.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_710_730.tex"
                ],
                "upstream_lines": "710-730 (next label at 722)",
            },
            "S9P1": {
                "claim": "Appendix B constructs the rules for real t and real x entries.",
                "path": "source/upstream/CM_dynSys.lines_1001_1005.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_1001_1005.tex"
                ],
                "upstream_lines": "1001-1005 (claim at 1003)",
            },
            "S9P2": {
                "claim": "alpha and beta are relative masses with alpha+beta=1.",
                "path": "source/upstream/CM_dynSys.lines_661_709.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_661_709.tex"
                ],
                "upstream_lines": "661-709 (claim at 671)",
            },
            "S9R1": {
                "claim": "The first-order divided difference is an exact quotient.",
                "path": "source/upstream/CM_dynSys.lines_1062_1069.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_1062_1069.tex"
                ],
                "upstream_lines": "1062-1069 (definition at 1065-1069)",
            },
            "S9P4": {
                "claim": "The reciprocal rule requires zero outside the image of f.",
                "path": "source/upstream/CM_dynSys.lines_1088_1118.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_1088_1118.tex"
                ],
                "upstream_lines": "1088-1118 (rule at 1100-1104)",
            },
            "S9P3A": {
                "claim": "The scalar chain rule states Delta_i g != 0.",
                "path": "source/upstream/CM_dynSys.lines_1088_1118.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_1088_1118.tex"
                ],
                "upstream_lines": "1088-1118 (rule at 1114-1118)",
            },
            "S9P3B": {
                "claim": "The rational-power rule assumes positive nodes when q>1.",
                "path": "source/upstream/CM_dynSys.lines_1148_1159.tex",
                "sha256": SOURCE_EXCERPT_HASHES[
                    "source/upstream/CM_dynSys.lines_1148_1159.tex"
                ],
                "upstream_lines": "1148-1159 (rule at 1148-1153)",
            },
            **{
                f"S9M{index}": {
                    "claim": (
                        f"The source's unnumbered coordinate identity {index} of four."
                    ),
                    "path": "source/upstream/CM_dynSys.lines_661_709.tex",
                    "sha256": SOURCE_EXCERPT_HASHES[
                        "source/upstream/CM_dynSys.lines_661_709.tex"
                    ],
                    "upstream_lines": f"661-709 (identity at {704 + index})",
                }
                for index in range(1, 5)
            },
        },
    }
    _write_json(PACKAGE / "source/dossier.json", dossier)
    lowering = {
        "derivation_status": "DERIVED_FROM_PRIMARY_SOURCE",
        "lowering_scope": "SOURCE_EQUATION_INSTANCE",
        "members": {
            f"M9H{index}": {
                "notation_map": notation_map,
                "source_locator_id": f"S9M{index}",
                "statement": (
                    "Replace the source midpoint by half the old/new sum and expand "
                    "the source A or B square-root definition; no scientific meaning "
                    "or source bytes are changed."
                ),
                "status": "DERIVED",
            }
            for index, notation_map in enumerate(
                (
                    {
                        "x_1^k": "x1_old",
                        "x_1^(k+1)": "x1_new",
                        "x_2^s": "x2_hold",
                        "2*overline{x}_1": "x1_old+x1_new",
                    },
                    {
                        "x_1^r": "x1_hold",
                        "x_2^k": "x2_old",
                        "x_2^(k+1)": "x2_new",
                        "2*overline{x}_2": "x2_old+x2_new",
                    },
                    {
                        "x_1^k": "x1_old",
                        "x_1^(k+1)": "x1_new",
                        "x_2^s": "x2_hold",
                        "2*overline{x}_1": "x1_old+x1_new",
                    },
                    {
                        "x_1^r": "x1_hold",
                        "x_2^k": "x2_old",
                        "x_2^(k+1)": "x2_new",
                        "2*overline{x}_2": "x2_old+x2_new",
                    },
                ),
                1,
            )
        },
        "shared_source_rules": [
            "S9R1",
            "S9P4",
            "S9P3A",
            "S9P3B",
        ],
    }
    _write_json(PACKAGE / "source/lowering.json", lowering)
    _write_json(
        PACKAGE / "source_manifest.json",
        {
            "member_lowering": {
                f"M9H{index}": f"source/lowering.json#M9H{index}"
                for index in range(1, 5)
            },
            "schema_version": "RPSSourceManifestV1",
            "source_artifacts": excerpt_rows,
            "source_dossier": {
                "path": "source/dossier.json",
                "sha256": _sha(PACKAGE / "source/dossier.json"),
            },
            "sources": [
                dossier["primary_source"]
                | {
                    "artifact_sha256": dossier["primary_source"]["source_archive_sha256"],
                    "locator": (
                        "Section 5.3 unnumbered displays in CM_dynSys.tex lines "
                        "699-709; Appendix B lines 1003, 1064-1069, 1100-1118, "
                        "and 1148-1159"
                    ),
                }
            ],
        },
    )

    _write_json(
        PACKAGE / "reference/obligations.json",
        {
            "obligations": [
                {
                    "current_member_id": f"M9H{index}",
                    "obligation_id": f"Q9H{index}",
                    "required": True,
                }
                for index in range(1, 5)
            ],
            "schema_version": "RPSObligationCatalogV1",
        },
    )
    full, primitive = _programs(source_members)
    _write_json(PACKAGE / "reference/program.json", full)
    _write_json(PACKAGE / "reference/ablations/G_NO_HERMITE.program.json", full)
    _write_json(PACKAGE / "reference/ablations/G_PRIMITIVE.program.json", primitive)
    variants = {
        "G_FULL": _compile(full, symbols, "G_FULL"),
        "G_NO_HERMITE": _compile(full, symbols, "G_NO_HERMITE"),
        "G_PRIMITIVE": _compile(primitive, symbols, "G_PRIMITIVE"),
    }
    for grammar_id, (payload, _compiled) in variants.items():
        _write_json(
            PACKAGE / "reference/compilations" / f"{grammar_id}.json",
            {
                "compilation": payload,
                "grammar_id": grammar_id,
                "program_id": (
                    full["program_id"] if grammar_id != "G_PRIMITIVE" else primitive["program_id"]
                ),
                "schema_version": "RPSCompilationReceiptV1",
            },
        )
    _write_json(
        PACKAGE / "reference/review.json",
        {
            "candidate_status": "CANDIDATE_FOR_INDEPENDENT_REVIEW",
            "depth_assessment": "R2_NEWTON_DD",
            "freshness_scope": (
                "REPAIR_OF_REJECTED_PREDECESSOR_NOT_A_NEW_SCIENTIFIC_IDENTITY"
            ),
            "grammar_assessment": {
                "g_full": "COMPILED",
                "g_no_hermite": "COMPILED",
                "g_primitive": "COMPILED",
                "named_primitive_required": False,
            },
            "leakage_assessment": (
                "OPAQUE_PUBLIC_IDS_AND_NO_SOURCE_OR_TARGET_OPERATOR NAMES; FORMULA-"
                "INTRINSIC FACTORIZATION REMAINS A MANUAL EASINESS RISK"
            ),
            "predecessor": (
                "research/representation_program_search/packages/gap_fill/"
                "gf-cr3bp-2017-eq28"
            ),
            "review_policy": "RPS_GAP_RECOVERY_REVIEW_V1",
        },
    )
    _verify(symbols, variants)
    _finish_manifest()
    return PACKAGE


if __name__ == "__main__":
    print(build())
