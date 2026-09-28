"""Every card in examples/cards runs and returns its declared `expect`."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from symbolic_compactification import cli
from symbolic_compactification.manybody import run_card, verify_fermi_integral
from symbolic_compactification.manybody.cards import CardError

pytestmark = pytest.mark.release_critical

CARDS = sorted((Path(__file__).resolve().parents[1] / "examples" / "cards").glob("*.yaml"))


@pytest.mark.parametrize("card", CARDS, ids=[c.stem for c in CARDS])
def test_example_card(card):
    expected = yaml.safe_load(card.read_text())["expect"]
    result = run_card(card)
    assert (result.get("status") or result.get("verdict")) == expected, result


def test_index_swap_card_names_the_swap():
    result = run_card(next(c for c in CARDS if c.stem == "index_swap_diagnosis"))
    assert any("n <-> m" in d for d in result["diagnosis"])


def test_fermi_integral_refuses_unsupported_forms():
    S = [{"name": "beta", "nonzero": True}, {"name": "G", "nonzero": True},
         {"name": "e"}, {"name": "w"}]
    kw = {"variable": "w", "beta": "beta", "symbols": S, "positive": ("beta", "G")}
    three = verify_fermi_integral("nF(e + w)*nF(e - w)*nF(w)/(w**2 + G**2)", "0", **kw)
    assert three["status"] == "UNKNOWN" and "UNSUPPORTED_FERMI_PRODUCT" in three["reasons"]
    slow = verify_fermi_integral("nF(e + w)/(w + I*G)", "0", **kw)
    assert "INTEGRAND_DECAY_BELOW_1_OVER_W2" in slow["reasons"]
    unsigned = verify_fermi_integral("nF(e + w)/(w**2 + G**2)", "0", variable="w", beta="beta",
                                     symbols=S)
    assert "POLE_HALF_PLANE_UNDETERMINED" in unsigned["reasons"]


def test_bad_card_is_rejected_and_cli_step_runs(capsys, tmp_path):
    with pytest.raises(CardError):
        run_card({"check": "nonsense"})
    card = tmp_path / "c.yaml"
    card.write_text("check: identity\nsymbols: [x]\nfunctions: [f]\n"
                    "lhs: DD_f(x, x, x)\nrhs: D_f(2, x)/2\n")
    assert cli.main(["manybody", "step", str(card)]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "ZERO"
