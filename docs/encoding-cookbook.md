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

- **`draft`** writes one card per displayed relation. It recognises:
  - chains: `A = B = C` becomes two steps;
  - continuation rows of `eqnarray`/`align`;
  - `+ O(x^n)` and `= O(x^n)`, which become `remainder` cards;
  - `\int dω … n_F`, which becomes `fermi_integral`;
  - `(1/β) Σ_n f(iω_n)`, which becomes `matsubara`;
  - `Σ_{n=0}^∞`, which becomes `series`;
  - Langreth rules `X^<(t,t') = ∫dt₁ [B^r C^< + B^< C^a]`, which become
    `langreth` cards whose product, component and notation are taken
    from the quote. This happens only when the text around the equation
    invokes Langreth's rules. Otherwise the card stays an `identity` with
    a hint, because a single-term Born self-energy has the same shape but
    is a definition, not the exact rule. Every
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
- `|X|`, `\left| X \right|` and `\lvert X \rvert` are read as `Abs(X)`.
  A claim that takes `|…|` of a symbol whose realness the paper does not
  state is not decided. This includes symbols inside a definition the
  claim uses: `|G(\omega)|^2` depends on every symbol in `G`'s definition.
  Realness is read from phrases such as `real $\omega$` and
  `$\varepsilon$, $\Omega$ and $t$ real`;
- sizing and spacing commands are dropped.

Anything else is left alone and refused by the parser, which makes the
field `UNCHECKED`, never misread.

These readings are never guessed, because a wrong guess would give a
confident wrong verdict:
- **The statistics of a Matsubara sum.** Evidence is taken in this order:
  1. the paper's own definition of that frequency symbol, e.g.
     `\omega_n = (2n+1)\pi/\beta` or `\Omega_m = 2\pi m T`;
  2. otherwise, the word fermionic or bosonic in the sentence that leads
     into the display.

  If neither gives an answer, the card stays an `identity` with a hint.
- **The limit point of `O(x^n)`.** It is `x → ∞` or `x → 0` when the text
  says so ("x \to \infty", "large x", "small x"). A negative order is a
  tail at infinity. A positive order with no stated point is checked at
  both points and decided only if the two verdicts agree. `x → 0⁺` is
  used only when the variable is stated positive.
- **Integration limits.** `\int` over the whole real line with an `n_F`
  becomes a `fermi_integral`. Any other `\int_a^b dx\, f` (or
  `\int_a^b f\, dx`) becomes a `definite_integral`. It is decided only
  when `f` is entire in `x` (polynomials, `exp`, `sin`, `cos`, `sinh`,
  `cosh` of entire arguments): the engine's antiderivative is verified by
  differentiation, and the fundamental theorem gives `F(b) − F(a)`. An
  infinite limit needs every term to decay there, `x^k e^{s x}` with the
  sign of `Re s` decided by the stated positive and real symbols (state
  the damping, e.g. `$\eta > 0$`). Integrands with a denominator in `x`,
  unknown functions, `θ(t)` and similar stay undecided. Primes in the
  variable become `_prime` (`dt'` integrates over `t_prime`).
- **Definitions and conditions in a display.** `\Sigma(\omega) = -i\Gamma,
  \qquad \Gamma \equiv \Gamma_L + \Gamma_R`: a segment after `\quad`,
  `\qquad` or `\text{and}` that reads `X \equiv expr` or `X := expr`, with a
  name on the left and a quantity on the right, defines the constant `X`
  for every card (`notation: {Gamma: Gamma()}`; `z_\pm \equiv …` gives
  both branches). It is not used when the text or another display gives `X`
  a different value, or when `X` is an integration variable. Anything else
  next to the relation (`\qquad \Omega t = \pi`, `\qquad \varphi \equiv \pi`,
  `(\mu = 0)`, `\text{at } \mu = 0`, a second relation) makes every step of
  that display `CONDITION_IN_DISPLAY`: the extra piece may restrict the
  claim. `1/\tau \equiv …` (no bare name on the left) is a definition in
  disguise and is not checked (`EQUIV_RELATION`).
- **Langreth shorthand.** `C^r = A^r B^r` and `C^< = A^r B^< + A^< B^a`
  are checked as Langreth rules when the text mentions Langreth and
  states a convolution with its order: `$C = A*B$`, `$C = A \ast B$`, or
  "the convolution $C = AB$". Not when the paper calls the product
  pointwise, local or equal-time anywhere, or writes it with arguments
  (`C(t,t') = A(t,t')B(t,t')`): those components multiply directly. A claim
  wrong only in the order of factors is `LANGRETH_ORDER_ONLY`, not INVALID.
- **One quantity in two displays.** When two displays give the same named
  left side (`T(\omega) = A`, later `T(\omega) = C`), the step
  `eq:a.vs.eq:b` checks `A = C`. It is VALID when they agree. When they
  differ it is NOT_DECIDED with `DISPLAYS_DISAGREE`, listed under
  `displays_disagree` in the review output and shown first on the
  reviewer page: the paper never wrote `A = C` itself, and the two
  displays may hold under different conditions (a limit, `T = 0`).
  Displays in different sections, or with a name given a new value in
  between, are not paired.
- **Named quantities.** An identity whose left side is a lone name
  (`A = …`) states the value of a quantity. With `A` as a free symbol it
  could be refuted wrongly, so it is not decided unless `A` has a
  definition in the conventions. The same holds wherever the paper gives
  a name a value: `Γ_L + Γ_R = Σ`, `−Σ = …` and `2Σ = …` all mark `Σ` as
  a named quantity (`named_quantities` in `conventions.yaml`, and
  `named_functions` for `G(ω) = …`). Any card that uses an undefined
  named quantity is `NAMED_QUANTITY_UNDEFINED`. Give it a definition,
  or remove it from the list if it really is a free parameter.
- **Definitions in the prose.** `where $z_\pm = \varepsilon_d \pm i\Gamma$`,
  `with $f(x) = …$` and `$X \equiv …$` become quoted shared definitions.
  A bare name is mapped through `notation`, as in `z_p: z_p()`.
- **Subscripted names** such as `\varepsilon_d` and `\Gamma_L` are
  symbols, unless the paper assigns them a value or they look like a
  combination of two other names (`e_nm` next to `e_n` and `e_m`). Those
  are left for you to define.
- **Sub- and superscripts are part of the name.** `A_{L/R}` becomes
  `A_L_R`, never a division.
- **A superscript made only of letters is a label, not a power.**
  `G^r`, `G^{<}` and `c^\dagger` become the names `G__r`, `G__lt` and
  `c__dagger`. Numbers and expressions are still powers (`\omega^2`,
  `x^{-1}`), and `e^{...}` is the exponential.
- **A name directly before `(` could be a product or a function value.**
  `\beta(\Gamma + i x)` is a product and `G(\epsilon)` is a function.
  `multiply:` lists the names read as products, `functions:` the names
  read as functions. `draft` pre-fills `multiply:` only with conventional
  constants (`beta`, `hbar`), unless the paper defines them as functions.
  A name the text calls real or positive (`$T > 0$`) may still be a
  function elsewhere (`T(\omega)`, `\epsilon(k)`, `\rho(\epsilon)`), so it is
  read as a product only in a card that also writes it bare
  (`\frac{i}{\varepsilon}(e^{-i\varepsilon(t-t_0)} - 1)`).
  Every other such name goes under `either:`: each card that uses it is
  checked under every assignment of function or product to those names
  (up to three names), and it is VALID only if every possible reading is
  VALID (`FUNCTION_OR_PRODUCT` otherwise). It is never INVALID: as a
  function the name stands for an arbitrary function, and the paper may
  mean a specific one (`\theta(t)`, the Fermi function, `\delta(\omega)`).
  A reading that cannot exist drops out: `K(a, b)` with a comma is never a
  product. Note that `h(a)^2` is `h·a²` as a product, so even simple
  claims can depend on the reading.
- **Refutations that a hidden fact could overturn are withheld.** A
  display is not always an identity: `\Gamma/(2\pi\rho) = V^2` defines Γ,
  `e^{iqL} = 1` is a boundary condition, `\cos(\Omega t) = -1` holds at one
  time. So an INVALID is reported only when every symbol of the relation
  occurs on both sides, as written and after the definitions are used
  (`ONE_SIDED_SYMBOL` otherwise); a rounded decimal (`= 0.7468`) is never
  refuted (`APPROXIMATE_NUMBER`). An INVALID also becomes NOT_DECIDED when
  the refuted relation puts an
  integer-like index inside `exp`, `sin` or `cos` (`n`, `m`, `l`, `j`,
  `k`, `\omega_n`, `\omega_\nu`, a name the text calls an integer, or a
  name in a sentence about Matsubara frequencies: `PERIODIC_IN_AN_INDEX`),
  or uses a name the running text gives a value that no definition
  supplies (`$x = \omega/\Delta$`, `$p = 0$`, `$u := \beta\omega/2$`:
  `VALUED_IN_TEXT`). A VALID is withheld when the text sets a name to a
  number where the claim is undefined (`$a = 0$` with `(e^a - 1)/a`:
  `SINGULAR_AT_STATED_VALUE`). When the text says its quantities are
  matrices or do not commute (`are matrices`, `Nambu`, `2\times2 Green's
  function`, a bold `$\mathbf{G}$`), every commutative check is withheld
  (`NONCOMMUTING_STATED`).
- **What the running text says about symbols.** Names the text calls
  operators, spin components, Pauli or coupling matrices, or that occur in
  a sentence about the Hamiltonian, (anti)commutation or a trace, are not
  multiplied as numbers (`OPERATORS`); a claim that only reorders factors
  (`c_k c_q = -c_q c_k`) is never refuted. A relation the text imposes
  without defining a new name (`$e^{iqL}=1$`, `$t > s$`, `$\eta < 0$`)
  makes its names `CONSTRAINED_IN_TEXT`; a name called negative or of
  either sign anywhere is not taken as positive, and `$\Gamma_L>0$` makes
  `Gamma_L` positive (not `L`). "To first order", "linear response" or
  "approximately" before a display withholds an INVALID
  (`APPROXIMATION_STATED`), and so does a negative value under a square
  root or a log when the text does not state the symbols positive
  (`BRANCH_DEPENDS_ON_SIGN`). When the paper writes its own `n_F` (with a
  chemical potential, say) or calls it non-thermal, the built-in
  `1/(e^{βx}+1)` is not used for it (`DISTRIBUTION_IN_TEXT`,
  `DISTRIBUTION_NOT_THERMAL`). A Matsubara sum is drafted only over all
  frequencies, and a prefactor `T` only when the text calls `T` the
  temperature. A Fermi integral needs a real shift in `n_F(ω + c)`.
- **What the reader takes literally.** A capital `E` or `I` is a quantity
  (an energy, a current); Euler's number and the imaginary unit are `e`
  and `i`. Comments, `\iffalse … \fi`, `verbatim` and `comment`
  environments, and anything after `\end{document}` are not read. A slash
  whose reach is unclear (`\omega/2T`) is refused; write `\frac`. Bold
  symbols (`\mathbf{k}`) are vectors or matrices and are not checked as
  numbers. A row that ends in an operator continues on the next row; two
  relations side by side in an `align` row block the display. `x \to
  -\infty` and `x \to \pm\infty` are read, and a negative-order `O(...)`
  with no stated side is checked at both `+∞` and `−∞`. A refutation that
  becomes exact when a phase factor is `±1` (`e^{i\pi N}` for even `N`,
  `e^{iqL}` on a periodic lattice) is withheld (`HOLDS_AT_SPECIAL_PHASES`),
  and so is one using names the text says take only discrete values
  (Ising spins, projectors, occupations `0` or `1`). A claim that only
  reorders factors (`A B = B A`) is not decided either way. A Langreth
  rule is drafted only if its time arguments chain from `t` through the
  integration variable to `t'`.
- **Reading real papers.** Display environments opened by the paper's own
  macros (`\newcommand{\be}{\begin{equation}}`), `\providecommand` and
  `\DeclareMathOperator` macros, and `aligned`/`split` inside an equation
  are read. In math mode a run of letters is a product (`px` is p·x, `eV`
  is e·V); subscripts and letter-only superscripts stay labels (`Γ_{eff}`,
  `G^{ra}`). `\coth\frac{βω}{2}`, `\ln x` and `\sin^2θ` take the next
  factor as their argument, unless more follows (`\cos\omega t` is
  refused). `\frac{\partial X}{\partial y}` is a derivative when X shows y;
  `dE/dk` with a bare E is refused. A relation with `\pm`/`\mp` gives two
  steps, `id.p` and `id.m`, which must both hold. Traces and determinants
  are not checked (`TRACE_OF_MATRICES`). A derivative of an expression
  that holds other symbols is not decided (`DERIVATIVE_HOLDS_FIXED`: the
  paper may let ω depend on t). `\tan^{-1} x` is arctan x. A slash right
  after an unbraced argument (`\ln T_2/T_1`) is refused. `ε_+` next to
  `ε_p` in one paper is refused (`SUBSCRIPT_COLLISION`), and so is `log`
  when the text uses another base. `\mathsf{T}`, `\dot N`,
  `\tilde G` and `\mathcal S` are names of their own.
- **Declared functions are arbitrary.** A name under `functions:` stands
  for any function, so a card using it is VALID only if it holds for every
  function, and it is never INVALID (`ARBITRARY_FUNCTION`): `ζ(4) = π⁴/90`
  is true for Riemann's ζ, false for an arbitrary one. For a special
  function, map the name instead: `notation: {zeta: zeta_fn}` (Riemann or
  Hurwitz ζ) or `{Gamma: gamma_fn}`; `erf` and `erfc` are built in. The
  drafter does this only when a sentence names the symbol as the Riemann
  (or Hurwitz) zeta function or the gamma function, no sentence denies it,
  and every other sentence that writes the letter is one of those. `real: true` on a symbol overrides a
  drafted `realness: unstated`.
- **Macros redefined in the document** (`\renewcommand` after the first
  definition) are not expanded: which meaning a display has depends on
  where it sits, so quotes using them are refused. A Langreth
  claim that differs from the exact rule only in the order of factors is
  not refuted either (`LANGRETH_ORDER_ONLY`). `psi(z)` and `psi0(z)`…`psi6(z)` are
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
  word for word, or the result is `NOT_IN_DOCUMENT`. Whitespace and layout
  (`&`, `\\`, `\nonumber`, `\label`) are ignored when comparing. Copy
  the claim out of the document; do not write it from memory.
- **A quote is a whole piece, from its own display.**
  - The quote must stand on its own. Its edges must be the edge of the
    display, a row end, `=`, punctuation, spacing, an integration measure
    or sum, or `+ O(...)`. So `a + b` quoted out of `x = a + b^2` is
    refused.
  - Drafted cards record their `display` (the `\label`, or `#n` for the
    n-th display). Their quotes must come from that display, so a card
    whose equation was later edited is not decided. It cannot pass on
    text found elsewhere.
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
