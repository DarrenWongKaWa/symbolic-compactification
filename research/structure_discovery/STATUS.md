# Structure-discovery research line — STATUS

Namespace: `research/structure_discovery/`
Branch: `research/verified-scientific-structure-discovery`
Parent line: compactification protocol v0 / Method v2 (publication **E**).
**Do not overwrite** previous benchmarks, decisions, or experiment logs.

Date opened: 2026-08-27

## DONE

- Isolated namespace and branch.
- Literature audit: `literature/` (DreamCoder/Stitch/babble, AI Poincaré,
  LieGAN, LGuess, FORM/CSE, FunSearch, Method v2). Triple
  abstraction+scientific-expr+exact-verify is not jointly covered.
- Frozen claims C1–C3, taxonomy D0–D6, typed hypothesis schema.
- Prototype: observations, discoverer, constructor, search graph, B0/B1/B6/B9.
- `ssc-structure-bench-v0.1` (21 DEV / 12 TEST, pos+neg; Guo not in TEST).
- DEV matrix 189 rows; freeze; held-out once; case studies; reviews; decision E.

## EVIDENCE

- DEV B9 pos type-hit 15/16; D3–D5 gold 9/9 vs B1/B6 0/9; unsafe 0.
- TEST B9 pos type-hit **8/8**, gold-certified 8/8, unsafe 0, fp 0.
- B9_no_obs = 0 (observations necessary).
- Guo: translation+observe OK; 8× repeated_kernel; no L4–L7.
- Leakage tests: no gold names in context.

Artifacts: `dev/`, `final/`, `case_studies/`, `analysis/`, `reviews/`,
`PUBLICATION_DECISION.md`.

## FAILED / BLOCKED

- Live LLM / multi-model / 5-seed: no usable API keys.
- Human D6 annotations: none (not fabricated).
- Guo Piecewise/confluence hypotheses: crowded out by CSE kernel ranking.
- S2-pos-perturbation (DEV): anti-unification not implemented.

## OPEN QUESTIONS

- Can an LLM discover H that the observer misses (Guo, perturbation)?
- Would a 3-role ensemble surface Piecewise on Guo?
- Does a physicist prefer B9 structured forms (D6)?

## NEXT STEP

Do not draft a paper. Optional later: LLM proposer vs frozen B9 observer
on a larger S3 set, new version id.

## Decision gate

**E — PROMISING BUT MORE EVIDENCE NEEDED**
(`PUBLICATION_DECISION.md`). No `paper_structure_discovery/`.

## commit SHA

*(filled after commit)*
