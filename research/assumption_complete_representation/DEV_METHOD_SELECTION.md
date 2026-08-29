# DEV method selection

Authority: DEV_EXECUTION_FREEZE.json, 135-run matrix, scorer ac-score-v1.3.
Guo excluded. TEST not used. PACKAGING_GAP (8/14) not in this matrix.

## Predeclared criteria (cluster-weighted)

1. OPERATIONAL_SUCCESS
2. CERTIFIED_DEPTH
3. false-abstraction (tautological) rate
4. robustness across domains
5. token cost (secondary)

Do not select by TYPE_CORRECT alone.

## Cluster-weighted rates (5 units for P0–P3; 2 for P4)

| condition | OP | mean CERTIFIED_DEPTH | tautological | mean tokens |
|---|---|---|---|---|
| P0 RAW | **0.12** | 2.0 | **0.46** | **7715** |
| P1 BASIC | 0.10 | 2.0 | 0.48 | 8460 |
| P2 SOL | 0.06 | 2.0 | 0.54 | 9213 |
| P3 GROUNDED | 0.08 | 2.0 | 0.66 | 9729 |
| P4 coalescence (eligible only) | 0.20 | 2.0 | 0.50 | 9575 |

P4 is not a general condition (3 tasks / 2 clusters).

## Task-level operational ZERO (v1.3: two-point F required)

Only RESOLVENT_CLUSTER certifies:

| task | P0 | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|
| mp-resolvent-dd-01 | 4/5 | 2/5 | 3/5 | 3/5 | 4/5 |
| ac-r01 | 2/5 | 3/5 | 0/5 | 1/5 | 0/5 |
| sciml-phi-hermite-01 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| thermal-01/03/05 | 0 | 0 | 0 | 0 | n/a |

max CERTIFIED_DEPTH = R2. Proposed R3/R5/R6 does not certify.

## Causal notes (DEV only)

- P0 → P2: SOL does **not** raise operational success. ac-r01 collapses 2/5 → 0/5. Tautological rate rises. Observation-induced prior, not a gain.
- P0 → P1: mixed (helps ac-r01, hurts mp-resolvent). Not a SOL-specific effect.
- P3: higher tautological rate; no depth gain.
- P4: type-correct on phi becomes 5/5 but ZERO stays 0. Naming ≠ certification.

## Selection

**GENERAL_FINAL = P0 RAW**

Reasons: highest cluster-weighted OP among P0–P3; lowest tautological rate; lowest tokens; SOL and P3 do not beat RAW; certified depth tied at R2.

**SPECIALIST_DD = P4** (eligible unlabeled DD/repeated-node families only; not the headline method).

No prompt version 2. First of at most three versions remains V1.
