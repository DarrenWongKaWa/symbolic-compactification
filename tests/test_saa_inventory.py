"""Frozen Guo source does not declare pole exclusion."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.source_assumption_audit.inventory import run as inventory  # noqa: E402
from research.source_assumption_audit.derive import run as derive  # noqa: E402


def test_no_positive_or_nonzero_declared():
    inv = inventory()
    assert inv["positive_declared"] == []
    assert inv["nonzero_declared"] == []
    assert inv["load_guo_item_required_assumptions"] is None
    assert inv["beta_json"]["real"] is True
    assert inv["beta_json"]["nonzero"] is False
    assert inv["gamma_json"]["nonzero"] is False
    assert inv["finite_gamma_phrase"] is True


def test_frozen_assumptions_do_not_derive_pole_exclusion():
    d = derive()
    assert d["derived_from_frozen_assumptions"] is False
    assert d["pole_witness_under_frozen_reals"]["z0_at_n_plus"] in ("0", "0.0")
    assert d["verdict"] == "TRULY_ADDITIONAL"


def test_counterfactual_positive_beta_gamma_and_real_epsilon():
    d = derive()
    assert d["derived_if_beta_and_gamma_positive"] is False
    assert d["derived_if_beta_gamma_positive_and_epsilon_real"] is True


def test_does_not_promote_hop_zero():
    d = derive()
    assert d["verdict"] != "ZERO"
    close = (ROOT / "research" / "remainder_certification" / "STATUS.md").read_text()
    assert "UNKNOWN LEVEL_B" in close or "LEVEL_B" in close
