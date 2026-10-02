"""Regressions for the coverage upgrade: displays with two relations,
Langreth shorthand, function-or-product readings, displays of one quantity,
definite integrals, and realness through definitions. Every new route must
stay fail-closed: a case it cannot settle is NOT_DECIDED, never a verdict."""
from __future__ import annotations

from pathlib import Path

import pytest

from symbolic_compactification.manybody.review import review

NOTES = Path(__file__).parent / "fixtures" / "notes"


def _review(tmp_path, body: str, name: str = "p") -> dict:
    tex = tmp_path / f"{name}.tex"
    tex.write_text("\\begin{document}\n" + body + "\n\\end{document}\n", encoding="utf-8")
    return review(tex, tmp_path / f"r_{name}")


def _decisions(result: dict) -> dict[str, str]:
    return {s["step"]: s["decision"] for s in result["steps"]}


def test_a_display_with_two_relations_is_split_and_the_equiv_names_a_constant(tmp_path):
    result = _review(tmp_path, r"""
In the wide-band limit
\begin{equation}\Sigma(\omega) = -i\Gamma, \qquad \Gamma \equiv \Gamma_L+\Gamma_R.\label{se}\end{equation}
\begin{equation}\frac{1}{\omega-\varepsilon-\Sigma(\omega)} = \frac{1}{\omega-\varepsilon+i\Gamma_L+i\Gamma_R}\label{g}\end{equation}
\begin{equation}\frac{1}{\omega-\varepsilon-\Sigma(\omega)} = \frac{1}{\omega-\varepsilon+i\Gamma_L}\label{bad}\end{equation}
""")
    assert _decisions(result) == {"g": "VALID", "bad": "INVALID"}


@pytest.mark.parametrize("display", [
    r"\sin(n\pi) = 0, \qquad n = 0, 1, 2, \dots",
    r"x^2 = x, \qquad x = 1",
    r"a^2 = b^2 \quad\text{for } a = b",
])
def test_a_condition_after_a_claim_is_never_split_off(tmp_path, display):
    """Dropping 'n = 0, 1, 2' would make sin(n pi) = 0 a false universal claim."""
    result = _review(tmp_path, r"\begin{equation}" + display + r"\label{c}\end{equation}")
    assert set(_decisions(result).values()) <= {"NOT_DECIDED"}


_LANGRETH = r"""
For contour functions $A,B$ with {product}, the Langreth rules give
\begin{{equation}}C^{{r}} = A^{{r}}\,B^{{r}}\label{{lr}}\end{{equation}}
\begin{{equation}}C^{{<}} = A^{{r}}\,B^{{<}}\label{{ll}}\end{{equation}}
"""


def test_langreth_shorthand_is_checked_against_the_stated_product(tmp_path):
    stated = _review(tmp_path, _LANGRETH.format(product="$C=A*B$"), "ab")
    assert _decisions(stated) == {"lr": "VALID", "ll": "INVALID"}      # the lesser rule drops A^< B^a
    reversed_ = _review(tmp_path, _LANGRETH.format(product="$C=B*A$"), "ba")
    # (BA)^r = B^r A^r: the claim is wrong only in the order of factors, which is
    # right for commuting scalars, so it is not refuted
    assert _decisions(reversed_)["lr"] == "NOT_DECIDED"
    unstated = _review(tmp_path, _LANGRETH.format(product="a convolution"), "none")
    assert set(_decisions(unstated).values()) == {"NOT_DECIDED"}       # order unknown: not drafted


def test_a_name_before_a_bracket_is_decided_only_when_both_readings_agree(tmp_path):
    result = _review(tmp_path, r"""
\begin{equation}h(a) + h(a) = 2h(a)\label{same}\end{equation}
\begin{equation}u(a) - u(a) = 1\label{wrong}\end{equation}
\begin{equation}K(a,b) + K(a,b) = 2K(a,b)\label{comma}\end{equation}
\begin{equation}g(x+y) = g\,x + g\,y\label{depends}\end{equation}
""")
    got = _decisions(result)
    # as a function the name is arbitrary, the paper's may be specific: never INVALID
    assert got["same"] == "VALID" and got["wrong"] == "NOT_DECIDED"
    # h(a)^2 is (h(a))^2 as a function but h*a^2 as a product: the readings differ
    assert got["comma"] == "VALID"            # K(a, b) cannot be a product
    assert got["depends"] == "NOT_DECIDED"    # true as a product, not as a function
    assert set(result["assumptions_to_confirm"]["function_or_product"]) >= {"h", "u", "g"}


def test_two_displays_of_one_quantity_are_compared_but_never_refuted(tmp_path):
    result = _review(tmp_path, r"""
\begin{equation}T(\omega) = \frac{4x\,y}{(x+y)^2}\label{t1}\end{equation}
\begin{equation}T(\omega) = \frac{4x\,y}{x^2+2x\,y+y^2}\label{t2}\end{equation}
\begin{equation}T(\omega) = \frac{2x\,y}{(x+y)^2}\label{t3}\end{equation}
""")
    got = _decisions(result)
    assert got["t1.vs.t2"] == "VALID"
    assert got["t2.vs.t3"] == "NOT_DECIDED"
    assert result["displays_disagree"] == ["t2.vs.t3"]


def test_time_integral_note(tmp_path):
    got = _decisions(review(NOTES / "time_integrals.tex", tmp_path / "r"))
    assert got == {"eq:phase": "VALID", "eq:switch": "VALID", "eq:moment": "INVALID",
                   "eq:drive": "VALID", "eq:adiabatic": "VALID", "eq:damped": "VALID"}


_S = [{"name": n, "real": True} for n in ("eps", "eta", "t1", "t", "t0", "w", "Om")] + [{"name": "a"}]


@pytest.mark.parametrize("integrand,claim,lower,upper,positive,status", [
    ("exp(-I*eps*t1)", "(1-exp(-I*eps*t))/(I*eps)", "0", "t", (), "CERTIFIED_BY_RULE"),
    ("exp(-I*eps*(t-t1))", "I*(exp(-I*eps*(t-t0))-1)/eps", "t0", "t", (), "CERTIFIED_BY_RULE"),
    ("t1*exp(a*t1)", "(t/a-1/a**2)*exp(a*t)", "0", "t", (), "NONZERO"),
    ("t1*exp(a*t1)", "(t/a-1/a**2)*exp(a*t)+1/a**2", "0", "t", (), "CERTIFIED_BY_RULE"),
    ("exp((I*eps-eta)*t1)", "1/(eta-I*eps)", "0", "oo", ("eta",), "CERTIFIED_BY_RULE"),
    ("exp((I*eps-eta)*t1)", "1/(eta+I*eps)", "0", "oo", ("eta",), "NONZERO"),
    ("exp(-eta*t1)*cos(w*t1)", "eta/(eta**2+w**2)", "0", "oo", ("eta",), "CERTIFIED_BY_RULE"),
    ("exp(eta*t1)", "exp(eta*t)/eta", "-oo", "t", (), "UNKNOWN"),          # sign of eta unstated
    ("exp(I*w*t1)", "I/w", "0", "oo", (), "UNKNOWN"),                     # does not converge
    ("1/(t1+a)", "log(t+a)-log(a)", "0", "t", (), "UNKNOWN"),             # not entire
    ("exp(-eta*t1)", "1/eta", "0", "t1", ("eta",), "UNKNOWN"),            # variable in a limit
])
def test_definite_integral_engine(integrand, claim, lower, upper, positive, status):
    from symbolic_compactification.manybody.definite import verify_definite_integral
    out = verify_definite_integral(integrand, claim, variable="t1", lower=lower, upper=upper,
                                   symbols=_S, positive=positive)
    assert out["status"] == status, out


def test_realness_counts_inside_a_definition(tmp_path):
    """|G(w)|^2 with G(w) = 1/(w - e + i g): the verdict depends on e and g
    being real, even though neither appears in the quote itself."""
    result = _review(tmp_path, r"""
Let $\omega$ be real and $g>0$.
\begin{equation}G(\omega) = \frac{1}{\omega-\varepsilon+ig}\label{def}\end{equation}
\begin{equation}|G(\omega)|^2 = \frac{1}{(\omega-\varepsilon)^2+g^2}\label{abs}\end{equation}
""")
    step = next(s for s in result["steps"] if s["step"] == "abs")
    assert step["decision"] == "NOT_DECIDED"
    assert any("REALNESS_UNSTATED" in w and "epsilon" in w for w in step["why_not_decided"])


@pytest.mark.parametrize("text,real,numbers", [
    (r"Let $\Gamma>0$ and real $\omega$.", {"omega"}, {"omega"}),
    (r"Let $\Gamma$ and real $\omega$.", {"omega"}, {"omega"}),
    (r"We take $\varepsilon$, $\Omega$ and $t$ real.", {"epsilon", "Omega", "t"}, {"epsilon", "Omega", "t"}),
    (r"the real dispersion $\varepsilon(k)$", {"epsilon", "k"}, set()),
])
def test_stated_realness_reads_lists_and_skips_functions(text, real, numbers):
    from symbolic_compactification.manybody.draft import _stated_numbers, _stated_realness
    assert set(_stated_realness(text)[0]) == real
    assert _stated_numbers(text) == numbers


def test_a_name_stated_real_and_used_bare_cannot_be_a_function(tmp_path):
    """epsilon is called real and written bare in the same quote, so
    epsilon(t - t_0) can only be a product there."""
    result = _review(tmp_path, r"""
We take $\varepsilon$, $t$ and $t_0$ real.
\begin{equation}\int_{t_0}^{t}dt_1\, e^{-i\varepsilon(t-t_1)} = \frac{i}{\varepsilon}\left(e^{-i\varepsilon(t-t_0)}-1\right)\label{sw}\end{equation}
""")
    assert _decisions(result) == {"sw": "VALID"}
    assert "epsilon" in result["assumptions_to_confirm"]["function_or_product"]
