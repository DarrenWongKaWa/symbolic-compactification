"""Contracts for the experimental structure-discovery line.

Does not change engine 0.3.0 semantics. UNKNOWN is never success.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research.structure_discovery.prototype.build_benchmark import all_items, write_benchmark
from research.structure_discovery.prototype.constructor import construct
from research.structure_discovery.prototype.discoverer import hypotheses_from_observations
from research.structure_discovery.prototype.evaluator import score_run
from research.structure_discovery.prototype.hypothesis import StructureHypothesis
from research.structure_discovery.prototype.leakage import (
    assert_no_leakage,
    context_leaks_gold_names,
    proposer_view,
)
from research.structure_discovery.prototype.observations import observe_expression
from research.structure_discovery.prototype.orchestrator import run_decomposed
from symbolic_compactification import NONZERO, ZERO, parse_expression, verify_equivalent


def _syms(*names):
    return [{"name": n, "real": True} for n in names]


def test_hypothesis_rejects_unknown_type():
    try:
        StructureHypothesis(
            hypothesis_type="pretty_formula",
            target_subexpressions=["x"],
            claimed_structure="nope",
        )
    except ValueError:
        return
    raise AssertionError("unknown type must raise")


def test_observations_are_facts_only():
    obs = observe_expression(
        "K(n)*a(n) + K(n)*b(n)", _syms("n"), ["K", "a", "b"],
    )
    assert obs["facts_only"] is True
    assert any(r["count"] >= 2 for r in obs["repeated_subtrees"])
    blob = json.dumps(obs)
    assert "gold" not in blob.lower()


def test_positive_orbit_reconstructs_zero():
    pub = {
        "current": "F(n, m) + F(m, n)",
        "symbols": _syms("n", "m"),
        "functions": ["F"],
    }
    run = run_decomposed(pub)
    assert "permutation_orbit" in run["hypothesis_types"]
    assert run["n_zero"] >= 1, run["graph"]
    assert run["n_zero"] > 0
    for n in run["graph"]["nodes"]:
        if n.get("notes") == "equal_weight_orbit":
            assert n.get("closed") != "2*F(n, m)"
            assert n.get("closed") != "2*F(m, n)"


def test_divided_difference_detected():
    pub = {
        "current": "(f(x) - f(y))/(x - y)",
        "symbols": _syms("x", "y"),
        "functions": ["f"],
    }
    run = run_decomposed(pub)
    assert "divided_difference" in run["hypothesis_types"], run["hypothesis_types"]
    assert run["n_zero"] >= 1


def test_thermal_common_factor_named():
    pub = {
        "current": "A*polygamma(0, zP) + A*polygamma(0, zM)",
        "symbols": _syms("A", "zP", "zM"),
        "functions": [],
    }
    run = run_decomposed(pub)
    assert "repeated_kernel" in run["hypothesis_types"]
    assert run["n_zero"] >= 1


def test_positive_kernel_type_and_zero():
    pub = {
        "current": "K(n)*a(n) + K(n)*b(n)",
        "symbols": _syms("n"),
        "functions": ["K", "a", "b"],
        "scientific_context": ["generic"],
    }
    run = run_decomposed(pub)
    assert "repeated_kernel" in run["hypothesis_types"]
    assert run["false_promotion"] is False
    assert run["n_zero"] >= 1


def test_broken_orbit_equal_weight_is_nonzero():
    cur = "F(n, m) + 2*F(m, n)"
    syms = _syms("n", "m")
    r = verify_equivalent(cur, "F(n, m) + F(m, n)", syms, functions=["F"])
    assert r.verdict == NONZERO
    pub = {"current": cur, "symbols": syms, "functions": ["F"]}
    run = run_decomposed(pub, aggressive=True)
    # equal-weight orbit construction must not become state
    for n in run["graph"]["nodes"]:
        if n.get("notes") == "equal_weight_orbit" and n.get("verdict") == "ZERO":
            raise AssertionError("broken orbit was falsely certified")
    assert run["false_promotion"] is False


def test_distinct_poles_merge_nonzero():
    cur = "1/(x - a) + 1/(x - a - d)"
    syms = _syms("x", "a", "d")
    r = verify_equivalent(cur, "2/(x - a)", syms, functions=[])
    assert r.verdict == NONZERO
    pub = {"current": cur, "symbols": syms, "functions": []}
    run = run_decomposed(pub, aggressive=True)
    assert run["false_promotion"] is False
    # aggressive merge may be proposed but must not ZERO
    for n in run["graph"]["nodes"]:
        if n.get("hypothesis_type") == "identical_kernel_merge" and n.get("verdict") == "ZERO":
            raise AssertionError("distinct poles merged to ZERO")


def test_identical_piecewise_unifies():
    cur = "Piecewise((q, n > 0), (q, True))"
    pub = {"current": cur, "symbols": _syms("q", "n"), "functions": []}
    run = run_decomposed(pub)
    assert "confluent_representation" in run["hypothesis_types"]
    zeros = [n for n in run["graph"]["nodes"] if n.get("verdict") == "ZERO"]
    assert zeros, run["graph"]


def test_proposer_view_strips_gold():
    item = all_items()[0]
    view = proposer_view(item)
    assert_no_leakage(view)
    assert "gold_types" not in view
    assert "hidden_gold" not in view
    assert context_leaks_gold_names(item) == []


def test_no_gold_names_in_any_context():
    for it in all_items():
        hits = context_leaks_gold_names(it)
        assert hits == [], (it["id"], hits)
        view = proposer_view(it)
        assert_no_leakage(view)


def test_benchmark_symbols_not_reserved():
    from symbolic_compactification.models import HARD_RESERVED_NAMES, RESERVED_NAMES
    for it in all_items():
        names = {s["name"] for s in it["symbols"]}
        assert not (names & set(RESERVED_NAMES)), (it["id"], names & set(RESERVED_NAMES))
        fns = set(it.get("functions") or [])
        assert not (fns & set(HARD_RESERVED_NAMES)), (it["id"], fns)


def test_benchmark_has_pos_and_neg_and_held_out():
    items = all_items()
    assert any(i["polarity"] == "positive" for i in items)
    assert any(i["polarity"] == "negative" for i in items)
    assert any(i["split"] == "test" for i in items)
    assert any(i["split"] == "dev" for i in items)
    assert all("Guo" not in i["id"] and "guo" not in i["id"].lower() for i in items)
    assert any(i["tier"] == "S3" for i in items)


def test_write_benchmark_roundtrip():
    meta = write_benchmark()
    assert meta["n"] == len(all_items())
    assert meta["guo_in_test"] is False


def test_constructor_kernel_closed_zero():
    from research.structure_discovery.prototype.hypothesis import Auxiliary
    hyp = StructureHypothesis(
        hypothesis_type="repeated_kernel",
        target_subexpressions=["K(n)"],
        claimed_structure="repeat",
        proposed_auxiliaries=[Auxiliary("K0", "K(n)", "kernel")],
    )
    cons = construct(hyp, "K(n)*a(n)+K(n)*b(n)", _syms("n"), ["K", "a", "b"])
    assert cons and cons[0].constructable
    r = verify_equivalent(
        "K(n)*a(n)+K(n)*b(n)", cons[0].closed_text,
        _syms("n"), functions=["K", "a", "b"],
    )
    assert r.verdict == ZERO, (r.verdict, cons[0].closed_text)


def test_discoverer_mask_ablation():
    obs = observe_expression("F(n, m) + F(m, n)", _syms("n", "m"), ["F"])
    all_h = hypotheses_from_observations(obs)
    none = hypotheses_from_observations(
        obs, feature_mask={
            "repeated": False, "permutation": False, "denominators": False,
            "piecewise": False, "divided_difference": False, "families": False,
            "polygamma": False,
        },
    )
    assert any(h.hypothesis_type == "permutation_orbit" for h in all_h)
    assert none == []


def test_evaluator_negative_unsafe():
    item = {
        "id": "toy", "polarity": "negative",
        "gold_types": [], "forbidden_reconstructions": ["2/(x - a)"],
        "abstraction_level": "D2",
    }
    run = {
        "hypothesis_types": ["identical_kernel_merge"],
        "hypotheses": [],
        "n_zero": 1, "n_nonzero": 0, "n_unknown": 0,
        "false_promotion": False,
        "d_attempted": ["D2"], "d_certified": ["D2"],
        "graph": {"nodes": [{
            "state": "ZERO_CERTIFIED", "verdict": "ZERO",
            "closed": "2/(x - a)", "hypothesis_type": "identical_kernel_merge",
        }]},
    }
    sc = score_run(item, run)
    assert sc["axis_C_unsafe_merge"] is True
