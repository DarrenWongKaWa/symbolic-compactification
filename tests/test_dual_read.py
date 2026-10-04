"""A LaTeX quote counts as read only when two independent readers agree."""
from __future__ import annotations

import pytest
import sympy

from symbolic_compactification.manybody import dualread, run_card
from symbolic_compactification.models import AdapterError

pytestmark = [pytest.mark.release_critical,
              pytest.mark.skipif(not dualread.available(), reason="antlr4 runtime missing")]


def _agree(tex: str, a_text: str, callables=(), keep_i=False, branch=None):
    from symbolic_compactification.manybody.calculus import CalculusSpace
    import re
    names = sorted(set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", a_text)) - set(callables)
                   - {"I", "pi", "E", "exp", "log", "sqrt", "Abs", "cosh", "sinh", "tanh", "coth",
                      "sin", "cos", "Diff", "re", "im"})
    space = CalculusSpace([{"name": n, "real": False} for n in names] or ["unused_symbol"], list(callables))
    return dualread.require_agreement(tex, space.parse_expanded(a_text), macros={},
                                      callables=set(callables), keep_i=keep_i, branch=branch)


@pytest.mark.parametrize("tex, a_text", [
    (r"\frac{\Gamma_L}{2} + i\omega_n", "Gamma_L/2 + I*omega_n"),
    (r"v_{12}^a v_{21}^b + v_{12}^b v_{21}^a", "v_12__a*v_21__b + v_12__b*v_21__a"),
    (r"2\epsilon_{12}^2 g_{ab}", "2*epsilon_12**2*g_ab"),
    (r"\frac{e^2}{h} e^{i k x}", "e**2/h*exp(I*k*x)"),
    (r"E - \mu", "Esym - mu"),
    (r"\frac{1}{e^{\beta x}+1}", "1/(exp(beta*x) + 1)"),
    (r"\sqrt{\Gamma_L\Gamma_R}\left[ x + 1 \right]^2", "sqrt(Gamma_L*Gamma_R)*(x + 1)**2"),
    (r"\tilde{G}^{r} + \omega'", "G__tilde__r + omega_prime"),
    (r"\cosh^2(x/2)", "cosh(x/2)**2"),
])
def test_readings_that_agree(tex, a_text):
    assert "reader_b" in _agree(tex, a_text)


def test_a_name_called_as_a_function_agrees_with_a_function_reading():
    _agree(r"G(\omega) + \sigma(\mu)", "G(omega) + sigma(mu)", callables=("G", "sigma"))


def test_a_declared_product_takes_the_power_on_its_bracket_only():
    # \lambda (\phi\phi)^2 is lambda * (phi phi)^2, not (lambda phi phi)^2
    _agree(r"\lambda (\phi_i \phi_i)^2", "lamda*(phi_i*phi_i)**2")


def test_misreading_by_reader_a_is_refused():
    # d/dq read as a fraction of two products would give 1/q
    with pytest.raises(AdapterError) as err:
        _agree(r"\frac{d}{dq}\Bigl( q^2 \Bigr)", "q")
    assert err.value.code.startswith(dualread.READERS_DISAGREE)


def test_misreading_by_reader_b_is_refused():
    # SymPy takes 'ds' for one symbol (a line element); A reads d * s^2: no agreement
    with pytest.raises(AdapterError) as err:
        _agree(r"y\,ds^2", "y*d*s**2")
    assert err.value.code.startswith(dualread.READERS_DISAGREE)


def test_real_and_imaginary_parts_are_read_by_both():
    _agree(r"2\,\mathrm{Re}\,\Sigma^{R}(x)", "2*re(Sigma__R(x))", callables=("Sigma__R",))
    _agree(r"{\rm Im} \left[ x + y \right]", "im(x + y)")


def test_unreadable_by_reader_b_is_refused():
    with pytest.raises(AdapterError) as err:
        _agree(r"x \;\; \frac{", "x")
    assert err.value.code.startswith(dualread.SECOND_READER_FAILED)


def test_a_different_symbol_is_a_disagreement():
    with pytest.raises(AdapterError) as err:
        _agree(r"\Gamma_L + \Gamma_R", "Gamma_L + Gamma_L")
    assert dualread.READERS_DISAGREE in err.value.code


def test_branch_of_pm_is_read_by_both():
    _agree(r"x \pm y", "x + y", branch="+")
    _agree(r"x \pm y", "x - y", branch="-")


def test_card_built_from_a_quote_records_the_second_reading(tmp_path):
    (tmp_path / "p.tex").write_text(
        "\\begin{document}\n\\begin{equation}\n"
        "\\frac{1}{2}\\left(\\Gamma_L+\\Gamma_R\\right) = \\frac{\\Gamma_L}{2}+\\frac{\\Gamma_R}{2}\n"
        "\\end{equation}\n\\end{document}\n")
    card = {"check": "identity", "symbols": ["Gamma_L", "Gamma_R"],
            "source_document": str(tmp_path / "p.tex"),
            "source": {"lhs": r"\frac{1}{2}\left(\Gamma_L+\Gamma_R\right)",
                       "rhs": r"\frac{\Gamma_L}{2}+\frac{\Gamma_R}{2}"}}
    result = run_card(card)
    assert result["decision"] == "VALID"
    assert result["transcription"]["fields"]["lhs"]["reader_b"]


def test_card_whose_quote_the_readers_read_differently_is_not_decided(tmp_path, monkeypatch):
    # simulate a misreading by our reader (x^2 read as x): alone it would refute a true
    # step; with the second reader the quote is not read and nothing is decided
    from symbolic_compactification.manybody import fidelity
    real = fidelity.latex_to_plain
    monkeypatch.setattr(fidelity, "latex_to_plain", lambda text, macros=None: real(text, macros).replace("x^(2)", "x"))
    (tmp_path / "p.tex").write_text(
        "\\begin{document}\n\\begin{equation}\n"
        "x^2 + 1 = 1 + x\\cdot x\n"
        "\\end{equation}\n\\end{document}\n")
    card = {"check": "identity", "symbols": ["x"], "source_document": str(tmp_path / "p.tex"),
            "source": {"lhs": "x^2 + 1", "rhs": r"1 + x\cdot x"}}
    single = monkeypatch.context()
    with single as m:
        m.setattr(fidelity, "_second_reader", lambda *a, **k: None)
        alone = run_card(card)
        assert alone["decision"] == "INVALID", alone.get("decision_blocked_by")   # the misreading alone: a wrong verdict
    result = run_card(card)
    assert result["decision"] == "NOT_DECIDED"
    assert any(dualread.READERS_DISAGREE in str(b) for b in result["decision_blocked_by"])


@pytest.mark.parametrize("tex", [r"x\, 2^{99999999999}", r"2^{3^{20}} x", "1" * 300 + " x"])
def test_numbers_too_large_to_compute_are_refused_before_reading(tex):
    with pytest.raises(AdapterError) as err:
        dualread.check_size(tex)
    assert err.value.code == "QUOTE_NUMBER_TOO_LARGE"


def test_a_large_expansion_is_compared_under_the_budget():
    import time
    x, y, z, w, q = sympy.symbols("x y z w q")
    a = (x + y) ** 60 * (x + z) ** 60 * (x + w) ** 60 * q
    start = time.monotonic()
    assert not dualread._equal(a, (x + y) ** 60 * (x + z) ** 60 * (x + w) ** 60)
    assert time.monotonic() - start < 60


def test_a_word_script_is_part_of_the_name_for_both_readers():
    # TeX gives \text{GL} to the subscript whole, as it gives {\rm GL}
    _agree(r"\Psi_\text{GL} + N^\text{eq}", "Psi_GL + N__eq")


def test_index_pair_superscripts_are_not_read_as_powers(tmp_path):
    # L^{11}, L^{12}, L^{22} are transport coefficients and T^{00} a tensor component:
    # both readers would read powers (L^{12}/L^{11} = L, T^{00} = 1), so the quote is refused
    (tmp_path / "p.tex").write_text(
        "\\begin{document}\n\\begin{equation}\nQ = \\frac{L^{12}}{L^{11}}\n\\end{equation}\n"
        "\\begin{equation}\nS = L^{22} - \\frac{(L^{12})^2}{L^{11}}\n\\end{equation}\n"
        "\\begin{equation}\nE = T^{00} x\n\\end{equation}\n\\end{document}\n")
    for quote in (r"\frac{L^{12}}{L^{11}}", r"T^{00} x"):
        card = {"check": "identity", "symbols": ["L", "T", "x", "Q"], "source_document": str(tmp_path / "p.tex"),
                "source": {"rhs": quote}, "lhs": "Q"}
        reason = run_card(card)["transcription"]["fields"]["rhs"].get("reason", "")
        assert "SUPERSCRIPT_INDEX_OR_POWER" in reason, reason


def test_an_exponent_nested_three_braces_deep_is_still_the_exponential():
    _agree(r"e^{-2\pi\left(\left(\frac{\omega}{\omega_{0}}\right)+1\right)}",
           "exp(-2*pi*(omega/omega_0 + 1))")
