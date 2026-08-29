"""Generic remainder suite: false CERTIFIED = 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.remainder_certification.eval.generic_suite import run  # noqa: E402
from research.remainder_certification.schema import CERTIFIED  # noqa: E402
from research.coefficient_laurent.schema import ZERO  # noqa: E402


def test_generic_false_certified_is_zero():
    r = run()
    assert r["false_CERTIFIED"] == 0
    assert r["falsifier_false_CERTIFIED"] == 0
    assert r["pass"] is True
    assert CERTIFIED != ZERO
    for row in r["rows"]:
        if row["expect"] != CERTIFIED:
            assert row["got"] != CERTIFIED or row["id"] == "nC-cross"
        assert row["not_hop_zero"] is True
