---
name: symbolic-compactification
description: >
  Use for verified symbolic reasoning in theoretical physics: forward
  derivation (candidate must be exact ZERO) or paper audit (inventory,
  source-grounded relations, RESULTS.md). Trigger /symbolic-compactification.
argument-hint: "[forward|audit]"
---

# symbolic-compactification

Deterministic propose-and-verify. This skill is not a CAS, not a theorem
prover, and not a physics-discovery box. LLM judgment is never proof.
Core verification needs no API key.

Two workflows. Full rules: `AGENTS.md`.

## Forward derivation

Current expression + candidate → `verify` / `step`. Promote only on `ZERO`.

| Verdict | Action |
|---|---|
| ZERO | Promote; candidate becomes current |
| NONZERO | Read residual + counterexample; propose again |
| UNKNOWN | Do not promote |

```bash
symbolic-compactification inspect current.txt --symbols symbols.json --json
symbolic-compactification verify WORKSPACE
# or step --run RUN_ID --candidate candidate.txt --symbols symbols.json
```

A human, CAS, or model may write the candidate. None of them certifies it.

## Paper audit

Printed equation numbers only. No adjacency-invented equalities.

```bash
symbolic-compactification audit verify WORKSPACE
symbolic-compactification audit table WORKSPACE
```

Flagship human-readable table: `examples/flagship/guo/RESULTS.md`.

## Red flags

- Treating a candidate as a result before `ZERO`
- Calling a rule certificate engine `ZERO`
- Promoting on `UNKNOWN`
- Requiring a model API key for verification
- Inventing Eq. (i) → Eq. (i+1) because the numbers are consecutive
