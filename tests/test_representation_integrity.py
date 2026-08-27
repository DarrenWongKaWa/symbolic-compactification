"""Frozen P1 / SOL / LLM-run artifacts must stay byte-identical to 3fea222."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.representation_invention.eval.integrity import assert_frozen_intact


def test_frozen_runs_match_parent():
    assert_frozen_intact()
