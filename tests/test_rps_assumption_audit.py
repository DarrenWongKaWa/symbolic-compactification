"""Focused tests for the representation-search assumption audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.representation_program_search.audits.assumptions.audit import (
    ARTIFACT_PATH,
    CASE_CLUSTERS,
    PREDICATE_FIELDS,
    PREDICATE_STATUSES,
    build_audit,
    case_paths,
    render_artifact,
)


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_UNDERSPECIFIED = {
    "thermal-10-polygamma-recurrence",
    "rps-r-birman-schwinger-kernel",
    "rps-r-fano-beutler-profile",
    "rps-r-lorentz-causal-poles",
    "rps-r-schrieffer-wolff-denom",
    "rps-r-weyl-titchmarsh-m",
    "rps-dp-dexpinv-bernoulli",
    "rps-dp-liouville-jacobi-cnf",
    "rps-dp-stm-sensitivity-kernel",
}


def _case_map(audit: dict) -> dict[str, dict]:
    return {case["case_id"]: case for case in audit["cases"]}


def test_scope_is_every_non_skeptic_case_and_only_those_cases():
    paths = case_paths()
    assert len(paths) == 39
    assert {path.parent.name for path in paths} == set(CASE_CLUSTERS)
    assert all("skeptic" not in path.parts for path in paths)
    assert all(path.name != "index.json" for path in paths)


def test_committed_artifact_is_canonical_and_reproducible():
    built = build_audit()
    assert ARTIFACT_PATH.read_bytes() == render_artifact(built)
    committed = json.loads(ARTIFACT_PATH.read_text(encoding="utf-8"))
    assert committed == built


def test_dossier_hashes_bind_every_audited_input():
    audit = build_audit()
    for case in audit["cases"]:
        path = ROOT / case["dossier_path"]
        assert path.is_file()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == case["dossier_sha256"]


def test_every_contract_entry_has_exactly_one_audit_record():
    audit = build_audit()
    for case in audit["cases"]:
        dossier = json.loads((ROOT / case["dossier_path"]).read_text(encoding="utf-8"))
        contract = dossier["assumption_contract"]
        expected = (
            len(contract["symbol_assumptions"])
            + len(contract["function_domains"])
            + len(contract.get("real_valued_functions") or [])
            + len(contract.get("branch_conventions") or [])
            + sum(len(contract.get(field) or []) for field in PREDICATE_FIELDS)
        )
        explicit = [
            record
            for record in case["predicates"]
            if record["origin"] == "CONTRACT_EXPLICIT"
        ]
        assert len(explicit) == expected, case["case_id"]
        assert len({record["predicate_id"] for record in case["predicates"]}) == len(
            case["predicates"]
        )


def test_statuses_and_fail_closed_outcomes_are_total():
    audit = build_audit()
    for case in audit["cases"]:
        statuses = [record["audit_status"] for record in case["predicates"]]
        assert statuses
        assert set(statuses) <= set(PREDICATE_STATUSES)
        has_gap = "NOT_DECLARED" in statuses
        assert (case["audit_outcome"] == "PROBLEM_UNDERSPECIFIED") is has_gap
        assert (
            case["downstream_gate"] == "EXCLUDE_UNTIL_ASSUMPTIONS_DECLARED"
        ) is has_gap


def test_expected_source_backed_gaps_are_reported_without_repair():
    audit = build_audit()
    cases = _case_map(audit)
    observed = {
        case_id
        for case_id, case in cases.items()
        if case["audit_outcome"] == "PROBLEM_UNDERSPECIFIED"
    }
    assert observed == EXPECTED_UNDERSPECIFIED
    assert audit["summary"]["problem_underspecified_count"] == 9
    assert audit["summary"]["assumption_complete_count"] == 30
    for case_id in observed:
        gaps = [
            record
            for record in cases[case_id]["predicates"]
            if record["audit_status"] == "NOT_DECLARED"
        ]
        assert gaps
        for gap in gaps:
            assert gap.get("audit_reason")
            assert gap.get("source_basis")
            assert gap["dossier_status"] in {"ABSENT", "DECLARED", "DERIVED"}


def test_thermal_pole_exclusion_is_reclassified_fail_closed():
    case = _case_map(build_audit())["thermal-10-polygamma-recurrence"]
    predicate = next(
        record
        for record in case["predicates"]
        if record["predicate_id"] == "analytic_domains:0"
    )
    assert predicate["dossier_status"] == "DERIVED"
    assert predicate["audit_status"] == "NOT_DECLARED"
    assert "z != 0" in predicate["audit_reason"]


def test_audit_does_not_mutate_dossier_rejection_state_or_select_partitions():
    audit = build_audit()
    assert all(case["dossier_rejected"] is False for case in audit["cases"])
    rendered = render_artifact(audit).decode("utf-8")
    assert '"selected_partition"' not in rendered
    assert '"DEV"' not in rendered
    assert '"TEST"' not in rendered
