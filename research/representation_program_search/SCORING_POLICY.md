# Scoring policy

Verification is a **hard gate**. A high score cannot override NONZERO.
COMPILE_FAILURE is not success. UNKNOWN does not become ZERO.

## Complexity (transparent, not per-task)

```
C(H) =
    n_latents
  + n_operators
  + max_operator_depth
  + n_parameters
  + n_member_exceptions
  + ceil(count_ops(F) / 8)
  + n_reconstruction_ops
```

`n_member_exceptions` counts member-specific special cases that are
not instances of a shared operator. Independent VALUE of a distinct
latent per member counts as an exception.

Do not hand-tune weights per task. Changing this formula is a new
method version.

## Score (DEV-frozen coefficients)

Concept:

```
good abstraction
  = maximum explained structure
    with minimum unnecessary machinery
```

Formula:

```
Score(H) =
    Coverage(H)
  + λ1 * VerifiedRelations(H)
  + λ2 * Reuse(H)
  - λ3 * Complexity(H)
  - λ4 * Exceptions(H)
```

Frozen coefficients (until DEV evidence forces a documented version
bump, **before TEST freeze**):

```
λ1 = 1
λ2 = 1
λ3 = 1
λ4 = 2
```

Definitions:

- Coverage = (# assigned catalog members) / (# catalog members)
- VerifiedRelations = count of compiled obligations with verdict ZERO
  that are not tautological VALUE-self maps
- Reuse = 0 if n_latents = 0 else
  (# members sharing a latent with another member) / n_latents
- Exceptions = n_member_exceptions
- Complexity = C(H) above

If any required obligation is NONZERO, H is **ineligible**. Score is
recorded for diagnostics but cannot rank it as a success.

UNKNOWN obligations do not increment VerifiedRelations.

## PROGRAM_SUCCESS (all required)

1. complete representation program
2. grounded source members
3. all required operators explicit
4. assumptions complete (DECLARED or DERIVED)
5. compilation succeeds
6. all required obligations ZERO
7. non-tautological
8. within frozen grammar
9. no target leakage

## AI_SEARCH_ADVANTAGE

Under **matched** state-expansion budget:

LLM-guided search finds PROGRAM_SUCCESS **and** deterministic /
symbolic / random search does not, with replication across seeds and
more than one task/cluster.

Three-auditor confirmation (enumeration-within-budget, leakage,
genuine search step). Only 3/3: AI_SEARCH_ADVANTAGE_CONFIRMED.

## GRAMMAR_ADVANTAGE

Deterministic program search succeeds where old free-form LLM **and**
old frozen symbolic stack failed. Method result, **not** an AI result.
Keep separate from AI_SEARCH_ADVANTAGE.

## Efficiency metrics

STATES_TO_FIRST_SUCCESS, TIME_TO_FIRST_SUCCESS, TOKENS_TO_FIRST_SUCCESS,
SUCCESS@10/50/100/500/1000, best certified depth vs budget.

Stochastic methods: success probability, median states-to-success,
seed sensitivity. Never report only the best seed. Task-weighted and
cluster-weighted both required.
