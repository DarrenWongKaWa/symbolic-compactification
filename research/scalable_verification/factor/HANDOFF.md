# HANDOFF — V2 local kernel factorization

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-local-kernel`

## What was implemented

Exact spectator-factor split under `research/scalable_verification/factor/`.
No LLM. No Guo gold. No edits to frozen runs or `api.py`.

Public API (`from research.scalable_verification.factor import ...`):

| symbol | relation | how `S` is obtained |
|---|---|---|
| `split_multiplicative(A, B)` | `A = S * A_local`, `B = S * B_local` | `gcd(num)/gcd(den)` after `together`/`fraction`, then `cancel` |
| `split_additive(A, B)` | `A = S + A_local`, `B = S + B_local` | same-sign min coefficient of common additive terms |

Return dict keys: `S`, `A_local`, `B_local`, `certified`, `note`.

If there is no exact common factor, `certified=False` and the function does
not guess (`S=1` multiplicative, `S=0` additive; locals are the originals).

Certification is fail-closed:

- reconstruction via `cancel` (never `simplify`)
- multiplicative: `num(S)` divides both numerators and `den(S)` divides both
  denominators (rejects invented poles and over-claimed coefficients)
- additive: every coefficient of `S` is contained in both sides
- units `±1` and zero are not spectators

## Negatives (not certified / not over-claimed)

- wrong sign: `(x+1)` vs `(x-1)`; additive `x` vs `-x`
- factor missing from one side: `x*y` vs `z`; extra factor never enters `S`
- coefficient mismatch: `2*(x+1)` vs `3*(x-1)`; `2*x` is not claimed of `3*x*z`
- pole mismatch: `1/(x-1)` vs `1/(x+1)`; shared pole uses min order, never a
  higher invented pole

False decomposition acceptance = 0.

## Tests

`tests/test_sv_factor.py`

Command: `.venv/bin/python -m pytest tests/test_sv_factor.py -q`
Result: **55 passed**

## Remaining risks

- `sympy.gcd` raises on some generators (e.g. Piecewise); those pairs fail
  closed (`certified=False`) rather than being structurally factored.
- Additive matching uses `Add.make_args` plus per-term `cancel` and
  `as_coefficients_dict`. Integer multiples of sums are already flattened by
  SymPy canonicalization; unsimplified but equal summands (`(x**2-1)/(x-1)`
  vs an already-cancelled `x+1` as different keys before cancel) rely on
  per-term `cancel`, not `simplify`.
- Symbolic (non-numeric) coefficients are extracted only when they match
  exactly; min-coefficient of `n*x` vs `2*n*x` is not guessed without a sign
  and magnitude proof.
- `together` on a sum puts terms over a common denominator before the
  multiplicative gcd. That is exact rational-function gcd, not a physics
  spectator in the summand-index sense.
- Callers must honor `certified`. Uncertified payloads set `S` to a unit/zero
  and do not return a guessed spectator.

## COMMIT SHA

Parent `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`.
Branch `work/v-local-kernel`. Message: `Add exact spectator-factor split for Track V.`
