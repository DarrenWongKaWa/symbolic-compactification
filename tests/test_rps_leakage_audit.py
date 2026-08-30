from __future__ import annotations

from pathlib import Path

from research.representation_program_search.audits.leakage.audit import (
    EXACT_DUPLICATE,
    FIRST_ORDER_LGG_ONLY,
    GRAMMAR_SYNTAX,
    HIDDEN_MEMBER_ROLE,
    HISTORICAL_ID,
    RENAMED_DUPLICATE,
    SEALED_GUO,
    TRIVIAL_CSE,
    CorpusDocument,
    alpha_normalize,
    audit_case,
    audit_repository,
    discover_reference_corpus,
    is_trivial_cse,
)


ROOT = Path(__file__).resolve().parents[1]


def _reference(expression: str = "(f(x)-f(y))/(x-y)") -> CorpusDocument:
    return CorpusDocument(
        document_id="old-case",
        path="research/old/bench/old-case.json",
        partition="PREVIOUS_BENCHMARK",
        title="Old quotient",
        formulas=(expression,),
        identity_text="Old quotient\n" + expression,
        source_ids=(),
    )


def _payload(expression: str) -> dict:
    return {
        "case_id": "new-case",
        "title": "Unlabeled source",
        "expression_sketch": expression,
        "proposed_ladder": "R3_hermite_dd",
        "rejected": False,
        "is_guo": False,
    }


def _codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def test_alpha_normalization_is_symbol_rename_invariant():
    assert alpha_normalize("(f(x)-f(y))/(x-y)") == alpha_normalize(
        "(f(a)-f(b))/(a-b)"
    )


def test_exact_and_renamed_duplicates_are_review_only():
    exact = audit_case(_payload("(f(x)-f(y))/(x-y)"), [_reference()], ())
    assert EXACT_DUPLICATE in _codes(exact)
    renamed = audit_case(_payload("(f(a)-f(b))/(a-b)"), [_reference()], ())
    assert RENAMED_DUPLICATE in _codes(renamed)
    for report in (exact, renamed):
        assert report["admission_decision"] is None
        assert all(not finding["auto_reject"] for finding in report["findings"])


def test_literal_grammar_syntax_and_member_roles_are_detected():
    payload = _payload("raw members")
    payload["proposer_view"] = {
        "catalog": [{"id": "G0001", "text": "f(x)", "role": "target_expression"}],
        "instruction": "Apply HERMITE_DD(F, NODES[x,x,y])",
    }
    report = audit_case(payload, [], ())
    assert GRAMMAR_SYNTAX in _codes(report)
    assert HIDDEN_MEMBER_ROLE in _codes(report)


def test_trivial_cse_and_first_order_lgg_controls():
    assert is_trivial_cse("Add(chi0, chi0)")
    payload = _payload("Add(chi0, chi0)")
    payload["proposed_ladder"] = "R1_parameterized_family"
    report = audit_case(payload, [], ())
    assert {TRIVIAL_CSE, FIRST_ORDER_LGG_ONLY} <= _codes(report)


def test_long_scientific_sketch_is_not_misread_as_one_cse():
    sketch = (
        "Let K be a matrix with K**2 = -I. For theta != 0, "
        "R = I + sin(theta)*K + (1-cos(theta))*K**2. "
        "With a separate member J = I + a*K + b*K**2, compare the family."
    )
    assert not is_trivial_cse(sketch)


def test_guo_requires_name_or_sealed_hop_pair():
    ordinary = _payload("Catalog member G0013 is an ordinary local identifier")
    ordinary["notes"] = "Not Guo; distinct from historical mp-resolvent-dd-01."
    ordinary["is_guo"] = False
    assert SEALED_GUO not in _codes(audit_case(ordinary, [], ()))
    sealed = _payload("historical control G0016 -> G0013")
    assert SEALED_GUO in _codes(audit_case(sealed, [], ()))


def test_explicit_proposer_view_isolates_audit_only_metadata():
    payload = _payload("The audit-only dossier names HERMITE_DD and NODES[x,x]")
    payload["title"] = "Audit-only Hermite title"
    payload["notes"] = "Not Guo; distinct from mp-hermite-fA-01."
    payload["proposer_view"] = {"catalog": [{"id": "G0001", "text": "f(x)"}]}
    codes = _codes(audit_case(payload, [], ("mp-hermite-fA-01",)))
    assert GRAMMAR_SYNTAX not in codes
    assert HISTORICAL_ID not in codes
    assert SEALED_GUO not in codes


def test_reference_corpus_covers_ac_and_previous_benchmarks_without_current_line():
    docs = discover_reference_corpus(ROOT)
    ids = {doc.document_id for doc in docs}
    assert "mp-resolvent-dd-01" in ids
    assert "dev-a-newton-first" in ids
    assert all("representation_program_search" not in doc.path for doc in docs)


def test_full_audit_is_deterministic_and_calibrates_controls():
    first = audit_repository(ROOT)
    second = audit_repository(ROOT)
    assert first == second
    assert first["gold_fields_used"] is False
    assert first["auto_rejects_similarity"] is False
    by_id = {case["case_id"]: case for case in first["cases"]}
    assert TRIVIAL_CSE in _codes(by_id["nc-trivial-cse"])
    assert FIRST_ORDER_LGG_ONLY in _codes(by_id["nc-first-order-lgg"])
    assert GRAMMAR_SYNTAX in _codes(by_id["nc-leaked-hermite-sketch"])
    assert SEALED_GUO in _codes(by_id["nc-guo-sigma-abc"])
