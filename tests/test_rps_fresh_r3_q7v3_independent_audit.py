from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import sympy as sp

from research.representation_program_search.audits.fresh_r3_q7v3_independent.validate import (
    AUDIT,
    CANDIDATE_COMMIT,
    PACKAGE,
    PROGRAM_IDS,
    ROOT,
    validate,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    canonical_program_hash,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import load_public_case


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_independent_audit_replays_and_rejects_admission():
    result = validate()
    assert result["status"] == "VALID_INDEPENDENT_AUDIT"
    assert result["verdict"] == "REJECT"
    assert result["recommended_disposition"] == "DIAGNOSTIC_ONLY"
    assert all(status == "COMPILED" for status in result["compiled_variants"].values())


def test_candidate_package_bytes_are_unchanged_from_reviewed_commit():
    completed = subprocess.run(
        ["git", "diff", "--exit-code", CANDIDATE_COMMIT, "--", str(PACKAGE.relative_to(ROOT))],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_primary_equation_excerpt_is_the_exact_hash_bound_theorem_block():
    path = PACKAGE / "source/theorem2-equations.tex"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "76cbf6191983c656681daca3b3c58bf9d62688fb5f4602ba0e42005dff0222a1"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("\\begin{equation}\\label{eq:integral_representation}\n")
    assert "sum\\limits_{\\pi \\in S_k}" in text
    assert "(\\zeta I - A)^{-1}E_{\\pi(1)}" in text
    assert text.endswith("\\end{equation}\n")


def test_public_surface_was_exact_and_contains_no_hidden_roles():
    case = load_public_case(PACKAGE / "proposer_view.json")
    assert case.namespace_provenance == "EXACT_PROPOSER_REFERENCE"
    assert tuple(case.accessed_paths) == (
        "assumptions.json",
        "members/M01.txt",
        "members/M02.txt",
        "members/M03.txt",
        "proposer_view.json",
        "source_catalog.json",
        "symbols.json",
    )
    visible = "\n".join((PACKAGE / item).read_text(encoding="utf-8") for item in case.accessed_paths).casefold()
    for forbidden in ("hermite", "frechet", "fréchet", "multiplicity", "repeated node", "third-order", "target representation", '"nodes"'):
        assert forbidden not in visible


def test_matrix_unit_paths_have_one_surviving_permutation_and_arity_four_nodes():
    rows = {
        "M01": (((1, 1), (1, 2), (2, 2)), (1, 2), ("a", "a", "b", "b")),
        "M02": (((1, 1), (1, 2), (2, 3)), (1, 3), ("a", "a", "b", "c")),
        "M03": (((1, 2), (2, 3), (3, 3)), (1, 3), ("a", "b", "c", "c")),
    }
    for edges, target, nodes in rows.values():
        surviving = []
        for permutation in itertools.permutations(range(3)):
            chain = tuple(edges[index] for index in permutation)
            if (
                chain[0][0] == target[0]
                and chain[-1][1] == target[1]
                and all(chain[index][1] == chain[index + 1][0] for index in range(2))
            ):
                surviving.append(permutation)
        assert surviving == [(0, 1, 2)]
        assert len(nodes) == 4
    assert tuple(sorted((nodes.count(nodes[0]) for _, _, nodes in rows.values()))) == (1, 2, 2)


def test_independent_residue_replay_is_exact_zero_for_every_member():
    z, a, b, c, p, q, r = sp.symbols("z a b c p q r", real=True)
    nodes = {
        "M01": (a, a, b, b),
        "M02": (a, a, b, c),
        "M03": (a, b, c, c),
    }
    namespace = {"a": a, "b": b, "c": c, "p": p, "q": q, "r": r, "exp": sp.exp}
    for member_id, sequence in nodes.items():
        integrand = sp.exp(z) / sp.prod(z - node for node in sequence)
        coefficient = sum(sp.residue(integrand, z, pole) for pole in sorted(set(sequence), key=str))
        member = sp.sympify((PACKAGE / f"members/{member_id}.txt").read_text(encoding="utf-8"), locals=namespace)
        assert sp.factor(sp.together(member - p * q * r * coefficient)) == 0


def test_canonical_programs_recompile_to_the_stored_candidates():
    loaded = load_case_package(PACKAGE)
    programs = {"G_FULL": loaded.program}
    for grammar in ("G_NO_HERMITE", "G_PRIMITIVE"):
        programs[grammar] = program_from_dict(_read(PACKAGE / f"reference/ablations/{grammar}.program.json"))
    suffix = {"G_FULL": "full", "G_NO_HERMITE": "no_hermite", "G_PRIMITIVE": "primitive"}
    for grammar, program in programs.items():
        assert canonical_program_hash(program) == PROGRAM_IDS[grammar]
        context = loaded.context if grammar == "G_FULL" else CompileContext(
            PACKAGE.resolve(), tuple(loaded.context.symbols), (), grammar_id=grammar
        )
        compiled = compile_program(program, context)
        assert compiled.status == "COMPILED"
        assert compiled.tautological is False
        for obligation in compiled.obligations:
            stored = PACKAGE / f"reference/candidates/{obligation.obligation_id}.{suffix[grammar]}.txt"
            assert stored.read_text(encoding="utf-8") == obligation.candidate_expression + "\n"


def test_old_test_generic_superfamily_is_explicit_and_was_omitted_by_candidate_audit():
    manifest = _read(ROOT / "research/assumption_complete_representation/TEST_MANIFEST.json")
    assert "mp-opitz-dd-01" in manifest["CHALLENGE"]
    opitz = _read(ROOT / "research/assumption_complete_representation/cases/mathphys/mp-opitz-dd-01.json")
    assert "nodes, not necessarily distinct" in opitz["expression_sketch"].casefold()
    assert "repeated nodes" in opitz["latent_structure"].casefold()
    package_audit = _read(PACKAGE / "source/duplicate_audit.json")
    reviewed = {item["identity"] for item in package_audit["manual_structural_anchors"]}
    assert "mp-opitz-dd-01" not in reviewed
    assert "mp-hermite-fA-01" not in reviewed
    independent = _read(AUDIT)
    relations = {item["identity"]: item["relation"] for item in independent["duplicate_and_freshness"]["controls"]}
    assert relations["mp-opitz-dd-01"] == "DIRECT_GENERIC_SUPERFAMILY"
    assert relations["C3J9"] == "SAME_R3_PRIMITIVE_RECURRENCE_DIFFERENT_FUNCTION"
