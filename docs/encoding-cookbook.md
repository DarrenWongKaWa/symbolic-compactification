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

**Bath integral against a residue form**, from Guo *et al.*, Eq. SM_rho1
(`examples/cards/guo_rho1_bath_integral.yaml`):

```yaml
check: fermi_integral
symbols:
  - {name: beta, positive: true}
  - {name: G, positive: true}
  - {name: en}
  - {name: em}
  - {name: mu}
  - {name: w}
  - {name: wb}
define:
  zp(x): 1/2 + beta*(G + I*(x - mu))/(2*pi)
  zm(x): 1/2 + beta*(G - I*(x - mu))/(2*pi)
  fp(x): 1/2 + I/pi*polygamma(0, zp(x))
  fm(x): 1/2 - I/pi*polygamma(0, zm(x))
  rho0(x): (fp(x) + fm(x))/2
  rp(w, a, b): I*G*(fp(b) - fp(a - w))/(w + b - a)
  rm(w, a, b): I*G*(fm(b + w) - fm(a))/(w + b - a)
  rho1(a, b, w): (rho0(b) - rho0(a) + rp(w, a, b) + rm(w, a, b))/(w + b - a + 2*I*G)
variable: wb
beta: beta
integrand: G/(pi*(wb**2 + G**2))*(nF(en - mu + wb) - nF(em - mu - wb))/(w + wb + en - em + I*G)
claim: rho1(em, en, w)
```

The result is `CERTIFIED_BY_RULE`. With `fp(a + w)` in `rp`, a planted error,
it is `NONZERO`.

**Confluent divided difference** (`repeated_node_divided_difference.yaml`):

```yaml
check: identity
symbols: [x, y]
functions: [f]
lhs: DD_f(x, y, y)
rhs: (DD_f(x, y) - D_f(1, y))/(x - y)
```

**Frequency coefficient of a kernel** (`shifted_node_coefficient.yaml`):

```yaml
check: coefficient
symbols: [x, y, z, w]
functions: [f]
expr: DD_f(x + w, y, z)
variable: w
order: 2
claim: DD_f(x, x, x, y, z)
```

To check a paper's `M = [ω²] ρ₁(ω)`, define `rho1(a, b, w)` as in the
first card and use `expr: rho1(em, en, w)`.

**Γ → 0 limit of a digamma form** (`occupation_gamma_limit.yaml`):

```yaml
check: remainder
function: rho0(e)
approximant: 1/(exp(beta*(e - mu)) + 1)
variable: G
point: "0"
order: 1
```

Digamma and Fermi/tanh forms are matched through the reflection formula.
When SymPy's limit fails, the Laurent coefficients are checked one by one.

**Index-order slip** (`index_swap_diagnosis.yaml`): the result is `NONZERO`
with the diagnosis `claim = computed with n <-> m (index order)`. Other
diagnoses name a sign, a factor 2 or a complex conjugate.

## When the tool says UNKNOWN

The usual causes and fixes:
- a symbol whose sign matters was not declared `positive`;
- the integrand has two Fermi factors in one product (split it first);
- a pole lies on the real axis;
- the expression is outside the supported forms.

Rewrite the card or check the step by other means, and report which one
you did.
