# Experiment A/B metrics

Records: 124

## Gold control (not proposer success)

- target recovery: 8/8
- promoted vs current: 6/8

## TargetRecovery@K (gold excluded)

| proposer | K | recovered tasks | rate |
|---|---:|---:|---:|
| cas_sympy | 4 | 6/8 | 0.750 |
| gplearn | 2 | 6/8 | 0.750 |
| llm_masked | 4 | 8/8 | 1.000 |
| gplearn-raw only | 1 | 0/8 | 0.000 |

gplearn @K=2 is inflated by `gplearn-identity` (copy of \(E_t\)). Raw SR
programs recovered 0/8 hidden targets.

Gold control: 8/8 target recovery; 6/8 promoted vs current. FR-06 and
FR-08 recovered the hidden formula and remained `NONZERO` versus current.

## Experiment B — injected negatives

- n = 36
- false promotions = 0
- false promotion rate = 0.0
- status histogram = {'NONZERO': 36}

## Promotion status histogram (all candidates)

`{'ZERO': 68, 'PARSE_FAILURE': 7, 'NONZERO': 48, 'UNKNOWN': 1}`

## FR-NC-01 remainder collapse to 0

- zero-collapse candidates: 1
- promoted: 0

