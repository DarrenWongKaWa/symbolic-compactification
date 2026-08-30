"""One-shot builder for recorded negative R4/R5 mining diagnostics.

These runs are not case packages and cannot be admitted.  They record the
exact verifier consequences of the two strongest real-domain screens and the
only frozen-parser special-function family with non-elementary semantics.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from symbolic_compactification import (
    adjudicate_candidate,
    init_session,
    load_expression,
    record_proposal,
    set_current,
)


ROOT = Path(__file__).resolve().parent
DIAGNOSTICS = ROOT / "diagnostics"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> None:
    if DIAGNOSTICS.exists():
        raise RuntimeError(f"REFUSE_EXISTING_DIAGNOSTICS:{DIAGNOSTICS}")
    specs = (
        {
            "candidate": "(-log(x)+log(y))/(-x+y)",
            "current": "(log(x)-log(y))/(x-y)",
            "diagnostic_id": "D001",
            "expected": "ZERO",
            "note": "Parser-feasible first divided-difference lowering; rejected as a direct old-TEST instantiation.",
            "symbols": [
                {"name": "x", "nonzero": True, "real": True},
                {"name": "y", "nonzero": True, "real": True},
            ],
        },
        {
            "candidate": "((log(y)+1)-((y*log(y)-x*log(x))/(y-x)))/(y-x)",
            "current": "(x*log(x/y)-(x-y))/(x-y)**2",
            "diagnostic_id": "D002",
            "expected": "NONZERO",
            "note": "The source declares positive eigenvalues, but positivity is unavailable in the frozen namespace; the required log quotient lowering is refuted on the broader real probe domain.",
            "symbols": [
                {"name": "x", "nonzero": True, "real": True},
                {"name": "y", "nonzero": True, "real": True},
            ],
        },
        {
            "candidate": "1/x",
            "current": "polygamma(0,x+1)-polygamma(0,x)",
            "diagnostic_id": "D003",
            "expected": "UNKNOWN",
            "note": "The only admitted non-elementary family does not certify its symbolic recurrence under the frozen verifier.",
            "symbols": [{"name": "x", "nonzero": True, "real": True}],
        },
        {
            "candidate": "((log(y)+1)-((y*log(y)-x*log(x))/(y-x)))/(y-x)",
            "current": "(x*(log(x)-log(y))-(x-y))/(x-y)**2",
            "diagnostic_id": "D004",
            "expected": "ZERO",
            "note": "After an external positive-domain log lowering, the proposed structure is exactly the historical Hermite-two template instantiated with F(z)=z*log(z); this diagnostic is not source-member certification.",
            "symbols": [
                {"name": "x", "nonzero": True, "real": True},
                {"name": "y", "nonzero": True, "real": True},
            ],
        },
    )
    workspace = DIAGNOSTICS / "verification" / "workspace"
    attempts: list[dict[str, Any]] = []
    for spec in specs:
        diagnostic_id = spec["diagnostic_id"]
        current_path = DIAGNOSTICS / "expressions" / f"{diagnostic_id}.current.txt"
        candidate_path = DIAGNOSTICS / "expressions" / f"{diagnostic_id}.candidate.txt"
        symbols_path = DIAGNOSTICS / "symbols" / f"{diagnostic_id}.json"
        _write_text(current_path, spec["current"])
        _write_text(candidate_path, spec["candidate"])
        _write_json(symbols_path, {"functions": [], "symbols": spec["symbols"]})
        current = load_expression(current_path, spec["symbols"])
        candidate = load_expression(candidate_path, spec["symbols"])
        session = init_session(
            str(workspace),
            meta={
                "diagnostic_id": diagnostic_id,
                "scope": "R4_R5_NEGATIVE_MINING_DIAGNOSTIC_ONLY",
            },
            requested_proposer_mode="main",
        )
        set_current(session, current)
        record_proposal(
            session,
            {
                "assumptions_status": "DECLARED",
                "candidate_expression_or_rewrite": candidate.text,
                "candidate_id": f"r4-r5-negative-{diagnostic_id}",
                "confidence": "low",
                "expected_structural_benefit": spec["note"],
                "hypothesis": "The exact verifier outcome determines package eligibility; it does not admit this rejected mining lead.",
                "rationale": spec["note"],
                "required_assumptions": ["source ledger and frozen symbol namespace"],
                "status": "HYPOTHESIS",
                "suggested_verification_strategy": "Run the exact verifier on the hash-bound diagnostic files.",
            },
        )
        outcome = adjudicate_candidate(
            session,
            candidate,
            meta={"diagnostic_id": diagnostic_id, "scope": "MINING_ONLY"},
        )
        if outcome.result.verdict != spec["expected"]:
            raise RuntimeError(
                f"UNEXPECTED_VERDICT:{diagnostic_id}:{outcome.result.verdict}"
            )
        attempts.append(
            {
                "candidate_path": candidate_path.relative_to(DIAGNOSTICS).as_posix(),
                "candidate_sha256": _sha(candidate_path),
                "current_path": current_path.relative_to(DIAGNOSTICS).as_posix(),
                "current_sha256": _sha(current_path),
                "diagnostic_id": diagnostic_id,
                "expected_verdict": spec["expected"],
                "note": spec["note"],
                "proposal_step": 1,
                "run_id": session.run_id,
                "symbols_path": symbols_path.relative_to(DIAGNOSTICS).as_posix(),
                "symbols_sha256": _sha(symbols_path),
                "verification_step": 2,
            }
        )
    _write_json(
        DIAGNOSTICS / "index.json",
        {
            "admission_effect": "NONE",
            "attempts": attempts,
            "schema_version": "RPSR4R5NegativeDiagnosticIndexV1",
        },
    )


if __name__ == "__main__":
    build()
