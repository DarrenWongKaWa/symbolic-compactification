# Table — Masked forward replay on Guo (RQ1 supplement)

Public experiment on `experiment/forward-proposer-replay-v1`, frozen
product peel `783ec64`. Not a leaderboard. Gold is a pipeline control,
not proposer success. Equivalent mathematical forms count as recovery.

| Source | Role | TargetRecovery | Promoted vs \(E_t\) | False promotion |
|---|---|---|---|---|
| Gold hidden target | control | 8/8 | 6/8 (`NONZERO` on FR-06, FR-08) | n/a |
| Masked LLM, \(K=4\) | proposer | 8/8 tasks | algebraic yes; substitution forms recovered then refused | n/a |
| SymPy CAS rewrites | proposer | 6/8 | stay-put `ZERO` on algebraic tasks | n/a |
| gplearn 0.4.3 raw | third-party SR | 0/8 | `PARSE_FAILURE` or `NONZERO` | n/a |
| gplearn identity copy | not SR discovery | 6/8 (copy of \(E_t\)) | stay-put | n/a |
| Injected invalids (sign, \(\times 2\), \(0\), \(+1\)) | adversarial | n/a | 0 / 36 | **0** |
| FR-NC-01 collapse to \(0\) | negative control | n/a | 0 / 1 | 0 |

MS-01 (FR-01→FR-02→FR-03, not paper-adjacent): gold / first-LLM /
first-CAS accepted 3/3. An injected FR-01 sign error was refused and did
not block a later gold candidate of the original state.

Substitution gap: FR-06 and FR-08 recover the hidden printed form and
remain `NONZERO` versus current, because \(\varepsilon_{21}=-\varepsilon_{12}\)
and \(f_{n}'=2f_{0,n}'\) are not Mode A assumptions.
