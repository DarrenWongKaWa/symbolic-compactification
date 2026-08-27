# Hypothesis-to-source grounding

Track B only. Frozen outputs. No SOL ranking changes.

## Intra-hypothesis only

Fingerprints may be completed from **this hypothesis’s** latent, maps,
members, rationale, and obligations. Never from a sibling hypothesis.

UNIQUE evidence (does not change the four-way decision):

- `UNIQUE_BY_EXPLICIT_EXPR` — hyp contains the matching \(h_1 h_2\) product
- `UNIQUE_BY_SOL_ID` — hyp cites `N####`
- `UNIQUE_BY_LOCAL_FINGERPRINT` — constraint intersection
  \(C_{\rm function}\cap C_{\rm indices}\cap C_{\rm branch}\cap C_{\rm symbols}\)
  has size 1

## Admissible confidences

| tag | meaning | to verifier? |
|---|---|---|
| EXACT_BIND | parse/srepr or `N####`/`G####` hits one source node | yes |
| UNIQUE_STRUCTURAL_BIND | unique `h1`/`h2` fingerprint and/or unique PW condition under that fingerprint | yes |
| AMBIGUOUS_BIND | more than one equally matching node (e.g. four `True` branches) | **no** |
| NO_BIND | alias with no exact hit and no fingerprint | **no** |

`S1_True` with no h-factor is **AMBIGUOUS** among four generic branches.
That is constructor failure, not a guess for “first sum.”

Declared index synonym (not fuzzy): `epsilon(m)=epsilon(n)` and
`epsilon(m)->epsilon(n)` mean the `Eq(m,n)` Piecewise condition in this
source (conditions are on indices, not on `epsilon` values).

## Representation compilation (only admissible binds)

- divided_difference: bound generic branch vs Newton form \((F(x)-F(y))/(x-y)\)
- confluence: `sympy.limit` of generic `epsilon(m)→epsilon(n)` vs `Eq(m,n)` branch
- derivative: `sympy.diff` between exact-bound members; polygamma order identities

ZERO here is **grounding/compiler gain** on frozen text, not a new LLM discovery.
