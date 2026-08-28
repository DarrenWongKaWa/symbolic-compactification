"""Generic family suite: false FAMILY_ZERO is 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.multibranch_verification.eval.generic_family_suite import run


def test_false_family_zero_is_zero():
    rep = run()
    assert rep["n_false_family_zero"] == 0
    assert rep["gate_pass"] is True
