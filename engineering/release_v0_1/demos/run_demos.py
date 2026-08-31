#!/usr/bin/env python3
"""Replay the three v0.1 demos without mutating committed inputs.

The runner copies each workspace to a fresh execution root and calls only the
stable researcher Python API.  Its stdout deliberately omits runtime-dependent
paths and timings so the summary is deterministic and easy to compare in a
clean-room replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from symbolic_compactification import generate_report, load_workspace, verify_hypothesis

DEMO_ROOT = Path(__file__).resolve().parent
EXPECTED_RESULTS = {
    "demo_a_zero": "ZERO",
    "demo_b_grounded_newton_dd": "ZERO",
    "demo_c_unknown": "UNKNOWN",
}
FIXED_TIMESTAMP = "2026-08-31T00:00:00Z"
REQUIRED_PROVENANCE_FIELDS = frozenset({
    "timestamp",
    "package_version",
    "engine_version",
    "git_commit",
    "python_version",
    "dependency_versions",
    "input_hashes",
    "expression_hashes",
    "hypothesis_hash",
    "assumptions_hash",
    "verifier_route",
    "result",
    "runtime_seconds",
    "warnings",
})


def _source_snapshot(root: Path) -> dict[str, tuple[str, int, int]]:
    """Hash user-owned files and retain mode/mtime for mutation detection."""
    snapshot: dict[str, tuple[str, int, int]] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or "runs" in relative.parts:
            continue
        stat = path.stat()
        snapshot[relative.as_posix()] = (
            hashlib.sha256(path.read_bytes()).hexdigest(),
            stat.st_mode,
            stat.st_mtime_ns,
        )
    return snapshot


def _snapshot_digest(snapshot: dict[str, tuple[str, int, int]]) -> str:
    hashes_only = {
        name: values[0]
        for name, values in sorted(snapshot.items())
    }
    encoded = json.dumps(
        hashes_only, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def run_demo(name: str, execution_root: Path) -> dict[str, Any]:
    """Copy and replay one named demo, returning a stable public summary."""
    if name not in EXPECTED_RESULTS:
        raise ValueError(f"unknown demo: {name}")
    source = DEMO_ROOT / name
    destination = execution_root / name
    shutil.copytree(source, destination)

    before = _source_snapshot(destination)
    workspace = load_workspace(destination)
    verification = verify_hypothesis(
        workspace,
        run_id=f"{name}-run",
        timestamp=FIXED_TIMESTAMP,
    )
    report = generate_report(destination, verification)
    after = _source_snapshot(destination)
    provenance = json.loads(
        verification.provenance_path.read_text(encoding="utf-8")
    )

    expected = EXPECTED_RESULTS[name]
    obligation_results = [item.verdict for item in verification.obligations]
    summary = {
        "actual": verification.result,
        "expected": expected,
        "obligation_results": obligation_results,
        "provenance_complete": REQUIRED_PROVENANCE_FIELDS <= set(provenance),
        "report_generated": report.path.is_file() and report.result == expected,
        "run_id": verification.run_id,
        "source_files_unchanged": before == after,
        "source_snapshot_sha256": _snapshot_digest(before),
    }
    summary["passed"] = all((
        summary["actual"] == expected,
        summary["provenance_complete"],
        summary["report_generated"],
        summary["source_files_unchanged"],
    ))
    return summary


def run_all(execution_root: Path) -> dict[str, dict[str, Any]]:
    """Replay exactly the release demo inventory into a new directory."""
    execution_root = Path(execution_root)
    if execution_root.exists() or execution_root.is_symlink():
        raise FileExistsError(
            f"execution root already exists; refusing to overwrite: {execution_root}"
        )
    execution_root.mkdir(parents=True)
    return {
        name: run_demo(name, execution_root)
        for name in EXPECTED_RESULTS
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replay the v0.1 release demos from temporary copies of their "
            "committed researcher workspaces."
        )
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        help=(
            "retain copied workspaces and generated runs under this new path; "
            "the path must not already exist"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.output_root is not None:
        summaries = run_all(args.output_root)
    else:
        with tempfile.TemporaryDirectory(prefix="ssc-release-demos-") as temporary:
            summaries = run_all(Path(temporary) / "execution")
    print(json.dumps(summaries, sort_keys=True, indent=2))
    return 0 if all(item["passed"] for item in summaries.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
