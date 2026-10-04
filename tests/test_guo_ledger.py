"""Acceptance: Appendix D of Guo et al. as a quoted step ledger."""
from __future__ import annotations

from pathlib import Path

import pytest

from symbolic_compactification.manybody import dualread
from symbolic_compactification.manybody.ledger import run_ledger

LEDGER = Path(__file__).resolve().parents[1] / "research-cases" / "guo-evidence-ledger" / "ledger" / "steps.yaml"

pytestmark = pytest.mark.skipif(not dualread.available() or not LEDGER.exists(),
                                reason="antlr4 runtime or the Guo case missing")


def test_guo_appendix_d_ledger_is_decided_from_quotes(tmp_path):
    out = run_ledger(LEDGER, tmp_path / "out")
    rows = {r["step"]: r for r in out["steps"]}
    assert out["counts"] == {"VALID": 12, "INVALID": 0, "NOT_DECIDED": 0, "NEEDS_REVIEWER": 0}
    exact = {k for k, r in rows.items() if not r["holds_given"]}
    assert exact == {"K1A-regroup", "TA-prefactor", "C1-regroup", "C2-regroup", "Vab-factor",
                     "A-antisym", "Omega-sign"}
    assert len(rows["Vab-FH"]["holds_given"]) == 4         # four index instances of Feynman-Hellmann
    assert rows["K1A-metric"]["to"] == "#59"                 # located in the paper
