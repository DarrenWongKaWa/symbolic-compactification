"""Layer-2 anti-unification contracts. Does not modify frozen B9."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.abstraction_invention.prototype.antiunify import lgg_pair
from research.abstraction_invention.prototype.build_benchmark import all_items, write_benchmark
from research.abstraction_invention.prototype.inventor import invent_from_expression
from research.abstraction_invention.prototype.orchestrator import run_inventor, run_b9_frozen
from research.abstraction_invention.prototype.evaluator import score_inventor, score_b9_frozen
from research.structure_discovery.prototype.leakage import proposer_view, assert_no_leakage
from symbolic_compactification import parse_expression, ZERO, verify_equivalent


def _s(*names):
    return [{"name": n, "real": True} for n in names]


def test_lgg_born_not_identical_subtree():
    e = parse_expression(
        "V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        _s("p", "q"), functions=["V", "G0"],
    )
    a, b = e.args
    g = lgg_pair(a, b)
    assert g.useful(), g
    assert g.n_holes == 1, g.substitutions
    t = str(g.template)
    assert "V" in t and "G0" in t
    assert "theta" in t


def test_inventor_recovers_born():
    hyps = invent_from_expression(
        "V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        _s("p", "q"), ["V", "G0"],
    )
    assert any(h.operator == "antiunification" for h in hyps)
    assert any("G0" in h.template and "theta" in h.template for h in hyps)


def test_inventor_rejects_unrelated_named_product():
    hyps = invent_from_expression(
        "V(p)*G0(p)*V(p) + W(q)*H0(q)*W(q)",
        _s("p", "q"), ["V", "G0", "W", "H0"],
    )
    bornish = [h for h in hyps if h.operator == "antiunification"
               and "V" in h.template and "W" in h.template]
    assert bornish == []
    item = {
        "id": "neg", "current": "V(p)*G0(p)*V(p) + W(q)*H0(q)*W(q)",
        "symbols": _s("p", "q"), "functions": ["V", "G0", "W", "H0"],
        "scientific_context": ["generic"],
        "gold_operator": "antiunification", "gold_members": [],
        "forbidden_operators": ["antiunification"],
        "polarity": "negative", "split": "dev", "family": "A",
    }
    sc = score_inventor(item, run_inventor(item))
    assert sc["invention_success"] is True


def test_obligation_zero_on_born():
    item = {
        "id": "toy", "current": "V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        "symbols": _s("p", "q"), "functions": ["V", "G0"],
        "scientific_context": ["generic"],
        "gold_operator": "antiunification",
        "gold_members": ["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        "polarity": "positive", "split": "dev", "family": "A",
    }
    run = run_inventor(item)
    sc = score_inventor(item, run)
    assert run["false_promotion"] is False
    assert sc["family_cover_certified"] is True, run


def test_frozen_b9_misses_born_invention():
    item = {
        "id": "toy", "current": "V(p)*G0(p)*V(p) + V(q)*G0(q)*V(q)",
        "symbols": _s("p", "q"), "functions": ["V", "G0"],
        "scientific_context": ["generic"],
        "gold_operator": "antiunification",
        "gold_members": ["V(p)*G0(p)*V(p)", "V(q)*G0(q)*V(q)"],
        "polarity": "positive", "split": "dev", "family": "A",
        "tier": "S1", "task": "abstraction_invention",
    }
    b9 = run_b9_frozen(item)
    sc = score_b9_frozen(item, b9)
    assert sc["invention_success"] is False
    assert "antiunification" not in (b9.get("hypothesis_types") or [])


def test_benchmark_no_guo_in_test_and_no_leakage():
    write_benchmark()
    items = all_items()
    assert any(i["split"] == "test" for i in items)
    assert all("guo" not in i["id"].lower() for i in items)
    for it in items:
        view = proposer_view(it)
        assert_no_leakage(view, extra_forbidden=("gold_operator", "gold_members", "gold_template"))
        assert "gold_template" not in view
        ctx = " ".join(it.get("scientific_context") or [])
        for n in (it.get("hidden_gold") or {}).get("aux_names") or []:
            assert n not in ctx


def test_piecewise_unequal_is_confluence_not_identical_fold():
    hyps = invent_from_expression(
        "Piecewise((K(n, m), Ne(n, m)), (K(n, n), True))",
        _s("n", "m"), ["K"],
    )
    assert any(h.operator == "confluence" for h in hyps)
