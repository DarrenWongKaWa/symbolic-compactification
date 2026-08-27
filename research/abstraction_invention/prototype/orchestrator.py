"""Layer 2 loop. Frozen B9 is imported, never copied or edited."""
from __future__ import annotations

from research.abstraction_invention.prototype.inventor import invent_from_expression
from research.abstraction_invention.prototype.obligations import adjudicate_hypothesis
from research.abstraction_invention.prototype.schema import AbstractionHypothesis
from research.structure_discovery.prototype.baselines import run_b9
from research.structure_discovery.prototype.leakage import (
    assert_no_leakage,
    proposer_view,
)


def run_inventor(item: dict) -> dict:
    pub = proposer_view(item)
    assert_no_leakage(pub, extra_forbidden=(
        "gold_operator", "gold_template", "gold_members", "gold_family",
    ))
    current = pub["current"]
    symbols = pub["symbols"]
    functions = pub.get("functions") or []
    hyps = invent_from_expression(current, symbols, functions)
    adj = [adjudicate_hypothesis(h, symbols, functions) for h in hyps]
    certified = [a for a in adj if a["certified_abstraction"]]
    return {
        "method": "M_lgg",
        "n_hypotheses": len(hyps),
        "operators": [h.operator for h in hyps],
        "n_certified_abstractions": len(certified),
        "false_promotion": False,
        "adjudications": adj,
        "best": certified[0] if certified else (adj[0] if adj else None),
    }


def run_b9_frozen(item: dict) -> dict:
    """Immutable Layer-1 baseline. Do not pass gold."""
    run = run_b9(item)
    run["method"] = "B9_frozen"
    return run


def llm_unavailable() -> dict:
    return {
        "method": "M_llm",
        "blocked": True,
        "reason": "no usable LLM API (ANTHROPIC_AUTH_TOKEN len=35; no OpenAI/xAI/Gemini)",
        "n_hypotheses": 0,
        "operators": [],
        "n_certified_abstractions": 0,
        "false_promotion": False,
    }
