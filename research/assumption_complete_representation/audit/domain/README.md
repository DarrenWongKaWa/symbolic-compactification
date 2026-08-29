# A2 — verifier analytic-domain requirements vs dossier contracts

Agent: A2. Branch: `work/ac-a-domain`. Parent: `f987fcc`.
Owns: `research/assumption_complete_representation/audit/domain/`.
Machine record: [`DOMAIN.json`](DOMAIN.json).

Guo is sealed (`9fc3c8a`): `G0016 → G0013 = UNKNOWN LEVEL_B`.
Not a C1–C5 case. No `beta>0` / `gamma>0` / real `epsilon` insertion.

## Remainder invariant

```
neg ZERO + C0 ZERO + rem UNKNOWN  ≠  hop ZERO
```

Domain `CERTIFIED` is not remainder `CERTIFIED`. Remainder `CERTIFIED` is not hop `ZERO` (`H8`). An `ASSUMPTION_GAP` (pole-exclusion needed and not `DECLARED`/`DERIVED`) is `PROBLEM_UNDERSPECIFIED`, not `DISCOVERY_FAILURE`, and cannot mint hop `ZERO`.

Authority: `ASSUMPTION_POLICY.md`, `THEOREMS.md` (T1–T7 / H1–H8), `polygamma/domain.py` (`rc-pg-domain-1`), `hypotheses.py` (`ENTIRE_FAMILIES`, `CLASSICAL_EXCLUDED_POINTS`), `ASSUMPTION_CONTRACT.md`.

## How labels are scored

| status | meaning |
|---|---|
| `DECLARED` | Labeled `DECLARED` on a contract predicate, or written as that head’s `function_domains` polar/cut set |
| `DERIVED` | Labeled `DERIVED` and proved from class A (no class C/D) |
| `NOT_DECLARED` | Explicit hole already recorded by the miner |
| `MISSING` | Verifier needs it; absent from labeled predicates and from `function_domains` |
| `N_A` | Not required for the claimed identity (entire family; algebraic tensor; distributional/boundary identity whose holomorphic remainder would be `H7 NONANALYTIC`; or a hypothesis the dossier forbids inserting) |
| `ASSUMPTION_GAP` | A **pole-exclusion** (or classical excluded point / resolvent-set membership) needed to certify a holomorphic remainder or ZERO residual is not `DECLARED` and not `DERIVED` |

`function_domains` records the polar set of the **head**. Argument pole-exclusion is a **separate** labeled predicate. Writing `n_F(z)=(e^{βz}+1)^{-1}` without `e^{βz}≠−1` is not pole-exclusion. That is the Guo lesson.

Not-identically-a-pole is not pole-exclusion (`rc-pg-domain-1`). Genericity is class C. Physics positivity is class D unless the source writes it.

## Special functions (verifier-required domains)

These are the families that actually appear in C1–C5 dossiers.

| family | holomorphy | poles / cuts | verifier must discharge |
|---|---|---|---|
| resolvent `R(z,A)` | holomorphic on `ρ(A)=ℂ\σ(A)` | spectrum | `z∈ρ(A)`; holomorphy on `ρ(A)` for confluent `R'` |
| `1/z` (inv) | meromorphic | `{0}` | argument `≠0` for a holomorphic disk (`CLASSICAL_EXCLUDED_POINTS['inv']`); real-line `ε→0+` identities are **boundary values**, not a disk about 0 (`H7`) |
| `exp` | entire | empty | named entire family; `ρ=+∞`; no pole-exclusion (`ENTIRE_FAMILIES`) |
| `log` | principal on `ℂ\(-∞,0]` | branch point 0; cut `(-∞,0]` | argument `≠0`; declared branch; disk must not contain 0 |
| `sqrt` | principal on `ℂ\(-∞,0]` | branch point 0 | declared branch; `0` excluded unless only a positive real root of a positive constant |
| polygamma / digamma / trigamma | meromorphic for integer `k≥−1`; entire for `k≤−2` | `Z_≤0` when `k≥−1` | `z∉Z_≤0` from A/B (`Im≠0`, `z>0`, or certified distance). Not-identically-a-pole is insufficient |
| `tanh` | meromorphic | `i(n+½)π` | none on `ℝ`; real argument ⇒ exclusion `DERIVED` |
| `coth` (`cosh/sinh`) | meromorphic | `nπi` (zeros of `sinh`) | `z≠nπi`; engine rewrite: `coth` not in `PARSE_POLICY` |
| `cot` / `1/tan` | meromorphic | `cot(πz)` poles at integers | `z∉ℤ` |
| `Gamma` | meromorphic | `Z_≤0` | argument not a nonpositive integer |
| `Li_s` | series `\|z\|<1`; continuation off the cut | branch point `z=1`; cut `[1,∞)` | declared `(s,x)` domain; argument off the cut or declared continuation |
| Fermi–Dirac `n_F` | meromorphic | `βz=(2n+1)πi` | `e^{βz}≠−1`; `β≠0` (`β>0` is class D unless declared or derived from a written interval `(0,β)`). `T=0` Heaviside is **not** this germ |
| Bose `n_B` | meromorphic | `βz=2nπi` including `z=0` | `e^{βz}≠1`, including `z≠0` |
| matrix `f(A)` | depends on the definition in force | poles of the scalar germ that meet `σ(A)`; resolvent poles on `Γ` if Cauchy–Dunford | do **not** upgrade Hermite “defined on the spectrum” (Higham 1.4) to holomorphy (1.11). Cauchy: `Γ∩Λ(A)=∅` and `f` holomorphic on/inside `Γ`. Fréchet/Mathias: `C^{2n-1}` on open `D∋σ(X)` |
| Helmholtz Green `e^{ikR}/(4πR)` | singular at `R=0`; `exp` entire in `kR` | `R=0` | `R≠0`, `k>0`, Euclidean (nonnegative) `sqrt`, Sommerfeld outgoing sign. `Im k>0` must not be inserted |
| Hilbert / Lehmann `G(z)` | holomorphic off `supp ρ ⊂ ℝ` | real spectral cut; free poles at `z=ξ` | interior remainder at real `ω` is `H7` unless a positive imaginary part is kept. `η→0+` must be declared for a retarded boundary value |
| `φ_k` | entire (`φ_k(0)=1/k!`) | empty (removable at 0) | named entire family; the `z≠0` Newton quotient is a separate member, then entire continuation |
| OU / Mehler Gaussian | entire of Gaussian type in `(x,y)` for `t>0` | none if `v_t>0` | `t>0`, `θ>0` ⇒ `v_t>0` so the real `sqrt` misses 0 |
| `sin` | entire | empty | zeros in a **denominator** are a separate inv pole-exclusion |
| Heaviside | not holomorphic | jump at 0 | no holomorphic remainder through the jump |

`PARSE_POLICY` allows `sin,cos,tan,exp,log,sqrt,Abs,conjugate,re,im,sinh,cosh,tanh,asin,acos,atan,atan2,Rational,polygamma`. `coth`, `polylog`, `gamma`, `Integral`, `DiracDelta`, `Heaviside` are not default builtins. That is engine admissibility, not an analytic-domain gap. Thermal sketches already write `coth` as `cosh/sinh`.

## Counts

Forty C1–C5 miner dossiers (C6 skeptic negatives are not candidates).

| cluster | n | `OK` | `ASSUMPTION_GAP` | miner-rejected |
|---|---:|---:|---:|---:|
| C1 response | 8 | 4 | 4 | 1 (`ac-r08`) |
| C2 thermal | 8 | 7 | 1 | 1 (`thermal-08`) |
| C3 mathphys | 8 | 8 | 0 | 0 |
| C4 tensor | 8 | 8 | 0 | 1 (`ac-t-rej-index-rename`, not a domain hole) |
| C5 sciml | 8 | 8 | 0 | 0 |
| **total** | **40** | **35** | **5** | **3** |

Gap case ids: `ac-r04-lindhard-occupation-dd`, `ac-r06-matsubara-pole-family`, `ac-r07-lippmann-schwinger-iepsilon`, `ac-r08-kubo-frequency-underspecified`, `thermal-08-matsubara-newton-dd-underspecified`.

## `ASSUMPTION_GAP`

### `thermal-08-matsubara-newton-dd-underspecified` (C2, miner-rejected)

Verifier for the two-pole occupancy Newton quotient needs

- `ξ1 ≠ ξ2`
- poles of `g` disjoint from `{iω_n}`
- occupancy poles `e^{βξ}=η` excluded
- `β>0` to locate those poles

All four are labeled `NOT_DECLARED`. Preserved as `PROBLEM_UNDERSPECIFIED`. Do not import Guo pole-exclusion to repair it.

### `ac-r06-matsubara-pole-family` (C1, skeptic-flagged `SILENT_PHYSICS_POSITIVITY`)

Same Wikipedia table as `thermal-08`, but C1 labeled more generously.

- `ξ1≠ξ2` is `DECLARED` (separate table rows).
- “poles of `g` distinct from Matsubara poles of `h_η`” is only `function_domains[g]` prose, not a labeled analytic predicate.
- `function_domains[n_F]` / `[n_B]` are **formulae**, not pole sets.
- `ξ` is complex and unconstrained, so `e^{βξ}=η` is not excluded from A/B.
- `β` is real only; `T>0` is not inserted. `0<τ<β` is the Green weighting-function paragraph, not a table-row `β>0`.

Occupancy pole-exclusion is `MISSING` → `ASSUMPTION_GAP`. A remainder certificate for `n_η(ξ)` cannot go `CERTIFIED` from this contract.

### `ac-r04-lindhard-occupation-dd` (C1, skeptic-flagged)

Retarded `ω+iδ` with `δ→0+` is `DECLARED`. That keeps the **dynamic** energy denominator off the real axis.

Gaps:

- Static limit `ω+iδ→0` leaves `E(k+q)−E(k)` with **no** labeled `E(k+q)≠E(k)`.
- Holomorphic confluence remainder of occupation needs a `C^1`/`C^∞` germ. Finite-`T` meromorphic `n_F` requires `T>0`, which the notes refuse to insert. `T=0` Heaviside is a jump (`H7`), not a meromorphic occupation.
- Occupancy poles `e^{βE}=−1` are not in the contract (`β` is not even a symbol).

The `T=0` log-abs closed form is correctly **not** the candidate (complex `log` branch undeclared). That avoidance is not a substitute for occupation pole-exclusion.

### `ac-r07-lippmann-schwinger-iepsilon` (C1, skeptic-flagged)

The **naive** pole `E∈σ(H0)` is `DECLARED`. Causal `±iε` and limiting-absorption half-planes are `DECLARED` as prose.

The regularized scalar model `1/(E−E_β ± iε)` still needs `ε≠0` to miss that pole. The symbol `ε` has no `nonzero`/`positive` flag; notes say `ε>0` is not inserted. Pole-exclusion of the regularized denominator is `MISSING` → `ASSUMPTION_GAP`.

### `ac-r08-kubo-frequency-underspecified` (C1, miner-rejected)

Time-domain Kubo is sourced. Frequency-domain `Im ω>0` and `i0+` are labeled `NOT_DECLARED`. Miner already `PROBLEM_UNDERSPECIFIED`. Gap confirmed: a retarded `1/ω` pole prescription is a pole-exclusion the contract does not grant.

## What is not a gap

**Entire families.** `exp`, `sin`, `φ_k` (entire continuation), linear-ODE `expm`, Van Loan block `exp`. `H1` holds with `ρ=+∞`. No pole-exclusion lemma.

**Polygamma keepers with written/derived exclusion.**

- `thermal-01`: `Re(½+iy)=½` ⇒ `DERIVED` `z∉Z_≤0`.
- `thermal-02`: `y≠0` `DECLARED`; `Iy∉Z_≤0` `DERIVED`.
- `thermal-03`: `z∉ℤ` `DECLARED`; both `ψ` arguments miss `Z_≤0` `DERIVED`.
- `thermal-05`: `z∉Z_≤0` written on DLMF 5.15.1.

**`coth` with written exclusion.** `thermal-04`: `z≠nπi` `DECLARED`; `sinh≠0` `DERIVED`. Thermal `T>0` is not used. (Skeptic `SILENT_PHYSICS_POSITIVITY` is A3, not this pole-exclusion hole.)

**`Li_s`.** `thermal-06`: `(s,x)` domains, principal cut `[1,∞)`, and `Gamma(s+1)` pole-free for `s>−1` are `DECLARED`/`DERIVED`. For real `x`, `−e^x∈(−∞,0]` is off the cut.

**Resolvent / matrix-function mathphys (C3).** `ρ(A)` membership, `Γ∩Λ(A)=∅`, simple eigenvalue, `T_ii≠T_jj`, `C^{2n-1}` on open `D∋σ(X)` are `DECLARED`. Hermite `f(A)` correctly **refuses** inserted holomorphy. Cauchy–Dunford correctly **requires** it. Those two definition lists must not be mixed.

**Hilbert masters** (`ac-r05`, `thermal-07`). Cuts and `η→0+` are `DECLARED`. An interior remainder at real `ω` is `H7 NONANALYTIC` **by the declared cut**, not a missing predicate. `thermal-07` derives `β>0` from the written interval `[0,β]`, not from folklore.

**Sokhotski `1/z` (`ac-r02`).** The identity **is** the pole at `0` as a distributional boundary value. `ε→0+` is `DECLARED`. A holomorphic remainder disk about `0` would be `H7`, which the contract does not claim.

**Helmholtz (`ac-r03`).** `R≠0`, `k>0`, Euclidean `sqrt`, Sommerfeld sign `DECLARED`. `Im k>0` is correctly not inserted.

**`φ_k` / Van Loan / adjoint (`sciml-phi-hermite-01`, `sciml-vanloan-blockexp-01`, `sciml-adjoint-linear-01`).** Entire `exp` / entire `φ_k`. The symbol `(e^z−1)/z` is the entire continuation, not a cut.

**SciML inverse / Kronecker / IFT.** `0∉σ(A)` for `f(z)=1/z`; `σ(A)∩σ(−B)=∅` for Lyapunov; `I−J_f` invertible for DEQ. All `DECLARED`.

**Tweedie `log`.** Real `log` on `(0,∞)` with `f>0` `DECLARED`; classical excluded point `0` avoided.

**OU/Mehler.** `v_t>0` `DECLARED`/`DERIVED` from `θ>0`, `t>0`; real `sqrt` misses `0`.

**Weyl `SU(2)` character.** Quotient poles `z^2=1` `DECLARED`; preferred path is the **division-free polynomial** (entire). Removable value `m+1` `DERIVED`.

**Algebraic tensors** (Levi-Civita, Pauli, Young, Ricci, isotropic projectors, Clebsch projectors). No meromorphic special function. Empty `analytic_domains` is correct. `sqrt(2)` in Clebsch kets is the positive real root, `DECLARED`, and is not used in the projector algebra.

**`ac-t-rej-index-rename`.** Rejected as index renaming, not as a domain hole.

## Cluster notes

**C1.** Four of eight dossiers have pole-exclusion gaps, two of them already miner-rejected (`ac-r08`) or the thermal twin of an underspecified table (`ac-r06` vs `thermal-08`). Keepers `ac-r01` and `ac-r03` are domain-complete for the claimed identities.

**C2.** The DLMF polygamma/`coth`/`Li_s` keepers write the pole/cut set on the same equation the verifier would use. `thermal-08` is the intentional underspecified control.

**C3.** Definition-sensitive holomorphy is handled: Cauchy vs Hermite vs `C^{2n-1}` Fréchet are not silently identified. Resolvent identities live on `ρ(A)`, not on a disk about the spectrum.

**C4.** Analytic-domain load is almost empty by design (finite-index algebra). The one meromorphic-looking object (Weyl quotient) has a polynomial bypass.

**C5.** Named entire `exp`/`φ_k`, declared invertibility, declared `log` domain, declared `v_t>0`. No pole-exclusion gap on the claimed members.

## Admission consequence

`ADMISSION_GATE.md` item 3: every verifier-domain hypothesis is `DECLARED` or `DERIVED`.

The five `ASSUMPTION_GAP` rows fail that item. They must not enter DEV as if domain-complete. `ac-r08` and `thermal-08` are already `PROBLEM_UNDERSPECIFIED`. `ac-r04`, `ac-r06`, `ac-r07` are not miner-rejected; this audit flags them so A4 / admission do not treat skeptic-only flags as a substitute for pole-exclusion.

No remainder `CERTIFIED` and no hop `ZERO` follows from these dossiers without the missing A/B predicates. That is fail-closed, not a verifier bug.
