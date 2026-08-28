# HANDOFF — Track V Subagent V5 (special-function localization)

Parent: `329c49c22c7d68d0192a59f04bf3ba8ad12c9b48`
Branch: `work/v-special-functions`

Commit message: `Add polygamma-local identity checks for Track V.`

## Owned

- `research/scalable_verification/special/**`
- `tests/test_sv_special.py`

Did not edit `research/representation_invention/llm/runs/`, grounded-proposer runs, SOL, Φ_Γ, or L4–L7.

## API

```
classify_identity(expr_or_pair) -> supported | unsupported | UNKNOWN
```

`supported` only for local identities already in SymPy:

1. `d/dz polygamma(n, z) = polygamma(n + 1, z)`
   (unevaluated `Derivative`, string `diff(...)`, or SymPy `diff` already reduced)
2. Newton first DD of `polygamma(0, ·)` vs `(psi(x) - psi(y))/(x - y)`
   (`psi` is a parse alias for `digamma` = `polygamma(0, ·)` in SymPy 1.14)

Anything else with a polygamma/gamma head is `unsupported` (recurrence,
wrong order, sign-flipped DD, confluence slogan Newton vs `polygamma(1, x)`,
Φ_Γ / L4–L7 names). Unparsed, algebraic, or oversized input is `UNKNOWN`.

No new assumptions. Symbols are parsed without `real=True`. No `sympy.limit`.
No master constructors.

## Guo confluence vs small polygamma identities

**UNKNOWN / not demonstrated.** There is no exact reduction in this package
from `examples/long/Guo_Sigma_abc_dc_exact.txt` (`CompleteDCSigmaABC`, 4 Sums,
14 Piecewise branches, ~22k characters of PolyGamma kernels) onto the two
local identities above. Size-guard returns `UNKNOWN` on the full source;
that is not a proof that a reduction exists or does not exist.

Local facts (polygamma fdiff, `polygamma(0)` vs `psi` Newton quotient) do
not discharge Guo index-coincidence limits. Claiming YES would be an
invented confluence/master slogan (Φ_Γ, L4–L7). Those were not constructed.

## Tests

```
.venv/bin/python -m pytest tests/test_sv_special.py -q
```

## Remaining risks

- `supported` is catalog membership, not an engine ZERO. Callers must still
  verify obligations through the existing verifier.
- Iterated `d²/dz² polygamma(n, z) = polygamma(n + 2, z)` is true in SymPy
  but is **not** admitted (listed identity is first derivative only).
- Polygamma recurrence `polygamma(0, z+1) - polygamma(0, z) = 1/z` can be
  `expand_func`'d by SymPy and is still `unsupported` here (UNKNOWN_AUDIT:
  do not add it as a silent local rule).
- `classify_identity((polygamma(k, z), polygamma(k, z)))` is `supported`
  because evaluated `diff` already is that equality. It is not a Guo claim.
- Chain-rule derivatives (`d/dz polygamma(n, g(z))` with `g ≠ z`) are not
  the listed identity and classify as `unsupported` when polygamma is present.
