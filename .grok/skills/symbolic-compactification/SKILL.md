---
name: symbolic-compactification
description: >
  Use for verified symbolic reasoning: forward derivation (candidate must
  be exact ZERO) or paper audit (inventory, source-grounded relations,
  reviewer HTML + Markdown). Trigger /symbolic-compactification.
argument-hint: "[forward|audit]"
---

# symbolic-compactification

Deterministic propose-and-verify. Not a CAS, not a theorem prover, not a
physics-discovery box. LLM judgment is never proof. Core verification
needs no API key. Full rules: `AGENTS.md`.

## Paper audit (default product path)

Printed equation numbers only. No adjacency-invented equalities.

```bash
symbolic-compactification audit init DIR
# copy manuscript into DIR/manuscript/
symbolic-compactification audit inventory DIR
# record source-grounded edges in DIR/edges/
symbolic-compactification audit verify DIR
symbolic-compactification audit report DIR
```

Outputs: `DIR/reports/REPORT.md` and `DIR/reports/report.html`.

Flagship (do not re-adjudicate unless asked):
`examples/guo-evidence-ledger/output/index.html`.

Independent paper example (Anan V3):
`examples/2604.04520/v3/audit.html` from `evidence/audit.json`.
Do not overwrite `v1/` or `v2/`.

HTML first screen must include a visible `<section id="map-sec">`
appendix map when the paper has appendices. Never `<details id="map-sec">`.
Never stamp Exact from `0*` (invalid overlay; archived).

## Forward derivation

Current expression + candidate → `verify` / `step`. Promote only on `ZERO`.

```bash
symbolic-compactification inspect current.txt --symbols symbols.json --json
symbolic-compactification verify WORKSPACE
```

## Red flags

- Treating a candidate as a result before `ZERO`
- Calling a rule certificate engine `ZERO`
- Promoting on `UNKNOWN`
- Inventing Eq. (i) → Eq. (i+1) because numbers are consecutive
- Putting `0*` in reviewer HTML
- Rewriting frozen RESULTS statuses to make a demo look better
