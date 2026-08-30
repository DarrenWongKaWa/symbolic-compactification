from __future__ import annotations

from research.representation_program_search.audits.dev_gate_final.validate import (
    validate,
)


def test_final_dev_gate_is_hash_bound_and_blocked():
    assert validate() == {
        "decision": "GATE_BLOCKED",
        "errors": [],
        "status": "VALID",
    }
