# Many-body equivalence checks

Many-body derivations rely on moves that are not plain algebra: frequency
sums, contour deformations, analytic continuation, asymptotic expansions and
operator algebra. This page lists the forms that appear most often, what the
tool checks for each, and which status a result can earn. The code is in
`symbolic_compactification.manybody`, and the CLI is
`symbolic-compactification manybody ...`.

The rule is the same as everywhere else in the tool. A model may propose a
form, but a status comes only from a computation. Some checks rest on a
named theorem, such as the residue theorem or the Langreth theorem. For
those, the result is `CERTIFIED_BY_RULE`. It means an exact local
computation was done and the theorem's hypotheses were checked
mechanically or declared. It is never an engine `ZERO` for the infinite
sum or integral itself.

## Forms and how each is checked

| Form | Typical use | Check | Best status |
|---|---|---|---|
| Matsubara sum of a rational summand, `T Σ_n F(iω_n)` | bubbles, self-energies, susceptibilities | residue theorem: poles of `F` weighted by `n_F`/`n_B`, compared with the claim by the exact verifier; mpmath summation as cross-check | `CERTIFIED_BY_RULE` |
| Convergence factor `e^{±iω_n 0⁺}` for `1/z` decay | equal-time densities, `G(τ=0^±)` | residue theorem with `n_F(z)` or `n_F(−z)` (bosons `n_B`) | `CERTIFIED_BY_RULE` |
| Asymptotic expansion `f = P + O(x^n)` | `Γ → 0` Laurent series, high-frequency tails `G(iω) ~ 1/iω + ⟨H⟩/(iω)² + …`, large-argument digamma | exact limit of `(f − P)/x^n`, two-sided when declared; numerical cross-check | `CERTIFIED_BY_RULE` with a remainder-certificate hash |
| Asymptotic-only series (Sommerfeld, Stirling) where no limit is computable | `T → 0` expansions | local slope of `log|f − P|` versus `log x` | `NUMERICAL_SUPPORT` |
| Real-frequency integral `∫ R(ω) n_F(c ± ω) dω`, `R` rational and `O(1/ω²)` | bath integrals, `∫dω n_F(ω) A(ω)` → digamma, dissipative kernels | `manybody fermi_integral` (step card): split `n_F` into digamma parts analytic in opposite half planes and close each contour; the half plane of each pole is decided from declared signs | `CERTIFIED_BY_RULE` |
| Other real-frequency integrals | general integrands | high-precision quadrature at rational sample points, split at pole real parts | `NUMERICAL_SUPPORT` |
| Langreth rules for contour products | Dyson/Keldysh equations, `(AB)^< = A^R B^< + A^< B^A` | Larkin–Ovchinnikov triangular matrices, exact comparison in the free algebra | `CERTIFIED_BY_RULE` |
| Operator identities | commutators, Lindblad generator versus `H_eff` plus jumps | normal form in the free associative algebra with a declared adjoint | `ZERO` / `NONZERO` |
| Partial fractions and divided differences of propagator products | `G_n G_m → (G_n − G_m)/(ε_n − ε_m)` | existing `DIVIDED_DIFFERENCE` / `ALGEBRAIC_EQUIVALENCE` edges | `ZERO` |
| Divided differences with repeated nodes and derivatives of arbitrary functions | confluent kernels `f[x,x,y]`, `f[x,x,x,y,z]` | `manybody identity`: expansion of `DD_f(...)`, `D_f(k,x)`; a counterexample uses a concrete test function | `ZERO` / `NONZERO` |
| Frequency Taylor coefficients `[ω^k]` | kernels `M = [ω²]ρ₁(ω)`, shifted-node rules | `manybody coefficient`: exact series, then the identity check | `ZERO` / `NONZERO` |
| Digamma versus Fermi forms | `ψ(1/2+iy) − ψ(1/2−iy) = iπ tanh(πy)`, Γ → 0 limits of broadened occupations | reflection formula `ψ(1−z) − ψ(z) = π cot(πz)` and its derivatives, applied inside every exact check; a Laurent-series route for Γ → 0 remainders | `ZERO` / `CERTIFIED_BY_RULE` |
| Coefficients of a series | `c_{-1}`, `c_0` of a Laurent expansion | existing `LAURENT_COEFFICIENT` / `SERIES_COEFFICIENT` edges | `ZERO` |
| Special-function relations | `n_F(−x) = 1 − n_F(x)`, `tanh`/`n_F`, digamma recurrence | exact verifier on explicit exponential forms | `ZERO` |

## Hypotheses that are checked, not assumed

For a Matsubara sum:

- `F` must be rational in the frequency variable, and every denominator
  factor must have explicit roots.
- The decay condition must hold: `deg(den) − deg(num) ≥ 2`. With exactly one
  power of decay, a declared convergence factor is required. The check
  refuses `CONVERGENCE_FACTOR_REQUIRED` rather than guessing a half-sum.
- No pole may sit on the Matsubara axis. The check proves this when a pole
  has a nonzero real part. It also proves it for real poles with fermions,
  because `ω_n ≠ 0`, and for real nonzero poles with bosons. Otherwise the
  workspace must declare `MATSUBARA_POLES_OFF_AXIS`. Without it the edge is
  `ASSUMPTION_REQUIRED`: the bosonic `ν_0 = 0` is exactly where this goes
  wrong.

For asymptotic claims:

- the limit must be finite, and equal from each declared side;
- a limit of infinite magnitude is `NONZERO`, because the claimed order
  fails for some admissible parameters;
- a limit like `oo·c/|c|` is `NONZERO` when an admissible sample value of
  `c` makes it infinite (the counterexample is recorded);
- when SymPy cannot take the limit, the Laurent coefficients below the
  claimed order are tested one by one. Each must vanish exactly
  (after polygamma reflection), and a coefficient certified nonzero at a
  sample point refutes the claim.

A disagreement between the exact result and the numerical cross-check
always leaves the claim `UNKNOWN`.

## Audit edges

Two edge kinds use these checks inside a derivation audit
(`tests/fixtures/audit_demos/M` is a complete example):

```yaml
- edge_id: M.fermion-bubble
  edge_type: MATSUBARA_SUM
  rhs: expressions/fermion_bubble.txt          # claimed T Σ_n F(iω_n)
  matsubara:
    summand: expressions/bubble_summand.txt    # F(z), z complex
    variable: z
    statistics: fermion                        # or boson
    beta: beta
    convergence: none                          # plus | minus for 1/z decay
    positive: [g]                              # optional: sampled > 0

- edge_id: M.tail
  edge_type: ASYMPTOTIC_CLAIM
  asymptotic:
    function: expressions/green.txt            # f
    approximant: expressions/green_tail.txt    # P
    variable: w
    point: oo                                  # 0 | oo | -oo
    order: -3                                  # O(w**-3)
    direction: "+-"                            # at 0: +, -, +-
```

Claims may write `nF(x)` and `nB(x)`. The frequency variable is not declared
in `assumptions.yaml`, because it is complex. A certified record is written
to the structural table. It carries a `rule_certificate`, and for
asymptotic claims a `remainder_certificate_hash`. Integrity checks reject a
`CERTIFIED_BY_RULE` record that lacks either one.

## CLI

```bash
symbolic-compactification manybody matsubara --statistics fermion \
  --summand "1/((z-a)*(z-c))" --claim "(nF(a)-nF(c))/(a-c)" \
  --symbols '[{"name":"a"},{"name":"c"},{"name":"beta","nonzero":true}]'

symbolic-compactification manybody remainder --function "1/(I*w - e)" \
  --approximant "1/(I*w) + e/(I*w)**2" --variable w --point oo --order -3 \
  --symbols '[{"name":"e","nonzero":true},{"name":"w","nonzero":true}]'

symbolic-compactification manybody langreth --product A,B,C --component less \
  --claim "A_R*B_R*C_less + A_R*B_less*C_A + A_less*B_A*C_A"

symbolic-compactification manybody operator --operators H,rho,c --hermitian H,rho \
  --lhs "-I*Comm(H,rho) + c*rho*Dag(c) - Rational(1,2)*Anti(Dag(c)*c, rho)" \
  --rhs "-I*((H - I/2*Dag(c)*c)*rho - rho*Dag(H - I/2*Dag(c)*c)) + c*rho*Dag(c)"

symbolic-compactification manybody integral --variable w --beta beta --positive g \
  --integrand "nF(w)*g/pi/((w-e)**2+g**2)" \
  --claim "1/2 - im(polygamma(0, 1/2 + beta*(g + I*e)/(2*pi)))/pi" \
  --symbols '[{"name":"beta","nonzero":true},{"name":"g","nonzero":true},{"name":"e"},{"name":"w"}]'
```

For divided differences and frequency coefficients:

```bash
symbolic-compactification manybody identity --functions f \
  --lhs "DD_f(x,y,y)" --rhs "(DD_f(x,y) - D_f(1,y))/(x - y)" \
  --symbols '[{"name":"x"},{"name":"y"}]'

symbolic-compactification manybody coefficient --functions f --variable w --order 2 \
  --expr "DD_f(x+w,y,z)" --claim "DD_f(x,x,x,y,z)" \
  --symbols '[{"name":"x"},{"name":"y"},{"name":"z"},{"name":"w"}]'
```

Declared functions are arbitrary smooth functions. `NONZERO` is proved by
a concrete test function at a rational point. The value is certified to
30 digits with strict evaluation, so the refutation is a genuine
counterexample to the universal claim.

Each command prints one JSON object with `status` (or `verdict`), the
reasons, the derived closed form or limit, the numerical cross-check and,
when certified, a certificate hash. Expressions can be read from files
with `@path`.

## Not covered yet

- **Pointwise products `A(t,t′)B(t,t′)`** (bubbles on the Keldysh contour).
  They have their own Langreth rows, but they are not matrix products.
- **Analytic continuation `iω_n → ω + i0⁺` of non-rational functions,
  Kramers–Kronig and Sokhotski–Plemelj relations.** These are distributional
  statements. Record them as `CITED_RULE` and support them numerically.
- **Wick contractions and diagram combinatorics, Dyson resummations, and
  BCH or exponential series.**
- **Momentum integrals with cutoffs or regularization.**

## References used to choose the forms

- P. Coleman, *Introduction to Many-Body Physics* (Cambridge, 2015):
  - ch. 8: imaginary time, Matsubara representation, the contour integral
    method;
  - ch. 9: spectral decompositions, the fluctuation–dissipation theorem,
    Kramers–Kronig (App. 9A).
- A. P. Jauho, *Introduction to the Keldysh nonequilibrium Green function
  technique* (lecture notes): the Langreth theorem and Table I; see also
  Haug and Jauho, *Quantum Kinetics in Transport and Optics of
  Semiconductors*.
- A. J. Daley, *Quantum trajectories and open many-body quantum systems*,
  Adv. Phys. **63**, 77 (2014), arXiv:1405.6694: the master equation and the
  effective non-Hermitian Hamiltonian of quantum-trajectory methods.
