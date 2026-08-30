from __future__ import annotations

import hashlib
import json
from pathlib import Path

from research.representation_program_search.evaluation import load_clearance_receipt
from research.representation_program_search.search import load_public_case


ROOT = Path(__file__).resolve().parents[1]
RPS = ROOT / "research/representation_program_search"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_c9h4_clearance_is_bound_to_the_independent_combined_audit():
    package = RPS / "recovery/gap_recovery/rps-candidate-k9-001"
    case = load_public_case(package / "proposer_view.json")
    clearance_path = RPS / "evaluation/clearances/C9H4.json"
    clearance = load_clearance_receipt(
        clearance_path,
        _sha256(clearance_path),
        case_id=case.case_id,
        proposer_view_sha256=case.proposer_view_sha256,
    )
    audit_path = (
        RPS
        / "audits/gap_recovery_admission/"
        "INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json"
    )
    audit_sha = _sha256(audit_path)
    assert clearance["admission_audit_sha256"] == audit_sha
    assert clearance["assumption_audit_sha256"] == audit_sha
    assert clearance["leakage_audit_sha256"] == audit_sha
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    assert audit["decision"] == "ADMISSION_READY"
    assert audit["admission_scope"] == "DEV_R2_CALIBRATION_ONLY"
    assert audit["sections"]["assumptions_and_public_boundary"]["status"] == "PASS"
