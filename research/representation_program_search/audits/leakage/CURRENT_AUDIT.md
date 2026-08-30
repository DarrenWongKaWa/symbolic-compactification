# Representation Program Search — Duplicate and Leakage Audit

Policy: `RPS_DUPLICATE_LEAKAGE_AUDIT_V1`.

This is a deterministic, gold-free screening report. Similarity is review evidence; it is never an automatic rejection or scientific verdict.

## Coverage

- New dossiers: 47 (39 scientific, 8 controls)
- Previous reference documents: 79
- Scientific cases requiring review: 9

## Scientific-case findings

### rps-dp-relton-second-frechet — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `sciml-vanloan-blockexp-01` (AC_DEV), score=0.476

### rps-dp-skaflestad-wright-phisq — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `sciml-phi-hermite-01` (AC_DEV), score=0.607
- `OPERATOR_NAME_LEAKAGE` (MEDIUM): {'operator': 'RECURRENCE', 'text': 'recurrence'}

### rps-dp-stm-sensitivity-kernel — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `sciml-adjoint-linear-01` (AC_HEADLINE), score=0.407

### rps-t-dirac-gamma-completeness — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `ac-t-pauli-completeness` (AC_CHALLENGE), score=0.479

### rps-t-su3-gellmann-fierz — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `ac-t-pauli-completeness` (AC_CHALLENGE), score=0.571

### thermal-09-digamma-recurrence — MEDIUM

- `OPERATOR_NAME_LEAKAGE` (MEDIUM): {'operator': 'RECURRENCE', 'text': 'recurrence'}

### thermal-10-polygamma-recurrence — MEDIUM

- `OPERATOR_NAME_LEAKAGE` (MEDIUM): {'operator': 'RECURRENCE', 'text': 'recurrence'}

### thermal-13-alternating-fermi-series — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `thermal-05-trigamma-double-pole` (AC_DEV), score=0.427

### thermal-16-gamma-cosh-modulus — MEDIUM

- `NEAR_DUPLICATE_IDENTITY_RISK` (MEDIUM): nearest `thermal-01-fermi-im-digamma` (AC_DEV), score=0.431

## Negative-control calibration

- `nc-fabricated-toy`: no finding
- `nc-first-order-lgg`: `FIRST_ORDER_LGG_ONLY`
- `nc-grammar-bait-hermite`: no finding
- `nc-guo-sigma-abc`: `SEALED_GUO_REFERENCE`, `EXACT_DUPLICATE_IDENTITY_RISK`
- `nc-leaked-hermite-sketch`: `GRAMMAR_SYNTAX_LEAKAGE`, `OPERATOR_NAME_LEAKAGE`
- `nc-renamed-resolvent`: `HISTORICAL_ID_REFERENCE`, `NEAR_DUPLICATE_IDENTITY_RISK`
- `nc-trivial-cse`: `TRIVIAL_CSE`, `NEAR_DUPLICATE_IDENTITY_RISK`
- `nc-unverifiable-domain`: `EXACT_DUPLICATE_IDENTITY_RISK`

## Interpretation boundary

A flag means inspect the public task packaging. It does not mean the identity is duplicate, the case is invalid, or hidden gold was consulted. Exact certification and benchmark admission remain separate gates.
