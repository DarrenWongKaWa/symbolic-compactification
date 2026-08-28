# HANDOFF — V3-J (adversarial iterated-path falsifier)

Branch: `work/v3-falsifier`
Parent: `dcfb90cac087a47241aced2dc0c3b851f1a12e21`
Owned: `research/iterated_confluence/falsifier/**`, `tests/test_ic_falsifier.py`
Tests: `.venv/bin/python -m pytest tests/test_ic_falsifier.py -q`

False FAMILY_ZERO: **0**. Two commuting polynomial controls remain FAMILY_ZERO
with path consistency CONSISTENT_ZERO.

Did not edit `schema.py`, freeze/runs, or sibling V3 packages. Local exact
checks fill step / reconstruction / iterated-end verdicts;
`compose_path_verdict` and `compose_family_verdict` are the only composition
rules. Majority PATH_ZERO and one-path PATH_ZERO are recorded as traps,
never as certificates.

## Attacks (must not be FAMILY_ZERO)

| id | family verdict | trap | defect |
|---|---|---|---|
| V3J_01_one_path_zero_other_nonzero | FAMILY_NONZERO | one PATH_ZERO | second path x→y claims 3y, true 2y |
| V3J_02_noncommuting_limits | FAMILY_NONZERO | both paths PATH_ZERO | x/(x+y) orders 1 vs 0; INCONSISTENT_NONZERO |
| V3J_03_hidden_pole | FAMILY_NONZERO | polynomial sibling PATH_ZERO | polar (x²−y²)/(x−y)²; dirs infinite |
| V3J_04_corrupted_intermediate | FAMILY_NONZERO | start→end skip ZERO | mid 2x² not 3x² |
| V3J_05_wrong_equality_surface | FAMILY_NONZERO | residual 0 on y=x | identity x²+y vs x²+x is NONZERO |
| V3J_06_path_dependent_repeated_node | FAMILY_NONZERO | one mixed node ZERO | x+2y+1 coalesces to 3x+1 |
| V3J_07_spectator_mismatch | FAMILY_NONZERO | local kernel PATH_ZERO | claimed spectator n+m; K_xx has n+2m |
| V3J_08_majority_path_unknown | FAMILY_UNKNOWN | 2/3 PATH_ZERO | third path size-guard PATH_UNKNOWN |

Lying that V3J_02 orders commute (`CONSISTENT_ZERO` on both PATH_ZERO
paths) makes `compose_family_verdict` return FAMILY_ZERO. That is the
attack, not a pass. Majority-voting V3J_08 likewise.

## Remaining risks

- A later composer that treats one PATH_ZERO as FAMILY_ZERO, majority-votes
  paths, or converts size-guard/timeout UNKNOWN to ZERO fails this suite.
- Noncommuting iterated limits are FAMILY_ZERO only if consistency is
  assumed from commuting-looking coordinates. Do not drop the obligation.
- Polar kernels: do not cancel one (x−y) and call the rest a derivative.
- Do not declare extra assumptions or weaken residuals to always-NONZERO:
  `V3J_POS_commuting_iterated_linear` and `V3J_POS_commuting_cubic_nodes`
  must stay FAMILY_ZERO.
