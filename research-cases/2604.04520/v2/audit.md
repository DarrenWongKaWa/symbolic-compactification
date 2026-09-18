# Paper audit V2 — arXiv:2604.04520

**Nonreciprocal current induced by dissipation in time-reversal symmetric systems**

Source: https://arxiv.org/abs/2604.04520

**Presentation is not a certificate.**

## A. Paper audit summary

- Overall state: `AUDIT_INCOMPLETE`
- Claims: 5
- Numbered equations (V2): 93 = main 11 + appendix 82
- V1 claimed: 94 = main 12 + appendix 82
- Relations reconstructed: 17
- Machine-certified edges: 1
- Assumption-dependent edges: 3
- Unresolved load-bearing edges: 13

V1 counted 12 main rows by splitting the S-matrix align on an inner array \\. Published numbering gives one number to that display, so main is 11 not 12. Appendix 82 is unchanged. Rice–Mele Hamiltonian is inline math, not a numbered equation.

### Warnings

- Local residual 0 is not a paper pass.
- Silence from non-submission is not a pass.
- Finite Laurent/Taylor coefficients do not prove an O(·) remainder bound.
- Human accept/reject does not convert a parent claim into machine Exact.
- Numerical agreement with a model is not an analytic proof of Eq. (5).

## B. Major scientific claims

### C1 — Human review

Nonreciprocal current can arise in time-reversal symmetric Bloch electrons when finite dissipation enables interband processes.

- **Status:** `HUMAN_REVIEW`
- **Locator:** Introduction; Discussion; abstract
- **Supporting equations:** (1), (4), (5)
- **Appendix chain:** A → B → D
- **Assumptions:** TR symmetry; inversion breaking; finite Γ; Bloch electrons
- **Unresolved obligations:** O1, O2
- **Downstream:** Motivates the Green-function formula and the geometric conductivity (C2).

- Blocker: Conceptual claim. The S-matrix unitarity argument is local algebra under S†S=I; the physical leap from non-unitarity to interband DC current is not a compiled residual.

### C2 — Gap

In TR-symmetric systems the longitudinal conductivity is geometric: \(\sigma^{\alpha\alpha\alpha}\) is built from the shift vector \(R_{ab}\) and Berry connections, Eq. (5), starting from the Green-function kernel Eq. (4).

- **Status:** `GAP`
- **Locator:** Results, Eqs. (4)–(5); Appendix D (app:derivationSigma2)
- **Supporting equations:** (3), (4), (5), C-1, C-2, D-1
- **Appendix chain:** Eq. (4) Green kernel → Appendix C: static σ from ∂ω²K and band-basis I^(1,2,3) → Appendix D: μ=β=α → Σ^{ααα} → TR identities on ∂H, ∂²H → antisymmetrization 𝒜 of Green products → shift-vector rewrite → H^α_ab = ξ_ab i A_ab → Eq. (5)
- **Assumptions:** TR: [T,H(k)]=0 with T=KU(k→−k); no band degeneracy; Bloch periodicity; constant Γ in G^{R,A}=(ε+μ−H±iΓ)^{-1}; velocity gauge
- **Unresolved obligations:** O1, O5, O6, O7
- **Downstream:** C3–C5 all quote Eq. (5). If C2 fails, the scaling and numerics lose their analytic parent.

- Blocker: The Appendix D algebra (antisymmetrization, shift-vector identity, H=ξ i A substitution) is not compiled as local A−B=0.
- Blocker: TR matrix-element identities are representation-theoretic, not a checked residual.

### C3 — Asymptotic, uncertified

For an insulator/semiconductor (\(\mu\) in the gap) at low \(T\) (\(\Gamma\ll\xi_{\min}\), \(\beta\Gamma\gg 2\pi\)), \(D^{(2,3)}=O(\Gamma^2)+O(\Gamma^3)\), so \(\sigma^{\alpha\alpha\alpha}=O(\Gamma^2)\).

- **Status:** `ASYMPTOTIC_UNCERTIFIED`
- **Locator:** Results, Eqs. (8)–(9); Appendix D kernels
- **Supporting equations:** (6), (7), (8), (9)
- **Appendix chain:** D (kernels already in main text) → digamma \(\psi(z)\sim\log z\)
- **Assumptions:** \(\mu\) inside the gap so \(\xi_{\min}\le|\xi_a|\) for all bands; \(\Gamma\ll\xi_{\min}\); \(\beta\Gamma\gg 2\pi\); \(\psi(z)\sim\log z\); no degeneracy
- **Unresolved obligations:** O8
- **Downstream:** Rice–Mele semiconducting \(\Gamma^2\) curves (C5) are consistency checks of this scaling.

- Blocker: Finite displayed terms do not prove the O(Γ³) remainder.

### C4 — Asymptotic, uncertified

At high \(T\) (\(\beta\Gamma\ll 2\pi\)), or when \(\mu\) lies in a band, the leading piece is \(O(\Gamma)\).

- **Status:** `ASYMPTOTIC_UNCERTIFIED`
- **Locator:** Results, Eqs. (10)–(11) and the metallic paragraph
- **Supporting equations:** (6), (7), (10), (11)
- **Appendix chain:** same D kernels; no extra appendix identity
- **Assumptions:** high-T: \(\beta\Gamma\ll 2\pi\); or metallic: some \(\xi_a=0\), so the low-T \(\xi_{\min}\) argument is unavailable
- **Unresolved obligations:** O8
- **Downstream:** Rice–Mele metallic/high-T \(\Gamma^1\) curves (C5).

- Blocker: O(Γ²) remainder in Eqs. (10)–(11) is declared, not certified.
- Blocker: Metallic O(Γ) is a domain argument, not a compiled expansion.

### C5 — Numerical support

A 1D Rice–Mele calculation produces \(\sigma^{xxx}(\mu,\Gamma,T)\) consistent with dissipation-induced geometric current in a TR-symmetric inversion-broken insulator/metal, and an order estimate for 3D polar semiconductors.

- **Status:** `NUMERICAL_SUPPORT`
- **Locator:** Model calculation; Figs. 2–3; Appendix E
- **Supporting equations:** (5), E-1, E-2, E-3
- **Appendix chain:** Appendix E order estimation (unnumbered Hamiltonian in main text)
- **Assumptions:** Rice–Mele \(H(k)=t_0\cos k\,\sigma_x+\delta t\sin k\,\sigma_y+m\sigma_z\); parameters \(m=\delta t=0.1 t_0\) in the figures; TR preserved so Drude and QMD vanish in this model
- **Unresolved obligations:** O9
- **Downstream:** Does not prove Eq. (5). Supports observability claims in the Discussion.

- Blocker: Numerical evaluation of a model is consistency, not derivation.

## C. Load-bearing derivation graph

Central chain reconstructed from the TeX: **Eq. (4)** `eq:currentbyExcitation` → Appendix C band-basis kernel → Appendix D longitudinal + TR + antisymmetrization + shift vector → **Eq. (5)** `eq:sigma2`.

| ID | From | To | Transformation | Assumptions | Status | Locator |
|---|---|---|---|---|---|---|
| `E-green-kernel` | (3) | (4) | cited identity | constant Γ; velocity-gauge vertices H^α=∂_{k_α}H | `GAP` | Results, Eq. (4); Appendices A–B |

$$ \mathcal{K}^{\mu\alpha\beta}(\omega,-\omega)\propto\int d\epsilon\,2\Gamma^2(f(\epsilon)-f(\epsilon+\hbar\omega))\,\mathrm{Tr}[\cdots G^R H^\alpha G^A \cdots] $$

| `E-C-static-from-green` | (3)+(B-16) | C-1 | substitution | static limit ω→0 taken before Γ→0 | `GAP` | Appendix C opening, eq:sigmaMuAlphaBetaGreenFunction |
| `E-C-band-basis` | C-1 | C-2 | exact algebra | spectral representation of G^{R,A}; no degeneracy later | `GAP` | Appendix C, eq:generalNonReciprocalKernel |
| `E-D-longitudinal` | C-2 | D-1 | substitution | μ=β=α (longitudinal); TR to be imposed next | `STRUCTURAL` | Appendix D, first paragraph and eq:longitudinalNonReciprocalKernel |
| `E-D-TR-matrix` | D-1 | D-2 | symmetry | TR: T=KU(k→−k), [T,H(k)]=0 | `HUMAN_REVIEW` | Appendix D after D-1, two numbered H-matrix identities |

$$ \langle a|\partial_{k_\alpha}H|b\rangle=-\langle b|\partial_{k_\alpha}H|a\rangle|_{k\to-k} $$

| `E-D-antisym` | D-2 | D-4 | symmetry | TR; coefficients may be antisymmetrized in band indices | `GAP` | Appendix D, steps marked \(\overset{\mathcal{A}}{=}\) |
| `E-D-shift` | D-1 | D-8 | cited identity | TR; F(a,b) arbitrary in band indices | `GAP` | Appendix D, “Using the TR symmetry, for arbitrary F(a,b)” |

$$ \sum H_{ba}^{\alpha\alpha}H_{ab}^\alpha F(a,b)=-i\sum R_{ba}H_{ba}^\alpha H_{ab}^\alpha F+\cdots $$

| `E-D-to-sigma2` | D-8 | (5) | substitution | H_{ab}^\alpha=\xi_{ab} i A_{ab}^\alpha; Eq. (C-1) Green identity | `GAP` | Appendix D last sentence: Using H=ξ i A and eq:sigmaMuAlphaBetaGreenFunction we obtain Eq. (5). |

$$ \sigma^{\alpha\alpha\alpha}=\frac{e^3}{\hbar}\int_{\mathrm{BZ}}\big[\sum_{a\neq b}R_{ab}|A_{ab}|^2 D^{(2)}_{ab}+\sum \Re(A_{ab}A_{bc}A_{ca})D^{(3)}_{abc}\big] $$


### Other load-bearing edges

| ID | From | To | Transformation | Assumptions | Status | Locator |
|---|---|---|---|---|---|---|
| `E-unitarity` | (1) | \|t_LR\|=\|t_RL\| | exact algebra | S†S = SS† = I | `EXACT_IF_ASSUMPTIONS` | Introduction, scattering-matrix paragraph |
| `E-static-sigma` | (2) | (3) | substitution | velocity gauge A=E/iω; monochromatic E | `GAP` | Results, sentence before Eq. (3); Appendix A |
| `E-gauge-vanish` | (2) | (3) | gauge argument | gauge invariance; Bloch electrons; static A unphysical | `HUMAN_REVIEW` | Results after Eq. (3); Appendix A (undifferentiated K and mixed ω1² terms) |
| `E-lowT` | (6)+(7) | (8)+(9) | asymptotic expansion | μ in gap; Γ≪ξ_min; βΓ≫2π; ψ(z)∼log z | `ASYMPTOTIC_UNCERTIFIED` | Results, low-temperature insulating paragraph |
| `E-highT` | (6)+(7) | (10)+(11) | asymptotic expansion | βΓ≪2π | `ASYMPTOTIC_UNCERTIFIED` | Results, high-temperature paragraph |
| `E-numeric-RM` | (5) | Figs. 2–3 | numerical evidence | H(k)=t_0\cos k\,\sigma_x+\delta t\sin k\,\sigma_y+m\sigma_z; TR of Rice–Mele; m=δt=0.1 t_0 in the plots | `NUMERICAL_SUPPORT` | Model calculation; Fig. colorMapvsMu; Fig. riceMelevsGamma |

## D. Reviewer queue

### O1 (priority 1) — `HUMAN_REVIEW`

**Claim being used.** Gauge invariance removes the \(O(\omega^0)\) and \(O(\omega)\) pieces of \(\mathcal{K}(\omega,-\omega)\), so static \(\sigma\) is the \(\omega^2\) term.

**Why the system cannot certify it.** This is a physical gauge/Bloch argument, not a local symbolic identity A−B=0. Appendix A also invokes that a static vector potential is unphysical.

**Evidence from the paper.** Main text after Eq. (3); Appendix A, undifferentiated K and \(\partial_{\omega_1}^2\mathcal{K}|_{0,0}\) vanishing.

**What the reviewer must decide.** Confirm that, under the declared Bloch + velocity-gauge assumptions, the two leading orders in ω vanish identically so that Eq. (3) is the DC conductivity.

**Blocks.** C2, E-gauge-vanish, E-static-sigma

Human approval does not stamp Exact.

### O5 (priority 2) — `HUMAN_REVIEW`

**Claim being used.** TR symmetry T=KU(k→−k) implies the two H-matrix identities used to antisymmetrize the longitudinal kernel.

**Why the system cannot certify it.** Requires the antiunitary representation of TR on Bloch states. Not encoded as a compiled residual.

**Evidence from the paper.** Appendix D, two numbered lines after Eq. (D-1).

**What the reviewer must decide.** Accept \(\langle a|\partial_\alpha H|b\rangle=-\langle b|\partial_\alpha H|a\rangle|_{k\to-k}\) and the corresponding \(\partial^2 H\) identity under the paper's T.

**Blocks.** C2, E-D-TR-matrix

Human approval does not stamp Exact.

### O6 (priority 3) — `GAP`

**Claim being used.** After TR, Green-function monomials may be replaced by antisymmetrized equivalents (\(\overset{\mathcal{A}}{=}\)).

**Why the system cannot certify it.** Local algebra of the 𝒜 steps was not compiled.

**Evidence from the paper.** Appendix D, four 𝒜 replacements on G^R, G^A strings.

**What the reviewer must decide.** Either accept the 𝒜 calculus as written, or request a compiled identity for each replacement.

**Blocks.** C2, E-D-antisym

Human approval does not stamp Exact.

### O7 (priority 4) — `GAP`

**Claim being used.** The TR rewrite of \(\sum H_{ba}^{\alpha\alpha}H_{ab}^\alpha F(a,b)\) produces the shift vector \(R_{ba}\) and the triple-A term, which become Eq. (5) after \(H=\xi i A\).

**Why the system cannot certify it.** Named geometric identity plus substitution; not a machine residual.

**Evidence from the paper.** Appendix D, F(a,b) display through the last sentence of the appendix.

**What the reviewer must decide.** Confirm the shift-vector identification and the final substitution that yields Eq. (5) from Σ^{ααα}.

**Blocks.** C2, E-D-shift, E-D-to-sigma2

Human approval does not stamp Exact.

### O2 (priority 5) — `HUMAN_REVIEW`

**Claim being used.** Finite Γ is the physically relevant non-unitarity that realises C1.

**Why the system cannot certify it.** Phenomenological self-energy; not derived here.

**Evidence from the paper.** Introduction, imaginary part of the self-energy; constant Γ in G^{R,A}.

**What the reviewer must decide.** Accept constant-Γ relaxation as the dissipation model of the paper.

**Blocks.** C1

Human approval does not stamp Exact.

### O8 (priority 6) — `ASYMPTOTIC_UNCERTIFIED`

**Claim being used.** \(\psi(z)\sim\log z\) plus the stated \(\Gamma,\beta,\xi\) regime justify C3/C4.

**Why the system cannot certify it.** Asymptotic remainder. Finite displayed polynomials are not an O(·) proof.

**Evidence from the paper.** Results, paragraphs containing Eqs. (8)–(11).

**What the reviewer must decide.** Accept the digamma expansion and domain split (gap vs band, low-T vs high-T) without a remainder certificate.

**Blocks.** C3, C4, E-lowT, E-highT

Human approval does not stamp Exact.

### O9 (priority 7) — `NUMERICAL_SUPPORT`

**Claim being used.** Rice–Mele numerics confirm dissipation-induced σ^{xxx} in a TR-symmetric model.

**Why the system cannot certify it.** Numerical support, not analytic certification of Eq. (5).

**Evidence from the paper.** Model calculation; Figs. colorMapvsMu and riceMelevsGamma; Appendix E.

**What the reviewer must decide.** Treat the figures as consistency in one 1D model (and an order-of-magnitude 3D estimate), not as a proof of the geometric formula.

**Blocks.** C5

Human approval does not stamp Exact.

### O3 (priority 8) — `HUMAN_REVIEW`

**Claim being used.** No band degeneracy.

**Why the system cannot certify it.** Standing assumption; poles merge if bands coincide (Appendix C).

**Evidence from the paper.** Results after Eq. (5); Appendix C ‘we assume that there are no degeneracies’.

**What the reviewer must decide.** Accept the nondegeneracy hypothesis for the geometric formula and the clean-limit cases.

**Blocks.** C2, C3

Human approval does not stamp Exact.


## Numerical evidence

### N1 — `NUMERICAL_SUPPORT`

- Quantity: \(\sigma^{xxx}(\mu,\Gamma,\beta)\) in 1D Rice–Mele
- Supports: C3/C4 scaling and C2’s claim that TR-symmetric inversion-broken crystals can carry this current
- Regime: \(m=\delta t=0.1 t_0\); semiconducting \(\mu=0\); metallic \(\mu=0.15 t_0\)
- Does not prove: Does not prove Eq. (5), the Appendix D identities, or remainder bounds.
- Locator: Figs. 2–3 (colorMapvsMu, riceMelevsGamma)

## E. Equation inventory

Method: Outer numbered equation/align/gather/multline rows without \nonumber. Nested array/tikzpicture/tabular breaks ignored.

| Public | ID | Section | TeX label |
|---|---|---|---|
| (1) | `M-1` | main | — |
| (2) | `M-2` | main | eq:definitionOfCurrent |
| (3) | `M-3` | main | eq:nonReciprocalEsquared |
| (4) | `M-4` | main | eq:currentbyExcitation |
| (5) | `M-5` | main | eq:sigma2 |
| (6) | `M-6` | main | — |
| (7) | `M-7` | main | — |
| (8) | `M-8` | main | eq:lowTmpGammaSquared |
| (9) | `M-9` | main | — |
| (10) | `M-10` | main | eq:highTmpGammaLinear |
| (11) | `M-11` | main | — |
| A-1 | `A-1` | appendix A | eq:DCsumOfalpha_beta |
| A-2 | `A-2` | appendix A | — |
| A-3 | `A-3` | appendix A | — |
| A-4 | `A-4` | appendix A | eq:expandK |
| A-5 | `A-5` | appendix A | — |
| A-6 | `A-6` | appendix A | — |
| A-7 | `A-7` | appendix A | — |
| A-8 | `A-8` | appendix A | eq:11ee |
| A-9 | `A-9` | appendix A | — |
| A-10 | `A-10` | appendix A | eq:current_response_function_diagram |
| A-11 | `A-11` | appendix A | eq:current_response_function |
| A-12 | `A-12` | appendix A | eq:0linTad |
| A-13 | `A-13` | appendix A | eq:0linbub1 |
| A-14 | `A-14` | appendix A | eq:0linbub2 |
| A-15 | `A-15` | appendix A | eq:1linbub1 |
| A-16 | `A-16` | appendix A | eq:1linbub2 |
| A-17 | `A-17` | appendix A | eq:2linbub1 |
| A-18 | `A-18` | appendix A | eq:2linbub2 |
| B-1 | `B-1` | appendix B | eq:tadpoleDerivative |
| B-2 | `B-2` | appendix B | eq:m2 |
| B-3 | `B-3` | appendix B | eq:p4 |
| B-4 | `B-4` | appendix B | eq:p2 |
| B-5 | `B-5` | appendix B | eq:m4 |
| B-6 | `B-6` | appendix B | eq:p1 |
| B-7 | `B-7` | appendix B | eq:m3 |
| B-8 | `B-8` | appendix B | eq:p5 |
| B-9 | `B-9` | appendix B | eq:m1 |
| B-10 | `B-10` | appendix B | eq:p3 |
| B-11 | `B-11` | appendix B | eq:m5 |
| B-12 | `B-12` | appendix B | eq:m1m5 |
| B-13 | `B-13` | appendix B | eq:p1p5 |
| B-14 | `B-14` | appendix B | — |
| B-15 | `B-15` | appendix B | — |
| B-16 | `B-16` | appendix B | eq:currentbyExcitationInX |
| B-17 | `B-17` | appendix B | — |
| B-18 | `B-18` | appendix B | eq:halfPhotocurrent |
| C-1 | `C-1` | appendix C | eq:sigmaMuAlphaBetaGreenFunction |
| C-2 | `C-2` | appendix C | eq:generalNonReciprocalKernel |
| C-3 | `C-3` | appendix C | — |
| C-4 | `C-4` | appendix C | — |
| C-5 | `C-5` | appendix C | — |
| C-6 | `C-6` | appendix C | — |
| C-7 | `C-7` | appendix C | — |
| C-8 | `C-8` | appendix C | — |
| C-9 | `C-9` | appendix C | — |
| C-10 | `C-10` | appendix C | — |
| C-11 | `C-11` | appendix C | — |
| C-12 | `C-12` | appendix C | — |
| C-13 | `C-13` | appendix C | — |
| C-14 | `C-14` | appendix C | — |
| C-15 | `C-15` | appendix C | — |
| C-16 | `C-16` | appendix C | — |
| C-17 | `C-17` | appendix C | — |
| C-18 | `C-18` | appendix C | eq:nonlinearConductivityUptoTau0 |
| C-19 | `C-19` | appendix C | — |
| C-20 | `C-20` | appendix C | — |
| C-21 | `C-21` | appendix C | — |
| C-22 | `C-22` | appendix C | — |
| C-23 | `C-23` | appendix C | — |
| C-24 | `C-24` | appendix C | — |
| C-25 | `C-25` | appendix C | — |
| C-26 | `C-26` | appendix C | — |
| C-27 | `C-27` | appendix C | — |
| C-28 | `C-28` | appendix C | — |
| D-1 | `D-1` | appendix D | eq:longitudinalNonReciprocalKernel |
| D-2 | `D-2` | appendix D | — |
| D-3 | `D-3` | appendix D | — |
| D-4 | `D-4` | appendix D | — |
| D-5 | `D-5` | appendix D | — |
| D-6 | `D-6` | appendix D | — |
| D-7 | `D-7` | appendix D | — |
| D-8 | `D-8` | appendix D | — |
| D-9 | `D-9` | appendix D | — |
| D-10 | `D-10` | appendix D | — |
| E-1 | `E-1` | appendix E | — |
| E-2 | `E-2` | appendix E | — |
| E-3 | `E-3` | appendix E | — |
| E-4 | `E-4` | appendix E | — |
| E-5 | `E-5` | appendix E | — |
| E-6 | `E-6` | appendix E | — |
| E-7 | `E-7` | appendix E | — |
| E-8 | `E-8` | appendix E | — |

### Published main-text map

| Number | Content |
|---|---|
| (1) | S-matrix |
| (2) | eq:definitionOfCurrent  (V1 row ‘main 3’) |
| (3) | eq:nonReciprocalEsquared  (V1 ‘main 4’) |
| (4) | eq:currentbyExcitation Green kernel  (V1 ‘main 5’) |
| (5) | eq:sigma2 geometric conductivity  (V1 ‘main 6’) |
| (6) | D^{(2)} definition |
| (7) | D^{(3)} definition |
| (8) | eq:lowTmpGammaSquared |
| (9) | low-T D^{(3)} |
| (10) | eq:highTmpGammaLinear |
| (11) | high-T D^{(3)} |

## F. Full relation ledger

| ID | From | To | Transformation | Assumptions | Status | Locator |
|---|---|---|---|---|---|---|
| `E-unitarity` | (1) | \|t_LR\|=\|t_RL\| | exact algebra | S†S = SS† = I | `EXACT_IF_ASSUMPTIONS` | Introduction, scattering-matrix paragraph |
| `E-define-K` | (2) | (2) | definition |  | `STRUCTURAL` | Results, Eq. (2) |
| `E-static-sigma` | (2) | (3) | substitution | velocity gauge A=E/iω; monochromatic E | `GAP` | Results, sentence before Eq. (3); Appendix A |
| `E-gauge-vanish` | (2) | (3) | gauge argument | gauge invariance; Bloch electrons; static A unphysical | `HUMAN_REVIEW` | Results after Eq. (3); Appendix A (undifferentiated K and mixed ω1² terms) |
| `E-green-kernel` | (3) | (4) | cited identity | constant Γ; velocity-gauge vertices H^α=∂_{k_α}H | `GAP` | Results, Eq. (4); Appendices A–B |
| `E-C-static-from-green` | (3)+(B-16) | C-1 | substitution | static limit ω→0 taken before Γ→0 | `GAP` | Appendix C opening, eq:sigmaMuAlphaBetaGreenFunction |
| `E-C-band-basis` | C-1 | C-2 | exact algebra | spectral representation of G^{R,A}; no degeneracy later | `GAP` | Appendix C, eq:generalNonReciprocalKernel |
| `E-D-longitudinal` | C-2 | D-1 | substitution | μ=β=α (longitudinal); TR to be imposed next | `STRUCTURAL` | Appendix D, first paragraph and eq:longitudinalNonReciprocalKernel |
| `E-D-TR-matrix` | D-1 | D-2 | symmetry | TR: T=KU(k→−k), [T,H(k)]=0 | `HUMAN_REVIEW` | Appendix D after D-1, two numbered H-matrix identities |
| `E-D-antisym` | D-2 | D-4 | symmetry | TR; coefficients may be antisymmetrized in band indices | `GAP` | Appendix D, steps marked \(\overset{\mathcal{A}}{=}\) |
| `E-D-shift` | D-1 | D-8 | cited identity | TR; F(a,b) arbitrary in band indices | `GAP` | Appendix D, “Using the TR symmetry, for arbitrary F(a,b)” |
| `E-D-to-sigma2` | D-8 | (5) | substitution | H_{ab}^\alpha=\xi_{ab} i A_{ab}^\alpha; Eq. (C-1) Green identity | `GAP` | Appendix D last sentence: Using H=ξ i A and eq:sigmaMuAlphaBetaGreenFunction we obtain Eq. (5). |
| `E-define-D` | (5) | (6)+(7) | definition | no degeneracy | `STRUCTURAL` | Results, displays immediately after Eq. (5) |
| `E-lowT` | (6)+(7) | (8)+(9) | asymptotic expansion | μ in gap; Γ≪ξ_min; βΓ≫2π; ψ(z)∼log z | `ASYMPTOTIC_UNCERTIFIED` | Results, low-temperature insulating paragraph |
| `E-highT` | (6)+(7) | (10)+(11) | asymptotic expansion | βΓ≪2π | `ASYMPTOTIC_UNCERTIFIED` | Results, high-temperature paragraph |
| `E-numeric-RM` | (5) | Figs. 2–3 | numerical evidence | H(k)=t_0\cos k\,\sigma_x+\delta t\sin k\,\sigma_y+m\sigma_z; TR of Rice–Mele; m=δt=0.1 t_0 in the plots | `NUMERICAL_SUPPORT` | Model calculation; Fig. colorMapvsMu; Fig. riceMelevsGamma |
| `E-order-est` | (5) | E-1 | asymptotic expansion | small ω; 3D extension of Rice–Mele | `ASYMPTOTIC_UNCERTIFIED` | Appendix E |

## Provenance

V1 RESULTS greened only 2×2 unitarity under S†S=I. That row is kept as EXACT_IF_ASSUMPTIONS. No other V1 orange row is promoted.

Canonical model: `evidence/audit.json`. HTML twin: `v2/audit.html`.

