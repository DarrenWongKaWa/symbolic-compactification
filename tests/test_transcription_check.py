"""A step card is checked against a verbatim quote of its source."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import run_card
from symbolic_compactification.manybody.fidelity import decide, translate

pytestmark = pytest.mark.release_critical

NOTE = """Claim: the divided difference obeys
  f[x, y] = (f(x) - f(y))/(x - y)  and  d/dx f[x, y] = f[x, x, y].
Lorentzian: L = 2G/(w^2 + G^2), and z_pm = 1/2 pm i beta x/(2 pi).
"""


def _card(tmp_path, **fields):
    (tmp_path / "note.md").write_text(NOTE)
    base = {"check": "identity", "symbols": ["x", "y"], "functions": ["f"],
            "source_document": str(tmp_path / "note.md")}
    return {**base, **fields}


def test_translate_rules():
    calls = {"psi", "f", "polygamma"}
    assert translate("2iG (x)^2", {}, calls, names={"G", "x"}) == "2*(I*G)*(x)**2"
    assert translate("[a - b] c", {}, calls, names={"a", "b", "c"}) == "(a-b)*c"
    assert translate("psi(z_+)", {"z_+": "zp"}, calls) == "psi(zp)"
    assert translate("e_nm/2", {"e_nm": "e_n - e_m"}, calls) == "(e_n-e_m)/2"
    assert translate("ψ(β x)", {}, calls, names={"beta", "x"}) == "psi(beta*x)"


def test_faithful_card_matches_and_decides(tmp_path):
    card = _card(tmp_path, lhs="Diff(DD_f(x, y), x, 1)", rhs="DD_f(x, x, y)",
                 notation={"d/dx f[x, y]": "Diff(DD_f(x, y), x, 1)", "f[x, x, y]": "DD_f(x, x, y)"},
                 source={"lhs": "d/dx f[x, y]", "rhs": "f[x, x, y]"})
    result = run_card(card)
    assert result["transcription"]["status"] == "MATCH"
    assert result["transcription_verified"] and result["decision"] == "VALID"


def test_card_that_changes_the_claim_is_not_decided(tmp_path):
    # the agent encodes the derivative of f itself instead of the divided difference
    card = _card(tmp_path, lhs="D_f(1, x)", rhs="DD_f(x, x, y)",
                 notation={"d/dx f[x, y]": "Diff(DD_f(x, y), x, 1)", "f[x, x, y]": "DD_f(x, x, y)"},
                 source={"lhs": "d/dx f[x, y]", "rhs": "f[x, x, y]"})
    result = run_card(card)
    assert result["verdict"] == "NONZERO"
    assert result["transcription"]["fields"]["lhs"]["status"] == "MISMATCH"
    assert result["decision"] == "NOT_DECIDED"


def test_quote_must_be_in_the_document(tmp_path):
    card = _card(tmp_path, lhs="DD_f(x, y)", rhs="(f(x) - f(y))/(x - y)",
                 notation={"f[x, y]": "DD_f(x, y)"},
                 source={"rhs": "(f(x) - f(y))/(y - x)"})
    result = run_card(card)
    assert result["transcription"]["status"] == "NOT_IN_DOCUMENT"
    assert result["decision"] == "NOT_DECIDED"


def test_branch_and_wrap(tmp_path):
    card = _card(tmp_path, symbols=[{"name": "beta", "positive": True}, {"name": "x"}],
                 functions=[], define={"zm(x)": "1/2 - I*beta*x/(2*pi)"},
                 lhs="zm(x)", rhs="1/2 - I*beta*x/(2*pi)",
                 source={"define:zm(x)": {"quote": "1/2 pm i beta x/(2 pi)", "branch": "-"},
                         "rhs": {"quote": "1/2 pm i beta x/(2 pi)", "branch": "-", "wrap": "({})"}})
    assert run_card(card)["transcription"]["status"] == "MATCH"
    card["source"]["define:zm(x)"]["branch"] = "+"
    assert run_card(card)["transcription"]["status"] == "MISMATCH"


def test_unparseable_quote_is_unchecked_not_mismatch(tmp_path):
    card = _card(tmp_path, lhs="DD_f(x, y)", rhs="(f(x) - f(y))/(x - y)",
                 source={"lhs": "f[x, y]"})          # f[...] without notation is not a call
    result = run_card(card)
    assert result["transcription"]["status"] == "UNCHECKED"
    assert result["decision"] == "VALID" and not result["transcription_verified"]


def test_decide():
    assert decide("CERTIFIED_BY_RULE", "ABSENT") == "VALID"
    assert decide("NONZERO", "MATCH") == "INVALID"
    assert decide("NONZERO", "MISMATCH") == "NOT_DECIDED"
    assert decide("UNKNOWN", "MATCH") == "NOT_DECIDED"


def test_wrap_cannot_change_the_claim(tmp_path):
    (tmp_path / "n.md").write_text("we have e_n - e_m here")
    card = {"check": "identity", "symbols": ["e_n", "e_m"], "source_document": str(tmp_path / "n.md"),
            "lhs": "-(e_n - e_m)", "rhs": "-(e_n - e_m)",
            "source": {"lhs": {"quote": "e_n - e_m", "wrap": "-({})"},
                       "rhs": {"quote": "e_n - e_m", "wrap": "-({})"}}}
    result = run_card(card, require_source=True)
    assert result["decision"] == "NOT_DECIDED"
    assert result["transcription"]["fields"]["lhs"]["reason"] == "SOURCE_WRAP_NOT_ALLOWED"


def test_strict_mode_requires_card_definitions_to_be_quoted(tmp_path):
    (tmp_path / "n.md").write_text("claim: fp(e_n) - fp(e_m)")
    card = {"check": "identity", "symbols": ["e_n", "e_m", "beta"],
            "source_document": str(tmp_path / "n.md"), "define": {"fp(x)": "1/2 + beta*x"},
            "source": {"lhs": "fp(e_n) - fp(e_m)", "rhs": "fp(e_n) - fp(e_m)"}}
    result = run_card(card, require_source=True)
    assert result["decision"] == "NOT_DECIDED"
    assert any(b.startswith("UNQUOTED_CARD_DEFINITION:fp") for b in result["decision_blocked_by"])


def test_sum_pm_needs_a_bracketed_group():
    from symbolic_compactification.manybody.fidelity import expand_sum_pm
    from symbolic_compactification.models import AdapterError
    with pytest.raises(AdapterError):
        expand_sum_pm("sum_pm A + B")


def test_source_entry_without_quote_is_unchecked(tmp_path):
    (tmp_path / "n.md").write_text("x")
    card = {"check": "identity", "symbols": ["x"], "lhs": "x", "rhs": "x",
            "source_document": str(tmp_path / "n.md"), "source": {"lhs": {"branch": "+"}}}
    assert run_card(card)["transcription"]["status"] == "UNCHECKED"
