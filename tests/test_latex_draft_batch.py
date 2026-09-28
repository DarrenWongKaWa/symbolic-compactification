"""LaTeX quotes, cards built from source, strict mode, drafts and batches."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from symbolic_compactification import cli
from symbolic_compactification.manybody import run_card
from symbolic_compactification.manybody.batch import run_cards, to_html
from symbolic_compactification.manybody.draft import draft, split_top_level, steps_from_latex
from symbolic_compactification.manybody.fidelity import expand_sum_pm
from symbolic_compactification.manybody.latex import latex_to_plain, read_macros

pytestmark = pytest.mark.release_critical

CARDS = Path(__file__).resolve().parents[1] / "examples" / "cards"

TEX = r"""\documentclass{article}
\newcommand{\ii}{\mathrm{i}}
\newcommand{\Lor}[1]{\frac{2\Gamma}{#1^2+\Gamma^2}}
\begin{document}
\begin{align}
  \Lor{\omega} &= \frac{\ii}{\omega + \ii\Gamma} - \frac{\ii}{\omega - \ii\Gamma} \label{eq:split}\\
  &= \frac{2\ii}{\omega + \ii\Gamma}
\end{align}
\begin{equation}
  \frac{1}{1-x} = 1 + x + \mathcal{O}(x^2)
\end{equation}
\end{document}
"""


def test_latex_conversion():
    macros = read_macros(TEX)
    assert latex_to_plain(r"\Lor{\omega}", macros) == "((2 Gamma )/( omega ^(2)+ Gamma ^(2)))"
    assert latex_to_plain(r"\psi^{(1)}(z_{n,+})") == "psi1(z_np)"
    assert latex_to_plain(r"\rho^{(0)}_{n}").strip() == "rho__0_n"
    assert "E^(" in latex_to_plain(r"e^{-\beta x}")
    assert "z_p" in (e := expand_sum_pm(latex_to_plain(r"\sum_{\pm} \psi(z_{\pm})"))) and "z_m" in e


def test_split_top_level_keeps_comparisons():
    assert split_top_level("a = f(b = c) <= d") == ["a ", " f(b = c) <= d"]


def test_card_built_from_latex_is_valid_under_strict_mode():
    result = run_card(CARDS / "lorentzian_split_from_latex.yaml", require_source=True)
    assert result["decision"] == "VALID" and result["built_from_source"] == ["lhs", "rhs"]
    assert result["transcription_verified"]


def test_strict_mode_blocks_cards_without_quotes(monkeypatch):
    result = run_card(CARDS / "divided_difference_symmetry.yaml", require_source=True)
    assert result["verdict"] == "ZERO" and result["decision"] == "NOT_DECIDED"
    monkeypatch.setenv("SYMBOLIC_COMPACTIFICATION_REQUIRE_SOURCE", "1")
    assert run_card(CARDS / "divided_difference_symmetry.yaml")["decision"] == "NOT_DECIDED"


def test_draft_then_run(tmp_path):
    doc = tmp_path / "note.tex"
    doc.write_text(TEX)
    out = draft(doc, tmp_path / "cards")
    assert len(out["cards"]) == 3
    steps = steps_from_latex(TEX)
    assert [s["id"] for s in steps] == ["eq:split.1", "eq:split.2", "eq2"]
    (tmp_path / "cards" / "conventions.yaml").write_text(
        "symbols:\n  - {name: Gamma, positive: true}\n  - {name: omega}\n  - {name: x}\n")
    report = run_cards([tmp_path / "cards"], require_source=True)
    by = {r["card"]: r for r in report["cards"]}
    assert by["eq_split.1"]["decision"] == "VALID"
    assert by["eq_split.2"]["decision"] == "INVALID"            # the planted slip
    assert by["eq2"]["check"] == "remainder" and by["eq2"]["decision"] == "VALID"
    html = to_html(report)
    assert "INVALID" in html and "<table>" in html


def test_card_may_not_override_shared_conventions(tmp_path):
    (tmp_path / "conventions.yaml").write_text("symbols: [x]\nnotation: {e_nm: (e_n - e_m)}\n")
    card = tmp_path / "c.yaml"
    card.write_text("include: conventions.yaml\ncheck: identity\nsymbols: [x]\n"
                    "notation: {e_nm: (e_m - e_n)}\nlhs: x\nrhs: x\n")
    result = run_card(card)
    assert result["decision"] == "NOT_DECIDED"
    assert any("e_nm" in c for c in result["convention_conflicts"])


def test_batch_warns_about_inconsistent_conventions(tmp_path, capsys):
    for name, value in (("a", "(e_n - e_m)"), ("b", "(e_m - e_n)")):
        (tmp_path / f"{name}.yaml").write_text(
            f"check: identity\nsymbols: [x]\nnotation: {{e_nm: '{value}'}}\nlhs: x\nrhs: x\n")
    assert cli.main(["manybody", "steps", str(tmp_path), "--html", str(tmp_path / "r.html")]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["convention_warnings"][0]["convention"] == "notation e_nm"
    assert (tmp_path / "r.html").exists()
