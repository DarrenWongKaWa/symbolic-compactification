"""Misreadings by reader A that the second reader caught on the 46-paper corpus.

Each quote below was refused as READERS_DISAGREE because reader A
(``latex_to_plain`` + ``translate``) misread it. Each test shows A's reading
and, through the card path (``dualread.require_agreement``), that SymPy's
reading now agrees with it. Quotes A cannot read safely are refused by A
itself instead of being misread."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import dualread, fidelity
from symbolic_compactification.manybody.fidelity import _pick_branch, translate
from symbolic_compactification.manybody.latex import latex_to_plain
from symbolic_compactification.models import AdapterError
from symbolic_compactification.parser import _ALLOWED_FUNCTIONS

needs_reader_b = pytest.mark.skipif(not dualread.available(), reason="antlr4 runtime missing")


def _a(tex: str, branch: str | None = None, functions=()) -> str:
    """Reader A alone: the quote in card syntax, before any notation."""
    callables = {*_ALLOWED_FUNCTIONS, *functions, "Diff"}
    return translate(_pick_branch(latex_to_plain(tex), branch), {}, callables)


def _both(tex: str, branch: str | None = None, functions=()) -> tuple[str, str]:
    """Both readers through the card path (dualread.require_agreement): A's
    expression and SymPy's reading. Raises AdapterError (READERS_DISAGREE)
    when they differ."""
    ctx = fidelity.source_context({"source_format": "latex"}, None, symbols=[],
                                  functions=list(functions), definitions={})
    entry = {"quote": tex, "branch": branch} if branch else tex
    _, expression, reader_b = fidelity._quote_expression(entry, ctx)
    assert reader_b is not None
    return expression, reader_b


def _refused_by_a(tex: str, functions=()) -> str:
    with pytest.raises(AdapterError) as err:
        _a(tex, functions=functions)
    return err.value.code


# 1. A subscript written after a superscript belongs to the base (TeX reads
#    X^{s}_{t} as X_{t}^{s}); it used to be left behind as a stray symbol '_t'.

SUB_AFTER_SUP = [
    (r"\Gamma^\mu_a", "Gamma_a**(mu)"),                     # nucl-th_0001040 eq7.def
    (r"\delta^\mu_\nu", "delta_nu**(mu)"),                  # 2207.00534 qed13.4
    (r"\delta^{\mu}_{\nu}", "delta_nu**(mu)"),              # 2207.00534 dys.r4
    (r"I^\beta_4", "Isym_4**(beta)"),                       # 2207.00534 phiq14.1
    (r"\dot{m}^2_\gamma", "m__dot_gamma**(2)"),             # 1607.01929 magn_mom
    (r"E^2_{p-k}", "Esym_pmk**(2)"),                        # 2207.00534 phiq13
    (r"m^2_{\textrm{th}}", "m_th**(2)"),                    # 2207.00534 spec4.3
]


@pytest.mark.parametrize("tex, expected", SUB_AFTER_SUP)
def test_subscript_after_superscript_belongs_to_the_base(tex, expected):
    assert _a(tex) == expected


@needs_reader_b
@pytest.mark.parametrize("tex, expected", SUB_AFTER_SUP)
def test_subscript_after_superscript_is_read_alike_by_both(tex, expected):
    assert _both(tex)[0] == expected


@needs_reader_b
def test_subscript_after_a_square_inside_a_quote_is_read_alike_by_both():
    expression, reader_b = _both(r"\frac{1}{(E_p-k_0)^2-E^2_{p-k}}")
    assert expression == "((1)/((Esym_p-k_0)**(2)-Esym_pmk**(2)))"
    assert "Esym_pmk" in reader_b


def test_label_superscript_then_subscript_is_unchanged():
    assert _a(r"F^b_{\mu\nu}") == "F__b_munu"
    assert _a(r"I^0_1") == "Isym__0_1"


@pytest.mark.parametrize("tex", [
    r"D^{-1}_{\rho\nu}",                 # an element of the inverse matrix, not 1/D_{rho nu}
    r"(D_0)^{-1}_{\lambda\nu}",          # a subscript on a bracket
    r"R^\alpha\,_{\beta\mu\nu}",         # a staggered index: the subscript has no base
    r"\left( a + b \right)_{x}",
])
def test_subscript_without_a_name_before_it_is_refused(tex):
    assert _refused_by_a(tex).startswith("SOURCE_CHARACTER_UNSUPPORTED")


# 2. {\rm X} in a subscript: the rewrite to \mathrm{X} dropped the subscript's
#    braces and the subscript took only '\mathrm', so r_{\rm H} became r_*(H).

RM_SUBSCRIPTS = [
    (r"r_{\rm H}", "r_H"),                                  # 1207.5808 eq91
    (r"E_{\rm tot}", "Esym_tot"),                           # hep-ph_0305001
    (r"\beta_{\rm m}", "beta_m"),                           # nucl-th_0001040 electric
    (r"\Omega_{\rm CN}", "Omega_CN"),                       # hep-ph_0011229
    (r"\Omega_{\rm loop}^{(0)}", "Omega_loop__0"),          # hep-ph_0011229 loop0
    (r"\frac{\mu\, r_{\rm H}^2}{\sqrt{3}}", "((mu*r_H**(2))/(sqrt(3)))"),
    (r"-\left(\frac{1}{ip-E_{\rm tot}} -\frac{1}{ip+E_{\rm tot}}\right)",
     "-(((1)/(I*p-Esym_tot))-((1)/(I*p+Esym_tot)))"),
]


@pytest.mark.parametrize("tex, expected", RM_SUBSCRIPTS)
def test_roman_subscript_is_part_of_the_name(tex, expected):
    assert _a(tex) == expected


@needs_reader_b
@pytest.mark.parametrize("tex, expected", RM_SUBSCRIPTS)
def test_roman_subscript_is_read_alike_by_both(tex, expected):
    assert _both(tex)[0] == expected


@pytest.mark.parametrize("tex, expected", [
    (r"\Psi_\text{GL}", "Psi_GL"),                          # 1802.09095 eq12
    (r"S_\mathrm{eff}", "S_eff"),
    (r"V^i_\mathrm{th}", "V__i_th"),                        # 1612.00466 eq30
    (r"G^\mathrm{R}", "G__R"),
])
def test_unbraced_wrapper_script_takes_its_group(tex, expected):
    assert _a(tex) == expected


# 3. k_0\mp k: the operator sign after a subscript was glued into it (k_0p).

@pytest.mark.parametrize("tex, branch, expected", [
    (r"k_0\mp k", "+", "k_0-k"),                            # 2207.00534 f3.m
    (r"k_0\mp k", "-", "k_0+k"),
    (r"\frac{\epsilon_0\mp eV/2}{\Gamma}", "+", "((epsilon_0-e*V/2)/(Gamma))"),   # 1403.8035 eq45
])
def test_sign_after_a_subscript_is_an_operator(tex, branch, expected):
    assert _a(tex, branch) == expected


@needs_reader_b
@pytest.mark.parametrize("tex, branch, expected", [
    (r"k_0\mp k", "+", "k_0-k"),
    (r"k_0\mp k", "-", "k_0+k"),
    (r"\frac{\epsilon_0\mp eV/2}{(\epsilon_0\mp eV/2)^2+\Gamma^2}", "+",
     "((epsilon_0-e*V/2)/((epsilon_0-e*V/2)**(2)+Gamma**(2)))"),
])
def test_sign_after_a_subscript_is_read_alike_by_both(tex, branch, expected):
    assert _both(tex, branch)[0] == expected


def test_sign_that_is_the_whole_subscript_still_picks_a_branch():
    assert _pick_branch("z_± + x_0∓y", "+") == "z_p + x_0 - y"
    assert _a(r"f_\pm + f_{\mp}", "-") == "f_m+f_p"


# 4. A letter right after a label superscript, an accent or a prime was glued
#    into that name (Sigma__ltG__A, C__cale, A__cal_primep_0).

GLUED = [
    (r"G^{R}\Sigma^{<}G^{A}", "G__R*Sigma__lt*G__A"),       # 1511.03276 eq61
    (r"\mathcal{C}eI_R^h", "C__cal*e*Isym_R__h"),           # 1403.8035 schottky1
    (r"(\mathcal{A}'p_0^2 +\mathcal{A}p^2)", "(A__cal_prime*p_0**(2)+A__cal*p**(2))"),   # 2207.00534 qfe23
    (r"\mathcal{A}'^2p_0^2", "A__cal_prime**(2)*p_0**(2)"),                              # 2207.00534 qfe22
    (r"x'y + \omega''t", "x_prime*y+omega_pprime*t"),
]


@pytest.mark.parametrize("tex, expected", GLUED)
def test_letter_after_a_label_accent_or_prime_is_a_new_factor(tex, expected):
    assert _a(tex) == expected


@needs_reader_b
@pytest.mark.parametrize("tex, expected", GLUED)
def test_letter_after_a_label_accent_or_prime_is_read_alike_by_both(tex, expected):
    assert _both(tex)[0] == expected


@pytest.mark.parametrize("tex, expected", [
    (r"\frac{\omega_{ll'} - \omega_{l'l}}{2}", "((omega_ll_prime-omega_l_primel)/(2))"),   # cond-mat_0608682
    (r"\delta_{ij'}\delta_{j'i'}", "delta_ij_prime*delta_j_primei_prime"),
])
def test_prime_inside_a_subscript_stays_in_the_name(tex, expected):
    assert _a(tex) == expected


@pytest.mark.parametrize("tex, expected", [
    (r"\Phi^I_k", "Phi__Isym_k"),                           # 1207.5808, 1312.1204
    (r"G^E + f_I", "G__Esym+f_Isym"),                       # f_I was f_I times 'sym'
])
def test_capital_e_or_i_as_a_whole_script(tex, expected):
    assert _a(tex) == expected


@needs_reader_b
def test_capital_i_as_a_whole_script_is_read_alike_by_both():
    assert _both(r"\Phi^I_k (u)", functions=("Phi__Isym_k",))[0] == "Phi__Isym_k(u)"


@pytest.mark.parametrize("tex", [
    r"\mathcal{R}e \, \chi(q,\nu)",       # 1111.5337 eq37: a calligraphic Re, not R times e
    r"\mathcal{I}m \, \chi_2^b(q,\nu)",   # 1111.5337 eq73
    r"{\cal I}m\,\chi",
])
def test_calligraphic_re_and_im_are_refused_not_split(tex):
    # once the accent no longer glues to the next letter, both readers would
    # agree on R__cal*e*chi: a misreading they share, so A refuses it
    assert _refused_by_a(tex, functions=("chi", "chi_2__b")).startswith("SOURCE_CHARACTER_UNSUPPORTED")


def test_accent_in_an_unbraced_superscript_stays_unread():
    # \sigma^\cV with \cV = \mathcal{V}: only word commands (\mathrm, \text) take
    # their group in a script, so this is not newly read as a power
    assert _refused_by_a(r"\sigma^\mathcal{V}").startswith("SOURCE_CHARACTER_UNSUPPORTED")


# 5. \frac{d}{dx} before anything but ( \left( [ { was read as d/(d x) = 1/x;
#    \Bigl( and the other sized brackets were not known as brackets.

SIZED = [
    (r"\frac{d}{dx}\Bigl( x^2 \Bigr)", "Diff((x**(2)),x,1)"),
    (r"\frac{d}{dx}\biggl[ x^2 \biggr]", "Diff((x**(2)),x,1)"),
    (r"\frac{d}{dx}\Big( x^3 \Big)", "Diff((x**(3)),x,1)"),
    (r"\frac{d}{dx}\,\left( x^2 \right)", "Diff((x**(2)),x,1)"),
]


@pytest.mark.parametrize("tex, expected", SIZED)
def test_derivative_before_a_sized_bracket(tex, expected):
    assert _a(tex) == expected


@pytest.mark.parametrize("tex, expected", [
    # 0804.3414 identityF: \left( \right) pairs inside the group
    (r"\frac{\partial}{\partial x}\left[\frac{F\left(x\right)}{\left(1+x\right)}\right]",
     "Diff((((F(x))/((1+x)))),x,1)"),
    (r"\frac{d}{dx}\Bigl( \left| x \right| + \left\{ x^2 \right\} \Bigr)", "Diff((Abs(x)+(x**(2))),x,1)"),
])
def test_derivative_group_with_nested_delimiters(tex, expected):
    assert _a(tex, functions=("F",)) == expected


@needs_reader_b
@pytest.mark.parametrize("tex, expected", SIZED)
def test_derivative_before_a_sized_bracket_is_read_alike_by_both(tex, expected):
    assert _both(tex)[0] == expected


@needs_reader_b
def test_derivative_of_a_product_in_bigl_is_read_alike_by_both():
    # 2108.11210 eq:app14, right side
    expression, _ = _both(r"-\frac{1}{\pi}\frac{d}{dq}\Bigl(\sin(\pi q)\Gamma(-q)\Bigr)",
                          functions=("Gamma",))
    assert expression == "-((1)/(pi))*Diff((sin(pi*q)*Gamma(-q)),q,1)"


@pytest.mark.parametrize("tex, functions", [
    (r"\frac{d}{dx} x^2", ()),
    (r"\frac{d}{dx} f(x)", ("f",)),
    (r"\frac{d}{dq}\frac{1}{\Gamma(q+1)}", ("Gamma",)),                 # 2108.11210 eq:app14
    (r"\frac{d}{dt}E^{(1)}", ()),                                       # 1511.03276 eq74
    (r"\frac{d}{d\varepsilon}\, \text{Re}\,\Sigma^{R}(\varepsilon)", ("Sigma__R",)),   # 1511.03276 eq42
])
def test_derivative_before_anything_else_is_refused_not_read_as_one_over_x(tex, functions):
    assert _refused_by_a(tex, functions).startswith("SOURCE_CHARACTER_UNSUPPORTED")


# A functional derivative dX/dY written with \delta was read by both readers as
# (delta X)/(delta Y) = X/Y: a shared misreading the comparison cannot catch.

@pytest.mark.parametrize("tex", [
    r"\frac{\delta W}{\delta A_\mu(x)}",                    # 1312.1204
    r"-\frac{\delta \mathcal{L}}{\delta A_i}",              # cond-mat_0512157
    r"\frac{\delta S_E}{\delta\Omega}",                     # 0903.3946 eq54
    r"{\delta W \over \delta A}",
])
def test_functional_derivative_is_refused(tex):
    assert _refused_by_a(tex).startswith("SOURCE_CHARACTER_UNSUPPORTED")


@pytest.mark.parametrize("tex, expected", [
    (r"\frac{\delta}{2}", "((delta)/(2))"),
    (r"\delta_{ab} x", "delta_ab*x"),
    (r"\frac{1}{\delta + 1}", "((1)/(delta+1))"),
])
def test_delta_as_a_symbol_still_reads(tex, expected):
    assert _a(tex) == expected


@pytest.mark.parametrize("tex", [r"\frac{\delta \rho}{\eta \omega}", r"\Delta T", r"\Delta\, \mu", r"\delta \hat{H}"])
def test_delta_before_a_name_is_refused(tex):
    # an increment (delta rho) or a product (delta times rho): both readers would multiply
    assert _refused_by_a(tex).startswith("SOURCE_CHARACTER_UNSUPPORTED")


# 6. A superscript that is one bracket group is a label, also when written
#    with \left( \right); a superscript (a)/(b) is not one group.

def test_left_right_parenthesized_superscript_is_a_label():
    assert _a(r"\dot{E}^{\left(2\right)}") == "Esym__dot__2"           # 1511.03276 eq74
    assert _a(r"\dot{E}^{(2)}") == "Esym__dot__2"


@needs_reader_b
def test_left_right_parenthesized_superscript_is_read_alike_by_both():
    assert _both(r"\dot{E}^{\left(2\right)}") == ("Esym__dot__2", "Esym__dot__2")


def test_superscript_of_two_groups_is_a_power():
    # 1403.8035 charge_noise: e^{(x)/(y)} was read as the label e__xy
    assert _a(r"e^{(\epsilon-\mu_p)/(k_B T_p)}") == "E**((epsilon-mu_p)/(k_B*T_p))"


@needs_reader_b
def test_superscript_of_two_groups_is_read_alike_by_both():
    expression, _ = _both(r"\left[1+e^{(\epsilon-\mu_p)/(k_B T_p)}\right]^{-1}")
    assert expression == "(1+E**((epsilon-mu_p)/(k_B*T_p)))**(-1)"


@needs_reader_b
def test_absolute_value_after_a_name_is_a_product():
    # e|V| is e times |V|; reader A used to glue them into one name 'eAbs'
    assert _a(r"e|V|") == "e*Abs(V)"
    assert _a(r"eV|V|") == "e*V*Abs(V)"
