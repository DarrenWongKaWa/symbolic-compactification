"""Step ledger: 'Eq. X -> Eq. Y, using R', every formula quoted from the paper."""
from __future__ import annotations

import pytest
import yaml

from symbolic_compactification.manybody import dualread
from symbolic_compactification.manybody.cards import CardError
from symbolic_compactification.manybody.ledger import load_ledger, run_ledger

pytestmark = [pytest.mark.release_critical,
              pytest.mark.skipif(not dualread.available(), reason="antlr4 runtime missing")]

PAPER = r"""\documentclass{article}
\begin{document}
The matrix elements obey the metric-velocity relation
($v_{12}^a v_{21}^b + v_{12}^b v_{21}^a = 2\epsilon_{12}^2 g_{ab}$).
\begin{equation}
K_1 = v_{21}^a(v_{12}^b v_1^c + v_1^b v_{12}^c) + v_{12}^a(v_{21}^b v_1^c + v_1^b v_{21}^c)
\label{eq:k1}
\end{equation}
We reorganize $K_{1A}$ and apply the metric-velocity relation:
\begin{equation}
K_{1A} = v_1^c(v_{21}^a v_{12}^b + v_{12}^a v_{21}^b) + v_1^b(v_{21}^a v_{12}^c + v_{12}^a v_{21}^c)
 = 2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})
\label{eq:k1a}
\end{equation}
A misprinted variant reads
\begin{equation}
K_{1A}' = 2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})
\label{eq:bad}
\end{equation}
and a summed form is
\begin{equation}
S = \sum_n \left[ v_n^a (x_n + y_n) \right] = \sum_n \left[ v_n^a x_n + v_n^a y_n \right]
\label{eq:sum}
\end{equation}
\begin{equation}
R = \sum_n [x_n] + [y_n] = \sum_n [y_n] + [x_n]
\label{eq:twogroups}
\end{equation}
\begin{equation}
Q = \int dk \sum_n [x_n + y_n] = \sum_n [y_n + x_n]
\label{eq:extra}
\end{equation}
\end{document}
"""

K1 = r"v_{21}^a(v_{12}^b v_1^c + v_1^b v_{12}^c) + v_{12}^a(v_{21}^b v_1^c + v_1^b v_{21}^c)"
K1A = r"v_1^c(v_{21}^a v_{12}^b + v_{12}^a v_{21}^b) + v_1^b(v_{21}^a v_{12}^c + v_{12}^a v_{21}^c)"
METRIC = r"v_{12}^a v_{21}^b + v_{12}^b v_{21}^a = 2\epsilon_{12}^2 g_{ab}"


# what an assistant fills in once: the names, and that v_1^c(...) multiplies the bracket
CONVENTIONS = {
    "symbols": ["v_12__a", "v_12__b", "v_12__c", "v_21__a", "v_21__b", "v_21__c", "v_1__b",
                "v_1__c", "epsilon_12", "g_ab", "g_ac", "v_n__a", "x_n", "y_n"],
    "multiply": ["v_1__b", "v_1__c", "v_12__a", "v_21__a", "v_n__a"],
}


def _ledger(tmp_path, steps):
    # a step's type says whether the tool checks it; the tests' steps are algebra unless they say otherwise
    steps = [{**step, "type": step.get("type", "sum-termwise" if step.get("under") else "algebra")}
             if isinstance(step, dict) and "id" in step and step.get("type") != "omit" else
             {k: v for k, v in step.items() if k != "type"} for step in steps]
    (tmp_path / "paper.tex").write_text(PAPER)
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump(CONVENTIONS))
    path = tmp_path / "steps.yaml"
    path.write_text(yaml.safe_dump({"source_document": "paper.tex", "include": "conventions.yaml",
                                    "steps": steps}, sort_keys=False))
    return path


def _run(tmp_path, steps):
    out = run_ledger(_ledger(tmp_path, steps), tmp_path / "out")
    return {row["step"]: row for row in out["steps"]}


def test_regrouping_across_two_displays_is_exact(tmp_path):
    rows = _run(tmp_path, [{"id": "regroup", "from": {"display": "eq:k1", "quote": K1},
                            "to": {"display": "eq:k1a", "quote": K1A}}])
    assert rows["regroup"]["decision"] == "VALID"
    assert rows["regroup"]["holds_given"] == []


def test_step_using_a_stated_relation_holds_given_it(tmp_path):
    rows = _run(tmp_path, [{
        "id": "metric", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"display": "eq:k1a", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})"},
        "given": [{"quote": METRIC, "instances": [{}, {"b": "c"}]}],
        "note": "apply the metric-velocity relation"}])
    row = rows["metric"]
    assert row["decision"] == "VALID", row
    assert [g.get("rename", {}) for g in row["holds_given"]] == [{}, {"b": "c"}]
    assert row["certificate"]["method"] == "cofactors"


def test_same_step_without_the_relation_is_not_valid(tmp_path):
    rows = _run(tmp_path, [{
        "id": "metric", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"display": "eq:k1a", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})"}}])
    assert rows["metric"]["decision"] != "VALID"


def test_misprint_is_refuted_under_the_stated_relation(tmp_path):
    rows = _run(tmp_path, [{
        "id": "bad", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"display": "eq:bad", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})"},
        "given": [{"quote": METRIC, "instances": [{}, {"b": "c"}]}]}])
    row = rows["bad"]
    assert row["decision"] == "INVALID", row
    assert row["counterexample"]


def test_relation_not_in_the_paper_is_not_used(tmp_path):
    rows = _run(tmp_path, [{
        "id": "metric", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"display": "eq:k1a", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})"},
        "given": [{"quote": r"v_{12}^a v_{21}^b = \epsilon_{12}^2 g_{ab}", "instances": [{}, {"b": "c"}]}]}])
    row = rows["metric"]
    assert row["decision"] == "NOT_DECIDED"
    assert any("GIVEN_UNREADABLE" in w for w in row["why_not_decided"])


def test_relation_quoted_from_the_target_display_is_refused(tmp_path):
    rows = _run(tmp_path, [{
        "id": "circular", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"display": "eq:bad", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})"},
        "given": [{"quote": r"K_{1A}' = 2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})",
                   "display": "eq:bad"}]}])
    assert rows["circular"]["decision"] == "NOT_DECIDED"


def test_step_under_a_common_sum_is_checked_term_by_term(tmp_path):
    rows = _run(tmp_path, [{
        "id": "sum", "under": r"\sum_n",
        "from": {"display": "eq:sum", "quote": r"\left[ v_n^a (x_n + y_n) \right]"},
        "to": {"display": "eq:sum", "quote": r"\left[ v_n^a x_n + v_n^a y_n \right]"}}])
    assert rows["sum"]["decision"] == "VALID", rows["sum"]
    assert rows["sum"]["under"] == r"\sum_n"


def test_wrapper_that_is_not_in_front_of_the_quote_blocks_the_step(tmp_path):
    rows = _run(tmp_path, [{
        "id": "sum", "under": r"\int dk",
        "from": {"display": "eq:sum", "quote": r"\left[ v_n^a (x_n + y_n) \right]"},
        "to": {"display": "eq:sum", "quote": r"\left[ v_n^a x_n + v_n^a y_n \right]"}}])
    assert rows["sum"]["decision"] == "NOT_DECIDED"
    assert any("UNDER_NOT_BEFORE_QUOTE" in w for w in rows["sum"]["why_not_decided"])


def test_unknown_ledger_key_is_an_error(tmp_path):
    path = _ledger(tmp_path, [{"id": "s", "form": {"quote": "x"}, "to": {"quote": "x"}}])
    with pytest.raises(CardError, match="unknown key"):
        load_ledger(path)


def test_noncommuting_override_needs_a_reason(tmp_path):
    path = _ledger(tmp_path, [{"id": "s", "from": {"quote": K1}, "to": {"quote": K1A},
                               "noncommuting": False}])
    with pytest.raises(CardError, match="note"):
        load_ledger(path)


def test_review_with_a_ledger_decides_the_steps_in_the_reviewer_package(tmp_path):
    from symbolic_compactification.manybody.review import review
    ledger = _ledger(tmp_path, [
        {"id": "metric", "from": {"display": "eq:k1a", "quote": K1A},
         "to": {"display": "eq:k1a", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^b g_{ac})"},
         "given": [{"quote": METRIC, "instances": [{}, {"b": "c"}]}]},
        {"id": "bad", "from": {"display": "eq:k1a", "quote": K1A},
         "to": {"display": "eq:bad", "quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})"},
         "given": [{"quote": METRIC, "instances": [{}, {"b": "c"}]}]}])
    result = review(tmp_path / "paper.tex", tmp_path / "review", ledger=ledger)
    steps = {s["step"]: s for s in result["steps"]}
    assert steps["metric"]["decision"] == "VALID" and steps["metric"]["ledger"]
    assert len(steps["metric"]["holds_given"]) == 2
    assert steps["bad"]["decision"] == "INVALID"
    assert result["html"]
    html = open(result["html"], encoding="utf-8").read()
    assert "metric" in html


def test_two_bracket_groups_are_not_one_summand(tmp_path):
    rows = _run(tmp_path, [{"id": "two", "under": r"\sum_n",
                            "from": {"display": "eq:twogroups", "quote": "[x_n] + [y_n]"},
                            "to": {"display": "eq:twogroups", "quote": "[y_n] + [x_n]"}}])
    assert rows["two"]["decision"] == "NOT_DECIDED"
    assert any("UNDER_SCOPE_AMBIGUOUS" in w for w in rows["two"]["why_not_decided"])


def test_the_wrapper_must_be_the_whole_prefix_of_each_side(tmp_path):
    # the left side is \int dk \sum_n [...], the right side only \sum_n [...]
    rows = _run(tmp_path, [{"id": "extra", "under": r"\sum_n",
                            "from": {"display": "eq:extra", "quote": "[x_n + y_n]"},
                            "to": {"display": "eq:extra", "quote": "[y_n + x_n]"}}])
    assert rows["extra"]["decision"] == "NOT_DECIDED"
    assert any("UNDER_NOT_BEFORE_QUOTE" in w for w in rows["extra"]["why_not_decided"])


def test_relation_quoted_from_the_target_display_by_number_is_refused(tmp_path):
    rows = _run(tmp_path, [{
        "id": "circular", "from": {"display": "eq:k1a", "quote": K1A},
        "to": {"quote": r"2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})"},
        "given": [{"quote": r"K_{1A}' = 2\epsilon_{12}^2 (v_1^c g_{ab} + v_1^c g_{ac})", "display": "#3"}]}])
    assert rows["circular"]["decision"] == "NOT_DECIDED"
    assert any("GIVEN_FROM_THE_STEP_DISPLAY" in w for w in rows["circular"]["why_not_decided"])


def test_renaming_a_letter_that_is_not_only_an_index_is_refused(tmp_path):
    from symbolic_compactification.manybody.fidelity import rename_indices
    from symbolic_compactification.models import AdapterError
    for tex, rename in [(r"x^{b} = b", {"b": "c"}), (r"e^{-\beta b} g_{ab}", {"b": "c"}),
                        (r"g_{\mathrm{max}} = a", {"a": "z"})]:
        with pytest.raises(AdapterError):
            rename_indices(tex, rename)
    assert rename_indices(r"v_{12}^a v_{21}^b = 2\epsilon_{12}^2 g_{ab}", {"b": "c"}) \
        == r"v_{12}^a v_{21}^c = 2\epsilon_{12}^2 g_{ac}"


def test_malformed_instances_are_an_error(tmp_path):
    path = _ledger(tmp_path, [{"id": "odd", "from": {"quote": K1A}, "to": {"quote": K1},
                               "given": [{"quote": METRIC, "instances": "not a list"}]}])
    with pytest.raises(CardError, match="instances"):
        load_ledger(path)


def test_a_step_that_crashes_does_not_stop_the_ledger(tmp_path, monkeypatch):
    from symbolic_compactification.manybody import cards
    real = cards.run_card

    def flaky(path, **kw):
        if "odd" in str(path):
            raise RuntimeError("boom")
        return real(path, **kw)
    monkeypatch.setattr(cards, "run_card", flaky)
    rows = _run(tmp_path, [
        {"id": "odd", "from": {"display": "eq:k1", "quote": K1}, "to": {"display": "eq:k1a", "quote": K1A}},
        {"id": "regroup", "from": {"display": "eq:k1", "quote": K1}, "to": {"display": "eq:k1a", "quote": K1A}}])
    assert rows["odd"]["decision"] == "NOT_DECIDED"
    assert rows["odd"]["why_not_decided"][0].startswith("STEP_ERROR")
    assert rows["regroup"]["decision"] == "VALID"


def test_include_outside_the_ledger_directory_is_refused(tmp_path):
    path = _ledger(tmp_path, [{"id": "s", "from": {"quote": K1}, "to": {"quote": K1A}}])
    data = yaml.safe_load(path.read_text())
    data["include"] = "../outside.yaml"
    path.write_text(yaml.safe_dump(data))
    with pytest.raises(CardError, match="include"):
        load_ledger(path)


def test_both_sides_of_one_display_keep_the_one_sided_guard(tmp_path):
    # 1/2 lambda^k E_k = 1/2 lambda^k hbar omega may be how the paper defines E_k
    paper = PAPER.replace("\\end{document}", "\\begin{equation}\n\\frac{1}{2} \\lambda^{k} E_k = "
                          "\\frac{1}{2} \\lambda^{k} \\hbar \\omega\n\\label{eq:r}\n\\end{equation}\n\\end{document}")
    path = _ledger(tmp_path, [{"id": "e", "from": {"display": "eq:r", "quote": r"\frac{1}{2} \lambda^{k} E_k"},
                               "to": {"display": "eq:r", "quote": r"\frac{1}{2} \lambda^{k} \hbar \omega"}}])
    (tmp_path / "paper.tex").write_text(paper)
    conventions = dict(CONVENTIONS, symbols=CONVENTIONS["symbols"] + ["lamda__k", "Esym_k", "hbar", "omega"])
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump(conventions))
    row = {r["step"]: r for r in run_ledger(path, tmp_path / "out")["steps"]}["e"]
    assert row["decision"] == "NOT_DECIDED"
    assert any(w.startswith("ONE_SIDED_SYMBOL") for w in row["why_not_decided"])


def test_wrapper_glued_to_the_quote_in_the_source(tmp_path):
    # \sum_{n=1}^{\infty}\frac{...}: no space between the wrapper and the summand
    paper = PAPER.replace("\\end{document}", "\\begin{equation}\nT = \\sum_{n=1}^{\\infty}\\frac{2 x_n}{4} "
                          "= \\sum_{n=1}^{\\infty}\\frac{x_n}{2}\n\\label{eq:glued}\n\\end{equation}\n\\end{document}")
    path = _ledger(tmp_path, [{"id": "glued", "under": r"\sum_{n=1}^{\infty}",
                               "from": {"display": "eq:glued", "quote": r"\frac{2 x_n}{4}"},
                               "to": {"display": "eq:glued", "quote": r"\frac{x_n}{2}"}}])
    (tmp_path / "paper.tex").write_text(paper)
    row = {r["step"]: r for r in run_ledger(path, tmp_path / "out")["steps"]}["glued"]
    assert row["decision"] == "VALID", row


def test_ledger_conventions_may_add_a_stated_sign_to_a_drafted_symbol(tmp_path):
    from symbolic_compactification.manybody.cards import resolve_includes
    (tmp_path / "drafted.yaml").write_text(yaml.safe_dump({"symbols": [
        {"name": "A", "realness": "unstated", "stated": "realness not stated"}, {"name": "B"}]}))
    (tmp_path / "ledger.yaml").write_text(yaml.safe_dump({"symbols": [{"name": "A", "positive": True}]}))
    card, conflicts = resolve_includes({"check": "identity", "include": ["drafted.yaml", "ledger.yaml"]}, tmp_path)
    assert conflicts == []
    assert {"name": "A", "positive": True} in card["symbols"]
    # contradicting a stated attribute is still a conflict
    (tmp_path / "drafted.yaml").write_text(yaml.safe_dump({"symbols": [{"name": "A", "positive": True}]}))
    (tmp_path / "ledger.yaml").write_text(yaml.safe_dump({"symbols": [{"name": "A", "real": False}]}))
    _, conflicts = resolve_includes({"check": "identity", "include": ["drafted.yaml", "ledger.yaml"]}, tmp_path)
    assert conflicts


def test_a_cited_definition_defines_the_named_quantity(tmp_path):
    paper = PAPER.replace("\\end{document}", "We write $\\Omega^2 \\equiv a_0 + a_1$.\n\\begin{equation}\n"
                          "\\Omega^2 = a_0 + a_1 = x + y\n\\label{eq:om}\n\\end{equation}\n"
                          "with $a_0 = x$ and $a_1 = y$.\n\\end{document}")
    path = _ledger(tmp_path, [{"id": "om", "from": {"display": "eq:om", "quote": "a_0 + a_1"},
                               "to": {"display": "eq:om", "quote": "x + y"},
                               "given": [{"quote": "a_0 = x"}, {"quote": "a_1 = y"}]}])
    (tmp_path / "paper.tex").write_text(paper)
    conventions = dict(CONVENTIONS, symbols=CONVENTIONS["symbols"] + ["a_0", "a_1", "x", "y"])
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump(conventions))
    row = {r["step"]: r for r in run_ledger(path, tmp_path / "out")["steps"]}["om"]
    assert row["decision"] == "VALID", row


def test_a_relation_written_with_equiv_can_be_cited(tmp_path):
    from symbolic_compactification.manybody.fidelity import given_relations
    (tmp_path / "p.tex").write_text("\\begin{document}\nLet $g \\equiv a + b$.\n\\end{document}\n")
    records = given_relations({"source_document": str(tmp_path / "p.tex"), "given": [{"quote": r"g \equiv a + b"}]},
                              None, symbols=["g", "a", "b"], functions=[], definitions={})
    assert records[0]["status"] == "MATCH" and records[0]["lhs"] == "g"


def test_wrapper_followed_by_a_backslash_space(tmp_path):
    paper = PAPER.replace("\\end{document}", "\\begin{equation}\nU = - \\sum_{j=1}^\\infty \\ \\frac{2 x_j}{4} "
                          "= - \\sum_{j=1}^\\infty \\ \\frac{x_j}{2}\n\\label{eq:bs}\n\\end{equation}\n\\end{document}")
    path = _ledger(tmp_path, [{"id": "bs", "under": r"- \sum_{j=1}^\infty",
                               "from": {"display": "eq:bs", "quote": r"\frac{2 x_j}{4}"},
                               "to": {"display": "eq:bs", "quote": r"\frac{x_j}{2}"}}])
    (tmp_path / "paper.tex").write_text(paper)
    conventions = dict(CONVENTIONS, symbols=CONVENTIONS["symbols"] + ["x_j"])
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump(conventions))
    row = {r["step"]: r for r in run_ledger(path, tmp_path / "out")["steps"]}["bs"]
    assert row["decision"] == "VALID", row


def test_steps_that_are_not_algebra_are_left_to_the_reviewer(tmp_path):
    rows = _run(tmp_path, [
        {"id": "regroup", "type": "algebra", "from": {"display": "eq:k1", "quote": K1},
         "to": {"display": "eq:k1a", "quote": K1A}},
        {"id": "an-integral", "type": "integral", "from": {"display": "eq:k1", "quote": K1},
         "to": {"display": "eq:k1a", "quote": K1A}}])
    assert rows["regroup"]["decision"] == "VALID" and rows["regroup"]["type"] == "algebra"
    assert rows["an-integral"]["decision"] == "NEEDS_REVIEWER" and rows["an-integral"]["type"] == "integral"
    assert rows["an-integral"]["why_not_decided"] == []


def test_a_step_without_a_known_type_is_an_error(tmp_path):
    path = _ledger(tmp_path, [{"id": "s", "type": "omit", "from": {"quote": K1}, "to": {"quote": K1A}}])
    with pytest.raises(CardError, match="type"):
        load_ledger(path)
    path = _ledger(tmp_path, [{"id": "s", "type": "guess", "from": {"quote": K1}, "to": {"quote": K1A}}])
    with pytest.raises(CardError, match="type"):
        load_ledger(path)


NAMED = r"""\documentclass{article}
\begin{document}
The total is
\begin{equation}
S = x + y
\label{eq:s}
\end{equation}
and it enters as
\begin{equation}
W = S (x - y) = S x - S y
\label{eq:w}
\end{equation}
\begin{equation}
V = S - x
\label{eq:v}
\end{equation}
\begin{equation}
V = y
\label{eq:v2}
\end{equation}
\end{document}
"""


def _named_run(tmp_path, steps):
    (tmp_path / "paper.tex").write_text(NAMED)
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump({"symbols": ["x", "y", "S"], "multiply": ["S"]}))
    path = tmp_path / "steps.yaml"
    path.write_text(yaml.safe_dump({"source_document": "paper.tex", "include": "conventions.yaml",
                                    "steps": steps}, sort_keys=False))
    return {r["step"]: r for r in run_ledger(path, tmp_path / "out")["steps"]}


def test_a_named_quantity_left_free_does_not_block_a_valid_step(tmp_path):
    # S (x - y) = S x - S y holds for every S, so for the paper's S = x + y too
    rows = _named_run(tmp_path, [{"id": "w", "type": "algebra", "from": {"display": "eq:w", "quote": "S (x - y)"},
                                  "to": {"display": "eq:w", "quote": "S x - S y"}}])
    assert rows["w"]["decision"] == "VALID", rows["w"]


def test_a_named_quantity_still_withholds_a_refutation(tmp_path):
    # S - x = y holds with the paper's S = x + y, which the step does not cite:
    # refuting it with S free would be wrong, so it is not decided
    rows = _named_run(tmp_path, [{"id": "v", "type": "algebra", "from": {"display": "eq:v", "quote": "S - x"},
                                  "to": {"display": "eq:v2", "quote": "y"}}])
    assert rows["v"]["decision"] == "NOT_DECIDED"
    assert any("NAMED_QUANTITY" in w for w in rows["v"]["why_not_decided"])


MACRO_PAPER = r"""\documentclass{article}
\newcommand{\rpq}{r_{pq}}
\begin{document}
For every pair of leads, $\rpq = a_{p} b_{q}$.
\begin{equation}
X = r_{LR} + c
\label{eq:x}
\end{equation}
\begin{equation}
Y = a_{L} b_{R} + c
\label{eq:y}
\end{equation}
\end{document}
"""


def _macro_run(tmp_path, given):
    (tmp_path / "paper.tex").write_text(MACRO_PAPER)
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump(
        {"symbols": ["r_LR", "r_pq", "a_L", "a_p", "b_R", "b_q", "c"]}))
    (tmp_path / "steps.yaml").write_text(yaml.safe_dump({
        "source_document": "paper.tex", "include": "conventions.yaml",
        "steps": [{"id": "rename", "type": "algebra", "from": {"display": "eq:x", "quote": "r_{LR} + c"},
                   "to": {"display": "eq:y", "quote": "a_{L} b_{R} + c"}, "given": given}]}, sort_keys=False))
    return run_ledger(tmp_path / "steps.yaml", tmp_path / "out")["steps"][0]


def test_index_rename_reaches_inside_a_macro(tmp_path):
    # \rpq expands to r_{pq}; the instance p -> L, q -> R must rename it, not leave r_pq
    row = _macro_run(tmp_path, [{"quote": r"\rpq = a_{p} b_{q}", "instances": [{"p": "L", "q": "R"}]}])
    assert row["decision"] == "VALID", row


def test_a_rename_that_changes_nothing_is_refused(tmp_path):
    row = _macro_run(tmp_path, [{"quote": r"\rpq = a_{p} b_{q}", "instances": [{"s": "L"}]}])
    assert row["decision"] == "NOT_DECIDED", row
    assert any("GIVEN_RENAME_CHANGED_NOTHING" in w for w in row["why_not_decided"]), row


INCREMENT_PAPER = r"""\documentclass{article}
\begin{document}
\begin{equation}
X = \frac{\Delta T}{\Delta V}
\label{eq:a}
\end{equation}
\begin{equation}
Y = \frac{T}{V}
\label{eq:b}
\end{equation}
\begin{equation}
Z = \Delta \mu + \Delta_0 T
\label{eq:c}
\end{equation}
\end{document}
"""


def test_an_increment_is_not_read_as_a_product(tmp_path):
    # Delta T / Delta V is not T / V: both readers would multiply by Delta and cancel it
    (tmp_path / "paper.tex").write_text(INCREMENT_PAPER)
    (tmp_path / "conventions.yaml").write_text(yaml.safe_dump({"symbols": ["T", "V", "Delta", "mu", "Delta_0"]}))
    (tmp_path / "steps.yaml").write_text(yaml.safe_dump({
        "source_document": "paper.tex", "include": "conventions.yaml",
        "steps": [{"id": "ratio", "type": "algebra", "from": {"display": "eq:a", "quote": r"\frac{\Delta T}{\Delta V}"},
                   "to": {"display": "eq:b", "quote": r"\frac{T}{V}"}},
                  {"id": "chem", "type": "algebra", "from": {"display": "eq:c", "quote": r"\Delta \mu + \Delta_0 T"},
                   "to": {"display": "eq:c", "quote": r"\Delta \mu + \Delta_0 T"}}]}, sort_keys=False))
    rows = {r["step"]: r for r in run_ledger(tmp_path / "steps.yaml", tmp_path / "out")["steps"]}
    assert rows["ratio"]["decision"] == "NOT_DECIDED", rows["ratio"]
    assert rows["chem"]["decision"] == "NOT_DECIDED", rows["chem"]


def test_a_subscripted_delta_is_still_a_name():
    from symbolic_compactification.manybody.latex import latex_to_plain
    assert "\\" not in latex_to_plain(r"\Delta_0 T + \Delta^2 + \delta_{ij} x")


def test_reviewer_page_lists_the_steps_left_to_the_reviewer(tmp_path):
    # an integral, limit, approximation or definition step is not checked; the page must still show it
    from symbolic_compactification.manybody.review import review
    ledger = _ledger(tmp_path, [
        {"id": "regroup", "from": {"display": "eq:k1", "quote": K1}, "to": {"display": "eq:k1a", "quote": K1A}},
        {"id": "the-integral", "type": "integral", "from": {"display": "eq:extra", "quote": r"\int dk \sum_n [x_n + y_n]"},
         "to": {"display": "eq:extra", "quote": r"\sum_n [y_n + x_n]"}}])
    result = review(tmp_path / "paper.tex", tmp_path / "review", ledger=ledger)
    assert result["counts"]["NEEDS_REVIEWER"] == 1
    html = open(result["html"], encoding="utf-8").read()
    assert "Steps for the reviewer" in html
    assert "the-integral" in html and "integral" in html
    md = (tmp_path / "review" / "reviewer-verification-package" / "REVIEWER_SUMMARY.md").read_text(encoding="utf-8")
    assert "the-integral" in md
