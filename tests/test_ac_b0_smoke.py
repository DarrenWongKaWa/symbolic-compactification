"""B0 smoke on assumption-complete DEV identities. Not Guo."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.assumption_complete_representation.eval.b0_sympy import run  # noqa: E402


def test_b0_smoke_all_zero_and_not_guo():
    r = run()
    assert r["guo"] is False
    assert r["ai_unique_success"] == 0
    assert r["n_zero"] == r["n"]
    for row in r["rows"]:
        assert row["b0_zero"] is True
        assert row["discovers_representation"] is False
        assert "guo" not in row["id"].lower()
