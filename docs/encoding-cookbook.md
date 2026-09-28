# Encoding cookbook: one step card per derivation step

In benchmark v1 (`benchmarks/derivation-steps-v1`) a small model had the
tool available but never managed to use it, and it rejected every step it
could not check. The hard part is encoding a step, not checking it. This
page gives a fixed recipe: write one YAML **step card** per step and run

```bash
symbolic-compactification manybody step card.yaml
```

Every card below exists in `examples/cards/` and is run by the test suite.

## Decision rule for agents

| Tool result | What you report |
|---|---|
| `ZERO` or `CERTIFIED_BY_RULE` | VALID |
| `NONZERO` (with a counterexample) | INVALID, and quote the `diagnosis` if there is one |
| `UNKNOWN`, `NUMERICAL_SUPPORT`, `ASSUMPTION_REQUIRED`, or a parse error | **not decided by the tool**. Fix the encoding, or check the step yourself and say so. Never report INVALID just because the tool could not decide. |

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
| `∫ R(ω) nF(c ± ω) dω = C` (bath integrals, Lorentzian averages) | `fermi_integral` | `integrand`, `variable`, `beta`, `claim` |
| `T Σ_n F(iω_n) = C` | `matsubara` | `summand`, `statistics`, `claim`, `convergence`, `rules` |
| Keldysh product components | `langreth` | `product`, `component`, `claim` |
| Operator identities | `operator` | `lhs`, `rhs`, `operators`, `hermitian` |

In integrands and claims, `nF(x) = 1/(exp(beta x) + 1)` and
`nB(x) = 1/(exp(beta x) − 1)`, so the Fermi function `f0(e)` of a paper is
`nF(e - mu)`.

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
