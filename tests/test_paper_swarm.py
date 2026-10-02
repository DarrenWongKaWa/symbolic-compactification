"""Regressions from the swarm test on sixteen arXiv papers (PRD-type thermal
field theory and NEGF transport). The inputs are small synthetic notes that
reproduce each reading problem; no paper text is used."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody.cards import run_card
from symbolic_compactification.manybody.latex import latex_to_plain, read_macros
from symbolic_compactification.manybody.relations import steps_from_latex
from symbolic_compactification.manybody.review import review


def _review(tmp_path, body: str, preamble: str = "", name: str = "p") -> dict:
    tex = tmp_path / f"{name}.tex"
    tex.write_text(preamble + "\\begin{document}\n" + body + "\n\\end{document}\n", encoding="utf-8")
    return review(tex, tmp_path / f"r_{name}")


def _decisions(result: dict) -> dict[str, str]:
    return {s["step"]: s["decision"] for s in result["steps"]}


def test_display_environments_opened_by_macros_are_read():
    raw = ("\\newcommand{\\be}{\\begin{equation}}\\newcommand{\\ee}{\\end{equation}}\n"
           "\\begin{document}\\be a + b = b + a \\label{x}\\ee\\end{document}")
    assert [(s["lhs"], s["rhs"]) for s in steps_from_latex(raw)] == [("a + b", "b + a")]


def test_providecommand_and_declare_math_operator_expand():
    macros = read_macros("\\providecommand{\\abs}[1]{\\left|#1\\right|}\\DeclareMathOperator{\\Tr}{Tr}")
    assert latex_to_plain(r"\abs{x} + \Tr(A)", macros) == "Abs(x) + Tr(A)"


@pytest.mark.parametrize("latex,plain", [
    (r"p\frac{1-px}{x}", "p((1-p x)/(x))"),          # px is p times x
    (r"K_0K_2", "K_0 K_2"),
    (r"e^{-iEt}", "E^(-i Esym t)"),
    (r"G^{ra}(t)", "G__ra(t)"),                     # a letter superscript stays a label
    (r"\Gamma_{eff}", " Gamma_eff"),                # a subscript stays one name
    (r"\coth\frac{\beta\omega}{2}", " coth((( beta  omega )/(2)))"),
    (r"\sin^2\theta", "( sin( theta ))^(2)"),
    (r"\frac{d (x^3)}{dx}", " Diff(((x^(3))), x, 1) "),
])
def test_physics_latex_reads_as_meant(latex, plain):
    assert latex_to_plain(latex) == plain


@pytest.mark.parametrize("latex", [r"\cos\omega t", r"\frac{dE}{dk}", r"\cos\theta^2"])
def test_ambiguous_latex_is_left_unread(latex):
    assert "\\" in latex_to_plain(latex)            # refused, never guessed


def test_plus_minus_relations_are_checked_for_both_signs(tmp_path):
    got = _decisions(_review(tmp_path, "Let $\\Gamma>0$ and real $\\epsilon$.\n"
                             "\\begin{equation}\\frac{1}{\\epsilon \\pm i\\Gamma} = \\frac{\\epsilon \\mp i\\Gamma}"
                             "{\\epsilon^2+\\Gamma^2}\\label{pm}\\end{equation}"))
    assert got == {"pm.p": "VALID", "pm.m": "VALID"}


def test_a_trace_is_never_checked_as_numbers(tmp_path):
    got = _decisions(_review(tmp_path, "\\begin{equation}\\mathrm{Tr}(A B C) = \\mathrm{Tr}(B A C)\\label{t}\\end{equation}"))
    assert got == {"t": "NOT_DECIDED"}


def test_a_declared_function_is_never_refuted_as_arbitrary(tmp_path):
    (tmp_path / "p.tex").write_text("\\begin{equation}\\zeta(4) = \\frac{\\pi^4}{90}\\label{z}\\end{equation}")
    card = {"check": "identity", "symbols": ["x"], "functions": ["zeta"], "source_document": str(tmp_path / "p.tex"),
            "display": "z", "source": {"lhs": "\\zeta(4)", "rhs": "\\frac{\\pi^4}{90}"}}
    out = run_card(card)
    assert out["decision"] == "NOT_DECIDED"
    assert any(w.startswith("ARBITRARY_FUNCTION") for w in out["decision_blocked_by"])


def test_a_named_special_function_is_the_special_function(tmp_path):
    got = _decisions(_review(tmp_path, "Here $\\zeta$ is the Riemann zeta function.\n"
                             "\\begin{equation}\\zeta(4) = \\frac{\\pi^4}{90}\\label{z4}\\end{equation}\n"
                             "\\begin{equation}\\zeta(2) = \\frac{\\pi^2}{7}\\label{z2}\\end{equation}"))
    assert got == {"z4": "VALID", "z2": "INVALID"}


def test_density_matrix_and_spinors_do_not_make_everything_a_matrix():
    from symbolic_compactification.manybody.prose import stated_noncommuting
    assert stated_noncommuting("where $\\rho$ is the density matrix and $\\psi$ a spinor") is None
    assert stated_noncommuting("V is the transfer matrix element") is None
    assert stated_noncommuting("G and Sigma are 2x2 matrices") is not None


def test_operator_names_come_from_next_to_the_word():
    from symbolic_compactification.manybody.prose import _operator_names
    text = ("At temperature $T$ and chemical potential $\\mu$ we use the Hamiltonian. "
            "The current operator $\\hat{I}^{e}_p$ is measured.")
    names = _operator_names(text)
    assert "T" not in names and "mu" not in names and "e" not in names


def test_aligned_inside_an_equation_is_layout():
    raw = "\\begin{document}\\begin{equation}\\begin{aligned} a &= b \\\\ &= c \\end{aligned}\\end{equation}\\end{document}"
    assert [(s["lhs"], s["rhs"]) for s in steps_from_latex(raw)] == [("a", "b"), ("b", "c")]
