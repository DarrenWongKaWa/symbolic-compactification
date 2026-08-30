"""Deterministically validate the evaluator-only falsifier suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import sympy

from symbolic_compactification import load_expression, parse_expression

from .adapter import (
    m1_failure_prefix,
    validate_action_sequence,
    validate_adapter_program,
)

ROOT = Path(__file__).resolve().parent
SUITE_PATH = ROOT / "suite.json"
TRAP_SCHEMA = "RPSFalsifierTrapV1"
PROGRAM_SCHEMA = "RepresentationProgramAdapterV1"
EXPECTED_TRAPS = {
    "attractive-wrong-basis": ("VERIFIER_NONZERO", "WRONG_BASIS"),
    "false-recurrence": ("VERIFIER_NONZERO", "FALSE_RECURRENCE"),
    "near-correct-divided-difference": (
        "VERIFIER_NONZERO",
        "NEAR_CORRECT_DD",
    ),
    "overcomplex-memorizing-master": (
        "PRE_VERIFICATION_INELIGIBLE",
        "DOMINATED_STATE",
    ),
    "tautological-member-memorization": (
        "PRE_VERIFICATION_INELIGIBLE",
        "TAUTOLOGICAL_PROGRAM",
    ),
    "wrong-hermite-multiplicity": (
        "COMPILE_FAILURE",
        "HERMITE_NODE_MULTIPLICITY",
    ),
}


class FalsifierValidationError(ValueError):
    """A fail-closed fixture or evidence violation."""


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FalsifierValidationError(f"unreadable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise FalsifierValidationError(f"JSON object required: {path}")
    return value


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(_canonical_bytes(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _fixture_json_paths() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*.json"))
        if "verification" not in path.parts and path != SUITE_PATH
    ]


def _artifact_paths() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*"))
        if path.is_file()
        and path != SUITE_PATH
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and not path.name.startswith(".")
    ]


def materialize_suite() -> None:
    """Set canonical program ids, canonicalize fixtures, and bind artifacts."""
    for path in _fixture_json_paths():
        payload = _load_json(path)
        if payload.get("schema_version") == PROGRAM_SCHEMA:
            unhashed = dict(payload)
            unhashed.pop("program_id", None)
            payload["program_id"] = _canonical_hash(unhashed)
        _atomic_json(path, payload)

    suite = _load_json(SUITE_PATH)
    suite["artifacts"] = {
        path.relative_to(ROOT).as_posix(): _file_hash(path)
        for path in _artifact_paths()
    }
    _atomic_json(SUITE_PATH, suite)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise FalsifierValidationError(message)


def _symbols(case_dir: Path) -> list[Any]:
    payload = _load_json(case_dir / "symbols.json")
    value = payload.get("symbols")
    _assert(isinstance(value, list) and value, f"missing symbols: {case_dir}")
    return value


def _parse_case_expressions(case_dir: Path, trap: dict[str, Any]) -> None:
    symbols = _symbols(case_dir)
    paths = list(trap["source_member_files"])
    paths.extend(row["candidate_path"] for row in trap["candidate_bindings"])
    for relative in paths:
        load_expression(case_dir / relative, symbols)


def _program_id_valid(program: dict[str, Any]) -> bool:
    unhashed = dict(program)
    program_id = unhashed.pop("program_id", None)
    return isinstance(program_id, str) and program_id == _canonical_hash(unhashed)


def _program_complexity(program: dict[str, Any], symbols: list[Any]) -> int:
    latents = program["latent_objects"]
    operators = program["operators"]
    parameters: set[str] = set()
    symbol_names = {item if isinstance(item, str) else item["name"] for item in symbols}
    latent_ops = 0
    for latent in latents:
        bound = list(latent.get("parameters", []))
        parameters.update(bound)
        declarations = list(symbols)
        declarations.extend(name for name in bound if name not in symbol_names)
        parsed = parse_expression(latent["symbolic_core"], declarations)
        latent_ops += int(sympy.count_ops(parsed, visual=False))
    max_depth = max((int(op.get("operator_depth", 1)) for op in operators), default=0)
    exceptions = len(program.get("member_specific_exceptions", []))
    reconstruction_ops = len(program["reconstruction"])
    return (
        len(latents)
        + len(operators)
        + max_depth
        + len(parameters)
        + exceptions
        + math.ceil(latent_ops / 8)
        + reconstruction_ops
    )


def _validate_tautology(
    case_dir: Path, program: dict[str, Any], trap: dict[str, Any]
) -> None:
    _assert(validate_adapter_program(program).valid, "tautology must be well typed")
    operators = {op["operator_id"]: op for op in program["operators"]}
    assignments = program["member_assignments"]
    used_latents: list[str] = []
    cores = {
        row["latent_id"]: row["symbolic_core"].strip()
        for row in program["latent_objects"]
    }
    for binding in trap["candidate_bindings"]:
        member = binding["member_id"]
        op = operators[assignments[member]]
        _assert(op["operator"] == "VALUE", "tautology must use VALUE-self maps")
        used_latents.append(op["latent"])
        current = (case_dir / binding["current_path"]).read_bytes()
        candidate = (case_dir / binding["candidate_path"]).read_bytes()
        _assert(current == candidate, "tautology exactness must be byte-identical")
        _assert(
            cores[op["latent"]] == current.decode().strip(),
            "latent must memorize member",
        )
    _assert(len(set(used_latents)) == len(assignments), "latents unexpectedly reused")


def _validate_dominated(
    case_dir: Path, program: dict[str, Any], trap: dict[str, Any]
) -> None:
    _assert(
        validate_adapter_program(program).valid, "memorizing master must be well typed"
    )
    witness = _load_json(case_dir / trap["dominance_witness_path"])
    _assert(_program_id_valid(witness), "invalid dominance-witness program_id")
    _assert(validate_adapter_program(witness).valid, "dominance witness is ill typed")
    for binding in trap["candidate_bindings"]:
        _assert(
            (case_dir / binding["current_path"]).read_bytes()
            == (case_dir / binding["candidate_path"]).read_bytes(),
            "dominated exactness must be byte-identical",
        )
    _assert(
        set(program["member_assignments"]) == set(witness["member_assignments"]),
        "dominance witness coverage differs",
    )
    symbols = _symbols(case_dir)
    candidate_cost = _program_complexity(program, symbols)
    witness_cost = _program_complexity(witness, symbols)
    _assert(
        witness_cost < candidate_cost, "memorizing master is not strictly dominated"
    )


def _load_only_step(case_dir: Path, binding: dict[str, Any]) -> tuple[dict, dict]:
    run_dir = case_dir / binding["run_path"]
    manifest = _load_json(run_dir / "manifest.json")
    steps = sorted((run_dir / "steps").glob("step_*.json"))
    _assert(len(steps) == 1, f"expected one recorded step: {run_dir}")
    return manifest, _load_json(steps[0])


def _validate_nonzero(case_dir: Path, trap: dict[str, Any]) -> int:
    count = 0
    for binding in trap["candidate_bindings"]:
        manifest, step = _load_only_step(case_dir, binding)
        current_path = case_dir / binding["current_path"]
        candidate_path = case_dir / binding["candidate_path"]
        _assert(step.get("verdict") == "NONZERO", "trap did not return NONZERO")
        _assert(step.get("status") == "UNVERIFIED", "NONZERO trap was certified")
        _assert(step.get("proof_status") == "REFUTED", "NONZERO trap not REFUTED")
        _assert(step.get("assumption_status") == "DECLARED", "assumptions changed")
        _assert(
            step.get("current_hash") == _file_hash(current_path), "current hash drift"
        )
        _assert(
            step.get("candidate_hash") == _file_hash(candidate_path),
            "candidate hash drift",
        )
        _assert(step.get("residual") not in (None, "", "0"), "missing exact residual")
        evidence = step.get("evidence", [])
        counterexamples = [
            row for row in evidence if row.get("kind") == "exact_counterexample"
        ]
        _assert(len(counterexamples) == 1, "missing exact counterexample")
        _assert(
            counterexamples[0].get("exact_value") not in (None, "", "0"),
            "zero counterexample",
        )
        _assert(
            manifest.get("current", {}).get("sha256") == _file_hash(current_path),
            "manifest drift",
        )
        _assert(
            not (case_dir / binding["run_path"] / "final/current.json").exists(),
            "trap promoted",
        )
        count += 1
    return count


def _validate_positive_control(relative: str) -> int:
    control_path = ROOT / relative
    case_dir = control_path.parent
    control = _load_json(control_path)
    symbols = _symbols(case_dir)
    load_expression(case_dir / control["current_path"], symbols)
    load_expression(case_dir / control["candidate_path"], symbols)
    binding = {
        "current_path": control["current_path"],
        "candidate_path": control["candidate_path"],
        "run_path": control["run_path"],
    }
    _, step = _load_only_step(case_dir, binding)
    _assert(control.get("is_trap") is False, "positive control marked as trap")
    _assert(step.get("verdict") == "ZERO", "positive control did not return ZERO")
    _assert(step.get("status") == "CERTIFIED", "positive control not certified")
    _assert(step.get("proof_status") == "PROVEN", "positive control not PROVEN")
    _assert(
        step.get("current_hash") == _file_hash(case_dir / control["current_path"]),
        "control current drift",
    )
    _assert(
        step.get("candidate_hash") == _file_hash(case_dir / control["candidate_path"]),
        "control candidate drift",
    )
    final_dir = case_dir / control["run_path"] / "final"
    _assert((final_dir / "current.json").is_file(), "positive control was not promoted")
    _assert(
        (final_dir / "FINAL_CERTIFIED_FORM.md").is_file(), "positive report missing"
    )
    return 1


def validate_suite() -> dict[str, Any]:
    """Return counts when every frozen control and evidence receipt is valid."""
    suite = _load_json(SUITE_PATH)
    _assert(suite.get("schema_version") == "RPSFalsifierSuiteV1", "suite schema")
    _assert(suite.get("version") == "1.0.0", "suite version")
    trap_paths = suite.get("traps")
    _assert(isinstance(trap_paths, list) and len(trap_paths) == 6, "trap count")

    seen: set[str] = set()
    counts = {
        "COMPILE_FAILURE": 0,
        "NONZERO": 0,
        "PRE_VERIFICATION_INELIGIBLE": 0,
        "UNKNOWN": 0,
        "ZERO": 0,
    }
    for relative in trap_paths:
        trap_path = ROOT / relative
        case_dir = trap_path.parent
        trap = _load_json(trap_path)
        trap_id = trap.get("trap_id")
        _assert(trap.get("schema_version") == TRAP_SCHEMA, f"trap schema: {trap_id}")
        _assert(
            trap_id in EXPECTED_TRAPS and trap_id not in seen, f"trap id: {trap_id}"
        )
        seen.add(trap_id)
        expected_stage, expected_class = EXPECTED_TRAPS[trap_id]
        _assert(trap.get("evaluation_stage") == expected_stage, f"stage: {trap_id}")
        _assert(
            trap.get("expected_failure_class") == expected_class, f"class: {trap_id}"
        )
        _assert(trap.get("evaluator_only") is True, f"not evaluator-only: {trap_id}")
        _assert(trap.get("admissible_benchmark") is False, f"admitted trap: {trap_id}")

        assumptions = _load_json(case_dir / "assumptions.json")
        _assert(assumptions.get("status") == "DECLARED", f"assumptions: {trap_id}")
        _assert(
            all(
                row.get("label") == "DECLARED"
                for row in assumptions.get("predicates", [])
            ),
            f"undeclared predicate: {trap_id}",
        )
        _parse_case_expressions(case_dir, trap)
        program = _load_json(case_dir / trap["program_path"])
        _assert(
            program.get("schema_version") == PROGRAM_SCHEMA,
            f"program schema: {trap_id}",
        )
        _assert(_program_id_valid(program), f"program_id: {trap_id}")
        actions = _load_json(case_dir / "evaluator/actions.json")
        _assert(
            validate_action_sequence(actions).valid, f"action vocabulary: {trap_id}"
        )

        adapter = validate_adapter_program(program)
        if expected_stage == "COMPILE_FAILURE":
            _assert(not adapter.valid, f"ill-typed trap compiled: {trap_id}")
            _assert(
                adapter.failure_class == expected_class, f"compile class: {trap_id}"
            )
            _assert(
                trap.get("m1_failure_prefix") == m1_failure_prefix(expected_class),
                f"M1 failure mapping: {trap_id}",
            )
            _assert(
                not (case_dir / "verification").exists(),
                f"compile trap reached verifier: {trap_id}",
            )
            counts["COMPILE_FAILURE"] += 1
        elif expected_stage == "PRE_VERIFICATION_INELIGIBLE":
            _assert(adapter.valid, f"eligibility trap ill typed: {trap_id}")
            _assert(
                not (case_dir / "verification").exists(),
                f"ineligible trap reached verifier: {trap_id}",
            )
            if expected_class == "TAUTOLOGICAL_PROGRAM":
                _validate_tautology(case_dir, program, trap)
            else:
                _validate_dominated(case_dir, program, trap)
            counts["PRE_VERIFICATION_INELIGIBLE"] += 1
        else:
            _assert(adapter.valid, f"NONZERO trap ill typed: {trap_id}")
            counts["NONZERO"] += _validate_nonzero(case_dir, trap)

    _assert(seen == set(EXPECTED_TRAPS), "missing trap")
    counts["ZERO"] = _validate_positive_control(suite["positive_control"])
    _assert(counts == suite.get("verdict_totals"), "verdict totals drift")

    expected_artifacts = suite.get("artifacts")
    actual_artifacts = {
        path.relative_to(ROOT).as_posix(): _file_hash(path)
        for path in _artifact_paths()
    }
    _assert(expected_artifacts == actual_artifacts, "artifact manifest drift")
    for path in [SUITE_PATH, *_fixture_json_paths()]:
        _assert(
            path.read_bytes() == _canonical_bytes(_load_json(path)),
            f"noncanonical JSON: {path}",
        )
    return {"trap_count": len(seen), "verdict_totals": counts}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialize", action="store_true")
    args = parser.parse_args(argv)
    if args.materialize:
        materialize_suite()
    print(json.dumps(validate_suite(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
