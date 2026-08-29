# Protocol

Parent: `0cdde49` (AC line, publication F). Branch:
`research/representation-program-search-v1`.

## Order

1. **This contract freeze.** No results before it.
2. Case mining C1–C6 on **fresh** scientific sources. No variants of
   the old TEST. Guo is not a new scientific case.
3. Assumption audit (existing ScientificAssumptionContract).
   PROBLEM_UNDERSPECIFIED rejected.
4. Admission → `ssc-representation-search-bench-v0.1` DEV/TEST/CHALLENGE
   proposal. TEST not frozen yet.
5. DEV calibration gate (R2, R3, R4/R5, R6, trap) for all search
   methods. Freeze implementation semantics.
6. DEV method development (grammar/search/scoring/routing).
7. **Fresh TEST freeze** (`final/FREEZE_MANIFEST.json`).
8. Held-out matrix S0–S7 + F0. Primary `deepseek-v4-pro`; later
   `deepseek-v4-flash` robustness.
9. Reviewers. Publication A–F. Repertoire V2 only after close.

## Firewalls

- Do not mutate SOL, frozen B9/LGG, AC benches, or Guo hops.
- Do not extend the parser.
- Do not retune AC prompts as this method.
- LLM may only emit legal actions or rank legal states.
- Isolated worktrees for M1–M10; no shared mutable manifests.

## Remainder invariant

neg ZERO ∧ C0 ZERO ∧ remainder UNKNOWN ⇒ UNKNOWN, never ZERO.
