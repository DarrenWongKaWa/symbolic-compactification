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


def test_draft_and_review_of_a_textbook_note(tmp_path):
    """A LaTeX note with a Matsubara sum, a Lorentzian Fermi integral written
    with Im psi, a trigamma series and a tail with a planted sign error."""
    import shutil
    from pathlib import Path

    from symbolic_compactification.manybody.batch import run_cards
    from symbolic_compactification.manybody.draft import draft

    note = tmp_path / "note.tex"
    shutil.copy(Path(__file__).parent / "fixtures" / "notes" / "broadened_level.tex", note)
    draft(note, tmp_path / "cards")
    report = run_cards([tmp_path / "cards"], require_source=True)
    by = {c["card"]: (c["check"], c["decision"]) for c in report["cards"]}
    assert by == {"eq_bubble": ("matsubara", "VALID"), "eq_lorentz": ("fermi_integral", "VALID"),
                  "eq_trigamma": ("series", "VALID"), "eq_tail": ("remainder", "INVALID")}


def test_physics_notation_is_never_misread_into_a_verdict(tmp_path):
    """Regression: the Dyson equation G^r(e) = [(g^r)^-1 - Sigma^r(e)]^-1 was
    once read as G**r * e and reported INVALID. Letter superscripts are labels
    and name(...) needs a declared reading, so it must not be decided."""
    from symbolic_compactification.manybody.latex import latex_to_plain

    assert "G__r" in latex_to_plain(r"{\mathbf G}^r(\epsilon)")
    assert "E^(" in latex_to_plain(r"e^{i x}") and "^(2)" in latex_to_plain(r"\omega^2")
    tex = tmp_path / "p.tex"
    tex.write_text(r"\begin{equation} {\mathbf G}^r(\epsilon)=[({\mathbf g}^r)^{-1}"
                   r"-{\mathbf\Sigma}^r(\epsilon)]^{-1} \end{equation}")
    card = {"check": "identity", "symbols": ["G", "g", "Sigma", "epsilon", "r"],
            "source_document": str(tex),
            "source": {"lhs": r"{\mathbf G}^r(\epsilon)",
                       "rhs": r"[({\mathbf g}^r)^{-1}-{\mathbf\Sigma}^r(\epsilon)]^{-1}"}}
    assert run_card(card, require_source=True)["decision"] == "NOT_DECIDED"
    product = {"check": "identity", "symbols": ["beta", "x"], "source_document": str(tex),
               "source": {"lhs": r"\beta(x)"}, "rhs": "beta*x"}
    tex.write_text(r"\beta(x)")
    assert any("SOURCE_APPLICATION_AMBIGUOUS" in b
               for b in run_card(product, require_source=True)["decision_blocked_by"])
    assert run_card({**product, "multiply": ["beta"]})["decision"] == "VALID"


def test_one_command_review_of_the_toolbox_note(tmp_path):
    """Eight displayed relations, every drafted check type, two planted errors
    (telescoping sum 1/(a+1) instead of 1/a; n_F slope beta/2 instead of beta/4)."""
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = Path(__file__).parent / "fixtures" / "notes" / "toolbox.tex"
    result = review(note, tmp_path / "review")
    decisions = {s["step"]: (s["check"], s["decision"]) for s in result["steps"]}
    assert decisions == {
        "eq:pf": ("identity", "VALID"), "eq:telescope": ("series", "INVALID"),
        "eq:triple": ("matsubara", "VALID"), "eq:small": ("remainder", "INVALID"),
        "eq:decay": ("remainder", "VALID"), "eq:lorentz": ("fermi_integral", "VALID"),
        "eq:trigamma": ("series", "VALID"), "eq:spectral": ("identity", "VALID")}
    assert result["html"] and Path(result["html"]).is_file()


def test_langreth_rules_are_drafted_and_checked(tmp_path):
    """JWM-style Langreth rules become langreth cards; C^r in place of C^a is caught."""
    from pathlib import Path

    from symbolic_compactification.manybody.latex import latex_to_plain
    from symbolic_compactification.manybody.review import review

    assert "L_R" in latex_to_plain(r"\Gamma^{L/R}") and "/" not in latex_to_plain(r"A_{L/R}(t)")
    note = Path(__file__).parent / "fixtures" / "notes" / "langreth_rules.tex"
    result = review(note, tmp_path / "review")
    assert {s["step"]: (s["check"], s["decision"]) for s in result["steps"]} == {
        "rules.r1": ("langreth", "VALID"), "rules.r2": ("langreth", "VALID"),
        "wrong": ("langreth", "INVALID")}


def test_adversarial_misreadings_are_not_decided(tmp_path):
    """Regressions from review: a Born self-energy definition must not be
    checked as an exact Langreth rule, and gamma(t) must not become a
    product just because 'gamma > 0' appears in the text."""
    from symbolic_compactification.manybody.review import review

    tex = tmp_path / "a.tex"
    tex.write_text("\\begin{document}\nWe have $\\gamma>0$ and write\n"
                   "\\begin{equation}\\label{g}\\gamma(t) = \\cos(t)\\end{equation}\n"
                   "\\begin{equation}\\label{py}\\gamma(t)^2 + \\sin(t)^2 = 1\\end{equation}\n"
                   "The Born self-energy is\n\\begin{equation}\\label{born}\\Sigma^{<}(t,t') = "
                   "\\int dt_1\\, G^{r}(t,t_1)\\,\\Gamma^{<}(t_1,t')\\end{equation}\n\\end{document}\n")
    result = review(tex, tmp_path / "review")
    assert result["assumptions_to_confirm"]["multiply"] == []
    assert {s["step"]: s["decision"] for s in result["steps"]} == {"py": "NOT_DECIDED",
                                                                   "born": "NOT_DECIDED"}


def test_charge_squared_is_not_an_exponential():
    from symbolic_compactification.manybody.latex import latex_to_plain

    assert "E^" not in latex_to_plain(r"\frac{e^2}{h}")
    assert "E^(" in latex_to_plain(r"e^{-\beta x}") and "E^(2)" in latex_to_plain(r"{\mathrm e}^{2}")


def test_matsubara_statistics_come_from_the_text(tmp_path):
    from symbolic_compactification.manybody.review import review

    body = (r"\begin{equation}\label{s}\frac{1}{\beta}\sum_n \frac{1}{(\ii\omega_n-a)(\ii\omega_n-c)}"
            r" = \frac{n_F(a)-n_F(c)}{a-c}\end{equation}")
    head = "\\documentclass{article}\\newcommand{\\ii}{\\mathrm{i}}\\begin{document}\n"
    for text, expected in (("With $\\beta>0$ the sum is\n", "NOT_DECIDED"),
                           ("With $\\beta>0$ the fermionic sum is\n", "VALID")):
        tex = tmp_path / f"{expected}.tex"
        tex.write_text(head + text + body + "\n\\end{document}\n")
        steps = review(tex, tmp_path / expected)["steps"]
        assert [s["decision"] for s in steps] == [expected]


def test_statistics_do_not_bleed_from_earlier_paragraphs(tmp_path):
    """Regression: 'fermionic' in earlier sentences must not tag a bosonic sum
    (defined via Omega_m = 2 pi m T) as fermionic and report it INVALID."""
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = Path(__file__).parent / "fixtures" / "notes" / "context_bleed.tex"
    result = review(note, tmp_path / "review")
    assert all(s["decision"] != "INVALID" for s in result["steps"])
    cards = list((tmp_path / "review" / "cards").glob("*.yaml"))
    assert not any("statistics: fermion" in c.read_text() for c in cards)


def test_fermi_integrals_with_finite_limits_are_not_drafted(tmp_path):
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = Path(__file__).parent / "fixtures" / "notes" / "integral_limits.tex"
    steps = {s["step"]: (s["check"], s["decision"]) for s in review(note, tmp_path / "r")["steps"]}
    assert steps == {"half": ("identity", "NOT_DECIDED"), "full": ("fermi_integral", "VALID")}


def test_positive_order_remainder_needs_a_stated_point(tmp_path):
    from symbolic_compactification.manybody.review import review

    body = r"\begin{equation}\label{big}x^2 + x + \frac{1}{x} = x^2 + \mathcal{O}(x)\end{equation}"
    for lead, expected in (("For large $x$ one has", "VALID"), ("One has", "NOT_DECIDED")):
        tex = tmp_path / f"{expected}.tex"
        tex.write_text("\\begin{document}\n" + lead + "\n" + body + "\n\\end{document}\n")
        assert [s["decision"] for s in review(tex, tmp_path / expected)["steps"]] == [expected]


def test_symbols_under_re_im_are_complex_unless_stated_real(tmp_path):
    """Regression: z = x + iy is complex, so z = Re z must not be VALID."""
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = Path(__file__).parent / "fixtures" / "notes" / "complex_z.tex"
    result = review(note, tmp_path / "r")
    assert "z" in result["assumptions_to_confirm"]["complex"]
    assert all(s["decision"] != "VALID" for s in result["steps"])


def test_rerun_drafts_new_relations_and_keeps_edits(tmp_path):
    import shutil
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = tmp_path / "n.tex"
    shutil.copy(Path(__file__).parent / "fixtures" / "notes" / "broadened_level.tex", note)
    first = review(note, tmp_path / "o")
    conventions = tmp_path / "o" / "cards" / "conventions.yaml"
    conventions.write_text(conventions.read_text() + "# reviewer note: kept\n")
    note.write_text(note.read_text().replace(
        "\\end{document}",
        "\\begin{equation}\\label{eq:new}\\frac{1}{x-a}-\\frac{1}{x-b} = \\frac{a-b}{(x-a)(x-b)}"
        "\\end{equation}\n\\end{document}"))
    second = review(note, tmp_path / "o")
    assert second["added_on_rerun"] == ["eq_new"]
    assert len(second["steps"]) == len(first["steps"]) + 1
    assert "# reviewer note: kept" in conventions.read_text()
    assert "../manuscript/source.tex" in (tmp_path / "o" / "cards" / "eq_new.yaml").read_text()


def test_realness_statements_and_unstated_realness(tmp_path):
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    note = Path(__file__).parent / "fixtures" / "notes" / "real_energies.tex"
    steps = {s["step"]: s["decision"] for s in review(note, tmp_path / "a")["steps"]}
    assert steps["eq:abssq"] == "VALID"            # "for real energies $\epsilon$"
    bare = tmp_path / "bare.tex"
    bare.write_text("\\begin{document}\n\\begin{equation}\\label{eq:abssq}"
                    "|\\mathrm{Re}\\,\\epsilon|^2 + (\\mathrm{Im}\\,\\epsilon)^2 = \\epsilon^2"
                    "\\end{equation}\n\\end{document}\n")
    result = review(bare, tmp_path / "b")
    assert [s["decision"] for s in result["steps"]] == ["NOT_DECIDED"]


def test_an_edited_claim_never_passes_on_a_stale_card(tmp_path):
    """Regression: after editing x + y = y + x into x + y = y - x the old card
    must not be certified against text found elsewhere in the paper."""
    from pathlib import Path

    from symbolic_compactification.manybody.review import review

    tex = tmp_path / "p.tex"
    tex.write_text("\\documentclass{article}\n\\begin{document}\n\\begin{equation}\n\\label{eq:one}\n"
                   "x + y = y + x\n\\end{equation}\n\\end{document}\n")
    assert [s["decision"] for s in review(tex, tmp_path / "o")["steps"]] == ["VALID"]
    tex.write_text((Path(__file__).parent / "fixtures" / "notes" / "stale_edit.tex").read_text())
    decisions = {s["step"]: s["decision"] for s in review(tex, tmp_path / "o")["steps"]}
    assert decisions["eq:one"] == "NOT_DECIDED" and decisions["eq:two"] == "VALID"
