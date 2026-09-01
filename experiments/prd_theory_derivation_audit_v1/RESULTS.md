# Theoretical-physics derivation verification table

Each row checks one printed equation transition. ZERO always means exact symbolic ZERO; conditions and approximation authority are shown separately.

| Paper | Eq. from -> to | Claimed move | Direct check | Condition / authority | Conditional check | Final status |
|---|---|---|---|---|---|---|
| Hagiwara et al., PRD 110, 056021 | (FDlightcone) -> (FPFD1) | substitution | NONZERO | s = sgn(q0), q0 nonzero | ZERO | ZERO_UNDER_SUBSTITUTION |
| Hagiwara et al., PRD 110, 056021 | (gaugepropagator-xi) -> (gaugepropagator) | substitution | NONZERO | xi = 0 | ZERO | ZERO_UNDER_SUBSTITUTION |
| Hagiwara et al., PRD 110, 056021 | (eq4) | definition | N/A | none | N/A | STRUCTURAL |
| Hagiwara et al., PRD 110, 056021 | (sampleintegral) | loop integral | N/A | none | N/A | COMPILE_FAILURE |
| Hagiwara et al., PRD 110, 056021 | (selfgg+selfgn+selfnn+selffp) -> (selfenergy) |q|^2 real | algebra | ZERO | none | N/A | EXACT_ZERO |
| Hagiwara et al., PRD 110, 056021 | (selfenergy) overall 1/2 * inner -> 11/3 | algebra | ZERO | none | N/A | EXACT_ZERO |
| Hagiwara et al., PRD 110, 056021 | UV pole vs full self-energy | UV pole extraction | N/A | AUTHOR_DECLARED: keep 1/epsilon pole only (\|_{div}) | N/A | UNKNOWN_REMAINDER |
| Cohen et al., PRD 108, 056027 | (eqn:Gdef) | definition | N/A | none | N/A | STRUCTURAL |
| Cohen et al., PRD 108, 056027 | F = -i[P,P] | definition | N/A | none | N/A | STRUCTURAL |
| Cohen et al., PRD 108, 056027 | (eqn:defineanomaly) | weak-alpha expansion | N/A | AUTHOR_DECLARED: discard O(alpha^2) | N/A | UNKNOWN_REMAINDER |
| Cohen et al., PRD 108, 056027 | (eq:A_ren) | limit procedure | N/A | Lambda -> infinity after counterterm | N/A | UNKNOWN |
| Cohen et al., PRD 108, 056027 | (eqn:CCProperties) double conjugation | algebra | N/A | none | N/A | STRUCTURAL |
| Cohen et al., PRD 108, 056027 | P_mu = i D_mu | definition | N/A | none | N/A | STRUCTURAL |
| Cohen et al., PRD 108, 056027 | det(e^{i a} X e^{-i a}) vs det X | algebra | N/A | none | N/A | STRUCTURAL |
| Cohen et al., PRD 108, 056027 | (eq:S_operators) | definition | N/A | none | N/A | STRUCTURAL |
| Guo et al., PRL 136, 206303 | (D-59) -> (D-60) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Guo et al., PRL 136, 206303 | (D-60) -> (D-61) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Guo et al., PRL 136, 206303 | (D-71) -> (D-72) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Guo et al., PRL 136, 206303 | (D-74) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Guo et al., PRL 136, 206303 | (D-66) -> (D-67) | substitution | NONZERO | e21 = -e12 | ZERO | ZERO_UNDER_SUBSTITUTION |
| Guo et al., PRL 136, 206303 | (D-126) -> (D-67 compact) | substitution | NONZERO | f1p = 2*f01p, f2p = 2*f02p | ZERO | ZERO_UNDER_SUBSTITUTION |
| Guo et al., PRL 136, 206303 | (D-120) -> (D-121) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Guo et al., PRL 136, 206303 | (D-114) -> (D-119) | IBP | N/A | BZ torus periodicity | local child ZERO | CERTIFIED_BY_RULE |
| Guo et al., PRL 136, 206303 | (D-57) | asymptotic truncation | N/A | AUTHOR_DECLARED: O(Gamma) remainder | UNKNOWN | UNKNOWN_REMAINDER |
| Souza et al., PRD 107, 105003 | mu1^2+mu2^2 parameterization | algebra | ZERO | none | N/A | EXACT_ZERO |
| Souza et al., PRD 107, 105003 | tadpole -> lam1 | substitution | NONZERO | lam1 = -3 lam3 (mu2/mu1)^2 from tadpole=0 | ZERO | ZERO_UNDER_SUBSTITUTION |
| Souza et al., PRD 107, 105003 | tadpole identity after cond | substitution | NONZERO | lam1 = -3 lam3 (mu2/mu1)^2 | ZERO | ZERO_UNDER_SUBSTITUTION |
| Souza et al., PRD 107, 105003 | m1^2 = -lam3 mu^2 = |lam3| mu^2 | sign convention | NONZERO | AUTHOR_DECLARED: lam3 < 0 so -lam3 = \|lam3\| | ZERO | ZERO_UNDER_SUBSTITUTION |
| Souza et al., PRD 107, 105003 | V at tree vev | substitution | NONZERO | sigma = mu sa, phi = mu ca, cota=cot alpha, tana=tan alpha | ZERO | ZERO_UNDER_SUBSTITUTION |
| Souza et al., PRD 107, 105003 | (RGE1) | algebra | ZERO | none | N/A | EXACT_ZERO |
| Souza et al., PRD 107, 105003 | Veff = tree+LL+NLL+... -> LL only | leading-log truncation | N/A | AUTHOR_DECLARED: keep leading logarithms, drop NLL+ | N/A | UNKNOWN_REMAINDER |
| Souza et al., PRD 107, 105003 | Gamma_sigma loop | loop integral | N/A | none | N/A | COMPILE_FAILURE |
| Souza et al., PRD 107, 105003 | tree Vmin=0 vs one-loop Vmin | suspected truncation | NONZERO | UNDECLARED / inferred only: drop one-loop CW piece | ZERO | UNDECLARED_APPROXIMATION_REQUIRED |
| Flathmann and Hohmann, PRD 105, 044002 | (eqn:torsion) | definition | N/A | none | N/A | STRUCTURAL |
| Flathmann and Hohmann, PRD 105, 044002 | (eqn:metricperturb) | PPN expansion | N/A | AUTHOR_DECLARED: discard O(5) in 1/c | N/A | UNKNOWN_REMAINDER |
| Flathmann and Hohmann, PRD 105, 044002 | kappa^2 + 2 pi l_Q (a5+a6)=0 -> a5+a6 | algebra | NONZERO | Spair := a5+a6 = -kappa^2/(2 pi l_Q) | ZERO | ZERO_UNDER_SUBSTITUTION |
| Flathmann and Hohmann, PRD 105, 044002 | general a1 vs STEGR a1 | coupling specialization | NONZERO | AUTHOR_DECLARED: l_Y = 0 with 3 l_Y^2 + l_X l_Q nonzero | ZERO | CERTIFIED_UNDER_DECLARED_APPROXIMATION |
| Flathmann and Hohmann, PRD 105, 044002 | gamma formula vs 1 | algebra | NONZERO | l_Y = 0 (minimally coupled scalar at linear order) | ZERO | ZERO_UNDER_SUBSTITUTION |
| Flathmann and Hohmann, PRD 105, 044002 | E_mu nu field equation | field equation | N/A | none | N/A | COMPILE_FAILURE |
| Flathmann and Hohmann, PRD 105, 044002 | Theta_00 PPN | PPN expansion | N/A | AUTHOR_DECLARED: discard O(6) | N/A | UNKNOWN_REMAINDER |
| Flathmann and Hohmann, PRD 105, 044002 | a5-a6 and a5+a6 -> a5 | algebra | ZERO | none | N/A | EXACT_ZERO |

## Campaign summary

- papers audited: 5
- equation edges: 41
- EXACT_ZERO: 10
- ZERO_UNDER_SUBSTITUTION: 10
- CERTIFIED_BY_RULE: 1
- CERTIFIED_UNDER_DECLARED_APPROXIMATION: 1
- UNKNOWN / UNKNOWN_REMAINDER: 7
- UNDECLARED_APPROXIMATION_REQUIRED: 1
- NONZERO: 0
- STRUCTURAL: 8
- PARSE_FAILURE / COMPILE_FAILURE: 3
- false promotion on injected invalid controls: 0 / 30
