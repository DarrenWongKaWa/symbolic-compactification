"""Generic iterated-confluence suite. FALSE FAMILY_ZERO = 0."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.iterated_confluence.eval.generic_suite import run  # noqa: E402
from research.iterated_confluence.falsifier import run_cases  # noqa: E402
from research.iterated_confluence.schema import FAMILY_ZERO  # noqa: E402


def test_generic_suite_false_family_zero_is_zero():
    report = run()
    assert report["false_FAMILY_ZERO"] == 0
    assert report["pass"] is True
    for row in report["rows"]:
        if row["expect"] != FAMILY_ZERO:
            assert row["got"] != FAMILY_ZERO


def test_falsifier_false_family_zero_is_zero():
    report = run_cases()
    assert report["n_false_family_zero"] == 0
    for row in report["rows"]:
        if row.get("expect") != FAMILY_ZERO:
            assert row["got"] != FAMILY_ZERO
