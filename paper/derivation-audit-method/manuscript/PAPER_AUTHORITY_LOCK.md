# Paper authority lock

This file is the manuscript constitution. `draft-v3`, `draft-v4`, figures,
Related Work, humanizer output, and contribution sentences must obey it.
If another working file disagrees, this file wins.

Do not polish prose, draw final figures, or run a humanizer until the
Claim–Evidence Matrix is frozen against this lock.

---

## Software authority

```text
Software authority
  v0.3.0-alpha @ f1d225e

Release
  https://github.com/DarrenWongKaWa/symbolic-compactification/releases/tag/v0.3.0-alpha

Package
  0.3.0-alpha (PEP 440 0.3.0a0)

Engine
  0.3.0   exact-adjudication kernel unchanged from 0.2.1
  ZERO means exact engine ZERO
  ZERO ≠ CERTIFIED_BY_RULE
  UNKNOWN never promotes
  proposal authority ≠ verification authority
  core verification: no model service, no API key

Product surface
  Forward derivation
  Paper audit
  Historical "Mode A" / "Mode B" = lineage only
```

## Do not use as scientific authority

```text
Do not use as scientific authority
  main
  a10e4b5          (Python 3.10 tomllib test-import hygiene only)
  old v0.2.1 README
  historical engineering branches
  deleted experiment branches
  later main commits unless a future patch release is explicitly authorized
```

Cite live `main` only to disclose that a test-import patch exists and that
the tag was not moved. Do not cite `main` for counts, semantics, or demos.

Historical tags remain unmoved lineage, not this paper's software identity:

- `derivation-audit-v0.2.0-alpha` → `aaf1199`
- `derivation-audit-v0.2.1-alpha` → `783ec64`

---

## Depth evidence

```text
Depth evidence
  Guo flagship
  source: Zhichao Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2
  product table: examples/flagship/guo/RESULTS.md on v0.3.0-alpha
  archive: archive/guo-full-paper-audit-flagship-v1 @ d92f3ec
  verdict: FULL_PAPER_AUDIT_DEMONSTRATED

  189/189 equations inventoried
  146 source-grounded relations
  53 executable numbered relations
  + 1 local Leibniz helper (not a numbered-equation row)
  EXACT_ZERO 32
  ZERO_UNDER_SUBSTITUTION 21
  CERTIFIED_BY_RULE 11
  UNKNOWN_REMAINDER 17
  STRUCTURAL 47
  UNSUPPORTED 18
  NONZERO 0
  false promotion 0/155
```

Inventory coverage ≠ certified residuals. The paper may say 189/189
equations were **inventoried**. It may not say 189 equations were
**verified**.

Selected-edge precursor (`archive/guo-selected-edge-validation-v1` @
`69ad474`) is lineage, not the flagship public result.

---

## Breadth evidence

```text
Breadth evidence
  five-paper sampled stress
  archive: archive/prd-cross-paper-stress-v1 @ 4f12401

  5 papers
  41 sampled edges
  EXACT_ZERO 10
  ZERO_UNDER_SUBSTITUTION 10
  CERTIFIED_BY_RULE 1
  UNKNOWN / UNKNOWN_REMAINDER 7
  STRUCTURAL 8
  PARSE_FAILURE / COMPILE_FAILURE 3
  NONZERO 0
  false promotion 0/30
  NOT five full-paper audits
```

Experiment-tree statuses `CERTIFIED_UNDER_DECLARED_APPROXIMATION` and
`UNDECLARED_APPROXIMATION_REQUIRED` are diagnostics in that campaign.
They are **not** v0.3.0-alpha product statuses.

---

## Forward evidence

```text
Forward evidence
  product demos on v0.3.0-alpha
    examples/forward/exact-step     ZERO
    examples/forward/refused-step   NONZERO; current not rewritten
  session tests with a scripted proposer
  masked replay: archive/forward-proposer-replay-v1 @ b9b6972
    peel 783ec64, engine 0.3.0 (same kernel as v0.3.0-alpha)
    injected invalids: false promotion 0/36
    gold recovered as expressions: 8/8
    gold promotion-eligible vs current: 6/8
    gplearn-raw TargetRecovery: 0/8
  FORWARD_WORKFLOW_DEMONSTRATED_WITH_CAVEATS
```

Caveats that must travel with any replay sentence: no shipped `propose`
command; notes name the intended operation (not a blind puzzle);
pretraining contamination unmeasured; substitution identities such as
\(\varepsilon_{21}=-\varepsilon_{12}\) are not machine-enforced workspace
assumptions; TargetRecovery@K is not the scientific headline.

---

## Approximation

```text
Approximation
  discussion / RQ4 candidate only
  archive: archive/approximation-authority-v1 @ 5477cf2
  not product capability
  do not enter the contribution list
```

Permitted Discussion sentence (may be edited for style, not strength):

> A further extension would distinguish author-declared approximation
> authority from exact verification of downstream algebra, without
> weakening engine `ZERO`.

---

## Shared object the paper may name

\[
\gamma=(e_{\mathrm{from}},e_{\mathrm{to}},\tau,\rho,A)
\]

Two independent axes:

- \(\tau\): claimed mathematical move
- \(c\): certificate provenance

Engine triad `{ZERO, NONZERO, UNKNOWN}` is adjudication, not a ranking of
certificate classes.

Evidence chain:

```text
proposal / extraction is untrusted
  → typed scientific claim
  → deterministic evidence
  → fail-closed scientific state
```

---

## Forbidden upgrades (humanizer and later drafts)

These substitutions are always illegal:

| From | To |
|---|---|
| demonstrated | proves / proof of the paper |
| sampled | general / holds for theory papers |
| inventoried / inventory | verified / certified / proved |
| candidate | product capability / shipped feature |
| under declared substitution | unconditional equality |
| `CERTIFIED_BY_RULE` | engine `ZERO` |
| `UNKNOWN` | support, near-miss, or permission to promote |
| formative | held-out / independent generalisation |
| experimental proposer | autonomous discovery |

---

## Private-manuscript policy

Unpublished local scientific manuscripts are excluded from this public
paper. Do not cite, describe, count, or reproduce them.

---

## Closure pipeline (do not skip)

```text
Authority Lock
  → Claim–Evidence Matrix
  → Related Work re-audit
  → Figures
  → Venue freeze
  → draft-v4
  → Humanizer
  → semantic diff against this lock
  → Adversarial pre-submission review
```

No new product experiments.
