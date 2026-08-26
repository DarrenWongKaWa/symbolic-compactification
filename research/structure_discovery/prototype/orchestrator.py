"""Decomposed architecture: observe → hypothesize → construct → verify.

Scientific state is replaced only on ZERO. UNKNOWN never promotes.
"""
from __future__ import annotations

from typing import Any, Optional

from research.structure_discovery.prototype.constructor import construct
from research.structure_discovery.prototype.discoverer import hypotheses_from_observations
from research.structure_discovery.prototype.hypothesis import StructureHypothesis
from research.structure_discovery.prototype.leakage import (
    assert_no_leakage,
    proposer_view,
)
from research.structure_discovery.prototype.observations import (
    observe_expression,
    proposer_safe_observations,
)
from research.structure_discovery.prototype.search_graph import HypothesisGraph
import sympy

from symbolic_compactification import (
    NONZERO,
    UNKNOWN,
    ZERO,
    parse_expression,
    verify_equivalent,
)
from symbolic_compactification.budgets import BudgetExceeded, run_with_budget
from symbolic_compactification.models import AdapterError


def _incomplete_reconstruction(current: str, closed: str, symbols, functions) -> str | None:
    """Skip a verify that is obviously not a reconstruction of E.

    Dropping Sum/Piecewise or collapsing to a tiny subexpression is a
    constructor failure, not a scientific state change. Skipping the
    probe-heavy UNKNOWN path is an engineering bound, not a verdict.
    """
    try:
        cur = parse_expression(current, symbols, functions=functions or None)
        cl = parse_expression(closed, symbols, functions=functions or None)
    except AdapterError:
        return "unparseable_closed"
    if cur.atoms(sympy.Sum) and not cl.atoms(sympy.Sum):
        return "dropped_sum"
    if cur.atoms(sympy.Piecewise) and not cl.atoms(sympy.Piecewise):
        # allowing identical-branch confluence to drop Piecewise is the
        # point of that constructor; only skip when the closed form is a
        # different head *and* much smaller.
        if sympy.count_ops(cl) + 1 < 0.5 * max(sympy.count_ops(cur), 1):
            # still allow the identical-value confluence constructor
            if not (isinstance(cur, sympy.Piecewise)):
                return "dropped_piecewise"
    cops, eops = sympy.count_ops(cl), sympy.count_ops(cur)
    if eops >= 8 and cops + 2 < 0.35 * eops:
        return "too_small"
    return None


def run_decomposed(
    item_public: dict,
    *,
    aggressive: bool = True,
    feature_mask: dict | None = None,
    max_hypotheses: int = 8,
    verify: bool = True,
) -> dict[str, Any]:
    assert_no_leakage(item_public)
    current = item_public["current"]
    symbols = item_public["symbols"]
    functions = item_public.get("functions") or []
    try:
        obs = proposer_safe_observations(
            observe_expression(current, symbols, functions)
        )
    except AdapterError as exc:
        return {
            "architecture": "observe→hypothesis→construct→verify",
            "n_hypotheses": 0,
            "hypothesis_types": [],
            "hypotheses": [],
            "n_zero": 0, "n_nonzero": 0, "n_unknown": 1,
            "false_promotion": False,
            "certified_closed": current,
            "certified_structured": current,
            "certified_definitions": {},
            "d_attempted": [], "d_certified": [],
            "graph": {"nodes": []},
            "observations_keys": [],
            "aggressive": aggressive,
            "parse_error": exc.code,
        }
    hyps = hypotheses_from_observations(
        obs, aggressive=aggressive, max_hypotheses=max_hypotheses,
        feature_mask=feature_mask,
    )
    graph = HypothesisGraph()
    certified_closed = current
    certified_structured = current
    certified_defs: dict = {}
    false_promotion = False
    n_zero = n_nz = n_unk = 0
    type_attempts: list[str] = []

    for i, hyp in enumerate(hyps):
        type_attempts.append(hyp.hypothesis_type)
        hid = f"H{i}"
        graph.add(
            node_id=hid, parent_id=None, state="PROPOSED",
            hypothesis=hyp.to_dict(), construction=None, verdict=None,
            d_level=hyp.d_level,
        )
        constructions = construct(hyp, current, symbols, functions)
        for j, cons in enumerate(constructions):
            cid = f"{hid}.C{j}"
            if not cons.constructable:
                graph.add(
                    node_id=cid, parent_id=hid, state="PROPOSED",
                    hypothesis=hyp.to_dict(), construction=cons.to_dict(),
                    verdict=None, d_level=hyp.d_level, notes=cons.notes,
                )
                continue
            graph.add(
                node_id=cid + ".ok", parent_id=hid, state="CONSTRUCTABLE",
                hypothesis=hyp.to_dict(), construction=cons.to_dict(),
                verdict=None, d_level=hyp.d_level, notes=cons.notes,
            )
            if not verify:
                continue
            reason = _incomplete_reconstruction(
                current, cons.closed_text, symbols, functions)
            if reason:
                graph.add(
                    node_id=cid + ".inc", parent_id=cid + ".ok",
                    state="CONSTRUCTABLE",
                    hypothesis=hyp.to_dict(), construction=cons.to_dict(),
                    verdict=None, d_level=hyp.d_level,
                    notes=f"incomplete:{reason}",
                )
                continue
            try:
                result = run_with_budget(
                    verify_equivalent,
                    (current, cons.closed_text, symbols),
                    kwargs={"functions": functions or None},
                    seconds=8.0,
                    operation="sd_verify",
                )
                verdict = result.verdict
            except BudgetExceeded:
                verdict = UNKNOWN
            except AdapterError:
                verdict = UNKNOWN
            if verdict == ZERO:
                n_zero += 1
                state = "ZERO_CERTIFIED"
                # Keep original current as the semantic identity; record
                # structured form as the certified scientific representation.
                certified_closed = cons.closed_text
                certified_structured = cons.structured_text
                certified_defs = cons.definitions
            elif verdict == NONZERO:
                n_nz += 1
                state = "NONZERO_REFUTED"
            else:
                n_unk += 1
                state = "UNKNOWN"
            graph.add(
                node_id=cid + ".v", parent_id=cid + ".ok", state=state,
                hypothesis=hyp.to_dict(), construction=cons.to_dict(),
                verdict=verdict, d_level=hyp.d_level, notes=cons.notes,
            )

    certified_nodes = graph.certified()
    d_certified = sorted({n.d_level for n in certified_nodes})
    d_attempted = sorted({h.d_level for h in hyps})
    return {
        "architecture": "observe→hypothesis→construct→verify",
        "n_hypotheses": len(hyps),
        "hypothesis_types": type_attempts,
        "hypotheses": [h.to_dict() for h in hyps],
        "n_zero": n_zero,
        "n_nonzero": n_nz,
        "n_unknown": n_unk,
        "false_promotion": false_promotion,
        "certified_closed": certified_closed,
        "certified_structured": certified_structured,
        "certified_definitions": certified_defs,
        "d_attempted": d_attempted,
        "d_certified": d_certified,
        "graph": graph.to_dict(),
        "observations_keys": sorted(obs.keys()),
        "aggressive": aggressive,
    }


def run_from_item(item: dict, **kwargs) -> dict[str, Any]:
    public = proposer_view(item)
    assert_no_leakage(public)
    hits = __import__(
        "research.structure_discovery.prototype.leakage",
        fromlist=["context_leaks_gold_names"],
    ).context_leaks_gold_names(item)
    result = run_decomposed(public, **kwargs)
    result["id"] = item.get("id")
    result["context_gold_name_hits"] = hits
    return result
