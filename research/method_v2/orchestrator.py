"""Method v2 loop: expand → verify → continue after ZERO.

Does not change engine verdict meanings. Step budget is small.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from symbolic_compactification import ZERO, UNKNOWN

from research.method_v2.expand import expand_and_verify
from research.method_v2.packager import (
    cheap_transforms,
    propose as default_propose,
)


Proposer = Callable[[str, list, list, Optional[dict]], list]


def run_method_v2(
    current: str,
    symbols: list,
    functions: list | None = None,
    *,
    max_steps: int = 4,
    proposer: Proposer | None = None,
    stop_at_first_zero: bool = False,
) -> dict:
    functions = functions or []
    propose = proposer or (
        lambda text, syms, fns, fb=None: default_propose(text, syms, fns)
    )
    certified = current
    steps: list[dict] = []
    first_zero_step = None
    extra_after_zero = 0
    false_promotion = False
    feedback = None
    seen: set[str] = set()

    for step_i in range(max_steps):
        try:
            raw = propose(certified, symbols, functions, feedback)
        except TypeError:
            raw = propose(certified, symbols, functions)
        if not raw:
            break
        progressed = False
        for cand in raw:
            text = cand.get("candidate_text") or ""
            defs = cand.get("hypothesis_definitions") or {}
            if not text or text in seen:
                continue
            seen.add(text)
            expanded, result = expand_and_verify(
                certified, text, defs, symbols, functions)
            rec = {
                "step": step_i,
                "candidate_text": text,
                "expanded": expanded,
                "definitions": defs,
                "abstraction_level": cand.get("abstraction_level"),
                "hypothesis_family": cand.get("hypothesis_family"),
                "verdict": result.verdict,
                "evidence0": (result.evidence or [{}])[0].get("kind"),
                "seconds": getattr(result, "seconds", None),
            }
            steps.append(rec)
            if result.verdict == ZERO:
                if expanded == certified and not defs:
                    continue
                certified = expanded
                progressed = True
                if first_zero_step is None:
                    first_zero_step = step_i
                else:
                    extra_after_zero += 1
                feedback = None
                if stop_at_first_zero:
                    return _finish(
                        current, certified, steps, first_zero_step,
                        extra_after_zero, false_promotion, functions)
                break
            feedback = {
                "verdict": result.verdict,
                "kind": rec["evidence0"],
            }
            if result.verdict not in (ZERO, UNKNOWN) and False:
                false_promotion = True
        if stop_at_first_zero and first_zero_step is not None:
            break
        if not progressed and step_i > 0:
            # still consume remaining proposer calls only if new cands
            if all(s["step"] == step_i for s in steps[-len(raw):] if True):
                if not any(s["verdict"] == ZERO and s["step"] == step_i
                           for s in steps):
                    break
    return _finish(
        current, certified, steps, first_zero_step,
        extra_after_zero, false_promotion, functions)


def _finish(current, certified, steps, first_zero, extra, false_p, functions):
    n_zero = sum(1 for s in steps if s["verdict"] == ZERO)
    n_unknown = sum(1 for s in steps if s["verdict"] == UNKNOWN)
    closed = sum(
        1 for s in steps
        if s["verdict"] != UNKNOWN
        or (s.get("evidence0") not in {
            "definition_expand_failed", "construction_or_parse_failed"})
    )
    named_zero = sum(
        1 for s in steps
        if s["verdict"] == ZERO and s.get("definitions")
    )
    return {
        "input": current,
        "certified": certified,
        "changed": certified != current,
        "steps": steps,
        "n_steps": len(steps),
        "n_zero": n_zero,
        "n_unknown": n_unknown,
        "first_zero_step": first_zero,
        "extra_certified_after_first_zero": extra,
        "named_aux_zero": named_zero,
        "false_promotion": false_p,
        "functions": functions,
    }


def _m0_propose(text, symbols, functions, feedback=None):
    transformed, notes = cheap_transforms(text, symbols, functions)
    if transformed == text:
        return []
    return [{
        "candidate_text": transformed,
        "hypothesis_definitions": {},
        "abstraction_level": "D2" if "combine" in notes else "D1",
        "hypothesis_family": "algebra",
        "rationale": ",".join(notes),
    }]


def run_m0(current: str, symbols: list, functions: list | None = None, **kwargs) -> dict:
    kwargs = dict(kwargs)
    kwargs["stop_at_first_zero"] = True
    kwargs["max_steps"] = 1
    kwargs["proposer"] = _m0_propose
    return run_method_v2(current, symbols, functions, **kwargs)
