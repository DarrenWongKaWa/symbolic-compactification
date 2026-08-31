# Derivation Audit Alpha — symbolic-compactification 0.2.0-alpha

**Pre-release / Research Preview Alpha.** Not a stable v1.0.

Machine-auditable symbolic derivation verification for theoretical and
mathematical physics, validated end-to-end on a published PRL derivation,
with source-grounded proof obligations and fail-closed exact adjudication.

- Tag: `derivation-audit-v0.2.0-alpha`
- Branch: `engineering/derivation-audit-v0.2`
- Package: `0.2.0-alpha` (PEP 440 `0.2.0a0`)
- Engine (unchanged ZERO/NONZERO/UNKNOWN semantics): `0.3.0`

## What is supported

```text
manuscript equations
  → typed derivation edges
  → executable obligations
  → ZERO / NONZERO / UNKNOWN
  → reviewer verification package
```

```bash
ssc audit init <dir>
ssc audit inventory <dir>
ssc audit inspect <dir>
ssc audit verify <dir>
ssc audit table <dir>
ssc audit report <dir>
ssc audit package <dir>
cd reviewer-verification-package && ./reproduce.sh
```

v0.1 Mode A (`init` → `inspect` → `verify` → `report`) remains supported.

## Design invariants

- The verified table is generated, not authored.
- LLM / agent text has no authority to assign ZERO, VERIFIED, or CERTIFIED.
- Finite coefficient agreement is not a proof of an asymptotic remainder.

## Public demos

Only these three public examples ship with the alpha:

| Demo | What it shows |
|---|---|
| A | Algebraic equation-to-equation identities → multiple ZERO |
| B | Typed steps (index relabeling, projector, pairwise) plus DEFINITION / RECORDED |
| C | Laurent coefficient ZERO, enclosing asymptotic remainder UNKNOWN |

Demo C is the soundness demo: the tool will not rewrite a remainder claim as
an exact identity to force a green row.

## What this is not

- not “AI proves your paper”
- not a guarantee that a derivation is correct
- not an autonomous theoretical physicist
- not a formal proof assistant
- not a claim that every manuscript step can be certified

Exact algebraic and local structural identities that were lowered to
executable residuals were evaluated under the declared symbolic semantics.
Only obligations returning exact ZERO are listed as machine-verified.
Definitions, integral-level arguments, asymptotic remainder claims, and
unsupported transformations are tracked separately.

## Release gates

| Gate | Result |
|---|---|
| Clean install (CPython 3.12) | PASS |
| `pytest -m derivation_audit_release_critical` | PASS |
| `pytest -m release_critical` (v0.1) | 17/17 PASS |
| Clean-room replay | PASS |
| Public demos A / B / C + `reproduce.sh` | PASS |
| Reviewer package regenerates tables from the bound run | PASS |

## Install

```bash
git clone --branch derivation-audit-v0.2.0-alpha \
  https://github.com/DarrenWongKaWa/symbolic-compactification.git
cd symbolic-compactification
python3.12 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/symbolic-compactification --version
```

Read `docs/DERIVATION_AUDIT_LIMITATIONS.md` before using a result in
scientific work.

## Post-release validation

After the `derivation-audit-v0.2.0-alpha` tag, the frozen pipeline was
exercised on a published paper **without changing the verifier core** and
**without retagging v0.2**:

Guo et al., arXiv:2511.16422v2 / Phys. Rev. Lett. 136, 206303 (2026).

- 25 selected derivation edges
- 18 executable identities returned exact ZERO (12 `DIRECT_EXACT`, 6 `SUBSTITUTION_EXACT`)
- 0 NONZERO
- Eq. (D-57) $\mathcal{O}(\Gamma)$ remainder remained `UNKNOWN`
- two global BZ integration-by-parts steps remained `NOT_LOWERED`

This is an equation-level derivation audit, not a proof of the paper.

Branch: `engineering/real-paper-validation-arxiv-2511-16422`  
Report: `examples/real_papers/arxiv_2511_16422/VALIDATION_REPORT.md`  
Reproduce: `examples/real_papers/arxiv_2511_16422/reproduce.sh`
