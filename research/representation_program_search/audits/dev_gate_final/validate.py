"""Fail-closed validator for the final independent DEV gate audit."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
AUDIT_ROOT = Path(__file__).resolve().parent


def validate() -> dict[str, object]:
    payload = json.loads((AUDIT_ROOT / "GATE_AUDIT.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    if payload.get("schema_version") != "RPSDevGateFinalV1":
        errors.append("SCHEMA_INVALID")
    if payload.get("decision") != "GATE_BLOCKED":
        errors.append("DECISION_INVALID")
    expected_slots = {
        "NEGATIVE_TRAP": "MISSING",
        "R2": "READY",
        "R3": "MISSING",
        "R4_R5": "MISSING",
        "R6": "MISSING",
    }
    slots = payload.get("required_slots", {})
    if {key: slots.get(key, {}).get("status") for key in expected_slots} != expected_slots:
        errors.append("SLOT_STATUS_INVALID")
    for row in payload.get("evidence", []):
        path = ROOT / row["path"]
        if not path.is_file():
            errors.append(f"EVIDENCE_MISSING:{row['path']}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != row["sha256"]:
            errors.append(f"EVIDENCE_DRIFT:{row['path']}")
    forbidden_artifacts = (
        ROOT / "research/representation_program_search/final/FREEZE_MANIFEST.json",
        ROOT / "research/representation_program_search/DEV_MANIFEST.json",
        ROOT / "research/representation_program_search/TEST_MANIFEST.json",
    )
    if any(path.exists() for path in forbidden_artifacts):
        errors.append("POST_GATE_SCIENTIFIC_ARTIFACT_PRESENT")
    return {
        "decision": payload.get("decision"),
        "errors": errors,
        "status": "VALID" if not errors else "INVALID",
    }


if __name__ == "__main__":
    print(json.dumps(validate(), indent=2, sort_keys=True))
