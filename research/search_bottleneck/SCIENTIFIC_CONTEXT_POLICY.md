# Scientific-context leakage policy

Field name: `scientific_context` (string or list of strings).

This field is **proposer-visible**. It must help a theoretical physicist
search without leaking a hidden gold compact form.

## Allowed

Generic domain and *kind* of useful structure, for example:

- this is a nonlinear-response / Kubo-like / Green's-function-like object;
- indices label bands, sites, or dummy summation indices;
- repeated denominators or summands may encode a common response kernel;
- useful compact forms often expose symmetries, invariant combinations,
  master analytic functions, generating functions, or geometric tensors;
- Piecewise branches may be coincident limits of one analytic object
  (stated as a *possibility*, not as "delete the default branch");
- introducing a named auxiliary `K(...) := ...` is allowed as a
  **hypothesis**, not as certified science.

## Forbidden (leakage; invalidates the run)

- the hidden target formula or any alphabetic permutation of it;
- the number of target generators, or their names if those names appear
  in a human reference (`Phi_Gamma`, `M_Gamma`, `T_Gamma`, nine
  `\mathcal G_alpha`, Hermite \(H_1,H_2\) as gold objects, Form I/II);
- "introduce Phi_Gamma" / "use divided differences \(H_1,H_2\)" when
  those are part of the hidden ladder;
- PRB closed-form files, `FINAL_EXACT_CLOSED_FORM.md`, scientific-line
  certificates;
- benchmark `human_reference` / `target_compact`;
- engine source, tests, git history, other items' answers.

Generic words "kernel", "master function", "confluence", "symmetry" are
**allowed**. Gold-specific identifiers are **not**.

## Guo (dev / case study)

Allowed: nonlinear DC response tensor; band indices `n,m,ell`; vertex-like
`h1,h2`; thermal polygamma/`Piecewise` strata; goal is a physically
meaningful equivalent form.

Forbidden: L3–L7 object names listed in
`docs/experiments/2026-08-21-progress-vs-prb-closed-form.md` as *the*
target construction.

Post-hoc **evaluation** may compare a finished run against that ladder.
Evaluation is not proposer context.

## Non-monotonic / hypothesis objects

A `hypothesis_definitions` map (name → exact expression) may be returned
with a candidate. It is **not** certified. Promotion, if any, requires
substituting definitions back and obtaining engine ZERO on the fully
expanded candidate versus current. Named auxiliaries may increase AST
size. That is allowed in search and is not a certified state transition.

## Checks

`proposer_view` / packet builders must not include `human_reference`,
`target_compact`, `expected_verdict`, gold ladder names, or repo paths
other than the current expression text. A run that fails this check is
`F_LEAK` and is discarded, not averaged in as success.
