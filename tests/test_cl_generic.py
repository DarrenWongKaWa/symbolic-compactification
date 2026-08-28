"""V5 generic suite: false ZERO = 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.coefficient_laurent.eval.generic_suite import run  # noqa: E402
from research.coefficient_laurent.schema import ZERO  # noqa: E402


def test_generic_false_zero_is_zero():
    r = run()
    assert r["false_ZERO"] == 0
    assert r["pass"] is True
    for row in r["rows"]:
        if row["expect"] != ZERO:
            assert row["got"] != ZERO
