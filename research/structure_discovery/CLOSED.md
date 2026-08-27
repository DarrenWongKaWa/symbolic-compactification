# CLOSED — Verified Scientific Structure Discovery v0.1

Closed: 2026-08-27
Evidence commit: `4237f6b`
Do not extend this line with more local detectors, verifier “discovery
help”, or a three-heuristic ensemble.

## Result

```
typed structure protocol works    but    structure invention remains unsolved
```

Frozen B9 (deterministic observer) is the Layer-1 baseline. **Do not edit**
`research/structure_discovery/prototype/` for this closure. Layer 2 lives in
`research/abstraction_invention/`.

## What v0.1 excluded

1. More local pattern detectors — toy 8/8 is “pattern exists + we encoded
   the detector ⇒ recovered.” Reviewer B: CSE + local patterns + residual gate.
2. Strengthening ZERO to help discovery — Guo fails *before* the verifier:
   the interesting \(H\) is never proposed.
3. Three deterministic subagents — that only enlarges a handcrafted library,
   it does not yield master-function invention.

## Frontier after closure

```
abstraction invention from non-identical structure
```

Canonical DEV miss: \(V(p)G_0(p)V(p)\) vs \(V(q)G_0(q)V(q)\) is one object
\(F(x)=V(x)G_0(x)V(x)\), but not an identical subtree.

Guo (3911 ops, 4 Piecewise, 740 indexed calls) filled 8 CSE kernels; no
master / divided difference / generator.

## Frozen baseline for Layer 2

`run_b9` in `research/structure_discovery/prototype/baselines.py`
commit `4237f6b`. New methods must beat it on **deliberately non-identical**
families, not on exact-pattern toys.
