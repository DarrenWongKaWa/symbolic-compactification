"""Phase 5 gate: generic DD positives ZERO; negatives not ZERO."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.eval.phase5 import evaluate
from research.representation_invention.obligations.constructors import dd_backend_name


def test_phase5_zero_false_zero():
    report = evaluate()
    assert report["n_false_zero"] == 0, report["rows"]
    assert report["gate_pass"] is True


def test_dd_package_is_used():
    assert dd_backend_name() == "research.representation_invention.dd"
