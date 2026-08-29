# Case-selection rejection taxonomy

Owner: C6 (skeptic). Attack surface, not a miner. Parent contracts
`5321eaa`. Guo is sealed (`G0016 → G0013 = UNKNOWN LEVEL_B`).

Rejected dossiers are preserved under `negative/` and **never** enter
DEV / TEST / CHALLENGE of `ssc-representation-search-bench-v0.1`.
C6 does not mine positive scientific cases and does not implement
search.

A candidate is rejected if **any** code fires. Mechanical hooks live
in `reject_reasons(dossier_dict)` (`check.py`). Must-reject witnesses
live in `negative/`, indexed by `index.json`.

| Code | Name |
|---|---|
| `RENAMED_OLD_DEV_TEST` | renamed old DEV/TEST |
| `SYNTAX_REVEALS_TARGET` | syntax revealing target |
| `TRIVIAL_CSE` | trivial CSE |
| `FIRST_ORDER_LGG_ONLY` | first-order LGG-only |
| `UNVERIFIABLE_DOMAIN` | unverifiable domain |
| `FABRICATED_TOY` | fabricated toys |
| `GRAMMAR_BAIT` | tasks chosen to fit RepresentationGrammarV1 (NEWTON_DD / HERMITE_DD bait) |
| `GUO_SEALED` | Guo rescue / sealed hop |

## RENAMED_OLD_DEV_TEST — renamed old DEV/TEST

The previous assumption-complete DEV/TEST is
`HISTORICAL_DIAGNOSTIC` only (`HISTORICAL_DIAGNOSTIC.md`,
`PROBLEM_STATEMENT.md`). Miners must not submit renamed or
symbol-permuted copies. Forbidden as new headline cases include
`mp-resolvent-dd-01`, `ac-r01-resolvent-hilbert-identity`,
`mp-hermite-fA-01`, `mp-kato-simple-ev-01`, `sciml-tweedie-gauss-01`,
and the rest of that list.

Near-duplicates of those identities — same identity, renamed
symbols, opposite resolvent convention, Fermi↔Bose Im-digamma pair —
are HISTORICAL_DIAGNOSTIC or DUPLICATE_CONTROL, never headline TEST
here. Reproducing only R2 resolvent identities is not an interesting
positive for this line (`CAUSAL_EXPERIMENT.md`).

Hook: `historical_parent` / `historical_ids` / `case_id` / `title` /
`notes` mention a frozen AC identity.

Witness: `nc-renamed-resolvent`.

## SYNTAX_REVEALS_TARGET — syntax revealing target

Proposer-visible text already contains the gold object. Representation
search may not see target representation type, gold program, gold
operator sequence, or hidden member roles
(`REPRESENTATION_GRAMMAR_V1.md`). `PROGRAM_SUCCESS` requires no
target leakage (`SCORING_POLICY.md`, `SUCCESS.md`).

Forbidden needles in sketch / catalog / proposer view / title include
`HERMITE_DD`, `NEWTON_DD`, `ADD_HERMITE_DD`, `Hermite interpolant`,
`gold program`, `target representation`, `the master function is`.
A leaked Hermite name in the sketch cannot support AI_SEARCH_ADVANTAGE
or GRAMMAR_ADVANTAGE.

Hook: proposer-visible string contains a leak needle, including a
bare Hermite name.

Witness: `nc-leaked-hermite-sketch`.

## TRIVIAL_CSE — trivial CSE

The sketch is a single `Add`/`Mul` of a repeated term (`Add(K, K)`,
`K + K`, `Mul(G, G)`). Common-subexpression extraction is a compiler
pass, not representation-program search. Frozen CSE already covers
it. Not PROGRAM_SUCCESS.

Hook: `expression_sketch` is one Add/Mul with a duplicated argument.

Witness: `nc-trivial-cse`.

## FIRST_ORDER_LGG_ONLY — first-order LGG-only

The claimed structure is first-order anti-unification / substitution
holes (`f(x)`, `f(x+a)`). Frozen LGG (`efc0924`) already solves that
class. Beyond-LGG (`3214a5a`) exists because LGG is not scientific
invention. A dossier whose latent is LGG is a closed problem, not an
R3+ search case.

Hook: `latent_structure` / notes name LGG or least-general
generalization as the target. Do not scan `why_not_cse_lgg` (that
field is allowed to mention LGG while denying it).

Witness: `nc-first-order-lgg`.

## UNVERIFIABLE_DOMAIN — unverifiable domain

No public or in-repo frozen provenance, **or** a verifier-domain
hypothesis is `NOT_DECLARED`. Without `source_provenance` the
expression cannot be hashed, replayed, or checked against a source
catalog. A missing analytic disk / cut / pole set is
`PROBLEM_UNDERSPECIFIED`, not method failure (`SUCCESS.md`). Empty
or whitespace-only provenance counts as empty. Unlabeled analytic
predicates default to `NOT_DECLARED`.

Hook: `assumption_contract.source_provenance` empty or missing;
`analytic_domains` entry labeled `NOT_DECLARED` (or unlabeled).

Witness: `nc-unverifiable-domain`.

## FABRICATED_TOY — fabricated toys

Author-constructed toys, generated algebras, or “looks like Green /
thermal / tensor / matrix-function” polynomials with no scientific
source, submitted as physics. This experiment tests program search
on real scientific problems with explicit assumptions, not whether
G_FULL can compactify a hand-built interpolant.

Hook: `synthetic` flag, toy/synthetic domain, or notes that admit
construction while `domain` claims science.

Witness: `nc-fabricated-toy`.

## GRAMMAR_BAIT — NEWTON_DD / HERMITE_DD bait

The task is in the pool because `RepresentationGrammarV1` already
contains `NEWTON_DD` or `HERMITE_DD` as named primitives, so
enumerative G_FULL succeeds by emitting the operator the grammar
gave it. That is confirmation sampling, not a test of representation
**program** search.

Hermite is not Newton plus English “repeated node”
(`REPRESENTATION_GRAMMAR_V1.md`). If PROGRAM_SUCCESS exists only
under a named HERMITE_DD / MASTER-like primitive, do not overclaim
invention (causal outcome CASE C). Ablations `G_NO_HERMITE` and
`G_PRIMITIVE` exist so a bait task cannot be sold as synthesis.

A genuine scientific coincident-node interpolant from a public source
is not automatically bait. Bait is **selection because the grammar
already names the answer**.

Hook: `grammar_bait` is true, or notes / `why_not_cse_lgg` /
`selection_reason` admit grammar-fit / HERMITE_DD / NEWTON_DD bait.

Witness: `nc-grammar-bait-hermite`.

## GUO_SEALED — Guo remains sealed

Guo cannot enter DEV/TEST on this line (`GUO_POLICY.md`). Frozen
hop:

```
G0016 → G0013 = UNKNOWN LEVEL_B
```

Forbidden: new Guo search, physical assumptions, prompt-tuning,
verifier rescue, inserting `beta>0` / `gamma>0` / real `epsilon`,
Track-D Hermite **on Guo**, headline positive result. A future
**human** may define a new Guo problem; C1–C6 may not. Include Guo
only as a negative control, already rejected.

Hook: `is_guo` is true, or `case_id` / `title` / `name` contains
`guo`.

Witness: `nc-guo-sigma-abc`.
