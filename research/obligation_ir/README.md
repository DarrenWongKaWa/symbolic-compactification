# Track B — Scientific Obligation Language (L4)

Independent of Track A. First measurement uses **frozen** DeepSeek
outputs from `research/llm_abstraction/runs/`. Those files are read-only.

```
LLM hypothesis  →  Obligation IR  →  backend verify
```

not

```
LLM prose  →  hope SymPy parses it
```

## Kinds

EQUALITY, SUBSTITUTION, PERMUTATION, DERIVATIVE, LIMIT,
DIVIDED_DIFFERENCE, CONFLUENCE, BASIS.

Uncompiled ≠ UNKNOWN. Uncompiled is `COMPILE_FAILURE` (layer **C**).
UNKNOWN after a compiled obligation is layer **V**.
A missing gold type is layer **D**.

If the same frozen raw output goes UNKNOWN → ZERO under this compiler,
that is **language gain**, not discovery gain.

## Guo bars (not shallow kernel count)

- G1 discovery of an explicit representation class
- G2 H_repr-like maps
- G3 compile to IR bound to source expressions
- G4 ZERO / NONZERO / UNKNOWN per obligation
