# Certification scope

Frozen language: **exact symbolic certification under declared engine
semantics**. Not: formal proof.

## Three levels

| Level | Meaning | This project |
|---|---|---|
| 1. Engine semantics | ZERO iff the SymPy residual pipeline in `verifier.py` proves exact zero under declared symbols, functions, assumptions, and named budgets | **default for all claims** |
| 2. Independent CAS cross-check | same identity checked in Mathematica and/or another CAS | B2 unavailable on freeze host; subset to be filled in `crosscheck_results.csv` if a kernel appears |
| 3. Formal kernel | Lean/Isabelle/Coq kernel accepts a proof of the identity | Lean not installed; only tractable polynomial/rational identities are even in scope |

ZERO is produced only by exact symbolic simplification (direct or after
budgeted complex normalization). NONZERO only by a proven exact rational
probe (`value.equals(0) is False`). Every other path is UNKNOWN.

Numeric agreement, `PossibleZeroQ`, `N[..., 30]`, coefficient matching
on expanded series, and finite-N `expand_finite` are **not** Level 1.

## Honest paper sentences

Allowed: "The engine certified `current − candidate = 0` under SymPy
semantics, policy snapshot S, and declared assumptions A."

Forbidden: "We formally proved the identity"; "machine-checked theorem";
"certified in the sense of Lean".

If Level 2 or 3 results later exist, they must be reported as a **subset**
with disagreements listed, never as a silent upgrade of all ZERO marks.
