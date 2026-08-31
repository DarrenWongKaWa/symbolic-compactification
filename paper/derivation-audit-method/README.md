# Methods paper workspace

**Writing and analysis only.** This directory must not modify Derivation
Audit product semantics.

| Field | Value |
|---|---|
| Working title | Machine-Auditable Derivation Verification for Theoretical Physics |
| Alternative title | Fail-Closed Verification of AI-Assisted Symbolic Derivations |
| Forbidden titles | “Autonomous Theoretical Physicist”; “AI Discovers Physics” |
| Product tag | `derivation-audit-v0.2.1-alpha` (`783ec64`) |
| Historical tag | `derivation-audit-v0.2.0-alpha` (`aaf1199`, do not move) |
| Evidence branch | `engineering/real-paper-validation-arxiv-2511-16422` (`69ad474`) |
| Draft status | `manuscript/draft-v0.md` — complete first draft |
| Engineering | **CLOSED** (`ENGINEERING_V0_2_CLOSED.md`) |

## Central question

> How can AI-assisted symbolic derivations be made machine-auditable
> without granting the AI authority to certify its own claims?

## Layout

```text
README.md                 this index
STATUS.md                 draft / freeze status
TITLE.md                  titles and anti-titles
CLAIMS.md                 allowed and forbidden claims
CONTRIBUTIONS.md          C1–C7
OUTLINE.md                section plan
REPRODUCIBILITY.md        public artifacts every result must cite
HANDOFF.md                engineering-closure / paper-handoff report
figures/                  Figure 1–4 plans (existing evidence only)
tables/                   Table 1–4 plans (existing evidence only)
manuscript/draft-v0.md    first complete manuscript draft
bib/references.bib        public bibliographic seeds
```

## Method (frozen)

```text
manuscript / derivation
    → equation inventory
    → typed derivation graph
    → source-grounded proof obligations
    → deterministic verification
    → evidence-bound certificate
    → generated reviewer tables
```

The method separates **proposal** from **authority**.

## Do not

- add a second paper case
- expand verifier coverage
- add rules
- tune results
- modify product
- rerun scientific-discovery experiments

until a later human authorization. If the draft needs a presentation
artifact, build it from existing public evidence.

## Public field-validation case

Guo et al., *Phys. Rev. Lett.* **136**, 206303 (2026), arXiv:2511.16422v2.
Workspace on the evidence branch:

[`examples/real_papers/arxiv_2511_16422/`](https://github.com/DarrenWongKaWa/symbolic-compactification/tree/engineering/real-paper-validation-arxiv-2511-16422/examples/real_papers/arxiv_2511_16422)

Approved public metrics (25 selected paper steps):

```text
MACHINE ZERO = 19
    DIRECT_EXACT = 13
    SUBSTITUTION_EXACT = 6
RULE_CERTIFICATE = 2
ASYMPTOTIC UNKNOWN = 1
NONZERO = 0
```

This is an equation-level audit and does not prove the paper or confirm
its physical conclusions.

Unpublished local scientific manuscripts are excluded from this paper.
