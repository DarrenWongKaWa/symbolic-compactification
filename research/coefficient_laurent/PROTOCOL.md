# Track V5 — coefficient-space Laurent certification

No LLM. Frozen generic→diagonal hops only. Track D2 locked until
FAMILY_ZERO or FAMILY_NONZERO.

## Central question

Can G0016 → G0013 be certified by sparse Laurent coefficients of local
atoms, without a 27k-op `together()` and without Guo identities?

## Proof levels

- **LEVEL A** — atoms expanded. Not hop ZERO.
- **LEVEL B** — all required negative coefficients vanish.
- **LEVEL C** — t^0 equals the diagonal target and remainder is sufficient.
  Only LEVEL C may return ZERO.

t^0 match with a surviving t^{-1} is NONZERO.

## Cache

Keys include source/target **full text** hashes, degeneration, target
value, assumptions hash, method version, atom-decomposition hash.
Missing `text_sha256` is computed from text. Never reuse G0014→G0012
for G0016→G0013.

## Composition

Reuse frozen V3/V4 graphs. Do not change topology. New edge verdicts
are V_GAIN only. Path consistency is not auto-CONSISTENT_ZERO.
