# Remainder-certification ownership

Shared (orchestrator): `schema.py`, `PROTOCOL.md`,
`PROBLEM_STATEMENT.md`, `ASSUMPTION_POLICY.md`, `STATUS.md`.

| agent | worktree | owns |
|---|---|---|
| R1 complex analysis | `work/r-complex-analysis` | `analysis/` |
| R2 polygamma domain | `work/r-polygamma-domain` | `polygamma/` |
| R3 neighborhood | `work/r-neighborhood` | `neighborhood/` |
| R4 Cauchy bound | `work/r-cauchy-bound` | `cauchy/` |
| R5 order algebra | `work/r-order-algebra` | `order_algebra/` |
| R6 polygamma derivatives | `work/r-polygamma-derivatives` | `derivatives/` |
| R7 affine normalizer | `work/r-affine-normalizer` | `affine/` |
| R8 certificate compiler | `work/r-cert-compiler` | `compiler/` |
| R9 analysis falsifier | `work/r-analysis-falsifier` | `falsifier/` |
| R10 assumption audit | `work/r-assumption-audit` | `assumption_audit/` |
| R11 numeric sanity | `work/r-numeric-sanity` | `numeric/` |
| R12 literature | `work/r-literature` | `literature/` |
| R13 alternatives | `work/r-alternatives` | `alternatives/` |

Do not edit another agent's directory. Do not edit frozen V5 files
except adding the remainder-regression test owned by the
orchestrator (`tests/test_cl_engine.py`).
