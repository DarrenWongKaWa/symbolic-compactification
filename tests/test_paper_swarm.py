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


# ---- second swarm (thirty more papers) ----

def test_sums_over_all_integers(tmp_path):
    got = _decisions(_review(tmp_path, "Let $y>0$.\n"
                             "\\begin{equation}\\sum_{n=-\\infty}^{\\infty} \\frac{y}{n^2+y^2} = \\pi\\coth(\\pi y)\\label{s1}\\end{equation}\n"
                             "\\begin{equation}\\sum_{n=-\\infty}^{\\infty} \\frac{y}{n^2+y^2} = 2\\pi\\coth(\\pi y)\\label{s2}\\end{equation}\n"
                             "\\begin{equation}\\sum_{n=-\\infty}^{\\infty} \\frac{1}{(n+a)^2} = \\frac{\\pi^2}{\\sin^2(\\pi a)}\\label{s3}\\end{equation}"))
    assert got == {"s1": "VALID", "s2": "INVALID", "s3": "VALID"}


def test_a_value_at_a_point_is_not_a_definition(tmp_path):
    """u(0) = u(a) = 0 are boundary conditions; reading u(a) = 0 as u = 0
    once gave the wrong VALID u(0) = u(a)."""
    got = _decisions(_review(tmp_path, "We impose Dirichlet boundary conditions,\n"
                             "\\begin{equation}u_k(0,y) = u_k(a,y) = 0 .\\label{bc}\\end{equation}"))
    assert set(got.values()) == {"NOT_DECIDED"}


def test_defining_displays_define_and_conditional_ones_do_not(tmp_path):
    got = _decisions(_review(tmp_path, "Let $\\beta>0$. We define the occupation\n"
                             "\\begin{equation}N_0 = \\frac{1}{e^{\\beta\\epsilon}+1}\\label{d}\\end{equation}\n"
                             "so that\n\\begin{equation}N_0 + \\frac{1}{e^{-\\beta\\epsilon}+1} = 1\\label{u}\\end{equation}\n"
                             "At zero temperature the occupation is\n\\begin{equation}M = 1\\label{c}\\end{equation}\n"
                             "\\begin{equation}M + 1 = 2\\label{v}\\end{equation}"))
    assert got["u"] == "VALID" and got["v"] == "NOT_DECIDED"


def test_partial_derivatives_hold_the_other_variables(tmp_path):
    got = _decisions(_review(tmp_path, "Let $\\beta>0$ and real $\\epsilon$, $\\mu$.\n"
                             "\\begin{equation}-\\frac{\\partial}{\\partial\\epsilon}\\left(\\frac{1}{e^{\\beta(\\epsilon-\\mu)}+1}\\right)"
                             " = \\frac{\\partial}{\\partial\\mu}\\left(\\frac{1}{e^{\\beta(\\epsilon-\\mu)}+1}\\right)\\label{s}\\end{equation}"))
    assert got == {"s": "VALID"}


def test_macros_follow_tex_rules():
    m = read_macros("\\newcommand{\\a}{x}\\renewcommand{\\a}{y}\\newcommand{\\b}{u}\\providecommand{\\b}{v}"
                    "\\begin{document}")
    assert m["a"] == (0, "y") and m["b"] == (0, "u")         # last preamble one; provide never overrides
    assert read_macros("\\newcommand{\\a}{x}\\begin{document}\\renewcommand{\\a}{y}")["a"][1] == "\\MACROREDEFINED"


@pytest.mark.parametrize("latex,plain", [
    (r"{\cal E}_0", " Esym__cal_0"),
    (r"\Biggl( x \Biggr)", " ( x  )"),
    (r"\frac{\pi^2}{\sin^2(\pi a)}", "(( pi ^(2))/(( sin( pi  a))^(2)))"),
])
def test_old_tex_and_function_powers(latex, plain):
    assert latex_to_plain(latex) == plain


def test_matrix_words_need_a_symbol():
    from symbolic_compactification.manybody.prose import stated_noncommuting
    assert stated_noncommuting("the aim is to calculate the matrix element") is None
    assert stated_noncommuting("where $\\sigma_i$ are Pauli matrices") is not None


def test_a_definition_quoted_from_the_checked_display_proves_nothing(tmp_path):
    """A reviewer who defines Q from display q and then checks q gets
    'Q = a/2 + 1' with Q := a/2 + 1: true by construction, not VALID."""
    import yaml
    body = ("Let $a$ be real.\n\nThe charge comes out as\n"
            "\\begin{equation}Q = \\frac{a}{2} + 1\\label{q}\\end{equation}\n"
            "\\begin{equation}2Q = a + 2\\label{c}\\end{equation}")
    _review(tmp_path, body)
    conventions = tmp_path / "r_p" / "cards" / "conventions.yaml"
    data = yaml.safe_load(conventions.read_text())
    data.setdefault("source", {})["define:Q()"] = {"quote": "\\frac{a}{2} + 1", "display": "q"}
    data["named_quantities"] = [n for n in data.get("named_quantities") or [] if n != "Q"]
    data["symbols"] = [x for x in data["symbols"] if x["name"] != "Q"]
    data["notation"] = {**(data.get("notation") or {}), "Q": "Q()"}
    data["source_document"] = "../manuscript/source.tex"
    conventions.write_text(yaml.safe_dump(data, sort_keys=False))
    result = _review(tmp_path, body)
    got = {s["step"]: s for s in result["steps"]}
    assert got["c"]["decision"] == "VALID"
    assert got["q"]["decision"] == "NOT_DECIDED"
    assert any("DEFINED_BY_THIS_DISPLAY:Q" in w for w in got["q"]["why_not_decided"])


def test_a_definition_from_another_section_does_not_refute(tmp_path):
    """R(x) defined for one model is not R(x) of the next section."""
    got = {s["step"]: s for s in _review(tmp_path, (
        "\\section{First model}\nThe function is\n"
        "\\begin{equation}R(x) = \\frac{1}{2} + x^2\\label{R}\\end{equation}\n"
        "\\begin{equation}R(1) = 2\\label{same}\\end{equation}\n"
        "\\section{Second model}\nHere\n"
        "\\begin{equation}R(1) = 7\\label{other}\\end{equation}\n"
        "\\begin{equation}R(1) = \\frac{3}{2}\\label{agrees}\\end{equation}"))["steps"]}
    assert got["same"]["decision"] == "INVALID"
    assert got["other"]["decision"] == "NOT_DECIDED"
    assert any("DEFINITION_FROM_ANOTHER_SECTION:R" in w for w in got["other"]["why_not_decided"])
    assert got["agrees"]["decision"] == "VALID"


def _matsubara(claim, **extra):
    from symbolic_compactification.audit.schema import MATSUBARA_POLES_OFF_AXIS
    return run_card({"label": "m", "check": "matsubara", "statistics": "boson", "variable": "z",
                     "beta": "beta", "summand": "1/(z**2 - w()**2)", "claim": claim,
                     "define": {"w()": "sqrt(k**2 + m**2)"},
                     "symbols": [{"name": "beta", "positive": True}, {"name": "k", "positive": True},
                                 {"name": "m", "positive": True}],
                     "rules": [MATSUBARA_POLES_OFF_AXIS], **extra}, require_source=False)


def test_matsubara_sums_expand_definitions():
    assert _matsubara("-(1 + 2*nB(w()))/(2*w())")["decision"] == "VALID"


def test_the_summed_variable_is_not_a_constrained_name():
    """'k_0 = i omega_n' in the text describes the summed variable; it must
    not hold back the refutation of a wrong sign."""
    out = _matsubara("(1 + 2*nB(w()))/(2*w())", constrained=["z"], valued_in_text=["z"])
    assert out["decision"] == "INVALID", out["decision_blocked_by"]
    out = _matsubara("(1 + 2*nB(w()))/(2*w())", constrained=["k"])
    assert out["decision"] == "NOT_DECIDED"


@pytest.mark.parametrize("latex,plain", [
    (r"(-1)^n", "(-1)^(n)"),
    (r"2^k", "2^(k)"),
    (r"f(x)^n", "f(x)^(n)"),
    (r"(AB)^R", "(A B)__R"),                     # a label of a product, never a power
    (r"x^n", "x__n"),
    (r"G_>(x) + G_{<}(x)", "G_gt(x) + G_lt(x)"),
    (r"\ln\left|\frac{1+q}{1-q}\right|", " log(Abs(((1+q)/(1-q))))"),
    (r"\ln|x| y", "\\lnx| y"),                   # ln|x| y or ln(|x| y): refused
    (r"a \> b", "a   b"),
])
def test_powers_bars_and_spacing(latex, plain):
    assert latex_to_plain(latex) == plain


def test_angle_bracket_macros_are_read():
    macros = read_macros("\\newcommand\\<{\\langle}\\renewcommand\\>{\\rangle}\\begin{document}")
    assert macros["<"] == (0, "\\langle")
    assert latex_to_plain("\\<T\\>", macros) == "\\langle T\\rangle"


@pytest.mark.parametrize("text,flagged", [
    ("fixing the divergence of the potential does not commute with the gauge fixing.", False),
    ("the two limits do not commute.", False),
    ("the spin operators do not commute.", True),
    ("Here $H_0$ does not commute with $V$.", True),
])
def test_do_not_commute_needs_a_mathematical_subject(text, flagged):
    """A remark about procedures in a long lecture once blocked every card of it."""
    from symbolic_compactification.manybody.prose import stated_noncommuting
    assert (stated_noncommuting(text) is not None) == flagged


@pytest.mark.parametrize("text,names", [
    # the relation and the momentum before 'is the annihilation operator' are not operators
    (r"with $K\equiv(k_0,\vec k)$, $\omega_k=\sqrt{k^2+m^2}$, $a(k)$ is the annihilation operator.", ["a"]),
    (r"$U(t,t_0)$ is the evolution operator.", ["U"]),
    (r"the operators $c_k$ and $d_k$ obey", ["c_k", "d_k"]),   # d_k is a name, not a differential
    (r"$p$ and $q$ are fermionic operators.", ["p", "q"]),
])
def test_operator_names_are_what_the_sentence_describes(text, names):
    from symbolic_compactification.manybody.prose import _operator_names
    assert sorted(_operator_names(text)) == names
