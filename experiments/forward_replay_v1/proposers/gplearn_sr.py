#!/usr/bin/env python3
"""Third-party gplearn SymbolicRegressor on samples of E_t.

Honest interface: sample the current expression numerically; ask gplearn
to fit a formula. Adapter maps the fitted program string to a candidate
expression. This is SR, not derivation search. Substitution identities
are not provided to gplearn.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import sympy as sp
import yaml
from gplearn.genetic import SymbolicRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from proposers.interface import write_candidates  # noqa: E402

SEED = 0
N_SAMPLES = 80


def parse(text: str) -> sp.Expr:
    return sp.sympify(text, locals={"Rational": sp.Rational, "I": sp.I})


def sample_and_fit(expr: sp.Expr) -> tuple[str, dict]:
    free = sorted(expr.free_symbols, key=str)
    if not free:
        return str(expr), {"n_features": 0}
    rng = np.random.default_rng(SEED)
    X = rng.uniform(0.4, 1.7, size=(N_SAMPLES, len(free)))
    f = sp.lambdify(free, expr, modules="numpy")
    cols = [X[:, i] for i in range(len(free))]
    y = np.array(f(*cols), dtype=float)
    if not np.all(np.isfinite(y)):
        mask = np.isfinite(y)
        X, y = X[mask], y[mask]
    est = SymbolicRegressor(
        population_size=200,
        generations=8,
        tournament_size=20,
        stopping_criteria=1e-10,
        const_range=(-2.0, 2.0),
        init_depth=(2, 4),
        function_set=("add", "sub", "mul", "div"),
        parsimony_coefficient=0.005,
        p_crossover=0.7,
        p_subtree_mutation=0.1,
        p_hoist_mutation=0.05,
        p_point_mutation=0.1,
        max_samples=1.0,
        verbose=0,
        random_state=SEED,
        n_jobs=1,
        feature_names=[str(s) for s in free],
    )
    t0 = time.time()
    est.fit(X, y)
    runtime = time.time() - t0
    prog = str(est._program)
    # gplearn uses add(x,y) etc. Leave raw for the adapter plus a sympy attempt.
    return prog, {
        "n_features": len(free),
        "features": [str(s) for s in free],
        "runtime_s": runtime,
        "n_samples": int(len(y)),
        "gplearn": "0.4.3",
        "seed": SEED,
        "generations": 8,
        "population_size": 200,
    }


def gp_to_sympy(prog: str) -> str:
    """Best-effort translation; may fail and remain a raw program string."""
    s = prog
    # Repeatedly fold add/sub/mul/div until stable or cap.
    import re

    for _ in range(40):
        n = s
        n = re.sub(r"add\(([^(),]+),([^(),]+)\)", r"(\1)+(\2)", n)
        n = re.sub(r"sub\(([^(),]+),([^(),]+)\)", r"(\1)-(\2)", n)
        n = re.sub(r"mul\(([^(),]+),([^(),]+)\)", r"(\1)*(\2)", n)
        n = re.sub(r"div\(([^(),]+),([^(),]+)\)", r"(\1)/(\2)", n)
        if n == s:
            break
        s = n
    return s


def main() -> None:
    frozen = yaml.safe_load((ROOT / "TASKS_FROZEN.yaml").read_text())
    for task in frozen["tasks"]:
        tid = task["task_id"]
        raw = (ROOT / "contexts" / tid / "current.txt").read_text().strip()
        expr = parse(raw)
        try:
            prog, extra = sample_and_fit(expr)
            translated = gp_to_sympy(prog)
        except Exception as exc:  # noqa: BLE001
            prog, translated, extra = "FAILED", "FAILED", {"error": repr(exc)}
        recs = [
            {
                "candidate_id": "gplearn-raw",
                "expression": translated if translated != "FAILED" else "0",
                "claimed_edge_type": "ALGEBRAIC_EQUIVALENCE",
                "rationale": "gplearn SymbolicRegressor fit to samples of E_t",
                "raw_program": prog,
            },
            {
                "candidate_id": "gplearn-identity",
                "expression": raw,
                "claimed_edge_type": "ALGEBRAIC_EQUIVALENCE",
                "rationale": "copy of current; SR did not propose a rewrite",
            },
        ]
        write_candidates(ROOT, "gplearn", tid, recs, extra=extra)
        print(tid, extra.get("runtime_s"), prog[:80] if isinstance(prog, str) else prog)


if __name__ == "__main__":
    main()
