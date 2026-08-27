# Publication decision — Layer 2 / beyond LGG

Date: 2026-08-27

## Decision: E — PROMISING BUT MORE EVIDENCE NEEDED

LGG milestone closed (`LGG_CLOSED.md`, `efc0924`). This file now covers
the *beyond LGG* control experiments as well.

### Strongest supported claim

(1) First-order LGG beats frozen B9 on substitution-level non-identical
families (v0.1 TEST 5/5 vs 0/5). (2) A gold-free score ranks Guo’s
polygamma family above `I*mu*theta0` and can drop the junk on `keep`.
(3) Distributivity “beyond LGG” is **canon/expand**, not invention.
(4) A relation graph recovers derivative and permutation edges that
zip-LGG mis-templates.

### Strongest unsupported claim

AI (LLM) supplies abstractions unavailable to symbolic methods. LLM
**BLOCKED**. Guo still not L4–L7 / confluence / generators.

### Known algorithms that now sit as baselines

Plotkin LGG (B1), expand/AC canon (B3/B4), sympy.diff (B5). Not novelty.

### Key limitation

Tiny v0.2 TEST (6 items). F5–F8 not solved. Score weights chosen on DEV Guo.

### Venue

None. Conditional P1: LLM vs B5/B1 on F3/F5 with the frozen schema.
No paper directory.

---

# Publication decision — Layer 2 (LGG freeze, retained)

Date: 2026-08-27

## Decision: E — PROMISING BUT MORE EVIDENCE NEEDED

### Strongest supported claim

First-order anti-unification recovers parameterized templates
(e.g. \(F(x)=V(x)G_0(x)V(x)\)) on non-identical members where frozen B9
invention-success is 0 (held-out 5/5 vs 0/5), with 3/3 negative abstain.

### Strongest unsupported claim

That an AI (LLM) invented scientific abstractions, or that Guo reached
L3–L7. LLM blocked. Guo templates include a real polygamma family *and*
shallow junk (`I*mu*theta0`). No confluence.

### Closest prior work

Plotkin LGG; babble/DreamCoder; frozen B9 CSE.

### Key experiment

Frozen B9 vs M_lgg on `ssc-abstraction-bench-v0.1` TEST.

### Key limitation

Tiny author-constructed set; LGG over-generates; no LLM; derivative
obligations use `sympy.diff` not the residual parser; Family D is still
LGG, not invariant-basis discovery.

### Venue

None. Next: noisy-LGG filter + LLM emitting the same schema vs LGG on Guo.
Not ICLR/ICML/NeurIPS. No `paper/`.
