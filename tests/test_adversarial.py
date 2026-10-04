"""Review rounds 9 and 10: inputs written by adversarial reviewers to make the
tool give a wrong verdict, after the coverage upgrade. Every one of them once
came back VALID or INVALID with the wrong answer, or stopped the review.

golden.json lists, per file, every step that is decided today; each was
checked by hand. Any new or changed verdict on these files fails the test
and has to be reviewed before golden.json is updated."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from symbolic_compactification.manybody.review import review

ADVERSARIAL = Path(__file__).parent / "fixtures" / "notes" / "adversarial"
GOLDEN = json.loads((ADVERSARIAL / "golden.json").read_text())


@pytest.mark.parametrize("name", sorted(GOLDEN))
def test_adversarial_input_gives_only_reviewed_verdicts(tmp_path, name):
    result = review(ADVERSARIAL / name, tmp_path / "r")
    assert "steps" in result, result                       # the review never stops
    decided = {s["step"]: s["decision"] for s in result["steps"] if s["decision"] != "NOT_DECIDED"}
    assert decided == GOLDEN[name]


def test_langreth_order_only_mismatch_is_not_refuted():
    from symbolic_compactification.manybody import verify_langreth
    assert verify_langreth(["A", "B"], "less", "B_less*A_R + B_A*A_less")["status"] == "UNKNOWN"
    assert verify_langreth(["A", "B"], "less", "A_R*B_less")["status"] == "NONZERO"


@pytest.mark.parametrize("text,expected", [
    ("All quantities below are matrices in orbital space.", True),
    ("G and Sigma are 2x2 matrices", True),
    ("the density matrix of the leads", False),
    ("the T-matrix approximation", False),
])
def test_stated_noncommuting(text, expected):
    from symbolic_compactification.manybody.draft import stated_noncommuting
    assert bool(stated_noncommuting(text)) is expected


def test_im_z_positive_is_not_z_positive():
    from symbolic_compactification.manybody.draft import _positive_symbols
    assert "z" not in _positive_symbols(r"for $\mathrm{Im}\,z>0$ and $\eta > 0$")
    assert "eta" in _positive_symbols(r"for $\mathrm{Im}\,z>0$ and $\eta > 0$")
