# Approximation-authority classification v1

Branch: `experiment/approximation-authority-v1` from peel `783ec64`.
Experiment tree only. `src/` untouched.

## Object

```
E0 --declared approximation--> E0_tilde --exact algebra--> E1
```

Three axes: provenance × control × downstream equality.
`ZERO` remains exact `ZERO`.

## Reproduce

```bash
# frozen product environment
python experiments/approximation_authority_v1/classify.py
```

## Verdict

`FOUR_DIAGNOSTIC_CASES_DISTINGUISHED` — see `FINAL_REPORT.md`.
