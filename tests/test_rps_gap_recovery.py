"""Regression tests for the strict R2 repair and bounded R6 mining gap."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from research.representation_program_search.recovery.gap_recovery.build_package import (
    SOURCE_EXCERPT_HASHES,
    build,
)
from research.representation_program_search.recovery.gap_recovery.validate import (
    CANDIDATE,
    PACKAGE_ID,
    PREDECESSOR,
    PREDECESSOR_TREE_SHA256,
    PUBLIC_FORBIDDEN_TERMS,
    _tree_hash,
    validate,
)
from research.representation_program_search.program_ir import (
    CompileContext,
    compile_program,
    load_case_package,
)
from research.representation_program_search.program_ir.schema import program_from_dict
from research.representation_program_search.search import load_public_case


ROOT = Path(__file__).resolve().parents[1]
COLLECTION = ROOT / "research/representation_program_search/recovery/gap_recovery"
PACKAGE = COLLECTION / PACKAGE_ID


def _json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def report():
    return validate(ROOT)


def test_recovery_audit_is_valid_candidate_only_with_negative_r6(report):
    assert report["status"] == "VALID"
    assert report["admission_decision"] == "NO_ADMISSION_PERFORMED"
    assert report["admission_self_assessment"] == CANDIDATE
    assert all(report["hard_checks"].values())
    assert report["r6_mining"]["status"] == "NO_DEFENSIBLE_R6_CANDIDATE"
    assert report["r6_mining"]["candidate_count"] == 0
    assert report["r6_mining"]["package_created"] is False


def test_actual_public_loader_has_exact_hash_bound_real_namespace():
    case = load_public_case(PACKAGE / "proposer_view.json")
    symbols = tuple(_json(PACKAGE / "symbols.json")["symbols"])
    statuses = {
        row["predicate_id"]: row["status"]
        for row in _json(PACKAGE / "assumptions.json")["predicates"]
    }
    assert case.case_id == "C9H4"
    assert case.symbols == symbols
    assert all(item["real"] is True for item in case.symbols)
    assert not any(item["real"] is False for item in case.symbols)
    assert dict(case.assumption_statuses) == statuses
    assert case.namespace_provenance == "EXACT_PROPOSER_REFERENCE"
    assert set(case.accessed_paths) == {
        "assumptions.json",
        "members/M9H1.txt",
        "members/M9H2.txt",
        "members/M9H3.txt",
        "members/M9H4.txt",
        "proposer_view.json",
        "source_catalog.json",
        "symbols.json",
    }
    assert all(
        not ({"reference", "verification", "final", "runs", "steps"} & set(Path(path).parts))
        for path in case.accessed_paths
    )


def test_public_ids_are_opaque_and_operator_target_terms_are_absent():
    case = load_public_case(PACKAGE / "proposer_view.json")
    public = [
        _json(PACKAGE / "proposer_view.json"),
        _json(PACKAGE / "source_catalog.json"),
        _json(PACKAGE / "assumptions.json"),
        _json(PACKAGE / "symbols.json"),
        *[member.expression for member in case.members],
    ]
    blob = json.dumps(public, sort_keys=True, ensure_ascii=False).casefold()
    assert case.case_id == "C9H4"
    assert [member.member_id for member in case.members] == [
        "M9H1",
        "M9H2",
        "M9H3",
        "M9H4",
    ]
    assert not any(term in blob for term in PUBLIC_FORBIDDEN_TERMS)
    assert "gf-cr3bp-2017-eq28" not in blob


def test_exact_primary_source_bytes_and_numbering_correction_are_bound():
    dossier = _json(PACKAGE / "source/dossier.json")
    for relative, expected in SOURCE_EXCERPT_HASHES.items():
        assert hashlib.sha256((PACKAGE / relative).read_bytes()).hexdigest() == expected
    assert {
        row["path"]: row["sha256"] for row in dossier["source_artifacts"]
    } == SOURCE_EXCERPT_HASHES
    assert dossier["primary_source"]["source_archive_sha256"] == (
        "698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a"
    )
    assert dossier["primary_source"]["source_file_sha256"] == (
        "59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3"
    )
    correction = dossier["numbering_correction"]
    assert correction["source_locator_ids"] == ["S9N1", "S9N2"]
    assert "unnumbered" in correction["claim"].casefold()
    assert "not equation (28)" in correction["claim"].casefold()
    for locator in dossier["source_locators"].values():
        assert hashlib.sha256((PACKAGE / locator["path"]).read_bytes()).hexdigest() == locator[
            "sha256"
        ]
        assert locator["upstream_lines"]


def test_assumptions_have_exact_locators_and_do_not_invent_mass_positivity():
    assumptions = _json(PACKAGE / "assumptions.json")
    dossier = _json(PACKAGE / "source/dossier.json")
    locator_ids = set(dossier["source_locators"])
    predicate_ids = {row["predicate_id"] for row in assumptions["predicates"]}
    assert assumptions["status"] == "ASSUMPTION_COMPLETE"
    assert [row["status"] for row in assumptions["predicates"]] == [
        "DECLARED",
        "DECLARED",
        "DECLARED",
        "DERIVED",
    ]
    for predicate in assumptions["predicates"]:
        for reference in predicate["source"].split(" and "):
            assert reference in locator_ids | predicate_ids
    blob = json.dumps(assumptions).casefold()
    assert "positive relative masses" not in blob
    assert "does not add it" in blob


def test_strict_m1_and_all_three_grammar_arms_compile_exactly():
    loaded = load_case_package(PACKAGE)
    assert loaded.schema_deltas == ()
    for grammar_id in ("G_FULL", "G_NO_HERMITE", "G_PRIMITIVE"):
        program = (
            loaded.program
            if grammar_id == "G_FULL"
            else program_from_dict(
                _json(PACKAGE / "reference/ablations" / f"{grammar_id}.program.json")
            )
        )
        result = compile_program(
            program,
            CompileContext(
                PACKAGE.resolve(),
                loaded.context.symbols,
                loaded.context.functions,
                grammar_id=grammar_id,
            ),
        )
        assert result.status == "COMPILED"
        assert result.tautological is False
        assert len(result.obligations) == 4
        assert _json(PACKAGE / "reference/compilations" / f"{grammar_id}.json")[
            "compilation"
        ] == result.to_dict()
    primitive = _json(PACKAGE / "reference/ablations/G_PRIMITIVE.program.json")
    assert {row["operator"] for row in primitive["operators"]} == {
        "VALUE",
        "LINEAR_COMBINATION",
    }


def test_every_variant_obligation_has_hypothesis_then_exact_zero(report):
    receipts = report["sections"]["receipts"]
    assert receipts["status"] == "VALID"
    assert receipts["attempt_count"] == 12
    assert receipts["errors"] == []
    assert all(all(row["checks"].values()) for row in receipts["rows"])
    assert _json(PACKAGE / "reference/obligations.json")["summary"] == {
        "NONZERO": 0,
        "UNKNOWN": 0,
        "ZERO": 4,
    }


def test_duplicate_audit_isolates_rejected_predecessor_and_preserves_it(report):
    duplicate = report["sections"]["duplicate_and_leakage"]
    assert duplicate["status"] == "VALID"
    assert duplicate["renamed_matches"] == []
    assert set(duplicate["expected_repair_predecessor_matches"]) == {
        f"{PREDECESSOR}/members/G{index:04d}.txt" for index in range(1, 5)
    }
    assert duplicate["corpus_audit"]["findings"] == []
    assert duplicate["guo_references"]
    tree_hash, file_count = _tree_hash(ROOT / PREDECESSOR)
    assert tree_hash == PREDECESSOR_TREE_SHA256
    assert file_count == 33


def test_r6_negative_result_is_source_located_and_no_r6_package_was_forced(report):
    audit = report["r6_mining"]
    assert audit["status"] == "NO_DEFENSIBLE_R6_CANDIDATE"
    assert len(audit["screened_families"]) == 5
    assert all(row["decision"] == "REJECT_NO_PACKAGE" for row in audit["screened_families"])
    assert all(len(row["operator_types_required"]) >= 2 for row in audit["screened_families"])
    assert all(row["source"]["locator"] for row in audit["screened_families"])
    assert {
        path.name
        for path in COLLECTION.iterdir()
        if path.is_dir() and (path / "package.json").is_file()
    } == {PACKAGE_ID}


def test_one_shot_builder_refuses_to_overwrite_committed_evidence():
    with pytest.raises(FileExistsError, match="refusing to overwrite"):
        build()
