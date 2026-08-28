"""Phase V1: false ZERO remains 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.scalable_verification.eval.generic_suite import run


def test_generic_suite_false_zero_is_zero():
    rep = run()
    assert rep["n_false_zero"] == 0
    assert rep["gate_pass"] is True
