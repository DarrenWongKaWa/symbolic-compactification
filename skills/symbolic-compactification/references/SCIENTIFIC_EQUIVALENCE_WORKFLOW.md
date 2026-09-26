# Scientific equivalence workflow

Use this reference when the task is more than simplifying one expression:
the user wants a paper's displayed formulas, derivation steps, or alternative
normalizations checked as equivalent. It is a paper-agnostic engineering
workflow. It does not supply scientific claims, example equations, or a
domain-specific result.

## 1. Freeze the object being audited

Before proposing a rewrite, identify the active source tree and its include
graph. Count only files reachable from the selected entry point. Keep archived,
duplicate, generated, and inactive drafts outside the active equation set.

Create a source snapshot with:

- the entry file and included files;
- source location and equation label/number for each displayed formula;
- raw-byte SHA-256 for every formula block and source file;
- the source revision, tool versions, and run identifier.

A successful compilation is only a source/build check. It does not certify an
equivalence. A source edit invalidates the old formula bridge until the changed
block is re-mapped and re-checked.

## 2. Write the mathematical contract first

Record conventions before comparing formulas. At minimum, make explicit:

- units and frequency/energy variables;
- sign of charge and current/field definitions;
- index order, ordered versus unordered sums, and dummy-index ranges;
- symmetrization or exchange normalization, including every factor of (1/2);
- kernel, derivative, special-function, and repeated-argument definitions;
- domain restrictions such as real variables, nonzero gaps, nonvanishing
  denominators, band isolation, or invertibility;
- symmetry sewing, periodicity, boundary conditions, and the order of limits.

Treat a convention change as a transformation with its own residual. Do not
identify two lifetimes, broadenings, or rates by visual inspection: match all
relevant poles and numerator functions under an explicit parameter dictionary.

## 3. Split the derivation into typed edges

One edge should represent one scientific move. Separate, for example:

1. definitions and notation insertion;
2. local algebraic rearrangement;
3. substitution under declared identities;
4. dummy-index relabeling or finite permutation;
5. local symmetry, Hermiticity, projector, or gauge-covariant identity;
6. sum, integral, or boundary argument;
7. coefficient extraction, Laurent/Taylor expansion, or limit statement;
8. numerical or model-specific support.

Never infer an edge from adjacent equation numbers. Do not collapse an appendix
into one “therefore” edge. A global sum or integral is not a local residual;
lower its local children and retain the global rule as a separate obligation.

## 4. Verify the narrowest exact statement

For each algebraic edge, submit the actual residual (A-B) with the exact
symbols, assumptions, and namespace used by the source. Promote only when the
deterministic engine returns exact `ZERO` with an integrity-bound receipt.

`ZERO` certifies that submitted residual under its recorded conditions. It does
not certify a broader domain, a physical interpretation, a global integration
step, or a remainder estimate.

Use confluent or divided-difference definitions when arguments coincide. Do not
replace a regular repeated-argument limit by a formal (0/0), and do not drop
the thermal/numerator part of a kernel while matching only its denominator.

When a physical formula is a rescaled version of another one, create an
explicit normalization bridge such as

```text
new_expression - declared_factor * reference_expression = 0
```

and record the factor, field convention, and exchange convention. Keep
kinematic, geometric/algebraic, and dynamical equivalence as separate edges.

## 5. Keep evidence scopes orthogonal

Use the narrowest applicable scope and preserve the distinction in the report:

| Scope | What it supports |
|---|---|
| `POINTWISE_EXACT` | Local identity at fixed variables and declared conditions |
| `BZ_INTEGRATED_EXACT` / global-rule certificate | Equality after a separately declared domain or boundary rule |
| `TRS_BZ_EXACT` / symmetry-projection scope | Pairing under declared symmetry sewing and full-domain integration |
| `COEFFICIENT_EXACT` | The extracted finite coefficient only |
| `WEAK_GAMMA_ASYMPTOTIC` or other asymptotic scope | A stated leading limit with its order of limits; never a finite-parameter identity |
| `NUMERICAL_SUPPORT_ONLY` | A reproducible numerical check for the stated model and mesh |
| `SOURCE_ONLY` / `UNCERTIFIED` | A source assertion or unresolved step without an executable certificate |

Project-specific labels may map to the skill's existing status vocabulary, but
must not promote an asymptotic, numerical, or source-only row to `EXACT`.
Finite Laurent/Taylor coefficients do not prove an enclosing (O(\cdot))
remainder. A numerical match does not prove an analytic identity.

## 6. Replay cold, then inspect the bridge

The reproducibility gate has two modes:

- **cold replay**: recompute source-dependent stages without authenticated
  caches;
- **cache replay**: useful for a quick check, but not evidence of a fresh
  derivation.

Run the environment/doctor check first, then the convention check, then the
cold replay. Record the run ID and all logs; never overwrite an earlier
evidence directory. Check that the replay's source hashes, formula-block hashes,
and engine/protocol versions match the formula bridge.

For every active formula, the bridge should expose at least:

```text
formula_id, source, block_hash, scope, assumptions,
edge_ids, residual_gate, run_id, status
```

Coverage is a separate gate from proof: all mapped blocks can still
contain asymptotic or global-rule scopes. Report both the coverage count and
the evidence-grade counts.

## 7. Produce a reviewer-facing package

Keep the delivery small and auditable:

- active manuscript/source subset;
- formula inventory and formula-to-edge bridge;
- convention and assumption ledger;
- machine certificates and cold-replay manifest;
- pre-generated `REVIEWER_SUMMARY.html` and matching Markdown for reviewers
  who do not run code;
- reviewer Markdown/HTML report with a visible unresolved queue;
- a short README with exact reproduction commands.

The summary is generated from sealed machine records after verification. It is
a convenience reading view: it may explain counts and point to the queue, but
it cannot create, promote, or hide a machine status.

Do not mix GPT notes, abandoned derivations, generated intermediates, unrelated
model scans, or private working files into the package. Archive them with a
manifest when they may need recovery; do not silently delete evidence.

## 8. Fail-closed decision table

| Observation | Action |
|---|---|
| exact residual is `ZERO` and hashes match | certify only that typed edge |
| `ZERO` requires a declared substitution | use the assumption-dependent status and show the substitution |
| local children pass but a global rule is needed | keep the parent as a rule certificate, not engine `ZERO` |
| coefficient passes but the remainder is unproved | keep the parent asymptotic/unresolved |
| numeric replay agrees | record numerical support only |
| source block changed or bridge hash mismatches | invalidate the bridge and re-audit |
| residual is `NONZERO`, `UNKNOWN`, missing, or timed out | preserve the result and stop promotion |

The final report should say what was proved, under which conditions, what was
only checked numerically or asymptotically, and which scientific choices remain
for the author or reviewer.
