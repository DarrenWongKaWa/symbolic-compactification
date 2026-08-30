# M10 / L handoff — adversarial search falsifier

Branch: `work/rps-search-falsifier`

Scope: evaluator-only negative controls. Nothing in
`research/representation_program_search/falsifier/` is a scientific case or
is eligible for DEV, TEST, CHALLENGE, PROGRAM_SUCCESS, GRAMMAR_ADVANTAGE, or
AI_SEARCH_ADVANTAGE.

## Delivered

- `RPSFalsifierSuiteV1` manifest with SHA-256 binding of every suite artifact.
- Six traps covering the requested failure modes.
- Exact source-member files, parser namespaces, declared assumptions,
  `RepresentationProgramAdapterV1` programs, grammar-action sequences, and
  evaluator-only reconstructions for every trap.
- A deterministic fixture adapter independent of unfinished M1.
- Recorded engine sessions for every executable false equality.
- One separate positive ZERO control and its `FINAL_CERTIFIED_FORM.md`.
- Six deterministic tests plus integrated validation.

## Failure matrix

| trap | stage | frozen outcome |
|---|---|---|
| tautological one-latent-per-member | pre-verifier | exact byte identity; `TAUTOLOGICAL_PROGRAM` |
| wrong Hermite multiplicity | compile | fixture class `HERMITE_NODE_MULTIPLICITY`; M1 prefix `HERMITE_REPEATED_NODE_REQUIRED`; `NODES[x,y]` has no repetition |
| false recurrence | verifier | `NONZERO`, residual `-1`, exact value `-1` |
| over-complex memorizing master | pre-verifier | exact byte identity; strictly dominated by `F(s)=x+s` |
| attractive wrong basis, member 1 | verifier | `NONZERO`, residual `x - y`, point `{x:-2,y:-1}`, exact value `-1` |
| attractive wrong basis, member 2 | verifier | `NONZERO`, residual `-x + y`, point `{x:-2,y:-1}`, exact value `1` |
| near-correct divided difference | verifier | `NONZERO`, residual `2*x*y`, point `{x:-2,y:-2}`, exact value `8` |

The constant false-recurrence residual needs no substitution; the engine
records its exact counterexample with the empty point `{}`, meaning the sides
differ throughout their declared domain.

## Evidence paths

- False recurrence:
  `traps/false-recurrence/verification/runs/20260830T113859Z-5855d4`
- Wrong basis member 1:
  `traps/attractive-wrong-basis/verification/runs/20260830T113901Z-4593b1`
- Wrong basis member 2:
  `traps/attractive-wrong-basis/verification/runs/20260830T113903Z-115255`
- Near-correct DD:
  `traps/near-correct-divided-difference/verification/runs/20260830T113905Z-d480f3`
- Positive control:
  `positive_control/verification/runs/20260830T113906Z-7346cc`

All paths above are relative to
`research/representation_program_search/falsifier/`. Every NONZERO step is
`UNVERIFIED/REFUTED`, retains the exact residual and counterexample in its
step evidence, and has no `final/current.json` promotion.

The positive control alone certified and promoted:

```text
(x + y)**2
```

Its complete report is
`positive_control/verification/runs/20260830T113906Z-7346cc/final/FINAL_CERTIFIED_FORM.md`.

## Verdict totals

```json
{
  "COMPILE_FAILURE": 1,
  "NONZERO": 4,
  "PRE_VERIFICATION_INELIGIBLE": 2,
  "UNKNOWN": 0,
  "ZERO": 1
}
```

`ZERO` belongs only to the positive control. No trap was promoted. The two
exact-but-ineligible traps do not create an equality proposal: candidate and
source bytes are identical, so the eligibility gate rejects the program
before verification. The ill-typed Hermite trap likewise cannot reach the
verifier.

## M1 integration seam

`adapter.py` checks frozen grammar membership and repeated-node typing without
claiming to be Program IR. Its fixture class
`HERMITE_NODE_MULTIPLICITY` maps explicitly to M1's implemented failure prefix
`HERMITE_REPEATED_NODE_REQUIRED`; M1 appends the node id after `:`. A later
integration should load each fixture into M1 and compare this prefix rather
than demand identical adapter/M1 strings. Do not expose fixture programs,
dominance witnesses, or expected labels to any proposer or search heuristic.

## Validation

```text
python -m research.representation_program_search.falsifier.validate
  -> 6 traps; COMPILE_FAILURE=1, NONZERO=4,
     PRE_VERIFICATION_INELIGIBLE=2, UNKNOWN=0, ZERO=1

pytest -q tests/test_rps_search_falsifier.py
  -> 6 passed

pytest -q tests/test_rps*.py
  -> 54 passed
```
