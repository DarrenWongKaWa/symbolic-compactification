# C1 — response / Green candidate dossiers

Owner: C1 (`work/ac-case-response`).
Parent: `1075d80`. Not admitted to DEV.

This directory holds **dossiers only** for publicly documented Green functions,
Kubo-like kernels, perturbative resolvents, and finite-T response identities
with **explicit** source assumptions. JSON records are `CandidateDossier`
objects (`schema.py`). Markdown files restated the same fields.

Guo G3 is sealed. No Guo case, no `Phi_Gamma`, no Hermite-on-Guo, no inserted
`beta>0` / `gamma>0` / real `epsilon` rescue.

## Layout

```
cases/response/
  README.md
  CANDIDATES.md
  dossiers/*.json
  dossiers/*.md
```

## Scope vs C2

Finite-T **response/Green** kernels (Matsubara poles, Lehmann master,
occupation divided differences) are in this pack.
Polygamma / Bose thermal compactifications are left to C2 `cases/thermal/`.

## Counts

- candidates: 8
- rejected: 1 (`ac-r08`, `PROBLEM_UNDERSPECIFIED`)
- `is_guo`: all false

Do not run admission. Do not add these to DEV.
