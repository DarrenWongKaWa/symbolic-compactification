# HANDOFF — Track V2 Subagent V2-G (special-function local prover)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-special-functions`

Commit message: `Add local polygamma prover for Track V2.`

## Owned

- `research/multibranch_verification/special/**`
- `tests/test_mb_special.py`

Did not edit `schema.py`, freeze inputs, Track-V `special/`, masters, or run JSON.

## API

```
prove_local(expr_or_pair, right=None, *, relation="", variable=None, target=None)
    -> LocalProof(verdict=ZERO|NONZERO|UNKNOWN, ...)
```

Spectators are stripped first (`split_multiplicative` then `split_additive`).
Units and zero are not spectators. Then:

1. `classify_identity` **supported** → `ZERO` (`derivative` or `newton_first`)
2. First-derivative / Newton-form mismatch → `NONZERO`
3. **Series** (only if `relation` in `{series, limit, one_parameter_confluence}`
   or `variable`/`target` given): Newton DD of `polygamma(n, ·)` as
   `y → x` has leading term `polygamma(n + 1, x)` → `ZERO` / wrong target
   `NONZERO`
4. Residual series constant with `is_zero is False` → `NONZERO`
5. else `UNKNOWN`

Algebraic `(psi(x)-psi(y))/(x-y) = polygamma(1, x)` is **not** ZERO (Track V
`unsupported`). That claim is the series identity, not an equality of functions.

No `expand_func` (recurrence would collapse). No `sympy.limit`. No Φ_Γ / L4–L7.

## Tests

```
.venv/bin/python -m pytest tests/test_mb_special.py -q
```

Result: **16 passed**. Deterministic. No network. No engine verifier import.

## Remaining risks

- Series ZERO is a diagonal leading-term identity, not `newton ≡ polygamma(1)`.
  Callers must pass `relation="series"` (or a limit edge) for confluence.
- Iterated `d²/dz²` and chain rule stay `UNKNOWN` even when SymPy `doit` is 0.
- Recurrence `polygamma(0,z+1)-polygamma(0,z)=1/z` is `UNKNOWN` (domain-
  sensitive; not a listed local rule).
- Residual-series NONZERO requires `is_zero is False` on the constant;
  free-symbol constants stay `UNKNOWN`.
