# Product gaps revealed by forward replay v1

Engineering firewall: the frozen product (`derivation-audit-v0.2.1-alpha`,
peel `783ec64`) was **not** modified. These gaps are recorded, not implemented.

## G1. Declared identities are not Mode A assumptions

FR-06 (`e21 = -e12`) and FR-08 (`f1p = 2*f01p`, `f2p = 2*f02p`) are
substitution-conditioned paper steps. Gold and LLM candidates can match the
hidden published next formula (TargetRecovery) while remaining `NONZERO`
versus the current expression, because `assumptions.yaml` only admits
`{symbols, functions}`. Notes do not compile identities.

The retrospective audit encodes the same identities as
`SUBSTITUTION_EXACT` residuals. Forward Mode A has no corresponding
assumption slot. Do not silently substitute from notes. Do not expand the
assumption language in this campaign.

## G2. No workspace `propose` command

The product façade remains `init | inspect | verify | report` and the
compatibility session `init-session | step`. External proposers live only
in `experiments/forward_replay_v1/proposers/`. Adapter code must not migrate
into `src/`.

## G3. Parser does not accept foreign SR program syntax

gplearn emits `add(x, y)` programs. Untranslated strings are
`PARSE_FAILURE` and are refused. That is correct fail-closed behaviour.
A product-level gplearn/PySR parser is out of scope.

## G4. Stay-put ZERO is not remainder certification

On FR-NC-01, algebraic rewrites of a nonzero remainder are `ZERO` versus
current and therefore Mode A promotion-eligible as *stay-put*. Collapse of
the remainder to `0` is `NONZERO` and refused. The product cannot, from
equivalence alone, know that the scientific intent was "certify the
remainder vanishes." Asymptotic remainder certification remains unsupported
(`NEGATIVE_RESULTS.md`, capability boundary).

## G5. Symbolic regression is the wrong native class for derivation rewrite

ERRLESS: no public implementation found; not emulated.
PySR: no Julia binary here; not faked.
AI Feynman: not installed; same native class as gplearn.
gplearn 0.4.3 was installed and run. Raw TargetRecovery@1 = 0/8.

Do not distort Guo tasks into Feynman-style (X, y) discovery problems in
order to force a leaderboard.

## G6. `UNKNOWN` is not a promotion path

FR-06 `llm-2` returned promotion `UNKNOWN` and was refused. Injected
`FR-08 neg-times_two` returned target-recovery `UNKNOWN` after a long
simplify and was still not promoted (promotion was `NONZERO`). Do not
retune the engine to force `NONZERO` or `ZERO` on those cases.
