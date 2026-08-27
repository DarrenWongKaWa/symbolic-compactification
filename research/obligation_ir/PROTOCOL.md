# Track B protocol

1. Freeze raw model output (`raw_content`, `hypotheses`).
2. Compile to Obligation IR.
3. Verify each compiled row: ZERO / NONZERO / UNKNOWN.
4. Label the miss D, C, or V.
5. Never promote UNKNOWN.

First experiment: `run_frozen.py` on the closed DeepSeek DEV snapshot.
No prompt changes. No SOL changes.

A later compiler that turns the same frozen Guo DD text into ZERO is
**C/L4 gain**. A new proposer that emits `H_repr` absent from the
snapshot is **D/L3 gain**. Record both; do not mix the claim.
