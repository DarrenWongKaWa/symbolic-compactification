# Handoff — independent recovered-R2 admission audit

## Verdict

`ADMISSION_READY` for **DEV R2 calibration only**.

Audited upstream commit:
`71b34a8c4c5d7d83e4191fb4286dcd02d27c32df`.

Audited package:
`research/representation_program_search/recovery/gap_recovery/rps-candidate-k9-001`.

No candidate, predecessor, method, benchmark manifest, or TEST artifact was
modified. The audit and tests are the only new artifacts.

## Independent findings

- Official arXiv and SIAM metadata agree on title, authors, DOI, venue, and
  pages.
- A new download of arXiv `1612.02417v1` produced archive SHA-256
  `698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a`
  and `CM_dynSys.tex` SHA-256
  `59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3`.
- All six stored excerpts are byte-identical to their claimed upstream line
  slices.
- The four retained formulas are unnumbered identities at lines 705--708;
  the predecessor's “Eq. 28” name was wrong.
- The public loader reads exactly eight public files and returns the exact
  eight-symbol real namespace with four complete assumption statuses.
- Public identifiers are opaque and the public projection exposes no target
  representation, operator name/sequence, node role, source identity, or
  evaluator receipt.
- M1 reports no schema deltas. All three program variants have canonical
  hashes and compile with four non-tautological obligations.
- The representation is genuinely R2: one reused `1/sqrt(z)` latent and four
  two-node coefficients; it has no repeated nodes.
- `G_PRIMITIVE` uses only `VALUE` and `LINEAR_COMBINATION`, so the named
  `NEWTON_DD` operator is not required.
- All 12 stored session receipts are hash-bound
  `HYPOTHESIS -> ZERO/CERTIFIED/PROVEN`; independent exact replay returns
  12/12 ZERO.

## Duplicate disposition

The four member expressions are exact copies of the rejected predecessor and
must be reported as such. No other exact or alpha-renamed package match was
found. This does not create a second scientific case: the predecessor was
newly mined inside the current experiment, failed admission on packaging
grounds, and was never admitted to DEV/TEST or consumed by a search method.

Therefore the repaired package can enter DEV as the sole canonical version of
that identity. The predecessor must remain excluded/aliased, and the repair
must never be counted as a fresh mining success.

## Limitations

- The public formulas are already factorized and may make R2 unusually easy.
- P9A4 uses the generic phrase “node difference.” It gives no operator,
  sequence, pairing role, or target label, so it is not classified as target
  leakage; it remains a documented easiness risk.
- This case is R2 calibration, not evidence about the primary R3+ frontier.
- Admission is not search success, generalization, grammar advantage, or AI
  advantage.

## Artifacts

- `audits/gap_recovery_admission/INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json`
- `audits/gap_recovery_admission/INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.md`
- `audits/gap_recovery_admission/audit.py`
- `tests/test_rps_gap_recovery_admission_audit.py`

The audit was AI-assisted, but every admission gate is backed by deterministic
repository artifacts, exact verifier replay, or independently reproduced
source hashes.

## Validation

On a clean integration worktree based on
`research/representation-program-search-v1`, with audited package commit
`71b34a8c4c5d7d83e4191fb4286dcd02d27c32df` and this audit applied:

```text
tests/test_rps_gap_recovery.py + independent audit tests: 18 passed
full repository suite: 1931 passed in 420.33s
```
