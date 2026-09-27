"""Rational series by the digamma rule, exponential decay, bracket errata."""
from __future__ import annotations

import mpmath as mp
import pytest
import sympy as sp

from symbolic_compactification.manybody import certify_remainder, run_card
from symbolic_compactification.manybody.latex import locate_quote, rewrite_over
from symbolic_compactification.manybody.series import series_closed_form, verify_series_sum

pytestmark = pytest.mark.release_critical

S = ["n", "a", "b"]


def test_series_digamma_rule_matches_nsum():
    n, a, b = sp.symbols("n a b")
    closed, assumptions = series_closed_form(1 / ((n + a) ** 2 * (n + b)), n)
    vals = {a: sp.Rational(3, 7), b: sp.Rational(5, 3)}
    with mp.workdps(30):
        exact = mp.nsum(lambda k: 1 / ((k + mp.mpf(3) / 7) ** 2 * (k + mp.mpf(5) / 3)), [0, mp.inf])
    assert abs(complex(sp.N(closed.subs(vals), 25)) - complex(exact)) < 1e-20
    assert assumptions == ["SERIES_POLES_OFF_SUMMATION_RANGE"]


def test_series_verdicts():
    kw = {"variable": "n", "symbols": S}
    assert verify_series_sum("1/((n+a)*(n+b))", "(polygamma(0,a)-polygamma(0,b))/(a-b)", **kw)["status"] == "CERTIFIED_BY_RULE"
    assert verify_series_sum("1/((n+a)*(n+b))", "(polygamma(0,b)-polygamma(0,a))/(a-b)", **kw)["status"] == "NONZERO"
    assert verify_series_sum("1/((n+1)*(n+2))", "1", **kw)["status"] == "CERTIFIED_BY_RULE"
    assert "SUMMAND_DECAY_BELOW_1_OVER_N2" in verify_series_sum("1/(n+a)", "0", **kw)["reasons"]
    assert "POLE_ON_SUMMATION_RANGE" in verify_series_sum("1/((n-2)*(n+1))", "0", **kw)["reasons"]


def test_exponential_decay_route():
    syms = [{"name": "t"}, {"name": "G"}, {"name": "c"}]
    kw = {"variable": "t", "point": "oo", "order": -5, "symbols": syms, "positive": ("G", "t")}
    assert certify_remainder("1 + exp(I*c*t - G*t)", "1", **kw).status == "CERTIFIED_BY_RULE"
    assert certify_remainder("1 + exp(I*c*t + G*t)", "1", **kw).status != "CERTIFIED_BY_RULE"
    assert certify_remainder("1 + exp(I*c*t)", "1", **kw).status != "CERTIFIED_BY_RULE"


def _card(tmp_path, text, entry, lhs="x"):
    (tmp_path / "p.tex").write_text(text)
    return {"check": "identity", "symbols": ["x", "y"], "source_document": str(tmp_path / "p.tex"),
            "rhs": lhs, "source": {"lhs": entry, "rhs": lhs}}


def test_unbalanced_quote_and_bracket_erratum(tmp_path):
    doc = r"\begin{equation} [x + (y - y) \end{equation}  x"
    bare = run_card(_card(tmp_path, doc, r"[x + (y - y)"), require_source=True)
    assert bare["decision"] == "NOT_DECIDED"
    assert any("SOURCE_BRACKETS_UNBALANCED" in b for b in bare["decision_blocked_by"])
    fixed = run_card(_card(tmp_path, doc, {"quote": r"[x + (y - y)", "erratum": r"[x + (y - y)]"}),
                     require_source=True)
    assert fixed["decision"] == "NOT_DECIDED" and fixed["decision_with_errata"] == "VALID"
    with pytest.raises(Exception):
        from symbolic_compactification.manybody.fidelity import erratum_of
        erratum_of({"quote": "[x + y", "erratum": "[x - y]"})     # not bracket-only


def test_plain_tex_over_and_appendix_numbers():
    assert rewrite_over(r"{1 \over a-b}") == r"{\frac{1 }{ a-b}}"
    raw = ("\\begin{equation}a\\end{equation}\n\\appendix\n\\section{One}\n"
           "\\begin{equation}bb2\\end{equation}\n\\section{Two}\n\\begin{equation}cc3\\end{equation}")
    assert locate_quote(raw, "cc3")["number"] == "B1"
    assert locate_quote(raw, "bb2")["number"] == "A1"
    assert locate_quote(raw, "a")["environment"] == "equation"      # displayed math preferred
