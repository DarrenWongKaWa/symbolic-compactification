"""Evaluator-only adversarial controls for representation-program search."""

from __future__ import annotations

import json
from pathlib import Path

from research.representation_program_search.falsifier.adapter import (
    m1_failure_prefix,
    validate_adapter_program,
)
from research.representation_program_search.falsifier.validate import (
    ROOT,
    validate_suite,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def trap_rows() -> list[tuple[Path, dict]]:
    suite = load(ROOT / "suite.json")
    return [(ROOT / relative, load(ROOT / relative)) for relative in suite["traps"]]


def test_falsifier_suite_validates_with_frozen_verdict_totals() -> None:
    assert validate_suite() == {
        "trap_count": 6,
        "verdict_totals": {
            "COMPILE_FAILURE": 1,
            "NONZERO": 4,
            "PRE_VERIFICATION_INELIGIBLE": 2,
            "UNKNOWN": 0,
            "ZERO": 1,
        },
    }


def test_all_six_traps_are_evaluator_only_and_benchmark_ineligible() -> None:
    rows = trap_rows()
    assert len(rows) == 6
    assert len({trap["trap_id"] for _, trap in rows}) == 6
    assert all(trap["evaluator_only"] is True for _, trap in rows)
    assert all(trap["admissible_benchmark"] is False for _, trap in rows)


def test_exact_but_ineligible_traps_do_not_reach_verifier() -> None:
    rows = {trap["trap_id"]: (path.parent, trap) for path, trap in trap_rows()}
    for trap_id in (
        "tautological-member-memorization",
        "overcomplex-memorizing-master",
    ):
        case_dir, trap = rows[trap_id]
        assert not (case_dir / "verification").exists()
        for binding in trap["candidate_bindings"]:
            assert (case_dir / binding["current_path"]).read_bytes() == (
                case_dir / binding["candidate_path"]
            ).read_bytes()


def test_wrong_hermite_multiplicity_is_structural_compile_failure() -> None:
    case_dir = ROOT / "traps/wrong-hermite-multiplicity"
    program = load(case_dir / "evaluator/program.json")
    result = validate_adapter_program(program)
    assert result.valid is False
    assert result.failure_class == "HERMITE_NODE_MULTIPLICITY"
    assert m1_failure_prefix(result.failure_class) == ("HERMITE_REPEATED_NODE_REQUIRED")
    trap = load(case_dir / "trap.json")
    assert trap["m1_failure_prefix"] == m1_failure_prefix(result.failure_class)
    nodes = program["node_structures"][0]["nodes"]
    assert len(nodes) == len(set(nodes))
    assert not (case_dir / "verification").exists()


def test_false_equalities_retain_nonzero_residual_and_counterexample() -> None:
    nonzero_steps: list[dict] = []
    for trap_path, trap in trap_rows():
        if trap["evaluation_stage"] != "VERIFIER_NONZERO":
            continue
        case_dir = trap_path.parent
        for binding in trap["candidate_bindings"]:
            run_dir = case_dir / binding["run_path"]
            step_path = next((run_dir / "steps").glob("step_*.json"))
            step = load(step_path)
            nonzero_steps.append(step)
            assert step["verdict"] == "NONZERO"
            assert step["proof_status"] == "REFUTED"
            assert step["residual"] not in (None, "", "0")
            counterexamples = [
                row
                for row in step["evidence"]
                if row.get("kind") == "exact_counterexample"
            ]
            assert len(counterexamples) == 1
            assert counterexamples[0]["exact_value"] != "0"
            assert not (run_dir / "final/current.json").exists()
    assert len(nonzero_steps) == 4


def test_zero_exists_only_in_positive_control() -> None:
    trap_zeroes = []
    for trap_path, trap in trap_rows():
        case_dir = trap_path.parent
        for binding in trap["candidate_bindings"]:
            run_path = binding.get("run_path")
            if not run_path:
                continue
            for step_path in (case_dir / run_path / "steps").glob("step_*.json"):
                if load(step_path)["verdict"] == "ZERO":
                    trap_zeroes.append(step_path)
    assert trap_zeroes == []

    control = load(ROOT / "positive_control/control.json")
    run_dir = ROOT / "positive_control" / control["run_path"]
    step = load(next((run_dir / "steps").glob("step_*.json")))
    assert step["verdict"] == "ZERO"
    assert (run_dir / "final/FINAL_CERTIFIED_FORM.md").is_file()
