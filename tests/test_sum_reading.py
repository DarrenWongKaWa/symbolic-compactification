"""Sums are read as structured objects by both readers and compared term by term."""
from __future__ import annotations

import pytest

from symbolic_compactification.manybody import dualread, run_card
from symbolic_compactification.manybody.latex import latex_to_plain

pytestmark = [pytest.mark.release_critical,
              pytest.mark.skipif(not dualread.available(), reason="antlr4 runtime missing")]


@pytest.mark.parametrize("tex, plain", [
    (r"\sum_{n=1}^{N} a_n b_n + c", "Sum(((a_n b_n)), (n, (1), (N))) + c"),
    (r"\sum_n a_n", "Sum(((a_n)), (n, sumlo_n, sumhi_n))"),
    (r"\sum_{j} \left[ x_j + y_j \right] z", "Sum((([x_j + y_j] z)), (j, sumlo_j, sumhi_j))"),
])
def test_reader_reads_a_sum_and_its_summand(tex, plain):
    assert "".join(latex_to_plain(tex).split()) == "".join(plain.split())


def test_a_sum_over_two_indices_is_left_unread():
    assert "\\sum" in latex_to_plain(r"\sum_{n,m} a_{nm}")


def _card(tmp_path, display, lhs, rhs, symbols):
    (tmp_path / "p.tex").write_text("\\begin{document}\n\\begin{equation}\n" + display
                                    + "\n\\end{equation}\n\\end{document}\n")
    return {"check": "identity", "symbols": symbols, "source_document": str(tmp_path / "p.tex"),
            "source": {"lhs": lhs, "rhs": rhs}}


def test_linearity_inside_a_sum_is_valid(tmp_path):
    card = _card(tmp_path, r"\sum_n 2\left( a_n + b_n \right) = 2\sum_n a_n + 2\sum_n b_n",
                 r"\sum_n 2\left( a_n + b_n \right)", r"2\sum_n a_n + 2\sum_n b_n", ["a_n", "b_n"])
    result = run_card(card, require_source=True)
    assert result["decision"] == "VALID", result.get("decision_blocked_by")


def test_a_sum_with_limits_on_both_sides_is_valid(tmp_path):
    card = _card(tmp_path, r"\sum_{n=0}^{\infty} \left(q^{n+1} + q^{n+2}\right) = \sum_{n=0}^{\infty} q^{n+1}\left(1 + q\right)",
                 r"\sum_{n=0}^{\infty} \left(q^{n+1} + q^{n+2}\right)", r"\sum_{n=0}^{\infty} q^{n+1}\left(1 + q\right)", ["q"])
    result = run_card(card, require_source=True)
    assert result["decision"] == "VALID", result.get("decision_blocked_by")


def test_a_name_with_the_index_in_its_subscript_stays_inside_the_sum(tmp_path):
    # a_n depends on n: sum_n a_n b_n is not a_n sum_n b_n
    card = _card(tmp_path, r"\sum_n a_n b_n = a_n \sum_n b_n", r"\sum_n a_n b_n", r"a_n \sum_n b_n", ["a_n", "b_n"])
    assert run_card(card, require_source=True)["decision"] == "NOT_DECIDED"


def test_the_summation_index_as_a_superscript_is_refused(tmp_path):
    # x^n is a power, Omega^n_{ab} a band label: the readers cannot tell
    card = _card(tmp_path, r"\sum_n \Omega^n_{ab} f_n = \sum_n f_n \Omega^n_{ab}",
                 r"\sum_n \Omega^n_{ab} f_n", r"\sum_n f_n \Omega^n_{ab}", ["f_n"])
    result = run_card(card, require_source=True)
    assert result["decision"] == "NOT_DECIDED"
    assert any("SUM_INDEX_AS_SUPERSCRIPT" in str(b) for b in result["decision_blocked_by"])


def test_a_false_step_with_sums_is_never_refuted(tmp_path):
    # a sum of products is not a product of sums, but sums are never evaluated: not decided
    card = _card(tmp_path, r"\sum_n a_n b_n = \sum_n a_n \sum_m b_m",
                 r"\sum_n a_n b_n", r"\sum_n a_n \sum_m b_m", ["a_n", "b_n", "b_m"])
    result = run_card(card, require_source=True)
    assert result["decision"] == "NOT_DECIDED"
