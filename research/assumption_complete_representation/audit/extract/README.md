# A1 — assumption extraction

Owner: A1 (`work/ac-a-extract`). Parent `f987fcc`.
Guo G3 is sealed. This directory does **not** admit DEV/TEST.

`EXTRACT.json` maps every non-Guo miner `case_id` to assumptions taken
**literally** from that dossier’s `source_provenance` and quoted source
sentences. Skeptic negatives are controls only.

## Labels (`ASSUMPTION_CONTRACT.md`)

| label | meaning |
|---|---|
| `DECLARED` | the cited source writes the predicate |
| `DERIVED` | follows from DECLARED predicates in the same dossier (class B) |
| `NOT_DECLARED` | verifier-needed or folklore; not written by the source |

Physical folklore (`T>0`, `broadening>0`, energies real) is
`NOT_DECLARED` unless the provenance quote already states it.
Inserted Guo-style positivity (`beta>0`, `gamma>0`, real `epsilon`)
is never promoted.

A task whose verifier needs a `NOT_DECLARED` analytic-domain hypothesis
with `role: underspecified` is `PROBLEM_UNDERSPECIFIED`, not
`DISCOVERY_FAILURE`. `role: forbidden_import` is not a missing
obligation and must not be used to complete a domain.

## File

```
audit/extract/
  README.md
  EXTRACT.json
```

Top-level keys:

- `meta` — counts, policy, `guo_admitted: false`, empty `admitted_dev`
- `cases` — `case_id` → `{declared, derived, not_declared, notes, ...}`
- `controls` — C6 negatives, including `nc-guo-sigma-abc` (`is_guo: true`,
  `admitted: false`)

Each statement object is `{statement, source, kind}` with
`kind` in `{analytic_domain, positivity, nonzero, limit, derived,
branch, symbol, function_domain, algebraic}`.

`not_declared` items also carry `role`:

- `underspecified` — a verifier would need it; the source does not write it
- `forbidden_import` — the source does not write it; do **not** use it
  (folklore positivity, cross-dossier holomorphy, Guo pole-exclusion)

Companion fields on each case (`screening`, `skeptic`, `rejected`,
`is_guo`, `admitted`, `source_provenance`) are machine-readable
screening copies. **`admitted` is false for every case.** Guo case_ids
do not appear under `cases`.

## Scope

All 40 miner dossiers in `SCREENING.json` (22 keepers, 15 flagged,
3 miner-rejected). Miner-rejected records are preserved, not deleted.

Not in `cases`:

- skeptic `negative/` controls (see `controls`)
- Guo as a scientific case

## Policy notes for A2–A4

- Do not mix hypothesis lists across dossiers (Higham C^{2n-1} vs
  Noferini C^1; Higham Def. 1.4 vs Def. 1.11; table row vs
  weighting-function paragraph).
- Interval language `0 < tau < beta` is not a license to declare `T>0`.
- `eta -> 0+` / `epsilon -> 0+` is not a standing `eta>0` inequality
  unless the source writes that inequality.
- SciML `T>0` on `sciml-adjoint-linear-01` is terminal-time interval
  length (Chen `t0 < t1`), not temperature.
- SciML OU/VP `beta>0` is a diffusion-schedule parameter in the cited
  Song appendix, not inverse temperature.

No LLM proposer. No physics invention. No Guo rescue.
