# K handoff — duplicate and target-leakage audit

Owner: K (duplicate / leakage audit)

Branch: `work/rps-leakage-audit`

## Delivered

- Deterministic audit implementation:
  `audits/leakage/audit.py`
- Frozen policy and usage notes:
  `audits/leakage/README.md`
- Full machine report:
  `audits/leakage/CURRENT_AUDIT.json`
- Human review queue:
  `audits/leakage/CURRENT_AUDIT.md`
- Focused tests:
  `tests/test_rps_leakage_audit.py`

The audit compares all 39 scientific dossiers and 8 skeptic controls with 79
previous source documents: all available AC DEV / HEADLINE TEST / CHALLENGE /
DUPLICATE_CONTROL case dossiers, Historical Diagnostic cases, and prior
benchmark task documents. Sealed Guo is checked by identifiers only; no Guo
search or hop execution occurs.

## Gold firewall

Duplicate similarity reads only source-facing formulas/catalog members, title,
and public citation identifiers. It does not read latent structures,
`proposed_ladder`, target type, gold program, hidden instance maps, or operator
sequences. First-order-LGG screening separately reads only declared dossier
metadata and is labeled as such.

Leakage screening uses an explicit `proposer_view` when present; otherwise it
uses the conservative frozen fallback of `title`, `expression_sketch`,
`source_catalog`, and `catalog`. Internal statements such as “not Guo” and
“distinct from historical-X” are excluded. Every evidence object records the
projection that triggered it.

Similarity never rejects a case. Every finding has `auto_reject=false`, the
recommendation is `MANUAL_REVIEW`, and `admission_decision` is `null`.

## Scientific review queue (39-case headline)

No scientific dossier has a CRITICAL or HIGH finding. Nine have MEDIUM review
risks:

| new case | finding | nearest historical case / detail |
|---|---|---|
| `rps-dp-relton-second-frechet` | near-duplicate structure | `sciml-vanloan-blockexp-01` (AC DEV), formula similarity 0.750, content Jaccard 0.213 |
| `rps-dp-skaflestad-wright-phisq` | near-duplicate structure; operator-name leakage | `sciml-phi-hermite-01` (AC DEV), max fragment similarity 1.000, content Jaccard 0.191; proposer fallback says “recurrence” |
| `rps-dp-stm-sensitivity-kernel` | near-duplicate structure | `sciml-adjoint-linear-01` (AC headline), formula similarity 0.647, content Jaccard 0.169 |
| `rps-t-dirac-gamma-completeness` | near-duplicate identity family | `ac-t-pauli-completeness` (AC challenge), formula similarity 0.693, shared public Fierz source |
| `rps-t-su3-gellmann-fierz` | near-duplicate identity family | `ac-t-pauli-completeness` (AC challenge), formula similarity 0.893, content Jaccard 0.266 |
| `thermal-09-digamma-recurrence` | operator-name leakage | proposer fallback says “recurrence” |
| `thermal-10-polygamma-recurrence` | operator-name leakage | proposer fallback says “recurrence” |
| `thermal-13-alternating-fermi-series` | near-duplicate structure | `thermal-05-trigamma-double-pole` (AC DEV), formula similarity 0.667, content Jaccard 0.200 |
| `thermal-16-gamma-cosh-modulus` | near-duplicate structure | `thermal-01-fermi-im-digamma` (AC DEV), formula similarity 0.648, content Jaccard 0.250 |

These are review prompts, not claims that the cases are duplicates. The
highest-priority scientific review is the SU(3) Gell-Mann Fierz case because it
is closest to the historical Pauli completeness identity family. The
Skaflestad-Wright case shares a short primitive `phi_0(z)=exp(z)` with the old
phi dossier; the short-fragment guard correctly prevents that primitive alone
from becoming an exact-duplicate finding.

The other 30 scientific dossiers have no finding at the frozen thresholds.
There are no current scientific literal grammar-action leaks, hidden
member-role leaks, trivial-CSE cases, first-order-LGG-only cases, sealed-Guo
references, or exact/alpha-renamed duplicates.

## Negative-control calibration

- `nc-renamed-resolvent`: explicit Historical Diagnostic ancestry plus
  near-duplicate match to `mp-resolvent-dd-01`.
- `nc-leaked-hermite-sketch`: literal `HERMITE_DD`, `NODES[...]`, “gold
  program,” and target-representation syntax.
- `nc-trivial-cse`: repeated top-level `Add(chi0, chi0)`.
- `nc-first-order-lgg`: declared R1 / first-order LGG.
- `nc-guo-sigma-abc`: sealed Guo name / flag, identifier-only audit.
- `nc-unverifiable-domain`: exact source-formula match to the analogous old
  assumption-contract control (informational for this audit).

`nc-fabricated-toy` and `nc-grammar-bait-hermite` intentionally exercise other
skeptic rules, so this focused audit does not claim to detect them.

## Validation

```text
/Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_leakage_audit.py tests/test_rps_skeptic.py
18 passed
```

The test suite covers deterministic output, corpus coverage, exact and renamed
matching, proposer-view isolation, syntax/operator leakage, hidden member
roles, trivial CSE, first-order LGG, sealed Guo identifiers, and the long-sketch
CSE false-positive guard.

## Coordinator action

Before admission/freeze, manually adjudicate the nine MEDIUM rows. Package an
explicit proposer view for every admitted task; the fallback audit proves only
that the current dossier source fields can be screened, not that final public
task packaging is frozen.
