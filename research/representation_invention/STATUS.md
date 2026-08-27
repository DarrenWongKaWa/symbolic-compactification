# STATUS — Verified Representation Invention v1

## DONE

- Branch from `3fea222`; contracts `45b2b4d`.
- Parallel packages: dd, master, obligations, bench, llm, falsifier, guo, literature.
- Phase 5 generic DD gate: 12/12, false ZERO = 0.
- P2 DEV matrix: 5 seeds, DeepSeek-v4-pro, same SOL as P1.
- Guo P2/P3 5 seeds each (new LLM calls). Full-text rescore; no prompt retune.

## EVIDENCE

- P1 frozen Guo: 11/11 local confluence ZERO (specialized compiler).
- P2 Newton DEV: 2/5 seeds DD-OK with explicit \(F(z)=f(z)\).
- P2 polygamma DEV: 1/5 seeds DD-OK; B9/LGG produced no hypothesis.
- P2 tautological master: 5/5 ABSTAIN.
- P2 Guo: grounded local_confluence / some hermite types; 0 ZERO (V/C: generic
  limit/size guard). Discovery present; certification not.

## FAILED

- Systematic Hermite DD-OK on repeated-node / two-node Hermite controls.
- Guo Newton/Hermite certification under the generic V2 verifier.
- Treating B9's typed `divided_difference` label as operational \(H_{\mathrm{repr}}\).

## OPEN QUESTIONS

- C2: only partially (seed-dependent Newton; not Hermite).
- C3: substitution masters exist; not two-operator nontrivial masters.
- C4: Guo P3 (RAW) parse-failed 1/5; P2 (SOL) 5/5 parse OK. SOL still an
  observation prior, not proven help for DD.
- C5: one AI_UNIQUE polygamma seed; Newton is mixed vs B9 naming.

## NEXT AUTO ACTION

Stop. Decision E recorded. Do not retune prompts. Do not add Guo ZERO
rules. Optional later: 10-seed Newton, generic Guo-scale limit without
Guo-specific identities, or a second model family on the frozen protocol.

## COMMIT SHA

Integration + Phase 5: `45f1e46`
Worktree merges on `research/verified-representation-invention-v1`.
