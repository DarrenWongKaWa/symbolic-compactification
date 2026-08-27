# Calibration suite (DEV only)

Purpose: find schema failures, verbosity, hallucinated structure,
over-generalization, failure to abstain, and unnecessary machinery
**before** Guo and before any held-out TEST.

| id | phenomenon | gold (evaluator only) |
|---|---|---|
| CAL-A-cse | trivial CSE | `repeated_kernel` |
| CAL-B-lgg | substitution family | `parameterized_family` `V(θ)G0(θ)V(θ)` — interpolation is `UNNECESSARY_STRUCTURE` |
| CAL-C-deriv | derivative family | `derivative_family` / `master_function` |
| CAL-D-perm | permutation | `symmetry_invariant` |
| CAL-E-neg | unrelated channels | abstain; do not certify a shared template |
| CAL-F-shallow | F1 shallow LGG trap | abstain or mark shallow; not a master |
| CAL-G-confluence | F5 specialize | `confluent_representation` |
| CAL-H-reprechg | F6 new language | `basis_reduction` / new head |

Conditions A0–A3, 1 seed, `deepseek-v4-pro`.

The smoke-test interpolation `O(z)=V(z)G0(z)V(z)` with affine/geodesic
`z` is the warning this suite is designed to catch on CAL-B.

## Calibration outcome (1 seed, frozen prompts)

- PARSE_FAILURE: 0/32
- UNNECESSARY_STRUCTURE (interpolation/geodesic): 0/32 on CAL-B
- CAL-F: A0/A2/A3 abstain; A1 over-proposes
- CAL-G: RAW missed confluence typing; A2/A3 hit
- CAL-H: no new-head `basis_reduction`
- Schema/json_object held; no prompt retune after this suite

Results: `runs/calibration/` and `RESULTS_DEV.csv`.
