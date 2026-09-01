# Derivation-audit limitations

Read this before using an audit report in scientific work. The v0.2
derivation-audit alpha is in development on
`engineering/derivation-audit-v0.2`. It is an additive fail-closed layer, not
a claim that a paper is proved.

Exact algebraic and local structural identities that were lowered to
executable residuals were evaluated under the declared symbolic semantics.
Only obligations returning exact ZERO are listed as machine-verified.

Definitions, integral-level arguments, asymptotic remainder claims, and
unsupported transformations are tracked separately rather than being
misreported as exact algebraic identities.

## Allowed non-blocking limitations

These are in-scope boundaries. Do not expand the alpha to “close” them:

- **Manual PDF inventory.** Inventory reads local UTF-8 LaTeX/Markdown
  labels. It does not understand PDFs or render glyphs.
- **Manual symbolic transcription.** LaTeX is not algebra. Native-text
  members in `expressions/` are researcher-authored.
- **`NOT_LOWERED` edges.** Many scientifically real steps have no supported
  residual. That is an encoding gap, not a proof or a refutation.
- **Limited integral and asymptotic remainder certification.**
  `INTEGRAL_ARGUMENT` is not a local residual. Finite Laurent/series
  coefficient `ZERO` is not a remainder proof. `ASYMPTOTIC_CLAIM` stays
  uncertified without `remainder_certificate_hash`.
- **Unsupported complex assumptions.** Alpha certification uses `real: true`
  symbols, optional `nonzero`, and declared functions. `real: false`,
  positivity, inequalities, excluded poles, parameter identities, boundaries,
  symmetries, and limit order are outside the machine-enforced surface.
- **Experimental AI edge proposal.** Optional and non-authoritative. Disabled
  under `SSC_PRIVATE_OFFLINE=1`. Proposer text cannot create `ZERO`.

## Verification coverage is incomplete

`UNKNOWN`, `PARSE_FAILURE`, `COMPILE_FAILURE`, `GROUNDING_FAILURE`, and
`NOT_LOWERED` are normal. A packaging gap is not evidence that a statement
is true, false, or impossible.

The parser whitelist, token/depth/size limits, and the SymPy exact route
bound what can be certified. Large tensors, hard special-function
identities, and general exact limits often remain undecidable here.

## Exactness is conditional

`ZERO` is exact only under the recorded engine semantics, namespace,
assumptions, residual bytes, and verifier route (`python_sympy_exact_v1`).
It does not validate undeclared physical folklore, provenance outside the
hashed snapshot, or a manuscript as a whole.

The tool does not silently integrate by parts, drop boundary terms, change
symmetry, reorder limits, or widen domains.

## Inventory is not mathematics

Equation inventory extracts labels, environments, order, and source ranges.
It does not type-check a derivation and does not fill missing steps.

## Split and remainder honesty

- A `SPLIT_PARENT` is never engine `ZERO`.
- Coefficient children may be machine-verified while the enclosing
  `ASYMPTOTIC_CLAIM` remains `UNKNOWN`.
- `CERTIFIED_BY_CHILDREN` is displayed as `SPLIT — all children certified`.

## Mode A still applies

Hypothesis-level Mode A limitations remain in
[engineering/release_v0_1/LIMITATIONS.md](../engineering/release_v0_1/LIMITATIONS.md).
Scientific representation-invention campaigns remain closed
([SCIENTIFIC_EXPERIMENTS_CLOSED.md](../SCIENTIFIC_EXPERIMENTS_CLOSED.md)).
