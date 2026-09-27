# Encoding cookbook: one step card per derivation step

In benchmark v1 (`benchmarks/derivation-steps-v1`) a small model had the
tool available but never managed to use it, and it rejected every step it
could not check. The hard part is encoding a step, not checking it. This
page gives a fixed recipe: write one YAML **step card** per step and run

```bash
symbolic-compactification manybody step card.yaml
```

Every card below exists in `examples/cards/` and is run by the test suite.

## Fastest path: draft the cards from the document

Nobody should retype a formula. Start from the paper itself, either a
`.tex` file or a plain-text sheet with `Claim:` lines:

```bash
symbolic-compactification manybody draft paper.tex --out cards/
# fill cards/conventions.yaml once: symbols, notation, definitions
symbolic-compactification manybody steps cards/ --require-source --html report.html
```

- **`draft`** writes one card per displayed equation. `A = B = C` becomes
  two steps, and a trailing `+ O(x^n)` becomes a `remainder` card. Every
  expression is a verbatim quote, so the card contains no hand-typed
  formula. It also writes `conventions.yaml`, listing the tokens it could
  not resolve.
- **`conventions.yaml`** is included by every card. It holds the symbols
  (mark `positive: true` where a sign matters), the `notation` table and
  the paper's definitions. A card may add names, but it may not give a
  shared name a different meaning: that is a `CONVENTION_CONFLICT`, and the
  card is not decided. `steps` also warns when two cards on the same
  document map a token differently.
- **`--require-source`** (or `SYMBOLIC_COMPACTIFICATION_REQUIRE_SOURCE=1`)
  makes every expression field a quote that matches the document.
  Otherwise the decision is `NOT_DECIDED` (`decision_blocked_by` says
  why). Reviewers should always replay with it.
- **Omitted fields are built from their quotes.** A card needs no
  `lhs`/`rhs`/`claim` of its own when `source:` quotes it, and a
  definition can come from a quote as `define:NAME(args)`.
  `built_from_source` lists what was built that way.
- **Editing a draft.** Change the `check` and its fields, or shorten a
  quote to drop prose. A shortened quote must still occur verbatim in the
  document.

LaTeX quotes are converted by a fixed, reviewable set of rules:
- document macros (`\newcommand`, `\def`, with arguments) are expanded;
- `\frac`, `\sqrt`, `^{}`, Greek letters, `\exp`, `\cosh`, `\ln`,
  `\mathrm{i}`, `\psi^{(k)}` → `psik`;
- subscripts are flattened into names: `e_{nm}` → `e_nm`,
  `z_{n,+}` → `z_np`, `\rho^{(0)}_n` → `rho__0_n`;
- `\pm`/`\mp` are resolved by `branch`, and `\sum_{\pm} X` expands to
  both signs;
- sizing and spacing commands are dropped.

Anything else is left alone and refused by the parser, which makes the
field `UNCHECKED`, never misread.

Two readings are never guessed, because a wrong guess would give a
confident wrong verdict:
- **A superscript made only of letters is a label, not a power.**
  `G^r`, `G^{<}` and `c^\dagger` become the names `G__r`, `G__lt` and
  `c__dagger`. Numbers and expressions are still powers (`\omega^2`,
  `x^{-1}`), and `e^{...}` is the exponential.
- **A name directly before `(` could be a product or a function value.**
  `\beta(\Gamma + i x)` is a product and `G(\epsilon)` is a function.
  The tool reads it as a product only if the name is listed under
  `multiply:` in the conventions; otherwise the quote is refused with
  `SOURCE_APPLICATION_AMBIGUOUS`. Define the name if it is a function.
  `draft` pre-fills `multiply:` with lowercase Greek letters and lists the
  other names for you to decide. `psi(z)` and `psi0(z)`…`psi6(z)` are
predefined as polygammas.

## Decision rule for agents

Every card result has a field `decision`. **Report it as is.**

| `decision` | What you report |
|---|---|
| `VALID` | VALID |
| `INVALID` | INVALID, and quote the `diagnosis` if there is one |
| `NOT_DECIDED` | the tool did not decide. Fix the card, or check the step yourself and say so. Never report INVALID just because the tool could not decide. |

`decision` is `NOT_DECIDED` whenever the card does not match its quoted
source (see below), so a wrong card cannot produce a confident answer.
`transcription_verified: true` means the card was checked against the
source. Without a `source:` block it is `false`, and the decision holds
only for what you typed.

## Recipe

1. **Symbols.** List every symbol. Add `positive: true` where a sign matters
   (β, Γ, a broadening). Leave the frequency variable of a Matsubara sum
   undeclared.
2. **Definitions.** Copy the paper's definitions once, as `name(args): body`.
   Definitions may call each other, and `DD_name(...)` and `D_name(k, x)`
   work on them. This is how f±, ρ₀, kernels and residue forms are written.
3. **Arbitrary functions.** Put a function under `functions:` only when the
   step must hold for every smooth function. Divided-difference rules are
   the typical case.
4. **Labels.** Set `labels: [n, m]` when band labels occur. A `NONZERO` then
   reports whether the claim is the computed value with two labels swapped.
5. **Check.** Pick the check that matches the step:

| Step looks like | `check` | Fields |
|---|---|---|
| `A = B` (algebra, divided differences, derivatives, conjugation) | `identity` | `lhs`, `rhs` |
| `[w^k] F(w) = C` (kernel coefficients, shifted-node rules) | `coefficient` | `expr`, `variable`, `order`, `claim` |
| `f = P + O(x^n)`, `lim_{x→x0} f = P` (use order 1) | `remainder` | `function`, `approximant`, `variable`, `point` (0, oo, -oo), `order`, `direction` |
| `∫ R(ω) nF(c ± ω) dω = C` (bath integrals, Lorentzian averages; at most two Fermi factors; a real-axis pole via `ω − a + I*eta`) | `fermi_integral` | `integrand`, `variable`, `beta`, `claim`, optional `infinitesimal: eta` |
| `Σ_{n≥n0} R(n) = C` (rational R; Matsubara sums over n ≥ 0) | `series` | `summand`, `variable`, `lower`, `claim` |
| `T Σ_n F(iω_n) = C` | `matsubara` | `summand`, `statistics`, `claim`, `convergence`, `rules` |
| Keldysh product components | `langreth` | `product`, `component`, `claim` |
| Operator identities | `operator` | `lhs`, `rhs`, `operators`, `hermitian` |

In integrands and claims, `nF(x) = 1/(exp(beta x) + 1)` and
`nB(x) = 1/(exp(beta x) − 1)`, so the Fermi function `f0(e)` of a paper is
`nF(e - mu)`.

## Tie the card to its source

In benchmark v1 every wrong answer from a small model came from a wrong
card, never from a wrong verdict: a term was dropped, a factor was added, a
derivative was taken of the wrong object, or an example was copied instead
of the claim. A `source:` block makes the tool check the card against the
text:

```yaml
source_document: sources/propagator_note.md   # the text the step is taken from
notation:                                      # paper token -> card syntax
  z_+: zp
  z_-: zm
source:                                        # card field -> verbatim quote
  integrand: "nF(w) / ((w − a + iG)(w − b − iG))"
  claim: "[iπ + ψ(z_−(b)) − ψ(z_+(a))]/(b − a + 2iG)"
  define:zp(x): {quote: "1/2 + β(G ± ix)/(2π)", branch: "+"}
  define:zm(x): {quote: "1/2 + β(G ± ix)/(2π)", branch: "-"}
```

(`examples/cards/fermi_pair_with_source.yaml`.)

- **Quote, do not retype.** Each quote must occur in `source_document`
  word for word (whitespace aside), or the result is `NOT_IN_DOCUMENT`.
  Copy the claim out of the document; do not write it from memory.
- **Quote only the expression.** Leave out "Claim:", the left-hand side
  and "=". A measure the quote leaves out goes in `wrap`, e.g.
  `{quote: "...", wrap: "({})/(2*pi)"}`.
- **The tool translates the quote itself.** It handles Unicode (ψ, β, π,
  −), `^`, square brackets, implicit multiplication (`2G`, `beta (x)`,
  `(a)(b)`), `i` and tokens such as `iG` = `I*G` when `G` is declared, and
  `pm`/`mp`/`±` through `branch`. Every other paper token (subscripted
  names, `f_+`, `e_nm`, `r_-`) needs a `notation` entry. Entries replace
  whole tokens once, and a multi-symbol value is bracketed automatically.
- **Quote definitions too.** `define:NAME(args)` checks a definition the
  same way. An unchecked definition is where a sign slips in unnoticed.
- The card and the quote must agree **identically**, not merely
  numerically at a point.

| `transcription.status` | Meaning |
|---|---|
| `MATCH` | every quoted field equals its card field |
| `MISMATCH` | some card field differs from the quote; `decision` is `NOT_DECIDED` |
| `NOT_IN_DOCUMENT` | a quote is not in the document; `decision` is `NOT_DECIDED` |
| `UNCHECKED` | a quote could not be translated (add `notation`) |
| `ABSENT` | no `source:` block |

On `MISMATCH`, fix the card, not the quote. If you believe the source is
wrong, the tool will say so through `INVALID` once the card matches it.

**Strict mode also requires**
- A card's own `define:` entries must be quoted as `define:NAME(args)`.
  Definitions from the shared `conventions.yaml` are allowed; they are
  reviewed once.
- `wrap` may only restore an integration measure: `({})/(2*pi)` and its
  powers.
- `sum_pm` must be followed by a bracketed group or a function call.

**When the printed formula is broken.** If a quote cannot be read, the step
is not decided. The typical cause is an unbalanced bracket
(`SOURCE_BRACKETS_UNBALANCED`). Declare the obvious fix as an erratum:

```yaml
source:
  function: {quote: "<printed LaTeX>", erratum: "<same LaTeX with the bracket fixed>",
             note: "closing ] missing in the printed equation"}
```

The erratum may only add, remove or move bracket characters, and this is
checked. The result stays `NOT_DECIDED` for the printed formula, and
`decision_with_errata` gives the verdict after correction. Report both.

## Worked cards

These examples are deliberately **not** taken from the benchmarks in
`benchmarks/`. Examples that match a test item teach agents to copy the
example instead of transcribing the claim in front of them.

**Fermi-weighted propagator pair**
(`examples/cards/fermi_weighted_propagator_pair.yaml`):

```yaml
check: fermi_integral
symbols:
  - {name: beta, positive: true}
  - {name: G, positive: true}
  - {name: a}
  - {name: b}
  - {name: w}
define:
  zp(x): 1/2 + beta*(G + I*x)/(2*pi)
  zm(x): 1/2 + beta*(G - I*x)/(2*pi)
variable: w
beta: beta
integrand: nF(w)/((w - a + I*G)*(w - b - I*G))
claim: (I*pi + polygamma(0, zm(b)) - polygamma(0, zp(a)))/(b - a + 2*I*G)
```

Paper definitions (f±, ρ₀, residue forms) go under `define:` in the same
way, and a claim can then be written with them, e.g. `claim: rho1(em, en, w)`.

**Divided differences of an arbitrary function**
(`divided_difference_symmetry.yaml`, `derivative_repeats_node.yaml`):

```yaml
check: identity
symbols: [x, y]
functions: [f]
lhs: Diff(DD_f(x, y), x, 1)
rhs: DD_f(x, x, y)
```

- `DD_f(...)` is the divided difference of `f`.
- `D_f(k, x)` is `f^(k)(x)`, the k-th derivative of `f` itself at `x`.
- `Diff(expr, x, k)` is the k-th derivative **of any expression** in `x`,
  for example of a divided difference.

`D_f(2, x)` and `Diff(DD_f(x, y), x, 2)` are different objects; confusing
them is the most common encoding error.

**Frequency coefficient** (`shifted_node_first_coefficient.yaml`):

```yaml
check: coefficient
symbols: [x, y, w]
functions: [f]
expr: DD_f(x + w, y)
variable: w
order: 1
claim: DD_f(x, x, y)
```

To check a kernel `M = [ω²] ρ₁(ω)`, define `rho1(a, b, w)` exactly as the
paper does. Use `expr: rho1(em, en, w)` and `order: 2`, and transcribe the
claim term by term.

**Γ → 0 limit of a digamma form**
(`broadened_occupation_derivative_limit.yaml`):

```yaml
check: remainder
function: Diff(occ(e), e, 1)
approximant: -beta/(4*cosh(beta*e/2)**2)
variable: G
point: "0"
order: 1
```

Digamma and Fermi/tanh/cosh forms are matched through the reflection
formula. When SymPy's limit fails, the Laurent coefficients are checked one
by one.

**Index-order slip** (`index_swap_diagnosis.yaml`): the result is `NONZERO`
with the diagnosis `claim = computed with n <-> m (index order)`. Other
diagnoses name a sign, a factor 2 or a complex conjugate.

**Transcribe, do not reconstruct.** The card must encode the claim exactly
as written, including any factor that looks wrong. If you "fix" the claim
while encoding it, the tool verifies your version instead of the author's.

## When the tool says UNKNOWN

The usual causes and fixes:
- a symbol whose sign matters was not declared `positive`;
- the integrand has two Fermi factors in one product (split it first);
- a pole lies on the real axis;
- the expression is outside the supported forms.

Rewrite the card or check the step by other means, and report which one
you did.
