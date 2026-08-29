# Remainder wiring

Independent reviews R1–R5 found that `sparse_laurent_limit`
hardcoded `remainder_verdict=ZERO` whenever reconstruction and
negatives succeeded. That skipped `remainder_ok`.

## Package

`remainder_ok` / `remainder_verdict` in `sufficiency.py`:

- True / ZERO only if every polygamma argument is affine in `t`
  and `α = z(0)` is certified not a nonpositive integer.
- Symbolic `α` is UNKNOWN (fail closed).
- False means remainder UNKNOWN, never NONZERO.

Toy: `z = 1+t` is regular; `z = t` hits the pole `α = 0`.

## Engine (after coordinator patch)

`sparse_laurent_limit` calls `remainder_ok` on every polygamma
unit after `variable → target_value + t`. Any False unit yields
`remainder_verdict=UNKNOWN`, so LEVEL C cannot fire.

No polygamma units: extra polar polygamma terms cannot appear;
remainder is ZERO once the extracted principal part vanished.

## Frozen primary hop

`ATOM_MAP.json` primary hop, 14 polygamma atoms. After the
degeneration substitution, `remainder_ok` is False on 14/14
because `α` has free symbols. LEVEL C is therefore not certified.
Negatives and C0 matching are independent of remainder.

Do not unlock D2. Do not retune ell-hops.
