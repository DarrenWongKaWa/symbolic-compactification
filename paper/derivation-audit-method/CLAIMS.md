# Frozen paper claims

Central question:

> How can AI-assisted symbolic derivations be made machine-auditable
> without granting the AI authority to certify its own claims?

## The paper MAY claim

- machine-auditable equation-level derivation verification
- fail-closed symbolic adjudication (`ZERO` / `NONZERO` / `UNKNOWN`)
- source-grounded provenance
- explicit distinction between local exact and theorem-mediated certificates
- reproducible reviewer packages
- end-to-end public real-paper validation

## The paper MUST NOT claim

- full formal proof of a manuscript
- verification of physical conclusions
- autonomous scientific discovery
- general theorem proving
- complete support for integrals / limits / asymptotics
- robust representation invention

## Approved public field-validation statement

> The Derivation Audit pipeline has been exercised end-to-end on a
> published theoretical-physics derivation.

> This is an equation-level audit and does not prove the paper or confirm
> its physical conclusions.

## Approved public metrics (Guo et al., arXiv:2511.16422v2)

Formative field validation. 189 numbered equations → 25 selected paper steps.

```text
Paper-level engine ZERO = 18
    DIRECT_EXACT = 12
    SUBSTITUTION_EXACT = 6
RULE_CERTIFICATE = 2
ASYMPTOTIC UNKNOWN = 1
Structural records = 4
NONZERO = 0
Complete-run ZERO records = 19
    (18 paper-level + 1 shared Leibniz helper, not a paper step)
```

Certificate classes describe **provenance**, not a hierarchy of truth.

## Private-manuscript policy

Unpublished local scientific manuscripts are excluded. Do not cite them,
describe them, report counts from them, reproduce their equations, or
mention their validation results in this public methods paper.
