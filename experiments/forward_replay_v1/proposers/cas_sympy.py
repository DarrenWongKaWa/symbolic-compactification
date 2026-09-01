#!/usr/bin/env python3
"""Deterministic SymPy rewrite proposer. Reads only contexts/<task>/current.txt."""
from __future__ import annotations

import sys
from pathlib import Path

import sympy as sp
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from proposers.interface import write_candidates  # noqa: E402


def parse(text: str) -> sp.Expr:
    local = {
        "Rational": sp.Rational,
        "I": sp.I,
        "I_sym": sp.I,
    }
    return sp.sympify(text.replace("**", "**"), locals=local)


def candidates_from(expr: sp.Expr) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    variants = [
        ("expand", sp.expand(expr)),
        ("factor", sp.factor(expr)),
        ("together", sp.together(expr)),
        ("cancel", sp.cancel(expr)),
        ("simplify", sp.simplify(expr)),
        ("collect_all", expr),
    ]
    seen = set()
    for name, e in variants:
        s = str(e)
        if s in seen:
            continue
        seen.add(s)
        out.append((name, s))
        if len(out) >= 4:
            break
    return out


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    for task in frozen["tasks"]:
        tid = task["task_id"]
        raw = (ROOT / "contexts" / tid / "current.txt").read_text().strip()
        expr = parse(raw)
        pairs = candidates_from(expr)
        recs = [
            {
                "candidate_id": f"cas-{i}",
                "expression": s,
                "claimed_edge_type": "ALGEBRAIC_EQUIVALENCE",
                "rationale": name,
            }
            for i, (name, s) in enumerate(pairs)
        ]
        write_candidates(ROOT, "cas_sympy", tid, recs, extra={"sympy": sp.__version__})
        print(tid, [c["rationale"] for c in recs])


if __name__ == "__main__":
    main()
