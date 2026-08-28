"""Track V2 family certificate contract."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.freeze_v2 import OUT, build
from research.multibranch_verification.schema import (
    FAMILY_NONZERO,
    FAMILY_UNKNOWN,
    FAMILY_ZERO,
    compose_family_verdict,
)


def test_freeze_has_seven_multibranch_or_hermite_hyps():
    blob = build()
    assert blob["n_hypotheses"] == 7
    assert blob["no_llm_calls"] is True
    types = {h["claimed_type"] for h in blob["hypotheses"]}
    assert "local_confluence" in types
    assert "hermite_divided_difference" in types
    assert all(h["n_members"] >= 4 or h["claimed_type"] == "hermite_divided_difference"
               for h in blob["hypotheses"])


def test_compose_majority_is_not_zero():
    # 4 ZERO + 1 UNKNOWN must not be FAMILY_ZERO
    assert compose_family_verdict(
        required_edge_verdicts=["ZERO", "ZERO", "ZERO", "ZERO", "UNKNOWN"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=True,
        multiplicities_consistent=True,
    ) == FAMILY_UNKNOWN


def test_compose_any_nonzero_is_family_nonzero():
    assert compose_family_verdict(
        required_edge_verdicts=["ZERO", "NONZERO"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=True,
        multiplicities_consistent=True,
    ) == FAMILY_NONZERO


def test_compose_all_zero_connected_is_family_zero():
    assert compose_family_verdict(
        required_edge_verdicts=["ZERO", "ZERO"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=True,
        multiplicities_consistent=True,
    ) == FAMILY_ZERO


def test_disconnected_is_unknown_not_zero():
    assert compose_family_verdict(
        required_edge_verdicts=["ZERO", "ZERO"],
        recurrence_verdicts=["ZERO"],
        path_verdicts=["ZERO"],
        connected=False,
        multiplicities_consistent=True,
    ) == FAMILY_UNKNOWN


def test_manifest_file_if_present_matches_builder():
    if OUT.is_file():
        disk = json.loads(OUT.read_text())
        assert disk["n_hypotheses"] == build()["n_hypotheses"]
