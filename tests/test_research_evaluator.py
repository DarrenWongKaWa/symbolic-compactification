"""Evaluator contracts: no leakage, UNKNOWN is not success."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.metrics.evaluator import (  # noqa: E402
    adjudicate_item,
    assert_no_leakage,
    proposer_view,
)


def test_proposer_view_strips_hidden_fields():
    item = {
        "id": "A-demo",
        "tier": "A",
        "family": "polynomial",
        "task": "adjudicate",
        "current": "(x+1)**2",
        "candidate": "x**2 + 2*x + 1",
        "symbols": [{"name": "x", "real": True, "nonzero": False}],
        "functions": [],
        "expected_verdict": "ZERO",
        "human_reference": "SECRET",
        "target_compact": "SECRET2",
        "mutation_type": None,
        "hidden_from_proposer": True,
    }
    view = proposer_view(item)
    assert "human_reference" not in view
    assert "target_compact" not in view
    assert "expected_verdict" not in view
    assert view["current"] == item["current"]
    assert_no_leakage(view)
    with pytest.raises(RuntimeError):
        assert_no_leakage(item)


def test_adjudicate_identity_and_corruption():
    ident = {
        "id": "A-demo-id",
        "current": "(x+1)**2",
        "candidate": "x**2 + 2*x + 1",
        "symbols": [{"name": "x", "real": True, "nonzero": False}],
        "functions": [],
        "expected_verdict": "ZERO",
    }
    rec = adjudicate_item(ident)
    assert rec["verdict"] == "ZERO"
    assert rec["certified_success"] is True
    assert rec["false_promotion"] is False
    assert rec["unknown_as_success"] is False

    bad = dict(ident, id="A-demo-bad", candidate="x**2 + 3*x + 1",
               expected_verdict="NONZERO")
    rec2 = adjudicate_item(bad)
    assert rec2["verdict"] == "NONZERO"
    assert rec2["false_promotion"] is False
    assert rec2["nonzero_detection"] is True
    assert rec2["unknown_as_success"] is False
