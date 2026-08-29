# Case-selection rejection taxonomy

Owner: C6 (skeptic). Attack surface, not a miner. Guo is sealed
(`G0016 → G0013 = UNKNOWN LEVEL_B`). Rejected dossiers are preserved
and never enter DEV / TEST / CHALLENGE.

A candidate is rejected if **any** code fires. Mechanical hooks live in
`reject_reasons(dossier_dict)` (`check.py`). Negative controls that
must fire live in `negative/`.

| Code | Name |
|---|---|
| `TRIVIAL_CSE` | trivial CSE |
| `OBVIOUS_LGG` | obvious LGG |
| `TARGET_LEAKED_BY_NOTATION` | target leaked by notation |
| `UNVERIFIABLE` | unverifiable |
| `UNDER_SPECIFIED` | under-specified |
| `SYNTHETIC_DISGUISED_AS_SCIENTIFIC` | synthetic disguised as scientific |
| `SELECTED_BECAUSE_METHOD_WORKS` | selected because the method already works |
| `GUO_RESCUE` | Guo rescue |
| `SILENT_PHYSICS_POSITIVITY` | silent physics positivity |

## TRIVIAL_CSE — trivial CSE

The sketch is a single `Add`/`Mul` of a repeated term (`Add(K, K)`,
`K + K`, `Mul(G, G)`). Common-subexpression extraction is a compiler
pass, not representation discovery. Frozen CSE / observations-layer
`CSE_SHARED` already covers it. Not `SCIENTIFIC_DD_OK`.

Hook: `expression_sketch` is one Add/Mul with a duplicated argument.

## OBVIOUS_LGG — obvious LGG

The claimed structure is first-order anti-unification / substitution
holes (`f(x)`, `f(x+a)`). Frozen LGG (`efc0924`) already solves that
class. Beyond-LGG (`3214a5a`) exists because LGG is not scientific
invention. A dossier whose `latent_structure` is LGG is a closed
problem, not an AC case.

Hook: `latent_structure` / notes name LGG or least-general
generalization as the target.

## TARGET_LEAKED_BY_NOTATION — target leaked by notation

Proposer-visible text already contains the gold object. Admission
gate item 7: no gold names / target wording. Forbidden needles
include `Hermite-on-Guo`, `Phi_Gamma`, and `the master function is`.
A leaked target cannot support `AI_UNIQUE_SUCCESS`.

Hook: any string field contains a leak needle.

## UNVERIFIABLE — unverifiable

No public or in-repo frozen provenance. Without
`source_provenance` the expression cannot be hashed, replayed, or
checked against a source catalog. Admission gate item 1 fails.
Empty / whitespace-only lists count as empty.

Hook: `assumption_contract.source_provenance` empty or missing.

## UNDER_SPECIFIED — under-specified

A verifier-domain hypothesis is `NOT_DECLARED`. That is
`PROBLEM_UNDERSPECIFIED`, not `DISCOVERY_FAILURE`. Missing predicate
labels default to `NOT_DECLARED` (schema default). Analytic disks,
cuts, and pole sets the verifier may use must be `DECLARED` or
`DERIVED`.

Hook: `analytic_domains` entry labeled `NOT_DECLARED` (or unlabeled).

## SYNTHETIC_DISGUISED_AS_SCIENTIFIC — synthetic disguised as scientific

Author-constructed toys, generated algebras, or “looks like Green /
thermal / tensor” expressions with no scientific source, submitted
as physics. The AC question is about real scientific problems with
explicit assumptions, not about whether the method can compactify a
hand-built polynomial.

Hook: `synthetic` / toy domain, or notes that admit construction
while `domain` claims science.

## SELECTED_BECAUSE_METHOD_WORKS — selected because the method already works

The case is in the pool because a frozen track already compactified
it, or because the miner writes that the method “already works” on
it. That is confirmation sampling, not a test of assumption-complete
discovery. Known successes of CSE, LGG, Newton DD toys, or Guo-line
hops are not new AC DEV.

Hook: notes / `why_not_cse_lgg` admit method-already-works selection.

## GUO_RESCUE — Guo rescue

Guo cannot enter DEV/TEST on this line (`GUO_POLICY.md`,
`guo_is_not_admitted`). Forbidden: prompt-tuning, verifier extension,
inserting `beta>0` / `gamma>0` / real `epsilon`, reading “finite
Gamma” as `gamma>0`, PRB-gold import, Track-D Hermite **on Guo**,
headline positive result, Remainder V2. A future human may define a
new Guo problem; C1–C6 may not.

Hook: `is_guo` is true, or `case_id` / `title` / `name` contains
`guo`.

## SILENT_PHYSICS_POSITIVITY — silent physics positivity

Physical folklore (`T>0`, `beta>0`, `gamma>0`, `broadening>0`,
energies real) used as if declared. `ASSUMPTION_CONTRACT.md`: folklore
is `NOT_DECLARED` unless the source writes it. Source-assumption
audit `9fc3c8a`: frozen Guo reals do not derive pole exclusion.
Inserting positivity to rescue a hop is a human change of the
problem, not a case.

Hook: positivity folklore in the dossier without a `DECLARED`
positivity predicate, or `positivity_conditions` labeled
`NOT_DECLARED`.
