# AGENTS.md

You are operating symbolic-compactification: a deterministic kernel for
verified symbolic reasoning in theoretical physics.

Two workflows:

1. **Forward derivation.** Read a current expression, write a candidate,
   run `verify` or `step`. Promote only on `ZERO`.
2. **Paper audit.** Inventory numbered equations, record only
   source-supported relations, run `audit verify`, emit `RESULTS.md`.

LLM judgment is never proof. Core verification needs no API key.

## Rules

- `ZERO` means exact engine `ZERO`.
- `ZERO` is not `CERTIFIED_BY_RULE`.
- `UNKNOWN` never promotes.
- Proposal authority is not verification authority.
- Do not invent Eq. (i) → Eq. (i+1) from adjacency.
- Do not weaken residuals to manufacture `ZERO`.
- Do not reopen frozen negative results in `docs/history/negative-results.md`
  without a new predeclared experiment.

## Forward loop

Copy researcher files into a workspace. Never transcribe long expressions
by hand.

```
inspect → write candidate.txt → verify/step → ZERO promotes, else retry
```

Optional proposer (human, CAS, or model). The verifier is the only judge.

## Paper-audit loop

```
inventory printed numbers → freeze source-grounded relations → verify → table
```

Printed equation numbers are the public identifiers.

Full skill text: `.grok/skills/symbolic-compactification/SKILL.md`.
