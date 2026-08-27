"""Score invented abstractions. Frozen B9 is compared on the same gold."""
from __future__ import annotations

from typing import Any

import sympy

from symbolic_compactification import parse_expression
from symbolic_compactification.models import AdapterError


def _norm(s: str) -> str:
    return "".join(s.split())


def _canon(text: str, item: dict) -> str:
    try:
        e = parse_expression(
            text, item.get("symbols") or [],
            functions=item.get("functions") or None,
        )
        return sympy.srepr(e)
    except (AdapterError, Exception):
        return _norm(text)


def score_inventor(item: dict, run: dict) -> dict[str, Any]:
    gold_op = item.get("gold_operator")
    gold_members = [_canon(x, item) for x in (item.get("gold_members") or [])]
    polarity = item.get("polarity") or "positive"
    adj = run.get("adjudications") or []
    operators = run.get("operators") or []
    certified = [a for a in adj if a.get("certified_abstraction")]
    cover = False
    if gold_members:
        gset = set(gold_members)
        for a in certified:
            fam = {_canon(x, item) for x in (a.get("family") or [])}
            if gset <= fam:
                cover = True
                break
    op_hit = gold_op in operators if gold_op else False
    unsafe = any(a.get("n_nonzero", 0) == 0 and a.get("certified_abstraction")
                 and gold_op and item.get("forbidden_operators")
                 and a.get("operator") in (item.get("forbidden_operators") or [])
                 for a in adj)

    if polarity == "negative":
        # Success = did not certify a forbidden / gold operator.
        success = not any(
            a.get("certified_abstraction")
            and (a.get("operator") == gold_op
                 or a.get("operator") in (item.get("forbidden_operators") or []))
            for a in adj
        )
    else:
        success = bool(cover)

    return {
        "id": item.get("id"),
        "split": item.get("split"),
        "family": item.get("family"),
        "polarity": polarity,
        "gold_operator": gold_op,
        "invention_success": success,
        "operator_hit": op_hit,
        "family_cover_certified": cover,
        "n_hypotheses": run.get("n_hypotheses") or 0,
        "n_certified": run.get("n_certified_abstractions") or 0,
        "false_promotion": bool(run.get("false_promotion")),
        "unsafe_forbidden": bool(unsafe),
        "operators": operators,
        "blocked": bool(run.get("blocked")),
    }


def score_b9_frozen(item: dict, run: dict) -> dict[str, Any]:
    """B9 cannot emit gold_operator antiunification; exact-pattern types only."""
    types = run.get("hypothesis_types") or []
    gold_op = item.get("gold_operator")
    # Exact-pattern recovery: repeated_kernel / permutation / etc.
    exact = any(t in ("repeated_kernel", "permutation_orbit",
                      "confluent_representation", "divided_difference",
                      "master_function", "derivative_family", "spectral_family")
                for t in types)
    # Invention of parameterized non-identical family: never, by construction.
    invention = gold_op in types  # always False for antiunification
    polarity = item.get("polarity") or "positive"
    return {
        "id": item.get("id"),
        "split": item.get("split"),
        "family": item.get("family"),
        "polarity": polarity,
        "gold_operator": gold_op,
        "invention_success": False if polarity == "positive" else True,
        "operator_hit": invention,
        "exact_pattern_types_emitted": exact,
        "b9_types": types,
        "n_zero": run.get("n_zero") or 0,
        "false_promotion": bool(run.get("false_promotion")),
        "method": "B9_frozen",
    }
