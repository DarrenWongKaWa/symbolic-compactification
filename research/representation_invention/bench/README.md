# Owner: Subagent D — ssc-representation-bench-v0.1

New benchmark. Do not mutate old benches
(`research/llm_abstraction/bench/`, `research/llm_abstraction/calibration/`,
`research/structure_discovery/`, `research/abstraction_invention/`).

DEV + frozen TEST. Tiers A/B/C. Positive and adversarial negatives.

Hidden fields (`target_type`, instance maps, R-level, polarity, difficulty)
must not appear in proposer view.

Guo is a DEV pointer only — not held-out TEST. The full Guo catalog is owned
by Subagent G.

## Layout

```
bench/
  schema.json          task JSON schema (on-disk record)
  loader.py            load + proposer_view() whitelist
  build_tasks.py       authoring helper (TEST regen = version bump)
  tasks/dev/*.json     DEV (method work allowed)
  tasks/test/*.json    frozen TEST (split=test)
  validation/freeze_manifest.json
```

On-disk records include source expressions, assumptions, symbols, functions,
and a per-task G#### catalog. Evaluation labels stay on disk and are stripped
by `proposer_view()`.

## Hidden fields (stripped)

`target_type`, `hidden_target_type`, `gold_types`, `instance_maps`,
`hidden_instance_maps`, `r_level`, `hidden_r_level`, `polarity`,
`negative_tempting_structures`, `provenance_hidden`, `expected_verdict`,
`notes`, `ladder_id`, `difficulty`.

Proposer-visible JSON must not contain R-level tokens, `gold`, `Phi_Gamma`,
`L4`–`L7`, or `hermite_divided_difference` as a target label.

## Tiers

### Tier A — clean math controls (DEV + TEST)

| id | split | polarity | control |
|---|---|---|---|
| `dev-a-newton-first` | dev | + | Newton first DD |
| `dev-a-repeated-node` | dev | + | repeated-node DD |
| `dev-a-hermite-two` | dev | + | Hermite / higher DD |
| `dev-a-deriv-family` | dev | + | derivative family |
| `dev-a-recurrence-family` | dev | + | recurrence family |
| `dev-a-wrong-sign-dd` | dev | − | wrong-sign DD bait |
| `test-a-newton-first` | test | + | held-out Newton first DD |
| `test-a-repeated-node` | test | + | held-out repeated-node DD |
| `test-a-hermite-two` | test | + | held-out Hermite DD |
| `test-a-deriv-family` | test | + | held-out derivative family |
| `test-a-recurrence-family` | test | + | held-out recurrence family |
| `test-a-wrong-sign-dd` | test | − | held-out wrong-sign DD |

### Tier B — representation change (DEV + TEST)

| id | split | polarity | control |
|---|---|---|---|
| `dev-b-piecewise-dd` | dev | + | piecewise → DD |
| `dev-b-branch-degen` | dev | + | branch degeneracy |
| `dev-b-special-fn` | dev | + | special-function family |
| `dev-b-master-induct` | dev | + | master-object induction |
| `dev-b-nonconfluent-pw` | dev | − | non-confluent piecewise |
| `dev-b-tautological-master` | dev | − | tautological master bait |
| `test-b-piecewise-dd` | test | + | held-out piecewise → DD |
| `test-b-special-fn` | test | + | held-out special-function DD |
| `test-b-nonconfluent-pw` | test | − | held-out non-confluent piecewise |
| `test-b-tautological-master` | test | − | held-out tautological master |

### Tier C — scientific-flavored, not full Guo (DEV + TEST)

Generic sympy (`polygamma`, `exp`, resolvents). Short fragments only.

| id | split | polarity | flavor |
|---|---|---|---|
| `dev-c-thermal-kernel` | dev | + | thermal-kernel-like |
| `dev-c-green-like` | dev | + | Green-function-like |
| `dev-c-nl-response` | dev | + | nonlinear-response fragment |
| `dev-c-pert-denom` | dev | + | perturbative denominator |
| `dev-c-tensor-family` | dev | + | tensor family |
| `dev-guo-pointer` | dev | pointer | external catalog; not TEST |
| `test-c-thermal-kernel` | test | + | held-out thermal-kernel-like |
| `test-c-green-like` | test | + | held-out Green-function-like |
| `test-c-nl-response` | test | + | held-out response fragment |
| `test-c-tensor-family` | test | + | held-out tensor family |

## Splits

- **DEV**: method work allowed.
- **TEST**: frozen at this version. Do not retune against TEST. Do not paste
  the full Guo `sigma_abc` expression into TEST.

Catalog ids are local `G0001`… per task, built from that task's expressions.
